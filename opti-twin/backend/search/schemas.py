"""
Search document schemas.

Common envelope per upgrade.md §6.1. The Meili index `opti_docs` holds a
union of three doc types, distinguished by the `type` field. Demo slice
covers `decision`, `crisis`, `safety_rollback` — `episode`, `model_version`,
`kpi_snapshot`, `tariff_event`, `operator_note` and `pricing_event` are
post-event.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

DocType = Literal["decision", "crisis", "safety_rollback"]
Severity = Literal["info", "warning", "critical"]


class SearchDoc(BaseModel):
    """Common envelope for every searchable document."""

    id: str  # ULID; sortable by time
    type: DocType
    plant_id: str = "ezz_ain_sokhna"
    line_id: Optional[str] = None
    ts: datetime  # UTC
    sim_hour: Optional[float] = None
    severity: Severity = "info"
    title_en: str
    title_ar: str
    body_en: str = ""
    body_ar: str = ""
    tags: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    indexed_at: datetime
    schema_version: str = "1.0.0"


# ── Response shapes (per upgrade.md §12.1) ──────────────────────────────────


class SearchResultRow(BaseModel):
    id: str
    type: DocType
    ts: datetime
    severity: Severity
    title: str  # picked from title_en / title_ar based on lang resolution
    snippet: str
    score: float
    deeplink: str


class SearchResponse(BaseModel):
    query: str
    took_ms: int
    total: int
    results: List[SearchResultRow]
    facets: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    next_offset: Optional[int] = None


class SearchHealth(BaseModel):
    meili: str  # "ok" | "degraded" | "down"
    docs: int
    indexed_at_max: Optional[datetime] = None


class SavedSearch(BaseModel):
    id: str
    title_en: str
    title_ar: str
    query: Dict[str, Any]
