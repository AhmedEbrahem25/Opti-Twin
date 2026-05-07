# Opti-Twin PPO v1.0.0 (demo)

**Status:** trained 2026-05-07. Below scripted-policy gate; demo ships with the
scripted decision tree (planing-v2.md §17 risk MR1). The full 5-model stack
(M2/M3/M4/M5 + data pipeline + scenarios + safety) remains active and durable.

## What this checkpoint is

A PPO policy trained on the 39-D hybrid observation:
- 16 telemetry dims
- 6 M2 forecast summary (5 quantiles + IPI width)
- 16 live dynamic-pricing dims (Redis pricing service)
- 1 M3 anomaly score

Warm-started from BC v0.2.0 (val acc 93.6%). Trained on the full
`data/processed/train` partition (210 episodes × 480 sim-min steps).

## Model stack

| ID | Path | Purpose |
|----|------|---------|
| M1 | this checkpoint | PPO policy (action recommender) |
| M2 | `models/forecaster/v0.1.0/forecaster.pt` | LSTM tariff/load forecaster (val pinball ~0.082, 90% PI cov ~89%) |
| M3 | `models/anomaly/v0.1.0/autoencoder.pt` | 1D-CNN telemetry autoencoder (95-pct threshold 0.169) |
| M4 | `models/bc/v0.2.0/bc_init.pt` | BC warm-start (val acc 93.6%) |
| M5 | `models/reward_model/v0.1.0/reward_model.pt` | Bradley-Terry preference model (val acc ~96.7% on synthetic oracle) |

## Training config

Optuna study: 6 trials × 30K steps each (TPE sampler, seed 42). Best config
applied to a 300K-step final run.

| Hyperparam | Value |
|---|---|
| `learning_rate` | 1.90e-05 |
| `clip_range` | 0.158 |
| `ent_coef` | 9.75e-04 |
| `gamma` | 0.972 |
| `n_steps` | 1024 |
| `batch_size` | 64 |
| `n_epochs` | 10 |

See `opti_twin_ppo.tuned_params.json` for the canonical record.

## Eval scoreboard

`metrics.json` contains the full per-scenario detail. Headline:

| ID | Scenario | scripted | PPO | Δ | Won |
|---|---|---:|---:|---:|---|
| S01 | 24-hr nominal, flat tariff | 2034.6 | 1740.3 | -294.3 | no |
| S02 | 24-hr TOU mode | 2255.0 | 1992.3 | -262.7 | no |
| S03 | Wall overheat at 18:00 | 1901.9 | 1755.7 | -146.2 | no |
| S04 | Electrode break in MELT_2 | 2110.5 | 1861.2 | -249.4 | no |
| S05 | Grid Hz dip 49.6 | 1730.8 | 1718.5 | -12.3 | no |
| S06 | Transformer alarm late | 1846.1 | 1720.4 | -125.8 | no |
| S07 | PF stuck at 0.74 | 1716.7 | 1290.3 | -426.4 | no |
| S08 | Forecast dropout | 1623.7 | 1194.6 | -429.2 | no |
| S09 | Multi-crisis | 1598.8 | 1512.1 | -86.7 | no |
| S10 | OOD batch weight | 1445.9 | 1552.5 | +106.6 | **yes** |

PPO scenario wins: 1/10 (gate requires >= 7).
PPO total safety breaches: 4 (gate requires 0).

## Latency

```
n_calls = 10,000
p50  = 0.88 ms
p95  = 1.62 ms
p99  = 2.43 ms     <-- gate: < 5 ms
max  = 48.90 ms    (single outlier, likely OS scheduling)
```

p99 latency gate passes by ~2× margin even with M2 + M3 inference + safety
mask + reward-component computation in the recommend() path.

## Demo gates (planing-v2.md §12.4) -- final result

| Gate | Required | v1.0.0 actual | Pass |
|---|---|---|---|
| Scenario wins | >= 7 / 10 | 1 / 10 | no |
| Safety breaches | 0 | 4 | no |
| Negative reward scenarios | 0 | 0 | yes |
| p99 latency | < 5 ms | 2.43 ms | yes |

Two of four gates pass. The two failing gates (wins, safety) are the
scripted-policy hurdle PPO has not cleared at this training budget.

## Demo gates (planing-v2.md §12.4)

1. PPO mean reward >= scripted on `eval_agent.py --episodes 100`.
2. >= 7 of 10 scenarios in `eval/benchmarks.py` favour PPO.
3. Zero PPO safety breaches across the scoreboard.
4. p99 inference latency < 5 ms.

## Known limitations

- **Synthetic preferences for M5.** The Bradley-Terry reward model is trained against a deterministic oracle (penalises wall-temp > 240, PF < 0.92, missed heats; rewards bath in [1600, 1650]). It is not a real RLHF training run. Documented per planing-v2.md §9.3 / §18.
- **PPO < scripted at the 200K-step demo budget.** With identical reward function, PPO did not beat the scripted decision tree at 200K steps even with low-entropy/low-lr tuning. Final 300K-step + Optuna run may close the gap; if not, the demo ships with the scripted policy (planing-v2.md §17 risk MR1) and the rest of the stack remains durable.
- **Hard tier in `OptiTwinEAFEnv` ≈ medium tier.** The simulator's underlying physics doesn't model the tariff jitter / multi-event bursts that planing-v2.md §11.1 calls for. The `hard` profile boosts crisis probability and noise but does not yet randomise tariff transitions.
- **24-hour episode horizon (480 steps).** The forecaster horizon was scaled from the spec's 600 ticks (which assumed 3-second ticks) down to 60 ticks (3 sim-hours forward) to fit episode length. See `forecaster/lstm_forecaster.py` for the rationale.

## Reproduce

```bash
cd opti-twin/ai_engine

# 1. Collect data
python collect_episodes.py --n-episodes 200 --difficulty medium --seed 1000
python collect_episodes.py --n-episodes 100 --difficulty hard   --seed 5000
python -m data_pipeline.split

# 2. Train M2/M3/M4
python train_anomaly.py     --epochs 30
python train_bc.py          --epochs 10 --forecaster models/forecaster/v0.1.0 --anomaly models/anomaly/v0.1.0
python train_forecaster.py  --epochs 10 --max-windows 10000

# 3. Train M5
python train_reward.py --n-pairs 200 --epochs 20

# 4. Optuna + final PPO (this checkpoint)
python train_ppo.py \
  --bc-init models/bc/v0.2.0/bc_init.pt \
  --forecaster models/forecaster/v0.1.0 \
  --anomaly models/anomaly/v0.1.0 \
  --tune --tune-trials 6 --tune-budget 30000 \
  --total-timesteps 300000 \
  --output models/ppo/v1.0.0_demo/opti_twin_ppo.zip

# 5. Eval
python -m eval.benchmarks --model models/ppo/v1.0.0_demo/opti_twin_ppo.zip
python -m eval.latency    --model models/ppo/v1.0.0_demo/opti_twin_ppo.zip
python -m eval.check_gates eval/results/scoreboard.json
```
