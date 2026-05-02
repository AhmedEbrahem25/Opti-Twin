"""
Price Signal Broker — single normalized interface for all electricity price sources.

Modes:
  flat      — constant 1.60 EGP/kWh (current EgyptERA rate, default)
  sim_tou   — binary TOU schedule (current system's TOU flag)
  sim_spot  — synthetic realistic Egyptian intraday spot prices
  live_eehc — EEHC real-time API (stub; falls back to flat until wired)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

from pricing.synthetic_spot_generator import SyntheticSpotGenerator

log = logging.getLogger("pricing.broker")

FLAT_RATE = float(os.getenv("TARIFF_RATE_EGP_PER_KWH", "1.60"))
DPE_MODE = os.getenv("DPE_MODE", "flat")
DPE_FORECAST_HORIZON_HOURS = int(os.getenv("DPE_FORECAST_HORIZON_HOURS", "24"))
DPE_FORECAST_STEP_MINUTES = int(os.getenv("DPE_FORECAST_STEP_MINUTES", "30"))
TOU_PEAK_START = float(os.getenv("TOU_PEAK_START_HOUR", "18.0"))
TOU_PEAK_END = float(os.getenv("TOU_PEAK_END_HOUR", "22.0"))
TOU_PEAK_RATE = float(os.getenv("TOU_PEAK_RATE_EGP", "2.50"))
TOU_OFFPEAK_RATE = float(os.getenv("TOU_OFFPEAK_RATE_EGP", "1.20"))


class PriceSignalBroker:
    def __init__(self) -> None:
        self.mode = DPE_MODE
        self._spot = SyntheticSpotGenerator(base_rate=FLAT_RATE)
        self._last_price: Optional[dict] = None

    def set_mode(self, mode: str) -> None:
        allowed = {"flat", "sim_tou", "sim_spot", "live_eehc"}
        if mode not in allowed:
            raise ValueError(f"Unknown pricing mode {mode!r}")
        self.mode = mode
        log.info("Pricing mode → %s", mode)

    def get_current_price(self, sim_hour: Optional[float] = None) -> dict:
        hour = sim_hour if sim_hour is not None else _utc_hour()
        if self.mode == "flat":
            price, is_peak, label = FLAT_RATE, False, "Flat (EgyptERA Aug 2024)"
        elif self.mode == "sim_tou":
            is_peak = TOU_PEAK_START <= (hour % 24) < TOU_PEAK_END
            price = TOU_PEAK_RATE if is_peak else TOU_OFFPEAK_RATE
            label = "TOU Peak" if is_peak else "TOU Off-peak"
        elif self.mode == "sim_spot":
            sp = self._spot.price_at(hour)
            price, is_peak, label = sp.price_egp_kwh, sp.is_peak, sp.label
        else:
            # live_eehc stub
            price, is_peak, label = FLAT_RATE, False, "EEHC (stub — using flat)"

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "price_egp_kwh": round(price, 3),
            "price_source": self.mode,
            "tariff_class": "UHV_220-132kV",
            "is_peak": is_peak,
            "is_dr_event": False,
            "dr_event_id": None,
            "confidence": 1.0,
            "label": label,
        }
        self._last_price = result
        return result

    def get_forecast(self, from_hour: Optional[float] = None) -> dict:
        hour = from_hour if from_hour is not None else _utc_hour()
        steps = int(DPE_FORECAST_HORIZON_HOURS * 60 / DPE_FORECAST_STEP_MINUTES)
        step_h = DPE_FORECAST_STEP_MINUTES / 60.0
        noise = 0.08

        forecast: List[dict] = []
        if self.mode in ("flat", "live_eehc"):
            for i in range(steps):
                forecast.append({
                    "t_offset_h": round(i * step_h, 2),
                    "t_hour": round((hour + i * step_h) % 24, 2),
                    "p50": FLAT_RATE,
                    "p10": round(FLAT_RATE * 0.95, 3),
                    "p90": round(FLAT_RATE * 1.05, 3),
                    "is_peak": False,
                })
        elif self.mode == "sim_tou":
            for i in range(steps):
                h = (hour + i * step_h) % 24
                is_peak = TOU_PEAK_START <= h < TOU_PEAK_END
                p = TOU_PEAK_RATE if is_peak else TOU_OFFPEAK_RATE
                forecast.append({
                    "t_offset_h": round(i * step_h, 2),
                    "t_hour": round(h, 2),
                    "p50": p, "p10": round(p * 0.98, 3), "p90": round(p * 1.02, 3),
                    "is_peak": is_peak,
                })
        else:
            prices = self._spot.forecast(hour, steps=steps, step_minutes=DPE_FORECAST_STEP_MINUTES)
            for i, sp in enumerate(prices):
                unc = noise * (1 + i * 0.02)
                forecast.append({
                    "t_offset_h": round(i * step_h, 2),
                    "t_hour": round(sp.hour, 2),
                    "p50": sp.price_egp_kwh,
                    "p10": round(max(0.5, sp.price_egp_kwh - 1.5 * unc), 3),
                    "p90": round(sp.price_egp_kwh + 1.5 * unc, 3),
                    "is_peak": sp.is_peak,
                })

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "from_hour": round(hour % 24, 2),
            "horizon_hours": DPE_FORECAST_HORIZON_HOURS,
            "step_minutes": DPE_FORECAST_STEP_MINUTES,
            "mode": self.mode,
            "forecast": forecast,
        }

    @property
    def last_price(self) -> Optional[dict]:
        return self._last_price


def _utc_hour() -> float:
    now = datetime.now(timezone.utc)
    return now.hour + now.minute / 60.0 + now.second / 3600.0
