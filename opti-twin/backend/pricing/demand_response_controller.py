"""
Demand Response Controller — DR event management and net benefit calculation.

Supports three DR program types matching Egyptian utility programs:
  CURTAILMENT        — grid requests load reduction, 30-min advance notice
  INTERRUPTIBLE      — immediate load cap under extreme grid stress
  FREQUENCY_RESPONSE — ±10 MW within 10 seconds, highest-value service
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

log = logging.getLogger("opti-twin.pricing.dr")

DR_RATES: Dict[str, float] = {
    "CURTAILMENT":        float(os.getenv("DPE_DR_CURTAILMENT_RATE_EGP", "250")),
    "INTERRUPTIBLE":      float(os.getenv("DPE_DR_INTERRUPTIBLE_RATE_EGP", "450")),
    "FREQUENCY_RESPONSE": float(os.getenv("DPE_DR_FREQUENCY_RATE_EGP", "950")),
}
DR_MIN_DURATION = int(os.getenv("DPE_DR_MIN_DURATION_MINUTES", "15"))
STEEL_MARGIN_PER_TONNE = float(os.getenv("STEEL_REVENUE_PER_TONNE", "8400")) - float(
    os.getenv("STEEL_COST_PER_TONNE", "6100")
)
TONNES_PER_HEAT = float(os.getenv("EAF_FURNACE_SIZE_T", "185"))
HEAT_DURATION_MIN = 70.0
MIN_SAFE_MW = float(os.getenv("EAF_MIN_POWER_MW", "60"))

UNSAFE_PHASES = {"CHARGING", "BORE_DOWN", "TAPPING"}


@dataclass
class DREvent:
    event_id: str
    event_type: str
    mw_requested: float
    duration_minutes: int
    rate_egp_per_mwh: float
    issued_at: str
    status: str = "PENDING"
    accepted_mw: float = 0.0
    payment_earned_egp: float = 0.0
    net_benefit_egp: float = 0.0
    decline_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "mw_requested": self.mw_requested,
            "duration_minutes": self.duration_minutes,
            "rate_egp_per_mwh": self.rate_egp_per_mwh,
            "issued_at": self.issued_at,
            "status": self.status,
            "accepted_mw": self.accepted_mw,
            "payment_earned_egp": self.payment_earned_egp,
            "net_benefit_egp": self.net_benefit_egp,
            "decline_reason": self.decline_reason,
        }


@dataclass
class DRState:
    events: List[DREvent] = field(default_factory=list)
    total_payments_today: float = 0.0
    active_event: Optional[DREvent] = None


class DemandResponseController:
    def __init__(self) -> None:
        self.state = DRState()

    def inject_event(
        self,
        event_type: str = "CURTAILMENT",
        mw_requested: float = 30.0,
        duration_minutes: int = 30,
    ) -> DREvent:
        ev = DREvent(
            event_id=str(uuid4())[:8],
            event_type=event_type,
            mw_requested=mw_requested,
            duration_minutes=max(DR_MIN_DURATION, duration_minutes),
            rate_egp_per_mwh=DR_RATES.get(event_type, DR_RATES["CURTAILMENT"]),
            issued_at=datetime.now(timezone.utc).isoformat(),
        )
        self.state.events.append(ev)
        log.info("DR event %s: %s, %s MW, %s min", ev.event_id, event_type, mw_requested, duration_minutes)
        return ev

    def evaluate(self, event: DREvent, machine_state: Dict) -> Dict:
        phase = str(machine_state.get("status", "IDLE"))
        arc_mw = float(machine_state.get("arc_power_mw", 0.0))

        if phase in UNSAFE_PHASES:
            return {"accept": False, "reason": f"Phase {phase} unsafe to curtail", "net_benefit_egp": 0.0}

        mw_available = max(0.0, arc_mw - MIN_SAFE_MW)
        mw_shed = min(mw_available, event.mw_requested)

        if mw_shed < 5.0:
            return {"accept": False, "reason": "Insufficient headroom (arc near minimum)", "net_benefit_egp": 0.0}

        duration_h = event.duration_minutes / 60.0
        dr_payment = mw_shed * duration_h * event.rate_egp_per_mwh
        heats_delayed = (event.duration_minutes / HEAT_DURATION_MIN) * (mw_shed / max(arc_mw, 1.0))
        production_cost = heats_delayed * TONNES_PER_HEAT * 0.5 * STEEL_MARGIN_PER_TONNE
        net = dr_payment - production_cost

        return {
            "accept": net > 0,
            "mw_to_shed": round(mw_shed, 1),
            "dr_payment_egp": round(dr_payment, 1),
            "production_cost_egp": round(production_cost, 1),
            "net_benefit_egp": round(net, 1),
            "reason": (
                f"DR payment {dr_payment:.0f} EGP "
                f"{'>' if net > 0 else '<'} production cost {production_cost:.0f} EGP"
            ),
        }

    def process_event(self, event: DREvent, machine_state: Dict) -> Dict:
        assessment = self.evaluate(event, machine_state)
        if assessment["accept"]:
            event.status = "ACCEPTED"
            event.accepted_mw = assessment["mw_to_shed"]
            event.payment_earned_egp = assessment["dr_payment_egp"]
            event.net_benefit_egp = assessment["net_benefit_egp"]
            self.state.total_payments_today += event.payment_earned_egp
            self.state.active_event = event
        else:
            event.status = "DECLINED"
            event.decline_reason = assessment.get("reason", "")
        log.info("DR %s → %s (net %+.0f EGP)", event.event_id, event.status, assessment["net_benefit_egp"])
        return assessment

    def complete_active(self) -> None:
        if self.state.active_event:
            self.state.active_event.status = "COMPLETED"
            self.state.active_event = None

    def snapshot(self) -> Dict:
        return {
            "total_dr_payments_today": round(self.state.total_payments_today, 1),
            "events_today": len(self.state.events),
            "events_accepted": sum(1 for e in self.state.events if e.status == "ACCEPTED"),
            "active_event": self.state.active_event.to_dict() if self.state.active_event else None,
            "history": [e.to_dict() for e in self.state.events[-20:]],
        }
