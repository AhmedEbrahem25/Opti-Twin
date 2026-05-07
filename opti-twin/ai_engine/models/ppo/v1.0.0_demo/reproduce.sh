#!/usr/bin/env bash
# Reproduce v1.0.0_demo end-to-end. Run from `opti-twin/ai_engine/`.
set -euo pipefail

# 1. Data
python collect_episodes.py --n-episodes 200 --difficulty medium --seed 1000
python collect_episodes.py --n-episodes 100 --difficulty hard   --seed 5000
python -m data_pipeline.split

# 2. Cheap models (M3 anomaly + M4 BC at 32-D for legacy parity)
python train_anomaly.py --epochs 30

# 3. M2 forecaster
python train_forecaster.py --epochs 10 --max-windows 10000

# 4. BC at 39-D (M2/M3 wired)
python train_bc.py \
  --epochs 10 \
  --forecaster models/forecaster/v0.1.0 \
  --anomaly   models/anomaly/v0.1.0 \
  --out       models/bc/v0.2.0/bc_init.pt

# 5. M5 reward model
python train_reward.py --n-pairs 200 --epochs 20

# 6. Optuna + final PPO (this checkpoint)
python train_ppo.py \
  --bc-init     models/bc/v0.2.0/bc_init.pt \
  --forecaster  models/forecaster/v0.1.0 \
  --anomaly     models/anomaly/v0.1.0 \
  --tune --tune-trials 6 --tune-budget 30000 \
  --total-timesteps 300000 \
  --output      models/ppo/v1.0.0_demo/opti_twin_ppo.zip

# 7. Evals
python -m eval.benchmarks --model models/ppo/v1.0.0_demo/opti_twin_ppo.zip \
                          --out   eval/results/v1.0.0_scoreboard.json
python -m eval.latency    --model models/ppo/v1.0.0_demo/opti_twin_ppo.zip \
                          --out   models/ppo/v1.0.0_demo/latency.json
python -m eval.check_gates eval/results/v1.0.0_scoreboard.json
