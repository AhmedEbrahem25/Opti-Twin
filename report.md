# Opti-Twin — Full Project Report
### NextCity AI Hack 2026 | Industrial Digital Twin for EAF Energy Optimization
**Generated:** 2026-05-02 | **Updated:** 2026-05-02 | **Author:** Mahmoud Emad | **Status:** Dynamic Pricing Engine Implemented

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Technology Stack](#2-technology-stack)
3. [System Architecture](#3-system-architecture)
4. [Directory & File Map](#4-directory--file-map)
5. [File-by-File Explanation](#5-file-by-file-explanation)
6. [Data Flow Diagrams](#6-data-flow-diagrams)
7. [AI & Reward System Deep Dive](#7-ai--reward-system-deep-dive)
8. [Physics Simulation Model](#8-physics-simulation-model)
9. [API Contract Reference](#9-api-contract-reference)
10. [Frontend Dashboard Layout](#10-frontend-dashboard-layout)
11. [Configuration Reference](#11-configuration-reference)
12. [Business Case & KPIs](#12-business-case--kpis)
13. [Demo Script](#13-demo-script)
14. [Coming Soon Features](#14-coming-soon-features)
15. [Autonomous Decision Twin — Full Plan](#15-autonomous-decision-twin--full-plan)
16. [Dynamic Pricing Engine — Full Plan](#16-dynamic-pricing-engine--full-plan)
17. [Deployment Guide](#17-deployment-guide)
18. [Known Limitations & Tech Debt](#18-known-limitations--tech-debt)

---

## 1. Executive Summary

**Opti-Twin** is a **Multi-Objective Reinforcement Learning (MORL)** system embedded inside an **Industrial Digital Twin** for autonomous real-time energy optimization of Electric Arc Furnaces (EAFs) in Egyptian steel manufacturing.

**Target Facility:** Ezz Flat Steel — Ain Sokhna Complex, Egypt  
**Target Machine:** 185-tonne EAF #2 (1.6 Mtpa annual capacity)

**Core Promise:**
> Reduce electricity cost by **5–15%** while maintaining **100% production throughput** and machine safety — with every AI decision fully explained in English and Arabic.

**What Makes This Different:**
- Real-world verified data: EgyptERA Aug 2024 tariffs, Global Energy Monitor furnace specs, IEA grid CO₂ factors
- Bilingual Explainable AI (EN + AR) — every decision explained to the operator
- Fully Dockerized — runs on a laptop with zero external dependencies
- Industry-standard 4-tier architecture: Edge → Stream → AI Core → Application
- **Dynamic Pricing Engine (DPE) — now live:** multi-mode price signals (flat / TOU / synthetic spot), 24h forecast, Demand Response participation, 4-stream revenue stacking, and heat schedule optimizer — all implemented in code

---

## 2. Technology Stack

### Backend & AI

| Layer | Technology | Version | Role |
|-------|-----------|---------|------|
| Web Framework | FastAPI | 0.110.0 | REST API + WebSocket |
| ASGI Server | Uvicorn | 0.29.0 | HTTP runtime |
| Validation | Pydantic v2 | 2.6.4 | Schema enforcement |
| Message Broker | Redis | 7.0 Alpine | Pub/Sub streaming |
| RL Framework | Gymnasium + SB3 | 0.29.1 + 2.3.0 | RL environment + PPO training |
| RL Algorithm | PPO (PyTorch) | 2.2.2 | Policy inference |
| Numerics | NumPy | 1.26.4 | Physics simulation |
| HTTP Client | Requests | 2.31.0 | Intra-service calls |

### Frontend

| Layer | Technology | Version | Role |
|-------|-----------|---------|------|
| Framework | Next.js | 14.2.3 | SSR + routing |
| UI Library | React | 18.3.1 | Component tree |
| Charts | Recharts | 2.12.4 | Energy/thermal plots |
| Icons | Lucide React | 0.378.0 | Dashboard icons |
| CSS | Tailwind CSS | 3.4.3 | Utility-first styling |
| Language | TypeScript | 5.4.5 | Type safety |

### Infrastructure

| Component | Details |
|-----------|---------|
| Containerization | Docker + Docker Compose 3.9 |
| Services | 5 microservices: simulator, ai_engine, backend, frontend, redis |
| Network | Internal bridge: `opti-twin-network` |
| Exposed Ports | Backend: 8000 · Frontend: 3000 |
| Internal Ports | Redis: 6379 (isolated, not exposed to host) |

---

## 3. System Architecture

### 4-Tier Overview

```
╔══════════════════════════════════════════════════════════════════════╗
║                        OPTI-TWIN SYSTEM                             ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ┌──────────────────────────────────────────────────────────────┐   ║
║  │  TIER 4 — APPLICATION LAYER                                  │   ║
║  │  ┌─────────────────────┐   ┌──────────────────────────────┐  │   ║
║  │  │  FastAPI Backend    │   │  Next.js Dashboard           │  │   ║
║  │  │  :8000              │   │  :3000                       │  │   ║
║  │  │  REST + WebSocket   │◄──┤  KPIBanner, EnergyChart,     │  │   ║
║  │  │  8 endpoints        │   │  ThermalGauge, XAILog,       │  │   ║
║  │  │  KPI Aggregator     │   │  Controls, EAFStatus         │  │   ║
║  │  └──────────┬──────────┘   └──────────────────────────────┘  │   ║
║  └─────────────┼────────────────────────────────────────────────┘   ║
║                │ Subscribe                                           ║
║  ┌─────────────▼────────────────────────────────────────────────┐   ║
║  │  TIER 2 — STREAMING LAYER                                    │   ║
║  │  Redis Pub/Sub   :6379 (internal)                            │   ║
║  │  ┌────────────────────┐  ┌─────────────────────────────┐    │   ║
║  │  │ factory.telemetry  │  │ ai.recommendation           │    │   ║
║  │  │ (40 fields/3s)     │  │ (action + XAI reason)       │    │   ║
║  │  └────────────────────┘  └─────────────────────────────┘    │   ║
║  │  ┌────────────────────┐  ┌─────────────────────────────┐    │   ║
║  │  │ ai.control         │  │ sim.control                 │    │   ║
║  │  │ (AI on/off/profile)│  │ (crisis inject, tariff mode)│    │   ║
║  │  └────────────────────┘  └─────────────────────────────┘    │   ║
║  └──────────┬──────────────────────────┬────────────────────────┘   ║
║             │ Publish telemetry        │ Publish recommendation     ║
║  ┌──────────▼──────────┐   ┌───────────▼──────────────────────┐    ║
║  │  TIER 1 — EDGE      │   │  TIER 3 — AI CORE                │    ║
║  │  Factory Simulator  │   │  RL Engine                       │    ║
║  │                     │   │  ┌──────────────────────────┐    │    ║
║  │  EAFMachine         │   │  │ OptiTwinEAFEnv           │    │    ║
║  │  ThermalModel       │   │  │ 16-D obs / 5 actions     │    │    ║
║  │  EgyptGridPricing   │   │  ├──────────────────────────┤    │    ║
║  │                     │   │  │ OptiTwinAgent (PPO+Scr.) │    │    ║
║  │  7 Heat Phases      │   │  ├──────────────────────────┤    │    ║
║  │  Physics-grounded   │   │  │ RewardFunction (MORL)    │    │    ║
║  │  Crisis events      │   │  ├──────────────────────────┤    │    ║
║  │  Time-warp ×15      │   │  │ XAIEngine (EN + AR)      │    │    ║
║  └─────────────────────┘   └──────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Service Dependency Graph

```
          ┌─────────┐
          │  redis  │  (starts first, health-checked)
          └────┬────┘
               │ depends-on
    ┌──────────┴──────────┐
    ▼                     ▼
┌──────────┐        ┌───────────┐
│ai_engine │        │  backend  │
└────┬─────┘        └─────┬─────┘
     │ publishes           │ subscribes
     └──────────┬──────────┘
                │
     ┌──────────┴──────────┐
     ▼                     ▼
┌──────────┐        ┌───────────┐
│simulator │        │ frontend  │
└──────────┘        └───────────┘
```

### Request Lifecycle

```
Simulator (3s)
    │
    ├─ POST /api/v1/telemetry ──► Backend ──► Redis: factory.telemetry
    │                                                      │
    │                                         AI Engine subscribes
    │                                                      │
    │                                         Agent.decide(obs)
    │                                                      │
    │                                         XAI.explain(action)
    │                                                      │
    │                                         Redis: ai.recommendation
    │                                                      │
    │◄────────────── Backend subscribes ───────────────────┘
    │
    └─ WebSocket /ws/live-feed ──► Dashboard (real-time)
```

---

## 4. Directory & File Map

```
opti-twin/
│
├── README.md                      Project overview and quick-start
├── ARCHITECTURE.md                Detailed 4-tier design doc
├── docker-compose.yml             All 5 services, network, health-checks
├── .env.example                   Complete config template (44 variables)
│
├── simulator/                     ─── TIER 1: EDGE LAYER ───
│   ├── factory_sim.py             Main simulation loop + telemetry builder
│   ├── requirements.txt           numpy, requests, redis, pydantic
│   ├── machines/
│   │   ├── eaf_machine.py         Heat phase state machine (291 lines)
│   │   ├── eaf_thermal_model.py   Energy-balance thermal equations (86 lines)
│   │   └── egypt_grid_pricing.py  EgyptERA tariff + TOU proposal (115 lines)
│   └── events/
│       ├── overheat_event.py      Wall overheat crisis trigger
│       ├── electrode_break.py     Electrode break crisis trigger
│       ├── grid_spike_event.py    Grid frequency crisis trigger
│       └── transformer_alarm.py   Transformer MVA cap crisis trigger
│
├── ai_engine/                     ─── TIER 3: AI CORE ───
│   ├── environment.py             OptiTwinEAFEnv Gymnasium env (138 lines)
│   ├── agent.py                   OptiTwinAgent PPO + scripted (200 lines)
│   ├── reward_function.py         Multi-objective reward (103 lines)
│   ├── xai_engine.py              Template-based EN+AR explainer (100 lines)
│   ├── requirements.txt           gymnasium, stable-baselines3, torch
│   └── models/
│       └── opti_twin_ppo.zip      Pre-trained PPO model (frozen for demo)
│
├── backend/                       ─── TIER 4: API ───
│   ├── main.py                    FastAPI routes + WebSocket + 8 DPE endpoints
│   ├── api_contracts/
│   │   └── schemas.py             Pydantic models (incl. DPE schemas)
│   ├── services/
│   │   ├── redis_broker.py        Async Pub/Sub wrapper
│   │   └── kpi_calculator.py      Running KPI aggregator (+ DR revenue)
│   ├── pricing/                   ─── DYNAMIC PRICING ENGINE (NEW) ───
│   │   ├── __init__.py
│   │   ├── synthetic_spot_generator.py  Egyptian intraday spot price simulator
│   │   ├── price_signal_broker.py       Multi-mode price signal (flat/TOU/spot/live)
│   │   ├── demand_response_controller.py DR event lifecycle + net benefit calc
│   │   ├── load_flexibility_scheduler.py Greedy multi-heat schedule optimizer
│   │   └── revenue_optimizer.py         4-stream revenue tracker & stacker
│   ├── requirements.txt           fastapi, uvicorn, pydantic, redis
│   └── Dockerfile
│
├── frontend/                      ─── TIER 4: DASHBOARD ───
│   ├── package.json               Dependencies (Next.js, React, Recharts)
│   ├── pages/
│   │   ├── index.tsx              Main dashboard page (+ DynamicPricingPanel)
│   │   └── _app.tsx               App wrapper + global providers
│   ├── components/
│   │   ├── KPIBanner.tsx          6 metric cards (savings, cost, bath, PF…)
│   │   ├── EnergyChart.tsx        Recharts arc power line chart
│   │   ├── ThermalGauge.tsx       Bath + wall temp gauge bars
│   │   ├── EAFStatusCard.tsx      Machine metadata, phase, batch count
│   │   ├── XAIDecisionLog.tsx     Scrollable AI decision log EN/AR
│   │   ├── Controls.tsx           AI/TOU/profile/crisis toggle panel
│   │   └── DynamicPricingPanel.tsx  NEW — live price, forecast, revenue, DR, schedule
│   ├── lib/
│   │   ├── ws.ts                  useLiveFeed WebSocket hook (+ LivePrice type)
│   │   └── api.ts                 API client helpers (+ 8 DPE functions)
│   ├── styles/
│   │   └── globals.css            Global Tailwind + custom tokens
│   ├── tailwind.config.js         Steel/flame color palette
│   ├── tsconfig.json              Strict TypeScript config
│   └── Dockerfile
│
├── data/
│   └── tariffs/
│       └── egypt_industrial_2026.json  EgyptERA tariff data + TOU proposal
│
└── docs/
    ├── demo-scenario.md           3-minute live demo script
    ├── planing-v2.md              Post-hackathon roadmap
    ├── upgrade.md                 Search engine + feature upgrade plan
    └── diagrams/                  Architecture PNG diagrams
```

---

## 5. File-by-File Explanation

### `docker-compose.yml`
Orchestrates all 5 services in a single file. Defines startup order (redis → ai_engine → backend → simulator → frontend), internal bridge network `opti-twin-network`, port bindings, and Redis health-check probe. No external volumes are mounted — the system is fully stateless.

---

### `.env.example`
Complete template for all 44 environment variables. Covers service ports, simulation timing (time-warp factor), Egyptian electricity tariff parameters (EgyptERA Aug 2024 verified), EAF machine physical specs, grid CO₂ intensity, and AI reward weights (α through ζ). Copy to `.env` before running.

---

### `simulator/factory_sim.py`
**The heartbeat of the system.** Runs an infinite loop that:
1. Advances the EAF machine by one timestep
2. Queries the thermal model for updated temperatures
3. Queries Egypt grid pricing for current tariff
4. Builds a 40-field telemetry JSON payload
5. POSTs it to `backend/api/v1/telemetry` every 3 real seconds
6. Listens on `sim.control` Redis channel for crisis injection commands or tariff mode switches

Time-warp factor default is 15 — meaning each real second represents 15 simulated minutes, so a full 70-minute heat cycle completes in ~4.7 real minutes.

---

### `simulator/machines/eaf_machine.py`
**State machine for the Electric Arc Furnace heat cycle.** Manages 7 discrete phases:

```
CHARGING (5 min) → BORE_DOWN (10 min) → MELTING_PHASE_1 (15 min)
→ MELTING_PHASE_2 (15 min) → REFINING (10 min) → TAPPING (5 min) → IDLE
```

For each phase, defines baseline arc power (MW), oxygen injection rate (m³/hr), power factor behavior, and electrode consumption rate. Handles AI override commands — if the AI agent sends a recommendation, the machine applies it with bounds checking (arc power capped 60–110 MW; cooling water 100–400 l/min).

---

### `simulator/machines/eaf_thermal_model.py`
**Zero-dimensional energy-balance thermal model.** Computes bath and wall temperatures using physics-grounded differential equations:

```
Bath:
  Q_arc    = P_arc_kW × dt_seconds
  Q_oxygen = O₂_rate × 2.5 × dt_hours
  Q_loss   = (T_bath - 25) × 0.15 × dt × 0.5
  Q_cool   = cooling_lmin × 0.07 × dt
  ΔT       = (Q_arc + Q_O2 - Q_loss - Q_cool) / (mass × C_steel)

Wall:
  Heat_in  = P_arc × 0.04 × dt     (4% arc radiation)
  Heat_out = cooling_lmin × 0.012 × dt
  Ambient  = (T_wall - 40) × 0.005 × dt
  ΔT_wall  = Heat_in - Heat_out - Ambient
  Bounds   = [40°C, 350°C]
```

Physical ceiling for bath temperature: 1700°C (prevents numerical runaway).

---

### `simulator/machines/egypt_grid_pricing.py`
**Egyptian industrial electricity tariff calculator.** Implements two modes:

- **Flat mode (default):** 1.60 EGP/kWh for UHV (220-132 kV) customers — verified against EgyptERA August 2024 tariff schedule
- **TOU mode (ready, not active yet):** Based on GUC Working Paper #29 proposal — peak 18:00–22:00 at ~2.5 EGP/kWh, off-peak at ~1.2 EGP/kWh

Also calculates power-factor penalty bracket: if measured PF < 0.92 (Egyptian utility reference), a penalty multiplier is applied to the bill.

---

### `simulator/events/`
Four modular crisis event files, each implementing an `inject()` function:

| File | Crisis | Mechanism |
|------|--------|-----------|
| `overheat_event.py` | Wall panel overheat | Ramps wall temp →200°C; clears when <180°C |
| `electrode_break.py` | Electrode fracture | Consumption rate ×3 multiplier |
| `grid_spike_event.py` | Grid frequency drop | Sets frequency to 49.6 Hz; AI forces 60 MW cap |
| `transformer_alarm.py` | Transformer overload | Caps available MVA to 75 MW; based on real Nov 2024 failure |

---

### `ai_engine/environment.py`
**Gymnasium-compatible custom RL environment.** Defines the AI's world view:

**Observation Space (16 dimensions, normalized 0–1):**
1. Electricity price (EGP/kWh normalized)
2. Grid frequency (Hz)
3. Bath temperature
4. Wall panel temperature
5. Arc power (MW)
6. Power factor
7. Heat progress % (0–100)
8. Production backlog
9. Batches completed today
10. Energy consumed today (kWh)
11. Oxygen injection rate
12. Electrode consumption rate
13. Cooling water flow
14. Is-peak hour flag
15. TOU mode flag
16. Crisis active flags (composite)

**Action Space (5 discrete actions):**
```
0: HOLD_STEADY          → No change
1: REDUCE_ARC_POWER     → Arc power -15%
2: RAISE_PF_COMPENSATION → Reactive comp +10 MVAR
3: EMERGENCY_COOLING    → Cooling water to 350 l/min
4: PRE_PEAK_DROP        → Arc power -20% (anticipatory)
```

Episode length: 480 steps = simulated 24-hour day (3-minute step resolution).

---

### `ai_engine/reward_function.py`
**Multi-objective reward function — the heart of the AI's decision-making.**

```
R = α·(E_saved) − β·(M_stress) − γ·(P_delay) + δ·(Quality) − ε·(Electrode) − ζ·(PF_penalty)
```

| Term | Symbol | Default Weight | What It Measures |
|------|--------|---------------|-----------------|
| Energy savings | α | 1.0 | EGP saved vs. full-power baseline |
| Machine stress | β | 0.9 | Wall/electrode temps approaching limits |
| Production delay | γ | 1.8 | Backlog accumulation penalty |
| Quality bonus | δ | 0.7 | Bath temp in optimal [1600–1650°C] window |
| Electrode waste | ε | 0.5 | Consumption rate above phase baseline |
| PF penalty | ζ | 0.8 | Bill penalty when PF < 0.92 |

Four preset profiles adjust these weights for different operator priorities:
- `cost_first`: α=2.0 (maximize savings aggressively)
- `equipment_sensitive`: β=2.0 (protect machine above all)
- `production_critical`: γ=2.5 (never risk throughput)
- `quality_focused`: δ=2.0 (steel quality first)

---

### `ai_engine/agent.py`
**Dual-mode decision engine.** On startup, attempts to load the pre-trained PPO model from `models/opti_twin_ppo.zip`. If it loads successfully, uses neural network inference. If loading fails, falls back to the **scripted policy** (deterministic, auditable, fast):

**Scripted Policy Priority Tree:**
```
Priority 1: Wall temp ≥ 200°C           → EMERGENCY_COOLING
Priority 2: Grid freq < 49.7 Hz          → GRID_RIDE_THROUGH (reduce arc)
Priority 3: Transformer alarm active      → TRANSFORMER_DERATE (cap MW)
Priority 4: PF < 0.85 AND load > 80 MW   → RAISE_PF_COMPENSATION
Priority 5: Peak pricing active           → REDUCE_ARC_POWER
Priority 6: TOU + pre-peak window 17–18h  → PRE_PEAK_DROP (anticipatory)
Priority 7: Default                       → HOLD_STEADY
```

Outputs an `AIRecommendation` dataclass: action label, magnitude %, savings estimate (EGP/hr), health status enum, production status enum, and reward component breakdown.

---

### `ai_engine/xai_engine.py`
**Template-based Explainable AI engine.** NOT a large language model — uses deterministic string templates matched to (action × dominant_reward_component) pairs. Ensures every explanation is auditable, reproducible, and never hallucinates.

Supports 8 action-reason combinations, each with English and Arabic templates. Language selection is biased based on the dominant reward component detected. Example output:

```
EN: "Peak pricing (2.5 EGP/kWh) is active. Bath temperature 1,590°C is safe.
     Reducing arc power by 15% saves ~185 EGP/hr with no production risk."

AR: "تسعير الذروة نشط (2.5 ج.م/كيلوواط ساعة). درجة حرارة الحوض 1,590°م آمنة.
     تخفيض قدرة القوس بنسبة 15% يوفر ~185 ج.م/ساعة دون مخاطر إنتاجية."
```

---

### `ai_engine/models/opti_twin_ppo.zip`
Pre-trained PPO checkpoint committed for demo use. Trained offline on the custom `OptiTwinEAFEnv`. Ships frozen — no training happens during demo runtime. The scripted policy serves as a fully functional fallback that produces identical-quality decisions for demo purposes.

---

### `backend/main.py`
**FastAPI application — central hub of the system.** Manages:
- 8 REST endpoints (see Section 9)
- 1 WebSocket endpoint (`/ws/live-feed`)
- Background Redis subscriber tasks (starts on app startup)
- In-memory state: `last_telemetry`, `last_recommendation`, `ai_enabled`, `current_profile`
- KPI aggregation via `KPICalculator`

On startup, subscribes to both `factory.telemetry` and `ai.recommendation` Redis channels. When telemetry arrives, broadcasts to all connected WebSocket clients. When a recommendation arrives, broadcasts it too. The WebSocket endpoint streams a merged event object every time either channel publishes.

---

### `backend/api_contracts/schemas.py`
**Pydantic v2 models for every API boundary.** Key models:
- `TelemetryInput` — 40+ field strict model; extra fields forbidden
- `RecommendationOutput` — AI decision schema with all metadata
- `KPISnapshot` — Daily aggregated metrics (savings, CO₂, incidents)
- `AIToggleRequest`, `ProfileRequest`, `CrisisInjectRequest`, `TariffModeRequest` — Control command schemas
- `LiveFeedEvent` — WebSocket broadcast envelope

Strict validation at every boundary means malformed inputs are rejected at the edge, protecting internal services from bad data.

---

### `backend/services/redis_broker.py`
**Async Redis Pub/Sub wrapper (57 lines).** Provides:
- `subscribe(channel)` — async generator yielding decoded messages
- `publish(channel, payload)` — async publish with JSON serialization
- Lazy connection (connects once, reuses across requests)
- Graceful shutdown hook

Used by `main.py` as the only interface to Redis — all other services never touch Redis directly.

---

### `backend/services/kpi_calculator.py`
**Running KPI aggregator (77 lines).** Maintains in-memory arrays of:
- Energy saved per recommendation (EGP)
- CO₂ avoided per recommendation (kg)
- Thermal incident count (wall temp >180°C events)
- PF penalty events avoided

Exposes `get_snapshot()` returning a `KPISnapshot` with daily totals and live rates. Resets on service restart (no persistence — by design for hackathon).

---

### `frontend/pages/index.tsx`
**Main dashboard page.** Connects the `useLiveFeed` WebSocket hook to all dashboard components. Manages component-level state: language toggle (EN/AR), AI active state, crisis dropdown selection, profile selection. Renders the 7-component dashboard layout in a responsive Tailwind grid.

---

### `frontend/components/KPIBanner.tsx`
Six summary cards displayed at the top of the dashboard:
1. **Energy Saved Today** (EGP, green badge)
2. **Electricity Cost/hr** (EGP/hr, dynamic color)
3. **Bath Temperature** (°C, warning if >1660°C)
4. **Power Factor** (ratio, red if <0.85)
5. **Machine Health** (SAFE / WARNING / CRITICAL badge)
6. **CO₂ Avoided** (kg, green)

Each card updates on every WebSocket message (~every 3 seconds).

---

### `frontend/components/EnergyChart.tsx`
Recharts `LineChart` displaying the last 6 minutes of arc power (MW) as a rolling time-series. Features a `ReferenceArea` overlay (light red) that highlights peak hours (18:00–22:00) when TOU mode is active. X-axis shows simulated time, not real time. Updates on each telemetry push.

---

### `frontend/components/ThermalGauge.tsx`
Dual horizontal gauge bars:
- **Bath temperature:** Range 1400–1700°C; green zone 1600–1650°C (optimal), yellow 1650–1680°C (high), red >1680°C (critical)
- **Wall panel temperature:** Range 40–250°C; green <150°C, yellow 150–200°C, red >200°C (triggers emergency cooling)

Visually communicates thermal health at a glance without requiring numeric literacy.

---

### `frontend/components/EAFStatusCard.tsx`
Machine metadata card showing:
- Machine ID (EAF_02_EZZ_AIN_SOKHNA)
- Current heat phase (e.g., MELTING_PHASE_2) with phase progress ring
- Batches completed today
- Grid frequency (Hz) with green/yellow/red color
- Electrode consumption today (kg)
- Production status badge (ON_TRACK / AT_RISK / BEHIND)

---

### `frontend/components/XAIDecisionLog.tsx`
Scrollable log of the last 80 AI decisions (older entries pruned automatically). Each entry shows:
- Simulated timestamp
- Action label (e.g., `REDUCE_ARC_POWER`)
- XAI reason text (EN or AR based on language toggle)
- Savings estimate (EGP/hr)
- Machine health badge

Language toggle (EN ⇄ AR) button at the top right switches all reason text simultaneously. This is the primary transparency mechanism for operators.

---

### `frontend/components/Controls.tsx`
4-column control panel (operator interface):
1. **AI Toggle** — Enable/disable the RL agent (fires `POST /api/v1/ai/toggle`)
2. **TOU Mode Toggle** — Switch flat ↔ TOU tariff pricing mode
3. **Reward Profile Selector** — Dropdown: cost_first / equipment_sensitive / production_critical / quality_focused
4. **Crisis Injector** — Dropdown: wall_overheat / electrode_break / grid_spike / transformer_alarm + "Inject" button

All controls fire API calls via `lib/api.ts` and reflect state immediately (optimistic UI).

---

### `frontend/lib/ws.ts`
**`useLiveFeed` React hook.** Manages:
- WebSocket connection to `ws://localhost:8000/ws/live-feed`
- Exponential backoff reconnection (2s → 4s → 8s, capped at 30s)
- Connection status tracking: `live` | `connecting` | `reconnecting` | `disconnected`
- Event buffering: queues events received before React re-render cycle completes
- **Updated:** handles `pricing` message type → stores in `livePrice` field of `LiveFrame`
- Exports `LivePrice` type with: `price_egp_kwh`, `is_peak`, `price_source`, `label`, `is_dr_event`
- Returns `{ telemetry, recommendations, energySeries, livePrice, connection }` to dashboard

---

### `frontend/lib/api.ts`
HTTP API client helpers. Thin wrappers around `fetch()` with both `post()` and `get()` utilities.

Original calls:
- `toggleAI(enabled)`, `setProfile(profile)`, `injectCrisis(event)`, `setTariffMode(tou)`

**New DPE calls (added):**
- `getPricingMode()` / `setPricingMode(mode)` — read or switch DPE mode
- `getLivePrice()` — current price snapshot
- `getForecast()` — 24h price forecast curve
- `getRevenue()` — today's 4-stream revenue breakdown
- `getSchedule()` — recommended heat schedule + savings estimate
- `getDREvents()` — DR event history
- `injectDREvent(type, mw, duration)` — inject a Demand Response event for demo

---

### `backend/pricing/synthetic_spot_generator.py` ★ NEW
Generates realistic Egyptian intraday electricity spot prices without any external API dependency. Uses a time-of-day multiplier curve (off-peak 0.85×, shoulder 1.20×, peak 1.80–2.50× with sine peak shape), plus 1–3 random demand spike events per day and Gaussian noise (σ=0.08 EGP). Anchored to EgyptERA flat rate as daily average. Also generates multi-step forecasts with widening uncertainty at longer horizons.

---

### `backend/pricing/price_signal_broker.py` ★ NEW
Single normalized interface for all electricity price sources. Supports four modes:
- `flat` — constant 1.60 EGP/kWh (default, unchanged from existing system)
- `sim_tou` — binary TOU schedule (18:00–22:00 peak at 2.50 EGP, off-peak 1.20 EGP)
- `sim_spot` — synthetic intraday spot prices from `SyntheticSpotGenerator`
- `live_eehc` — EEHC real-time API stub (falls back to flat until wired to real feed)

Provides `get_current_price(sim_hour)` and `get_forecast(from_hour)` methods. The backend publishes results to Redis `pricing.live` (every 60 s) and `pricing.forecast` (every 30 min).

---

### `backend/pricing/demand_response_controller.py` ★ NEW
Full DR event lifecycle manager. Supports three program types: CURTAILMENT (250 EGP/MWh), INTERRUPTIBLE (450 EGP/MWh), FREQUENCY_RESPONSE (950 EGP/MWh). Core logic: `evaluate(event, machine_state)` calculates net benefit = DR payment − production cost impact, then auto-accepts or declines. Unsafe phases (CHARGING, BORE_DOWN, TAPPING) always decline. Maintains `DRState` with history, active event, and daily payment total.

---

### `backend/pricing/load_flexibility_scheduler.py` ★ NEW
Greedy multi-heat schedule optimizer. Given the 24-hour price forecast, it places each remaining heat into the cheapest available 30-minute window within the shift horizon (default 8 hours), respecting a 5-minute gap between heats. Computes `savings_vs_backtoback_egp` to show operators the financial benefit of the schedule vs. running heats consecutively.

---

### `backend/pricing/revenue_optimizer.py` ★ NEW
Tracks and accumulates 4 simultaneous revenue streams per day: energy savings (from AI arc power reductions), DR payments (from accepted DR events), capacity credits (prorated daily from contracted flexibility), and ancillary services. `accrue_capacity_credit()` is called on every telemetry tick to continuously add the prorated daily credit. Exposes `snapshot()` dict for the `/api/v1/pricing/revenue` endpoint.

---

### `frontend/components/DynamicPricingPanel.tsx` ★ NEW
4-column live dashboard panel added below the Controls row. Polls pricing API endpoints every 3 seconds. Columns:
1. **Live Price** — large price readout with peak/off-peak badge + DPE mode dropdown
2. **4h Forecast** — mini bar chart (8 bars × 30-min steps), peak bars in red, off-peak in green
3. **Revenue Streams** — 4 horizontal bar gauges (energy savings, DR payments, capacity credits, ancillary) + total stacked revenue
4. **Demand Response** — DR event injection dropdown (CURTAILMENT / INTERRUPTIBLE / FREQUENCY_RESPONSE) + recent DR event history (accept/decline + EGP earned) + heat schedule savings summary

---

### `data/tariffs/egypt_industrial_2026.json`
JSON file containing:
- EgyptERA August 2024 verified industrial tariff schedule (UHV, HV, MV tiers)
- Power-factor penalty bracket table (0.92 reference)
- GUC Working Paper #29 TOU proposal rates (draft)
- Grid CO₂ intensity factor (0.50 kg CO₂/kWh, IEA-derived)

Loaded by `egypt_grid_pricing.py` at simulator startup.

---

### `docs/demo-scenario.md`
3-minute live demo script with timestamps, what to click, and expected outputs. Written for hackathon judging presentations.

### `docs/planing-v2.md`
Post-hackathon development roadmap covering M2 (Demand Forecaster), M3 (Anomaly Detector), M4 (Behavior Cloning), M5 (Preference Learning), and sim-to-real deployment strategy.

### `docs/upgrade.md`
Detailed plan for the **Opti-Search** microservice — a semantic + lexical search engine over telemetry, decisions, and KPI data with a Ctrl+K command palette UI.

---

## 6. Data Flow Diagrams

### Telemetry Flow

```
factory_sim.py
    │
    │  Every 3 real seconds:
    │  POST { machine_id, timestamp, arc_power_mw, bath_temp,
    │          electricity_price, batches_today, ... (40 fields) }
    ▼
backend/main.py  POST /api/v1/telemetry
    │
    ├── validates with TelemetryInput (Pydantic)
    ├── stores in last_telemetry (in-memory)
    ├── publishes to Redis: factory.telemetry
    └── broadcasts to all WebSocket clients
              │
    ┌─────────┴──────────────────────┐
    ▼                                ▼
ai_engine/agent.py              frontend/lib/ws.ts
    │                                │
    │ reads observation               │ updates React state
    │ runs scripted/PPO policy        │ triggers re-render
    │ builds AIRecommendation         │
    │                           All dashboard components
    │ publishes to Redis:        refresh (~3s cadence)
    │ ai.recommendation
    ▼
backend/main.py (subscriber)
    │
    ├── stores in last_recommendation
    ├── updates KPICalculator
    └── broadcasts to WebSocket clients
```

### Control Flow (Operator → Machine)

```
Dashboard Controls.tsx
    │
    │  User clicks "AI On"
    ▼
lib/api.ts → POST /api/v1/ai/toggle  { enabled: true }
    │
backend/main.py
    │
    ├── sets ai_enabled = true (in-memory)
    └── publishes to Redis: ai.control  { command: "toggle", enabled: true }
              │
    ai_engine/agent.py (subscriber)
              │
              └── starts emitting recommendations on next telemetry event
```

---

## 7. AI & Reward System Deep Dive

### Multi-Objective Reward Formula

```
R(t) = α · E_saved(t)
      − β · M_stress(t)
      − γ · P_delay(t)
      + δ · Q_bonus(t)
      − ε · Electrode_waste(t)
      − ζ · PF_penalty(t)
```

### Component Details

**E_saved(t) — Energy Savings (α = 1.0)**
```
E_saved = (P_baseline − P_actual) × price_EGP/kWh × dt_hours
```
Rewards the agent for reducing arc power during high-price periods. Scales with tariff (peak hours yield 1.5–2× baseline reward).

**M_stress(t) — Machine Stress (β = 0.9)**
```
Wall penalty:     max(0, (T_wall - 160) / 90) ^ 2
Electrode penalty: max(0, consumption_rate - phase_baseline) / 5
M_stress = (wall_penalty + electrode_penalty) / 2
```
Quadratic penalty near physical limits ensures the agent avoids the danger zone aggressively.

**P_delay(t) — Production Delay (γ = 1.8)**
```
P_delay = backlog_tonnes / max_backlog × phase_weight
phase_weight = 2.0 during MELTING phases, 1.0 otherwise
```
Largest weight by default — ensures production throughput is the binding constraint.

**Q_bonus(t) — Quality Bonus (δ = 0.7)**
```
if 1600°C ≤ bath_temp ≤ 1650°C: Q = 1.0
if 1580°C ≤ bath_temp < 1600°C: Q = 0.5  (approaching optimal)
else:                             Q = 0.0
```
Encourages refining phase precision — the temperature window for optimal steel chemistry.

### Reward Profile Presets

```
Profile             α     β     γ     δ     ε     ζ
──────────────────  ────  ────  ────  ────  ────  ────
default             1.0   0.9   1.8   0.7   0.5   0.8
cost_first          2.0   0.9   1.8   0.7   0.5   0.8
equipment_sensitive 1.0   2.0   1.8   0.7   0.5   0.8
production_critical 1.0   0.9   2.5   0.7   0.5   0.8
quality_focused     1.0   0.9   1.8   2.0   0.5   0.8
```

### Scripted Policy Decision Tree

```
┌─ Check wall_temp ──────► ≥ 200°C ──────► EMERGENCY_COOLING
│
├─ Check grid_freq ──────► < 49.7 Hz ─────► REDUCE_ARC_POWER (grid ride-through)
│
├─ Check transformer ───► alarm = true ──► REDUCE_ARC_POWER (cap at 75 MW)
│
├─ Check PF + load ──────► PF<0.85 & MW>80 ► RAISE_PF_COMPENSATION
│
├─ Check tariff ─────────► is_peak = true ► REDUCE_ARC_POWER (-15%)
│
├─ Check TOU pre-peak ───► 17≤hour<18 ─────► PRE_PEAK_DROP (-20%)
│
└─ Default ──────────────────────────────► HOLD_STEADY
```

---

## 8. Physics Simulation Model

### EAF Heat Cycle

```
Phase           Duration  Arc Power  O₂ Rate   Description
──────────────  ────────  ─────────  ────────  ───────────────────────────
CHARGING          5 min    OFF (0)    0 m³/hr   Load 185t scrap into furnace
BORE_DOWN        10 min    70 MW     100 m³/hr  Arcs ignite, drill through scrap
MELTING_PHASE_1  15 min   100 MW     350 m³/hr  Bulk melt, maximum arc power
MELTING_PHASE_2  15 min    95 MW     450 m³/hr  Flat bath, peak oxygen injection
REFINING         10 min    60 MW     150 m³/hr  Temperature trim & chemistry
TAPPING           5 min    OFF (0)    0 m³/hr   Pour molten steel to ladle
IDLE           variable    OFF (0)    0 m³/hr   Recovery between heats
Total heat cycle: 60 min + IDLE ≈ 70 min per heat
```

### AI Controllable Variables

| Variable | Range | AI Can | Unit |
|----------|-------|--------|------|
| Arc power | 60–110 MW | Reduce (not exceed baseline) | MW |
| Cooling water | 100–400 l/min | Increase to 350 (emergency) | l/min |
| Reactive compensation | 0–30 MVAR | Increase (PF correction) | MVAR |

### Crisis Event Effects

```
Crisis             Trigger                   AI Response             Recovery
─────────────────  ────────────────────────  ──────────────────────  ─────────────────
wall_overheat      Wall temp → >200°C        EMERGENCY_COOLING       Auto: temp <180°C
electrode_break    Consumption rate ×3        HOLD (reduce wear)      Manual: clear flag
grid_spike         Frequency → 49.6 Hz        REDUCE_ARC to 60 MW    Auto: Hz recovery
transformer_alarm  MVA cap → 75 MW           TRANSFORMER_DERATE      Manual: clear flag
```

---

## 9. API Contract Reference

### REST Endpoints

| Method | Path | Request Body | Response | Purpose |
|--------|------|-------------|----------|---------|
| GET | `/` | — | `{service, version, status}` | Health check |
| POST | `/api/v1/telemetry` | `TelemetryInput` | `{status: ok}` | Ingest machine telemetry |
| GET | `/api/v1/recommendation` | — | `RecommendationOutput` | Latest AI decision |
| GET | `/api/v1/stats` | — | `KPISnapshot` | Daily aggregated KPIs |
| POST | `/api/v1/ai/toggle` | `{enabled: bool}` | `{ai_enabled: bool}` | Enable/disable AI |
| POST | `/api/v1/ai/profile` | `{profile: string}` | `{profile: string}` | Switch reward profile |
| POST | `/api/v1/sim/inject` | `{crisis_type: string}` | `{injected: string}` | Inject crisis event |
| POST | `/api/v1/tariff/mode` | `{tou: bool}` | `{tou_mode: bool}` | Toggle TOU pricing |
| **GET** | **`/api/v1/pricing/live`** | — | `LivePriceResponse` | Current live price + peak flag |
| **GET** | **`/api/v1/pricing/forecast`** | — | forecast JSON | 24h price forecast (P10/P50/P90) |
| **GET** | **`/api/v1/pricing/mode`** | — | `{mode: string}` | Current DPE mode |
| **POST** | **`/api/v1/pricing/mode`** | `{mode: string}` | `{ok, mode}` | Switch DPE mode |
| **GET** | **`/api/v1/pricing/revenue`** | — | `RevenueSnapshot` | Today's 4-stream revenue |
| **GET** | **`/api/v1/pricing/schedule`** | — | schedule JSON | Recommended heat schedule |
| **POST** | **`/api/v1/pricing/dr/inject`** | `DRInjectRequest` | `{event, assessment}` | Inject DR event (demo) |
| **GET** | **`/api/v1/pricing/dr/events`** | — | DR history JSON | DR event log + active event |

### WebSocket

| Path | Direction | Payload | Cadence |
|------|-----------|---------|---------|
| `/ws/live-feed` | Server → Client | `telemetry` events (~3s), `recommendation` events (~3s), **`pricing` events** (~60s) | ~3 / ~60 seconds |

**New `pricing` message type** broadcast over the existing WebSocket:
```json
{ "type": "pricing", "data": { "price_egp_kwh": 2.43, "is_peak": true, "label": "Peak", "price_source": "sim_spot", ... } }
```

### New DPE Schemas

**`LivePriceResponse`**
```typescript
{
  timestamp: string,
  price_egp_kwh: float,        // current live price
  price_source: "flat" | "sim_tou" | "sim_spot" | "live_eehc",
  tariff_class: string,
  is_peak: boolean,
  is_dr_event: boolean,
  dr_event_id: string | null,
  confidence: float,           // 1.0 for sim, <1.0 for forecasted
  label: string                // e.g. "Peak", "Off-peak", "Shoulder + demand event"
}
```

**`RevenueSnapshot`**
```typescript
{
  energy_savings_egp: float,   // arc power reduction × live price
  dr_payments_egp: float,      // accepted DR events today
  capacity_credits_egp: float, // contracted flexibility credit (prorated)
  ancillary_egp: float,        // frequency response payments
  total_revenue_egp: float     // sum of all four streams
}
```

**`DRInjectRequest`**
```typescript
{
  event_type: "CURTAILMENT" | "INTERRUPTIBLE" | "FREQUENCY_RESPONSE",
  mw_requested: float,   // 5.0–110.0
  duration_minutes: int  // 15–120
}
```

### Key Schema: `TelemetryInput` (selected fields)

```typescript
{
  machine_id: string,          // "EAF_02_EZZ_AIN_SOKHNA"
  timestamp: datetime,
  arc_power_mw: float,         // 0–110 MW
  furnace_bath_temp: float,    // °C
  wall_panel_temp: float,      // °C
  electricity_price: float,    // EGP/kWh
  power_factor: float,         // 0.0–1.0
  heat_progress_pct: float,    // 0–100
  batches_today: int,
  is_peak: bool,
  grid_frequency: float,       // Hz
  ai_active: bool,
  // ... 30+ more fields
}
```

### Key Schema: `RecommendationOutput`

```typescript
{
  timestamp: datetime,
  machine_id: string,
  action_label: "HOLD_STEADY" | "REDUCE_ARC_POWER" | "RAISE_PF_COMPENSATION"
              | "EMERGENCY_COOLING" | "PRE_PEAK_DROP",
  action_magnitude_pct: float,          // e.g., -15.0
  estimated_savings_egp_per_hour: float,
  pf_penalty_avoided_egp: float,
  co2_saved_kg: float,
  xai_reason: string,                   // English explanation
  xai_reason_ar: string,                // Arabic explanation
  machine_health: "SAFE" | "WARNING" | "CRITICAL",
  production_status: "ON_TRACK" | "AT_RISK" | "BEHIND",
  reward_components: {
    energy_savings_egp: float,
    machine_stress_penalty: float,
    production_delay_penalty: float,
    quality_bonus: float,
    electrode_waste_penalty: float,
    pf_penalty: float
  },
  dominant_reason: string,
  ai_enabled: bool
}
```

---

## 10. Frontend Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│  OPTI-TWIN  |  EAF Digital Twin                          ● LIVE          │
├──────────────────────────────────────────────────────────────────────────┤
│                          KPI BANNER (6 cards)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──┐ │
│  │ Savings  │ │ Cost/hr  │ │  Bath °C │ │   PF     │ │ Health   │ │CO₂│ │
│  │ 2,340EGP │ │ 1,240EGP │ │  1,623°C │ │   0.91   │ │  SAFE ✓ │ │125│ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──┘ │
├────────────────────────────────────────────┬─────────────────────────────┤
│  ENERGY CHART                              │  THERMAL GAUGE              │
│  Arc Power (MW)  ▲                         │                             │
│  100 ─ ─ ─ ─     ╭────╮                   │  Bath Temp    ████████░  92%│
│   80 ─          ╭╯    ╰──╮                │  1,623°C      [OPTIMAL]     │
│   60 ─         ╱         ╰╮               │                             │
│       17:30  18:00  18:30  19:00          │  Wall Temp    ████░░░░░  58%│
│       [peak zone highlighted red]         │  142°C        [NORMAL]      │
├────────────────────────────────────────────┼─────────────────────────────┤
│  EAF STATUS CARD                           │  XAI DECISION LOG      EN│AR│
│  Machine:  EAF_02_EZZ_AIN_SOKHNA          │  18:32 REDUCE_ARC_POWER     │
│  Phase:    MELTING_PHASE_2  [──────── 67%]│  "Peak pricing (2.5 EGP)... │
│  Batches:  7 today                        │   Bath safe. Saving 185/hr" │
│  Grid Hz:  50.01 ● Normal                 │                             │
│  Electrode:14.3 kg today                  │  18:29 RAISE_PF_COMP        │
│  Status:   ON_TRACK ✓                     │  "PF 0.87 below ref 0.92..."│
├────────────────────────────────────────────┴─────────────────────────────┤
│  CONTROLS                                                                 │
│  ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐ ┌──────────┐ │
│  │ AI: [ON ●]      │ │ TOU: [OFF ○] │ │ Profile: cost▼   │ │ Crisis ▼ │ │
│  └─────────────────┘ └──────────────┘ └──────────────────┘ │  Inject  │ │
│                                                              └──────────┘ │
├──────────────────────────────────────────────────────────────────────────┤
│  DYNAMIC PRICING ENGINE                                  [Spot market ●] │
│  ┌────────────────────┐ ┌──────────────────┐ ┌──────────────┐ ┌───────┐ │
│  │ Live Price         │ │ 4h Price Forecast│ │ Revenue Today│ │  DR   │ │
│  │ 2.431 EGP/kWh      │ │ ▓▓▓░░▓▓▓░░▓▓░░░░ │ │ Savings 2340 │ │[Inj▼] │ │
│  │ [PEAK ●]           │ │ Max: 2.50        │ │ DR Pay   580 │ │CURT ✓ │ │
│  │ Mode: [Spot ▼]     │ │ Min: 1.35        │ │ Cap Cred  92 │ │ 580   │ │
│  │                    │ │ now       +4h    │ │ Total   3012 │ │ EGP   │ │
│  └────────────────────┘ └──────────────────┘ └──────────────┘ └───────┘ │
│  Schedule: 3 heats optimised · Saves 890 EGP vs back-to-back             │
├──────────────────────────────────────────────────────────────────────────┤
│  Tariff: EgyptERA Aug 2024 · Grid CO₂: 0.50 kg/kWh · © Opti-Twin 2026  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Configuration Reference

### Complete `.env` Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_PORT` | 8000 | FastAPI server port |
| `FRONTEND_PORT` | 3000 | Next.js server port |
| `REDIS_PORT` | 6379 | Redis (internal only) |
| `SIM_MACHINE` | EAF_02_EZZ_AIN_SOKHNA | Machine ID |
| `SIM_INTERVAL_SECONDS` | 3 | Telemetry publish cadence |
| `SIM_TIME_WARP_MINUTES` | 15 | Simulated min per real sec |
| `SIM_START_HOUR` | 17.75 | Start at 17:45 (pre-peak) |
| `TARIFF_CLASS` | UHV_220-132kV | Egyptian tariff tier |
| `TARIFF_RATE_EGP_PER_KWH` | 1.60 | EgyptERA Aug 2024 rate |
| `TOU_MODE_DEFAULT` | false | Start in flat tariff mode |
| `PF_REFERENCE` | 0.92 | Egyptian utility PF ref |
| `GRID_CO2_INTENSITY_KG_PER_KWH` | 0.50 | Egypt grid emission factor |
| `EAF_RATED_TPA` | 1600000 | Annual capacity (tonnes) |
| `EAF_FURNACE_SIZE_T` | 185 | Furnace charge weight |
| `EAF_MAX_POWER_MW` | 110 | Physical max arc power |
| `EAF_MIN_POWER_MW` | 60 | Safe minimum arc power |
| `FURNACE_MAX_WALL_TEMP` | 250 | Wall panel limit (°C) |
| `FURNACE_TARGET_BATH_TEMP` | 1630 | Optimal bath target (°C) |
| `RL_ALPHA` | 1.0 | Reward: energy savings weight |
| `RL_BETA` | 0.9 | Reward: machine stress weight |
| `RL_GAMMA` | 1.8 | Reward: production delay weight |
| `RL_DELTA` | 0.7 | Reward: quality bonus weight |
| `RL_EPSILON` | 0.5 | Reward: electrode waste weight |
| `RL_ZETA` | 0.8 | Reward: PF penalty weight |
| **Dynamic Pricing Engine** | | |
| `DPE_ENABLED` | true | Enable pricing engine |
| `DPE_MODE` | sim_spot | Pricing mode: flat \| sim_tou \| sim_spot \| live_eehc |
| `DPE_PRICE_UPDATE_INTERVAL_SECONDS` | 60 | How often live price is recalculated |
| `DPE_FORECAST_UPDATE_INTERVAL_SECONDS` | 1800 | How often 24h forecast is published to Redis |
| `DPE_FORECAST_HORIZON_HOURS` | 24 | Forecast lookahead window |
| `DPE_FORECAST_STEP_MINUTES` | 30 | Forecast granularity (30-min slots) |
| `TOU_PEAK_START_HOUR` | 18.0 | Peak period start (TOU mode) |
| `TOU_PEAK_END_HOUR` | 22.0 | Peak period end (TOU mode) |
| `TOU_PEAK_RATE_EGP` | 2.50 | Peak tariff rate EGP/kWh |
| `TOU_OFFPEAK_RATE_EGP` | 1.20 | Off-peak tariff rate EGP/kWh |
| `DPE_SPOT_PEAK_MULTIPLIER_MIN` | 1.8 | Spot peak price floor multiplier |
| `DPE_SPOT_PEAK_MULTIPLIER_MAX` | 2.5 | Spot peak price ceiling multiplier |
| `DPE_SPOT_OFFPEAK_MULTIPLIER` | 0.85 | Spot off-peak price multiplier |
| `DPE_SPOT_NOISE_STD` | 0.08 | Gaussian noise std-dev on spot price (EGP) |
| `DPE_DR_ENABLED` | true | Enable Demand Response participation |
| `DPE_DR_MIN_DURATION_MINUTES` | 15 | Minimum DR event duration |
| `DPE_DR_CURTAILMENT_RATE_EGP` | 250 | DR payment: curtailment (EGP/MWh) |
| `DPE_DR_INTERRUPTIBLE_RATE_EGP` | 450 | DR payment: interruptible (EGP/MWh) |
| `DPE_DR_FREQUENCY_RATE_EGP` | 950 | DR payment: frequency response (EGP/MWh) |
| `DPE_CAPACITY_CREDIT_RATE_EGP` | 80 | Capacity market credit rate (EGP/kW/month) |
| `DPE_CONTRACTED_FLEXIBILITY_MW` | 30 | Contracted flexibility capacity (MW) |
| `DPE_SCHEDULE_HORIZON_HOURS` | 8 | Heat schedule optimizer lookahead (hours) |
| `STEEL_REVENUE_PER_TONNE` | 8400 | Steel revenue for DR net-benefit calculation |
| `STEEL_COST_PER_TONNE` | 6100 | Steel variable cost (EGP/tonne) |

---

## 12. Business Case & KPIs

### Financial Impact (1 EAF, Annual)

| Metric | Baseline | With Opti-Twin | Change |
|--------|----------|----------------|--------|
| Energy intensity | 450 kWh/t | 405 kWh/t | −10% |
| Annual electricity cost | ~1.15B EGP | ~1.04B EGP | −115M EGP |
| Power factor avg | 0.78 | 0.92 (ref) | Penalty eliminated |
| Annual CO₂ (Scope 2) | ~360,000 t | ~324,000 t | −36,000 t/yr |
| Production throughput | 1.6 Mtpa | 1.6 Mtpa | 0% (guaranteed) |
| ROI payback period | — | < 2 months | — |

### DPE Revenue Stack (Annual, 1 EAF — DPE Active)

| Revenue Stream | Mechanism | Est. Annual (EGP) |
|----------------|-----------|-------------------|
| Energy savings (flat tariff) | 10% intensity reduction @ 1.60 EGP/kWh | ~115,000,000 |
| TOU / spot shifting | Load shift peak → off-peak, additional 5–8% | ~55,000,000 |
| Demand Response payments | Avg 2 events/week × 30 MW × 30 min @ 450 EGP/MWh | ~42,000,000 |
| Capacity market credits | 30 MW × 80 EGP/kW/month × 12 months | ~28,800,000 |
| **Total stacked revenue** | | **~240,800,000 EGP/yr** |

> DPE Phase 3 projection: ~212–241M EGP/yr per furnace (vs. 115M EGP flat-tariff baseline)

### Live Demo Output (Expected by Judges)

```
┌────────────────────────────────────────────┐
│  ⚡ Energy Cost Reduction    ↓ 15–18%      │
│  🏭 Production Throughput    = 100%        │
│  🌡  Machine Health           SAFE ✓       │
│  💰  Total Saved Today        2,340 EGP    │
│  ♻️  CO₂ Avoided Today        125 kg       │
│  ⚡  Power Factor             0.91 (ref: 0.92) │
└────────────────────────────────────────────┘
```

### Verified Data Sources

| Fact | Source | Status |
|------|--------|--------|
| EgyptERA UHV tariff 1.60 EGP/kWh | EgyptERA "Current Electricity Tariff" Aug 2024 | ✓ Verified |
| Furnace specs (Ezz Ain Sokhna EAF #2) | Global Energy Monitor | ✓ Verified |
| EAF energy intensity 450 kWh/t | World Steel Association | ✓ Verified |
| Egypt grid CO₂ 0.45–0.5 tCO₂/MWh | IEA / EIA / Climatiq | ✓ Verified |
| PF penalty mechanism | EgyptERA tariff doc + ResearchGate | ✓ Verified |
| TOU rate proposal | GUC Working Paper #29 | ✓ Verified |
| Transformer failure Nov 2024 | Global Energy Monitor (Ain Sokhna EAF #2) | ✓ Verified |

---

## 13. Demo Script

### 3-Minute Hackathon Demo Flow

```
00:00–00:45  BASELINE: Show dashboard approaching peak hour
             ─ Clock shows 17:45 → 18:00 approaching
             ─ Energy cost per hour climbing on KPI banner
             ─ "Without AI the factory spends ~1,240 EGP/hr at peak"

00:45–01:15  PEAK HITS: Tariff spikes visible
             ─ Chart shows electricity cost jump (flat 1.60 → peak 2.5 EGP/kWh)
             ─ Cost/hr card turns red
             ─ "18:00 — peak pricing active. Expensive minutes"

01:15–02:00  ACTIVATE AI: Toggle AI ON
             ─ Controls panel: click AI toggle → ON
             ─ XAI Decision Log populates instantly (EN + AR)
             ─ Arc power drops on EnergyChart
             ─ Savings KPI starts climbing
             ─ "AI reduced arc power 15%. Bath still 1,610°C — safe"
             ─ Flip to Arabic: bilingual XAI visible

02:00–02:30  INJECT CRISIS: Wall overheat event
             ─ Crisis dropdown → wall_overheat → Inject
             ─ Thermal gauge turns red (wall 185°C → 210°C)
             ─ AI fires EMERGENCY_COOLING within 1 cycle
             ─ XAI: "Wall temperature critical. Emergency cooling engaged."
             ─ Temperature recovers over 2 cycles
             ─ Health badge: WARNING → SAFE

02:30–03:00  RESULT: Final KPI read-out
             ─ "Energy ↓18%  |  Production 100%  |  Health SAFE  |  Saved 2,340 EGP today"
```

---

## 14. Coming Soon Features

### Dynamic Pricing Engine ★ **Status: IMPLEMENTED ✓**
**All components coded and integrated** — see [Section 16](#16-dynamic-pricing-engine--full-plan) for full architecture details.

**What was built:**
- `pricing/synthetic_spot_generator.py` — Intraday Egyptian spot price generator with peak curves and demand spikes
- `pricing/price_signal_broker.py` — 4-mode price interface (flat / TOU / spot / live)
- `pricing/demand_response_controller.py` — DR event lifecycle with safety-phase gating
- `pricing/load_flexibility_scheduler.py` — Greedy heat schedule optimizer
- `pricing/revenue_optimizer.py` — 4-stream revenue accumulator
- `DynamicPricingPanel.tsx` — Live dashboard panel with forecast bars, revenue breakdown, DR injection
- AI observation space expanded 16D → 32D with live price + 8-step forecast
- 8 new REST endpoints; `pricing.live` and `pricing.forecast` Redis channels

---

### M2 — Electricity Demand Forecaster
**Status:** Planned (architecture documented)  
**Tech:** LSTM or Temporal Fusion Transformer  
**What it does:** Predicts the next 30-minute electricity price curve and factory load profile. The AI agent will look ahead — reduce power *before* peak starts, not just *after*. Expected additional savings: 3–5% on top of reactive optimization.

**Current gap:** Today the agent only reacts to `is_peak` flag. Forecasting enables *anticipatory* action.

### M3 — Equipment Anomaly Detector
**Status:** Planned (architecture documented)  
**Tech:** Autoencoder on telemetry time-series  
**What it does:** Detects when "telemetry looks wrong" — subtle deviations from normal patterns that precede failures. Outputs anomaly score 0–1; triggers maintenance alert before breakdown.

**Current gap:** Today crises are manually injected. This module makes the system self-aware of emerging faults.

### M4 — Behavior Cloning Warm Start
**Status:** Planned  
**Tech:** Imitation learning from scripted policy demonstrations  
**What it does:** Generates 50,000 scripted-policy episodes and uses behavioral cloning to warm-start the PPO model. Reduces cold-start training from >100k steps to <5k steps.

**Current gap:** Pre-trained PPO model ships frozen from offline training. Warm start enables faster retraining on new environments.

### M5 — Preference Learning (RLHF)
**Status:** Planned  
**Tech:** Pairwise operator feedback → reward weight adjustment  
**What it does:** Presents operators with pairs of past decisions ("which was better?"). Uses Bradley-Terry model to infer preferred reward weights. Personalizes the AI to each operator's priorities without manual weight tuning.

**Current gap:** Today profile presets are fixed. RLHF enables continuous operator-aligned learning.

### Opti-Search — Semantic Search Engine
**Status:** Architecture designed, Day-1 demo slice in `upgrade.md`  
**Tech:** FastAPI microservice + lexical + semantic + structured query layers  
**What it does:** Command-palette interface (Ctrl+K) to search all telemetry, decisions, KPI history, and tariff data. Natural language queries: "Show all times wall temp exceeded 200°C last week" or "When was the most expensive hour yesterday?"  
**Languages:** EN + AR full-text search  
**Demo slice:** 3 document types (telemetry, decisions, tariffs), saved searches, top-5 results

**Current gap:** Today data is ephemeral (no persistence). Search requires: persistent storage (Postgres/Elasticsearch), embedding model, retrieval pipeline.

### Real SCADA Integration (Sim-to-Real)
**Status:** Deployment roadmap documented  
**Strategy:**
1. **Shadow Mode** — AI runs in parallel to human decisions, advises but does not control; builds confidence
2. **Domain Randomization** — Retrain PPO with randomized furnace parameters (±20% physics constants) for robustness
3. **SCADA Adapter** — OPC-UA / Modbus connector to replace simulator with live sensor feeds
4. **Closed-Loop Deployment** — AI takes control with human override always available

**Current gap:** Simulator only. No OPC-UA connector or real historian integration.

### Multi-Machine Dashboard
**Status:** Architecture supports it (Redis multi-subscribe), not exercised  
**What it does:** Monitor N furnaces simultaneously. Fleet-level KPI aggregation. Cross-furnace load balancing (shift heat schedules across furnaces to flatten peak demand).

**Current gap:** Single-machine demo only. Backend multi-subscribe logic is present but untested.

### Persistent Data Layer
**Status:** Not implemented  
**Tech:** TimescaleDB (time-series PostgreSQL) or ClickHouse  
**What it does:** Stores all telemetry + decisions → enables historical analysis, trend detection, shift-by-shift reports, and the search engine.

**Current gap:** All data in Redis (ephemeral, resets on restart). No historical records.

### Authentication & RBAC
**Status:** Not implemented  
**What it does:** JWT-based auth for dashboard. Role-based access control: Operator (view + controls), Supervisor (all + profile changes), Admin (all + crisis inject, tariff config).

**Current gap:** All endpoints open to localhost — acceptable for hackathon, not for production.

### EU CBAM Carbon Reporting Module
**Status:** Data ready, module not built  
**What it does:** Calculates Scope 2 CO₂ avoided per heat, per day, per quarter. Generates CBAM (Carbon Border Adjustment Mechanism) compatible reports for EU steel export compliance. Starting 2026, steel exported to EU carries CBAM certificate cost — CO₂ avoidance has direct financial value (~€50–80/tonne CO₂).

**Current gap:** CO₂ avoided is shown in dashboard. Export report format not built.

### Autonomous Decision Twin ★ FLAGSHIP NEXT FEATURE
**Status:** Fully planned — see [Section 15](#15-autonomous-decision-twin--full-plan) for complete architecture, phase plan, API design, and safety framework.

**What it does:** Evolves Opti-Twin from an *advisory* system (AI recommends → human decides) to a *closed-loop autonomous* system (AI decides → system acts → twin learns from outcome). Four graduated autonomy levels from observation-only to full closed-loop control with hard safety envelopes that can never be overridden.

**Why this matters:** Advisory systems capture ~30% of potential savings because operators don't act on every recommendation. Autonomous execution captures the full 10–15% target.

---

## 15. Autonomous Decision Twin — Full Plan

### Overview

The **Autonomous Decision Twin (ADT)** is the architectural evolution that closes the loop between the digital twin and the physical machine. Today Opti-Twin is an *Advisory Twin* — the AI generates recommendations, and a human operator decides whether to act. The ADT removes that gap.

```
ADVISORY TWIN (current):
  Physical Machine → Simulator → AI Recommendation → [Human Gap] → Machine Act
                                                           ↑
                                              30–70% of decisions not acted on

AUTONOMOUS DECISION TWIN (target):
  Physical Machine ←→ State Mirror ←→ AI Decision Engine → Execution Bus → Machine
                           ↑                    ↑
                    Continuous sync      Counterfactual
                                         simulation first
                                              ↑
                                       Outcome Learning
                                       (real vs predicted)
```

### The Autonomy Ladder (4 Levels)

The ADT is not a binary on/off. It uses a **graduated trust framework** — the system earns the right to act more autonomously over time as operators build confidence.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AUTONOMY LADDER                                 │
├───────┬────────────────┬────────────────────────────────────────────┤
│ Level │ Name           │ Behavior                                   │
├───────┼────────────────┼────────────────────────────────────────────┤
│  L0   │ OBSERVE        │ Twin mirrors real state. No recommendations.│
│       │                │ Baseline data collection only.             │
├───────┼────────────────┼────────────────────────────────────────────┤
│  L1   │ ADVISE         │ AI generates recommendations + XAI.        │
│  ★    │ (current)      │ Human operator decides whether to act.     │
│       │                │ Zero autonomous execution.                  │
├───────┼────────────────┼────────────────────────────────────────────┤
│  L2   │ SUPERVISED     │ AI auto-executes LOW-IMPACT actions        │
│       │                │ (PF compensation, minor arc adjustments).   │
│       │                │ HIGH-IMPACT actions need operator approval  │
│       │                │ within 30 seconds or AI holds.             │
├───────┼────────────────┼────────────────────────────────────────────┤
│  L3   │ AUTONOMOUS     │ AI executes ALL actions within safety      │
│       │                │ envelope. Human override always available.  │
│       │                │ Requires 30-day L2 track record with       │
│       │                │ zero safety violations.                     │
└───────┴────────────────┴────────────────────────────────────────────┘

Current system = L1.  ADT target = L2 → L3 over 90 days.
```

---

### Architecture: New Components

The ADT adds 6 new components to the existing 4-tier system:

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    AUTONOMOUS DECISION TWIN                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │  EXISTING SYSTEM (Tiers 1–4)           [unchanged]               │   ║
║  └─────────────────────────────┬────────────────────────────────────┘   ║
║                                 │                                        ║
║  ┌──────────────────────────────▼────────────────────────────────────┐  ║
║  │  NEW: ADT LAYER                                                   │  ║
║  │                                                                   │  ║
║  │  ┌──────────────────┐   ┌────────────────────────────────────┐   │  ║
║  │  │ State Mirror     │   │ Counterfactual Engine              │   │  ║
║  │  │ Engine           │   │                                    │   │  ║
║  │  │ Physical ↔ Twin  │   │ Before acting: simulate N futures  │   │  ║
║  │  │ real-time sync   │   │ Compare outcomes. Pick best.       │   │  ║
║  │  │ drift detection  │   │ Rollback if outcome diverges.      │   │  ║
║  │  └────────┬─────────┘   └──────────────┬─────────────────────┘   │  ║
║  │           │                             │                          │  ║
║  │  ┌────────▼──────────────────────────────▼─────────────────────┐  │  ║
║  │  │ Confidence Engine                                           │  │  ║
║  │  │ Score = f(state_certainty, model_accuracy, crisis_risk)     │  │  ║
║  │  │ L2: execute if score > 0.75                                 │  │  ║
║  │  │ L3: execute if score > 0.60                                 │  │  ║
║  │  └───────────────────────────┬─────────────────────────────────┘  │  ║
║  │                              │                                      │  ║
║  │  ┌───────────────────────────▼─────────────────────────────────┐  │  ║
║  │  │ Safety Envelope Monitor (HARD GATES — never overridden)     │  │  ║
║  │  │  • arc_power: [60 MW, 110 MW]                               │  │  ║
║  │  │  • wall_temp: never command action that raises wall >180°C  │  │  ║
║  │  │  • cooling: never reduce below 100 l/min                    │  │  ║
║  │  │  • rate-of-change: max ±20 MW / 3-second cycle              │  │  ║
║  │  └───────────────────────────┬─────────────────────────────────┘  │  ║
║  │                              │                                      │  ║
║  │  ┌───────────────────────────▼─────────────────────────────────┐  │  ║
║  │  │ Autonomous Execution Bus                                    │  │  ║
║  │  │ Converts AI decision → OPC-UA command → machine actuator   │  │  ║
║  │  │ (sim: writes to simulator control channel today)            │  │  ║
║  │  └───────────────────────────┬─────────────────────────────────┘  │  ║
║  │                              │                                      │  ║
║  │  ┌───────────────────────────▼─────────────────────────────────┐  │  ║
║  │  │ Outcome Learning Loop                                       │  │  ║
║  │  │ Predicted outcome vs. real outcome → model update signal    │  │  ║
║  │  │ Drift detected → escalate to L1 (operator) automatically    │  │  ║
║  │  └─────────────────────────────────────────────────────────────┘  │  ║
║  │                                                                   │  ║
║  │  ┌─────────────────────────────────────────────────────────────┐  │  ║
║  │  │ Decision Audit Ledger (immutable append-only log)           │  │  ║
║  │  │ Every autonomous action: timestamp, action, XAI, confidence,│  │  ║
║  │  │ predicted outcome, actual outcome, operator override (Y/N)   │  │  ║
║  │  └─────────────────────────────────────────────────────────────┘  │  ║
║  └───────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

### Component 1 — State Mirror Engine

**Purpose:** Keep the digital twin synchronized with the physical machine in real-time. Detect drift between twin state and real state — if they diverge, escalate to human.

**How it works:**
```
Physical Machine (OPC-UA / SCADA feed, or simulator)
    │
    │  Every 1 second: raw sensor values
    ▼
State Mirror Engine
    ├── Ingest: normalize sensor values → internal state vector
    ├── Compare: |twin_state - physical_state| > threshold?
    │       YES → DriftAlert → escalate to L1 (advisory)
    │       NO  → sync accepted
    ├── Update: push synchronized state to AI engine
    └── Publish: mirror.state Redis channel

Drift Thresholds:
    bath_temp:        ±25°C
    arc_power:        ±5 MW
    wall_temp:        ±15°C
    power_factor:     ±0.05
```

**New file:** `adt/state_mirror.py`

**New Redis channel:** `mirror.state` (1s cadence, real sensor values)

---

### Component 2 — Counterfactual Simulation Engine

**Purpose:** Before the AI acts, run N fast forward-simulations to predict consequences. Pick the action with the best predicted outcome. If predicted outcome later differs from reality → trigger model recalibration.

**How it works:**
```
Trigger: AI agent produces candidate_action

For each candidate action in action_space:
    1. Clone current twin state
    2. Fast-forward simulation for next 5 steps (15 minutes)
    3. Evaluate projected reward components
    4. Record: predicted_bath_temp, predicted_cost, predicted_health

Select action with highest projected R (subject to safety envelope)

Store prediction → compare against real outcome 5 steps later
If |predicted - actual| > threshold:
    → flag model divergence
    → reduce confidence score
    → escalate to L1 until confidence recovers
```

**Key capability:** The ADT never acts blindly. Every decision has a simulated prediction attached. This is the "twin" in "Decision Twin" — decisions are made *inside the simulation first*.

**New file:** `adt/counterfactual_engine.py`

**Configuration:**
```env
ADT_COUNTERFACTUAL_STEPS=5        # Simulate 5 steps forward (15 min)
ADT_COUNTERFACTUAL_ACTIONS=5      # Evaluate all 5 actions
ADT_DIVERGENCE_THRESHOLD=0.15     # 15% prediction error triggers escalation
```

---

### Component 3 — Confidence Engine

**Purpose:** Compute a single confidence score [0, 1] for each proposed action. The system only executes autonomously if confidence exceeds the level threshold.

**Confidence Formula:**
```
confidence = w1 · state_certainty
           + w2 · model_accuracy_recent
           + w3 · (1 - crisis_risk)
           + w4 · action_familiarity

Where:
  state_certainty       = 1 - normalized_sensor_noise
  model_accuracy_recent = rolling accuracy of last 20 predictions
  crisis_risk           = max(crisis_flag_scores) — any active alarm reduces this
  action_familiarity    = how often this action was taken in similar states
                          (from Decision Audit Ledger)

Weights: w1=0.30, w2=0.35, w3=0.25, w4=0.10  (tunable)

L2 threshold: 0.75  (auto-execute low-impact actions)
L3 threshold: 0.60  (auto-execute all safe actions)
Below threshold: → hold, publish advisory only (L1 fallback)
```

**New file:** `adt/confidence_engine.py`

---

### Component 4 — Safety Envelope Monitor

**Purpose:** Hard physical constraints that CANNOT be overridden by any AI decision at any autonomy level. These are the absolute boundaries that protect the machine and workers.

```
SAFETY ENVELOPE (enforced in hardware command layer)

┌──────────────────────────────────────────────────────────────────┐
│ Variable          │ Hard Min    │ Hard Max    │ Rate Limit        │
├───────────────────┼─────────────┼─────────────┼───────────────────┤
│ arc_power_mw      │ 60 MW       │ 110 MW      │ ±20 MW / cycle    │
│ cooling_l_min     │ 100 l/min   │ 400 l/min   │ ±50 l/min / cycle │
│ reactive_comp_mvar│ 0 MVAR      │ 30 MVAR     │ ±10 MVAR / cycle  │
│ wall_temp_delta   │ —           │ +5°C/cycle  │ never increase    │
│                   │             │             │ if wall > 180°C   │
└──────────────────────────────────────────────────────────────────┘

If AI produces a command that violates any bound:
  → Command is CLAMPED to the nearest safe value
  → Violation logged to audit ledger
  → Consecutive violations (≥3) trigger autonomy level downgrade (L3→L2→L1)
```

**New file:** `adt/safety_envelope.py`

This runs as a synchronous middleware layer between the AI decision and the execution bus — it cannot be disabled.

---

### Component 5 — Autonomous Execution Bus

**Purpose:** Translate AI decisions into machine commands. In simulation mode, writes to the `sim.control` Redis channel (which the simulator already listens to). In production mode, sends OPC-UA write commands to the SCADA system.

**Command Protocol:**
```
AI Decision
    │
    ├── Safety Envelope check (clamp/reject)
    │
    ├── Confidence check (proceed or hold)
    │
    ├── Level check (L2: flag if high-impact)
    │
    └── Execute:
        Sim mode:   Redis PUBLISH sim.control { "arc_mw": 85, "cooling": 180 }
        Prod mode:  OPC-UA WriteNode("ns=2;s=EAF2.ArcPower", 85)
                    + confirmation read-back within 2 seconds

Confirmation read-back:
    If machine state doesn't reflect command within 2s:
        → log execution_failure
        → escalate to L1 (operator)
        → do NOT retry automatically
```

**New file:** `adt/execution_bus.py`

**New env variable:** `ADT_EXECUTION_MODE=sim|opcua`

---

### Component 6 — Outcome Learning Loop

**Purpose:** Close the feedback loop. After every autonomous action, compare the predicted outcome (from Counterfactual Engine) to the actual outcome (from State Mirror). Use divergence to:
1. Update model accuracy metrics (feeds Confidence Engine)
2. Flag states where the model is unreliable
3. Generate training signals for PPO retraining (future)

```
Action at t=0: REDUCE_ARC_POWER (-15%)
Predicted at t=0: bath_temp[t+5] = 1,590°C, savings = 185 EGP/hr

Actual at t+5: bath_temp = 1,571°C (−19°C from prediction)
               savings   = 162 EGP/hr (−12% from prediction)

Divergence:
  temperature: |1590 - 1571| / 1590 = 1.2%  ← within tolerance (15%)
  savings:     |185 - 162| / 185    = 12.4% ← within tolerance (15%)

Result: prediction accepted, model_accuracy_recent += (1 - avg_divergence)
        = += 0.869 (rolling average over last 20 predictions)

If divergence > 15% on ANY metric:
    → escalate autonomy to L1 for this state class
    → log as divergence_event in audit ledger
    → flag for human review
```

**New file:** `adt/outcome_learning.py`

**New Redis channel:** `adt.outcomes` (stores predicted vs actual per action)

---

### Component 7 — Decision Audit Ledger

**Purpose:** Immutable, append-only record of every autonomous decision. Required for regulatory compliance, incident investigation, and RLHF training data.

**Schema per entry:**
```json
{
  "ledger_id":         "uuid",
  "timestamp":         "2026-05-07T18:32:08Z",
  "autonomy_level":    "L2",
  "machine_id":        "EAF_02_EZZ_AIN_SOKHNA",
  "action_label":      "REDUCE_ARC_POWER",
  "action_magnitude":  -15.0,
  "confidence_score":  0.87,
  "xai_reason_en":     "Peak pricing active. Bath safe. Reducing arc power.",
  "xai_reason_ar":     "تسعير الذروة نشط...",
  "predicted_outcome": {
    "bath_temp_t5":    1590,
    "savings_egp_hr":  185,
    "health_status":   "SAFE"
  },
  "actual_outcome": {
    "bath_temp_t5":    1571,
    "savings_egp_hr":  162,
    "health_status":   "SAFE"
  },
  "divergence_pct":    { "bath_temp": 1.2, "savings": 12.4 },
  "operator_override": false,
  "safety_clamped":    false
}
```

**Storage:** TimescaleDB (append-only hypertable, retention 2 years minimum)

**New file:** `adt/audit_ledger.py`

**New endpoint:** `GET /api/v1/adt/ledger?from=&to=&action=&autonomy_level=`

---

### New Dashboard Panel — ADT Control Center

The existing dashboard gets a new panel for ADT-specific controls and monitoring:

```
┌──────────────────────────────────────────────────────────────────────┐
│  AUTONOMOUS DECISION TWIN                          Autonomy: L2 ●    │
├─────────────────────────┬────────────────────────────────────────────┤
│  CONFIDENCE GAUGE        │  EXECUTION STATUS                         │
│                          │                                            │
│  Current: 0.87 ████████░ │  Last action:  18:32:08                  │
│  L2 gate: 0.75 ─────────│  REDUCE_ARC_POWER  (-15%)                 │
│  L3 gate: 0.60 ─────────│  Confidence: 0.87 ✓                       │
│                          │  Predicted bath: 1,590°C                  │
│  State Certainty: 0.94   │  Actual bath:    1,571°C  (+1.2% drift)  │
│  Model Accuracy: 0.89    │  Status: EXECUTED ✓                       │
│  Crisis Risk:    0.02    │                                            │
├─────────────────────────┼────────────────────────────────────────────┤
│  AUTONOMY CONTROLS       │  PREDICTION vs REALITY (last 10)          │
│                          │                                            │
│  Level: L1 ○ L2 ● L3 ○  │  ████░ bath_temp    97.8% accurate       │
│  [Upgrade to L3]         │  ████░ savings_egp  91.2% accurate       │
│                          │  █████ health       100%  accurate        │
│  Override: [HOLD AI]     │                                            │
├──────────────────────────┴────────────────────────────────────────────┤
│  AUDIT LEDGER  (last 5 autonomous actions)              [View All]   │
│  18:32  L2  REDUCE_ARC ✓  conf=0.87  pred=1590°  act=1571°  Δ=1.2% │
│  18:29  L2  RAISE_PF   ✓  conf=0.81  pred=0.91   act=0.90   Δ=1.1% │
│  18:26  L1  HOLD       —  conf=0.71  below L2 gate, advisory only   │
│  18:23  L2  REDUCE_ARC ✓  conf=0.83  pred=1580°  act=1568°  Δ=0.8% │
│  18:20  L2  HOLD       ✓  conf=0.92  no action needed               │
└───────────────────────────────────────────────────────────────────────┘
```

---

### New API Endpoints (ADT)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/adt/status` | Current autonomy level, confidence score, execution stats |
| POST | `/api/v1/adt/level` | Set autonomy level (L0/L1/L2/L3) |
| GET | `/api/v1/adt/ledger` | Query audit ledger (filters: time, action, level) |
| GET | `/api/v1/adt/predictions` | Last N predicted vs actual outcome pairs |
| POST | `/api/v1/adt/override` | Operator hold — pause autonomous execution |
| GET | `/api/v1/adt/confidence` | Real-time confidence score breakdown |
| GET | `/api/v1/adt/safety` | Safety envelope status + recent clamp events |

---

### New Files to Create

```
adt/
├── __init__.py
├── state_mirror.py          State sync engine + drift detection
├── counterfactual_engine.py Fast-forward simulation for N actions
├── confidence_engine.py     Score computation [0,1]
├── safety_envelope.py       Hard constraint enforcement (synchronous)
├── execution_bus.py         Sim/OPC-UA command dispatch
├── outcome_learning.py      Predicted vs actual + model accuracy tracking
└── audit_ledger.py          Append-only decision log writer

frontend/components/
└── ADTControlPanel.tsx      New dashboard panel (confidence, ledger, level)

backend/
├── main.py                  7 new ADT endpoints added
└── services/
    └── adt_service.py       ADT state manager (glues all adt/ modules)
```

---

### New Environment Variables

```env
# Autonomous Decision Twin
ADT_ENABLED=false                     # Start disabled (operator enables)
ADT_DEFAULT_LEVEL=L1                  # Default: advisory only
ADT_L2_CONFIDENCE_THRESHOLD=0.75      # Auto-execute low-impact above this
ADT_L3_CONFIDENCE_THRESHOLD=0.60      # Auto-execute all safe actions
ADT_EXECUTION_MODE=sim                # sim | opcua
ADT_OPCUA_ENDPOINT=opc.tcp://scada:4840
ADT_COUNTERFACTUAL_STEPS=5            # Steps to simulate forward
ADT_DIVERGENCE_THRESHOLD=0.15         # 15% error triggers escalation
ADT_APPROVAL_TIMEOUT_SECONDS=30       # L2 high-impact approval window
ADT_LEDGER_RETENTION_DAYS=730         # 2-year audit retention
ADT_CONFIDENCE_WEIGHTS=0.30,0.35,0.25,0.10  # w1,w2,w3,w4
ADT_MIN_L3_TRACK_RECORD_DAYS=30       # Days at L2 before L3 allowed
```

---

### Implementation Plan — 4 Phases

#### Phase 1: Foundation (Weeks 1–2)
**Goal:** ADT layer runs in L1 (advisory) mode — same as current system but with the new architecture wired up.

```
Week 1:
  [ ] Create adt/ package structure
  [ ] Implement state_mirror.py (drift detection on simulator telemetry)
  [ ] Implement safety_envelope.py (hard clamp logic, unit tested)
  [ ] Implement audit_ledger.py (write to TimescaleDB or JSON file initially)
  [ ] Add GET /api/v1/adt/status endpoint
  [ ] Add POST /api/v1/adt/override endpoint

Week 2:
  [ ] Implement confidence_engine.py (initial formula, v1 weights)
  [ ] Add GET /api/v1/adt/confidence endpoint
  [ ] Add ADTControlPanel.tsx to frontend (read-only, shows confidence)
  [ ] Integration test: state mirror drift detection with injected bad telemetry
  [ ] All existing tests still pass (no regression)
```

**Exit criterion:** Dashboard shows confidence score and audit ledger. Safety envelope tested with 1000 random adversarial commands — zero violations pass through.

---

#### Phase 2: Counterfactual + Supervised Execution (Weeks 3–4)
**Goal:** System executes LOW-IMPACT actions autonomously at L2. High-impact actions require operator confirmation.

```
Week 3:
  [ ] Implement counterfactual_engine.py
        - Clone EAFMachine state, fast-forward 5 steps
        - Evaluate all 5 actions, pick best
        - Store predictions in memory (Redis hash per cycle)
  [ ] Implement execution_bus.py (sim mode: publish to sim.control)
  [ ] Add POST /api/v1/adt/level endpoint
  [ ] L2 action classification table:
        LOW-IMPACT:  RAISE_PF_COMPENSATION, HOLD_STEADY
        HIGH-IMPACT: REDUCE_ARC_POWER (>10%), EMERGENCY_COOLING, PRE_PEAK_DROP

Week 4:
  [ ] Wire: Confidence ≥ 0.75 + LOW-IMPACT → execution_bus.execute()
  [ ] Wire: HIGH-IMPACT → push to /api/v1/adt/pending_approval (30s timeout)
  [ ] Frontend: approval notification badge + approve/reject button
  [ ] Add GET /api/v1/adt/ledger endpoint (query last N entries)
  [ ] Integration test: L2 auto-execute through full heat cycle
  [ ] Regression test: L1 advisory still works if L2 disabled
```

**Exit criterion:** System runs 10 complete heat cycles at L2, zero safety violations, operator approval flow tested for high-impact actions.

---

#### Phase 3: Outcome Learning + Full Autonomy (Weeks 5–6)
**Goal:** Full L3 autonomy with self-correcting feedback loop.

```
Week 5:
  [ ] Implement outcome_learning.py
        - Match predictions to actuals at t+5
        - Compute per-metric divergence %
        - Update model_accuracy_recent rolling window
        - Trigger L1 escalation if divergence > threshold
  [ ] Feed outcome accuracy into confidence_engine.py (model_accuracy_recent term)
  [ ] Add GET /api/v1/adt/predictions endpoint
  [ ] Frontend: prediction vs actual accuracy bars in ADTControlPanel

Week 6:
  [ ] Implement L3 autonomy path (all safe actions auto-executed)
  [ ] L3 unlock gate: 30-day L2 track record + zero safety violations
  [ ] Automatic autonomy downgrade on consecutive safety clamps (≥3)
  [ ] Full audit ledger: predicted + actual + divergence per entry
  [ ] TimescaleDB migration: replace JSON file ledger with real DB
  [ ] End-to-end demo: L3 full autonomous shift (8h simulated)
```

**Exit criterion:** 30-day (simulated) track record at L2, clean L3 upgrade, full audit trail queryable, drift-triggered downgrade tested.

---

#### Phase 4: Production Hardening (Weeks 7–8)
**Goal:** Production-ready ADT with OPC-UA connector, RBAC, and compliance reports.

```
Week 7:
  [ ] OPC-UA connector in execution_bus.py (opcua mode)
  [ ] SCADA adapter: OPC-UA read (state mirror) + write (execution bus)
  [ ] Command confirmation read-back (2s timeout → escalate)
  [ ] Authentication: JWT required for all /adt/ endpoints
  [ ] RBAC: Operator=L2 control, Supervisor=L3 unlock, Admin=safety config
  [ ] Rate limiting on execution bus (prevent command flooding)

Week 8:
  [ ] Audit ledger export: CSV + JSON for compliance reporting
  [ ] CBAM integration: autonomous actions tagged with CO₂ impact
  [ ] Stress test: 1000-cycle autonomous run, measure clamp rate + divergence
  [ ] Security review: OPC-UA auth, command injection prevention
  [ ] Documentation: operator training guide, safety procedures
  [ ] Load test: 5 concurrent machines at L2/L3
```

**Exit criterion:** System passes shadow-mode 30-day deployment test at real Ain Sokhna facility, zero unauthorized commands, full audit trail.

---

### ADT Business Impact

The current advisory system captures only a fraction of potential savings because operators act on approximately 30–50% of recommendations. The ADT closes this gap:

| Scenario | Energy Saved | Annual Savings (EGP) |
|----------|-------------|---------------------|
| Current (L1 advisory, 40% adoption) | ~4% | ~46M EGP |
| L2 supervised autonomous | ~9% | ~104M EGP |
| L3 full autonomous | ~13% | ~150M EGP |
| L3 + demand forecaster (M2) | ~16% | ~184M EGP |

**The ADT doubles the financial return of the advisory system.**

Additional ADT-specific value:
- **Consistency:** Every peak hour managed, every PF excursion caught — no operator fatigue
- **Speed:** 3-second response time vs. 30–120 second human response
- **Audit trail:** Full legal-grade record for every machine command (regulatory compliance)
- **Learning:** Each shift makes the system measurably more accurate (outcome learning loop)

---

### Safety Philosophy

The ADT is designed with the principle that **safety is non-negotiable and non-bypassable**:

1. **Safety Envelope is synchronous** — it runs before every command leaves the system, it cannot be disabled via API or config
2. **Autonomy is earned** — L3 requires a 30-day clean track record; it cannot be unlocked by config alone
3. **Human override is always available** — one button on the dashboard halts all autonomous execution immediately
4. **Drift triggers downgrade** — if the AI's predictions are wrong, it loses autonomy automatically
5. **All decisions are auditable** — nothing happens without a ledger entry that includes the full XAI reason

> "The twin makes decisions like a senior engineer who has memorized every safety procedure, never gets tired, and always writes down what they did and why."

---

## 16. Dynamic Pricing Engine — Full Plan

> **STATUS: IMPLEMENTED ✓** — All 6 components coded and integrated as of 2026-05-02.  
> Code: `backend/pricing/`, `ai_engine/environment.py` (32D obs), `ai_engine/agent.py` (PRE_PEAK_DROP), `frontend/components/DynamicPricingPanel.tsx`.  
> 8 new REST endpoints, 2 Redis channels (`pricing.live`, `pricing.forecast`).

### Overview

The **Dynamic Pricing Engine (DPE)** is the financial intelligence layer of Opti-Twin. The system started with a fixed flat tariff (1.60 EGP/kWh). The DPE replaces this with a live, multi-signal pricing layer that:

- Ingests real-time or near-real-time electricity price signals from multiple sources
- Forecasts the next 4-hour price curve using a machine learning model
- Participates in grid **Demand Response (DR)** programs — earning payments for reducing load on request
- Stacks multiple revenue streams simultaneously (savings + DR payments + capacity credits)
- Feeds live prices directly into the RL reward function so the AI optimizes against the *actual* market, not a flat rate assumption

**Why this matters:**
> Egypt's electricity market is undergoing liberalization. The Egyptian Electricity Holding Company (EEHC) and EgyptERA are piloting real-time pricing for industrial UHV consumers. Factories that can respond intelligently to price signals will save 20–35% more than those using flat-rate contracts — and earn additional revenue from demand flexibility.

---

### Current State vs. Target State

```
CURRENT (Flat Tariff):
  Price signal = constant 1.60 EGP/kWh  (or TOU toggle: 2.5 peak / 1.2 off-peak)
  AI reward α = 1.0 × fixed_rate × power_saved
  Revenue streams: 1 (cost savings only)

TARGET (Dynamic Pricing Engine):
  Price signal = real-time spot price API + 4h forecast curve
  AI reward α = 1.0 × live_price(t) × power_saved(t)   ← changes every cycle
  Revenue streams: 4 (savings + DR payment + capacity credit + ancillary services)
  Optimization horizon: 4 hours ahead (not just current-cycle reactive)
```

---

### Architecture: Dynamic Pricing Engine

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    DYNAMIC PRICING ENGINE                                ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │  COMPONENT 1: Price Signal Broker                                │   ║
║  │                                                                  │   ║
║  │  Source A: EEHC/EgyptERA real-time API (production)             │   ║
║  │  Source B: Simulated spot market (hackathon/dev mode)            │   ║
║  │  Source C: Day-ahead auction prices (when market matures)        │   ║
║  │  Source D: Demand Response event stream (grid operator signals)  │   ║
║  │                                                                  │   ║
║  │  → Publishes: pricing.live  (Redis, every 60s)                  │   ║
║  │  → Publishes: pricing.dr_events  (Redis, on event)              │   ║
║  └─────────────────────────────┬────────────────────────────────────┘   ║
║                                 │                                        ║
║  ┌──────────────────────────────▼────────────────────────────────────┐  ║
║  │  COMPONENT 2: Price Forecaster (ML)                               │  ║
║  │                                                                   │  ║
║  │  Model: LSTM or Temporal Fusion Transformer                       │  ║
║  │  Input features (12):                                             │  ║
║  │    time_of_day, day_of_week, industrial_calendar_flag,           │  ║
║  │    last_24h_prices[8], grid_load_mw, temperature_cairo,          │  ║
║  │    gas_spot_price, ramadan_flag, public_holiday_flag             │  ║
║  │  Output: price_curve[t+1 … t+48] (30-min steps, 24h ahead)      │  ║
║  │           + confidence_interval (P10, P50, P90)                  │  ║
║  │                                                                   │  ║
║  │  → Publishes: pricing.forecast  (Redis, every 30 min)            │  ║
║  └─────────────────────────────┬─────────────────────────────────────┘  ║
║                                 │                                        ║
║  ┌──────────────────────────────▼─────────────────────────────────────┐ ║
║  │  COMPONENT 3: Demand Response Controller                          │ ║
║  │                                                                   │ ║
║  │  Listens to: pricing.dr_events                                    │ ║
║  │  DR Event types:                                                  │ ║
║  │    CURTAILMENT  → grid asks to shed N MW for T minutes            │ ║
║  │    INTERRUPTIBLE → grid cuts power to max 60 MW                  │ ║
║  │    FREQUENCY_RESPONSE → immediate ±10 MW within 10 seconds       │ ║
║  │                                                                   │ ║
║  │  Calculates: optimal load reduction + production impact           │ ║
║  │  Calculates: DR payment earned (EGP/MWh × MW reduced)            │ ║
║  │  Triggers:   Execution Bus command (if ADT L2+) or advisory       │ ║
║  │                                                                   │ ║
║  │  → Publishes: dr.response  (Redis)                               │ ║
║  └─────────────────────────────┬─────────────────────────────────────┘ ║
║                                 │                                        ║
║  ┌──────────────────────────────▼─────────────────────────────────────┐ ║
║  │  COMPONENT 4: Dynamic Reward Adapter                              │ ║
║  │                                                                   │ ║
║  │  Replaces static tariff in RL reward function with live signal:   │ ║
║  │                                                                   │ ║
║  │  OLD: R_energy = α × fixed_rate × ΔP × dt                        │ ║
║  │  NEW: R_energy = α × price_live(t) × ΔP × dt                     │ ║
║  │         + β_dr  × dr_payment_earned(t)                            │ ║
║  │         + β_cap × capacity_credit(t)                              │ ║
║  │                                                                   │ ║
║  │  Also: injects price_curve[t+1…t+16] into observation space      │ ║
║  │  (4h horizon at 15-min steps = 16 new observation dimensions)    │ ║
║  │                                                                   │ ║
║  └─────────────────────────────┬─────────────────────────────────────┘ ║
║                                 │                                        ║
║  ┌──────────────────────────────▼─────────────────────────────────────┐ ║
║  │  COMPONENT 5: Load Flexibility Scheduler                          │ ║
║  │                                                                   │ ║
║  │  Horizon: 4–8 hours (cross-shift optimization)                    │ ║
║  │  Solves: When to schedule each heat (MELTING_PHASE_1/2)           │ ║
║  │          such that total energy cost is minimized                 │ ║
║  │          while meeting daily production quota (batches)           │ ║
║  │                                                                   │ ║
║  │  Method: Mixed-Integer Linear Programming (MILP) or              │ ║
║  │          Greedy schedule on price forecast curve                  │ ║
║  │                                                                   │ ║
║  │  Output: recommended_heat_schedule (start times for next N heats) │ ║
║  │  → Published: schedule.recommendation (Redis)                    │ ║
║  └─────────────────────────────┬─────────────────────────────────────┘ ║
║                                 │                                        ║
║  ┌──────────────────────────────▼─────────────────────────────────────┐ ║
║  │  COMPONENT 6: Revenue Optimizer (Multi-Stream Stacker)            │ ║
║  │                                                                   │ ║
║  │  Tracks and maximizes 4 simultaneous revenue streams:            │ ║
║  │                                                                   │ ║
║  │  Stream 1: ENERGY SAVINGS        ΔP × live_price × dt            │ ║
║  │  Stream 2: DR PAYMENTS           MW_reduced × dr_rate × duration  │ ║
║  │  Stream 3: CAPACITY CREDITS      contracted_MW × cap_rate/month   │ ║
║  │  Stream 4: ANCILLARY SERVICES    ΔHz_response × freq_rate         │ ║
║  │                                                                   │ ║
║  │  Resolves conflicts: e.g. DR event during peak melting phase      │ ║
║  │  → calculate cost of production delay vs. DR payment earned      │ ║
║  │  → recommend: accept DR if payment > production_cost_impact       │ ║
║  └────────────────────────────────────────────────────────────────────┘ ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

### Component 1 — Price Signal Broker

**Purpose:** Single normalized interface for all external price signals, regardless of source. Isolates the rest of the system from API changes.

**Modes:**

| Mode | Source | Update Rate | Use Case |
|------|--------|------------|---------|
| `sim_flat` | `.env` constant (1.60 EGP) | Never | Current system |
| `sim_tou` | TOU schedule (binary peak flag) | Hourly | Current TOU mode |
| `sim_spot` | Synthetic price generator | Every 30 min | Dev/demo dynamic pricing |
| `live_eehc` | EEHC real-time API (future) | Every 15 min | Production |
| `live_dayahead` | Day-ahead auction (future) | Once/day | Market participation |

**Synthetic spot price generator** (for demo/development):
```python
# Simulates realistic Egyptian industrial spot price curves
base = 1.60 EGP/kWh
peak_multiplier = 1.8–2.5×  (17:00–22:00)
shoulder_multiplier = 1.2×  (07:00–17:00, 22:00–24:00)
offpeak_multiplier = 0.85×  (00:00–07:00)
noise = ±0.08 EGP/kWh (Gaussian)
demand_events = ±0.40 EGP spike (random, 1–3/day, 15–45 min duration)
seasonal_factor = summer +15% (grid AC load), winter -5%
```

**New file:** `pricing/price_signal_broker.py`

**New Redis channel:** `pricing.live` — publishes every 60 seconds:
```json
{
  "timestamp": "2026-05-07T18:00:00Z",
  "price_egp_kwh": 2.43,
  "price_source": "sim_spot",
  "tariff_class": "UHV_220-132kV",
  "is_peak": true,
  "is_dr_event": false,
  "dr_event_id": null,
  "confidence": 1.0
}
```

---

### Component 2 — Price Forecaster

**Purpose:** Predict the electricity price for the next 24 hours at 30-minute resolution. The AI agent uses this to make *anticipatory* decisions — reducing load *before* a price spike rather than *after* it starts.

**Model Architecture:**
```
Input window: last 48 price points (24h at 30-min resolution)
+ 12 contextual features:
    time_sin, time_cos (cyclical encoding)
    day_of_week_sin, day_of_week_cos
    is_ramadan (bool)
    is_public_holiday (bool)
    temperature_celsius (Cairo)
    grid_load_mw (from public EEHC reports)
    gas_spot_price_usd (proxy for generation cost)
    industrial_calendar_flag (factory shutdown days)
    month_sin, month_cos

Output: price_forecast[48] — 48 values, 30-min steps = 24h ahead
        confidence_p10[48], confidence_p50[48], confidence_p90[48]

Model options:
  Baseline:    Prophet (Facebook, fast, interpretable)
  Production:  Temporal Fusion Transformer (state-of-art, handles regime shifts)
  Fallback:    Historical mean by hour-of-week (always available)
```

**Forecast quality target:** MAE < 0.15 EGP/kWh on held-out test set (Egyptian industrial price data 2022–2025).

**New file:** `pricing/price_forecaster.py`

**New Redis channel:** `pricing.forecast` — published every 30 minutes:
```json
{
  "generated_at": "2026-05-07T18:00:00Z",
  "horizon_hours": 24,
  "step_minutes": 30,
  "forecast": [
    {"t": "18:00", "p50": 2.43, "p10": 2.21, "p90": 2.68},
    {"t": "18:30", "p50": 2.51, "p10": 2.28, "p90": 2.79},
    ...
  ],
  "model": "temporal_fusion_transformer_v1",
  "mae_recent_7d": 0.12
}
```

---

### Component 3 — Demand Response Controller

**Purpose:** Enable the factory to participate in grid operator DR programs — earning payments for reducing electrical load on request.

**Demand Response Program Types (Egypt context):**

| Program | Trigger | Factory Action | Payment |
|---------|---------|---------------|---------|
| **CURTAILMENT** | Grid operator signals 30-min advance notice | Reduce arc power by agreed MW for agreed duration | ~150–300 EGP/MWh reduced |
| **INTERRUPTIBLE** | Extreme grid stress, immediate cap | Arc power hard-cap to 60 MW until release | ~400–600 EGP/MWh reduced |
| **FREQUENCY_RESPONSE** | Grid Hz drops below 49.8 Hz | Reduce load ±10 MW within 10 seconds | ~800–1200 EGP/MWh (premium) |
| **VOLUNTARY PEAK** | Price signal exceeds threshold | Voluntarily curtail during highest-price windows | Self-savings only |

**DR Decision Logic:**
```
On DR event received:
    1. Calculate: MW_can_reduce = current_arc_power - min_safe_power
    2. Calculate: dr_payment = MW_can_reduce × event_duration × dr_rate
    3. Calculate: production_cost = delay_tonnes × (value_per_tonne - cost_per_tonne)
    4. Calculate: net_benefit = dr_payment - production_cost - startup_penalty

    If net_benefit > 0 AND heat_phase NOT IN [TAPPING, BORE_DOWN]:
        → Accept DR event → publish to execution_bus
        → Log to dr_participation_ledger
    Else:
        → Decline DR event → notify grid operator
        → Log reason (production_priority / unsafe_phase)
```

**New file:** `pricing/demand_response_controller.py`

**New Redis channel:** `pricing.dr_events` — incoming grid operator signals

**New Redis channel:** `dr.response` — factory response (accept/decline + action plan)

---

### Component 4 — Dynamic Reward Adapter

**Purpose:** Update the RL reward function in real-time with live price signals. This is the bridge between the pricing layer and the AI core.

**Current reward (static):**
```python
R_energy = alpha * FIXED_RATE * (P_baseline - P_actual) * dt_hours
# FIXED_RATE = 1.60 EGP/kWh — never changes
```

**New reward (dynamic):**
```python
R_energy = alpha * price_live(t) * (P_baseline - P_actual) * dt_hours
         + beta_dr  * dr_payment_earned(t)           # demand response bonus
         + beta_cap * capacity_credit_rate * contracted_MW  # capacity bonus

# price_live(t) changes every 60 seconds
# When price = 2.5 EGP/kWh: reward is 1.56× higher for same MW reduction
# When price = 0.85 EGP/kWh: reward is 0.53× → agent correctly does less curtailment
```

**Observation space expansion (+16 dimensions):**
```
Current obs space: 16 dimensions (normalized)

New obs dimensions added:
  [16]:  price_now_normalized           current live price
  [17]:  price_t+1_normalized           forecast 30 min ahead
  [18]:  price_t+2_normalized           forecast 1 hour ahead
  [19]:  price_t+3_normalized           forecast 1.5 hours ahead
  [20]:  price_t+4_normalized           forecast 2 hours ahead
  [21]:  price_t+5_normalized           forecast 2.5 hours ahead
  [22]:  price_t+6_normalized           forecast 3 hours ahead
  [23]:  price_t+7_normalized           forecast 3.5 hours ahead
  [24]:  price_t+8_normalized           forecast 4 hours ahead
  [25]:  price_max_next4h_normalized    max price in next 4h window
  [26]:  price_min_next4h_normalized    min price in next 4h window
  [27]:  dr_event_active                bool: DR event in progress
  [28]:  dr_payment_rate_normalized     current DR payment rate
  [29]:  capacity_credit_active         bool: in contracted capacity window
  [30]:  price_trend_slope              rising/falling/flat price signal
  [31]:  hours_until_next_peak          normalized time to next peak window

New obs space: 32 dimensions (was 16)
```

**New file:** `pricing/dynamic_reward_adapter.py`

This module patches `RewardFunction.compute()` at runtime — no changes needed to the base reward function file.

---

### Component 5 — Load Flexibility Scheduler

**Purpose:** Multi-heat schedule optimizer. Given the 4–24 hour price forecast, determine the optimal *start time* for each upcoming heat to minimize total energy cost while meeting the production quota (batches per shift).

**Problem formulation:**
```
Minimize:    Σ_heats  energy_cost(heat_i) = Σ Σ price(t) × arc_power(t) × dt
Subject to:
  - N heats must complete within the shift window (8h / 12h)
  - Each heat takes ~70 minutes (fixed cycle time)
  - At most 1 heat running at a time (single furnace)
  - Furnace idle time between heats: min 5 min (refractory recovery)
  - High-power phases (MELTING 1/2) must not be interrupted mid-phase
  - Production deadline: all N heats done before shift_end

Approach A (fast, demo-ready):
  Greedy: sort available time slots by forecast price,
  schedule MELTING phases into cheapest slots first

Approach B (optimal, production):
  MILP using scipy.optimize or PuLP
  Variables: heat_start_time_i (integer, minutes since shift start)
  Constraints: non-overlapping, deadline, min_gap
  Objective: minimize total_cost
```

**Output: recommended schedule published to dashboard:**
```
Recommended Heat Schedule (next 8h)
┌──────┬───────────┬────────────┬───────────────┬──────────────────┐
│ Heat │ Start     │ Phase      │ Price (EGP)   │ Cost Estimate    │
├──────┼───────────┼────────────┼───────────────┼──────────────────┤
│  #8  │ 18:05     │ (in prog.) │ 2.43 EGP/kWh  │ current heat     │
│  #9  │ 19:15     │ scheduled  │ 1.95 EGP/kWh  │ ~42,300 EGP      │
│ #10  │ 20:30     │ scheduled  │ 1.72 EGP/kWh  │ ~37,800 EGP      │
│ #11  │ 21:45     │ scheduled  │ 1.68 EGP/kWh  │ ~36,900 EGP      │
│ #12  │ 23:00     │ scheduled  │ 1.45 EGP/kWh  │ ~31,800 EGP      │
├──────┴───────────┴────────────┴───────────────┼──────────────────┤
│  vs. unoptimized schedule (heats run back-to-back continuously)   │
│  Unoptimized cost estimate: ~196,500 EGP                          │
│  Optimized cost estimate:   ~168,800 EGP    SAVINGS: 27,700 EGP  │
└───────────────────────────────────────────────────────────────────┘
```

**New file:** `pricing/load_flexibility_scheduler.py`

**New Redis channel:** `schedule.recommendation`

---

### Component 6 — Revenue Optimizer (Multi-Stream Stacker)

**Purpose:** Track and maximize all 4 revenue streams simultaneously. When streams conflict (e.g., DR event during peak melting phase), calculate net benefit and recommend accept/decline.

**Revenue Streams:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  REVENUE STREAM         MECHANISM               TYPICAL RATE        │
├─────────────────────────────────────────────────────────────────────┤
│  1. Energy Savings      ΔP × live_price × dt   1.60–2.50 EGP/kWh  │
│                         (vs. full-power baseline)                   │
│                                                                     │
│  2. DR Payments         MW_shed × duration      150–1200 EGP/MWh   │
│                         × dr_program_rate       (program-dependent) │
│                                                                     │
│  3. Capacity Credits    contracted_MW × rate    ~80 EGP/kW/month   │
│                         (for committing to be flexible)             │
│                                                                     │
│  4. Ancillary Services  ΔMW within 10s          800–1200 EGP/MWh   │
│                         frequency response      (premium service)   │
└─────────────────────────────────────────────────────────────────────┘
```

**Conflict resolution example:**
```
Scenario: DR CURTAILMENT event arrives at 18:32
          Factory is currently in MELTING_PHASE_2 (heat #8)

Revenue Optimizer calculates:
  DR payment:          35 MW × 45 min × 250 EGP/MWh  = 6,562 EGP
  Production impact:   delay 45 min × 2 heats affected = 1.5t lost
                       1.5t × (8,400 EGP/t revenue - 6,100 EGP/t cost)
                     = 1.5t × 2,300 EGP/t = 3,450 EGP opportunity cost
  Net DR benefit:      6,562 - 3,450 = +3,112 EGP

Decision: ACCEPT DR event (net positive)
XAI: "DR event accepted. 45-min curtailment earns 6,562 EGP.
      Production delay costs ~3,450 EGP. Net gain: 3,112 EGP."
```

**New file:** `pricing/revenue_optimizer.py`

---

### New Dashboard Panel — Dynamic Pricing Center

```
┌──────────────────────────────────────────────────────────────────────┐
│  DYNAMIC PRICING                              Source: sim_spot ●     │
├───────────────────────────┬──────────────────────────────────────────┤
│  LIVE PRICE                │  4-HOUR PRICE FORECAST                  │
│                            │                                          │
│  2.43 EGP/kWh              │   ▲ EGP                                 │
│  ▲ PEAK (+52% vs base)     │   2.8│         ╭──╮                     │
│                            │   2.4│    ─────╯  ╰──╮                  │
│  vs. flat:  +0.83 EGP/kWh  │   2.0│               ╰────             │
│  vs. 1h ago: +0.12 EGP/kWh │   1.6│                    ────         │
│                            │    ──┴──────────────────────── t        │
│  Next cheap window:        │   now  +1h  +2h  +3h  +4h              │
│  21:30  →  1.45 EGP/kWh    │   [P10 ░░░ P50 ─── P90 ░░░]           │
├───────────────────────────┴──────────────────────────────────────────┤
│  REVENUE STREAMS                               TODAY'S TOTAL         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ ⚡ Energy Savings       ████████████████████░░   3,840 EGP   │   │
│  │ 📡 DR Payments          ████░░░░░░░░░░░░░░░░░░     780 EGP   │   │
│  │ 🔋 Capacity Credits     ██░░░░░░░░░░░░░░░░░░░░     320 EGP   │   │
│  │ ⚡ Ancillary Services   █░░░░░░░░░░░░░░░░░░░░░      95 EGP   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  TOTAL STACKED REVENUE TODAY:                        5,035 EGP      │
│  vs. flat-rate advisory system:                      2,340 EGP      │
│  DYNAMIC PRICING UPLIFT:                            +2,695 EGP (+115%)│
├──────────────────────────────────────────────────────────────────────┤
│  HEAT SCHEDULE                              [Apply Schedule]         │
│  Heat #9: 19:15  (1.95 EGP)  Heat #10: 20:30  (1.72 EGP)           │
│  Heat #11: 21:45 (1.68 EGP)  Heat #12: 23:00  (1.45 EGP)           │
│  Optimized savings vs. back-to-back: 27,700 EGP                     │
├──────────────────────────────────────────────────────────────────────┤
│  DR EVENTS                                                           │
│  18:32  CURTAILMENT ✓ accepted  +6,562 EGP  45 min  net +3,112 EGP  │
│  17:15  VOLUNTARY   ✓ accepted  +780 EGP    30 min  net +780 EGP    │
└──────────────────────────────────────────────────────────────────────┘
```

---

### New API Endpoints (Dynamic Pricing)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/pricing/live` | Current live price, source, peak status |
| GET | `/api/v1/pricing/forecast` | 24h price forecast curve (P10/P50/P90) |
| GET | `/api/v1/pricing/mode` | Current pricing mode (flat/tou/sim_spot/live) |
| POST | `/api/v1/pricing/mode` | Switch pricing mode |
| GET | `/api/v1/pricing/revenue` | Today's stacked revenue breakdown |
| GET | `/api/v1/pricing/schedule` | Recommended heat schedule |
| POST | `/api/v1/pricing/schedule/apply` | Apply recommended schedule |
| GET | `/api/v1/pricing/dr/events` | DR event history (today) |
| POST | `/api/v1/pricing/dr/respond` | Manual accept/decline DR event override |

---

### New Files to Create

```
pricing/
├── __init__.py
├── price_signal_broker.py         Multi-source price signal ingestion
├── synthetic_spot_generator.py    Realistic simulated Egyptian spot prices
├── price_forecaster.py            LSTM/TFT forecast model + Prophet fallback
├── demand_response_controller.py  DR event handler + net benefit calculator
├── dynamic_reward_adapter.py      Patches RewardFunction with live prices
├── load_flexibility_scheduler.py  Multi-heat schedule optimizer (MILP/greedy)
└── revenue_optimizer.py           4-stream revenue stacker + conflict resolver

frontend/components/
└── DynamicPricingPanel.tsx        New dashboard panel (price + forecast + DR + schedule)

backend/services/
└── pricing_service.py             Glues pricing/ modules into backend state
```

---

### New Environment Variables

```env
# Dynamic Pricing Engine
DPE_ENABLED=false                          # Start disabled
DPE_MODE=sim_spot                          # flat | sim_tou | sim_spot | live_eehc
DPE_PRICE_UPDATE_INTERVAL_SECONDS=60       # How often to update live price
DPE_FORECAST_HORIZON_HOURS=24              # Forecast look-ahead
DPE_FORECAST_STEP_MINUTES=30              # Forecast resolution
DPE_FORECASTER_MODEL=prophet               # prophet | lstm | tft | mean_baseline
DPE_DR_ENABLED=false                       # Demand response participation
DPE_DR_MIN_DURATION_MINUTES=15             # Minimum DR event to accept
DPE_DR_CURTAILMENT_RATE_EGP=250           # EGP/MWh curtailment payment
DPE_DR_INTERRUPTIBLE_RATE_EGP=450         # EGP/MWh interruptible payment
DPE_DR_FREQUENCY_RATE_EGP=950            # EGP/MWh frequency response payment
DPE_CAPACITY_CREDIT_RATE_EGP=80          # EGP/kW/month capacity credit
DPE_SCHEDULE_OPTIMIZER=greedy             # greedy | milp
DPE_SCHEDULE_HORIZON_HOURS=8             # Shift planning horizon
DPE_SPOT_PEAK_MULTIPLIER=1.8             # Sim spot peak multiplier
DPE_SPOT_OFFPEAK_MULTIPLIER=0.85         # Sim spot off-peak multiplier
DPE_SPOT_NOISE_EGP=0.08                  # Sim spot price noise std dev
```

---

### Updated Observation Space (32D → used in retrained PPO)

```
Dimension  Name                         Source
─────────  ───────────────────────────  ──────────────────────────
 0         electricity_price_norm       DPE live price (was static)
 1         grid_frequency_norm          simulator
 2         bath_temp_norm               thermal model
 3         wall_temp_norm               thermal model
 4         arc_power_norm               EAF machine
 5         power_factor_norm            EAF machine
 6         heat_progress_norm           EAF machine
 7         production_backlog_norm      EAF machine
 8         batches_today_norm           EAF machine
 9         energy_kwh_today_norm        EAF machine
10         oxygen_injection_norm        EAF machine
11         electrode_consumption_norm   EAF machine
12         cooling_water_norm           EAF machine
13         is_peak                      DPE (was static TOU flag)
14         tou_mode                     config
15         crisis_composite_norm        simulator events
16         price_t1_norm                DPE forecast +30 min  ← NEW
17         price_t2_norm                DPE forecast +60 min  ← NEW
18         price_t3_norm                DPE forecast +90 min  ← NEW
19         price_t4_norm                DPE forecast +2h      ← NEW
20         price_t5_norm                DPE forecast +2.5h    ← NEW
21         price_t6_norm                DPE forecast +3h      ← NEW
22         price_t7_norm                DPE forecast +3.5h    ← NEW
23         price_t8_norm                DPE forecast +4h      ← NEW
24         price_max_4h_norm            DPE forecast summary  ← NEW
25         price_min_4h_norm            DPE forecast summary  ← NEW
26         dr_event_active              DR controller         ← NEW
27         dr_payment_rate_norm         DR controller         ← NEW
28         capacity_credit_active       revenue optimizer     ← NEW
29         price_trend_slope_norm       DPE forecaster        ← NEW
30         hours_to_next_peak_norm      DPE forecaster        ← NEW
31         schedule_alignment_score     load scheduler        ← NEW
```

---

### Implementation Plan — 3 Phases

#### Phase 1: Live Price Signal + Dynamic Reward (Weeks 1–2)
**Goal:** Replace static tariff with live dynamic price. AI reward updates every 60 seconds.

```
Week 1:
  [ ] Create pricing/ package structure
  [ ] Implement synthetic_spot_generator.py (realistic Egyptian price curves)
  [ ] Implement price_signal_broker.py (sim_spot mode + flat fallback)
  [ ] Implement dynamic_reward_adapter.py (patches RewardFunction at runtime)
  [ ] Add observation dimensions [16] (price_now) to environment.py
  [ ] New Redis channel: pricing.live (60s cadence)
  [ ] New endpoint: GET /api/v1/pricing/live
  [ ] New endpoint: POST /api/v1/pricing/mode
  [ ] Unit test: reward correctly scales with price (2.5 EGP → 1.56× reward vs 1.60 EGP)

Week 2:
  [ ] Implement price_forecaster.py (Prophet model, 24h horizon, 30-min steps)
  [ ] Add observation dimensions [17–31] (forecast curve) to environment.py
  [ ] New Redis channel: pricing.forecast (30-min cadence)
  [ ] New endpoint: GET /api/v1/pricing/forecast
  [ ] Frontend: DynamicPricingPanel.tsx (live price card + forecast chart)
  [ ] Integration test: agent makes anticipatory PRE_PEAK_DROP before peak
  [ ] Retrain scripted policy to use forecast[t+1] for pre-peak detection
```

**Exit criterion:** Agent uses forecast to preemptively act 30 min before peak. Live price visible on dashboard. Revenue uplift +15–20% vs. flat-rate advisory system.

---

#### Phase 2: Demand Response + Revenue Stacking (Weeks 3–4)
**Goal:** Factory participates in DR programs, stacks 4 revenue streams.

```
Week 3:
  [ ] Implement demand_response_controller.py
        - DR event types: CURTAILMENT, INTERRUPTIBLE, FREQUENCY_RESPONSE
        - Net benefit calculator (dr_payment vs production_cost_impact)
        - Accept/decline logic + XAI reason
  [ ] Implement revenue_optimizer.py (4-stream tracker)
  [ ] New Redis channels: pricing.dr_events, dr.response
  [ ] New endpoints: GET /api/v1/pricing/dr/events
                     POST /api/v1/pricing/dr/respond
  [ ] DR events integrated into simulator (random injection, configurable rate)
  [ ] DR event shown in XAIDecisionLog (new entry type)

Week 4:
  [ ] Revenue breakdown KPI cards added to DynamicPricingPanel
  [ ] GET /api/v1/pricing/revenue endpoint
  [ ] DR event injection in Controls.tsx (new crisis type: dr_curtailment)
  [ ] Integration test: accept DR → arc power reduces → DR payment earned → net positive
  [ ] Integration test: decline DR when in BORE_DOWN (unsafe phase)
  [ ] Demo scenario: DR event during peak hour, net benefit calculation shown
```

**Exit criterion:** Full DR accept/decline cycle demonstrated. 4-stream revenue stacking visible. DR payment shown in dashboard. XAI explains every DR decision.

---

#### Phase 3: Heat Schedule Optimizer + Production (Weeks 5–6)
**Goal:** Multi-heat schedule optimization. Full production-grade dynamic pricing.

```
Week 5:
  [ ] Implement load_flexibility_scheduler.py
        - Greedy optimizer (v1, always available)
        - Schedule N heats over 8h horizon using price forecast
        - Output: heat_start_times + cost_estimate
  [ ] New Redis channel: schedule.recommendation
  [ ] New endpoint: GET /api/v1/pricing/schedule
  [ ] New endpoint: POST /api/v1/pricing/schedule/apply
  [ ] Frontend: heat schedule table in DynamicPricingPanel
  [ ] Schedule applied: simulator shifts heat start times accordingly

Week 6:
  [ ] MILP optimizer (scipy/PuLP) as optional alternative to greedy
  [ ] Live EEHC API connector stub (read from config, stubbed response)
  [ ] Pricing mode switch: flat → sim_spot → live_eehc (when available)
  [ ] Full integration test: 24h simulated run with dynamic pricing
        Expected: 2.1× revenue vs. flat-rate advisory system
  [ ] Documentation: dynamic pricing operator guide
  [ ] Stress test: price spikes, DR events, schedule changes — all handled
```

**Exit criterion:** Full 24-hour simulated run with dynamic pricing. Heat schedule optimized. All 4 revenue streams active. Total revenue 2–2.5× flat-rate advisory baseline.

---

### Business Impact: Dynamic Pricing vs. Flat Rate

| System Configuration | Daily Revenue (EGP) | Annual (EGP) | Multiplier |
|---------------------|--------------------:|-------------:|:---------:|
| Flat tariff, no AI (baseline) | 0 | 0 | 1× |
| Current: Flat + Advisory AI (L1) | ~2,340 | ~85M | — |
| DPE Phase 1: Live price + dynamic reward | ~3,600 | ~131M | +54% |
| DPE Phase 2: + Demand Response | ~4,800 | ~175M | +105% |
| DPE Phase 3: + Heat Schedule | ~5,800 | ~212M | +148% |
| Full stack: DPE + ADT (L3) + Forecaster | ~7,200 | ~263M | +208% |

**Dynamic Pricing alone adds +115% to the advisory system's revenue.**  
**Combined with Autonomous Decision Twin, total value reaches 263M EGP/year per furnace.**

---

### Integration with Existing Features

| Feature | Integration Point |
|---------|------------------|
| **Autonomous Decision Twin** | DPE live price feeds into ADT Confidence Engine; DR events trigger ADT execution bus |
| **Reward Function** | `dynamic_reward_adapter.py` patches `RewardFunction.compute()` at runtime — no base file changes |
| **XAI Engine** | 6 new action-reason templates added for DR events and schedule decisions |
| **KPI Calculator** | 4-stream revenue breakdown added to `KPISnapshot` schema |
| **Simulator** | `egypt_grid_pricing.py` replaced by `price_signal_broker.py` subscription |
| **Observation Space** | Grows from 16D to 32D; PPO model must be retrained on new space |

---

## 17. Deployment Guide

```bash
# 1. Clone repository
git clone <repo-url>
cd opti-twin

# 2. Configure environment
cp .env.example .env
# Edit .env if needed (defaults work out of the box)

# 3. Start all services
docker-compose up --build

# Services start in order:
#   redis (5s health check)
#   ai_engine (starts subscribing to factory.telemetry)
#   backend (API ready at :8000)
#   simulator (starts emitting telemetry)
#   frontend (dashboard ready at :3000)

# 4. Access
#   Dashboard:  http://localhost:3000
#   API Docs:   http://localhost:8000/docs
#   API Health: http://localhost:8000/
```

### Service Health Check

```bash
# Check all containers running
docker-compose ps

# Check Redis liveness
docker exec opti-twin-redis redis-cli ping  # → PONG

# Check backend
curl http://localhost:8000/

# Check WebSocket (requires wscat)
wscat -c ws://localhost:8000/ws/live-feed
```

### Stopping & Resetting

```bash
# Stop all services
docker-compose down

# Full reset (wipe all data — Redis ephemeral anyway)
docker-compose down -v
```

---

## 18. Known Limitations & Tech Debt

### Current Limitations

| Issue | Impact | Status |
|-------|--------|--------|
| PPO model trained offline, not during demo | No live RL training shown | Intentional (scripted policy is demo-grade) |
| No real SCADA integration | Simulator only | By design for hackathon |
| Single-machine in demo | Fleet features untested | Architecture ready |
| No data persistence | KPIs reset on restart | Redis is ephemeral |
| WebSocket offline buffer | Events lost when disconnected | Backoff reconnect works |
| No authentication | All endpoints open | Development-appropriate |
| No unit tests | No automated regression guard | Manual e2e via Docker |
| PPO obs space 32D vs. frozen 16D model | PPO model needs retraining | Scripted policy unaffected; retrain with new obs |
| DPE uses synthetic spot prices | Not real EEHC live feed | live_eehc mode stubbed, ready for adapter |

### Intentional Trade-Offs (7-Day Delivery Scope)

- **No semantic search** — planned (upgrade.md); Day-1 slice does lexical + structured filters
- **No preference learning** — reward weights fixed via presets; RLHF on roadmap
- **No anomaly detection** — crisis injection only; autoencoder on roadmap
- **No ML demand forecasting** — DPE uses synthetic spot generator; LSTM/TFT model on roadmap (M2)
- **No CBAM report export** — CO₂ shown in UI; export module on roadmap

### Performance Characteristics

| Metric | Value |
|--------|-------|
| Telemetry ingest latency | ~2 ms (HTTP POST) |
| AI recommendation latency | ~10–15 ms (scripted policy) |
| WebSocket broadcast latency | <50 ms per client |
| KPI aggregation | <1 ms (in-memory) |
| Telemetry payload size | ~9.6 KB/sec per machine |
| Redis memory (1 day) | <500 MB estimated |
| Single-node machine ceiling | ~100 concurrent furnaces (estimated) |

---

*Report generated from full codebase analysis — NextCity AI Hack 2026*  
*Opti-Twin | Mahmoud Emad | mahmoudemad3391@gmail.com | 2026-05-02*
