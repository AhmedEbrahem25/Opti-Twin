<div align="center">

# Opti-Twin

**Autonomous energy intelligence for smart manufacturing.**

A production-grade industrial digital twin for Electric Arc Furnace operations, combining a physics-based simulator, reinforcement learning, dynamic pricing, bilingual explainable AI, and real-time dashboards.

Built for the **NextCity AI Hack 2026**. Reference facility: **Ezz Flat Steel, Ain Sokhna EAF #2** — a 185-tonne furnace.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Pub%2FSub-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Meilisearch](https://img.shields.io/badge/Meilisearch-Search-FF5CAA?logo=meilisearch&logoColor=white)](https://www.meilisearch.com/)
[![PPO](https://img.shields.io/badge/RL-PPO-EE4C2C?logo=pytorch&logoColor=white)](https://stable-baselines3.readthedocs.io/)

[Quick Start](#quick-start) · [Architecture](#architecture) · [API](#api-highlights) · [Demo Flow](#demo-flow) · [Docs](#more-documentation)

</div>

---

## Table of Contents

1. [Overview](#overview)
2. [Capabilities](#capabilities)
3. [Architecture](#architecture)
4. [Quick Start](#quick-start)
5. [Service Topology](#service-topology)
6. [Repository Layout](#repository-layout)
7. [API Highlights](#api-highlights)
8. [Local Frontend Development](#local-frontend-development)
9. [Training Workflow](#training-workflow)
10. [Configuration](#configuration)
11. [Project Status](#project-status)
12. [Demo Flow](#demo-flow)
13. [More Documentation](#more-documentation)

---

## Overview

Opti-Twin pairs a physics-grounded EAF simulator with a reinforcement-learning decision layer to optimise four objectives simultaneously:

| Objective | Lever |
| --- | --- |
| **Energy cost** | Arc-power scheduling against time-of-use & spot pricing |
| **Power factor** | Reactive compensation and tap setpoints |
| **Equipment safety** | Cooling, electrode, transformer, wall-temperature limits |
| **Production throughput** | Heat scheduling against demand-response windows |

Every recommendation is explained in **English and Arabic**, indexed for fast retrieval, and rendered live across two purpose-built dashboards.

---

## Capabilities

- **Telemetry streaming** — physics-based EAF state pushed every few seconds.
- **AI control loop** — arc power, cooling, power factor, and crisis response.
- **Bilingual XAI** — operator-grade explanations in English and Arabic.
- **Dynamic pricing** — flat tariff, time-of-use, synthetic spot, and demand response.
- **KPI tracking** — energy cost, savings, production, safety, revenue.
- **Searchable history** — Meilisearch index over decisions and operational events.
- **Two dashboards** — the original live EAF view and a multi-factory SaaS-style view.

---

## Architecture

```text
                 ┌──────────────┐
                 │  Simulator   │  Physics-grounded EAF telemetry
                 └──────┬───────┘
                        │ pub
                ┌───────▼────────┐
                │     Redis      │  Pub/Sub broker
                └───┬────────┬───┘
                    │        │
              sub   │        │   sub
            ┌───────▼──┐  ┌──▼──────────┐
            │ AI Engine│  │  Backend    │  FastAPI REST + WebSocket
            │  PPO/    │  │  KPIs,      │
            │  Scripted│  │  Pricing,   │
            │  + XAI   │  │  Logs,      │
            │  + Safety│  │  Search     │
            └─────┬────┘  └──┬───────┬──┘
                  │          │       │
                  └────┬─────┘       │
                       │             │
               ┌───────▼─────┐  ┌────▼────────┐
               │ Meilisearch │  │ Dashboards  │
               │  (history)  │  │  3000/3001  │
               └─────────────┘  └─────────────┘
```

The runnable stack lives in [`opti-twin/`](opti-twin/) and is orchestrated by Docker Compose.

> See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the deep-dive.

---

## Quick Start

### Prerequisites

- **Docker Desktop** or Docker Engine with Compose
- *Optional* — Node.js 20+ for frontend-only development
- *Optional* — Python 3.11+ for AI engine development or training

### Run the demo stack

```bash
cd opti-twin
cp .env.example .env
docker compose up --build
```

### Open

| Service | URL |
| --- | --- |
| Original EAF dashboard | <http://localhost:3000> |
| Multi-factory dashboard | <http://localhost:3001> |
| Backend Swagger docs | <http://localhost:8000/docs> |
| Backend health/root | <http://localhost:8000/> |

### Tear down

```bash
docker compose down
```

---

## Service Topology

| Service | Path | Purpose |
| --- | --- | --- |
| `simulator` | `opti-twin/simulator/` | Physics-grounded EAF telemetry, crisis events, tariff context |
| `redis` | Docker image | Pub/Sub broker for telemetry, AI decisions, pricing, and logs |
| `ai_engine` | `opti-twin/ai_engine/` | Gymnasium environment, PPO/scripted policy, safety mask, XAI |
| `backend` | `opti-twin/backend/` | FastAPI gateway, WebSocket feed, KPIs, pricing, logs, search |
| `meilisearch` | Docker image | Search index for decisions and operational events |
| `frontend` | `opti-twin/frontend/` | Original Next.js EAF dashboard — port 3000 |
| `frontend_app` | `frontend-app/` | Multi-factory Next.js dashboard — port 3001 |

---

## Repository Layout

```text
.
├── README.md                 # You are here
├── ARCHITECTURE.md           # Detailed architecture notes
├── plan.md                   # Evidence-backed master plan
├── planing-v2.md             # AI / model roadmap
├── report.md                 # Full project report
├── simulations.md            # Simulation notes
├── upgrade.md                # Search / product upgrade notes
├── frontend-app/             # Multi-factory Next.js dashboard
└── opti-twin/
    ├── docker-compose.yml    # Full-stack orchestration
    ├── .env.example          # Runtime configuration template
    ├── README.md             # Stack-specific quick start & training commands
    ├── JUDGES_BRIEF.md       # Demo / pitch reference
    ├── ai_engine/            # RL, forecasting, anomaly, reward, XAI
    ├── backend/              # FastAPI, pricing, search, KPI services
    ├── data/                 # Tariffs, model/data artifacts, Meili data
    ├── frontend/             # Original dashboard
    └── simulator/            # EAF simulator
```

---

## API Highlights

The backend exposes a REST surface plus a live WebSocket stream. Full Swagger UI at <http://localhost:8000/docs>.

<details open>
<summary><b>Telemetry & Recommendations</b></summary>

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Backend service metadata |
| `POST` | `/api/v1/telemetry` | Ingest simulator telemetry |
| `GET` | `/api/v1/recommendation` | Last AI recommendation |
| `GET` | `/api/v1/stats` | KPI snapshot |
| `WS`  | `/ws/live-feed` | Real-time telemetry & recommendation stream |

</details>

<details open>
<summary><b>AI Control</b></summary>

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/ai/toggle` | Enable or disable AI control |
| `POST` | `/api/v1/ai/profile` | Switch reward profile |
| `POST` | `/api/v1/sim/inject` | Inject simulator crisis event |

</details>

<details open>
<summary><b>Pricing & Demand Response</b></summary>

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/tariff/mode` | Toggle tariff mode |
| `GET`  | `/api/v1/pricing/live` | Current price signal |
| `GET`  | `/api/v1/pricing/forecast` | Forecast price curve |
| `GET`  | `/api/v1/pricing/revenue` | Revenue stack snapshot |
| `GET`  | `/api/v1/pricing/schedule` | Heat schedule recommendation |
| `POST` | `/api/v1/pricing/dr/inject` | Inject a demand-response event |
| `GET`  | `/api/v1/pricing/dr/events` | Demand-response event history |

</details>

<details open>
<summary><b>Logs & Search</b></summary>

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/logs` | Query in-memory logs |
| `GET` | `/api/v1/search` | Search indexed operational events |

</details>

---

## Local Frontend Development

### Multi-factory dashboard (port 3001)

```bash
cd frontend-app
cp .env.local.example .env.local
npm install
npm run dev
```

Default environment:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/live-feed
```

### Original dashboard (port 3000)

```bash
cd opti-twin/frontend
npm install
npm run dev
```

---

## Training Workflow

The training container is gated behind a Compose profile so demos do not start long ML jobs.

```bash
cd opti-twin
docker compose --profile training run --rm trainer train_ppo.py --help
```

The full **collect → split → train → evaluate** sequence lives in [`opti-twin/README.md`](opti-twin/README.md).

---

## Configuration

Copy `opti-twin/.env.example` to `opti-twin/.env` and tune as needed. Key groups:

| Group | Keys |
| --- | --- |
| Infrastructure | Redis & service host settings |
| Physical model | EAF physical limits and furnace sizing |
| Tariff | Egypt industrial tariff assumptions |
| RL reward | `RL_ALPHA` … `RL_ZETA` |
| Pricing engine | `DPE_*` |
| Search | `SEARCH_ENABLED`, `MEILI_MASTER_KEY` |
| Optional LLM XAI | `ANTHROPIC_API_KEY` |

> Defaults are tuned so the demo runs locally without external services.

---

## Project Status

### Built & runnable

- Dockerized simulator, Redis, backend, AI engine, Meilisearch, and dashboards
- Live telemetry and WebSocket updates
- Scripted demo policy with reward-profile hooks
- Safety masking and crisis response
- Dynamic pricing and demand-response demo flows
- Search routes and saved-search UX
- Training pipeline scaffolding and model artifact folders

### Caveats

- The demo can fall back to a scripted policy when trained PPO weights are absent or not selected.
- The simulator is not a real SCADA connection.
- Dynamic spot pricing is synthetic unless a real market connector is added.
- Data persistence is demo-oriented — review storage settings before production deployment.

---

## Demo Flow

| Step | Action |
| ---: | --- |
| 1 | `docker compose up --build` |
| 2 | Open <http://localhost:3000> or <http://localhost:3001> |
| 3 | Watch baseline furnace telemetry and KPIs |
| 4 | Enable the AI control flow |
| 5 | Toggle tariff or pricing scenarios |
| 6 | Inject a crisis (wall overheat, grid spike, transformer alarm) |
| 7 | Search decisions, crises, and safety events |
| 8 | Close with the KPI and revenue summary |

---

## More Documentation

| Document | Purpose |
| --- | --- |
| [`report.md`](report.md) | Full project report |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Detailed technical architecture |
| [`opti-twin/JUDGES_BRIEF.md`](opti-twin/JUDGES_BRIEF.md) | Hackathon demo script & Q&A |
| [`plan.md`](plan.md) | Evidence-backed business and implementation plan |
| [`planing-v2.md`](planing-v2.md) | Model roadmap |
| [`upgrade.md`](upgrade.md) | Search / product upgrade notes |
| [`simulations.md`](simulations.md) | Simulation notes |

---

<div align="center">

**Opti-Twin** — built for **NextCity AI Hack 2026**.

</div>
