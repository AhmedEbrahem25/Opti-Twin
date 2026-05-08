"""
Multi-objective reward function for OptiTwinEAFEnv.

R = α·E_saved − β·M_stress − γ·P_delay + δ·Quality − ε·Wear − ζ·PF_penalty
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class RewardWeights:
    alpha: float = 1.0   # Energy savings (EGP)
    beta: float = 0.9    # Machine stress
    gamma: float = 1.8   # Production delay
    delta: float = 0.7   # Steel quality
    epsilon: float = 0.5 # Electrode waste
    zeta: float = 0.8    # Power-factor penalty (verified Egyptian mechanism)

    @classmethod
    def preset(cls, profile: str) -> "RewardWeights":
        profiles = {
            "cost_first":          cls(2.0, 0.5, 1.0, 0.5, 0.3, 1.5),
            "equipment_sensitive": cls(0.8, 2.0, 1.0, 0.7, 1.0, 0.5),
            "production_critical": cls(0.8, 0.8, 2.5, 0.7, 0.3, 0.5),
            "quality_focused":     cls(0.8, 0.9, 1.0, 2.0, 0.5, 0.5),
            "default":             cls(),
        }
        return profiles.get(profile, profiles["default"])


@dataclass
class RewardComponents:
    energy_savings_egp: float = 0.0
    machine_stress_penalty: float = 0.0
    production_delay_penalty: float = 0.0
    quality_bonus: float = 0.0
    electrode_waste: float = 0.0
    pf_penalty: float = 0.0
    productivity_bonus: float = 0.0
    process_stability_bonus: float = 0.0
    maintenance_risk_penalty: float = 0.0
    idle_time_penalty: float = 0.0
    total: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "energy_savings_egp": round(self.energy_savings_egp, 2),
            "machine_stress_penalty": round(self.machine_stress_penalty, 2),
            "production_delay_penalty": round(self.production_delay_penalty, 2),
            "quality_bonus": round(self.quality_bonus, 2),
            "electrode_waste": round(self.electrode_waste, 2),
            "pf_penalty": round(self.pf_penalty, 2),
            "productivity_bonus": round(self.productivity_bonus, 2),
            "process_stability_bonus": round(self.process_stability_bonus, 2),
            "maintenance_risk_penalty": round(self.maintenance_risk_penalty, 2),
            "idle_time_penalty": round(self.idle_time_penalty, 2),
            "total": round(self.total, 2),
        }


def compute_reward(
    state: Dict,
    weights: RewardWeights,
    baseline_arc_power_mw: float = 90.0,
) -> RewardComponents:
    """Compute reward components from a telemetry-style state dict."""
    rc = RewardComponents()

    # Energy savings — current arc power vs baseline at current price
    arc_p = float(state.get("arc_power_mw", 0.0))
    price = float(state.get("electricity_price", 1.60))
    delta_kw = max(0.0, baseline_arc_power_mw - arc_p) * 1000.0
    rc.energy_savings_egp = delta_kw * price / 3600.0  # EGP per simulated second

    # Machine stress — wall + electrode hot zones
    wall = float(state.get("wall_panel_temp", 0.0))
    el_t = float(state.get("electrode_temp", 0.0))
    rc.machine_stress_penalty = (
        max(0.0, wall - 200.0) * 0.5
        + max(0.0, el_t - 2800.0) * 0.05
    )

    # Production delay — backlog at per-step opportunity cost.
    # The original 500.0 coefficient was paired with a stuck backlog=0 (env bug);
    # at the realistic backlog amplitude (1–5 heats), it dominated every other
    # signal at ~10⁶ per episode. 5.0 keeps this term in the same order of
    # magnitude as energy_savings/quality so PPO has gradient on every objective.
    backlog = int(state.get("production_backlog", 0))
    rc.production_delay_penalty = backlog * 5.0

    # Quality — bath temperature target window
    bath = float(state.get("furnace_bath_temp", 0.0))
    if 1600.0 <= bath <= 1650.0:
        rc.quality_bonus = 1.0
    else:
        rc.quality_bonus = 0.0

    # Electrode waste
    el_rate = float(state.get("electrode_consumption_kg", 0.0))
    rc.electrode_waste = el_rate * arc_p * 0.1

    # PF penalty
    rc.pf_penalty = float(state.get("pf_penalty_egp_per_hour_est", 0.0)) / 3600.0

    # Flat-pricing operational objectives. These make "do the right thing"
    # visible even when electricity price is constant: finish heats efficiently,
    # avoid idle drift, and keep the process stable without pushing equipment.
    cycle_eff = float(state.get("cycle_efficiency_pct", 85.0))
    stability = float(state.get("process_stability_score", 85.0))
    throughput = float(state.get("throughput_score", 85.0))
    idle_min = float(state.get("idle_minutes_today", 0.0))
    maint_risk = float(state.get("maintenance_risk_score", 0.0))
    thermal_stress = float(state.get("thermal_stress_index", 0.0)) / 100.0

    rc.productivity_bonus = max(0.0, (cycle_eff + throughput - 160.0) / 40.0)
    rc.process_stability_bonus = max(0.0, (stability - 75.0) / 25.0)
    rc.idle_time_penalty = min(10.0, idle_min * 0.05)
    rc.maintenance_risk_penalty = maint_risk * 15.0 + thermal_stress * 4.0

    rc.total = (
        weights.alpha * rc.energy_savings_egp
        - weights.beta * rc.machine_stress_penalty
        - weights.gamma * rc.production_delay_penalty
        + weights.delta * rc.quality_bonus
        - weights.epsilon * rc.electrode_waste
        - weights.zeta * rc.pf_penalty
        + weights.gamma * 0.35 * rc.productivity_bonus
        + weights.delta * 0.55 * rc.process_stability_bonus
        - weights.beta * rc.maintenance_risk_penalty
        - weights.gamma * 0.20 * rc.idle_time_penalty
    )
    return rc
