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
from xai_engine import generate_reason, pick_dominant_component


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


class OptiTwinAgent:
    """Wraps a trained PPO model OR the scripted fallback policy."""

    def __init__(self, weights: Optional[RewardWeights] = None,
                 model_path: Optional[str] = None) -> None:
        self.weights = weights or RewardWeights()
        self.model: Optional[Any] = None
        if model_path and os.path.exists(model_path) and PPO is not None:
            try:
                self.model = PPO.load(model_path)
                _log.info("Loaded PPO model from %s", model_path)
            except Exception as exc:  # pragma: no cover
                _log.warning("Failed to load PPO model (%s) — using scripted policy", exc)
                self.model = None
        else:
            _log.info("No PPO model found at %s — using scripted fallback policy", model_path)

    # ------- Public API -------
    def recommend(self, state: Dict[str, Any]) -> AIRecommendation:
        if self.model is not None:
            obs = make_obs_vector(state)
            action, _ = self.model.predict(obs, deterministic=True)
            label = ACTIONS[int(action)]
        else:
            label = self._scripted_policy(state)
        return self._build_recommendation(label, state)

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
