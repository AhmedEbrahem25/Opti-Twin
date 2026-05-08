"""
Safety / action-masking layer.

Sits between the policy output (PPO or scripted fallback) and the
recommendation publish path. Enforces hard physical limits regardless of what
the policy chose. Mirrors planing-v2.md §13.1.

Design notes:
  - Action mask returns the (possibly overridden) action label plus a flag and
    a machine-readable reason code. The reason code drives operator-facing
    messaging in the dashboard / XAI prompt.
  - Setpoint clamps mirror the simulator-side clamps in
    `simulator/machines/eaf_machine.py:158–160`. We apply them earlier so the
    operator-visible `arc_power_mw` / `cooling_lmin` / `reactive_comp_mvar`
    values match exactly what the simulator will execute.
  - The compose env vars `EAF_MIN_POWER_MW`, `EAF_MAX_POWER_MW`,
    `FURNACE_MAX_WALL_TEMP` define the physical envelope.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

# Physical envelope (overridable via env vars to match simulator config)
EAF_MIN_POWER_MW = float(os.getenv("EAF_MIN_POWER_MW", "60"))
EAF_MAX_POWER_MW = float(os.getenv("EAF_MAX_POWER_MW", "110"))
FURNACE_MAX_WALL_TEMP = float(os.getenv("FURNACE_MAX_WALL_TEMP", "250"))

COOLING_MIN_LMIN = 100.0
COOLING_MAX_LMIN = 400.0
REACTIVE_COMP_MAX_MVAR = 30.0

# Thresholds — keep colocated for readability
GRID_FREQ_RIDE_THROUGH_HZ = 49.7
BATH_FREEZE_RISK_C = 1500.0
MAX_OPTIMIZE_WALL_TEMP_C = 190.0
MAX_OPTIMIZE_BATH_TEMP_C = 1648.0
MAX_OPTIMIZE_MAINTENANCE_RISK = 0.35


# Reason codes — short stable identifiers; the dashboard / XAI prompt maps
# these to operator-visible bilingual messages.
class MaskReason:
    NONE = None
    WALL_OVER_LIMIT = "wall_over_limit"
    BATH_FREEZE_RISK = "bath_freeze_risk"
    GRID_FREQ_LOW = "grid_freq_low"
    TRANSFORMER_ALARM = "transformer_alarm"
    MAINTENANCE_RISK = "maintenance_risk"
    OPTIMIZATION_LIMIT = "optimization_limit"


@dataclass
class MaskResult:
    label: str
    overridden: bool
    reason: Optional[str]


def apply_action_mask(label: str, state: Dict[str, Any]) -> MaskResult:
    """Return the (possibly overridden) action label per planing-v2.md §13.1.

    Order matters — earlier rules take priority over later ones:
      1. Wall over limit  -> EMERGENCY_COOLING
      2. Grid freq low    -> GRID_RIDE_THROUGH
      3. Transformer alarm-> TRANSFORMER_DERATE
      4. Bath freeze risk -> HOLD_STEADY (only blocks downward power moves)
    """
    wall = float(state.get("wall_panel_temp", 0.0))
    if wall >= FURNACE_MAX_WALL_TEMP:
        if label != "EMERGENCY_COOLING":
            return MaskResult("EMERGENCY_COOLING", True, MaskReason.WALL_OVER_LIMIT)
        return MaskResult(label, False, MaskReason.NONE)

    freq = float(state.get("grid_frequency", 50.0))
    if freq < GRID_FREQ_RIDE_THROUGH_HZ:
        if label != "GRID_RIDE_THROUGH":
            return MaskResult("GRID_RIDE_THROUGH", True, MaskReason.GRID_FREQ_LOW)
        return MaskResult(label, False, MaskReason.NONE)

    if state.get("crisis_flags", {}).get("transformer_alarm"):
        if label != "TRANSFORMER_DERATE":
            return MaskResult("TRANSFORMER_DERATE", True, MaskReason.TRANSFORMER_ALARM)
        return MaskResult(label, False, MaskReason.NONE)

    bath = float(state.get("furnace_bath_temp", 1600.0))
    if bath < BATH_FREEZE_RISK_C and label in ("REDUCE_ARC_POWER", "PRE_PEAK_DROP"):
        return MaskResult("HOLD_STEADY", True, MaskReason.BATH_FREEZE_RISK)
    if bath < BATH_FREEZE_RISK_C and label == "MAINTENANCE_DERATE":
        return MaskResult("STABILIZE_PROCESS", True, MaskReason.BATH_FREEZE_RISK)

    maintenance_risk = float(state.get("maintenance_risk_score", 0.0))
    if maintenance_risk >= 0.65 and label in (
        "OPTIMIZE_THROUGHPUT",
        "REDUCE_IDLE_TIME",
        "STABILIZE_PROCESS",
    ):
        return MaskResult("MAINTENANCE_DERATE", True, MaskReason.MAINTENANCE_RISK)

    if label == "OPTIMIZE_THROUGHPUT":
        if (
            wall >= MAX_OPTIMIZE_WALL_TEMP_C
            or bath >= MAX_OPTIMIZE_BATH_TEMP_C
            or maintenance_risk >= MAX_OPTIMIZE_MAINTENANCE_RISK
        ):
            return MaskResult("STABILIZE_PROCESS", True, MaskReason.OPTIMIZATION_LIMIT)

    return MaskResult(label, False, MaskReason.NONE)


def clamp_setpoints(
    arc_power_mw: Optional[float],
    cooling_lmin: Optional[float],
    reactive_comp_mvar: Optional[float],
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Clamp continuous setpoints into the physical envelope. None passes through."""
    if arc_power_mw is not None:
        arc_power_mw = max(EAF_MIN_POWER_MW, min(EAF_MAX_POWER_MW, float(arc_power_mw)))
    if cooling_lmin is not None:
        cooling_lmin = max(COOLING_MIN_LMIN, min(COOLING_MAX_LMIN, float(cooling_lmin)))
    if reactive_comp_mvar is not None:
        reactive_comp_mvar = max(0.0, min(REACTIVE_COMP_MAX_MVAR, float(reactive_comp_mvar)))
    return arc_power_mw, cooling_lmin, reactive_comp_mvar
