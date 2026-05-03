"""
Search REST endpoints.

All routes mounted under `/api/v1/search` per upgrade.md §12. The demo slice
exposes only:

  GET /api/v1/search                      — hybrid lexical + filter search
  GET /api/v1/search/health               — index status + doc count
  GET /api/v1/search/saved/default        — canonical "shift overrides" preset

Semantic search, NL parser, full saved-search CRUD, and the WS live channel
are R-phase (post-event).
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, time as dtime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from search.meili_client import MeiliWrapper
from search.schemas import SavedSearch

log = logging.getLogger("opti-twin.search.routes")

# Module-level handle set by `mount(app, meili)` from main.py at startup.
_meili: Optional[MeiliWrapper] = None

router = APIRouter(prefix="/api/v1/search", tags=["search"])

# Crude Arabic-codepoint detector used for lang=auto resolution.
_AR_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿ]")


def mount(meili_wrapper: MeiliWrapper) -> APIRouter:
    """Bind the module-level Meili handle. Call this once during app startup
    after the wrapper has connected and initialised the index."""
    global _meili
    _meili = meili_wrapper
    return router


# ── /search ─────────────────────────────────────────────────────────────────


@router.get("")
async def search(
    q: str = Query("", description="Free-text query"),
    types: Optional[str] = Query(None, description="csv: decision,crisis,safety_rollback"),
    severity: Optional[str] = Query(None, description="csv: info,warning,critical"),
    from_: Optional[datetime] = Query(None, alias="from", description="ISO 8601 lower bound"),
    to: Optional[datetime] = Query(None, description="ISO 8601 upper bound"),
    lang: str = Query("auto", description="en | ar | auto"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    if _meili is None or _meili.client is None:
        raise HTTPException(503, "search not available")

    type_list = _parse_csv(types)
    sev_list = _parse_csv(severity)
    use_ar = (lang == "ar") or (lang == "auto" and bool(_AR_RE.search(q or "")))

    crop_attrs = ["body_ar"] if use_ar else ["body_en"]
    t0 = time.monotonic()
    raw = _meili.search(
        q or "",
        types=type_list,
        severities=sev_list,
        ts_from=from_,
        ts_to=to,
        limit=limit,
        offset=offset,
        attributes_to_crop=crop_attrs,
        crop_length=30,
    )
    took_ms = int((time.monotonic() - t0) * 1000)

    results = []
    for hit in raw.get("hits", []):
        title = hit.get("title_ar" if use_ar else "title_en") or hit.get("title_en", "")
        snippet = ""
        formatted = hit.get("_formatted") or {}
        if use_ar:
            snippet = formatted.get("body_ar") or formatted.get("title_ar") or hit.get("body_ar", "")
        else:
            snippet = formatted.get("body_en") or formatted.get("title_en") or hit.get("body_en", "")
        ts_value = hit.get("ts")
        ts_iso = _ts_to_iso(ts_value)
        results.append({
            "id": hit.get("id"),
            "type": hit.get("type"),
            "ts": ts_iso,
            "severity": hit.get("severity"),
            "title": title,
            "snippet": snippet,
            "score": float(hit.get("_rankingScore", 0.0)),
            "deeplink": f"/?ts={ts_iso}&focus={hit.get('id')}",
        })

    facets = raw.get("facetDistribution") or {}
    total = int(raw.get("estimatedTotalHits") or len(results))
    next_offset = offset + limit if offset + limit < total else None

    return JSONResponse({
        "query": q,
        "took_ms": took_ms,
        "total": total,
        "results": results,
        "facets": facets,
        "next_offset": next_offset,
    })


# ── /search/health ──────────────────────────────────────────────────────────


@router.get("/health")
async def health():
    if _meili is None or _meili.client is None:
        return JSONResponse({"meili": "down", "docs": 0}, status_code=503)
    try:
        h = _meili.client.health()
        meili_status = "ok" if h.get("status") == "available" else "degraded"
    except Exception:
        meili_status = "down"
    stats = _meili.stats()
    return {"meili": meili_status, "docs": stats.get("docs", 0)}


# ── /search/saved/default ───────────────────────────────────────────────────

# Canonical default saved search per upgrade.md §11.3 — "safety overrides
# since shift start." Shift start = today 06:00 UTC for demo purposes.

_DEFAULT_SAVED = SavedSearch(
    id="shift_overrides",
    title_en="Safety overrides this shift",
    title_ar="تجاوزات السلامة هذه الوردية",
    query={
        "types": ["safety_rollback", "decision"],
        "severity": ["critical"],
        # `from` resolved per-request below to keep the timestamp fresh.
    },
)


@router.get("/saved/default")
async def saved_default():
    payload = _DEFAULT_SAVED.model_dump()
    payload["query"]["from"] = _shift_start_iso()
    return payload


# ── Helpers ─────────────────────────────────────────────────────────────────


def _parse_csv(s: Optional[str]) -> Optional[List[str]]:
    if not s:
        return None
    parts = [x.strip() for x in s.split(",") if x.strip()]
    return parts or None


def _ts_to_iso(value) -> str:
    """Meili stores `ts` as a UNIX int (we converted on upsert). Convert back
    to ISO 8601 for the API response."""
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    return str(value)


def _shift_start_iso() -> str:
    """Today 06:00 UTC — hardcoded shift boundary for demo."""
    now = datetime.now(timezone.utc)
    shift_start = datetime.combine(now.date(), dtime(6, 0), tzinfo=timezone.utc)
    if now < shift_start:
        # Before 06:00 — use yesterday's shift
        from datetime import timedelta
        shift_start -= timedelta(days=1)
    return shift_start.isoformat()
