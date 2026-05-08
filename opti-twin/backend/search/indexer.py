"""
Redis → Meilisearch indexer.

Three subscribers, one per Redis channel, all sharing a single MeiliWrapper.
Each emits its own doc type:

  ai.recommendation  → decision (when not HOLD_STEADY OR safety_overridden)
  ai.safety_rollback → safety_rollback
  ai.maintenance_alert → maintenance_alert
  factory.telemetry  → crisis (rising edge of any crisis_flag)

Reuses the existing async pub/sub pattern from `services/redis_broker.py`.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import ulid

from search.meili_client import MeiliWrapper
from services.redis_broker import RedisBroker

log = logging.getLogger("opti-twin.search.indexer")


# Action labels that escalate to "warning" severity even without a mask override.
_HIGH_SEVERITY_ACTIONS = {
    "EMERGENCY_COOLING",
    "GRID_RIDE_THROUGH",
    "TRANSFORMER_DERATE",
}


# Bilingual templates for crisis docs. Keyed by `crisis_kind`.
_CRISIS_TITLE = {
    "wall_overheat": (
        "Wall overheat — panel reached {wall:.0f}°C",
        "ارتفاع حرارة الجدار — اللوح بلغ {wall:.0f}°م",
    ),
    "grid_spike": (
        "Grid spike — frequency dropped to {freq:.2f} Hz",
        "تذبذب الشبكة — انخفض التردد إلى {freq:.2f} هرتز",
    ),
    "transformer_alarm": (
        "Transformer thermal alarm",
        "إنذار حراري للمحول",
    ),
}

_ROLLBACK_TITLE = (
    "Safety rollback — {count} consecutive overrides ({reason})",
    "تجاوز السلامة — {count} تجاوزات متتالية ({reason})",
)


class Indexer:
    def __init__(self, meili: MeiliWrapper, broker: RedisBroker) -> None:
        self.meili = meili
        self.broker = broker
        # Per-machine memory of last seen crisis_flags (for rising-edge detection).
        self._prev_flags: Dict[str, Dict[str, bool]] = {}
        self._counts = {
            "decision": 0,
            "crisis": 0,
            "safety_rollback": 0,
            "maintenance_alert": 0,
            "skipped": 0,
        }

    # ── Subscriber loops ─────────────────────────────────────────────────────

    async def consume_recommendations(self) -> None:
        log.info("Indexer subscribed to ai.recommendation")
        async for _, data in self.broker.subscribe("ai.recommendation"):
            try:
                doc = self._build_decision_doc(data)
                if doc is None:
                    self._counts["skipped"] += 1
                    continue
                await asyncio.to_thread(self.meili.upsert, [doc])
                self._counts["decision"] += 1
                if self._counts["decision"] % 25 == 1:
                    log.info(
                        "indexed decision %s (action=%s, severity=%s, total=%d)",
                        doc["id"], doc["payload"].get("action_label"),
                        doc["severity"], self._counts["decision"],
                    )
            except Exception as exc:  # pragma: no cover
                log.warning("decision indexing error: %s", exc)

    async def consume_safety_rollback(self) -> None:
        log.info("Indexer subscribed to ai.safety_rollback")
        async for _, data in self.broker.subscribe("ai.safety_rollback"):
            try:
                doc = self._build_rollback_doc(data)
                await asyncio.to_thread(self.meili.upsert, [doc])
                self._counts["safety_rollback"] += 1
                log.info(
                    "indexed safety_rollback %s (reason=%s, count=%s)",
                    doc["id"], doc["payload"].get("reason"),
                    doc["payload"].get("consecutive_overrides"),
                )
            except Exception as exc:  # pragma: no cover
                log.warning("safety_rollback indexing error: %s", exc)

    async def consume_maintenance_alerts(self) -> None:
        log.info("Indexer subscribed to ai.maintenance_alert")
        async for _, data in self.broker.subscribe("ai.maintenance_alert"):
            try:
                doc = self._build_maintenance_doc(data)
                await asyncio.to_thread(self.meili.upsert, [doc])
                self._counts["maintenance_alert"] += 1
                log.info(
                    "indexed maintenance_alert %s (risk=%s, level=%s)",
                    doc["id"], doc["payload"].get("risk_score"),
                    doc["payload"].get("risk_level"),
                )
            except Exception as exc:  # pragma: no cover
                log.warning("maintenance_alert indexing error: %s", exc)

    async def consume_telemetry_for_crises(self) -> None:
        log.info("Indexer subscribed to factory.telemetry (crisis-edge detection)")
        async for _, data in self.broker.subscribe("factory.telemetry"):
            try:
                docs = self._build_crisis_docs(data)
                if not docs:
                    continue
                await asyncio.to_thread(self.meili.upsert, docs)
                self._counts["crisis"] += len(docs)
                for doc in docs:
                    log.info(
                        "indexed crisis %s (kind=%s)",
                        doc["id"], doc["payload"].get("crisis_kind"),
                    )
            except Exception as exc:  # pragma: no cover
                log.warning("crisis indexing error: %s", exc)

    # ── Doc builders ────────────────────────────────────────────────────────

    def _build_decision_doc(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        action_label = str(data.get("action_label", "HOLD_STEADY"))
        safety_overridden = bool(data.get("safety_overridden", False))

        # Filter rule: skip noisy HOLD_STEADY decisions unless something interesting
        # happened (an override). Drops indexer volume by ~90%.
        if action_label == "HOLD_STEADY" and not safety_overridden:
            return None

        ts = _parse_ts(data.get("timestamp"))
        machine_id = str(data.get("machine_id") or "EAF_UNKNOWN")
        severity = (
            "critical" if safety_overridden
            else ("warning" if action_label in _HIGH_SEVERITY_ACTIONS else "info")
        )

        title_en = data.get("xai_reason") or _decision_title_en(action_label, safety_overridden)
        title_ar = data.get("xai_reason_ar") or _decision_title_ar(action_label, safety_overridden)

        body_en_parts = [
            f"action={action_label}",
            f"machine={machine_id}",
            f"health={data.get('machine_health', 'unknown')}",
        ]
        if safety_overridden:
            body_en_parts.append(f"override_reason={data.get('safety_reason')}")
            if data.get("raw_action_label"):
                body_en_parts.append(f"policy_wanted={data.get('raw_action_label')}")
        body_en = " · ".join(body_en_parts)

        tags = ["decision", action_label.lower(), severity]
        if safety_overridden:
            tags.append("override")
            if data.get("safety_reason"):
                tags.append(str(data["safety_reason"]))

        return {
            "id": str(ulid.new()),
            "type": "decision",
            "plant_id": "ezz_ain_sokhna",
            "line_id": machine_id,
            "ts": ts,
            "severity": severity,
            "title_en": title_en,
            "title_ar": title_ar,
            "body_en": body_en,
            "body_ar": title_ar,  # body in AR mirrors title for now (template engine is short)
            "tags": tags,
            "payload": {
                "action_label": action_label,
                "action_magnitude_pct": data.get("action_magnitude_pct"),
                "safety_overridden": safety_overridden,
                "safety_reason": data.get("safety_reason"),
                "raw_action_label": data.get("raw_action_label"),
                "machine_health": data.get("machine_health"),
                "estimated_savings_egp_per_hour": data.get("estimated_savings_egp_per_hour"),
                "dominant_reason": data.get("dominant_reason"),
            },
            "indexed_at": datetime.now(timezone.utc),
        }

    def _build_rollback_doc(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ts = _parse_ts(data.get("timestamp"))
        machine_id = str(data.get("machine_id") or "EAF_UNKNOWN")
        reason = str(data.get("reason") or "unknown")
        count = int(data.get("consecutive_overrides") or 0)

        en_tpl, ar_tpl = _ROLLBACK_TITLE
        title_en = en_tpl.format(count=count, reason=reason)
        title_ar = ar_tpl.format(count=count, reason=reason)

        return {
            "id": str(ulid.new()),
            "type": "safety_rollback",
            "plant_id": "ezz_ain_sokhna",
            "line_id": machine_id,
            "ts": ts,
            "severity": "critical",
            "title_en": title_en,
            "title_ar": title_ar,
            "body_en": (
                f"The safety mask overrode the policy {count} times in a row "
                f"(reason={reason}). Human review recommended."
            ),
            "body_ar": (
                f"تجاوزت طبقة السلامة قرار الوكيل {count} مرات متتالية "
                f"(السبب={reason}). يُوصى بالمراجعة البشرية."
            ),
            "tags": ["safety_rollback", "override", reason],
            "payload": {
                "reason": reason,
                "consecutive_overrides": count,
                "level": data.get("level", "critical"),
            },
            "indexed_at": datetime.now(timezone.utc),
        }

    def _build_maintenance_doc(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ts = _parse_ts(data.get("timestamp"))
        machine_id = str(data.get("machine_id") or "EAF_UNKNOWN")
        risk = float(data.get("risk_score") or 0.0)
        level = str(data.get("risk_level") or "WARNING")
        fault = str(data.get("fault_prediction") or "process drift detected")
        action = str(data.get("recommended_action") or "STABILIZE_AND_INSPECT")
        severity = "critical" if level == "CRITICAL" else "warning"
        title_en = f"Predictive maintenance {level.lower()} — risk {risk:.2f}"
        title_ar = data.get("xai_reason_ar") or title_en

        return {
            "id": str(ulid.new()),
            "type": "maintenance_alert",
            "plant_id": "ezz_ain_sokhna",
            "line_id": machine_id,
            "ts": ts,
            "severity": severity,
            "title_en": title_en,
            "title_ar": title_ar,
            "body_en": data.get("xai_reason") or fault,
            "body_ar": title_ar,
            "tags": ["maintenance", "predictive", level.lower(), action.lower()],
            "payload": {
                "alert_type": data.get("alert_type"),
                "risk_score": risk,
                "risk_level": level,
                "fault_prediction": fault,
                "recommended_action": action,
                "safe_recovery_action": data.get("safe_recovery_action"),
            },
            "indexed_at": datetime.now(timezone.utc),
        }

    def _build_crisis_docs(self, data: Dict[str, Any]) -> list:
        flags = data.get("crisis_flags") or {}
        if not flags:
            return []

        machine_id = str(data.get("machine_id") or "EAF_UNKNOWN")
        prev = self._prev_flags.setdefault(machine_id, {})

        ts = _parse_ts(data.get("timestamp"))
        wall = float(data.get("wall_panel_temp", 0.0))
        freq = float(data.get("grid_frequency", 50.0))

        docs = []
        for kind in ("wall_overheat", "grid_spike", "transformer_alarm"):
            now_on = bool(flags.get(kind, False))
            was_on = bool(prev.get(kind, False))
            if now_on and not was_on:  # rising edge
                en_tpl, ar_tpl = _CRISIS_TITLE[kind]
                fmt = {"wall": wall, "freq": freq}
                docs.append({
                    "id": str(ulid.new()),
                    "type": "crisis",
                    "plant_id": "ezz_ain_sokhna",
                    "line_id": machine_id,
                    "ts": ts,
                    "severity": "critical",
                    "title_en": en_tpl.format(**fmt),
                    "title_ar": ar_tpl.format(**fmt),
                    "body_en": (
                        f"Crisis kind={kind}, machine={machine_id}, "
                        f"wall={wall:.0f}°C, freq={freq:.2f}Hz."
                    ),
                    "body_ar": en_tpl.format(**fmt),
                    "tags": ["crisis", kind],
                    "payload": {
                        "crisis_kind": kind,
                        "wall_panel_temp": wall,
                        "grid_frequency": freq,
                        "arc_power_mw": data.get("arc_power_mw"),
                    },
                    "indexed_at": datetime.now(timezone.utc),
                })

        # Update memory after edge detection
        self._prev_flags[machine_id] = {k: bool(flags.get(k, False)) for k in flags}
        return docs

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def start_all(self) -> list[asyncio.Task]:
        return [
            asyncio.create_task(self.consume_recommendations(), name="idx-recs"),
            asyncio.create_task(self.consume_safety_rollback(), name="idx-rollback"),
            asyncio.create_task(self.consume_maintenance_alerts(), name="idx-maintenance"),
            asyncio.create_task(self.consume_telemetry_for_crises(), name="idx-crisis"),
        ]


# ── Helpers ─────────────────────────────────────────────────────────────────


def _parse_ts(value: Any) -> datetime:
    """Best-effort ISO 8601 parser; falls back to now() on bad input."""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            pass
    return datetime.now(timezone.utc)


def _decision_title_en(action: str, overridden: bool) -> str:
    base = action.replace("_", " ").lower().capitalize()
    return f"{base} (mask override)" if overridden else base


def _decision_title_ar(action: str, overridden: bool) -> str:
    map_ar = {
        "EMERGENCY_COOLING": "تبريد طارئ",
        "GRID_RIDE_THROUGH": "استجابة الشبكة",
        "TRANSFORMER_DERATE": "خفض المحول",
        "REDUCE_ARC_POWER": "خفض قدرة القوس",
        "PRE_PEAK_DROP": "خفض ما قبل الذروة",
        "RAISE_PF_COMPENSATION": "رفع معامل القدرة",
        "HOLD_STEADY": "ثبات",
    }
    base = map_ar.get(action, action)
    return f"{base} (تجاوز السلامة)" if overridden else base
