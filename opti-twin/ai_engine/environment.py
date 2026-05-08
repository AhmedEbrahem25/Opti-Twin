"""
OptiTwinEAFEnv — custom Gymnasium environment for training the PPO agent.

State (39-D, hybrid): normalized to [0, 1].
  Dims 0-15:   core telemetry
  Dims 16-21:  M2 forecast summary (5 quantile + horizon-mean + interval width)
  Dims 22-37:  live dynamic-pricing features (Redis-driven)
  Dim 38:      M3 anomaly score

Dims 16-21 and 38 are populated lazily — when the upstream models aren't
loaded (e.g. during initial PPO training before M2/M3 exist) they default
to zero, so the same obs builder runs in every phase.

Action: 7-action discrete space.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:  # pragma: no cover
    gym = None
    spaces = None  # type: ignore

from reward_function import RewardWeights, compute_reward

ACTIONS = [
    "HOLD_STEADY",
    "REDUCE_ARC_POWER",
    "RAISE_PF_COMPENSATION",
    "EMERGENCY_COOLING",
    "PRE_PEAK_DROP",
    "GRID_RIDE_THROUGH",
    "TRANSFORMER_DERATE",
    "OPTIMIZE_THROUGHPUT",
    "STABILIZE_PROCESS",
    "MAINTENANCE_DERATE",
]

# 16 core telemetry + 6 M2 forecast summary + 16 live pricing + 1 M3 anomaly.
TELEMETRY_DIM = 16
FORECAST_SUMMARY_DIM = 6
PRICING_DIM = 16
ANOMALY_DIM = 1
OBS_DIM = TELEMETRY_DIM + FORECAST_SUMMARY_DIM + PRICING_DIM + ANOMALY_DIM  # = 39

# Thread-safe forecast cache — updated by agent_service pricing subscriber
_forecast_cache: Dict[str, Any] = {}
_forecast_lock = threading.Lock()


def update_forecast_cache(forecast_data: Dict) -> None:
    with _forecast_lock:
        _forecast_cache.update(forecast_data)


def _get_forecast_prices(n: int = 8) -> List[float]:
    """Return up to n forecast p50 prices, padded with last known price."""
    with _forecast_lock:
        steps = _forecast_cache.get("forecast", [])
    prices = [float(s.get("p50", 1.60)) for s in steps[:n]]
    if prices:
        while len(prices) < n:
            prices.append(prices[-1])
    else:
        prices = [1.60] * n
    return prices


def _normalize_price(p: float) -> float:
    return max(0.0, min(1.0, (p - 0.5) / 2.5))


def _normalize_forecast_summary(summary: np.ndarray) -> np.ndarray:
    """Map M2's raw 6-D summary into roughly [0, 1].

    Components are: median@+30min, median@+60min, p05, p95, horizon mean, IPI width.
    Prices in this env range ~[1.0, 2.5] EGP/kWh; the IPI width is bounded by the
    same scale. Apply a robust linear squash and clip.
    """
    out = np.empty_like(summary, dtype=np.float32)
    # First 5 entries are price-like; squash with the same transform as live price.
    for i in range(5):
        out[i] = max(0.0, min(1.0, (float(summary[i]) - 0.5) / 2.5))
    # IPI width — bounded scaling assuming widths < 2.5 EGP.
    out[5] = max(0.0, min(1.0, float(summary[5]) / 2.5))
    return out


def make_obs_vector(
    state: Dict[str, Any],
    *,
    forecast_summary: Optional[np.ndarray] = None,
    anomaly_score: Optional[float] = None,
) -> np.ndarray:
    """Map a telemetry dict to a normalized 39-D observation vector.

    `forecast_summary` is the M2 6-D summary from `forecaster.summarise_for_obs`.
    `anomaly_score` is the M3 scalar in [0, 1] from `AnomalyDetector.score`.
    Both default to zero so this function works during initial training before
    those models exist.
    """
    # --- Dims 0–15: core telemetry (unchanged) ---
    core = [
        (float(state.get("electricity_price", 1.60)) - 1.0) / 1.5,           # 0
        1.0 if state.get("is_peak", False) else 0.0,                         # 1
        (float(state.get("grid_frequency", 50.0)) - 49.5) / 1.0,             # 2
        (float(state.get("furnace_bath_temp", 1500.0)) - 1200.0) / 480.0,    # 3
        (float(state.get("electrode_temp", 1500.0)) - 1500.0) / 1500.0,      # 4
        (float(state.get("wall_panel_temp", 100.0)) - 80.0) / 170.0,         # 5
        (float(state.get("cooling_water_outlet_temp", 35.0)) - 25.0) / 30.0, # 6
        float(state.get("heat_progress_pct", 0.0)) / 100.0,                  # 7
        (float(state.get("current_batch_weight", 180.0)) - 80.0) / 105.0,   # 8
        float(state.get("batches_today", 0)) / 24.0,                         # 9
        float(state.get("production_backlog", 0)) / 5.0,                     # 10
        float(state.get("arc_power_mw", 0.0)) / 200.0,                       # 11
        (float(state.get("power_factor", 0.78)) - 0.6) / 0.35,               # 12
        float(state.get("energy_this_heat_kwh", 0.0)) / 100000.0,            # 13
        float(state.get("electrode_position_mm", 250.0)) / 500.0,            # 14
        float(state.get("electrode_consumption_kg", 0.0)) / 0.2,             # 15
    ]

    # --- Dims 16–31: dynamic pricing features ---
    forecast_prices = _get_forecast_prices(8)  # next 4h at 30-min steps
    p_now = float(state.get("electricity_price", 1.60))
    p_max = max(forecast_prices + [p_now])
    p_min = min(forecast_prices + [p_now])
    # Price trend: slope of first 3 forecast steps
    trend = (forecast_prices[2] - forecast_prices[0]) / 2.0 if len(forecast_prices) >= 3 else 0.0

    pricing_features = [
        _normalize_price(p_now),                                       # live
        _normalize_price(forecast_prices[0]),                          # +30 min (Redis pricing)
        _normalize_price(forecast_prices[1]),                          # +60 min
        _normalize_price(forecast_prices[2]),                          # +90 min
        _normalize_price(forecast_prices[3]),                          # +2 h
        _normalize_price(forecast_prices[4]),                          # +2.5 h
        _normalize_price(forecast_prices[5]),                          # +3 h
        _normalize_price(forecast_prices[6]),                          # +3.5 h
        _normalize_price(forecast_prices[7]),                          # +4 h
        _normalize_price(p_max),                                       # max in next 4h
        _normalize_price(p_min),                                       # min in next 4h
        1.0 if state.get("dr_event_active", False) else 0.0,           # DR active
        float(state.get("dr_payment_rate_norm", 0.0)),                 # DR rate
        1.0 if state.get("capacity_credit_active", False) else 0.0,    # capacity credit
        max(0.0, min(1.0, (trend + 0.5) / 1.0)),                       # price trend slope
        float(state.get("hours_to_peak_norm", 0.5)),                   # hours to next peak
    ]

    # M2 6-D forecast summary (zeros until forecaster is wired).
    if forecast_summary is None:
        forecast_block = [0.0] * FORECAST_SUMMARY_DIM
    else:
        if len(forecast_summary) != FORECAST_SUMMARY_DIM:
            raise ValueError(
                f"forecast_summary must be {FORECAST_SUMMARY_DIM}-D; got {len(forecast_summary)}"
            )
        forecast_block = _normalize_forecast_summary(np.asarray(forecast_summary)).tolist()

    # M3 anomaly score (zero until detector is wired).
    anomaly_block = [float(np.clip(anomaly_score if anomaly_score is not None else 0.0, 0.0, 1.0))]

    vec = core + forecast_block + pricing_features + anomaly_block
    assert len(vec) == OBS_DIM, f"obs dim {len(vec)} != OBS_DIM {OBS_DIM}"
    return np.array(vec, dtype=np.float32).clip(0.0, 1.0)


class OptiTwinEAFEnv:
    """Gymnasium-compatible env. Lightweight stand-in suitable for PPO training.

    Optionally accepts an M2 forecaster and M3 anomaly detector; when supplied,
    the corresponding obs slots are populated from the live model outputs
    instead of zero. The env maintains its own rolling lookback windows so
    callers don't have to.
    """

    metadata = {"render_modes": []}

    # Curriculum tiers (planing-v2.md §11.1). Each tier scales crisis-injection
    # probabilities and adds bookkeeping noise. PPO trains across all three
    # via the curriculum callback in train_ppo.py.
    DIFFICULTY_PROFILES: Dict[str, Dict[str, float]] = {
        "easy":   {"wall_p": 0.000, "grid_p": 0.000, "tx_p": 0.000, "tou": 0.0,  "noise_scale": 0.5},
        "medium": {"wall_p": 0.005, "grid_p": 0.003, "tx_p": 0.002, "tou": 1.0,  "noise_scale": 1.0},
        "hard":   {"wall_p": 0.020, "grid_p": 0.012, "tx_p": 0.008, "tou": 1.0,  "noise_scale": 2.0},
    }

    def __init__(
        self,
        weights: Optional[RewardWeights] = None,
        *,
        forecaster: Optional[Any] = None,
        anomaly_detector: Optional[Any] = None,
        forecast_refresh_every: int = 10,
        difficulty: str = "medium",
    ) -> None:
        if gym is None:
            raise RuntimeError("gymnasium not installed")
        self.weights = weights or RewardWeights()
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(OBS_DIM,), dtype=np.float32)
        self.action_space = spaces.Discrete(len(ACTIONS))
        self._step = 0
        self._max_steps = 480  # 1 simulated day at 3 sim-min steps
        self._state: Dict[str, Any] = {}

        # M2/M3 hooks. Imports are deferred to keep env importable on minimal
        # installs (e.g. when only running the scripted policy).
        self._forecaster = forecaster
        self._anomaly = anomaly_detector
        self._forecast_refresh_every = forecast_refresh_every
        self._forecast_window: Optional[np.ndarray] = None  # (lookback, 7)
        self._anomaly_window: Optional[np.ndarray] = None   # (9, 60)
        self._cached_forecast_summary: Optional[np.ndarray] = None
        self._cached_anomaly_score: float = 0.0

        self.set_difficulty(difficulty)

    def set_difficulty(self, difficulty: str) -> None:
        if difficulty not in self.DIFFICULTY_PROFILES:
            raise ValueError(
                f"unknown difficulty {difficulty!r}; expected one of {list(self.DIFFICULTY_PROFILES)}"
            )
        self.difficulty = difficulty
        self._diff_profile = self.DIFFICULTY_PROFILES[difficulty]

    # Each env step represents 3 sim-minutes; 480 steps ≈ 24 sim-hours.
    SIM_MIN_PER_STEP = 3.0

    # TOU peak window (matches docker-compose TOU_PEAK_START_HOUR/TOU_PEAK_END_HOUR)
    _TOU_PEAK_START_HOUR = 18.0
    _TOU_PEAK_END_HOUR = 22.0
    _TOU_PEAK_RATE_EGP = 2.50
    _TOU_OFFPEAK_RATE_EGP = 1.20

    # Production target matches the simulator's heat duration. With heat progress
    # scaled to `arc_power / 90` per 3-sim-min step, a steady 90 MW arc completes
    # 100 steps = 5 sim-hours per heat → 24 / 5 ≈ 4.8 heats per sim-day. Anything
    # higher than this would require faster heat physics in the simulator. The
    # scripted baseline therefore stays near zero backlog when running nominally
    # and incurs penalty only when arc is dropped below the reference for
    # extended periods.
    HEATS_PER_DAY_TARGET = 4.8
    HEAT_PROGRESS_REFERENCE_ARC_MW = 90.0

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict] = None
              ) -> Tuple[np.ndarray, Dict]:
        self._rng = np.random.default_rng(seed)
        self._step = 0
        # Seed initial sim_hour anywhere in the 24-hour cycle so each episode
        # samples both peak and off-peak periods.
        sim_hour = float(self._rng.uniform(0.0, 24.0))
        # Carry an internal counter so a low-frequency event lasts multiple ticks.
        self._grid_spike_ticks_remaining = 0
        # Track when the current episode "started" on the production clock so
        # backlog is measured against pace-since-reset, not absolute sim_hour.
        self._episode_start_sim_hour = sim_hour
        # Reset rolling lookback windows used by M2/M3.
        if self._forecaster is not None:
            from forecaster import LOOKBACK as _F_LB
            self._forecast_window = np.zeros((_F_LB, 7), dtype=np.float32)
        if self._anomaly is not None:
            self._anomaly_window = np.zeros(
                (self._anomaly.model.channels, self._anomaly.model.window),
                dtype=np.float32,
            )
        self._cached_forecast_summary = None
        self._cached_anomaly_score = 0.0
        self._state = {
            "electricity_price": self._tou_price(sim_hour),
            "is_peak": self._is_peak_hour(sim_hour),
            "sim_hour": sim_hour,
            "tou_mode": True,
            "grid_frequency": 50.0 + float(self._rng.normal(0, 0.05)),
            "furnace_bath_temp": 1300.0 + float(self._rng.uniform(-50, 50)),
            "electrode_temp": 2000.0 + float(self._rng.uniform(-200, 200)),
            "wall_panel_temp": 120.0 + float(self._rng.uniform(-20, 20)),
            "cooling_water_outlet_temp": 35.0,
            "heat_progress_pct": 0.0,
            "current_batch_weight": 180.0,
            "batches_today": 0,
            "production_backlog": 0,
            "arc_power_mw": 90.0,
            "power_factor": 0.78,
            "energy_this_heat_kwh": 0.0,
            "electrode_position_mm": 250.0,
            "electrode_consumption_kg": 0.05,
            "pf_penalty_egp_per_hour_est": 0.0,
            "crisis_flags": {"wall_overheat": False, "grid_spike": False, "transformer_alarm": False},
        }
        return self._make_observation(), {}

    def _state_to_forecast_features(self, s: Dict[str, Any]) -> np.ndarray:
        """Project a state dict into M2's 7-feature input row."""
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
        """Project a state dict into M3's 9-channel telemetry row."""
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

    def _update_model_windows(self) -> None:
        """Roll the M2/M3 lookback windows by one tick from the current state."""
        if self._forecaster is not None and self._forecast_window is not None:
            self._forecast_window = np.roll(self._forecast_window, -1, axis=0)
            self._forecast_window[-1] = self._state_to_forecast_features(self._state)
        if self._anomaly is not None and self._anomaly_window is not None:
            self._anomaly_window = np.roll(self._anomaly_window, -1, axis=1)
            self._anomaly_window[:, -1] = self._state_to_anomaly_channels(self._state)
            # Anomaly score every step (fast and useful per-tick).
            ch_means = self._anomaly.channel_means[:, None]
            ch_stds = self._anomaly.channel_stds[:, None] + 1e-6
            normed = (self._anomaly_window - ch_means) / ch_stds
            self._cached_anomaly_score = self._anomaly.score(normed.astype(np.float32))

    def _refresh_forecast_summary(self) -> None:
        if self._forecaster is None or self._forecast_window is None:
            return
        from forecaster import summarise_for_obs
        price_q, _load = self._forecaster.predict(self._forecast_window)
        self._cached_forecast_summary = summarise_for_obs(price_q)

    def _make_observation(self) -> np.ndarray:
        """Build the 39-D obs from the current state plus cached M2/M3 outputs."""
        return make_obs_vector(
            self._state,
            forecast_summary=self._cached_forecast_summary,
            anomaly_score=self._cached_anomaly_score,
        )

    @classmethod
    def _is_peak_hour(cls, sim_hour: float) -> bool:
        h = sim_hour % 24.0
        return cls._TOU_PEAK_START_HOUR <= h < cls._TOU_PEAK_END_HOUR

    @classmethod
    def _tou_price(cls, sim_hour: float) -> float:
        return cls._TOU_PEAK_RATE_EGP if cls._is_peak_hour(sim_hour) else cls._TOU_OFFPEAK_RATE_EGP

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        s = self._state
        rng = self._rng
        label = ACTIONS[action]

        # Action effects
        if label == "REDUCE_ARC_POWER":
            s["arc_power_mw"] = max(60.0, s["arc_power_mw"] - 10.0)
        elif label == "RAISE_PF_COMPENSATION":
            s["power_factor"] = min(0.94, s["power_factor"] + 0.03)
        elif label == "EMERGENCY_COOLING":
            s["wall_panel_temp"] = max(80.0, s["wall_panel_temp"] - 15.0)
            s["arc_power_mw"] = max(60.0, s["arc_power_mw"] - 10.0)
        elif label == "PRE_PEAK_DROP":
            s["arc_power_mw"] = max(60.0, s["arc_power_mw"] - 20.0)
        elif label == "GRID_RIDE_THROUGH":
            s["arc_power_mw"] = 60.0
        elif label == "TRANSFORMER_DERATE":
            s["arc_power_mw"] = min(75.0, s["arc_power_mw"])
        elif label == "OPTIMIZE_THROUGHPUT":
            if (
                s["wall_panel_temp"] < 185.0
                and s["furnace_bath_temp"] < 1645.0
                and s["grid_frequency"] >= 49.8
            ):
                s["arc_power_mw"] = min(105.0, s["arc_power_mw"] + 8.0)
        elif label == "STABILIZE_PROCESS":
            s["wall_panel_temp"] = max(80.0, s["wall_panel_temp"] - 6.0)
            s["power_factor"] = min(0.94, s["power_factor"] + 0.02)
        elif label == "MAINTENANCE_DERATE":
            s["arc_power_mw"] = max(60.0, s["arc_power_mw"] - 15.0)
            s["wall_panel_temp"] = max(80.0, s["wall_panel_temp"] - 10.0)
        # HOLD_STEADY: no change

        # Advance sim clock + TOU pricing schedule
        s["sim_hour"] = (s["sim_hour"] + self.SIM_MIN_PER_STEP / 60.0) % 24.0
        s["is_peak"] = self._is_peak_hour(s["sim_hour"])
        s["electricity_price"] = self._tou_price(s["sim_hour"])

        # Stochastic crisis injection — gives PPO the chance to learn the rare actions.
        # Probabilities and sensor-noise scale come from the active difficulty profile.
        flags = s["crisis_flags"]
        flags["wall_overheat"] = False
        flags["transformer_alarm"] = False
        prof = self._diff_profile
        noise = float(prof["noise_scale"])

        if rng.random() < prof["wall_p"]:
            s["wall_panel_temp"] = float(s["wall_panel_temp"] + 50.0)
            flags["wall_overheat"] = True
        if rng.random() < prof["grid_p"]:
            self._grid_spike_ticks_remaining = 5
        if self._grid_spike_ticks_remaining > 0:
            s["grid_frequency"] = 49.5 + float(rng.uniform(-0.1, 0.1))
            flags["grid_spike"] = True
            self._grid_spike_ticks_remaining -= 1
        else:
            s["grid_frequency"] = 50.0 + float(rng.normal(0, 0.05 * noise))
            flags["grid_spike"] = False
        if rng.random() < prof["tx_p"]:
            flags["transformer_alarm"] = True

        # Baseline thermal & production dynamics
        s["wall_panel_temp"] = float(s["wall_panel_temp"] + rng.uniform(-1, 3) * noise)
        s["furnace_bath_temp"] = float(
            min(1700.0, s["furnace_bath_temp"] + s["arc_power_mw"] * 0.3 + rng.uniform(-2, 2))
        )
        # Heat progress is now arc-power-driven (was constant +1.0/step). At the
        # 90 MW reference this still produces ~one heat per 60 sim-min; dropping
        # arc power slows the heat → backlog accumulates → PPO actually pays for
        # `REDUCE_ARC_POWER` / `TRANSFORMER_DERATE` abuse.
        progress_increment = s["arc_power_mw"] / self.HEAT_PROGRESS_REFERENCE_ARC_MW
        s["heat_progress_pct"] = min(100.0, s["heat_progress_pct"] + progress_increment)
        s["energy_this_heat_kwh"] += s["arc_power_mw"] * 1000.0 / 60.0

        # Heat completion → bump batches_today and reset per-heat counters.
        if s["heat_progress_pct"] >= 100.0:
            s["batches_today"] = int(s["batches_today"]) + 1
            s["heat_progress_pct"] = 0.0
            s["energy_this_heat_kwh"] = 0.0
            # Bath cools when slag/steel is tapped; fresh charge brings it back down
            s["furnace_bath_temp"] = float(s["furnace_bath_temp"] - 80.0)
            # Electrode wear ticks up per heat; the consumption rate floats around 0.05
            s["electrode_consumption_kg"] = float(
                min(0.2, s["electrode_consumption_kg"] + rng.uniform(0.005, 0.015))
            )

        # Production backlog: how many heats *should* have completed by now vs how
        # many actually did. Linear in elapsed sim-time since reset.
        elapsed_h = (s["sim_hour"] - self._episode_start_sim_hour) % 24.0
        expected = elapsed_h / 24.0 * self.HEATS_PER_DAY_TARGET
        s["production_backlog"] = max(0, int(round(expected)) - int(s["batches_today"]))

        # PF penalty estimate (uses current TOU price, not hardcoded 1.60)
        if s["arc_power_mw"] * 1000.0 > 500.0 and s["power_factor"] < 0.92:
            deficit = 0.92 - s["power_factor"]
            s["pf_penalty_egp_per_hour_est"] = deficit * s["arc_power_mw"] * 1000.0 * s["electricity_price"] * 0.05
        else:
            s["pf_penalty_egp_per_hour_est"] = 0.0

        rc = compute_reward(s, self.weights, baseline_arc_power_mw=100.0)

        # Training-time-only crisis-violation penalties.
        # The user-facing reward in agent.py omits these (KPI display only).
        # Without them, PPO has no gradient to keep GRID_RIDE_THROUGH /
        # TRANSFORMER_DERATE alive after BC warm-start drifts under entropy.
        crisis_penalty = 0.0
        if flags["grid_spike"] and s["arc_power_mw"] > 65.0:
            crisis_penalty -= 50.0
        if flags["transformer_alarm"] and s["arc_power_mw"] > 80.0:
            crisis_penalty -= 50.0
        if flags["wall_overheat"] and s["arc_power_mw"] > 80.0:
            crisis_penalty -= 30.0

        total = rc.total + crisis_penalty

        self._step += 1
        terminated = s["heat_progress_pct"] >= 100.0
        truncated = self._step >= self._max_steps

        # Update M2/M3 caches AFTER state mutation so they reflect the new tick.
        self._update_model_windows()
        if (
            self._forecaster is not None
            and self._step % self._forecast_refresh_every == 0
        ):
            self._refresh_forecast_summary()

        return self._make_observation(), total, terminated, truncated, {"reward_components": rc.as_dict()}
