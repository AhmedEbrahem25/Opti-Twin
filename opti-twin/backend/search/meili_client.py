"""
Meilisearch client wrapper.

One index `opti_docs` for all three doc types (discriminated by `type` field).
Init configures searchable / filterable / sortable attributes, ranking rules,
and the synonym dictionary loaded from `synonyms.yaml`.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml
from meilisearch import Client

log = logging.getLogger("opti-twin.search.meili")

INDEX = "opti_docs"

MEILI_URL = os.getenv("MEILI_URL", "http://meilisearch:7700")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY", "opti-twin-demo-master-key")

# Resolve `synonyms.yaml` relative to this file
SYNONYMS_PATH = Path(__file__).resolve().parent / "synonyms.yaml"


SEARCHABLE_ATTRS = ["title_en", "title_ar", "body_en", "body_ar", "tags"]
FILTERABLE_ATTRS = [
    "type",
    "severity",
    "ts",
    "plant_id",
    "line_id",
    "payload.action_label",
    "payload.safety_reason",
    "payload.crisis_kind",
]
SORTABLE_ATTRS = ["ts", "indexed_at"]
RANKING_RULES = ["words", "typo", "proximity", "attribute", "sort", "exactness"]


class MeiliWrapper:
    """Synchronous facade. Meili calls are fast (<10 ms localhost); we run
    them inside `asyncio.to_thread` from the indexer when needed."""

    def __init__(self) -> None:
        self.client: Optional[Client] = None

    def connect(self, retries: int = 20, delay_sec: float = 1.5) -> None:
        last_exc: Optional[Exception] = None
        for attempt in range(retries):
            try:
                self.client = Client(MEILI_URL, MEILI_MASTER_KEY)
                health = self.client.health()
                if health.get("status") == "available":
                    log.info("Meilisearch reachable at %s", MEILI_URL)
                    return
            except Exception as exc:  # pragma: no cover
                last_exc = exc
            log.debug("Meili not ready (try %d/%d)", attempt + 1, retries)
            time.sleep(delay_sec)
        raise RuntimeError(f"Meilisearch unreachable at {MEILI_URL}: {last_exc}")

    def init_index(self) -> None:
        """Create the index if missing and apply settings + synonyms."""
        assert self.client is not None
        try:
            self.client.create_index(INDEX, {"primaryKey": "id"})
        except Exception:
            pass  # already exists

        idx = self.client.index(INDEX)
        idx.update_searchable_attributes(SEARCHABLE_ATTRS)
        idx.update_filterable_attributes(FILTERABLE_ATTRS)
        idx.update_sortable_attributes(SORTABLE_ATTRS)
        idx.update_ranking_rules(RANKING_RULES)

        synonyms = _load_synonym_groups(SYNONYMS_PATH)
        idx.update_synonyms(synonyms)

        # Stats best-effort (avoid failing init if Meili hasn't materialised yet)
        try:
            stats = idx.get_stats()
            n_docs = getattr(stats, "number_of_documents", None) or stats["numberOfDocuments"]
        except Exception:
            n_docs = 0
        log.info(
            "Meilisearch index ready (docs=%d, synonym_groups=%d)",
            n_docs, len(synonyms),
        )

    def upsert(self, docs: Sequence[Dict[str, Any]]) -> None:
        """Push documents to Meili. Async-style id-keyed upsert."""
        assert self.client is not None
        if not docs:
            return
        # Meili accepts `ts` and `indexed_at` as ISO strings; convert any datetime
        # objects defensively so the indexer can pass either.
        prepared = [_prepare(doc) for doc in docs]
        self.client.index(INDEX).add_documents(prepared)

    def search(
        self,
        q: str,
        *,
        types: Optional[List[str]] = None,
        severities: Optional[List[str]] = None,
        ts_from: Optional[datetime] = None,
        ts_to: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
        attributes_to_retrieve: Optional[List[str]] = None,
        attributes_to_crop: Optional[List[str]] = None,
        crop_length: int = 30,
    ) -> Dict[str, Any]:
        """Run a Meilisearch query. Returns the raw Meili response dict."""
        assert self.client is not None

        filters: List[str] = []
        if types:
            filters.append("(" + " OR ".join(f"type = {t!r}" for t in types) + ")")
        if severities:
            filters.append("(" + " OR ".join(f"severity = {s!r}" for s in severities) + ")")
        if ts_from is not None:
            filters.append(f"ts >= {int(ts_from.timestamp())}")
        if ts_to is not None:
            filters.append(f"ts <= {int(ts_to.timestamp())}")

        # Meili search API
        opts: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "showMatchesPosition": False,
            "attributesToHighlight": ["title_en", "title_ar", "body_en", "body_ar"],
            "highlightPreTag": "<em>",
            "highlightPostTag": "</em>",
        }
        if filters:
            opts["filter"] = filters
        if attributes_to_retrieve:
            opts["attributesToRetrieve"] = attributes_to_retrieve
        if attributes_to_crop:
            opts["attributesToCrop"] = attributes_to_crop
            opts["cropLength"] = crop_length
        # facetDistribution lets us return type/severity counts on each query
        opts["facets"] = ["type", "severity"]

        return self.client.index(INDEX).search(q or "", opts)

    def stats(self) -> Dict[str, Any]:
        assert self.client is not None
        try:
            stats = self.client.index(INDEX).get_stats()
            n = getattr(stats, "number_of_documents", None)
            if n is None and isinstance(stats, dict):
                n = stats.get("numberOfDocuments", 0)
            return {"docs": int(n or 0)}
        except Exception:
            return {"docs": 0}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _prepare(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime fields to UNIX timestamps so Meili can sort/filter them.

    Meilisearch sorts strings lexicographically — we want chronological order on
    `ts` and `indexed_at`. UNIX seconds work, and the JSON wire format stays
    cheap (an int instead of an ISO string).
    """
    out = dict(doc)
    for key in ("ts", "indexed_at"):
        v = out.get(key)
        if isinstance(v, datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            out[key] = int(v.timestamp())
        elif isinstance(v, str):
            try:
                # ISO 8601 with potential trailing Z
                out[key] = int(datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp())
            except Exception:
                pass  # leave raw; Meili will reject if invalid
    return out


def _load_synonym_groups(path: Path) -> Dict[str, List[str]]:
    """Convert the YAML synonym-group format to Meili's flat
    `{term: [synonyms]}` shape. Each group becomes N entries (one per term),
    each pointing at the rest of the group."""
    if not path.exists():
        log.warning("synonyms.yaml not found at %s; skipping", path)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    groups: List[List[str]] = data.get("synonyms", [])
    out: Dict[str, List[str]] = {}
    for group in groups:
        norm = [str(t).strip() for t in group if str(t).strip()]
        for term in norm:
            others = [t for t in norm if t.lower() != term.lower()]
            if not others:
                continue
            existing = out.get(term, [])
            out[term] = list(dict.fromkeys(existing + others))  # dedup, keep order
    return out
