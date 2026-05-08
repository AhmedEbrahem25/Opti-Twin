"""
Predictive Maintenance Engine for Opti-Twin EAF.

Four lightweight, stateful detectors run on every telemetry tick and emit
MaintenanceAlert objects when trend thresholds are crossed.  No ML model is
required — each detector uses a simple sliding-window slope or rate-of-change
test calibrated to the EAF operating envelope.

Alerts are published to the `maintenance.alerts` Redis channel by
agent_service.py so the backend can broadcast them over WebSocket and expose
them via the REST API.
"""

from __future__ import annotations

import datetime
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class MaintenanceAlert:
    alert_id: str
    timestamp: str
    machine_id: str
    alert_type: str          # "wall_temp_trend" | "electrode_wear" | "transformer_stress" | "refractory_age"
    severity: str            # "info" | "warning" | "critical"
    description_en: str
    description_ar: str
    recommended_action: str  # maps to an existing action label
    confidence_pct: float
    estimated_minutes_to_threshold: Optional[float]


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _alert(
    machine_id: str,
    alert_type: str,
    severity: str,
    en: str,
    ar: str,
    action: str,
    confidence: float,
    eta_min: Optional[float],
) -> MaintenanceAlert:
    return MaintenanceAlert(
        alert_id=str(uuid.uuid4()),
        timestamp=_now_iso(),
        machine_id=machine_id,
        alert_type=alert_type,
        severity=severity,
        description_en=en,
        description_ar=ar,
        recommended_action=action,
        confidence_pct=round(confidence, 1),
        estimated_minutes_to_threshold=round(eta_min, 1) if eta_min is not None else None,
    )


class WallTempTrendDetector:
    """
    Fires when wall panel temperature shows a sustained rising trend in the
    pre-critical zone (150–200°C), allowing preventive cooling before the
    250°C hard limit is reached.

    Slope is computed over a 5-step window (~15 real seconds at 3s intervals).
    """

    WINDOW = 5
    WARN_SLOPE_C_PER_STEP = 1.5   # °C per 3-second tick
    CRIT_SLOPE_C_PER_STEP = 3.0
    PRECRITIC_FLOOR_C = 150.0     # only fire when wall is already warm
    HARD_LIMIT_C = 250.0

    def __init__(self) -> None:
        self._history: deque[float] = deque(maxlen=self.WINDOW)

    def update(self, wall_temp_c: float, machine_id: str) -> Optional[MaintenanceAlert]:
        self._history.append(wall_temp_c)
        if len(self._history) < self.WINDOW:
            return None
        if wall_temp_c < self.PRECRITIC_FLOOR_C:
            return None

        slope = (self._history[-1] - self._history[0]) / (self.WINDOW - 1)
        if slope < self.WARN_SLOPE_C_PER_STEP:
            return None

        severity = "critical" if slope >= self.CRIT_SLOPE_C_PER_STEP else "warning"
        # Steps until hard limit at current rate
        steps_to_limit = (self.HARD_LIMIT_C - wall_temp_c) / slope if slope > 0 else None
        eta_min = (steps_to_limit * 3.0 / 60.0) if steps_to_limit is not None else None
        confidence = min(95.0, 60.0 + abs(slope) * 10.0)

        en = (
            f"Wall panel temperature trending upward at {slope:.1f}°C/step "
            f"(current {wall_temp_c:.0f}°C). "
            f"{'Imminent' if severity == 'critical' else 'Projected'} approach "
            f"to 250°C hard limit"
            + (f" in ~{eta_min:.0f} min." if eta_min else ".")
            + " Activating preventive cooling now avoids emergency shutdown."
        )
        ar = (
            f"درجة حرارة اللوح الجداري في ارتفاع بمعدل {slope:.1f}°م/خطوة "
            f"(الحالية {wall_temp_c:.0f}°م). "
            f"{'اقتراب وشيك' if severity == 'critical' else 'وصول متوقع'} "
            f"للحد الأقصى 250°م"
            + (f" خلال ~{eta_min:.0f} دقيقة." if eta_min else ".")
            + " التبريد الوقائي الآن يتجنب الإيقاف الطارئ."
        )
        return _alert(machine_id, "wall_temp_trend", severity, en, ar,
                      "EMERGENCY_COOLING", confidence, eta_min)


class ElectrodeWearMonitor:
    """
    Tracks electrode consumption rate. Fires when rate is anomalously high
    (e.g., after electrode_break crisis) or when accumulated daily consumption
    approaches a segment-change threshold.
    """

    NORMAL_RATE_KG_MIN = 0.05
    WARN_RATE_KG_MIN = 0.075
    CRIT_RATE_KG_MIN = 0.10
    SEGMENT_CHANGE_KG = 45.0   # typical electrode segment ~45 kg consumed before change

    def __init__(self) -> None:
        self._last_severity: Optional[str] = None

    def update(
        self, rate_kg_per_min: float, accumulated_kg: float, machine_id: str
    ) -> Optional[MaintenanceAlert]:
        if rate_kg_per_min <= 0:
            self._last_severity = None
            return None

        if rate_kg_per_min >= self.CRIT_RATE_KG_MIN:
            severity = "critical"
        elif rate_kg_per_min >= self.WARN_RATE_KG_MIN:
            severity = "warning"
        else:
            # Check accumulated threshold
            remaining = self.SEGMENT_CHANGE_KG - (accumulated_kg % self.SEGMENT_CHANGE_KG)
            if remaining < 5.0:
                severity = "info"
                en = (
                    f"Electrode segment approaching change threshold "
                    f"({accumulated_kg:.1f} kg consumed today, ~{remaining:.1f} kg to next change). "
                    f"Schedule segment replacement at next tap."
                )
                ar = (
                    f"الإلكترود يقترب من حد التغيير "
                    f"({accumulated_kg:.1f} كغ مستهلكة اليوم، ~{remaining:.1f} كغ للتغيير القادم). "
                    f"جدولة تغيير القطعة عند الصبة القادمة."
                )
                return _alert(machine_id, "electrode_wear", severity, en, ar,
                              "REDUCE_ARC_POWER", 70.0, remaining / self.NORMAL_RATE_KG_MIN)
            return None

        excess = rate_kg_per_min - self.NORMAL_RATE_KG_MIN
        confidence = min(95.0, 50.0 + (excess / self.NORMAL_RATE_KG_MIN) * 30.0)
        en = (
            f"Electrode consumption rate elevated: {rate_kg_per_min:.3f} kg/min "
            f"(normal <{self.NORMAL_RATE_KG_MIN} kg/min, "
            f"{(rate_kg_per_min / self.NORMAL_RATE_KG_MIN - 1) * 100:.0f}% above baseline). "
            + ("Possible electrode fracture — inspect immediately." if severity == "critical"
               else "Reducing arc power will slow wear and extend electrode life.")
        )
        ar = (
            f"معدل استهلاك الإلكترود مرتفع: {rate_kg_per_min:.3f} كغ/دقيقة "
            f"(الطبيعي <{self.NORMAL_RATE_KG_MIN} كغ/دقيقة، "
            f"{(rate_kg_per_min / self.NORMAL_RATE_KG_MIN - 1) * 100:.0f}% فوق الأساسي). "
            + ("احتمال كسر الإلكترود — افحص فوراً." if severity == "critical"
               else "تقليل القدرة سيبطئ التآكل ويطيل عمر الإلكترود.")
        )
        return _alert(machine_id, "electrode_wear", severity, en, ar,
                      "REDUCE_ARC_POWER", confidence, None)


class TransformerLoadMonitor:
    """
    Fires when arc power is sustained above the safe continuous rating (100 MW)
    for more than SUSTAINED_STEPS consecutive ticks (~15 seconds).
    """

    HIGH_LOAD_MW = 100.0
    SUSTAINED_STEPS = 5

    def __init__(self) -> None:
        self._high_count = 0

    def update(self, arc_power_mw: float, machine_id: str) -> Optional[MaintenanceAlert]:
        if arc_power_mw >= self.HIGH_LOAD_MW:
            self._high_count += 1
        else:
            self._high_count = 0
            return None

        if self._high_count < self.SUSTAINED_STEPS:
            return None

        severity = "critical" if self._high_count >= self.SUSTAINED_STEPS * 3 else "warning"
        sustained_sec = self._high_count * 3
        en = (
            f"Transformer sustained at {arc_power_mw:.1f} MW for {sustained_sec}s "
            f"(safe continuous rating: {self.HIGH_LOAD_MW} MW). "
            f"Prolonged overload accelerates insulation ageing. "
            f"Derate to ≤{self.HIGH_LOAD_MW} MW to protect transformer."
        )
        ar = (
            f"المحول يعمل عند {arc_power_mw:.1f} ميغاواط لمدة {sustained_sec} ثانية "
            f"(التقييم المستمر الآمن: {self.HIGH_LOAD_MW} ميغاواط). "
            f"الحمل الزائد المستمر يسرّع شيخوخة العزل. "
            f"قلل إلى ≤{self.HIGH_LOAD_MW} ميغاواط لحماية المحول."
        )
        return _alert(machine_id, "transformer_stress", severity, en, ar,
                      "TRANSFORMER_DERATE", min(95.0, 60.0 + self._high_count * 2.0), None)


class RefractoryAgeMonitor:
    """
    Tracks cumulative heats since last refractory reline. Modern EAF lining
    typically lasts 600–1000 heats; fires a warning at 700 and critical at 780.
    """

    WARN_HEATS = 700
    CRIT_HEATS = 780
    RELINE_INTERVAL = 800

    def update(self, age_heats: int, machine_id: str) -> Optional[MaintenanceAlert]:
        if age_heats < self.WARN_HEATS:
            return None

        severity = "critical" if age_heats >= self.CRIT_HEATS else "warning"
        remaining = max(0, self.RELINE_INTERVAL - age_heats)
        en = (
            f"Refractory lining age: {age_heats} heats "
            f"({'past warning threshold' if severity == 'warning' else 'APPROACHING REPLACEMENT LIMIT'}). "
            f"Approximately {remaining} heats remaining before mandatory reline. "
            f"Schedule reline during next planned maintenance window."
        )
        ar = (
            f"عمر بطانة الحرارية: {age_heats} صبّة "
            f"({'تجاوز عتبة التحذير' if severity == 'warning' else 'اقتراب من حد الاستبدال'}). "
            f"تبقى حوالي {remaining} صبّة قبل إعادة تبطين إلزامية. "
            f"جدول إعادة التبطين في نافذة الصيانة القادمة."
        )
        confidence = min(99.0, 70.0 + (age_heats - self.WARN_HEATS) * 0.3)
        return _alert(machine_id, "refractory_age", severity, en, ar,
                      "HOLD_STEADY", confidence, None)


class PredictiveMaintenanceEngine:
    """
    Aggregates all four detectors. Call `process(state)` on every telemetry
    tick. Returns a (possibly empty) list of MaintenanceAlert objects.
    """

    def __init__(self) -> None:
        self.wall = WallTempTrendDetector()
        self.electrode = ElectrodeWearMonitor()
        self.transformer = TransformerLoadMonitor()
        self.refractory = RefractoryAgeMonitor()

    def process(self, state: dict) -> list[MaintenanceAlert]:
        machine_id = state.get("machine_id", "unknown")
        alerts: list[MaintenanceAlert] = []

        wall_alert = self.wall.update(
            float(state.get("wall_panel_temp", 0.0)), machine_id
        )
        if wall_alert:
            alerts.append(wall_alert)

        elec_alert = self.electrode.update(
            float(state.get("electrode_consumption_kg", 0.0)),   # rate field
            float(state.get("electrode_consumption_today_kg", 0.0)),
            machine_id,
        )
        if elec_alert:
            alerts.append(elec_alert)

        trans_alert = self.transformer.update(
            float(state.get("arc_power_mw", 0.0)), machine_id
        )
        if trans_alert:
            alerts.append(trans_alert)

        refrac_alert = self.refractory.update(
            int(state.get("refractory_age_heats", 0)), machine_id
        )
        if refrac_alert:
            alerts.append(refrac_alert)

        return alerts
