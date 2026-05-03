"""Unit tests for the safety / action-masking layer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make ai_engine importable when running pytest from repo root or this dir
HERE = Path(__file__).resolve().parent
AI_ENGINE = HERE.parent
sys.path.insert(0, str(AI_ENGINE))

from safety import (  # noqa: E402
    BATH_FREEZE_RISK_C,
    EAF_MAX_POWER_MW,
    EAF_MIN_POWER_MW,
    FURNACE_MAX_WALL_TEMP,
    GRID_FREQ_RIDE_THROUGH_HZ,
    MaskReason,
    apply_action_mask,
    clamp_setpoints,
)


# --- Helpers --------------------------------------------------------------

def _safe_state(**overrides):
    """A state dict with all telemetry inside the safe envelope."""
    base = {
        "wall_panel_temp": 150.0,
        "furnace_bath_temp": 1620.0,
        "grid_frequency": 50.0,
        "crisis_flags": {"wall_overheat": False, "grid_spike": False, "transformer_alarm": False},
    }
    base.update(overrides)
    return base


# --- apply_action_mask ----------------------------------------------------

def test_safe_state_passes_through_unchanged():
    res = apply_action_mask("HOLD_STEADY", _safe_state())
    assert res.label == "HOLD_STEADY"
    assert res.overridden is False
    assert res.reason is None


def test_wall_over_limit_forces_emergency_cooling():
    state = _safe_state(wall_panel_temp=FURNACE_MAX_WALL_TEMP + 10)
    res = apply_action_mask("HOLD_STEADY", state)
    assert res.label == "EMERGENCY_COOLING"
    assert res.overridden is True
    assert res.reason == MaskReason.WALL_OVER_LIMIT


def test_wall_over_limit_with_already_correct_action_not_marked_overridden():
    state = _safe_state(wall_panel_temp=FURNACE_MAX_WALL_TEMP + 10)
    res = apply_action_mask("EMERGENCY_COOLING", state)
    assert res.label == "EMERGENCY_COOLING"
    assert res.overridden is False


def test_low_grid_frequency_forces_ride_through():
    state = _safe_state(grid_frequency=GRID_FREQ_RIDE_THROUGH_HZ - 0.1)
    res = apply_action_mask("REDUCE_ARC_POWER", state)
    assert res.label == "GRID_RIDE_THROUGH"
    assert res.overridden is True
    assert res.reason == MaskReason.GRID_FREQ_LOW


def test_transformer_alarm_forces_derate():
    state = _safe_state(crisis_flags={"transformer_alarm": True})
    res = apply_action_mask("HOLD_STEADY", state)
    assert res.label == "TRANSFORMER_DERATE"
    assert res.overridden is True
    assert res.reason == MaskReason.TRANSFORMER_ALARM


def test_bath_freeze_blocks_power_drops_only():
    state = _safe_state(furnace_bath_temp=BATH_FREEZE_RISK_C - 50)

    # Downward power moves are blocked
    res = apply_action_mask("REDUCE_ARC_POWER", state)
    assert res.label == "HOLD_STEADY"
    assert res.overridden is True
    assert res.reason == MaskReason.BATH_FREEZE_RISK

    res = apply_action_mask("PRE_PEAK_DROP", state)
    assert res.label == "HOLD_STEADY"
    assert res.overridden is True

    # PF compensation is fine — doesn't cool the bath further
    res = apply_action_mask("RAISE_PF_COMPENSATION", state)
    assert res.label == "RAISE_PF_COMPENSATION"
    assert res.overridden is False


def test_priority_wall_over_grid():
    """When both fire, wall override wins (it's a faster-failing equipment risk)."""
    state = _safe_state(
        wall_panel_temp=FURNACE_MAX_WALL_TEMP + 10,
        grid_frequency=GRID_FREQ_RIDE_THROUGH_HZ - 0.1,
    )
    res = apply_action_mask("HOLD_STEADY", state)
    assert res.label == "EMERGENCY_COOLING"


# --- clamp_setpoints ------------------------------------------------------

def test_clamp_arc_power_within_envelope():
    arc, _, _ = clamp_setpoints(EAF_MIN_POWER_MW + 5, None, None)
    assert arc == EAF_MIN_POWER_MW + 5

    arc, _, _ = clamp_setpoints(EAF_MIN_POWER_MW - 10, None, None)
    assert arc == EAF_MIN_POWER_MW

    arc, _, _ = clamp_setpoints(EAF_MAX_POWER_MW + 50, None, None)
    assert arc == EAF_MAX_POWER_MW


def test_clamp_cooling_within_envelope():
    _, cool, _ = clamp_setpoints(None, 50.0, None)
    assert cool == 100.0

    _, cool, _ = clamp_setpoints(None, 500.0, None)
    assert cool == 400.0

    _, cool, _ = clamp_setpoints(None, 250.0, None)
    assert cool == 250.0


def test_clamp_reactive_within_envelope():
    _, _, comp = clamp_setpoints(None, None, -5.0)
    assert comp == 0.0

    _, _, comp = clamp_setpoints(None, None, 50.0)
    assert comp == 30.0

    _, _, comp = clamp_setpoints(None, None, 15.0)
    assert comp == 15.0


def test_clamp_passes_none_through():
    arc, cool, comp = clamp_setpoints(None, None, None)
    assert arc is None and cool is None and comp is None
