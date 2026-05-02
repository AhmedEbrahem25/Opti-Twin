"""
Synthetic Egyptian industrial spot price generator.

Produces realistic intraday price curves for the UHV (220-132 kV) segment,
anchored to EgyptERA Aug 2024 flat rate of 1.60 EGP/kWh as the daily average.

Time-of-day structure:
  Off-peak   00:00–07:00  ~0.85× base
  Shoulder   07:00–17:00  ~1.20× base
  Peak       17:00–22:00  ~1.80–2.50× base (sine curve + demand events)
  Evening    22:00–24:00  ~1.10× base
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List


@dataclass
class SpotPrice:
    hour: float
    price_egp_kwh: float
    is_peak: bool
    label: str


class SyntheticSpotGenerator:
    PEAK_START = 17.0
    PEAK_END = 22.0

    def __init__(
        self,
        base_rate: float = 1.60,
        peak_multiplier_min: float = 1.8,
        peak_multiplier_max: float = 2.5,
        offpeak_multiplier: float = 0.85,
        shoulder_multiplier: float = 1.20,
        noise_std: float = 0.08,
        seed: int = 42,
    ) -> None:
        self.base = base_rate
        self.peak_min = peak_multiplier_min
        self.peak_max = peak_multiplier_max
        self.offpeak = offpeak_multiplier
        self.shoulder = shoulder_multiplier
        self.noise_std = noise_std
        self._rng = random.Random(seed)
        self._demand_spikes: List[tuple] = []
        self._inject_random_spikes()

    def _inject_random_spikes(self) -> None:
        n = self._rng.randint(1, 3)
        for _ in range(n):
            start = self._rng.uniform(14.0, 21.5)
            duration = self._rng.uniform(0.25, 0.75)
            extra = self._rng.uniform(0.25, 0.45)
            self._demand_spikes.append((start, duration, extra))

    def price_at(self, hour: float) -> SpotPrice:
        h = hour % 24.0
        is_peak = self.PEAK_START <= h < self.PEAK_END

        if h < 7.0:
            mult = self.offpeak
            label = "Off-peak"
        elif h < self.PEAK_START:
            mult = self.shoulder
            label = "Shoulder"
        elif is_peak:
            progress = (h - self.PEAK_START) / (self.PEAK_END - self.PEAK_START)
            peak_factor = math.sin(progress * math.pi)
            mult = self.peak_min + (self.peak_max - self.peak_min) * peak_factor
            label = "Peak"
        else:
            mult = self.shoulder * 0.92
            label = "Evening shoulder"

        price = self.base * mult
        for (start, duration, extra) in self._demand_spikes:
            if start <= h < start + duration:
                price += extra
                label = f"{label} + demand event"
                break
        price += self._rng.gauss(0, self.noise_std)
        price = max(0.50, round(price, 3))
        return SpotPrice(hour=h, price_egp_kwh=price, is_peak=is_peak, label=label)

    def forecast(self, from_hour: float, steps: int = 48, step_minutes: int = 30) -> List[SpotPrice]:
        step_h = step_minutes / 60.0
        return [self.price_at(from_hour + i * step_h) for i in range(steps)]
