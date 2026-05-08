"""
Template-based Explainable AI engine.

Generates deterministic, auditable human-readable reasons for every
agent action — in English and Arabic. NOT an LLM.

Reasons are selected based on the dominant reward component contributing
to the action choice.
"""

from typing import Dict, Tuple


def _en(reason: str) -> str:
    return reason


def _ar(reason: str) -> str:
    return reason


# Reason templates — keyed by (action_label, dominant_reason).
TEMPLATES = {
    ("REDUCE_ARC_POWER", "pf_penalty"): {
        "en": "Power factor {pf:.2f} is below the 0.92 reference. Reducing arc power and adding reactive compensation to escape the EgyptERA penalty bracket. Bath at {bath:.0f}°C — safe.",
        "ar": "معامل القدرة {pf:.2f} أقل من المرجع 0.92. تقليل قدرة القوس وإضافة تعويض رد فعلي للخروج من شريحة الغرامة. الحوض عند {bath:.0f}°م - آمن.",
    },
    ("REDUCE_ARC_POWER", "energy_savings_egp"): {
        "en": "TOU peak pricing active ({price:.2f} EGP/kWh). Bath {bath:.0f}°C maintains liquidity above 1500°C. Backlog={backlog}. Reducing arc power saves est. {savings:.0f} EGP/hr.",
        "ar": "تسعير الذروة نشط ({price:.2f} ج.م/كيلوواط ساعة). الحوض {bath:.0f}°م يحافظ على السيولة. التراكم={backlog}. تقليل القدرة يوفر تقديرياً {savings:.0f} ج.م/ساعة.",
    },
    ("EMERGENCY_COOLING", "machine_stress"): {
        "en": "Wall panel {wall:.0f}°C exceeded 200°C threshold. β-weight override: machine protection takes priority over energy savings. Cooling to +120 l/min; reducing oxygen.",
        "ar": "اللوح الجداري {wall:.0f}°م تجاوز عتبة 200°م. تجاوز β-weight: حماية الآلة تتقدم على توفير الطاقة. زيادة التبريد +120 ل/د؛ تقليل الأكسجين.",
    },
    ("RAISE_PF_COMPENSATION", "pf_penalty"): {
        "en": "Power factor {pf:.2f} is in penalty bracket (Egypt PF ref 0.92). Engaging capacitor bank +10 MVAR to raise PF without sacrificing arc power.",
        "ar": "معامل القدرة {pf:.2f} في شريحة الغرامة (المرجع المصري 0.92). تشغيل بنك المكثفات +10 MVAR لرفع معامل القدرة دون التضحية بقدرة القوس.",
    },
    ("HOLD_STEADY", "stable"): {
        "en": "Phase {phase}, bath {bath:.0f}°C, PF {pf:.2f}, no constraint violation. Holding current setpoints; predicted reward stable.",
        "ar": "المرحلة {phase}، الحوض {bath:.0f}°م، PF {pf:.2f}، لا يوجد انتهاك. الحفاظ على نقاط الضبط الحالية.",
    },
    ("PRE_PEAK_DROP", "tou_window"): {
        "en": "Forecast TOU peak in <30 min. Pre-emptively dropping arc power to avoid peak billing. Heat at {progress:.0f}% — safe to slow.",
        "ar": "ذروة TOU متوقعة خلال أقل من 30 دقيقة. خفض القدرة وقائياً لتجنب فاتورة الذروة. الانصهار عند {progress:.0f}% - آمن للتباطؤ.",
    },
    ("GRID_RIDE_THROUGH", "machine_stress"): {
        "en": "Grid frequency {freq:.2f} Hz — outside safe band. Capping arc power at 60 MW for ride-through; awaiting frequency recovery.",
        "ar": "تردد الشبكة {freq:.2f} هرتز - خارج النطاق الآمن. تحديد قدرة القوس عند 60 ميغاواط للتعامل مع التذبذب.",
    },
    ("TRANSFORMER_DERATE", "machine_stress"): {
        "en": "Transformer thermal alarm. Capping MVA to 75 MW to extend insulation life. Anchored to known Nov 2024 EAF #2 transformer failure pattern.",
        "ar": "إنذار حراري للمحول. تحديد القدرة عند 75 ميغاواط لإطالة عمر العزل. مرتبط بنمط فشل محول EAF #2 المعروف في نوفمبر 2024.",
    },
    ("REDUCE_ARC_POWER", "dr_curtailment"): {
        "en": "Demand Response CURTAILMENT event accepted. Shedding {mw_shed:.0f} MW for {duration} min earns {dr_payment:.0f} EGP DR payment — net benefit {net:.0f} EGP after production cost.",
        "ar": "تم قبول طلب تخفيض الحمل من المشغل. تخفيض {mw_shed:.0f} ميغاواط لمدة {duration} دقيقة يكسب {dr_payment:.0f} ج.م — صافي الفائدة {net:.0f} ج.م.",
    },
    ("PRE_PEAK_DROP", "energy_savings_egp"): {
        "en": "Price forecast shows spike to {forecast_max:.2f} EGP/kWh in next 2h. Pre-emptively dropping arc {progress:.0f}% into heat. Anticipated savings: {savings:.0f} EGP/hr.",
        "ar": "توقعات الأسعار تظهر ارتفاعاً إلى {forecast_max:.2f} ج.م/كيلوواط ساعة خلال ساعتين. تخفيض استباقي للقوس بنسبة {progress:.0f}%. المدخرات المتوقعة: {savings:.0f} ج.م/ساعة.",
    },
    # ── Flat-tariff / predictive-maintenance templates ─────────────────────────
    ("REDUCE_ARC_POWER", "electrode_wear"): {
        "en": "Electrode consumption rate elevated ({el_rate:.3f} kg/min, normal <0.05 kg/min). Flat tariff — no load-shift value. Reducing arc power to conserve electrode and reduce wear-induced downtime risk.",
        "ar": "معدل استهلاك الإلكترود مرتفع ({el_rate:.3f} كغ/دقيقة، الطبيعي <0.05 كغ/دقيقة). التعريفة ثابتة — لا قيمة لنقل الحمل. تقليل القدرة للحفاظ على الإلكترود وتقليل مخاطر التوقف.",
    },
    ("EMERGENCY_COOLING", "wall_temp_trend"): {
        "en": "Wall temperature trending upward ({wall_trend:.1f}°C/step over last 15s, current {wall:.0f}°C). Activating preventive cooling before critical threshold (250°C). Flat tariff — equipment protection is primary objective.",
        "ar": "درجة حرارة الجدار في ارتفاع ({wall_trend:.1f}°م/خطوة خلال 15 ثانية، الحالية {wall:.0f}°م). تفعيل التبريد الوقائي قبل العتبة الحرجة (250°م). التعريفة ثابتة — حماية المعدات هي الهدف الأساسي.",
    },
    ("RAISE_PF_COMPENSATION", "pf_optimization"): {
        "en": "Power factor at {pf:.3f} under flat tariff ({price:.2f} EGP/kWh). Proactive compensation avoids EgyptERA penalty and maintains transmission efficiency. Estimated savings: {savings:.0f} EGP/hr.",
        "ar": "معامل القدرة {pf:.3f} في ظل التعريفة الثابتة ({price:.2f} ج.م/كيلوواط ساعة). التعويض الاستباقي يتفادى غرامة الهيئة المصرية ويحافظ على كفاءة النقل. مدخرات تقديرية: {savings:.0f} ج.م/ساعة.",
    },
    ("HOLD_STEADY", "production_optimal"): {
        "en": "All parameters within optimal range. Bath {bath:.0f}°C on track for tap target. Flat tariff ({price:.2f} EGP/kWh) — no load-shift advantage. PF {pf:.2f} within bounds. Maintaining current arc power for maximum throughput.",
        "ar": "جميع المعاملات ضمن النطاق الأمثل. الحوض {bath:.0f}°م في المسار الصحيح لهدف الصبة. التعريفة ثابتة ({price:.2f} ج.م/كيلوواط ساعة) — لا ميزة لنقل الحمل. معامل القدرة {pf:.2f} ضمن الحدود. الحفاظ على قدرة القوس الحالية لتحقيق أقصى إنتاجية.",
    },
}


def generate_reason(
    action_label: str,
    state: Dict,
    reward_components: Dict[str, float],
    dominant: str,
) -> Tuple[str, str]:
    """Return (english, arabic) explanation strings."""
    key = (action_label, dominant)
    template = TEMPLATES.get(key)
    if template is None:
        # Fallback generic
        en = f"ACTION={action_label}. State: bath={state.get('furnace_bath_temp', 0):.0f}°C, PF={state.get('power_factor', 0):.2f}."
        ar = f"إجراء={action_label}. الحالة: حوض={state.get('furnace_bath_temp', 0):.0f}°م، PF={state.get('power_factor', 0):.2f}."
        return en, ar
    fmt_args = {
        "bath": float(state.get("furnace_bath_temp", 0.0)),
        "wall": float(state.get("wall_panel_temp", 0.0)),
        "pf": float(state.get("power_factor", 0.0)),
        "price": float(state.get("electricity_price", 1.60)),
        "backlog": int(state.get("production_backlog", 0)),
        "phase": str(state.get("status", "")),
        "progress": float(state.get("heat_progress_pct", 0.0)),
        "freq": float(state.get("grid_frequency", 50.0)),
        "savings": float(reward_components.get("energy_savings_egp", 0.0)) * 3600.0,
        # Dynamic pricing extras
        "mw_shed": float(state.get("dr_mw_shed", 0.0)),
        "duration": int(state.get("dr_duration_min", 0)),
        "dr_payment": float(state.get("dr_payment_egp", 0.0)),
        "net": float(state.get("dr_net_egp", 0.0)),
        "forecast_max": float(state.get("forecast_max_price", 1.60)),
        # Flat-tariff / predictive-maintenance extras
        "el_rate": float(state.get("electrode_consumption_kg", 0.0)),
        "wall_trend": float(state.get("wall_temp_trend_c_per_step", 0.0)),
    }
    return (
        template["en"].format(**fmt_args),
        template["ar"].format(**fmt_args),
    )


def pick_dominant_component(reward_components: Dict[str, float]) -> str:
    """Choose which reward component dominates the action."""
    candidates = {
        "energy_savings_egp": reward_components.get("energy_savings_egp", 0.0),
        "pf_penalty": reward_components.get("pf_penalty", 0.0),
        "machine_stress": reward_components.get("machine_stress_penalty", 0.0),
        "production_delay": reward_components.get("production_delay_penalty", 0.0),
        "electrode_wear": reward_components.get("electrode_waste", 0.0),
        "stable": 0.001,  # ensure fallback
    }
    return max(candidates, key=lambda k: abs(candidates[k]))


def pick_dominant_for_action(action_label: str, state: Dict, reward_components: Dict[str, float]) -> str:
    """Context-aware dominant reason picker that handles flat-tariff signals."""
    tou_mode = state.get("tou_mode", False)

    # Flat-tariff-specific overrides: when TOU is off, map action triggers to
    # the correct template keys so bilingual XAI strings are accurate.
    if not tou_mode:
        el_rate = float(state.get("electrode_consumption_kg", 0.0))
        wall_trend = float(state.get("wall_temp_trend_c_per_step", 0.0))
        wall = float(state.get("wall_panel_temp", 0.0))
        pf = float(state.get("power_factor", 1.0))
        arc_p = float(state.get("arc_power_mw", 0.0))

        if action_label == "REDUCE_ARC_POWER" and el_rate > 0.075:
            return "electrode_wear"
        if action_label == "EMERGENCY_COOLING" and 150.0 <= wall < 250.0 and wall_trend > 1.0:
            return "wall_temp_trend"
        if action_label == "RAISE_PF_COMPENSATION" and pf < 0.93:
            return "pf_optimization"
        if action_label == "HOLD_STEADY":
            return "production_optimal"

    return pick_dominant_component(reward_components)
