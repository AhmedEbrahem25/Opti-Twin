"""
EAF heat-phase state machine.

Phases (industry-typical for modern UHP EAF):
    1. CHARGING            — scrap/DRI loaded; arc off                  (~5 min)
    2. BORE_DOWN           — arcs ignite, drilling channels             (~10 min)
    3. MELTING_PHASE_1     — bulk melting; max power                    (~15 min)
    4. MELTING_PHASE_2     — flat bath forming; oxygen peaks            (~15 min)
    5. REFINING            — temperature trim to 1,630 °C; chemistry    (~10 min)
    6. TAPPING             — pour to ladle; furnace tilts               (~5 min)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import random

from .eaf_thermal_model import (
    ThermalInputs,
    update_bath_temp,
    update_wall_temp,
    update_electrode_temp,
    update_cooling_outlet,
)


class HeatPhase(str, Enum):
    CHARGING = "CHARGING"
    BORE_DOWN = "BORE_DOWN"
    MELTING_PHASE_1 = "MELTING_PHASE_1"
    MELTING_PHASE_2 = "MELTING_PHASE_2"
    REFINING = "REFINING"
    TAPPING = "TAPPING"
    IDLE = "IDLE"


PHASE_DURATIONS_MIN = {
    HeatPhase.CHARGING: 5,
    HeatPhase.BORE_DOWN: 10,
    HeatPhase.MELTING_PHASE_1: 15,
    HeatPhase.MELTING_PHASE_2: 15,
    HeatPhase.REFINING: 10,
    HeatPhase.TAPPING: 5,
}

PHASE_POWER_PROFILE_MW = {
    HeatPhase.CHARGING: 0.0,
    HeatPhase.BORE_DOWN: 70.0,
    HeatPhase.MELTING_PHASE_1: 100.0,
    HeatPhase.MELTING_PHASE_2: 95.0,
    HeatPhase.REFINING: 60.0,
    HeatPhase.TAPPING: 0.0,
    HeatPhase.IDLE: 0.0,
}

PHASE_OXYGEN_PROFILE_M3HR = {
    HeatPhase.CHARGING: 0.0,
    HeatPhase.BORE_DOWN: 100.0,
    HeatPhase.MELTING_PHASE_1: 350.0,
    HeatPhase.MELTING_PHASE_2: 450.0,
    HeatPhase.REFINING: 150.0,
    HeatPhase.TAPPING: 0.0,
    HeatPhase.IDLE: 0.0,
}


@dataclass
class EAFState:
    machine_id: str = "EAF_02_EZZ_AIN_SOKHNA"
    factory: str = "Ezz Flat Steel — Ain Sokhna Complex"
    manufacturer: str = "Danieli"
    rated_capacity_tpa: int = 1_600_000
    furnace_size_t: int = 185

    # Current phase state
    phase: HeatPhase = HeatPhase.CHARGING
    phase_elapsed_min: float = 0.0
    heat_progress_pct: float = 0.0

    # Production
    batches_today: int = 0
    production_backlog: int = 0
    current_batch_weight: float = 180.0

    # Thermal
    bath_temp_c: float = 1250.0
    wall_panel_temp_c: float = 110.0
    electrode_temp_c: float = 1500.0
    cooling_water_outlet_c: float = 35.0

    # Electrical
    arc_power_mw: float = 0.0
    power_factor: float = 0.78  # uncompensated EAF typical
    energy_this_heat_kwh: float = 0.0
    energy_kwh_today: float = 0.0
    grid_frequency_hz: float = 50.00

    # Electrodes
    electrode_position_mm: float = 250.0
    electrode_consumption_rate_kg_per_min: float = 0.0
    electrode_consumption_today_kg: float = 0.0

    # Inputs (controllable)
    oxygen_injection_m3hr: float = 0.0
    cooling_water_flow_lmin: float = 200.0
    reactive_power_comp_mvar: float = 0.0
    tap_changer_position: int = 12

    # Override flag — set by AI agent recommendations
    ai_active: bool = False
    ai_arc_power_setpoint_mw: Optional[float] = None
    ai_cooling_lmin: Optional[float] = None
    ai_reactive_comp_mvar: Optional[float] = None

    # Crisis flags (set by event injectors)
    crisis_wall_overheat: bool = False
    crisis_electrode_break: bool = False
    crisis_grid_spike: bool = False
    crisis_transformer_alarm: bool = False


class EAFMachine:
    """Drives a single EAF through its heat phase cycle."""

    def __init__(self, state: Optional[EAFState] = None) -> None:
        self.state = state or EAFState()
        self.phase_order = [
            HeatPhase.CHARGING,
            HeatPhase.BORE_DOWN,
            HeatPhase.MELTING_PHASE_1,
            HeatPhase.MELTING_PHASE_2,
            HeatPhase.REFINING,
            HeatPhase.TAPPING,
        ]

    # ---- Crisis injection API ----
    def inject_event(self, event: str) -> None:
        if event == "wall_overheat":
            self.state.crisis_wall_overheat = True
        elif event == "electrode_break":
            self.state.crisis_electrode_break = True
        elif event == "grid_spike":
            self.state.crisis_grid_spike = True
        elif event == "transformer_alarm":
            self.state.crisis_transformer_alarm = True

    # ---- AI override API ----
    def apply_ai_recommendation(
        self,
        arc_power_mw: Optional[float] = None,
        cooling_lmin: Optional[float] = None,
        reactive_comp_mvar: Optional[float] = None,
    ) -> None:
        self.state.ai_active = True
        if arc_power_mw is not None:
            self.state.ai_arc_power_setpoint_mw = max(60.0, min(110.0, arc_power_mw))
        if cooling_lmin is not None:
            self.state.ai_cooling_lmin = max(100.0, min(400.0, cooling_lmin))
        if reactive_comp_mvar is not None:
            self.state.ai_reactive_comp_mvar = max(0.0, min(30.0, reactive_comp_mvar))

    def clear_ai(self) -> None:
        self.state.ai_active = False
        self.state.ai_arc_power_setpoint_mw = None
        self.state.ai_cooling_lmin = None
        self.state.ai_reactive_comp_mvar = None

    # ---- Phase progression ----
    def _advance_phase(self) -> None:
        idx = self.phase_order.index(self.state.phase)
        if idx + 1 < len(self.phase_order):
            self.state.phase = self.phase_order[idx + 1]
            self.state.phase_elapsed_min = 0.0
        else:
            # Tap finished → next heat
            self.state.batches_today += 1
            self.state.energy_this_heat_kwh = 0.0
            self.state.phase = HeatPhase.CHARGING
            self.state.phase_elapsed_min = 0.0
            self.state.bath_temp_c = max(1250.0, self.state.bath_temp_c - 200.0)
            self.state.heat_progress_pct = 0.0
            # New scrap/DRI charge
            self.state.current_batch_weight = 180.0 + random.uniform(-3, 3)

    # ---- Per-tick step ----
    def step(self, dt_seconds: float, sim_minutes_per_real_second: float = 15.0) -> None:
        s = self.state
        sim_dt_min = (dt_seconds * sim_minutes_per_real_second) / 60.0

        # Determine baseline arc power from phase profile, possibly overridden by AI
        baseline_power = PHASE_POWER_PROFILE_MW[s.phase]
        if s.ai_active and s.ai_arc_power_setpoint_mw is not None and baseline_power > 0:
            target_power = min(baseline_power, s.ai_arc_power_setpoint_mw)
        else:
            target_power = baseline_power

        # Crisis: grid spike caps power
        if s.crisis_grid_spike:
            target_power = min(target_power, 60.0)
            s.grid_frequency_hz = 49.6 + random.uniform(-0.05, 0.05)
        else:
            s.grid_frequency_hz = 50.0 + random.uniform(-0.05, 0.05)

        # Crisis: transformer alarm reduces allowed MVA
        if s.crisis_transformer_alarm:
            target_power = min(target_power, 75.0)

        # Smooth power transitions (no instantaneous step changes)
        s.arc_power_mw += (target_power - s.arc_power_mw) * 0.4
        s.arc_power_mw = max(0.0, s.arc_power_mw)

        # Oxygen injection — phase-driven
        target_o2 = PHASE_OXYGEN_PROFILE_M3HR[s.phase]
        s.oxygen_injection_m3hr += (target_o2 - s.oxygen_injection_m3hr) * 0.3

        # Cooling water — AI-overridable; default proportional to arc power
        if s.ai_active and s.ai_cooling_lmin is not None:
            target_cool = s.ai_cooling_lmin
        elif s.crisis_wall_overheat:
            target_cool = 350.0
        else:
            target_cool = 150.0 + s.arc_power_mw * 1.5
        s.cooling_water_flow_lmin += (target_cool - s.cooling_water_flow_lmin) * 0.5

        # Reactive power compensation
        if s.ai_active and s.ai_reactive_comp_mvar is not None:
            s.reactive_power_comp_mvar = s.ai_reactive_comp_mvar

        # Power factor — improves with reactive comp
        base_pf = 0.78
        pf_uplift = (s.reactive_power_comp_mvar / 30.0) * 0.16  # up to +0.16
        s.power_factor = min(0.95, base_pf + pf_uplift)
        # Worse PF during heavy melting if uncompensated
        if s.phase in (HeatPhase.MELTING_PHASE_1, HeatPhase.MELTING_PHASE_2) and s.reactive_power_comp_mvar < 5:
            s.power_factor = max(0.72, s.power_factor - 0.04)

        # Thermal updates
        thermal_in = ThermalInputs(
            arc_power_mw=s.arc_power_mw,
            batch_weight_t=s.current_batch_weight,
            oxygen_m3hr=s.oxygen_injection_m3hr,
            cooling_lmin=s.cooling_water_flow_lmin,
        )
        s.bath_temp_c = update_bath_temp(s.bath_temp_c, thermal_in, dt_seconds * sim_minutes_per_real_second / 1.0)
        s.wall_panel_temp_c = update_wall_temp(
            s.wall_panel_temp_c, s.arc_power_mw, s.cooling_water_flow_lmin,
            dt_seconds * sim_minutes_per_real_second / 1.0,
        )
        # Crisis: wall overheat — force ramp-up
        if s.crisis_wall_overheat and s.wall_panel_temp_c < 230:
            s.wall_panel_temp_c += 8.0
        # If wall has cooled back below 180, clear the crisis
        if s.crisis_wall_overheat and s.wall_panel_temp_c < 180:
            s.crisis_wall_overheat = False

        s.electrode_temp_c = update_electrode_temp(
            s.electrode_temp_c, s.arc_power_mw, dt_seconds * sim_minutes_per_real_second / 1.0,
        )
        s.cooling_water_outlet_c = update_cooling_outlet(
            35.0, s.cooling_water_flow_lmin, s.arc_power_mw,
            dt_seconds * sim_minutes_per_real_second / 1.0,
        )

        # Energy accumulation
        # Energy (kWh) added in this real-time tick = power (MW) × sim_hours
        sim_hours_this_tick = (dt_seconds * sim_minutes_per_real_second) / 60.0
        kwh_added = s.arc_power_mw * 1000.0 * sim_hours_this_tick
        s.energy_this_heat_kwh += kwh_added
        s.energy_kwh_today += kwh_added

        # Electrode consumption — modern UHP baseline ~1.7 kg/t × melt phase intensity
        if s.phase in (HeatPhase.BORE_DOWN, HeatPhase.MELTING_PHASE_1, HeatPhase.MELTING_PHASE_2):
            base_rate = 0.05  # kg/min
            crisis_mult = 3.0 if s.crisis_electrode_break else 1.0
            s.electrode_consumption_rate_kg_per_min = base_rate * crisis_mult
            s.electrode_consumption_today_kg += s.electrode_consumption_rate_kg_per_min * sim_dt_min
        else:
            s.electrode_consumption_rate_kg_per_min = 0.0

        # Phase progression
        s.phase_elapsed_min += sim_dt_min
        phase_total = PHASE_DURATIONS_MIN[s.phase]
        if s.phase_elapsed_min >= phase_total:
            self._advance_phase()

        # Heat progress
        idx = self.phase_order.index(s.phase) if s.phase in self.phase_order else 0
        total_heat_min = sum(PHASE_DURATIONS_MIN[p] for p in self.phase_order)
        elapsed_so_far = sum(PHASE_DURATIONS_MIN[p] for p in self.phase_order[:idx]) + s.phase_elapsed_min
        s.heat_progress_pct = min(100.0, (elapsed_so_far / total_heat_min) * 100.0)
