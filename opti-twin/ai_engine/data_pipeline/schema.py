"""Pydantic schema for one transition record (planing-v2.md §3.2).

A row written to `data/raw/episode_{seed}.parquet` describes one env step:
  - the 16-D telemetry observation,
  - the action that the (scripted or trained) policy chose,
  - the reward components that resulted,
  - episode/step metadata.

`featurize.py` consumes these rows; `split.py` partitions by episode.
"""

from __future__ import annotations

from typing import Dict, Literal

from pydantic import BaseModel, Field

Difficulty = Literal["easy", "medium", "hard"]


class TransitionRecord(BaseModel):
    """One environment transition. Field names match `environment._state` keys
    so the collector can pass `**state` straight through."""

    # Episode / step metadata
    episode_id: int
    step_id: int
    difficulty: Difficulty
    ts: float = Field(description="Unix timestamp at write")
    sim_hour: float

    # Telemetry (16-D observation, pre-normalisation)
    arc_power_mw: float
    furnace_bath_temp: float
    wall_panel_temp: float
    electrode_temp: float
    cooling_water_outlet_temp: float
    heat_progress_pct: float
    current_batch_weight: float
    batches_today: int
    production_backlog: int
    power_factor: float
    energy_this_heat_kwh: float
    electrode_position_mm: float
    electrode_consumption_kg: float
    electricity_price: float
    is_peak: bool
    grid_frequency: float
    tou_mode: bool

    # Action
    action_label: str
    action_id: int

    # Reward
    reward_total: float
    reward_components: Dict[str, float]

    # Crisis flags (booleans, recorded for anomaly-detector training filter)
    crisis_wall_overheat: bool
    crisis_grid_spike: bool
    crisis_transformer_alarm: bool

    @classmethod
    def from_state(
        cls,
        state: Dict,
        *,
        episode_id: int,
        step_id: int,
        difficulty: Difficulty,
        ts: float,
        action_label: str,
        action_id: int,
        reward_total: float,
        reward_components: Dict[str, float],
    ) -> "TransitionRecord":
        flags = state.get("crisis_flags", {})
        return cls(
            episode_id=episode_id,
            step_id=step_id,
            difficulty=difficulty,
            ts=ts,
            sim_hour=float(state.get("sim_hour", 0.0)),
            arc_power_mw=float(state.get("arc_power_mw", 0.0)),
            furnace_bath_temp=float(state.get("furnace_bath_temp", 0.0)),
            wall_panel_temp=float(state.get("wall_panel_temp", 0.0)),
            electrode_temp=float(state.get("electrode_temp", 0.0)),
            cooling_water_outlet_temp=float(state.get("cooling_water_outlet_temp", 0.0)),
            heat_progress_pct=float(state.get("heat_progress_pct", 0.0)),
            current_batch_weight=float(state.get("current_batch_weight", 0.0)),
            batches_today=int(state.get("batches_today", 0)),
            production_backlog=int(state.get("production_backlog", 0)),
            power_factor=float(state.get("power_factor", 0.0)),
            energy_this_heat_kwh=float(state.get("energy_this_heat_kwh", 0.0)),
            electrode_position_mm=float(state.get("electrode_position_mm", 0.0)),
            electrode_consumption_kg=float(state.get("electrode_consumption_kg", 0.0)),
            electricity_price=float(state.get("electricity_price", 1.60)),
            is_peak=bool(state.get("is_peak", False)),
            grid_frequency=float(state.get("grid_frequency", 50.0)),
            tou_mode=bool(state.get("tou_mode", False)),
            action_label=action_label,
            action_id=action_id,
            reward_total=float(reward_total),
            reward_components=dict(reward_components),
            crisis_wall_overheat=bool(flags.get("wall_overheat", False)),
            crisis_grid_spike=bool(flags.get("grid_spike", False)),
            crisis_transformer_alarm=bool(flags.get("transformer_alarm", False)),
        )


# Channels used by the M3 anomaly autoencoder (planing-v2.md §7.2: 9 thermal/electrical channels).
ANOMALY_CHANNELS = [
    "arc_power_mw",
    "furnace_bath_temp",
    "wall_panel_temp",
    "electrode_temp",
    "cooling_water_outlet_temp",
    "power_factor",
    "energy_this_heat_kwh",
    "electrode_consumption_kg",
    "grid_frequency",
]

# Channels used by the M2 forecaster (planing-v2.md §6.1).
FORECASTER_INPUT_CHANNELS = [
    "electricity_price",
    "arc_power_mw",
    "is_peak",
    "tou_mode",
    "sim_hour_sin",   # derived in featurize.py
    "sim_hour_cos",   # derived in featurize.py
    "grid_frequency",
]
