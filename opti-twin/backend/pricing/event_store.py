"""
Pricing Event Store — in-memory ring buffer for all DPE events.

Captures structural events (peak transitions, price spikes, DR lifecycle,
forecast updates, mode changes) and exposes a filter/search interface.
No external dependency — survives in Redis-only deployments.
"""
from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional

MAX_EVENTS = 500
SPIKE_PRICE_THRESHOLD = 2.0   # EGP — only flag spikes above this
SPIKE_JUMP_PCT = 15.0          # minimum % jump to qualify as a spike


class PricingEvent:
    __slots__ = (
        "ts", "event_kind", "payload", "label",
        "price_egp_kwh", "is_peak", "dr_status",
        "dr_type", "dr_payment_egp", "net_benefit_egp",
        "mode_from", "mode_to",
    )

    def __init__(self, event_kind: str, payload: Dict) -> None:
        self.ts: str = datetime.now(timezone.utc).isoformat()
        self.event_kind = event_kind
        self.payload = payload
        self.price_egp_kwh: Optional[float] = payload.get("price_egp_kwh")
        self.is_peak: Optional[bool] = payload.get("is_peak")
        self.dr_status: Optional[str] = payload.get("dr_status")
        self.dr_type: Optional[str] = payload.get("dr_type")
        self.dr_payment_egp: Optional[float] = payload.get("dr_payment_egp")
        self.net_benefit_egp: Optional[float] = payload.get("net_benefit_egp")
        self.mode_from: Optional[str] = payload.get("mode_from")
        self.mode_to: Optional[str] = payload.get("mode_to")
        self.label: str = _build_label(event_kind, payload)

    def to_dict(self) -> Dict:
        d: Dict = {
            "ts": self.ts,
            "event_kind": self.event_kind,
            "label": self.label,
        }
        # only include non-None top-level convenience fields
        if self.price_egp_kwh is not None:
            d["price_egp_kwh"] = self.price_egp_kwh
        if self.is_peak is not None:
            d["is_peak"] = self.is_peak
        if self.dr_status is not None:
            d["dr_status"] = self.dr_status
        if self.dr_type is not None:
            d["dr_type"] = self.dr_type
        if self.dr_payment_egp is not None:
            d["dr_payment_egp"] = self.dr_payment_egp
        if self.net_benefit_egp is not None:
            d["net_benefit_egp"] = self.net_benefit_egp
        if self.mode_from is not None:
            d["mode_from"] = self.mode_from
        if self.mode_to is not None:
            d["mode_to"] = self.mode_to
        d.update(self.payload)
        return d


def _build_label(kind: str, p: Dict) -> str:
    price = p.get("price_egp_kwh", 0.0)
    if kind == "peak_start":
        return f"ذروة بدأت — {price:.3f} جنيه/كيلوواط | Peak started — {price:.3f} EGP/kWh"
    if kind == "peak_end":
        return f"ذروة انتهت — {price:.3f} جنيه/كيلوواط | Peak ended — {price:.3f} EGP/kWh"
    if kind == "price_spike":
        jump = p.get("jump_pct", 0)
        return f"ارتفاع سعر +{jump:.0f}% — {price:.3f} | Price spike +{jump:.0f}% — {price:.3f} EGP/kWh"
    if kind == "dr_event":
        dr_type = p.get("dr_type", "")
        status = p.get("dr_status", "")
        payment = p.get("dr_payment_egp", 0.0) or 0.0
        if status == "ACCEPTED":
            return f"DR {dr_type} مقبول +{payment:.0f} جنيه | DR {dr_type} accepted +{payment:.0f} EGP"
        reason = p.get("decline_reason", "")
        return f"DR {dr_type} مرفوض | DR {dr_type} declined — {reason}"
    if kind == "forecast_update":
        mx = p.get("forecast_p50_max", 0.0)
        mn = p.get("forecast_p50_min", 0.0)
        return f"توقعات محدَّثة max {mx:.2f} / min {mn:.2f} | Forecast updated max {mx:.2f} / min {mn:.2f} EGP"
    if kind == "mode_change":
        return f"وضع التسعير: {p.get('mode_from','?')} ← {p.get('mode_to','?')} | Pricing mode: {p.get('mode_from','?')} → {p.get('mode_to','?')}"
    return kind


# ── Arabic / English synonym map for query expansion ─────────────────────────
_SYNONYMS: Dict[str, List[str]] = {
    "dr": ["demand response", "استجابة الطلب", "curtailment", "interruptible", "frequency"],
    "استجابة": ["dr", "demand response", "curtailment"],
    "ذروة": ["peak", "peak_start", "peak_end"],
    "peak": ["ذروة", "peak_start", "peak_end"],
    "spike": ["price_spike", "ارتفاع", "jump"],
    "ارتفاع": ["spike", "price_spike"],
    "forecast": ["forecast_update", "توقعات"],
    "توقعات": ["forecast", "forecast_update"],
    "mode": ["mode_change", "وضع"],
    "وضع": ["mode", "mode_change"],
}


def _expand_query(q: str) -> List[str]:
    """Return list of search tokens including synonym expansions."""
    tokens = q.lower().split()
    expanded = list(tokens)
    for t in tokens:
        for syn in _SYNONYMS.get(t, []):
            if syn not in expanded:
                expanded.append(syn)
    return expanded


class PricingEventStore:
    def __init__(self) -> None:
        self._events: Deque[PricingEvent] = deque(maxlen=MAX_EVENTS)
        self._lock = threading.Lock()
        self._last_is_peak: Optional[bool] = None
        self._last_price: Optional[float] = None

    # ── Ingest ────────────────────────────────────────────────────────────────

    def record_price_tick(self, price_data: Dict) -> None:
        """Called on every price_publisher cycle; emits only structural events."""
        price = float(price_data.get("price_egp_kwh", 1.60))
        is_peak = bool(price_data.get("is_peak", False))

        with self._lock:
            # Peak transition
            if self._last_is_peak is not None and is_peak != self._last_is_peak:
                kind = "peak_start" if is_peak else "peak_end"
                self._events.append(PricingEvent(kind, {
                    "price_egp_kwh": round(price, 4),
                    "is_peak": is_peak,
                    "price_source": price_data.get("price_source", ""),
                    "tariff_label": price_data.get("label", ""),
                }))

            # Price spike
            if (
                self._last_price is not None
                and price > SPIKE_PRICE_THRESHOLD
                and self._last_price > 0
                and (price / self._last_price - 1) * 100 >= SPIKE_JUMP_PCT
            ):
                self._events.append(PricingEvent("price_spike", {
                    "price_egp_kwh": round(price, 4),
                    "is_peak": is_peak,
                    "price_source": price_data.get("price_source", ""),
                    "prev_price_egp_kwh": round(self._last_price, 4),
                    "jump_pct": round((price / self._last_price - 1) * 100, 1),
                }))

            self._last_is_peak = is_peak
            self._last_price = price

    def record_forecast_update(self, forecast_data: Dict) -> None:
        steps = forecast_data.get("forecast", [])
        if not steps:
            return
        p50_vals = [float(s.get("p50", 1.60)) for s in steps]
        with self._lock:
            self._events.append(PricingEvent("forecast_update", {
                "forecast_p50_max": round(max(p50_vals), 3),
                "forecast_p50_min": round(min(p50_vals), 3),
                "steps": len(steps),
                "horizon_h": round(len(steps) * 0.5, 1),
            }))

    def record_dr_event(self, dr_event: Dict, assessment: Dict) -> None:
        with self._lock:
            self._events.append(PricingEvent("dr_event", {
                "dr_event_id": dr_event.get("event_id"),
                "dr_type": dr_event.get("event_type"),
                "dr_status": dr_event.get("status"),
                "dr_mw": dr_event.get("accepted_mw", 0.0),
                "dr_payment_egp": round(float(dr_event.get("payment_earned_egp", 0.0)), 1),
                "net_benefit_egp": round(float(dr_event.get("net_benefit_egp", 0.0)), 1),
                "duration_minutes": dr_event.get("duration_minutes"),
                "rate_egp_per_mwh": dr_event.get("rate_egp_per_mwh"),
                "decline_reason": dr_event.get("decline_reason"),
            }))

    def record_mode_change(self, from_mode: str, to_mode: str) -> None:
        with self._lock:
            self._events.append(PricingEvent("mode_change", {
                "mode_from": from_mode,
                "mode_to": to_mode,
            }))

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        q: Optional[str] = None,
        event_kind: Optional[str] = None,
        dr_status: Optional[str] = None,
        dr_type: Optional[str] = None,
        is_peak: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Dict]:
        with self._lock:
            snapshot = list(reversed(self._events))  # newest first

        tokens = _expand_query(q) if q else []

        results: List[Dict] = []
        for ev in snapshot:
            if event_kind and ev.event_kind != event_kind:
                continue
            if dr_status and (ev.dr_status or "").upper() != dr_status.upper():
                continue
            if dr_type and (ev.dr_type or "").upper() != dr_type.upper():
                continue
            if is_peak is not None and ev.is_peak != is_peak:
                continue
            if tokens:
                haystack = (
                    f"{ev.event_kind} {ev.label} "
                    f"{ev.dr_type or ''} {ev.dr_status or ''} "
                    f"{ev.mode_from or ''} {ev.mode_to or ''}"
                ).lower()
                if not any(tok in haystack for tok in tokens):
                    continue
            results.append(ev.to_dict())
            if len(results) >= limit:
                break

        return results

    def stats(self) -> Dict:
        with self._lock:
            evs = list(self._events)
        return {
            "total_events": len(evs),
            "peak_transitions": sum(1 for e in evs if e.event_kind in ("peak_start", "peak_end")),
            "price_spikes": sum(1 for e in evs if e.event_kind == "price_spike"),
            "dr_accepted": sum(1 for e in evs if e.event_kind == "dr_event" and e.dr_status == "ACCEPTED"),
            "dr_declined": sum(1 for e in evs if e.event_kind == "dr_event" and e.dr_status in ("DECLINED", "REJECTED")),
            "forecast_updates": sum(1 for e in evs if e.event_kind == "forecast_update"),
            "mode_changes": sum(1 for e in evs if e.event_kind == "mode_change"),
        }
