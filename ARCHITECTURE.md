# 🏭 Opti-Twin — System Architecture & Project Layout

> **Version:** 1.0.0 | **Event:** NextCity AI Hack 2026 | **Track:** Industry-Driven Challenges

---

## 📐 System Architecture Overview

Opti-Twin is built on a **4-Tier Enterprise Architecture**, inspired by production-grade IIoT systems used by Siemens and GE Digital. Each tier is independently containerized and communicates through strictly defined interfaces.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    OPTI-TWIN — ENTERPRISE ARCHITECTURE                       ║
║              NextCity AI Hack 2026 | Alamein International University        ║
╚══════════════════════════════════════════════════════════════════════════════╝

 ┌──────────────────────────────────────────────────────────────────────────┐
 │  TIER 1 ─ EDGE LAYER (Data Source)                                       │
 │                                                                          │
 │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐        │
 │  │  Machine A      │   │  Machine B      │   │  Machine C      │        │
 │  │  Motor          │   │  Cooling System │   │  Furnace        │        │
 │  │─────────────────│   │─────────────────│   │─────────────────│        │
 │  │ • RPM           │   │ • Temp Load     │   │ • Batch Size    │        │
 │  │ • Temperature   │   │ • Cooling Power │   │ • Cycle Time    │        │
 │  │ • Energy (kWh)  │   │ • Energy (kWh)  │   │ • Energy (kWh)  │        │
 │  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘        │
 │           └──────────────────┬──┘                     │                 │
 │                              ▼                         │                 │
 │              ┌──────────────────────────┐              │                 │
 │              │   factory_sim.py         │◄─────────────┘                 │
 │              │   Hybrid Simulation      │                                │
 │              │   Engine (Docker)        │                                │
 │              └──────────────┬───────────┘                                │
 └─────────────────────────────│──────────────────────────────────────────┘
                               │
                  WebSocket / JSON Events (Event-Driven)
                  Every 3 seconds → {machine_id, rpm,
                  temperature, energy_kwh, is_peak, ...}
                               │
 ┌─────────────────────────────▼──────────────────────────────────────────┐
 │  TIER 2 ─ STREAMING LAYER (Message Broker)                              │
 │                                                                          │
 │              ┌──────────────────────────┐                               │
 │              │   Redis Pub/Sub          │                               │
 │              │   (Dockerized)           │                               │
 │              │─────────────────────────│                               │
 │              │ ✔ Zero Data Loss         │                               │
 │              │ ✔ Decouples Edge from AI │                               │
 │              │ ✔ Scales to 1000+ nodes  │                               │
 │              └──────────────┬───────────┘                               │
 └─────────────────────────────│──────────────────────────────────────────┘
                               │
                  Internal Event Stream (channel: factory.telemetry)
                               │
 ┌─────────────────────────────▼──────────────────────────────────────────┐
 │  TIER 3 ─ AI CORE (The Brain)                                            │
 │                                                                          │
 │   ┌──────────────────────────────────────────────────────────────────┐  │
 │   │   OptiTwinFactoryEnv  (Gymnasium)                                │  │
 │   │                                                                  │  │
 │   │   State Vector:  [price, motor_temp, furnace_temp, backlog]      │  │
 │   │                                                                  │  │
 │   │   Action Space:  [motor_speed Δ, cooling_power, furnace_run]     │  │
 │   │                                                                  │  │
 │   │   Reward:   R = α(E_saved) − β(M_stress) − γ(P_delay)           │  │
 │   │             ↑ tunable per factory's operational priorities       │  │
 │   │                                                                  │  │
 │   │   Output:   { action_label, magnitude, xai_reason, savings_est} │  │
 │   └──────────────────────────────────────────────────────────────────┘  │
 │                                                                          │
 │   ┌─────────────────────┐    ┌─────────────────────────────────────┐    │
 │   │  RL Agent           │    │  XAI Engine                         │    │
 │   │  (Stable Baselines3)│    │  Generates human-readable reason    │    │
 │   │  PPO Algorithm      │    │  for every AI decision taken        │    │
 │   └─────────────────────┘    └─────────────────────────────────────┘    │
 └─────────────────────────────│──────────────────────────────────────────┘
                               │
             Pydantic-Validated REST + WebSocket responses
                               │
 ┌─────────────────────────────▼──────────────────────────────────────────┐
 │  TIER 4 ─ APPLICATION LAYER (API Gateway + Dashboard)                   │
 │                                                                          │
 │  ┌───────────────────────────────┐   ┌────────────────────────────────┐ │
 │  │  FastAPI Gateway              │   │  React / Next.js Dashboard     │ │
 │  │  (Strict API Contracts)       │   │                                │ │
 │  │───────────────────────────────│   │  ┌──────────────────────────┐ │ │
 │  │ POST /api/v1/telemetry        │   │  │  ⚡ Energy Chart (Live)  │ │ │
 │  │ GET  /api/v1/recommendation   │   │  │  🏭 Machine Status Cards │ │ │
 │  │ WS   /ws/live-feed            │   │  │  🧠 XAI Decision Log     │ │ │
 │  │                               │   │  │  💰 KPI: Cost Saved      │ │ │
 │  │ Pydantic Schemas:             │   │  └──────────────────────────┘ │ │
 │  │  TelemetryInput               │   │                                │ │
 │  │  RecommendationOutput         │   │  localhost:3000                │ │
 │  │  XAILogEntry                  │   └────────────────────────────────┘ │
 │  │                               │                                      │
 │  │  localhost:8000/docs          │                                      │
 │  └───────────────────────────────┘                                      │
 └──────────────────────────────────────────────────────────────────────────┘

 ╔══════════════════════════════════════════════════════════════════════════╗
 ║  🐳  ALL FOUR TIERS LAUNCHED WITH:  docker-compose up --build           ║
 ║       Zero manual configuration. Production-identical environment.       ║
 ╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 🧠 AI Core Deep Dive — The Reward Function

The heart of Opti-Twin is a **Multi-Objective Reinforcement Learning** agent that balances three competing priorities simultaneously:

```
╔══════════════════════════════════════════════════════════════╗
║           MULTI-OBJECTIVE REWARD FUNCTION                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   R = α · (E_saved)  −  β · (M_stress)  −  γ · (P_delay)   ║
║                                                              ║
╠══════════════╦═══════════════════╦══════════════════════════╣
║  Variable    ║  Objective        ║  Business Meaning         ║
╠══════════════╬═══════════════════╬══════════════════════════╣
║  α (alpha)   ║  Energy Savings   ║  Reward for cutting       ║
║  default=1.0 ║  (E_saved)        ║  peak-hour costs          ║
╠══════════════╬═══════════════════╬══════════════════════════╣
║  β (beta)    ║  Machine Stress   ║  Penalty for overheating  ║
║  default=0.8 ║  (M_stress)       ║  or mechanical strain     ║
╠══════════════╬═══════════════════╬══════════════════════════╣
║  γ (gamma)   ║  Production Delay ║  Penalty for missing      ║
║  default=1.5 ║  (P_delay)        ║  production deadlines     ║
╚══════════════╩═══════════════════╩══════════════════════════╝

  ► Cost-first factory    →  set  α=2.0, β=0.5, γ=1.0
  ► Equipment-sensitive   →  set  α=0.8, β=2.0, γ=1.0
  ► Production-critical   →  set  α=0.8, β=0.8, γ=2.5
```

---

## 🔁 Data Flow & API Contract

```
┌──────────────────────────────────────────────────────────────┐
│                    DATA FLOW DIAGRAM                         │
└──────────────────────────────────────────────────────────────┘

  [factory_sim.py]  ──POST /api/v1/telemetry──►  [FastAPI]
                                                      │
         Payload (every 3s):                          ▼
         {                                    [Redis Pub/Sub]
           "machine_id": "Machine_A_Motor",           │
           "timestamp":  "2026-05-07T18:32:07Z",      ▼
           "rpm":         1487.3,             [RL Agent reads
           "temperature":   68.4,              current state]
           "energy_kwh":   112.7,                     │
           "cost_rate":      2.5,                     ▼
           "is_peak":       true,             [Computes action
           "status":    "RUNNING"              + XAI reason]
         }                                            │
                                                      ▼
  [Dashboard]  ◄──WS /ws/live-feed──────  [FastAPI broadcasts]

         Recommendation Payload:
         {
           "action_label":     "REDUCE_MOTOR_SPEED",
           "magnitude_pct":    -15.0,
           "savings_egp_hr":   185.0,
           "xai_reason":       "Peak pricing (2.5 EGP/kWh).
                                Motor temp safe (68°C < 90°C).
                                Backlog nominal. Optimal to reduce.",
           "machine_health":   "SAFE",
           "production_status":"ON_TRACK",
           "reward_components": {
             "energy_savings_score": 92.3,
             "machine_stress_penalty": 0.0,
             "production_delay_penalty": 4.1
           }
         }
```

---

## 📁 Project Layout (Directory Structure)

```
opti-twin/
│
├── 🐳 docker-compose.yml          # Orchestrates all 4 service tiers
├── .env.example                   # Environment variable template
├── .env                           # Local config (git-ignored)
├── README.md                      # Project overview & quick start
├── ARCHITECTURE.md                # This file — full system design
│
│
├── ─────────────────────────────────────────────────────────────
│   TIER 1 — Edge Layer (Factory Simulator)
├── ─────────────────────────────────────────────────────────────
│
├── simulator/
│   ├── Dockerfile
│   ├── requirements.txt           # numpy, requests, websockets
│   └── factory_sim.py             # Synthetic telemetry generator
│       │                          # Simulates 3 machines with
│       │                          # realistic physics (heat/RPM)
│       │                          # and peak-hour pricing model
│       │
│       ├── generate_machine_data()    # Core physics simulation
│       ├── inject_crisis_event()      # For WOW demo moment
│       └── run_simulation()           # Main loop with time-warp
│
│
├── ─────────────────────────────────────────────────────────────
│   TIER 3 — AI Core (RL Engine)
├── ─────────────────────────────────────────────────────────────
│
├── ai_engine/
│   ├── Dockerfile
│   ├── requirements.txt           # gymnasium, stable-baselines3, numpy
│   ├── environment.py             # OptiTwinFactoryEnv (Gymnasium)
│   │   ├── __init__()             # Defines action/observation spaces
│   │   ├── step()                 # Physics + reward calculation
│   │   ├── reset()                # Episode reset
│   │   └── _generate_xai_reason() # XAI string builder
│   │
│   ├── agent.py                   # RL Agent wrapper
│   │   ├── load_model()           # Loads pre-trained PPO model
│   │   ├── predict()              # Returns action given state
│   │   └── get_recommendation()   # Full decision payload
│   │
│   └── models/
│       └── opti_twin_ppo.zip      # Pre-trained model (committed for demo)
│
│
├── ─────────────────────────────────────────────────────────────
│   TIER 4 — Application Layer (API Gateway)
├── ─────────────────────────────────────────────────────────────
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt           # fastapi, uvicorn, pydantic, redis
│   ├── main.py                    # FastAPI app entry point
│   │   ├── POST /api/v1/telemetry     # Receives edge data
│   │   ├── GET  /api/v1/recommendation # Returns AI decision
│   │   ├── GET  /api/v1/stats         # Aggregated KPIs
│   │   └── WS   /ws/live-feed         # Real-time dashboard stream
│   │
│   ├── api_contracts/
│   │   └── schemas.py             # All Pydantic models (Single Source of Truth)
│   │       ├── TelemetryInput         # Validates edge data in
│   │       ├── RecommendationOutput   # Validates AI response out
│   │       ├── XAILogEntry            # Dashboard log entry
│   │       └── KPISnapshot            # Aggregated metrics payload
│   │
│   ├── services/
│   │   ├── redis_client.py        # Redis Pub/Sub connection
│   │   ├── ai_service.py          # Calls ai_engine, formats response
│   │   └── stats_service.py       # Computes running KPIs (savings etc.)
│   │
│   └── logger.py                  # JSON-formatted standardized logging
│                                  # Every decision logged:
│                                  # {ts, action, reason, savings_est}
│
│
├── ─────────────────────────────────────────────────────────────
│   TIER 4 — Application Layer (Dashboard)
├── ─────────────────────────────────────────────────────────────
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── pages/
│   │   └── index.tsx              # Main dashboard page
│   │
│   └── components/
│       ├── EnergyChart.tsx        # Real-time Recharts line chart
│       │                          # Shows energy_kwh over time
│       │                          # Highlights peak hours in red
│       │
│       ├── MachineCard.tsx        # Per-machine status widget
│       │                          # Shows: RPM, Temp, Health badge
│       │
│       ├── XAILogPanel.tsx        # Live AI decision feed
│       │                          # Displays: action + reason + savings
│       │
│       ├── KPIBanner.tsx          # Top-row KPI cards
│       │                          # "Total Saved Today: 1,240 EGP"
│       │
│       └── AIToggle.tsx           # ON/OFF switch for AI Agent
│                                  # (The WOW moment trigger in demo)
│
│
└── ─────────────────────────────────────────────────────────────
    docs/
    ├── ARCHITECTURE.md            # This file
    ├── demo-scenario.md           # Step-by-step live demo script
    ├── pitch-deck.pdf             # Hackathon presentation slides
    └── diagrams/
        ├── system-architecture.png
        └── reward-function.png
```

---

## 🐳 Docker Compose Map

```
docker-compose.yml orchestrates 4 services on an internal bridge network:

  ┌─────────────────┐     ┌─────────────────┐
  │   simulator     │     │   ai_engine     │
  │   (Port: none)  │     │   (Port: none)  │
  │   Depends on:   │     │   Depends on:   │
  │   → backend     │     │   → redis       │
  └────────┬────────┘     └────────┬────────┘
           │                       │
           │   opti-twin-network   │
           │    (bridge, internal) │
           ▼                       ▼
  ┌─────────────────┐     ┌─────────────────┐
  │   backend       │     │   redis         │
  │   Port: 8000    │◄────│   Port: 6379    │
  │   FastAPI       │     │   (internal)    │
  └────────┬────────┘     └─────────────────┘
           │
           ▼
  ┌─────────────────┐
  │   frontend      │
  │   Port: 3000    │
  │   Next.js       │
  └─────────────────┘

  Startup order (via depends_on):
  redis  →  ai_engine  →  backend  →  simulator  →  frontend
```

---

## ⚙️ Environment Variables Reference

```
# ═══════════════════════════════════════════════
# .env.example — Opti-Twin Configuration
# ═══════════════════════════════════════════════

# Service Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
REDIS_PORT=6379

# Simulation Config
SIM_INTERVAL_SECONDS=3         # How often machines emit data
SIM_TIME_WARP_MINUTES=15       # 1 real second = 15 sim minutes
SIM_START_HOUR=16              # Start at 4 PM (approaching peak)

# Peak Hour Config
PEAK_HOUR_START=18
PEAK_HOUR_END=22
PEAK_PRICE_PER_KWH=2.5         # EGP/kWh during peak
OFF_PEAK_PRICE_PER_KWH=1.2     # EGP/kWh outside peak

# AI Agent Weights (Tunable per factory strategy)
RL_ALPHA=1.0                   # Energy savings priority
RL_BETA=0.8                    # Machine stress penalty
RL_GAMMA=1.5                   # Production delay penalty

# Machine Thresholds
MOTOR_MAX_TEMP_CELSIUS=90
FURNACE_MIN_BATCH_SIZE=10
COOLING_RESPONSE_RATE=0.8
```

---

## 🎬 Live Demo Scenario (For Hackathon Judges)

```
┌──────────────────────────────────────────────────────────────┐
│                   DEMO SCRIPT — 3 MINUTES                    │
└──────────────────────────────────────────────────────────────┘

  STEP 1 — Baseline (0:00 – 0:45)
  ─────────────────────────────────
  ► Show dashboard: 3 machines running at full capacity
  ► Clock shows 17:45 (approaching peak hour)
  ► Point to energy cost accumulating — "this is the problem"
  ► KPI: "Current cost rate: 1.2 EGP/kWh"

  STEP 2 — Peak Hour Hits (0:45 – 1:15)
  ──────────────────────────────────────
  ► Time-warp kicks clock to 18:00
  ► Cost rate jumps to 2.5 EGP/kWh on the chart
  ► Energy bill counter spikes visibly
  ► "Without AI — the factory is bleeding money right now"

  STEP 3 — Activate AI Agent (1:15 – 2:00)
  ──────────────────────────────────────────
  ► Toggle AI switch ON on the dashboard
  ► XAI Log panel populates instantly:
      [18:00:03] ACTION: REDUCE_MOTOR_SPEED (-15%)
                 REASON: Peak pricing (2.5 EGP/kWh).
                 SAVINGS_EST: ~185 EGP/hr
  ► Energy chart curve visibly flattens
  ► "Total Saved Today" KPI card begins climbing

  STEP 4 — Inject Crisis (2:00 – 2:30)
  ──────────────────────────────────────
  ► Press "Inject Overheat Event" on simulator panel
  ► Machine B temperature spikes above 85°C
  ► XAI Log:
      [18:02:11] ACTION: INCREASE_COOLING_POWER (+80%)
                 REASON: Motor stress detected (87°C > 85°C
                 threshold). β-weight override activated.
                 Machine health prioritized.
  ► Temperature drops back to safe range

  RESULT SHOWN TO JUDGES:
  ┌──────────────────────────────────────┐
  │  ⚡ Energy Cost    ↓ 18%             │
  │  🏭 Production     = 100% (ON TRACK) │
  │  🌡️  Machine Health = SAFE           │
  │  💰  Savings Today = 2,340 EGP      │
  └──────────────────────────────────────┘
```

---

## 👥 Team Roles & Responsibilities

| Role | Responsibility | Owns |
|------|----------------|------|
| **Tech Lead / Architect** | System design, Docker setup, API contracts | `docker-compose.yml`, `backend/main.py`, `schemas.py` |
| **AI / ML Engineer** | RL environment, reward function, pre-train model | `ai_engine/environment.py`, `ai_engine/agent.py` |
| **Frontend Engineer** | Dashboard UI, live charts, XAI log panel | `frontend/components/` |
| **Backend / Simulator** | FastAPI endpoints, factory simulator | `simulator/factory_sim.py`, `backend/services/` |

---

## 🏆 Why This Architecture Wins

```
  Traditional Approach       vs.      Opti-Twin Approach
  ──────────────────                  ──────────────────
  ❌ HTTP polling (slow)              ✅ WebSocket + Event-Driven
  ❌ Single monolith                  ✅ Independent microservices
  ❌ No explainability                ✅ XAI on every decision
  ❌ Fixed rules                      ✅ Learns and adapts (RL)
  ❌ Manual tuning                    ✅ Configurable α, β, γ weights
  ❌ "Works on my machine"            ✅ 100% Dockerized
  ❌ Static dashboard                 ✅ Real-time live feed
```

---

*Built with ⚡ by Team Opti-Twin — NextCity AI Hack 2026*
*Transforming Egyptian manufacturing, one optimized watt at a time.*
