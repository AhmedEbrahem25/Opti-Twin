# Opti-Twin

Autonomous energy intelligence for smart manufacturing, built for the
NextCity AI Hack 2026.

Opti-Twin is an industrial digital twin for Electric Arc Furnace (EAF)
operations. It combines a physics-based factory simulator, a reinforcement
learning decision layer, dynamic pricing controls, bilingual explainable AI,
searchable decision history, and real-time dashboards.

The demo target is Ezz Flat Steel, Ain Sokhna EAF #2: a 185-tonne furnace used
as the reference facility for energy-cost, power-factor, equipment-safety, and
production-throughput scenarios.

## What It Does

- Streams simulated EAF telemetry every few seconds.
- Runs AI recommendations for arc power, cooling, power factor, and crisis
  response.
- Explains decisions in operator-friendly English and Arabic.
- Models flat tariff, time-of-use, synthetic spot pricing, and demand response.
- Tracks KPIs for energy cost, savings, production, safety, and revenue.
- Indexes operational events for fast search and saved-search workflows.
- Ships with two dashboards: the original live EAF dashboard and a newer
  multi-factory SaaS-style dashboard.

## Architecture

```text
simulator -> redis -> ai_engine -> backend -> dashboards
                |          |          |
                |          |          +-- FastAPI REST + WebSocket
                |          +------------- PPO/scripted policy + XAI + safety
                +------------------------ Pub/Sub event stream

meilisearch <--------------------------- searchable decision/event history
```

The main runnable stack lives in `opti-twin/` and is orchestrated with Docker
Compose.

## Quick Start

Prerequisites:

- Docker Desktop or Docker Engine with Compose
- Optional for frontend-only development: Node.js 20+
- Optional for Python development/training: Python 3.11+

Run the full demo stack:

```bash
cd opti-twin
cp .env.example .env
docker compose up --build
```

Open:

| Service | URL |
| --- | --- |
| Original EAF dashboard | http://localhost:3000 |
| New multi-factory dashboard | http://localhost:3001 |
| Backend API docs | http://localhost:8000/docs |
| Backend health/root | http://localhost:8000/ |

Stop the stack:

```bash
docker compose down
```

## Main Services

| Service | Path | Purpose |
| --- | --- | --- |
| `simulator` | `opti-twin/simulator/` | Physics-grounded EAF telemetry, crisis events, tariff context |
| `redis` | Docker image | Pub/Sub broker for telemetry, AI decisions, pricing, and logs |
| `ai_engine` | `opti-twin/ai_engine/` | Gymnasium environment, PPO/scripted policy, safety mask, XAI |
| `backend` | `opti-twin/backend/` | FastAPI gateway, WebSocket feed, KPIs, pricing, logs, search routes |
| `meilisearch` | Docker image | Internal search index for decisions and operational events |
| `frontend` | `opti-twin/frontend/` | Original Next.js EAF dashboard on port 3000 |
| `frontend_app` | `frontend-app/` | New Next.js multi-factory dashboard on port 3001 |

## Repository Layout

```text
.
|-- README.md                 # This file
|-- ARCHITECTURE.md           # Detailed architecture notes
|-- plan.md                   # Evidence-backed master plan
|-- planing-v2.md             # AI/model roadmap
|-- report.md                 # Full project report
|-- simulations.md            # Simulation notes
|-- upgrade.md                # Search/product upgrade notes
|-- frontend-app/             # New Next.js app
`-- opti-twin/
    |-- docker-compose.yml    # Full stack orchestration
    |-- .env.example          # Runtime configuration template
    |-- README.md             # Stack-specific quick start and training commands
    |-- JUDGES_BRIEF.md       # Demo/pitch reference
    |-- GUIDE_AR.md           # Arabic operator/project guide
    |-- HOW_AI_WORKS_AR.md    # Arabic AI explainer
    |-- ai_engine/            # RL, forecasting, anomaly, reward, XAI
    |-- backend/              # FastAPI, pricing, search, KPI services
    |-- data/                 # Tariffs, model/data artifacts, Meili data
    |-- frontend/             # Original dashboard
    `-- simulator/            # EAF simulator
```

## API Highlights

The backend exposes REST endpoints and a live WebSocket stream:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Backend service metadata |
| `POST` | `/api/v1/telemetry` | Ingest simulator telemetry |
| `GET` | `/api/v1/recommendation` | Last AI recommendation |
| `GET` | `/api/v1/stats` | KPI snapshot |
| `POST` | `/api/v1/ai/toggle` | Enable or disable AI control |
| `POST` | `/api/v1/ai/profile` | Switch reward profile |
| `POST` | `/api/v1/sim/inject` | Inject simulator crisis event |
| `POST` | `/api/v1/tariff/mode` | Toggle tariff mode |
| `GET` | `/api/v1/pricing/live` | Current price signal |
| `GET` | `/api/v1/pricing/forecast` | Forecast price curve |
| `GET` | `/api/v1/pricing/revenue` | Revenue stack snapshot |
| `GET` | `/api/v1/pricing/schedule` | Heat schedule recommendation |
| `POST` | `/api/v1/pricing/dr/inject` | Inject a demand-response event |
| `GET` | `/api/v1/pricing/dr/events` | Demand-response event history |
| `GET` | `/api/v1/logs` | Query in-memory logs |
| `GET` | `/api/v1/search` | Search indexed operational events |
| `WS` | `/ws/live-feed` | Real-time telemetry and recommendation stream |

Swagger UI is available at `http://localhost:8000/docs` after the stack starts.

## Local Frontend Development

Run the new dashboard directly:

```bash
cd frontend-app
cp .env.local.example .env.local
npm install
npm run dev
```

By default, this app expects:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/live-feed
```

Run the original dashboard directly:

```bash
cd opti-twin/frontend
npm install
npm run dev
```

## Training Workflow

The training container is gated behind a Compose profile so normal demos do not
start long ML jobs.

Example:

```bash
cd opti-twin
docker compose --profile training run --rm trainer train_ppo.py --help
```

The stack-specific `opti-twin/README.md` contains the full collect, split,
train, and evaluate command sequence.

## Configuration

Copy `opti-twin/.env.example` to `opti-twin/.env` and adjust values as needed.
Important groups include:

- Redis and service host settings
- EAF physical limits and furnace sizing
- Egypt industrial tariff assumptions
- RL reward weights: `RL_ALPHA` through `RL_ZETA`
- Dynamic Pricing Engine settings: `DPE_*`
- Search settings: `SEARCH_ENABLED`, `MEILI_MASTER_KEY`
- Optional LLM XAI setting: `ANTHROPIC_API_KEY`

Defaults are chosen so the demo runs locally without external services.

## Project Status

Built and runnable:

- Dockerized simulator, Redis, backend, AI engine, Meilisearch, and dashboards
- Live telemetry and WebSocket updates
- Scripted demo policy with reward-profile hooks
- Safety masking and crisis response
- Dynamic pricing and demand-response demo flows
- Search routes and saved-search UX
- Training pipeline scaffolding and model artifact folders

Important caveats:

- The demo can fall back to a scripted decision policy when trained PPO weights
  are absent or not selected.
- The simulator is not a real SCADA connection.
- Dynamic spot pricing is synthetic unless a real market connector is added.
- Data persistence is demo-oriented; check storage settings before production
  deployment.

## Demo Flow

1. Start the stack with `docker compose up --build`.
2. Open `http://localhost:3000` or `http://localhost:3001`.
3. Watch baseline furnace telemetry and KPIs.
4. Enable the AI control flow.
5. Toggle tariff or pricing scenarios.
6. Inject a crisis such as wall overheat, grid spike, or transformer alarm.
7. Use search to find decisions, crises, and safety events.
8. Close with the KPI and revenue summary.

## More Documentation

- `report.md` - full project report
- `ARCHITECTURE.md` - detailed technical architecture
- `opti-twin/JUDGES_BRIEF.md` - hackathon demo script and Q&A
- `plan.md` - evidence-backed business and implementation plan
- `planing-v2.md` - model roadmap
- `upgrade.md` - search/product upgrade notes
- `opti-twin/GUIDE_AR.md` - Arabic project guide
- `opti-twin/HOW_AI_WORKS_AR.md` - Arabic AI explanation
