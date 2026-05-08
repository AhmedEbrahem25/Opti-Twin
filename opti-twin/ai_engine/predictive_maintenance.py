"""Predictive maintenance and flat-price operations evaluator.

This module is deliberately lightweight: it runs per telemetry frame inside the
AI service, uses only current process signals plus the optional anomaly score,
and returns an auditable assessment that can be attached to recommendations.
It is not a replacement for the M3 autoencoder; it turns M3 plus domain rules
into operator-facing maintenance risk, recovery actions, and efficiency scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


RiskLevel = str


@dataclass
class MaintenanceAssessment:
    risk_score: float
    risk_level: RiskLevel
    alert_type: Optional[str]
    fault_prediction: Optional[str]
    recommended_action: str
    safe_recovery_action: Optional[str]
    xai_reason_en: str
    xai_reason_ar: str
    operational_efficiency_score: float
    throughput_score: float
    process_stability_score: float
    thermal_stress_index: float
    reasons: List[str] = field(default_factory=list)

    @property
    def alert_active(self) -> bool:
        return self.risk_level in ("WARNING", "CRITICAL")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "maintenance_risk_score": round(self.risk_score, 3),
            "maintenance_risk_level": self.risk_level,
            "maintenance_alert": self.alert_type,
            "maintenance_fault_prediction": self.fault_prediction,
            "maintenance_recommended_action": self.recommended_action,
            "maintenance_safe_recovery_action": self.safe_recovery_action,
            "maintenance_xai_reason": self.xai_reason_en,
            "maintenance_xai_reason_ar": self.xai_reason_ar,
            "operational_efficiency_score": round(self.operational_efficiency_score, 1),
            "throughput_score": round(self.throughput_score, 1),
            "process_stability_score": round(self.process_stability_score, 1),
            "thermal_stress_index": round(self.thermal_stress_index, 1),
            "maintenance_reasons": list(self.reasons),
        }


def evaluate_maintenance(
    state: Dict[str, Any],
    *,
    anomaly_score: float = 0.0,
) -> MaintenanceAssessment:
    """Score failure risk and operational quality from one telemetry frame."""
    wall = float(state.get("wall_panel_temp", 0.0))
    bath = float(state.get("furnace_bath_temp", 0.0))
    electrode = float(state.get("electrode_temp", 0.0))
    cooling_out = float(state.get("cooling_water_outlet_temp", 35.0))
    cooling_flow = float(state.get("cooling_water_flow_lmin", 200.0))
    pf = float(state.get("power_factor", 0.92))
    grid_hz = float(state.get("grid_frequency", 50.0))
    vibration = float(state.get("vibration_mm_s", 2.0))
    cycle_eff = float(state.get("cycle_efficiency_pct", 85.0))
    idle_minutes = float(state.get("idle_minutes_today", 0.0))
    thermal_stress = float(state.get("thermal_stress_index", _thermal_stress_fallback(state)))
    backlog = int(state.get("production_backlog", 0))
    phase = str(state.get("status", ""))
    flags = state.get("crisis_flags") or {}

    reasons: list[str] = []

    thermal_risk = _clip01(thermal_stress / 100.0)
    vibration_risk = _clip01((vibration - 3.5) / 3.5)
    anomaly_risk = _clip01(anomaly_score)
    pf_risk = _clip01((0.92 - pf) / 0.20)
    grid_risk = _clip01((49.8 - grid_hz) / 0.35)
    cooling_risk = max(
        _clip01((cooling_out - 55.0) / 18.0),
        _clip01((180.0 - cooling_flow) / 100.0),
    )
    phase_risk = 0.15 if phase in ("BORE_DOWN", "MELTING_PHASE_1", "MELTING_PHASE_2") else 0.0
    crisis_risk = 0.45 if any(flags.values()) else 0.0

    risk = max(
        thermal_risk * 0.95,
        vibration_risk * 0.85,
        anomaly_risk * 0.90,
        grid_risk * 0.90,
        crisis_risk,
    )
    risk += 0.18 * cooling_risk + 0.10 * pf_risk + phase_risk
    risk = _clip01(risk)

    if thermal_risk >= 0.55:
        reasons.append(f"thermal stress index {thermal_stress:.0f}/100")
    if vibration_risk >= 0.35:
        reasons.append(f"vibration {vibration:.1f} mm/s")
    if anomaly_risk >= 0.45:
        reasons.append(f"anomaly score {anomaly_score:.2f}")
    if cooling_risk >= 0.35:
        reasons.append("cooling margin narrowing")
    if pf_risk >= 0.35:
        reasons.append(f"power factor {pf:.2f} below 0.92")
    if grid_risk >= 0.35:
        reasons.append(f"grid frequency {grid_hz:.2f} Hz")
    if any(flags.values()):
        reasons.append("active crisis flag")

    risk_level: RiskLevel
    alert_type: Optional[str] = None
    fault_prediction: Optional[str] = None
    recommended_action = "MONITOR"
    safe_recovery_action: Optional[str] = None

    if risk >= 0.75:
        risk_level = "CRITICAL"
        alert_type = "PREDICTED_FAILURE_RISK"
        fault_prediction = _fault_prediction(thermal_risk, vibration_risk, grid_risk, flags)
        recommended_action = "DERATE_AND_COOL"
        safe_recovery_action = "Reduce arc power, raise cooling flow, and request operator inspection."
    elif risk >= 0.55:
        risk_level = "WARNING"
        alert_type = "PREDICTIVE_MAINTENANCE"
        fault_prediction = _fault_prediction(thermal_risk, vibration_risk, grid_risk, flags)
        recommended_action = "STABILIZE_AND_INSPECT"
        safe_recovery_action = "Hold aggressive optimization and schedule inspection before next heat."
    elif risk >= 0.35:
        risk_level = "WATCH"
        recommended_action = "WATCH_TREND"
        safe_recovery_action = "Keep current setpoints and watch trend for two more telemetry windows."
    else:
        risk_level = "NOMINAL"
        recommended_action = "NONE"

    throughput_score = _clip_percent(
        92.0
        - min(20.0, idle_minutes * 0.35)
        - max(0, backlog) * 7.0
        + (6.0 if phase in ("MELTING_PHASE_1", "MELTING_PHASE_2", "REFINING") else 0.0)
    )
    process_stability_score = _clip_percent(
        100.0
        - thermal_stress * 0.45
        - abs(grid_hz - 50.0) * 45.0
        - max(0.0, 0.92 - pf) * 90.0
        - max(0.0, vibration - 3.0) * 5.0
    )
    operational_efficiency_score = _clip_percent(
        cycle_eff * 0.55 + throughput_score * 0.25 + process_stability_score * 0.20
    )

    reason_text = ", ".join(reasons) if reasons else "all critical signals remain inside the safe envelope"
    xai_en = (
        f"Maintenance risk {risk_level.lower()} ({risk:.2f}) because {reason_text}. "
        f"Recommended action: {recommended_action}. Safety envelope preserved by limiting "
        "arc-power increases when thermal, vibration, grid, or anomaly risk rises."
    )
    xai_ar = (
        f"مخاطر الصيانة {risk_level} ({risk:.2f}) بسبب {reason_text}. "
        f"الإجراء المقترح: {recommended_action}. يتم حفظ حدود السلامة عبر منع زيادة "
        "قدرة القوس عند ارتفاع الحرارة أو الاهتزاز أو اضطراب الشبكة أو مؤشر الشذوذ."
    )

    return MaintenanceAssessment(
        risk_score=risk,
        risk_level=risk_level,
        alert_type=alert_type,
        fault_prediction=fault_prediction,
        recommended_action=recommended_action,
        safe_recovery_action=safe_recovery_action,
        xai_reason_en=xai_en,
        xai_reason_ar=xai_ar,
        operational_efficiency_score=operational_efficiency_score,
        throughput_score=throughput_score,
        process_stability_score=process_stability_score,
        thermal_stress_index=thermal_stress,
        reasons=reasons,
    )


def should_optimize_flat_production(
    state: Dict[str, Any],
    assessment: MaintenanceAssessment,
) -> bool:
    """Return True when flat-price productivity optimization is safe."""
    if bool(state.get("is_peak", False)):
        return False
    if assessment.risk_score >= 0.35:
        return False
    if assessment.process_stability_score < 82.0:
        return False
    phase = str(state.get("status", ""))
    if phase not in ("BORE_DOWN", "MELTING_PHASE_1", "MELTING_PHASE_2", "REFINING"):
        return False
    bath = float(state.get("furnace_bath_temp", 1500.0))
    wall = float(state.get("wall_panel_temp", 120.0))
    arc = float(state.get("arc_power_mw", 0.0))
    backlog = int(state.get("production_backlog", 0))
    idle = float(state.get("idle_minutes_today", 0.0))
    efficiency = float(state.get("cycle_efficiency_pct", 85.0))
    return (
        arc < 102.0
        and wall < 185.0
        and bath < 1645.0
        and (backlog > 0 or idle > 4.0 or efficiency < 82.0 or arc < 82.0)
    )


def should_stabilize_process(
    state: Dict[str, Any],
    assessment: MaintenanceAssessment,
) -> bool:
    if assessment.risk_level in ("WARNING", "CRITICAL"):
        return True
    if assessment.process_stability_score < 78.0:
        return True
    wall = float(state.get("wall_panel_temp", 0.0))
    cooling_out = float(state.get("cooling_water_outlet_temp", 35.0))
    vibration = float(state.get("vibration_mm_s", 2.0))
    return wall >= 190.0 or cooling_out >= 58.0 or vibration >= 5.0


def _thermal_stress_fallback(state: Dict[str, Any]) -> float:
    wall = float(state.get("wall_panel_temp", 0.0))
    bath = float(state.get("furnace_bath_temp", 0.0))
    electrode = float(state.get("electrode_temp", 0.0))
    cooling = float(state.get("cooling_water_outlet_temp", 35.0))
    return min(
        100.0,
        max(0.0, wall - 170.0) * 0.55
        + max(0.0, bath - 1650.0) * 0.25
        + max(0.0, electrode - 2450.0) * 0.05
        + max(0.0, cooling - 52.0) * 0.7,
    )


def _fault_prediction(
    thermal_risk: float,
    vibration_risk: float,
    grid_risk: float,
    flags: Dict[str, Any],
) -> str:
    if flags.get("transformer_alarm") or grid_risk >= 0.6:
        return "Transformer or grid-stability stress may force a derate."
    if thermal_risk >= 0.65:
        return "Thermal stress could damage refractory or wall panels."
    if vibration_risk >= 0.55 or flags.get("electrode_break"):
        return "Abnormal vibration may indicate electrode or mechanical wear."
    return "Process drift may become an equipment fault without stabilization."


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _clip_percent(value: float) -> float:
    return max(0.0, min(100.0, float(value)))

