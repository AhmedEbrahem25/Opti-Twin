"""
Egyptian industrial electricity tariff service.

Verified source:
    EgyptERA — Current Electricity Tariff, August 2024
    https://egyptera.org/en/TarrifAug2024.aspx

Reality: industrial UHV (220-132 kV) customers are billed at a FLAT rate of
1.60 EGP/kWh as of August 2024. There is no published peak/off-peak split
for industrial UHV customers.

Forward-looking TOU schedule below is sourced from academic proposal
(Ahmed et al., GUC Working Paper #29) and is exposed via `tou_mode=True`
to demonstrate that the system is ready for tariff reform.
"""

from dataclasses import dataclass
from typing import Optional


# ---------- Verified flat tariffs (EgyptERA Aug 2024) ----------

FLAT_TARIFFS_EGP_PER_KWH = {
    "UHV_220-132kV": 1.60,
    "HV_66-33kV": 1.74,
    "MV_22-11kV": 1.94,
}

POWER_FACTOR_REFERENCE = 0.92  # PF below this triggers penalty for >500 kW loads
CUSTOMER_SERVICE_FEE_EGP_PER_MONTH = 35.0


# ---------- Forward-looking proposed TOU (NOT current Egyptian rate) ----------
# Source: Ahmed et al., GUC Working Paper #29 — Designing a Prudent Peak Load
#         Pricing Model. Used only when `tou_mode=True` for reform readiness.

PROPOSED_TOU_SCHEDULE = [
    # (hour_start_inclusive, hour_end_exclusive, rate_egp_per_kwh, label)
    (0,  6,  1.00, "Off-peak"),
    (6,  18, 1.50, "Normal"),
    (18, 22, 2.50, "Peak"),
    (22, 24, 1.80, "Semi-peak"),
]


@dataclass
class TariffSnapshot:
    rate_egp_per_kwh: float
    is_peak: bool
    label: str
    tou_mode: bool
    tariff_class: str


class EgyptGridPricing:
    """Returns the EGP/kWh applicable for a given simulated hour."""

    def __init__(
        self,
        tariff_class: str = "UHV_220-132kV",
        tou_mode: bool = False,
    ) -> None:
        if tariff_class not in FLAT_TARIFFS_EGP_PER_KWH:
            raise ValueError(f"Unknown tariff class: {tariff_class}")
        self.tariff_class = tariff_class
        self.tou_mode = tou_mode

    def set_tou_mode(self, enabled: bool) -> None:
        self.tou_mode = enabled

    def price_at(self, sim_hour_of_day: float) -> TariffSnapshot:
        if not self.tou_mode:
            rate = FLAT_TARIFFS_EGP_PER_KWH[self.tariff_class]
            return TariffSnapshot(
                rate_egp_per_kwh=rate,
                is_peak=False,
                label="Flat (current)",
                tou_mode=False,
                tariff_class=self.tariff_class,
            )

        h = sim_hour_of_day % 24
        for start, end, rate, label in PROPOSED_TOU_SCHEDULE:
            if start <= h < end:
                return TariffSnapshot(
                    rate_egp_per_kwh=rate,
                    is_peak=(label == "Peak"),
                    label=label + " (TOU reform mode)",
                    tou_mode=True,
                    tariff_class=self.tariff_class,
                )
        # fallback (shouldn't hit)
        rate = FLAT_TARIFFS_EGP_PER_KWH[self.tariff_class]
        return TariffSnapshot(rate, False, "Flat fallback", False, self.tariff_class)

    def power_factor_penalty_egp_per_hour(
        self,
        current_pf: float,
        arc_power_mw: float,
    ) -> float:
        """Estimate the hourly bill add-on caused by sub-reference PF.

        Mechanism: Egypt penalizes industrial loads > 500 kW with PF below 0.92
        reference. Magnitude varies by site/contract; we use a conservative
        proportional model: penalty ∝ (PF_ref - PF) × hourly bill × 0.05.
        """
        if arc_power_mw * 1000.0 < 500.0:
            return 0.0
        deficit = max(0.0, POWER_FACTOR_REFERENCE - current_pf)
        if deficit <= 0:
            return 0.0
        rate = FLAT_TARIFFS_EGP_PER_KWH[self.tariff_class]
        hourly_bill = arc_power_mw * 1000.0 * rate
        return deficit * hourly_bill * 0.05
