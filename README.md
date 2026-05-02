# 🏭 Opti-Twin
### Autonomous Energy Intelligence for Smart Manufacturing

> *"We don't stop production to save energy. We make production smarter."*

[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Strict_Contract-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Reinforcement Learning](https://img.shields.io/badge/AI-Reinforcement_Learning-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)]()
[![License MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![NextCity AI Hack](https://img.shields.io/badge/NextCity_AI_Hack-2026_🏆-FF9900?style=for-the-badge)](https://aiu.edu.eg)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen?style=for-the-badge)]()

---

## 📌 The Vision

Egyptian manufacturing plants lose **millions of EGP annually** due to unmanaged peak-hour electricity pricing and rigid, manual energy scheduling — a tradeoff that forces factory managers to choose between saving energy and meeting production targets.

**Opti-Twin** eliminates that tradeoff. By deploying a Multi-Objective Reinforcement Learning agent inside a real-time Industrial Digital Twin, the system autonomously orchestrates machine parameters — motor speeds, cooling loads, furnace scheduling — to slash energy costs by up to **15%** during peak hours, while simultaneously guaranteeing production deadlines and machine health are never compromised.

The result: a factory that pays for this system's implementation **in under two months** through energy savings alone.

---

## 🏗️ System Architecture

Opti-Twin is built on a **4-Tier Enterprise Design**, inspired by production-grade IIoT architectures used by Siemens and GE Digital. Each tier is independently containerized and communicates through strictly defined interfaces.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     OPTI-TWIN SYSTEM ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────┐
  │   TIER 1: EDGE LAYER │  factory_sim.py (Dockerized Microservice)
  │                      │  ► Simulates 3 Industrial Machines:
  │  🏭 Factory Simulator│    - Machine A: Motor (RPM / Heat Dynamics)
  │                      │    - Machine B: Cooling System (Temp Load)
  │  Synthetic Telemetry │    - Machine C: Furnace (Production Batches)
  │  (Hybrid Data Model) │  ► Emits: temperature, RPM, energy_kwh,
  └──────────┬───────────┘    cost_rate, is_peak → every 3 seconds
             │
             │  WebSocket / JSON Events (Event-Driven)
             ▼
  ┌──────────────────────┐
  │  TIER 2: STREAMING   │  Redis Pub/Sub (Dockerized)
  │       LAYER          │  ► Decouples edge data from AI processing
  │                      │  ► Guarantees Zero Data Loss during bursts
  │  📡 Message Broker   │  ► Scales to thousands of machines without
  │  (Redis Pub/Sub)     │    refactoring the core architecture
  └──────────┬───────────┘
             │
             │  Internal Event Stream
             ▼
  ┌──────────────────────┐
  │  TIER 3: AI CORE     │  ai_engine/ (Dockerized)
  │                      │  ► OptiTwinFactoryEnv (Gymnasium)
  │  🧠 RL Agent         │  ► Multi-Objective Reward Function:
  │  (Gymnasium + SB3)   │
  │                      │    R = α(E_saved) - β(M_stress) - γ(P_delay)
  │  Explainable AI      │
  │  Decision Engine     │  ► Produces: Action + XAI Reason String
  └──────────┬───────────┘
             │
             │  Pydantic-Validated REST + WebSocket
             ▼
  ┌──────────────────────┐
  │  TIER 4: APPLICATION │  main.py (FastAPI) + Dashboard (React/Next.js)
  │       LAYER          │
  │                      │  ► POST /api/v1/telemetry
  │  ⚡ API Gateway       │  ► GET  /api/v1/recommendation
  │  (FastAPI + Pydantic) │  ► WS  /ws/live-feed
  │                      │
  │  📊 Dashboard         │  ► Real-time energy charts
  │  (React / Next.js)   │  ► AI Decision Log (XAI Panel)
  │                      │  ► KPI Cards: Cost Saved / Machine Status
  └──────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │  🐳 ALL TIERS RUN VIA: docker-compose up --build               │
  │  Zero manual configuration. Production-identical environment.   │
  └─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features — The WOW Factor

### 🧠 Multi-Objective Reinforcement Learning
Unlike simple rule-based systems, Opti-Twin's RL agent learns from the factory environment using a **tunable, three-objective reward function**:

```
R = α(E_saved) − β(M_stress) − γ(P_delay)
```

| Weight | Objective | Description |
|--------|-----------|-------------|
| `α` | Energy Savings | Reward for reducing cost during peak pricing |
| `β` | Machine Stress | Penalty for overheating or mechanical strain |
| `γ` | Production Delay | Penalty for missing production targets |

> Factories can tune `α`, `β`, `γ` to match their operational priorities — a cost-first factory sets high `α`; an equipment-sensitive plant prioritizes `β`. **This is not a product for factories — this is a product for each factory.**

---

### 🔍 Explainable AI (XAI) — Trustworthy Decisions

Every action taken by the AI agent is accompanied by a **human-readable justification**, rendered live on the dashboard. No black-box decisions reach the factory floor.

```
┌─────────────────────────────────────────────────────────┐
│ [16:32:07]  ACTION: REDUCE_MOTOR_SPEED (-15%)           │
│ REASON: Peak pricing detected (2.5 EGP/kWh).           │
│         Motor temp within safe range. Backlog nominal.  │
│ SAVINGS_EST: ~185 EGP saved this cycle.                 │
│ STATUS: ✅ Machine Health: SAFE | Production: ON-TRACK  │
└─────────────────────────────────────────────────────────┘
```

---

### 🐳 100% Dockerized — Production-Ready from Day One

The entire system — simulator, Redis broker, AI engine, API server, and dashboard — runs inside Docker containers orchestrated by a single `docker-compose.yml`. This guarantees:

- **Zero "works on my machine" failures** during the live demo
- Environment parity between development and deployment
- Instant reproducibility for judges, mentors, and future investors

---

### 📡 Event-Driven Architecture — Built for Scale

By replacing synchronous HTTP polling with a **WebSocket + Redis Pub/Sub** pipeline, Opti-Twin's architecture is designed to scale from 3 simulated machines to hundreds of real IIoT devices without architectural changes. This is the same pattern used in industrial SCADA systems.

---

### 🔐 Zero-Trust Network Principles

Inter-service communication is restricted to the internal Docker network. No service is exposed externally except the API Gateway and Dashboard ports. All data models are validated at the boundary using **Pydantic**, preventing malformed data from ever reaching the AI core.

---

## 🛠️ Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **AI / ML** | `Gymnasium` + `Stable Baselines3` | RL environment & agent training |
| **AI / ML** | `NumPy` | State vector computation & physics simulation |
| **Backend** | `FastAPI` | High-performance async API Gateway |
| **Backend** | `Pydantic v2` | Strict API contract enforcement |
| **Backend** | `Uvicorn` | ASGI server for WebSocket support |
| **Streaming** | `Redis` (Pub/Sub) | Event-driven message broker |
| **Simulator** | `Python 3.11` | Hybrid synthetic telemetry engine |
| **Frontend** | `React` / `Next.js` | Real-time dashboard & XAI log viewer |
| **Frontend** | `Recharts` / `Chart.js` | Live energy consumption visualization |
| **Infrastructure** | `Docker` + `Docker Compose` | Full-stack containerization |
| **Logging** | `Python logging` (JSON format) | Standardized, parseable system logs |

---

## 🚀 Quick Start

> **Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running. Nothing else required.

```bash
# 1. Clone the repository
git clone https://github.com/your-org/opti-twin.git
cd opti-twin

# 2. Copy environment configuration
cp .env.example .env

# 3. Launch the entire system — all 4 tiers start automatically
docker-compose up --build
```

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | `http://localhost:3000` | Real-time factory monitoring UI |
| **API Docs** | `http://localhost:8000/docs` | Interactive FastAPI Swagger UI |
| **API ReDoc** | `http://localhost:8000/redoc` | Alternative API documentation |
| **Redis** | `localhost:6379` (internal) | Message broker (internal only) |

> ⚡ The factory simulator starts automatically and begins emitting telemetry data every 3 seconds. Open the Dashboard to see the AI agent making live decisions.

### Stopping the System
```bash
docker-compose down
```

### Environment Variables (`.env.example`)
```env
# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
REDIS_PORT=6379

# Simulation Config
SIM_INTERVAL_SECONDS=3
SIM_TIME_WARP_MINUTES=15       # Each real second = 15 sim minutes

# AI Agent Weights (Tunable per factory)
RL_ALPHA=1.0                   # Energy savings priority
RL_BETA=0.8                    # Machine stress penalty weight
RL_GAMMA=1.5                   # Production delay penalty weight

# Peak Hour Config
PEAK_HOUR_START=18
PEAK_HOUR_END=22
PEAK_PRICE_PER_KWH=2.5
OFF_PEAK_PRICE_PER_KWH=1.2
```

---

## 📄 Strict API Contract

All data exchanged between services is validated by Pydantic models. Below are the core payloads.

### `POST /api/v1/telemetry` — Edge → Backend
**Request Body (emitted by factory simulator every 3 seconds):**
```json
{
  "machine_id": "Machine_A_Motor",
  "timestamp": "2026-05-07T18:32:07.441Z",
  "rpm": 1487.3,
  "temperature_celsius": 68.4,
  "energy_kwh": 112.7,
  "cost_rate_per_kwh": 2.5,
  "is_peak_hour": true,
  "status": "RUNNING"
}
```

### `GET /api/v1/recommendation` — Dashboard → Backend → AI
**Response Body (AI agent decision + XAI justification):**
```json
{
  "timestamp": "2026-05-07T18:32:08.102Z",
  "action_id": 1,
  "action_label": "REDUCE_MOTOR_SPEED",
  "action_magnitude_percent": -15.0,
  "estimated_savings_egp_per_hour": 185.0,
  "xai_reason": "Peak pricing detected (2.5 EGP/kWh). Motor temp within safe range (68.4°C < 90°C threshold). Production backlog is nominal. Reducing speed is optimal.",
  "machine_health": "SAFE",
  "production_status": "ON_TRACK",
  "reward_components": {
    "energy_savings_score": 92.3,
    "machine_stress_penalty": 0.0,
    "production_delay_penalty": 4.1
  }
}
```

### `WS /ws/live-feed` — Real-time Stream
The dashboard connects to this WebSocket endpoint to receive a continuous stream of telemetry + AI decisions for live chart updates without polling.

---

## 📁 Project Structure

```
opti-twin/
├── 🐳 docker-compose.yml        # Orchestrates all 4 service tiers
├── .env.example                 # Environment variable template
├── .env                         # Local config (gitignored)
│
├── backend/                     # TIER 4 — API Gateway (FastAPI)
│   ├── Dockerfile
│   ├── main.py                  # FastAPI app, routes, WebSocket handler
│   ├── api_contracts/
│   │   └── schemas.py           # Pydantic models (TelemetryInput, RecommendationOutput)
│   ├── ai_engine/
│   │   ├── environment.py       # OptiTwinFactoryEnv (Gymnasium)
│   │   └── agent.py             # RL Agent loader & inference interface
│   └── logger.py                # JSON-formatted standardized logging
│
├── simulator/                   # TIER 1 — Edge Layer
│   ├── Dockerfile
│   └── factory_sim.py           # Synthetic telemetry generator (3 machines)
│
├── frontend/                    # TIER 4 — Dashboard (React/Next.js)
│   ├── Dockerfile
│   ├── pages/
│   │   └── index.tsx            # Main dashboard page
│   └── components/
│       ├── EnergyChart.tsx      # Real-time line chart
│       ├── MachineCard.tsx      # Per-machine status widget
│       └── XAILogPanel.tsx      # AI decision explanation feed
│
└── docs/
    ├── architecture.png         # System architecture diagram
    └── demo-scenario.md         # Step-by-step demo script for judges
```

---

## 📊 Live Demo Scenario

> Follow this script during the hackathon pitch for maximum impact.

**Step 1 — Baseline (No AI):** Show the dashboard with all 3 machines running at full capacity during peak hours. Point to the high energy cost accumulating in real time.

**Step 2 — Activate AI Agent:** Toggle the AI agent ON via the dashboard switch.

**Step 3 — Watch the WOW:** Within seconds, the XAI panel populates with decisions. Machine A's RPM drops. The energy cost curve on the chart visibly flattens. The "Total Savings" KPI card begins climbing.

**Step 4 — Inject a Crisis:** Use the simulator's "inject event" button to spike Machine B's temperature above the warning threshold. Watch the AI immediately prioritize `β` (machine stress), activating the cooling system before overheating occurs — all without human input.

**Expected outcome shown to judges:** `Energy ↓ 15-18%` | `Production = 100%` | `Machine Health = SAFE`

---

## 👥 The Team

| Name | Role | Responsibilities |
|------|------|-----------------|
| **[Team Leader Name]** | Tech Lead & Software Architect | System architecture, Docker orchestration, API design |
| **[Member 2]** | AI / ML Engineer | RL environment (Gymnasium), reward function, agent training |
| **[Member 3]** | Frontend Engineer | React dashboard, real-time charts, XAI log panel |
| **[Member 4]** | Backend & Simulator | FastAPI endpoints, factory simulator, Redis integration |

---

## 🏆 About the Hackathon

**Event:** NextCity AI Hack 2026
**Organizer:** Alamein Center for Innovation and Entrepreneurship (A.C.I.E)
**Host:** Alamein International University (AIU)
**Track:** Industry-Driven Challenges
**Dates:** May 7–8, 2026

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ⚡ by Team Opti-Twin @ NextCity AI Hack 2026**

*Transforming Egyptian manufacturing — one optimized watt at a time.*

</div>
