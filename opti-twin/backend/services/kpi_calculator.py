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
    last_batches: int = 0
    seen_wall_warning: bool = False
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
        if len(s.arc_power_samples) > 1200:
            s.arc_power_samples = s.arc_power_samples[-1200:]
            s.pf_samples = s.pf_samples[-1200:]
        s.last_batches = int(t.get("batches_today", 0))
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
        return {
            "egp_saved_today": round(s.egp_saved_today, 1),
            "batches_completed": s.last_batches,
            "avg_arc_power_mw": round(avg_p, 1),
            "avg_power_factor": round(avg_pf, 3),
            "co2_saved_kg": round(s.co2_saved_kg, 2),
            "thermal_incidents_today": s.thermal_incidents_today,
            "pf_penalty_avoided_today_egp": round(s.pf_penalty_avoided_today_egp, 1),
            "ai_decisions_today": s.ai_decisions_today,
            "dr_payments_today": round(s.dr_payments_today, 1),
            "capacity_credits_today": round(s.capacity_credits_today, 1),
        }

    def reset(self) -> None:
        self.state = KPIState()
