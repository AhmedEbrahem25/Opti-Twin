"""
OptiTwinEAFEnv — custom Gymnasium environment for training the PPO agent.

State (32-D): normalized to [0, 1].
  Dims 0–15:  original telemetry features
  Dims 16–31: dynamic pricing features (live price + 8-step forecast + DR state)

Action: 5-action discrete space.
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
]

OBS_DIM = 32  # extended from 16 with dynamic pricing features

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


def make_obs_vector(state: Dict[str, Any]) -> np.ndarray:
    """Map a telemetry dict to a normalized 32-D observation vector."""
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
        _normalize_price(p_now),                    # 16: live price
        _normalize_price(forecast_prices[0]),        # 17: +30 min
        _normalize_price(forecast_prices[1]),        # 18: +60 min
        _normalize_price(forecast_prices[2]),        # 19: +90 min
        _normalize_price(forecast_prices[3]),        # 20: +2h
        _normalize_price(forecast_prices[4]),        # 21: +2.5h
        _normalize_price(forecast_prices[5]),        # 22: +3h
        _normalize_price(forecast_prices[6]),        # 23: +3.5h
        _normalize_price(forecast_prices[7]),        # 24: +4h
        _normalize_price(p_max),                     # 25: max in next 4h
        _normalize_price(p_min),                     # 26: min in next 4h
        1.0 if state.get("dr_event_active", False) else 0.0,   # 27: DR active
        float(state.get("dr_payment_rate_norm", 0.0)),          # 28: DR rate
        1.0 if state.get("capacity_credit_active", False) else 0.0,  # 29
        max(0.0, min(1.0, (trend + 0.5) / 1.0)),   # 30: price trend slope
        float(state.get("hours_to_peak_norm", 0.5)), # 31: time to next peak
    ]

    return np.array(core + pricing_features, dtype=np.float32).clip(0.0, 1.0)


class OptiTwinEAFEnv:
    """Gymnasium-compatible env. Lightweight stand-in suitable for PPO training."""

    metadata = {"render_modes": []}

    def __init__(self, weights: Optional[RewardWeights] = None) -> None:
        if gym is None:
            raise RuntimeError("gymnasium not installed")
        self.weights = weights or RewardWeights()
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(OBS_DIM,), dtype=np.float32)
        self.action_space = spaces.Discrete(len(ACTIONS))
        self._step = 0
        self._max_steps = 480  # 1 simulated day at 3 sim-min steps
        self._state: Dict[str, Any] = {}

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict] = None
              ) -> Tuple[np.ndarray, Dict]:
        rng = np.random.default_rng(seed)
        self._step = 0
        self._state = {
            "electricity_price": 1.60,
            "is_peak": False,
            "grid_frequency": 50.0 + float(rng.normal(0, 0.05)),
            "furnace_bath_temp": 1300.0 + float(rng.uniform(-50, 50)),
            "electrode_temp": 2000.0 + float(rng.uniform(-200, 200)),
            "wall_panel_temp": 120.0 + float(rng.uniform(-20, 20)),
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
        }
        return make_obs_vector(self._state), {}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        s = self._state
        label = ACTIONS[action]

        # Action effects
        if label == "REDUCE_ARC_POWER":
            s["arc_power_mw"] = max(60.0, s["arc_power_mw"] - 10.0)
        elif label == "RAISE_PF_COMPENSATION":
            s["power_factor"] = min(0.94, s["power_factor"] + 0.03)
        elif label == "EMERGENCY_COOLING":
            s["wall_panel_temp"] = max(80.0, s["wall_panel_temp"] - 15.0)
        elif label == "PRE_PEAK_DROP":
            s["arc_power_mw"] = max(60.0, s["arc_power_mw"] - 20.0)
        # HOLD_STEADY: no change

        # Stochastic environment dynamics
        rng = np.random.default_rng()
        s["wall_panel_temp"] = float(s["wall_panel_temp"] + rng.uniform(-1, 3))
        s["furnace_bath_temp"] = float(
            min(1700.0, s["furnace_bath_temp"] + s["arc_power_mw"] * 0.3 + rng.uniform(-2, 2))
        )
        s["heat_progress_pct"] = min(100.0, s["heat_progress_pct"] + 1.0)
        s["energy_this_heat_kwh"] += s["arc_power_mw"] * 1000.0 / 60.0

        # PF penalty estimate
        if s["arc_power_mw"] * 1000.0 > 500.0 and s["power_factor"] < 0.92:
            deficit = 0.92 - s["power_factor"]
            s["pf_penalty_egp_per_hour_est"] = deficit * s["arc_power_mw"] * 1000.0 * 1.60 * 0.05
        else:
            s["pf_penalty_egp_per_hour_est"] = 0.0

        rc = compute_reward(s, self.weights, baseline_arc_power_mw=100.0)

        self._step += 1
        terminated = s["heat_progress_pct"] >= 100.0
        truncated = self._step >= self._max_steps

        return make_obs_vector(s), rc.total, terminated, truncated, {"reward_components": rc.as_dict()}
