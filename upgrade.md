# 🔍 OPTI-TWIN — UPGRADE PLAN: ULTRA PRO USER SEARCH ENGINE
> **Companion to:** `plan.md` (master plan) · `planing-v2.md` (ML system plan) · `ARCHITECTURE.md` (4-tier system)
> **Focus:** A first-class, factory-floor-grade search experience over every Opti-Twin artefact — XAI decisions, telemetry, episodes, crises, models, KPIs, tariffs, and operator notes.
> **Version:** 1.0 · **Created:** 2026-05-01 · **Days to Demo:** 7
> **Track:** Industry-Driven Challenges · NextCity AI Hack 2026 · Alamein International University

> **Why this upgrade exists.** Opti-Twin already produces a torrent of structured signal: 28,800 telemetry ticks per day per machine, every recommendation logged with its reward decomposition, every crisis event timestamped, every reward-weight retune by the operator captured. The operator's question is rarely "what is happening *right now*" — it is **"what happened the last time the wall hit 240 °C during a TOU peak window, and what did the agent do?"** A `Ctrl + F` over a single screen does not answer that. A real search engine does. This plan turns that capability into a flagship feature without compromising the 7-day demo timeline — a thin Day-1 slice ships during the hackathon, the rest becomes the post-event roadmap.

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Why a Search Engine Inside an Industrial Twin](#2-why-a-search-engine-inside-an-industrial-twin)
3. [Personas & Jobs-To-Be-Done](#3-personas--jobs-to-be-done)
4. [Feature Catalogue — The "Ultra Pro" Bar](#4-feature-catalogue--the-ultra-pro-bar)
5. [System Architecture (5-Layer Search Stack)](#5-system-architecture-5-layer-search-stack)
6. [Indexed Data Sources & Document Model](#6-indexed-data-sources--document-model)
7. [Indexing Pipeline (Real-Time + Backfill)](#7-indexing-pipeline-real-time--backfill)
8. [Query Layer — Lexical, Semantic, Structured, Natural-Language](#8-query-layer--lexical-semantic-structured-natural-language)
9. [Ranking, Relevance & Recency Boosts](#9-ranking-relevance--recency-boosts)
10. [Bilingual Search (English + Arabic)](#10-bilingual-search-english--arabic)
11. [UI / UX Specification](#11-ui--ux-specification)
12. [REST + WebSocket API Contracts](#12-rest--websocket-api-contracts)
13. [Saved Searches, Alerts & Subscriptions](#13-saved-searches-alerts--subscriptions)
14. [Security, RBAC & Audit Trail](#14-security-rbac--audit-trail)
15. [Performance Budget & Capacity Planning](#15-performance-budget--capacity-planning)
16. [Tech-Stack Decisions (with Trade-offs)](#16-tech-stack-decisions-with-trade-offs)
17. [Integration with the 4-Tier Architecture](#17-integration-with-the-4-tier-architecture)
18. [7-Day Execution Plan (Demo-Critical Slice)](#18-7-day-execution-plan-demo-critical-slice)
19. [Post-Hackathon Roadmap](#19-post-hackathon-roadmap)
20. [Risk Register](#20-risk-register)
21. [Appendix A — Sample Queries](#21-appendix-a--sample-queries)
22. [Appendix B — Document JSON Schemas](#22-appendix-b--document-json-schemas)
23. [Appendix C — Glossary](#23-appendix-c--glossary)

---

## 1. Executive Summary

The Ultra Pro Search Engine (`opti-search`) is a **dedicated retrieval microservice** added as a sixth concern alongside the existing 4-tier architecture. It indexes every document Opti-Twin emits — telemetry ticks, XAI decisions, crisis events, episode rollouts, model versions, reward-weight changes, KPI snapshots, tariff schedules, operator annotations — and exposes them through a single, fast, multilingual, hybrid (lexical + semantic + structured) search surface.

It is not a "log viewer with a filter box." It is the **operator's memory** — an instrument that turns months of furnace history into 200 ms answers. The flagship interaction is a global Command-Palette (`Ctrl + K`) on the dashboard; the second is a Search Console route for analysts and auditors.

### 1.1 Headline Capability Targets

| Dimension | Target | Confidence |
|---|---|---|
| Query latency p50 / p99 (50M docs) | **< 80 ms / < 250 ms** | ✔ Meilisearch / OpenSearch published benchmarks |
| Index freshness (event → searchable) | **< 1 s** | ✔ Redis Streams + push pipeline |
| Recall @ 10 (semantic eval set) | **≥ 0.92** | ⚠ Subject to embedding choice |
| MRR @ 10 (mixed lexical + semantic) | **≥ 0.78** | ⚠ Depends on ranker tuning |
| Languages supported at launch | English + Arabic (RTL-aware UI) | ✔ Tokenisers exist |
| Document types indexed at launch | 8 (see §6) | ✔ All already produced by core system |
| Concurrent search sessions | 200 active operators | ✔ Single-node baseline |
| Cold-start full re-index of 90 days | **< 15 min** | ⚠ Estimated on dev hardware |

### 1.2 What ships in the 7-day demo

The "demo slice" is intentionally small. It earns the WOW factor without putting the rest of the project at risk:

- ✅ Command-palette (`Ctrl + K`) on the React dashboard
- ✅ Hybrid search across **decisions** + **crisis events** + **episodes** (3 of 8 types)
- ✅ English + Arabic tokenisation
- ✅ Time-range and severity filters
- ✅ Result deep-links back into the dashboard timeline at the exact tick
- ✅ One saved-search → live banner ("3 new wall-overheat events this shift")

Everything else — semantic embeddings, NL query parser, RBAC, alerts, audit — is on the post-hackathon roadmap (§19) but designed for here, so the Day-1 slice is forward-compatible.

### 1.3 Why this is a credible WOW factor for judges

Industrial dashboards rarely have real search. Operators live with `find`-as-you-type drop-downs, hard-coded filter panels, and CSV exports. A judge who has ever worked in a SCADA environment will recognise — instantly — what `Ctrl + K → "wall overheat last shift in arabic"` returning sub-second results means. Combined with the existing AI core, the message becomes: *"Opti-Twin doesn't just decide — it remembers, and lets you interrogate that memory."*

---

## 2. Why a Search Engine Inside an Industrial Twin

### 2.1 The information-retrieval gap in process control

Plant operators are drowning in time-series data and starved of **context**. The questions they actually ask during a shift:

| Operator question | Today's answer | With Opti-Search |
|---|---|---|
| "Has the agent ever overridden me on a PRE_PEAK_DROP before?" | Scroll through 8 hours of XAI log | 1 query, 3 results, with timestamps |
| "Find the last wall overheat that happened during a TOU peak window" | Cross-reference two systems | Single hybrid query |
| "Which model version produced last Tuesday's record-low PF penalty?" | Ask the ML lead | Filter by `model_version` + KPI threshold |
| "Show all heats in the last 30 days where bath dropped below 1500 °C" | Manual SQL through DBA | Saved search, run on demand |
| "Did the synthetic preference oracle (M5) ever flip its rating on the same trajectory?" | Re-run training | Index + diff |

Each one is the kind of question that, today, takes minutes-to-hours and frequently goes unasked. A search surface compresses them to seconds.

### 2.2 The compounding value with the existing AI core

The AI core (M1–M5 in `planing-v2.md`) already produces **structured, schema-validated** events for every decision. This is the dream input for a search engine — clean, rich, dense in metadata. Layering search on top costs roughly an order of magnitude less effort than building search over raw SCADA dumps would.

### 2.3 Strategic — why this also helps the post-hackathon path

For the deployment path documented in `plan.md` §19 (shadow → advisory → closed-loop), the **single biggest blocker** is operator trust. Trust is built by transparency, and transparency is bottlenecked by retrievability. A search engine over the XAI log is the practical mechanism for "show me, not tell me" — which is what every reluctant plant manager actually wants.

---

## 3. Personas & Jobs-To-Be-Done

### 3.1 P1 — Shift Operator (primary)
- **Context:** 12-hour shift, 3 displays, hands on the HMI.
- **JTBD:** "When the agent does something I don't expect, I want to find out — fast — whether it has done this before, and what happened."
- **Critical query types:** recent decisions, recent alarms, "have I seen this".
- **Ergonomics:** keyboard-only flow; `Ctrl + K`; result preview on hover; single-click deep-link.

### 3.2 P2 — Energy Manager
- **Context:** Reviews KPI dashboards weekly; reports to CFO monthly.
- **JTBD:** "I need to slice savings and PF outcomes by tariff regime, model version, shift, and crisis-presence."
- **Critical query types:** structured filters, aggregations, exports.
- **Ergonomics:** Search Console route; CSV / Parquet export; saved-search digest.

### 3.3 P3 — ML Engineer (internal)
- **Context:** Iterating on model versions; debugging anomalies in eval scenarios.
- **JTBD:** "I want to find every transition where M3 anomaly score >0.8 but the policy still chose REDUCE_ARC_POWER — those are interesting bugs."
- **Critical query types:** complex structured + semantic; trajectory-level retrieval.
- **Ergonomics:** API access; programmatic queries; result exports for offline analysis.

### 3.4 P4 — Plant Manager / Auditor
- **Context:** Compliance reviews, incident post-mortems.
- **JTBD:** "I need an immutable, time-indexed record of who/what/when, in Arabic for our internal report and English for the EU CBAM auditor."
- **Critical query types:** date-bounded, full export, signed.
- **Ergonomics:** Search Console; bilingual switch; audit-export bundle.

### 3.5 P5 — Demo / Judge (event-only)
- **Context:** 3-minute demo, looking for the WOW factor.
- **JTBD:** "Convince me this team built something coherent in 7 days."
- **Critical query types:** anything that returns a fast, beautiful result.
- **Ergonomics:** the `Ctrl + K` interaction is the entire surface they see.

---

## 4. Feature Catalogue — The "Ultra Pro" Bar

A flat list, with each row tagged by phase: **D** = demo-critical (in the 7-day window), **R** = roadmap (post-hackathon), **F** = future / stretch.

| # | Feature | Phase |
|---|---|---|
| F01 | Global command palette (`Ctrl + K`, `⌘ + K`) | D |
| F02 | Hybrid search: BM25 lexical + dense vector + structured filters in one query | D |
| F03 | English + Arabic tokenisers (proper RTL handling, kashida-aware) | D |
| F04 | Time-range scoping (last hour / shift / day / week / 30 d / custom) | D |
| F05 | Severity / criticality filters (info → warning → critical) | D |
| F06 | Result deep-link → opens dashboard at the exact tick | D |
| F07 | Inline result preview (charts, action label, XAI snippet) | D |
| F08 | One default saved-search ("crises since shift start") wired to a banner | D |
| F09 | Synonym & abbreviation expansion (PF ↔ power factor, EAF ↔ furnace, etc.) | D |
| F10 | Typo tolerance (Damerau-Levenshtein 1–2) | D |
| F11 | Faceted search UI (counts per facet, drill-down) | R |
| F12 | Natural-language query parser ("show wall overheats during last TOU peak in arabic") | R |
| F13 | Saved searches with email / Slack / WhatsApp / on-screen alerts | R |
| F14 | Per-user RBAC scoped to plant / line / shift | R |
| F15 | Immutable audit log with hash-chained entries | R |
| F16 | CSV / Parquet / PDF export bundles | R |
| F17 | Search history with personal relevance weighting | R |
| F18 | Multilingual semantic embeddings (LaBSE / E5-mistral-multilingual) | R |
| F19 | Cross-document linking (a decision links to its episode, model version, forecast, anomaly score) | R |
| F20 | Trajectory-level retrieval ("find episodes that look like this one") via embedding the rollout | R |
| F21 | Agentic search ("explain this incident") — RAG over the index using the project's existing LLM | F |
| F22 | Anomaly-aware ranking — boost docs that are statistically rare given the query context | F |
| F23 | Voice query (Arabic + Egyptian dialect) on the HMI | F |
| F24 | Federated search across multiple plants (multi-tenant) | F |
| F25 | "Why did this rank here?" debug panel | R |
| F26 | Per-shift digest email at handover | R |
| F27 | OpenSearch / Meilisearch dual-write for graceful migration | R |
| F28 | Compliance pack (read-only audit URL valid for N days, signed) | R |

---

## 5. System Architecture (5-Layer Search Stack)

The search engine is **not** a fifth tier on top of the existing four — it sits *beside* the AI Core and the API Gateway, sharing Tier 2 (Redis) as its event source.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                  OPTI-TWIN — SEARCH STACK (UPGRADE)                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │  LAYER 1 — EVENT INGRESS                                             │   ║
║  │  Redis Streams: factory.telemetry, ai.decisions, ai.crisis,          │   ║
║  │                 ai.episodes, ai.kpi, ai.models, ops.notes            │   ║
║  └──────────────────────┬───────────────────────────────────────────────┘   ║
║                         │                                                    ║
║  ┌──────────────────────▼───────────────────────────────────────────────┐   ║
║  │  LAYER 2 — INDEXER (Python; consumer group `opti-search`)            │   ║
║  │  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │   ║
║  │  │ schema validate │→│ enrich + denorm  │→│ embed (lazy)     │    │   ║
║  │  │ (Pydantic)      │  │ (joins, derived) │  │ (D = none yet)   │    │   ║
║  │  └─────────────────┘  └──────────────────┘  └────────┬─────────┘    │   ║
║  │                                                       │              │   ║
║  └───────────────────────────────────────────────────────│──────────────┘   ║
║                                                          ▼                   ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │  LAYER 3 — INDEX                                                     │   ║
║  │  ┌─────────────────────┐    ┌─────────────────────┐                 │   ║
║  │  │ Meilisearch (D)     │    │ Postgres (canonical │                 │   ║
║  │  │ lexical + filters   │    │ + JSONB doc store)  │                 │   ║
║  │  │ ~50 ms p99 @ 50M    │    │ source of truth     │                 │   ║
║  │  └─────────────────────┘    └─────────────────────┘                 │   ║
║  │  ┌─────────────────────┐    ┌─────────────────────┐                 │   ║
║  │  │ Qdrant (R)          │    │ Redis (hot recents) │                 │   ║
║  │  │ dense vectors       │    │ last 24h cache      │                 │   ║
║  │  └─────────────────────┘    └─────────────────────┘                 │   ║
║  └──────────────────────┬───────────────────────────────────────────────┘   ║
║                         │                                                    ║
║  ┌──────────────────────▼───────────────────────────────────────────────┐   ║
║  │  LAYER 4 — SEARCH API (FastAPI service: opti-search)                 │   ║
║  │   GET   /search?q=…&filters=…                                         │   ║
║  │   POST  /search/nl   (NL → structured query)        [R]              │   ║
║  │   GET   /search/saved/{id}                          [R]              │   ║
║  │   WS    /ws/search/live  (saved-search alerts)      [R]              │   ║
║  │   GET   /search/health, /metrics                                     │   ║
║  └──────────────────────┬───────────────────────────────────────────────┘   ║
║                         │                                                    ║
║  ┌──────────────────────▼───────────────────────────────────────────────┐   ║
║  │  LAYER 5 — UI                                                        │   ║
║  │   • CommandPalette.tsx        (Ctrl+K, dashboard-global)             │   ║
║  │   • SearchConsole.tsx         (full-page route /search)              │   ║
║  │   • SavedSearchBanner.tsx     (top of dashboard)                     │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### 5.1 Why two indexes (Meilisearch + Qdrant) instead of one (OpenSearch with k-NN)

| Path | Pros | Cons | Decision |
|---|---|---|---|
| **OpenSearch (single index, lexical + k-NN)** | One service to operate | Heavyweight (JVM, ~2 GB RAM idle); slower to learn for the team in 7 days | ✗ Post-hackathon migration target only |
| **Meilisearch (lexical only)** | Sub-50 ms; trivial ops; Arabic supported; built-in typo tolerance, synonyms, faceting | No native vector search until v1.6 (basic) | ✓ Demo (D) |
| **Meilisearch + Qdrant (hybrid)** | Each tool best-in-class for its job | Two services | ✓ Roadmap (R) |
| **Postgres `pg_trgm` + `pgvector` only** | One service | Slow at 50M docs; weaker tokenisers | ✗ |

Meilisearch buys us speed in the 7-day window. Qdrant joins post-hackathon when we need semantic recall.

### 5.2 The Postgres canonical store

Every searchable document has a row in Postgres (JSONB blob + a few promoted columns). This is the **source of truth**. Meilisearch and Qdrant are derivable from it. If a search index goes corrupt, we re-index from Postgres in <15 min.

This separation also makes RBAC enforceable: filtering happens in Postgres after the search index returns IDs, not inside the search index where access control is harder to reason about.

---

## 6. Indexed Data Sources & Document Model

Eight document types ship across phases. Each is **already produced** by other parts of the system — the search service does not generate new data, it just makes existing data findable.

| # | Type | Source | Phase | Vol/day | Avg size |
|---|---|---|---|---|---|
| T1 | `decision` (XAI log) | `ai_engine.agent.decide()` | D | ~28,800 | ~1.2 KB |
| T2 | `crisis` (overheat, electrode, grid, transformer) | `simulator.crisis_engine` | D | 2–10 | ~0.8 KB |
| T3 | `episode` (heat-level rollup) | `ai_engine.collect_episodes` | D | ~24 | ~6 KB |
| T4 | `telemetry_anomaly` (M3 score >threshold) | `ai_engine.anomaly` | R | ~50 | ~0.5 KB |
| T5 | `model_version` (any time a model is retrained / promoted) | MLOps lifecycle | R | <1 | ~3 KB |
| T6 | `kpi_snapshot` (per-shift, per-day rollups) | `backend.kpi.aggregator` | R | 4–24 | ~2 KB |
| T7 | `tariff_event` (TOU mode change, rate update) | external feed / mock | R | <1 | ~1 KB |
| T8 | `operator_note` (manual annotation) | dashboard | R | ~10–50 | ~0.5 KB |

### 6.1 Common envelope (every doc)

```python
class SearchDoc(BaseModel):
    id: str                       # ULID; sortable by time
    type: Literal["decision", "crisis", "episode", "telemetry_anomaly",
                  "model_version", "kpi_snapshot", "tariff_event", "operator_note"]
    plant_id: str                 # for multi-tenant; "ezz_ain_sokhna" by default
    line_id: str | None           # e.g. "eaf_1"
    ts: datetime                  # UTC; primary time key
    sim_hour: float | None        # if produced inside a simulation
    severity: Literal["info", "warning", "critical"] | None
    title_en: str                 # 1-line summary, English
    title_ar: str                 # 1-line summary, Arabic
    body_en: str                  # full text, English (XAI string for decisions)
    body_ar: str                  # full text, Arabic
    tags: list[str]               # ["pf", "wall_overheat", "tou_peak", …]
    payload: dict                 # type-specific JSON (see §22)
    indexed_at: datetime
    schema_version: str = "1.0.0"
```

`title_*` and `body_*` are the lexical surface. `payload` is filterable but not full-text indexed (saves index size). `tags` is the cheapest, highest-leverage signal — every emitter is required to populate it.

### 6.2 Type-specific payloads

See [Appendix B](#22-appendix-b--document-json-schemas) for full schemas. Quick examples:

- **`decision`** payload: `{action_id, action_label, reward_total, reward_components, masked_by, model_version, forecast_summary, anomaly_score, episode_id, step_id}`
- **`crisis`** payload: `{kind, peak_temp, duration_sec, recovered_in_sec, related_decision_ids, related_episode_id}`
- **`episode`** payload: `{difficulty, total_steps, total_reward, energy_kwh, egp_saved_vs_baseline, pf_avg, crisis_count, model_version, completed: bool}`

---

## 7. Indexing Pipeline (Real-Time + Backfill)

### 7.1 Real-time path (event → searchable, <1 s)

```
Producer  ─┐
(agent,    │   XADD factory.events …
simulator, ├──────────────►  Redis Streams
backend)   │                       │
           │                       │  XREADGROUP opti-search
           │                       ▼
           │             ┌────────────────┐    upsert    ┌──────────┐
           │             │ Indexer worker │─────────────►│ Postgres │
           │             │ (asyncio)      │              └────────┬─┘
           │             └───────┬────────┘                       │
           │                     │ index                           │  CDC
           │                     ▼                                  ▼
           │             ┌────────────────┐                ┌──────────────┐
           │             │ Meilisearch    │                │ Qdrant       │
           │             └────────────────┘                │ (lazy embed) │
           │                                                └──────────────┘
```

- **Consumer group** `opti-search` with N=2 workers for HA.
- **At-least-once** delivery; deduped by `id` (ULID).
- **Acknowledgement** only after both Postgres write and Meilisearch upsert succeed.
- **Failure handling:** events that fail validation go to a dead-letter stream `opti-search.dlq` for replay after schema fixes.

### 7.2 Backfill path

For day-of-demo and any post-hackathon redeploys, a one-shot job re-reads Postgres and rebuilds Meilisearch + Qdrant indexes from scratch.

```bash
python -m opti_search.tools.reindex \
    --types decision,crisis,episode \
    --since 2026-04-01 \
    --batch 1000 \
    --target meilisearch,qdrant
```

Target: 50M docs in <15 min on dev hardware (single laptop). Achieved by 1000-doc batch upserts and disabling refresh during the run.

### 7.3 Embedding policy (R-phase only)

To control cost, embeddings are computed **lazily**:
- `decision`, `crisis`, `episode` always embedded on insert (semantic recall matters).
- `telemetry_anomaly`, `kpi_snapshot`, `tariff_event` embedded only on first query that needs vector recall (cache miss → compute → cache).
- `operator_note` embedded immediately (high-recall use case).

Model: **`intfloat/multilingual-e5-large-instruct`** — strong English + Arabic, 1024-dim, runs on CPU at ~100 docs/sec. Alternative if size is a problem: `intfloat/multilingual-e5-small` (384-dim, ~3× faster, modest recall hit).

---

## 8. Query Layer — Lexical, Semantic, Structured, Natural-Language

A single `/search` endpoint accepts a query plan; the service decides which engines to fan out to.

### 8.1 Query types

| Mode | Phase | Example | Engines used |
|---|---|---|---|
| **Lexical** | D | `"wall overheat"` | Meilisearch |
| **Lexical + filters** | D | `q: "wall overheat", filters: {ts: last_24h, severity: critical}` | Meilisearch |
| **Structured-only** | D | `filters: {type: decision, action_label: PRE_PEAK_DROP, model_version: v1.1.0}` | Meilisearch (filter mode) |
| **Semantic** | R | `"the agent did something weird around dinner time"` | Qdrant |
| **Hybrid** | R | lexical recall + dense rerank | Both, RRF-fused |
| **Natural-language** | R | `"show every PF below 0.85 during the last TOU peak window in march"` | NL parser → structured |

### 8.2 Reciprocal Rank Fusion (RRF) for hybrid

When both lexical and semantic candidate lists are produced, fuse them:

```python
def rrf_fuse(lexical_ids, semantic_ids, k=60):
    score = defaultdict(float)
    for rank, doc_id in enumerate(lexical_ids):
        score[doc_id] += 1 / (k + rank)
    for rank, doc_id in enumerate(semantic_ids):
        score[doc_id] += 1 / (k + rank)
    return sorted(score, key=score.get, reverse=True)
```

RRF is hyperparameter-light (only `k`), well-studied, and beats most learned-sparse fusion approaches at small data volumes.

### 8.3 NL query parser (R)

Two paths, picked by query length / complexity:

1. **Rule-based fast path** — regex + synonym dictionary handles 80% of queries (durations, type names, severities, action labels). Sub-millisecond.
2. **LLM fallback** — calls the project's existing LLM (`claude-haiku-4-5` if budget permits, otherwise local `qwen2.5-7b-instruct` quantised) with a structured-output schema. Caches results by query hash for 24 h.

The fast path always runs first; LLM is only called on miss. This bounds cost in production.

### 8.4 Synonym dictionary (D)

Stored as a small YAML file, hot-reloaded by the API:

```yaml
synonyms:
  - [pf, power factor, "معامل القدرة"]
  - [eaf, electric arc furnace, furnace, "فرن قوس كهربائي"]
  - [tou, time-of-use, peak/off-peak, "تعرفة زمنية"]
  - [pre_peak_drop, "خفض ما قبل الذروة"]
  - [reduce_arc_power, "خفض قدرة القوس"]
  - [emergency_cooling, "تبريد طارئ"]
```

Meilisearch ingests this directly; the same file feeds the NL parser's vocabulary.

### 8.5 Filter grammar

```
filters := key ":" op value [ "," filters ]
op      := "=" | "!=" | ">" | "<" | ">=" | "<=" | "in"
value   := literal | range | array
range   := "[" lo "," hi "]"
```

Example: `filters: type=decision, ts:[2026-04-01,2026-04-30], severity:in[warning,critical]`.

Parsed once into a `MeiliFilterDSL`; Postgres-equivalent generated lazily for the canonical-store path.

---

## 9. Ranking, Relevance & Recency Boosts

### 9.1 Default ranking (D)

Meilisearch's built-in ranking rules, in order:
1. `words` (more matched query terms first)
2. `typo` (fewer typos first)
3. `proximity` (matched terms closer together first)
4. `attribute` (matches in `title_*` outweigh `body_*`)
5. `sort: ts:desc` (recency, configurable)
6. `exactness`

For demo, this is enough. Operators expect "recent first" by default and that is what they get.

### 9.2 Custom ranking attributes (D)

Promote a few signals to first-class ranking inputs:
- `severity_score`: critical=3, warning=2, info=1 → boost
- `bookmark_count` (R): how many users have starred this doc
- `view_count` (R): with time-decay

### 9.3 Personalisation (R)

A per-user vector is learned from clicked results in their query history. At query time, this vector lightly re-ranks Top-50 candidates. Off by default; opt-in.

### 9.4 Anti-pattern alarms

Two ranking pathologies we will explicitly test for and prevent:
- **Recency dominance** drowning relevant older results. Mitigation: cap recency boost at `ts > query_time - 7d`; older results compete on relevance only.
- **Severity dominance** drowning all info-level matches when the user actually wants them. Mitigation: severity is a tie-breaker, not a multiplicative boost.

---

## 10. Bilingual Search (English + Arabic)

The Egyptian factory floor speaks Arabic; the engineering team and EU CBAM auditors read English. The index must natively serve both, not via Google-Translate-after-the-fact.

### 10.1 Tokenisation

- **Meilisearch** ships with Arabic tokenisation (kashida-stripped, NFKC-normalised) since v1.5. Verified on the Meilisearch docs language matrix.
- **Postgres** uses the `arabic` text-search config (or `simple` + custom dictionary for our domain terms).
- **Qdrant** is tokeniser-agnostic — we feed it embeddings, the model handles the script.

### 10.2 Bidirectional document fields

Every doc carries both `title_en` / `title_ar` and `body_en` / `body_ar`. Producers fill both; for the demo, the XAI engine already produces bilingual strings (per `plan.md` §1).

### 10.3 RTL UI

- Result rows auto-detect `dir="rtl"` per field.
- Highlight spans are computed per-language to avoid mid-word breakage on shaped Arabic glyphs.
- Time labels use Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩) when the UI locale is `ar-EG`, regular digits otherwise. Operator preference, not auto-locale.

### 10.4 Language-blind queries

Operator types `"بحث ⌘"` mid-English-session: the engine searches both `title_ar` + `body_ar` and `title_en` + `body_en` simultaneously, no language flag required. Handled by Meilisearch multi-attribute search.

---

## 11. UI / UX Specification

### 11.1 Command Palette (`Ctrl + K`) — D

The flagship surface. Mounted globally on the dashboard via a portal:

```
┌────────────────────────────────────────────────────────────────────┐
│  🔍  wall overheat                                          ⌘K     │
├────────────────────────────────────────────────────────────────────┤
│  TIME      | last 24h | last shift | this week | custom            │
│  TYPE      | all | decisions | crises | episodes                   │
│  SEVERITY  | all | critical | warning | info                       │
├────────────────────────────────────────────────────────────────────┤
│  🔥  Wall overheat — Panel #4, 247 °C @ 18:42                      │
│      crisis · critical · sim_hour 14.7 · 3 related decisions       │
│      "EMERGENCY_COOLING applied; bath stable in 41 s"              │
│  ──────────────────────────────────────────────────────────────────│
│  ⚡  Decision: EMERGENCY_COOLING — reward −0.21 (β override)       │
│      decision · warning · sim_hour 14.7 · model v1.1.0             │
│      "Wall panel 247 °C; β-weight forced cooling over cost"        │
│  ──────────────────────────────────────────────────────────────────│
│  📈  Episode #482 — total reward 184.3, 1 crisis                   │
│      episode · sim_hour 14.0–18.0 · medium difficulty              │
└────────────────────────────────────────────────────────────────────┘
   ↑↓ navigate   ↵ open   ⌫ filter   ⌘+enter open in console
```

- Opens in <100 ms (component already mounted; just unhide).
- First search debounced at 80 ms keystroke gap.
- Result rows are full Arrow-key navigable.
- `Enter` deep-links into the dashboard timeline at the doc's `ts`.
- `⌘ + Enter` opens the Search Console (full page) with the query pre-filled.

### 11.2 Search Console (full page) — R

Route: `/search`. Layout: 2-column.
- Left: query bar + facets (type, severity, model_version, plant, line, shift).
- Right: result list (virtualised, infinite scroll); preview pane below or to the right.
- Top bar: time-range scrubber linked to the dashboard timeline.

Power features:
- Keyboard-first: `j/k` scroll, `o` open, `s` save, `e` export, `?` help.
- Bulk select → export CSV / Parquet / PDF.
- Histogram showing result density over time.
- "Why this rank?" debug panel (toggle).

### 11.3 Saved-Search Banner — D (one default) / R (full)

A slim row at the top of the dashboard:

```
🔔  3 new wall-overheat events this shift   [view all]   [mute for 1h]   [edit]
```

Default saved search shipped with the demo: `type:crisis severity:critical ts:since_shift_start`.

### 11.4 Empty-state copy

The empty result state is not "no results." It is:
- A friendly tip (in the user's locale).
- Suggestions based on common searches.
- A "did you mean…" using the typo-corrector.
- A link to the synonym dictionary so power users can extend it.

### 11.5 Accessibility

- Full ARIA labels on the command palette.
- High-contrast theme honoured.
- Screen-reader-friendly result row (announces type + severity + title).
- Keyboard alternative for every mouse action.

---

## 12. REST + WebSocket API Contracts

All routes mounted under `/api/v1/search` on the existing FastAPI gateway, proxied to the `opti-search` service.

### 12.1 `GET /search`

Query params:

| param | type | required | example |
|---|---|---|---|
| `q` | str | ❌ (optional if filters) | `wall overheat` |
| `types` | csv | ❌ | `decision,crisis` |
| `from` | iso8601 | ❌ | `2026-04-01T00:00:00Z` |
| `to` | iso8601 | ❌ | `2026-04-30T23:59:59Z` |
| `severity` | csv | ❌ | `warning,critical` |
| `plant_id` | str | ❌ (RBAC may force) | `ezz_ain_sokhna` |
| `lang` | enum `en|ar|auto` | ❌ default `auto` | `ar` |
| `limit` | int | ❌ default 20, max 100 | `50` |
| `offset` | int | ❌ default 0 | `0` |
| `sort` | enum | ❌ default `relevance` | `ts:desc` |

Response (Pydantic schema `SearchResponse`):

```json
{
  "query": "wall overheat",
  "took_ms": 42,
  "total": 137,
  "results": [
    {
      "id": "01HXY…",
      "type": "crisis",
      "ts": "2026-04-29T18:42:11Z",
      "severity": "critical",
      "title": "Wall overheat — Panel #4, 247 °C @ 18:42",
      "snippet": "<em>Wall</em> panel #4 reached 247 °C…",
      "score": 0.91,
      "deeplink": "/dashboard?ts=2026-04-29T18:42:11Z&focus=01HXY…"
    }
  ],
  "facets": { "type": {"crisis": 12, "decision": 121, "episode": 4} },
  "next_offset": 20
}
```

### 12.2 `POST /search/nl` (R)

Body:
```json
{ "text": "show wall overheats during the last TOU peak window", "lang": "auto" }
```

Returns the parsed structured query plus the same payload as `GET /search`. Useful for the Search Console "explain my query" inspector.

### 12.3 `GET /search/saved`, `POST /search/saved`, `DELETE /search/saved/{id}` (R)

Saved searches CRUD. Body for POST:
```json
{
  "name": "Wall overheats this shift",
  "query": "wall overheat",
  "filters": {"severity": ["critical"], "ts_relative": "since_shift_start"},
  "alert": {"channel": "banner", "min_count": 1}
}
```

### 12.4 `WS /ws/search/live` (R)

Subscribes to a saved search; pushes `SearchHit` payloads as new events match. Reconnection with `Last-Event-Id` semantics.

### 12.5 `GET /search/health`, `GET /search/metrics`

- `/health`: returns `{meili: ok, postgres: ok, qdrant: ok|degraded, lag_ms: 312}`.
- `/metrics`: Prometheus exposition; key SLO counters in §15.

---

## 13. Saved Searches, Alerts & Subscriptions

(R-phase; design captured here so the D-phase one-default-saved-search doesn't paint us into a corner.)

### 13.1 Lifecycle

```
create → validate → store (postgres) → if alert: register watcher → live
                                                    │
                                          on each indexed doc:
                                          if doc matches saved query
                                          && rate-limit not hit
                                            → fan out to channels
```

### 13.2 Channels

| Channel | Mechanism | Latency |
|---|---|---|
| Banner (in-dashboard) | WS push to UI | <500 ms |
| Email | SMTP | <60 s |
| Slack | Slack Incoming Webhook | <5 s |
| WhatsApp | Twilio WhatsApp API (optional) | <30 s |
| HMI buzzer (factory floor) | OPC UA write (R-deployed only) | <1 s |

### 13.3 Rate limiting

Every saved search has a `rate_limit_per_hour` (default 10). Storms (e.g. 100 anomaly hits in 30 s during a real crisis) are coalesced into a single "10+ matches" alert with a deep-link to the full list.

### 13.4 Quiet hours

Per-user: no non-critical alerts during configured hours. Critical alerts always go through.

---

## 14. Security, RBAC & Audit Trail

### 14.1 Authentication

- Demo: shared session cookie issued by the dashboard's existing auth (mock for hackathon).
- Production: SSO via Keycloak / Auth0; JWT with `plant_ids`, `line_ids`, `role`, `lang` claims.

### 14.2 Authorisation matrix

| Role | Read | Write saved | Export | Audit | Manage synonyms |
|---|---|---|---|---|---|
| Operator | scoped to plant/line | self only | ❌ | ❌ | ❌ |
| Energy manager | plant-wide | self + team | ✓ | ❌ | ❌ |
| ML engineer | all | self | ✓ | ✓ | ✓ |
| Plant manager | plant-wide | self + team | ✓ | ✓ | ❌ |
| Auditor | read-only, time-bounded | ❌ | ✓ (signed) | ✓ | ❌ |

Filters injected server-side; the search index is never asked to enforce RBAC directly.

### 14.3 Audit trail

Every query (and its result count) is logged to a `search_audit` table with:
- `user_id`, `query`, `filters`, `result_count`, `took_ms`, `ts`, `ip`, `ua`, `request_id`.
- Hash-chained: each row carries `prev_hash` + `row_hash = sha256(prev_hash || row_canonical_json)`. Any tampering breaks the chain.
- Export bundles include the chain segment for the queried window.

### 14.4 Sensitive data

Operator notes can contain PII (names, contact info). The indexer runs a lightweight PII scrubber (regex for phone/email + a Pydantic validator) on `body_*` before writing to the index, and stores only the scrubbed copy. The full text remains in Postgres behind RBAC.

---

## 15. Performance Budget & Capacity Planning

### 15.1 SLOs

| Metric | Target | Alert at |
|---|---|---|
| `/search` p50 latency | < 80 ms | > 150 ms for 5 min |
| `/search` p99 latency | < 250 ms | > 500 ms for 5 min |
| Index lag (event → searchable) | < 1 s | > 5 s for 1 min |
| Indexer DLQ rate | < 0.01% events | > 0.1% in 1 h |
| Search availability | 99.5% (demo) / 99.9% (prod) | downtime alert |

### 15.2 Capacity baseline (single dev laptop, 16 GB RAM)

| Component | RAM | CPU | Disk @ 90d retention |
|---|---|---|---|
| Postgres | ~500 MB | low | ~12 GB |
| Meilisearch | ~1.5 GB | medium | ~6 GB |
| Qdrant (R) | ~2.0 GB | low | ~4 GB (1024-d × 5M docs) |
| Indexer worker | ~150 MB | medium | n/a |
| API service | ~100 MB | low | n/a |

90-day retention envelope: **~22 GB**. Below the threshold of "fits on a hackathon laptop without thinking about it."

### 15.3 Scale-out path (post-hackathon)

- Meilisearch supports horizontal sharding via index partitioning (one index per plant); operationally simple.
- Qdrant has native horizontal scaling.
- Postgres sharded by `plant_id` once we hit ~500M rows.

---

## 16. Tech-Stack Decisions (with Trade-offs)

| Concern | Pick | Why | Alternatives considered |
|---|---|---|---|
| Lexical engine | **Meilisearch v1.6+** | Sub-50 ms; trivial ops; Arabic ✓; built-in typo, synonym, faceting | Typesense (similar but Arabic weaker); OpenSearch (heavyweight); Postgres FTS (slow at scale) |
| Vector engine | **Qdrant v1.10+** | Strong filtering on payload; Rust core; gRPC + REST | Weaviate (heavier); Milvus (overkill); pgvector (slower at >1M docs) |
| Canonical store | **Postgres 16 + JSONB** | Already in the stack; great filtering; predictable | Mongo (would add ops); SQLite (single-writer) |
| Stream broker | **Redis Streams** (already deployed) | Reuse Tier 2; simple consumer groups | Kafka (overkill for a hackathon) |
| Embeddings | **multilingual-e5-large-instruct** | Strong Ar+En; CPU-runnable; 1024-d | LaBSE (older); BGE-M3 (great but heavier); OpenAI (cost / vendor lock) |
| API runtime | **FastAPI + Pydantic v2** | Matches existing tier-4 contracts | Litestar (similar; less team experience) |
| Indexer runtime | **asyncio + redis-py** | Single-process, simple | Celery (more moving parts); Faust (abandoned) |
| UI framework | **Existing React/Next.js** | No new dep | Solid / Svelte (would fragment) |
| Command-palette | **`cmdk` (radix-ui)** | Battle-tested; keyboard-first; small | kbar (older); custom (waste of time) |
| Telemetry | **OpenTelemetry → Prometheus + Grafana** | Standard | StatsD (legacy) |

### 16.1 Cost envelope

All-open-source. Zero vendor lock-in. Total external monthly cost in production: **0 EGP** for the search stack itself. The only paid optional dependency is the LLM-fallback NL parser (R), bounded by the existing project budget.

---

## 17. Integration with the 4-Tier Architecture

The search stack does not replace any existing tier; it composes:

| Existing tier | Search-stack interaction |
|---|---|
| **Tier 1 — Edge (simulator / SCADA)** | No direct touch. Already emits to Tier 2. |
| **Tier 2 — Streaming (Redis)** | Search indexer is a consumer group. **No producer changes required.** |
| **Tier 3 — AI Core** | Decisions and crises gain a new field `search_doc_id` for round-trip links. The XAI engine is amended to also produce the bilingual `title_*` / `body_*` strings if not already (it already does for `body_en` per `plan.md` §1). |
| **Tier 4 — App (FastAPI + React)** | New routes under `/api/v1/search/*`. Dashboard mounts the command palette. |

### 17.1 Docker-compose addition

```yaml
# docker-compose.yml — added services (excerpt)
services:
  meilisearch:
    image: getmeili/meilisearch:v1.10
    environment:
      - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
      - MEILI_ENV=development
    volumes: ["./data/meili:/meili_data"]
    ports: ["7700:7700"]

  qdrant:                       # phase R
    image: qdrant/qdrant:v1.10
    profiles: ["roadmap"]       # not started by default in D
    volumes: ["./data/qdrant:/qdrant/storage"]
    ports: ["6333:6333"]

  opti-search:
    build: ./services/opti-search
    environment:
      - REDIS_URL=redis://redis:6379
      - MEILI_URL=http://meilisearch:7700
      - PG_URL=postgresql://opti:opti@postgres:5432/opti
    depends_on: [redis, meilisearch, postgres]
    ports: ["8001:8001"]
```

`profiles: ["roadmap"]` lets the demo skip Qdrant entirely without removing the config — a single env flag flips it on later.

### 17.2 Repository layout addition

```
opti-twin/
├── services/
│   └── opti-search/
│       ├── opti_search/
│       │   ├── api/
│       │   │   ├── routes.py
│       │   │   └── schemas.py
│       │   ├── indexer/
│       │   │   ├── consumer.py
│       │   │   ├── enrich.py
│       │   │   └── embed.py        # R-phase
│       │   ├── search/
│       │   │   ├── meilisearch_backend.py
│       │   │   ├── qdrant_backend.py # R-phase
│       │   │   └── fusion.py         # R-phase
│       │   ├── config.py
│       │   └── main.py
│       ├── tests/
│       ├── Dockerfile
│       └── pyproject.toml
└── frontend/
    └── components/
        ├── search/
        │   ├── CommandPalette.tsx
        │   ├── SearchConsole.tsx       # R-phase
        │   └── SavedSearchBanner.tsx
        └── …
```

---

## 18. 7-Day Execution Plan (Demo-Critical Slice)

Aligned with the master 7-day plan in `plan.md` §12 and the ML plan in `planing-v2.md` §16. The search slice runs **in parallel** without blocking either.

| Day | Owner | Deliverable | Acceptance |
|---|---|---|---|
| **D1 — May 1** | Backend lead | docker-compose adds meili+postgres+opti-search skeleton; healthcheck ✓ | `curl :8001/search/health` returns OK |
| **D2 — May 2** | Backend lead | Indexer consumes `ai.decisions` + `ai.crisis` from Redis; Postgres write; Meili upsert | 1k synthetic events end-to-end <30 s |
| **D3 — May 3** | Backend lead + ML lead | Backfill of 90 simulated days; synonym file; bilingual fields wired | Lexical search returns Arabic and English correctly |
| **D4 — May 4** | Frontend lead | `CommandPalette.tsx` integrated; `Ctrl+K` opens; live results | Manual demo passes |
| **D5 — May 5** | Frontend + backend | Time-range + severity facets; deep-link to dashboard timeline | Click result → dashboard scrubs to ts |
| **D6 — May 6** | All | Default saved-search banner; performance pass (p99 <250 ms with 5M docs) | Load test: 200 RPS, p99 < SLO |
| **D7 — May 7** | All | Demo dry-runs; bilingual smoke test; one-pager screenshot for slide | 3 successful dry-runs; no Sev-1 issues |

### 18.1 Parallelism

- The search service has **zero new requirements on the AI core** for the D-slice. M1–M5 can land at their own pace.
- The simulator/agent already emit the events the indexer needs; only field naming has to be agreed (a 30-min schema review on D1).

### 18.2 Stop-loss criteria

If by **end of D3** the indexer is not ingesting at >100 events/s sustained, the team cuts the search slice from the demo and re-allocates the frontend lead's time to the existing dashboard polish. The decision is owned by the Backend lead and rubber-stamped by the team lead at the D3 stand-up. No emotion attached — the AI core is the show.

---

## 19. Post-Hackathon Roadmap

A 12-week plan for everything labelled R (and selected F) above.

| Week | Theme | Outcome |
|---|---|---|
| W1 | Qdrant integration | Vector search in shadow mode; recall metrics tracked |
| W2 | Hybrid (RRF) ranking | A/B test vs. lexical-only; promote when ≥+10 % MRR |
| W3 | NL parser (rule-based) | 80 % of common queries handled <1 ms |
| W4 | NL parser (LLM fallback) | Remaining 20 %; cost-bounded by cache |
| W5 | RBAC + multi-tenant | Plant-scoped reads enforced |
| W6 | Audit trail with hash-chain | First export bundle delivered to a friendly auditor |
| W7 | Saved searches + alerts (banner + email) | One operator-facing alert in production-pilot environment |
| W8 | CSV / Parquet / PDF export | Energy manager's monthly report autogenerated |
| W9 | Faceted UI + Search Console | Full /search route shipped |
| W10 | Trajectory-level retrieval (F20) | "Find episodes like this" demo to ML-lead |
| W11 | Personalisation (F17) | Per-user click model live |
| W12 | OpenSearch dual-write | Migration pre-flight for >100M-doc tenants |

---

## 20. Risk Register

| ID | Risk | P × I | Mitigation |
|---|---|---|---|
| SR1 | Meilisearch Arabic tokenisation produces poor results on domain terms | M × H | Domain synonym dictionary; manual eval set of 50 Ar queries on D3 |
| SR2 | Indexer drops events under load | L × H | Redis consumer-group at-least-once; DLQ + replay; load test on D6 |
| SR3 | Search latency dominates dashboard FCP because of cold start | M × M | Mount palette unhidden but invisible; pre-warm one query on app load |
| SR4 | Embeddings model too slow on team CPU | M × M | R-phase only; D-phase ships lexical-only; use `e5-small` if needed |
| SR5 | Schema drift breaks the index | L × H | Pydantic `schema_version`; automated reindex on bump |
| SR6 | Bilingual UI breaks RTL on mixed Arabic/English result rows | M × L | Per-field `dir` attribute + visual regression test on D6 |
| SR7 | Search service becomes a SPOF for the dashboard | M × M | UI degrades gracefully: command palette greys out with a toast, rest of dashboard unaffected |
| SR8 | Operator notes leak PII into export bundles | L × H | PII scrubber on indexing; audit row records redaction count |
| SR9 | Synonym file edits go uncommitted; demo regresses | L × M | Synonym file under `services/opti-search/synonyms/`; CI blocks merge if missing |
| SR10 | Judges ask for a feature on the F-list during Q&A | H × L | "On the post-hackathon roadmap, here's the design" — point to §19 |
| SR11 | Saved-search banner hides a more critical alarm | L × H | Z-index ordering: alarms always above; banner is `info` styled |
| SR12 | RBAC misconfiguration in demo environment leaks all docs to all users | L × H | Demo runs single-tenant with one role; multi-tenant gated behind `ENABLE_RBAC=true` |

---

## 21. Appendix A — Sample Queries

Copy-pasteable, intended for the demo dry-runs and the smoke test on D6.

```
# 1) Wall-overheat events in the last 24 h
q=wall overheat&types=crisis&from=now-24h&severity=critical

# 2) Every PRE_PEAK_DROP decision under model v1.1.0
q=&types=decision&filters=action_label=PRE_PEAK_DROP,model_version=v1.1.0

# 3) Bilingual synonym test — Arabic query, English+Arabic results
q=معامل القدرة&types=decision

# 4) Episodes with >10 % EGP saved
q=&types=episode&filters=egp_saved_pct:>0.10

# 5) Anomaly score >0.8 but the policy did REDUCE_ARC_POWER (regression hunt)
q=&types=decision,telemetry_anomaly&filters=anomaly_score:>0.8,action_label=REDUCE_ARC_POWER

# 6) "Show me everything weird in the last shift" — NL (R-phase)
POST /search/nl  body={"text":"show me everything weird in the last shift"}

# 7) Operator-note search across both languages
q=transformer alarm&types=operator_note

# 8) Audit export for the EU CBAM auditor (R-phase)
GET /search/export?from=2026-01-01&to=2026-12-31&types=kpi_snapshot,episode&format=pdf
```

---

## 22. Appendix B — Document JSON Schemas

Type-specific payloads. Common envelope from §6.1 omitted for brevity.

### 22.1 `decision`

```json
{
  "type": "decision",
  "payload": {
    "action_id": 4,
    "action_label": "PRE_PEAK_DROP",
    "reward_total": -0.21,
    "reward_components": {
      "energy": 0.12, "stress": -0.30, "delay": -0.05,
      "quality": 0.04, "wear": -0.01, "pf": -0.01
    },
    "masked_by": null,
    "model_version": "v1.1.0_2026-05-06_seed7",
    "forecast_summary": {"price_p50": 1.60, "price_p95": 1.92, "horizon_min": 30},
    "anomaly_score": 0.31,
    "episode_id": "ep_00482",
    "step_id": 1734
  }
}
```

### 22.2 `crisis`

```json
{
  "type": "crisis",
  "payload": {
    "kind": "wall_overheat",
    "peak_temp": 247.0,
    "duration_sec": 41,
    "recovered_in_sec": 41,
    "related_decision_ids": ["01HXY…01", "01HXY…02", "01HXY…03"],
    "related_episode_id": "ep_00482"
  }
}
```

### 22.3 `episode`

```json
{
  "type": "episode",
  "payload": {
    "difficulty": "medium",
    "total_steps": 480,
    "total_reward": 184.3,
    "energy_kwh": 81000,
    "egp_saved_vs_baseline": 12350.50,
    "egp_saved_pct": 0.107,
    "pf_avg": 0.89,
    "crisis_count": 1,
    "model_version": "v1.1.0_2026-05-06_seed7",
    "completed": true
  }
}
```

### 22.4 `telemetry_anomaly` (R)

```json
{
  "type": "telemetry_anomaly",
  "payload": {
    "score": 0.87,
    "channel": "wall_panel_temp",
    "window_start": "2026-04-29T18:40:00Z",
    "window_end": "2026-04-29T18:43:00Z",
    "model_version": "anomaly_v0.1.0"
  }
}
```

### 22.5 `model_version` (R)

```json
{
  "type": "model_version",
  "payload": {
    "model": "ppo",
    "version": "v1.1.0_2026-05-06_seed7",
    "promoted_at": "2026-05-06T10:00:00Z",
    "training_run_id": "tr_2025_05_06_001",
    "eval_summary": {"win_rate_vs_champion": 0.7, "safety_breaches": 0}
  }
}
```

### 22.6 `kpi_snapshot` (R)

```json
{
  "type": "kpi_snapshot",
  "payload": {
    "window": "shift",
    "egp_saved": 41250.00,
    "co2_saved_kg": 1200,
    "pf_avg": 0.91,
    "heats_completed": 8,
    "model_version": "v1.1.0"
  }
}
```

### 22.7 `tariff_event` (R)

```json
{
  "type": "tariff_event",
  "payload": {
    "kind": "tou_mode_on",
    "effective_at": "2026-06-01T00:00:00Z",
    "schedule_id": "egyptera_tou_2026_q3"
  }
}
```

### 22.8 `operator_note` (R)

```json
{
  "type": "operator_note",
  "payload": {
    "author_id": "op_amr",
    "shift_id": "shift_2026_05_06_night",
    "scope_ts": "2026-05-06T22:14:00Z",
    "redactions": 0
  }
}
```

---

## 23. Appendix C — Glossary

| Term | Meaning |
|---|---|
| BM25 | The classic lexical relevance model used by Lucene-family engines. |
| RRF | Reciprocal Rank Fusion — an unsupervised rank-aggregation method. |
| ULID | Universally Unique Lexicographically Sortable Identifier; preferred over UUID for time-ordered keys. |
| TOU | Time-of-Use tariff. |
| PF | Power Factor. |
| EAF | Electric Arc Furnace. |
| NFKC | Unicode normalisation form (compatibility composition). Used to canonicalise Arabic input. |
| Kashida | Arabic typographic elongation character; stripped during tokenisation. |
| RAG | Retrieval-Augmented Generation. |
| RBAC | Role-Based Access Control. |
| DLQ | Dead-Letter Queue. |
| SLO | Service-Level Objective. |
| MRR | Mean Reciprocal Rank. |
| FCP | First Contentful Paint (UI metric). |
| HMI | Human-Machine Interface (factory-floor terminal). |
| OPC UA | Industrial communication protocol used by SCADA / PLCs. |

---

*Built with 🔍 by Team Opti-Twin — NextCity AI Hack 2026*
*Eight document types, two languages, one Ctrl + K.*
