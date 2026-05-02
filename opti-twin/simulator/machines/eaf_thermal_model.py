"""
Simplified zero-dimensional energy-balance thermal model for an Electric Arc Furnace.

This is NOT a CFD or finite-element model. Coefficients are seeded from textbook
thermodynamic relationships and tuned for visual realism in a hackathon demo.

References:
  - Specific heat of liquid steel: ~0.50 kJ/(kg·°C) — industry constant.
  - Wall heat-loss fraction: 0.10–0.20 typical for water-cooled panels.
  - Effective oxygen heat coupling: tuned (real value depends on slag/post-combustion).
"""

from dataclasses import dataclass


SPECIFIC_HEAT_STEEL = 0.50       # kJ/(kg·°C)
HEAT_LOSS_COEFFICIENT = 0.15     # fractional wall heat loss
OXYGEN_HEAT_GAIN = 2.5           # kJ per (m³/hr · sec) — empirical bath-coupled
COOLING_HEAT_EXTRACT = 0.07      # kJ per (l/min · sec)
PHYSICAL_BATH_CEILING = 1700.0   # °C


@dataclass
class ThermalInputs:
    arc_power_mw: float
    batch_weight_t: float
    oxygen_m3hr: float
    cooling_lmin: float


def update_bath_temp(
    current_temp: float,
    inputs: ThermalInputs,
    dt_seconds: float = 3.0,
) -> float:
    """Compute new bath temperature in °C after dt simulated seconds."""
    mass_kg = max(inputs.batch_weight_t * 1000.0, 1.0)
    q_arc = inputs.arc_power_mw * 1000.0 * dt_seconds                 # kJ
    q_oxygen = inputs.oxygen_m3hr * OXYGEN_HEAT_GAIN * (dt_seconds / 3600.0)
    q_loss = (current_temp - 25.0) * HEAT_LOSS_COEFFICIENT * dt_seconds * 0.5
    q_cooling = inputs.cooling_lmin * COOLING_HEAT_EXTRACT * dt_seconds
    q_net = q_arc + q_oxygen - q_loss - q_cooling
    delta_temp = q_net / (mass_kg * SPECIFIC_HEAT_STEEL)
    return min(current_temp + delta_temp, PHYSICAL_BATH_CEILING)


def update_wall_temp(
    current_wall_temp: float,
    arc_power_mw: float,
    cooling_lmin: float,
    dt_seconds: float = 3.0,
) -> float:
    """Wall panel temperature dynamics — simple first-order response."""
    heat_in = arc_power_mw * 0.04 * dt_seconds        # 4% of arc as wall radiation
    heat_out = cooling_lmin * 0.012 * dt_seconds      # cooling-water extraction
    ambient_loss = (current_wall_temp - 40.0) * 0.005 * dt_seconds
    delta = heat_in - heat_out - ambient_loss
    new_temp = current_wall_temp + delta
    return max(40.0, min(new_temp, 350.0))


def update_electrode_temp(
    current_temp: float,
    arc_power_mw: float,
    dt_seconds: float = 3.0,
) -> float:
    """Electrode tip temperature — driven by arc current density."""
    target = 1500.0 + arc_power_mw * 14.0
    target = min(target, 3000.0)
    tau = 30.0  # time constant seconds
    return current_temp + (target - current_temp) * (dt_seconds / tau)


def update_cooling_outlet(
    inlet_temp: float,
    cooling_lmin: float,
    arc_power_mw: float,
    dt_seconds: float = 3.0,
) -> float:
    """Cooling water outlet temperature — energy balance."""
    if cooling_lmin < 1.0:
        return 55.0
    heat_picked_up_kw = arc_power_mw * 1000.0 * 0.04
    delta_t = heat_picked_up_kw / (cooling_lmin / 60.0 * 4.18)  # specific heat water
    return min(55.0, inlet_temp + delta_t * 0.05)
