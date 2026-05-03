"""
Load Flexibility Scheduler — greedy multi-heat schedule optimizer.

Given a 24-hour price forecast, determines the optimal start time for each
upcoming heat to minimize total energy cost while meeting production quota.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

log = logging.getLogger("opti-twin.pricing.scheduler")

HEAT_DURATION_H = 70 / 60       # 70 minutes
MIN_GAP_H = 5 / 60              # 5-minute refractory recovery
BORE_DOWN_H = 10 / 60           # bore-down before melting
MELTING_DURATION_H = 30 / 60   # MELTING_PHASE_1 + 2 combined
MELTING_MW = 97.5               # average over melting phases
NON_MELTING_MW = 55.0           # bore-down + refining average
EVAL_STEP_H = 0.5               # evaluate candidate starts every 30 min


@dataclass
class HeatSlot:
    heat_number: int
    start_hour: float
    end_hour: float
    melting_avg_price_egp: float
    total_cost_egp: float
    label: str

    def to_dict(self) -> Dict:
        return {
            "heat_number": self.heat_number,
            "start_hour": self.start_hour,
            "end_hour": self.end_hour,
            "melting_avg_price_egp": self.melting_avg_price_egp,
            "total_cost_egp": self.total_cost_egp,
            "label": self.label,
        }


class LoadFlexibilityScheduler:
    def __init__(self) -> None:
        self._last_schedule: List[HeatSlot] = []

    def optimize(
        self,
        forecast: List[Dict],
        current_hour: float,
        heats_remaining: int,
        shift_end_hour: float,
    ) -> List[HeatSlot]:
        if not forecast or heats_remaining <= 0:
            return []

        price_map = {round(f["t_hour"] % 24, 2): f["p50"] for f in forecast}

        def price_at(h: float) -> float:
            key = round(h % 24, 2)
            if key in price_map:
                return price_map[key]
            keys = list(price_map.keys())
            if not keys:
                return 1.60
            nearest = min(keys, key=lambda k: abs(k - key))
            return price_map[nearest]

        def heat_cost(start_h: float) -> float:
            melting_start = start_h + BORE_DOWN_H
            cost = 0.0
            h = start_h
            while h < start_h + HEAT_DURATION_H:
                mw = MELTING_MW if melting_start <= h < melting_start + MELTING_DURATION_H else NON_MELTING_MW
                cost += mw * 1000 * price_at(h) * EVAL_STEP_H
                h += EVAL_STEP_H
            return cost

        slots: List[HeatSlot] = []
        earliest = current_hour

        for n in range(heats_remaining):
            latest_start = max(earliest, shift_end_hour - HEAT_DURATION_H * (heats_remaining - n))
            best_start, best_cost = earliest, float("inf")
            h = earliest
            while h <= latest_start + 0.01:
                c = heat_cost(h)
                if c < best_cost:
                    best_cost, best_start = c, h
                h += EVAL_STEP_H

            melting_start_h = best_start + BORE_DOWN_H
            melting_avg_p = (price_at(melting_start_h) + price_at(melting_start_h + 0.25)) / 2

            slots.append(HeatSlot(
                heat_number=n + 1,
                start_hour=round(best_start % 24, 3),
                end_hour=round((best_start + HEAT_DURATION_H) % 24, 3),
                melting_avg_price_egp=round(melting_avg_p, 3),
                total_cost_egp=round(best_cost, 0),
                label=f"Heat #{n+1} @ {best_start % 24:.2f}h",
            ))
            earliest = best_start + HEAT_DURATION_H + MIN_GAP_H

        self._last_schedule = slots
        if slots:
            log.info(
                "Schedule optimised: %d heats  total_cost=%.0f EGP  first_start=%.2fh",
                len(slots), sum(s.total_cost_egp for s in slots), slots[0].start_hour,
            )
        return slots

    def savings_vs_backtoback(
        self, slots: List[HeatSlot], from_hour: float, forecast: List[Dict]
    ) -> float:
        if not slots or not forecast:
            return 0.0

        price_map = {round(f["t_hour"] % 24, 2): f["p50"] for f in forecast}

        def price_at(h: float) -> float:
            key = round(h % 24, 2)
            keys = list(price_map.keys())
            if not keys:
                return 1.60
            nearest = min(keys, key=lambda k: abs(k - key))
            return price_map.get(key, price_map[nearest])

        def heat_cost_at(start_h: float) -> float:
            melting_start = start_h + BORE_DOWN_H
            cost = 0.0
            h = start_h
            while h < start_h + HEAT_DURATION_H:
                mw = MELTING_MW if melting_start <= h < melting_start + MELTING_DURATION_H else NON_MELTING_MW
                cost += mw * 1000 * price_at(h) * EVAL_STEP_H
                h += EVAL_STEP_H
            return cost

        b2b_cost = 0.0
        h = from_hour
        for _ in slots:
            b2b_cost += heat_cost_at(h)
            h += HEAT_DURATION_H + MIN_GAP_H

        optimized = sum(s.total_cost_egp for s in slots)
        return round(b2b_cost - optimized, 0)
