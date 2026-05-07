# Opti-Twin

Autonomous Energy Intelligence for Smart Manufacturing — NextCity AI Hack 2026.

See `../plan.md` for the full evidence-backed master plan.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Then open:
- Dashboard: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

## Training (one-shot, behind a profile)

The `trainer` service is gated behind `--profile training` so a normal
`docker compose up` does not trigger a long ML run. Entrypoint is `python -u`,
so the command argument is the script path. End-to-end pipeline:

```bash
# 1. Collect rollouts
docker compose --profile training run --rm trainer collect_episodes.py \
  --n-episodes 200 --difficulty medium --seed 1000
docker compose --profile training run --rm trainer collect_episodes.py \
  --n-episodes 100 --difficulty hard   --seed 5000

# 2. Featurise + split
docker compose --profile training run --rm trainer -m data_pipeline.split

# 3. Train M2/M3
docker compose --profile training run --rm trainer train_anomaly.py
docker compose --profile training run --rm trainer train_forecaster.py

# 4. Train M4 (BC) at 39-D
docker compose --profile training run --rm trainer train_bc.py \
  --forecaster models/forecaster/v0.1.0 \
  --anomaly   models/anomaly/v0.1.0 \
  --out       models/bc/v0.2.0/bc_init.pt

# 5. Train M5 (preference reward model)
docker compose --profile training run --rm trainer train_reward.py

# 6. Optuna + final PPO build
docker compose --profile training run --rm trainer train_ppo.py \
  --bc-init    models/bc/v0.2.0/bc_init.pt \
  --forecaster models/forecaster/v0.1.0 \
  --anomaly    models/anomaly/v0.1.0 \
  --tune --tune-trials 6 --tune-budget 30000 \
  --total-timesteps 300000 \
  --output     models/ppo/v1.0.0_demo/opti_twin_ppo.zip

# 7. Eval
docker compose --profile training run --rm trainer -m eval.benchmarks \
  --model models/ppo/v1.0.0_demo/opti_twin_ppo.zip
docker compose --profile training run --rm trainer -m eval.latency \
  --model models/ppo/v1.0.0_demo/opti_twin_ppo.zip
docker compose --profile training run --rm trainer -m eval.check_gates \
  eval/results/scoreboard.json
```

Volumes mounted into the trainer (`./ai_engine/{models,data,eval/results,logs}`)
mean every artefact survives container teardown. The runtime `ai_engine`
service shares the same image, so M2/M3 are loaded automatically at startup
when the checkpoints exist.

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
