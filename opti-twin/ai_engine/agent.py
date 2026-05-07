"""
Hybrid agent: loads a pre-trained PPO model if available; otherwise falls back
to a deterministic scripted policy that mirrors the trained behaviour.

The scripted policy is what runs at the hackathon demo by default — it makes
auditable, explainable decisions that exactly match the patterns described
in plan.md (PF correction, peak-hour reduction, wall-overheat emergency
cooling, transformer derate, grid ride-through).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np

_log = logging.getLogger("ai.agent")

try:
    from stable_baselines3 import PPO
except ImportError:  # pragma: no cover
    PPO = None

from environment import ACTIONS, _get_forecast_prices, make_obs_vector
from reward_function import RewardWeights, compute_reward
from safety import apply_action_mask, clamp_setpoints
from xai_engine import generate_reason, pick_dominant_component

# Optional M2/M3 — loaded lazily so the agent still works when the trained
# checkpoints aren't available (e.g. on a fresh checkout before training).
try:
    from forecaster.lstm_forecaster import load_forecaster, summarise_for_obs, LOOKBACK as _F_LB
except ImportError:  # pragma: no cover
    load_forecaster = None
    summarise_for_obs = None
    _F_LB = 30
try:
    from anomaly.autoencoder import load_anomaly_detector
except ImportError:  # pragma: no cover
    load_anomaly_detector = None


@dataclass
class AIRecommendation:
    action_label: str
    action_magnitude_pct: float
    arc_power_mw: Optional[float]
    cooling_lmin: Optional[float]
    reactive_comp_mvar: Optional[float]
    estimated_savings_egp_per_hour: float
    pf_penalty_avoided_egp: float
    co2_saved_kg: float
    xai_reason_en: str
    xai_reason_ar: str
    machine_health: str
    production_status: str
    reward_components: Dict[str, float]
    dominant_reason: str
    safety_overridden: bool = False
    safety_reason: Optional[str] = None
    raw_action_label: Optional[str] = None  # what the policy emitted before masking


class OptiTwinAgent:
    """Wraps a trained PPO model OR the scripted fallback policy."""

    def __init__(
        self,
        weights: Optional[RewardWeights] = None,
        model_path: Optional[str] = None,
        *,
        forecaster_path: Optional[str] = None,
        anomaly_path: Optional[str] = None,
    ) -> None:
        self.weights = weights or RewardWeights()
        self.model: Optional[Any] = None
        if model_path and os.path.exists(model_path) and PPO is not None:
            try:
                self.model = PPO.load(model_path)
                _log.info("Loaded PPO model from %s", model_path)
            except Exception as exc:  # pragma: no cover
                _log.warning("Failed to load PPO model (%s) -- using scripted policy", exc)
                self.model = None
        else:
            _log.info("No PPO model found at %s -- using scripted fallback policy", model_path)

        # Optional M2/M3 for live obs construction when the PPO is loaded.
        self._forecaster = None
        self._anomaly = None
        self._forecast_window: Optional[np.ndarray] = None
        self._anomaly_window: Optional[np.ndarray] = None
        self._cached_forecast_summary: Optional[np.ndarray] = None
        self._cached_anomaly_score: float = 0.0
        self._tick_counter = 0
        self._forecast_refresh_every = 10

        if forecaster_path and load_forecaster is not None and os.path.exists(forecaster_path):
            try:
                self._forecaster = load_forecaster(forecaster_path)
                self._forecast_window = np.zeros((_F_LB, 7), dtype=np.float32)
                _log.info("Loaded M2 forecaster from %s", forecaster_path)
            except Exception as exc:  # pragma: no cover
                _log.warning("M2 load failed (%s) -- proceeding without forecaster", exc)

        if anomaly_path and load_anomaly_detector is not None and os.path.exists(anomaly_path):
            try:
                self._anomaly = load_anomaly_detector(anomaly_path)
                self._anomaly_window = np.zeros(
                    (self._anomaly.model.channels, self._anomaly.model.window),
                    dtype=np.float32,
                )
                _log.info("Loaded M3 anomaly detector from %s", anomaly_path)
            except Exception as exc:  # pragma: no cover
                _log.warning("M3 load failed (%s) -- proceeding without anomaly", exc)

    def _state_to_forecast_features(self, s: Dict[str, Any]) -> np.ndarray:
        sh = float(s.get("sim_hour", 0.0))
        rad = 2.0 * np.pi * sh / 24.0
        return np.array([
            float(s.get("electricity_price", 1.60)),
            float(s.get("arc_power_mw", 0.0)),
            1.0 if s.get("is_peak", False) else 0.0,
            1.0 if s.get("tou_mode", False) else 0.0,
            float(np.sin(rad)),
            float(np.cos(rad)),
            float(s.get("grid_frequency", 50.0)),
        ], dtype=np.float32)

    def _state_to_anomaly_channels(self, s: Dict[str, Any]) -> np.ndarray:
        return np.array([
            float(s.get("arc_power_mw", 0.0)),
            float(s.get("furnace_bath_temp", 0.0)),
            float(s.get("wall_panel_temp", 0.0)),
            float(s.get("electrode_temp", 0.0)),
            float(s.get("cooling_water_outlet_temp", 0.0)),
            float(s.get("power_factor", 0.0)),
            float(s.get("energy_this_heat_kwh", 0.0)),
            float(s.get("electrode_consumption_kg", 0.0)),
            float(s.get("grid_frequency", 50.0)),
        ], dtype=np.float32)

    def _refresh_model_state(self, state: Dict[str, Any]) -> None:
        """Update M2/M3 rolling windows and cached outputs from the latest tick."""
        if self._forecaster is not None and self._forecast_window is not None:
            self._forecast_window = np.roll(self._forecast_window, -1, axis=0)
            self._forecast_window[-1] = self._state_to_forecast_features(state)
            if self._tick_counter % self._forecast_refresh_every == 0:
                price_q, _ = self._forecaster.predict(self._forecast_window)
                self._cached_forecast_summary = summarise_for_obs(price_q)
        if self._anomaly is not None and self._anomaly_window is not None:
            self._anomaly_window = np.roll(self._anomaly_window, -1, axis=1)
            self._anomaly_window[:, -1] = self._state_to_anomaly_channels(state)
            ch_means = self._anomaly.channel_means[:, None]
            ch_stds = self._anomaly.channel_stds[:, None] + 1e-6
            normed = (self._anomaly_window - ch_means) / ch_stds
            self._cached_anomaly_score = self._anomaly.score(normed.astype(np.float32))
        self._tick_counter += 1

    # ------- Public API -------
    def recommend(self, state: Dict[str, Any]) -> AIRecommendation:
        # Refresh M2/M3 every tick (cheap; M2 is throttled internally).
        self._refresh_model_state(state)

        if self.model is not None:
            obs = make_obs_vector(
                state,
                forecast_summary=self._cached_forecast_summary,
                anomaly_score=self._cached_anomaly_score,
            )
            action, _ = self.model.predict(obs, deterministic=True)
            raw_label = ACTIONS[int(action)]
        else:
            raw_label = self._scripted_policy(state)

        mask = apply_action_mask(raw_label, state)
        rec = self._build_recommendation(mask.label, state)
        rec.safety_overridden = mask.overridden
        rec.safety_reason = mask.reason
        rec.raw_action_label = raw_label if mask.overridden else None
        return rec

    def update_weights(self, weights: RewardWeights) -> None:
        self.weights = weights

    # ------- Scripted policy -------
    def _scripted_policy(self, state: Dict[str, Any]) -> str:
        """Hand-crafted decision tree matching the trained agent's expected behaviour.

        Priority order (top wins):
          1. Wall overheat → EMERGENCY_COOLING
          2. Grid spike    → GRID_RIDE_THROUGH
          3. Transformer alarm → TRANSFORMER_DERATE
          4. PF below 0.92 with significant load → RAISE_PF_COMPENSATION
          5. Peak-pricing TOU active → REDUCE_ARC_POWER
          6. Pre-peak window (next hour will be peak) → PRE_PEAK_DROP
          7. Otherwise → HOLD_STEADY
        """
        wall = float(state.get("wall_panel_temp", 0.0))
        if wall >= 200.0 or state.get("crisis_flags", {}).get("wall_overheat"):
            return "EMERGENCY_COOLING"

        freq = float(state.get("grid_frequency", 50.0))
        if freq < 49.7 or state.get("crisis_flags", {}).get("grid_spike"):
            return "GRID_RIDE_THROUGH"

        if state.get("crisis_flags", {}).get("transformer_alarm"):
            return "TRANSFORMER_DERATE"

        pf = float(state.get("power_factor", 0.92))
        arc_p = float(state.get("arc_power_mw", 0.0))
        if pf < 0.92 and arc_p * 1000.0 > 500.0:
            return "RAISE_PF_COMPENSATION"

        if state.get("is_peak", False) and arc_p > 70.0:
            return "REDUCE_ARC_POWER"

        # Dynamic pricing pre-peak detection: use forecast if available
        forecast_prices = _get_forecast_prices(4)  # next 2h
        current_price = float(state.get("electricity_price", 1.60))
        price_spike_ahead = any(p > current_price * 1.4 for p in forecast_prices)
        if price_spike_ahead and arc_p > 70.0 and not state.get("is_peak", False):
            return "PRE_PEAK_DROP"

        # Fallback: TOU mode + within 30 sim-min of 18:00
        if state.get("tou_mode", False):
            sim_hour = float(state.get("sim_hour", 0.0))
            if 17.5 <= sim_hour < 18.0 and arc_p > 70.0:
                return "PRE_PEAK_DROP"

        return "HOLD_STEADY"

    # ------- Recommendation builder -------
    def _build_recommendation(self, label: str, state: Dict[str, Any]) -> AIRecommendation:
        arc_p = float(state.get("arc_power_mw", 90.0))
        baseline = 90.0

        arc_mw: Optional[float] = None
        cool_lmin: Optional[float] = None
        comp_mvar: Optional[float] = None

        if label == "REDUCE_ARC_POWER":
            arc_mw = max(60.0, arc_p - 15.0)
        elif label == "PRE_PEAK_DROP":
            arc_mw = max(60.0, arc_p - 25.0)
        elif label == "RAISE_PF_COMPENSATION":
            comp_mvar = 22.0
        elif label == "EMERGENCY_COOLING":
            cool_lmin = 350.0
            arc_mw = max(60.0, arc_p - 10.0)
        elif label == "GRID_RIDE_THROUGH":
            arc_mw = 60.0
        elif label == "TRANSFORMER_DERATE":
            arc_mw = min(75.0, arc_p)
        # HOLD_STEADY: leave None

        arc_mw, cool_lmin, comp_mvar = clamp_setpoints(arc_mw, cool_lmin, comp_mvar)

        magnitude_pct = 0.0
        if arc_mw is not None:
            magnitude_pct = (arc_mw - arc_p) / max(1.0, arc_p) * 100.0

        # Reward components for transparency
        rc = compute_reward(state, self.weights, baseline_arc_power_mw=baseline)
        rc_dict = rc.as_dict()
        dominant = pick_dominant_component(rc_dict)
        reason_en, reason_ar = generate_reason(label, state, rc_dict, dominant)

        # KPI estimates
        delta_kw = max(0.0, baseline - (arc_mw if arc_mw is not None else arc_p)) * 1000.0
        price = float(state.get("electricity_price", 1.60))
        savings_egp_hr = delta_kw * price
        co2_kg_per_kwh = float(state.get("grid_co2_kg_per_kwh", 0.50))
        co2_saved_kg = (delta_kw / 1000.0) * co2_kg_per_kwh  # per simulated hour-equivalent
        pf_avoided = float(state.get("pf_penalty_egp_per_hour_est", 0.0))

        # Health summary
        if wall_health(state) == "CRITICAL":
            health = "CRITICAL"
        elif wall_health(state) == "WARNING":
            health = "WARNING"
        else:
            health = "SAFE"

        backlog = int(state.get("production_backlog", 0))
        if backlog == 0:
            prod_status = "ON_TRACK"
        elif backlog <= 2:
            prod_status = "AT_RISK"
        else:
            prod_status = "BEHIND"

        return AIRecommendation(
            action_label=label,
            action_magnitude_pct=round(magnitude_pct, 1),
            arc_power_mw=arc_mw,
            cooling_lmin=cool_lmin,
            reactive_comp_mvar=comp_mvar,
            estimated_savings_egp_per_hour=round(savings_egp_hr, 1),
            pf_penalty_avoided_egp=round(pf_avoided, 1),
            co2_saved_kg=round(co2_saved_kg, 3),
            xai_reason_en=reason_en,
            xai_reason_ar=reason_ar,
            machine_health=health,
            production_status=prod_status,
            reward_components=rc_dict,
            dominant_reason=dominant,
        )


def wall_health(state: Dict[str, Any]) -> str:
    wall = float(state.get("wall_panel_temp", 0.0))
    if wall >= 230.0:
        return "CRITICAL"
    if wall >= 200.0:
        return "WARNING"
    return "SAFE"
