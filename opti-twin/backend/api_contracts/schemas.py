"""
Pydantic schemas — single source of truth for API contracts.
Aligned with simulator telemetry payload (§8.2 of plan.md).
"""

from datetime import datetime
from typing import Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class CrisisFlags(BaseModel):
    wall_overheat: bool = False
    electrode_break: bool = False
    grid_spike: bool = False
    transformer_alarm: bool = False


class TelemetryInput(BaseModel):
    model_config = ConfigDict(extra="allow")  # tolerate forward-compatible fields

    machine_id: str
    machine_type: str = "Electric Arc Furnace"
    factory: str
    manufacturer: Optional[str] = "Danieli"
    rated_capacity_tpa: Optional[int] = None
    timestamp: datetime
    sim_hour: Optional[float] = None

    # Electrical
    arc_power_mw: float = Field(ge=0, le=250)
    energy_kwh: float = Field(ge=0)
    energy_this_heat_kwh: float = Field(ge=0)
    power_factor: float = Field(ge=0, le=1)
    pf_penalty_bracket: bool = False
    pf_penalty_egp_per_hour_est: float = 0.0
    reactive_power_comp_mvar: float = 0.0
    tap_changer_position: int = 12

    # Thermal
    furnace_bath_temp: float = Field(ge=0, le=1700)
    electrode_temp: float = Field(ge=0, le=3000)
    wall_panel_temp: float = Field(ge=0, le=300)
    cooling_water_outlet_temp: float = 35.0

    # Production
    heat_progress_pct: float = Field(ge=0, le=100)
    current_batch_weight: float = 180.0
    batches_today: int = 0
    production_backlog: int = 0
    idle_minutes_today: float = 0.0
    cycle_efficiency_pct: float = 85.0
    thermal_stress_index: float = 0.0
    vibration_mm_s: float = 2.0

    # Tariff
    electricity_price: float = 1.60
    tariff_class: str = "UHV_220-132kV"
    tou_mode: bool = False
    is_peak: bool = False
    tariff_label: str = "Flat (current)"

    # Grid
    grid_frequency: float = 50.0
    grid_co2_kg_per_kwh: float = 0.50

    # Electrodes
    electrode_position_mm: float = 250.0
    electrode_consumption_kg: float = 0.0
    electrode_consumption_today_kg: float = 0.0

    # Inputs
    oxygen_injection_m3hr: float = 0.0
    cooling_water_flow_lmin: float = 200.0

    # Status
    status: str = "IDLE"
    ai_active: bool = False
    crisis_flags: CrisisFlags = Field(default_factory=CrisisFlags)


class RecommendationOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: Optional[datetime] = None
    machine_id: Optional[str] = None
    action_label: str
    action_magnitude_pct: float = 0.0
    estimated_savings_egp_per_hour: float = 0.0
    pf_penalty_avoided_egp: float = 0.0
    co2_saved_kg: float = 0.0
    xai_reason: str
    xai_reason_ar: str = ""
    machine_health: Literal["SAFE", "WARNING", "CRITICAL"] = "SAFE"
    production_status: Literal["ON_TRACK", "AT_RISK", "BEHIND"] = "ON_TRACK"
    reward_components: Dict[str, float] = Field(default_factory=dict)
    dominant_reason: str = "stable"
    ai_enabled: bool = False
    maintenance_risk_score: float = 0.0
    maintenance_risk_level: Literal["NOMINAL", "WATCH", "WARNING", "CRITICAL"] = "NOMINAL"
    maintenance_alert: Optional[str] = None
    maintenance_fault_prediction: Optional[str] = None
    maintenance_recommended_action: str = "NONE"
    maintenance_safe_recovery_action: Optional[str] = None
    maintenance_xai_reason: str = ""
    maintenance_xai_reason_ar: str = ""
    operational_efficiency_score: float = 0.0
    throughput_score: float = 0.0
    process_stability_score: float = 0.0
    thermal_stress_index: float = 0.0


class KPISnapshot(BaseModel):
    egp_saved_today: float = 0.0
    batches_completed: int = 0
    avg_arc_power_mw: float = 0.0
    avg_power_factor: float = 0.0
    co2_saved_kg: float = 0.0
    thermal_incidents_today: int = 0
    pf_penalty_avoided_today_egp: float = 0.0
    ai_decisions_today: int = 0
    maintenance_alerts_today: int = 0
    avg_maintenance_risk: float = 0.0
    avg_operational_efficiency: float = 0.0
    avg_process_stability: float = 0.0
    idle_minutes_today: float = 0.0


class AIToggleRequest(BaseModel):
    enabled: bool


class ProfileRequest(BaseModel):
    profile: Literal[
        "default", "cost_first", "equipment_sensitive",
        "production_critical", "quality_focused"
    ] = "default"


class CrisisInjectRequest(BaseModel):
    event: Literal["wall_overheat", "electrode_break", "grid_spike", "transformer_alarm"]


class TariffModeRequest(BaseModel):
    enabled: bool  # True = TOU reform mode; False = current flat


# ── Dynamic Pricing Engine schemas ──────────────────────────────────────────

class PricingModeRequest(BaseModel):
    mode: Literal["flat", "sim_tou", "sim_spot", "live_eehc"] = "flat"


class DRInjectRequest(BaseModel):
    event_type: Literal["CURTAILMENT", "INTERRUPTIBLE", "FREQUENCY_RESPONSE"] = "CURTAILMENT"
    mw_requested: float = Field(default=30.0, ge=5.0, le=110.0)
    duration_minutes: int = Field(default=30, ge=15, le=120)


class LivePriceResponse(BaseModel):
    timestamp: str
    price_egp_kwh: float
    price_source: str
    tariff_class: str
    is_peak: bool
    is_dr_event: bool
    dr_event_id: Optional[str] = None
    confidence: float = 1.0
    label: str


class RevenueSnapshot(BaseModel):
    energy_savings_egp: float = 0.0
    dr_payments_egp: float = 0.0
    capacity_credits_egp: float = 0.0
    ancillary_egp: float = 0.0
    total_revenue_egp: float = 0.0


class PricingEventSearchResult(BaseModel):
    total: int
    results: list[dict]
    stats: dict
