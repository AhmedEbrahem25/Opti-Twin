"""
Revenue Optimizer — tracks and stacks 4 simultaneous revenue streams.

Stream 1: Energy savings  (arc power reduction × live price)
Stream 2: DR payments     (accepted DR events)
Stream 3: Capacity credits (contracted flexibility, prorated daily)
Stream 4: Ancillary services (frequency response)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict

log = logging.getLogger("pricing.revenue")

CAPACITY_RATE_EGP = float(os.getenv("DPE_CAPACITY_CREDIT_RATE_EGP", "80"))   # EGP/kW/month
CONTRACTED_MW = float(os.getenv("DPE_CONTRACTED_FLEXIBILITY_MW", "30"))


@dataclass
class RevenueState:
    energy_savings_egp: float = 0.0
    dr_payments_egp: float = 0.0
    capacity_credits_egp: float = 0.0
    ancillary_egp: float = 0.0


class RevenueOptimizer:
    def __init__(self) -> None:
        self.state = RevenueState()
        # Monthly capacity credit prorated per tick (3 real seconds out of 86400)
        self._capacity_per_tick = (CONTRACTED_MW * 1000 * CAPACITY_RATE_EGP / 30.0) * (3.0 / 86400.0)

    def record_energy_saving(self, egp_per_tick: float) -> None:
        self.state.energy_savings_egp += max(0.0, egp_per_tick)

    def record_dr_payment(self, payment_egp: float) -> None:
        self.state.dr_payments_egp += max(0.0, payment_egp)
        log.info("DR payment recorded: %.1f EGP", payment_egp)

    def record_ancillary(self, payment_egp: float) -> None:
        self.state.ancillary_egp += max(0.0, payment_egp)

    def accrue_capacity_credit(self) -> None:
        self.state.capacity_credits_egp += self._capacity_per_tick

    def total(self) -> float:
        s = self.state
        return s.energy_savings_egp + s.dr_payments_egp + s.capacity_credits_egp + s.ancillary_egp

    def snapshot(self) -> Dict:
        s = self.state
        return {
            "energy_savings_egp": round(s.energy_savings_egp, 1),
            "dr_payments_egp": round(s.dr_payments_egp, 1),
            "capacity_credits_egp": round(s.capacity_credits_egp, 1),
            "ancillary_egp": round(s.ancillary_egp, 1),
            "total_revenue_egp": round(self.total(), 1),
        }

    def reset(self) -> None:
        self.state = RevenueState()
