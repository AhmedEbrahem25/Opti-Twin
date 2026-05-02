# Opti-Twin

Autonomous Energy Intelligence for Smart Manufacturing — NextCity AI Hack 2026.

See `../plan.md` for the full evidence-backed master plan.

## Quick Start

```bash
cp .env.example .env
docker-compose up --build
```

Then open:
- Dashboard: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

## Architecture (4 tiers)

```
simulator (edge) → redis (broker) → ai_engine (RL+XAI) → backend (FastAPI) → frontend (Next.js)
```

## Modeled facility

Ezz Flat Steel — Ain Sokhna EAF #2 (185-tonne Danieli, 1.6 Mtpa, started 2023).
Source: Global Energy Monitor.

## Egyptian tariff (verified)

UHV 220-132 kV: **1.60 EGP/kWh** flat (EgyptERA, August 2024).
No published time-of-use for industrial UHV. Power-factor penalty applies for loads >500 kW below 0.92.
