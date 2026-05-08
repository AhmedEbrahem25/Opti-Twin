"""
KPI aggregator — running daily KPIs computed from streamed telemetry/recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class KPIState:
    egp_saved_today: float = 0.0
    co2_saved_kg: float = 0.0
    pf_penalty_avoided_today_egp: float = 0.0
    ai_decisions_today: int = 0
    thermal_incidents_today: int = 0
    arc_power_samples: list[float] = field(default_factory=list)
    pf_samples: list[float] = field(default_factory=list)
    maintenance_risk_samples: list[float] = field(default_factory=list)
    operational_efficiency_samples: list[float] = field(default_factory=list)
    process_stability_samples: list[float] = field(default_factory=list)
    last_batches: int = 0
    idle_minutes_today: float = 0.0
    seen_wall_warning: bool = False
    seen_maintenance_alert: bool = False
    maintenance_alerts_today: int = 0
    # Dynamic pricing revenue streams
    dr_payments_today: float = 0.0
    capacity_credits_today: float = 0.0


class KPICalculator:
    """Single-machine KPI tracker. Stateless across restarts (resets daily)."""

    def __init__(self) -> None:
        self.state = KPIState()

    # Telemetry contributes: arc power / PF samples; thermal incidents.
    def ingest_telemetry(self, t: Dict) -> None:
        s = self.state
        s.arc_power_samples.append(float(t.get("arc_power_mw", 0.0)))
        s.pf_samples.append(float(t.get("power_factor", 0.0)))
        s.operational_efficiency_samples.append(float(t.get("cycle_efficiency_pct", 0.0)))
        thermal_stress = float(t.get("thermal_stress_index", 0.0))
        process_stability = max(0.0, min(100.0, 100.0 - thermal_stress * 0.45))
        s.process_stability_samples.append(process_stability)
        if len(s.arc_power_samples) > 1200:
            s.arc_power_samples = s.arc_power_samples[-1200:]
            s.pf_samples = s.pf_samples[-1200:]
            s.operational_efficiency_samples = s.operational_efficiency_samples[-1200:]
            s.process_stability_samples = s.process_stability_samples[-1200:]
            s.maintenance_risk_samples = s.maintenance_risk_samples[-1200:]
        s.last_batches = int(t.get("batches_today", 0))
        s.idle_minutes_today = float(t.get("idle_minutes_today", s.idle_minutes_today))
        # Wall-overheat incident — count once per crossing
        wall = float(t.get("wall_panel_temp", 0.0))
        if wall >= 200.0 and not s.seen_wall_warning:
            s.thermal_incidents_today += 1
            s.seen_wall_warning = True
        elif wall < 180.0:
            s.seen_wall_warning = False

    # Recommendation contributes: realized savings (only when AI enabled).
    def ingest_recommendation(self, r: Dict) -> None:
        s = self.state
        risk = float(r.get("maintenance_risk_score", 0.0))
        s.maintenance_risk_samples.append(risk)
        if r.get("operational_efficiency_score") is not None:
            s.operational_efficiency_samples.append(float(r.get("operational_efficiency_score", 0.0)))
        if r.get("process_stability_score") is not None:
            s.process_stability_samples.append(float(r.get("process_stability_score", 0.0)))
        alert_active = bool(r.get("maintenance_alert"))
        if alert_active and not s.seen_maintenance_alert:
            s.maintenance_alerts_today += 1
            s.seen_maintenance_alert = True
        elif not alert_active and risk < 0.35:
            s.seen_maintenance_alert = False

        if not r.get("ai_enabled"):
            return
        # 1 sample = 3 sim-seconds. Recommendation savings_per_hour /1200 ≈ /hr scaled.
        per_tick = float(r.get("estimated_savings_egp_per_hour", 0.0)) * (3.0 / 3600.0)
        s.egp_saved_today += per_tick
        s.co2_saved_kg += float(r.get("co2_saved_kg", 0.0)) * (3.0 / 3600.0) * 1000.0
        s.pf_penalty_avoided_today_egp += float(r.get("pf_penalty_avoided_egp", 0.0)) * (3.0 / 3600.0)
        if r.get("action_label") and r.get("action_label") != "HOLD_STEADY":
            s.ai_decisions_today += 1

    def ingest_dr_payment(self, payment_egp: float) -> None:
        self.state.dr_payments_today += payment_egp

    def ingest_capacity_credit(self, credit_egp: float) -> None:
        self.state.capacity_credits_today += credit_egp

    def snapshot(self) -> Dict:
        s = self.state
        avg_p = sum(s.arc_power_samples) / len(s.arc_power_samples) if s.arc_power_samples else 0.0
        avg_pf = sum(s.pf_samples) / len(s.pf_samples) if s.pf_samples else 0.0
        avg_risk = (
            sum(s.maintenance_risk_samples) / len(s.maintenance_risk_samples)
            if s.maintenance_risk_samples else 0.0
        )
        avg_eff = (
            sum(s.operational_efficiency_samples) / len(s.operational_efficiency_samples)
            if s.operational_efficiency_samples else 0.0
        )
        avg_stability = (
            sum(s.process_stability_samples) / len(s.process_stability_samples)
            if s.process_stability_samples else 0.0
        )
        return {
            "egp_saved_today": round(s.egp_saved_today, 1),
            "batches_completed": s.last_batches,
            "avg_arc_power_mw": round(avg_p, 1),
            "avg_power_factor": round(avg_pf, 3),
            "co2_saved_kg": round(s.co2_saved_kg, 2),
            "thermal_incidents_today": s.thermal_incidents_today,
            "pf_penalty_avoided_today_egp": round(s.pf_penalty_avoided_today_egp, 1),
            "ai_decisions_today": s.ai_decisions_today,
            "maintenance_alerts_today": s.maintenance_alerts_today,
            "avg_maintenance_risk": round(avg_risk, 3),
            "avg_operational_efficiency": round(avg_eff, 1),
            "avg_process_stability": round(avg_stability, 1),
            "idle_minutes_today": round(s.idle_minutes_today, 1),
            "dr_payments_today": round(s.dr_payments_today, 1),
            "capacity_credits_today": round(s.capacity_credits_today, 1),
        }

    def reset(self) -> None:
        self.state = KPIState()
