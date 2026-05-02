# 🧠 OPTI-TWIN — ML SYSTEM PLAN (Planning v2)
> **Companion to:** `plan.md` (master plan, evidence-backed)
> **Focus:** Machine-Learning architecture, datasets, training pipeline, evaluation, deployment
> **Version:** 1.0 · **Created:** 2026-05-01 · **Days to Demo:** 7
> **Hackathon:** NextCity AI Hack 2026 · Alamein International University

> This document defines **how Opti-Twin actually learns**, not just what it does at runtime. The runtime architecture, problem catalogue, datasets, and demo are in `plan.md`. This file is the ML-engineering blueprint a senior ML engineer would expect to see before shipping a system that issues setpoint recommendations to a 200 MW Electric Arc Furnace.

---

## 📋 Table of Contents

1. [ML System Overview](#1-ml-system-overview)
2. [Why Multiple Models, Not One](#2-why-multiple-models)
3. [Data Pipeline](#3-data-pipeline)
4. [Model Catalogue](#4-model-catalogue)
5. [Model 1 — Multi-Objective RL Policy (PPO)](#5-model-1--rl-policy)
6. [Model 2 — Tariff & Demand Forecaster (Temporal Fusion / LSTM)](#6-model-2--tariff-demand-forecaster)
7. [Model 3 — Equipment Anomaly Detector (Autoencoder)](#7-model-3--anomaly-detector)
8. [Model 4 — Behavior-Cloning Warm Start](#8-model-4--behaviour-cloning)
9. [Model 5 — Reward Model (Preference Learning)](#9-model-5--reward-model)
10. [Training Infrastructure](#10-training-infrastructure)
11. [Curriculum & Domain Randomisation](#11-curriculum--domain-randomisation)
12. [Evaluation Framework](#12-evaluation-framework)
13. [Safety, Uncertainty & Action Masking](#13-safety-uncertainty--action-masking)
14. [Sim-to-Real Transfer](#14-sim-to-real-transfer)
15. [MLOps & Model Lifecycle](#15-mlops--model-lifecycle)
16. [7-Day ML Execution Plan](#16-7-day-ml-execution-plan)
17. [Risk Register (ML-Specific)](#17-risk-register-ml-specific)
18. [References](#18-references)

---

## 1. ML System Overview

Opti-Twin is **not a single ML model** — it is a stack of five complementary models, each with a distinct role, that together produce a single auditable recommendation per 3-second telemetry tick. Treating it as a single PPO agent would be a research project that takes months. Decomposing the problem matches industrial reality and lets each component be trained, evaluated, and deployed independently.

```
╔════════════════════════════════════════════════════════════════════╗
║                  OPTI-TWIN — ML STACK                              ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  ┌──────────────────────┐                                         ║
║  │  Telemetry stream    │  3-sec ticks from simulator (or SCADA) ║
║  └──────────┬───────────┘                                         ║
║             │                                                      ║
║             ├────────────────────────┐                            ║
║             ▼                        ▼                            ║
║   ┌──────────────────┐     ┌──────────────────────┐              ║
║   │  M2: Forecaster  │     │  M3: Anomaly Det.    │              ║
║   │  Price/Load LSTM │     │  Reconstruction AE   │              ║
║   │  Horizon: 30 min │     │  Output: anomaly_p   │              ║
║   └────────┬─────────┘     └──────────┬───────────┘              ║
║            │                          │                           ║
║            └──────┬───────────────────┘                           ║
║                   ▼                                                ║
║       ┌─────────────────────────────────┐                         ║
║       │  M1: RL Policy  (PPO)           │  Augmented state:       ║
║       │  Input: state + forecast +      │  16-D telemetry         ║
║       │  anomaly                        │  + 6-D forecast         ║
║       │  Output: action distribution    │  + 1-D anomaly score    ║
║       └────────┬────────────────────────┘                         ║
║                │                                                   ║
║                ├── M4: BC warm-start (offline init)                ║
║                ├── M5: Reward model (preference fine-tune)         ║
║                ▼                                                   ║
║       ┌──────────────────────┐                                    ║
║       │ Action mask + safety │  Hard physical limits enforced     ║
║       │ envelope             │  before action reaches simulator   ║
║       └────────┬─────────────┘                                    ║
║                ▼                                                   ║
║       ┌──────────────────────┐                                    ║
║       │  XAI engine          │  Template-based, deterministic     ║
║       └──────────────────────┘                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

### Design principles

1. **Model decomposition over monolithic RL.** A 1M-step PPO agent that has to simultaneously learn price forecasting, equipment anomaly detection, and control policy is sample-inefficient and fragile. Separate concerns let each model converge fast.
2. **Auditable by construction.** Every recommendation traces to: forecast values, anomaly score, action probabilities, dominant reward component, applied safety mask. This becomes the XAI payload.
3. **Offline-warm + online-tune.** Behaviour cloning from scripted-policy rollouts gives the RL agent a reasonable starting point in <5 min, instead of 30 min of cold PPO.
4. **Uncertainty-aware action masking.** Forecasts come with prediction intervals; if confidence is low and the action is risky, the policy is masked toward conservative actions.
5. **The same training code runs in sim and shadow-mode.** A single `Trainer` abstraction, just with a different env source, supports both.

---

## 2. Why Multiple Models

| Job to be done | Best ML tool | Why |
|---|---|---|
| Decide arc-power / cooling / PF setpoints | **Reinforcement Learning** | Sequential decision, delayed reward, multi-objective tradeoffs |
| Forecast next 30-min electricity price (under TOU mode) and load curve | **Supervised time-series** (LSTM / Temporal Fusion Transformer) | Stationary input → numeric output; well-studied; cheap |
| Detect "this telemetry frame doesn't look right" (equipment health) | **Unsupervised reconstruction** (autoencoder) | We don't have labels for "about-to-fail"; AE learns normal manifold |
| Bootstrap RL policy without 30-min training time | **Behaviour cloning** (supervised) | Imitates the scripted policy → instant warm start |
| Tune reward weights against operator preferences | **Preference learning** (Bradley-Terry / RLHF) | Reward weights are subjective; pairwise feedback is cheap to collect |

Trying to learn all of this with one PPO is the standard mistake — the credit assignment problem becomes intractable. Decomposition is the engineering move.

---

## 3. Data Pipeline

### 3.1 Sources (mapped to plan.md §6)

| Source | Type | Use | Volume |
|---|---|---|---|
| Synthetic simulator rollouts | telemetry stream | Train M1, M2, M3, M4 | ~500K transitions per training run |
| EgyptERA tariff schedule | static JSON | Ground truth for M2 forecasting | 1 file |
| GUC Working Paper #29 TOU proposal | static JSON | Future-mode forecasting target | 1 file |
| World Steel / IEA energy intensities | static reference | Calibrate sim → realism check | Numeric anchors |
| Operator-rating session logs (synthetic) | preference pairs | Train M5 reward model | Target: 200 pairs |

### 3.2 Schema — single transition record

```python
# data/transitions/episode_{n}.parquet
{
  # Telemetry (16-D obs)
  "ts": float,
  "sim_hour": float,
  "arc_power_mw": float,
  "furnace_bath_temp": float,
  "wall_panel_temp": float,
  "electrode_temp": float,
  "cooling_water_outlet_temp": float,
  "heat_progress_pct": float,
  "current_batch_weight": float,
  "batches_today": int,
  "production_backlog": int,
  "power_factor": float,
  "energy_this_heat_kwh": float,
  "electrode_position_mm": float,
  "electrode_consumption_kg": float,
  "electricity_price": float,
  "is_peak": bool,
  "grid_frequency": float,
  "tou_mode": bool,
  # Action taken
  "action_label": str,
  "action_id": int,
  # Outcome
  "reward_total": float,
  "reward_components": {…},
  # Meta
  "episode_id": int,
  "step_id": int,
  "crisis_flags": {…},
}
```

Stored as **Parquet** (columnar, fast for sequential reads during training). One file per episode (~480 rows), partitioned by `difficulty/{easy|medium|hard}`.

### 3.3 Pipeline stages

```
┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ collect.py  │ → │ validate.py  │ → │ featurize.py │ → │ split.py     │
│ run sim     │   │ schema check │   │ scale + lag  │   │ train/val/   │
│ N episodes  │   │ + outliers   │   │ features     │   │ test 70/15/15│
└─────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

- `collect.py` runs the simulator headless under varied configs (curriculum levels, crisis injection probability, tariff mode).
- `validate.py` checks schemas with Pydantic and runs basic sanity rules (e.g., `bath_temp ∈ [1100, 1700]`).
- `featurize.py` adds rolling means (5/15/30 min), lag features for forecasting, and z-score normalisation per column. Scaler stats are saved so inference uses the exact same transform.
- `split.py` stratifies by episode (no leakage) and difficulty.

### 3.4 Storage layout

```
data/
├── raw/              # parquet from collect.py
├── processed/        # post featurize
│   ├── train/
│   ├── val/
│   └── test/
├── scalers/          # joblib StandardScaler + MinMaxScaler artefacts
├── tariffs/          # static JSON (D1, D3 from plan.md §6.1)
└── preferences/      # M5 reward-model training pairs (JSONL)
```

---

## 4. Model Catalogue

| ID | Name | Family | Input | Output | Training data | Latency target |
|---|---|---|---|---|---|---|
| **M1** | RL Policy | PPO (Stable Baselines3) | 23-D state (16 telem + 6 forecast + 1 anomaly) | Discrete(7) action | 1M timesteps from sim | <5 ms/inference |
| **M2** | Forecaster | LSTM (or Temporal Fusion Transformer) | last 60 ticks (3 min) of price + load | next 600 ticks (30 min) of price + load + uncertainty | 50K episodes of simulator | <20 ms/inference, refresh every 30 s |
| **M3** | Anomaly Detector | Autoencoder (1D-CNN) | 60-tick window of 9 thermal + electrical channels | reconstruction error → anomaly score [0, 1] | "normal" episodes only | <10 ms/inference |
| **M4** | BC Warm-Start | MLP (supervised) | 23-D state | Discrete(7) action | scripted policy rollouts | one-shot, used to init M1 |
| **M5** | Reward Model | Bradley-Terry MLP | 2 trajectories (50 frames each) | preference logit | 200 human-rated pairs | <50 ms/eval, used during RL training |

All five models are exposed by the same `ai_engine` container as composable Python classes; only M1 (the policy) is in the per-tick critical path.

---

## 5. Model 1 — RL Policy

### 5.1 Why PPO

| Candidate | Pros | Cons | Decision |
|---|---|---|---|
| PPO | Stable, on-policy, well-documented in SB3 | Sample inefficient | ✓ Choose |
| SAC | Sample efficient, off-policy | Continuous actions only without modification | ✗ |
| DQN | Simple, off-policy | Discrete action only, less stable on dense reward | ✗ |
| MARL (e.g. one agent per actuator) | Cleaner credit assignment | Coordination bugs at hackathon scale | ✗ Future |

PPO is the safe industry choice and integrates cleanly with the multi-objective reward.

### 5.2 Architecture

```python
# ai_engine/policies/ppo_policy.py
from stable_baselines3 import PPO

policy_kwargs = dict(
    net_arch=dict(pi=[256, 256], vf=[256, 256]),
    activation_fn=torch.nn.Tanh,        # Tanh for bounded value estimates
)

model = PPO(
    policy="MlpPolicy",
    env=vec_env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,                       # encourage exploration
    vf_coef=0.5,
    max_grad_norm=0.5,
    policy_kwargs=policy_kwargs,
    tensorboard_log="logs/tb/",
)
```

### 5.3 Augmented observation space

| Group | Source | Dim |
|---|---|---|
| Live telemetry | simulator | 16 |
| Forecast (M2) — 5 quantiles + 1 horizon-mean | M2 | 6 |
| Anomaly score (M3) | M3 | 1 |
| **Total** | | **23** |

> The **forecast and anomaly score are themselves model outputs** — this is intentional. The RL policy doesn't have to learn forecasting from scratch; it consumes a learned forecast.

### 5.4 Action space

7 discrete actions:

```
0  HOLD_STEADY
1  REDUCE_ARC_POWER          (Δ −10 MW)
2  RAISE_PF_COMPENSATION     (+10 MVAR)
3  EMERGENCY_COOLING         (+150 l/min, Δ arc −10 MW)
4  PRE_PEAK_DROP             (Δ −20 MW)
5  GRID_RIDE_THROUGH         (cap arc at 60 MW)
6  TRANSFORMER_DERATE        (cap arc at 75 MW)
```

A discrete head is trained but each action carries a **default magnitude**. A second continuous critic head is reserved for v2 (parameterized actions).

### 5.5 Reward (already in plan.md §7.3)

```
R = α·E_saved − β·M_stress − γ·P_delay + δ·Quality − ε·Wear − ζ·PF_penalty
```

In v2 of the ML plan, **the weights themselves can be tuned by M5** (reward model from preferences) instead of fixed by hand.

### 5.6 Training procedure

```bash
# ai_engine/train_ppo.py
python -m ai_engine.train_ppo \
    --env opti_twin_eaf \
    --total-timesteps 1_000_000 \
    --curriculum easy,medium,hard \
    --bc-init models/bc_init.pt \
    --reward-model models/reward_model.pt \
    --output models/opti_twin_ppo.zip \
    --seed 42
```

### 5.7 Hyperparameter search

Use **Optuna** with TPE sampler on a 50K-step proxy task:
- Learning rate: log-uniform [1e-5, 1e-3]
- `clip_range`: [0.1, 0.3]
- `ent_coef`: log-uniform [0.001, 0.05]
- `gamma`: [0.95, 0.999]
- `n_steps`: {1024, 2048, 4096}

Best config promoted to full 1M-step run.

---

## 6. Model 2 — Tariff & Demand Forecaster

### 6.1 What it predicts

Given the last 60 ticks (3 sim-minutes) of:
- `electricity_price`
- `arc_power_mw`
- `is_peak`
- `tou_mode`
- `sim_hour` (sin/cos encoded)

Predict the next **600 ticks (30 sim-minutes)** of:
- `electricity_price` (mean + 5 quantiles: 0.05, 0.25, 0.5, 0.75, 0.95)
- `expected_load_mw`

### 6.2 Why a forecaster matters

Under the **current Egyptian flat tariff (1.60 EGP/kWh)**, M2's price forecast is trivial — but its load forecast still matters for power-factor planning and pre-emptive cooling. Under **TOU reform mode**, M2 becomes critical: the agent should drop arc power **before** the peak window starts, and only a forecaster can deliver that lead time.

### 6.3 Architecture choice

| Candidate | Verdict |
|---|---|
| Naïve persistence (last-value) | Too weak under TOU transitions |
| ARIMA / SARIMA | Brittle to regime changes (peak/off-peak boundaries) |
| **LSTM (1 layer, 128 hidden)** | ✓ Default choice — fast to train, well-supported, fine for 30-min horizon |
| Temporal Fusion Transformer | Best results; expensive to train; overkill for hackathon |
| N-BEATS | Strong but adds dep; consider post-hackathon |

**Decision:** ship LSTM at the hackathon; bench TFT for post-hackathon.

```python
# ai_engine/forecaster/lstm_forecaster.py
class TariffLoadForecaster(nn.Module):
    def __init__(self, input_dim=7, hidden=128, horizon=600, n_quantiles=5):
        super().__init__()
        self.encoder = nn.LSTM(input_dim, hidden, batch_first=True)
        # Output heads: price (5 quantiles + mean) + load (1)
        self.price_head = nn.Linear(hidden, horizon * (n_quantiles + 1))
        self.load_head = nn.Linear(hidden, horizon)
        self.horizon = horizon
        self.n_quantiles = n_quantiles

    def forward(self, x):  # x: (B, 60, 7)
        _, (h, _) = self.encoder(x)
        h = h[-1]
        price = self.price_head(h).view(-1, self.horizon, self.n_quantiles + 1)
        load = self.load_head(h)
        return price, load
```

### 6.4 Loss

**Quantile loss (pinball)** for prices — gives prediction intervals natively. **MSE** for load.

```python
def pinball_loss(y_true, y_pred_quantiles, quantiles=(0.05, 0.25, 0.5, 0.75, 0.95)):
    losses = []
    for i, q in enumerate(quantiles):
        diff = y_true - y_pred_quantiles[..., i]
        losses.append(torch.max(q * diff, (q - 1) * diff))
    return torch.mean(torch.stack(losses))
```

### 6.5 Training

- 50K episodes from the simulator → ~24M frames.
- Sliding window of 60 lookback / 600 ahead → ~24M training samples (heavy overlap, downsample 10×).
- Adam, lr=1e-3, batch 256, 20 epochs, early stop on val pinball loss.
- Train time: ~15 min on CPU, <5 min on GPU.

### 6.6 Inference cadence

Refresh every 30 sim-seconds (10 ticks). The **last forecast** is included in the RL policy's observation each tick; it doesn't need recomputing every tick.

### 6.7 Metrics

- **Pinball loss** at quantiles 0.5 (sharpness) and 0.05/0.95 (calibration).
- **MAPE** for load.
- **Coverage** — fraction of true prices inside 90% interval (target: ~90%).

---

## 7. Model 3 — Anomaly Detector

### 7.1 Job

Detect "this telemetry frame is unusual" — early warning for wall overheat, electrode break, transformer alarm, grid spike. We don't have labels for these (low base rate, varied causes), so we use **unsupervised reconstruction**.

### 7.2 Architecture: 1D-CNN Autoencoder

```python
# ai_engine/anomaly/autoencoder.py
class TelemetryAutoencoder(nn.Module):
    """Reconstructs a 60-tick window of 9 thermal/electrical channels.
    Reconstruction error → anomaly score."""
    def __init__(self, channels=9, window=60, latent=8):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(channels, 32, 5, padding=2), nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, 3, padding=1), nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Flatten(),
            nn.Linear(64 * (window // 4), latent),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent, 64 * (window // 4)),
            nn.Unflatten(1, (64, window // 4)),
            nn.Upsample(scale_factor=2),
            nn.Conv1d(64, 32, 3, padding=1), nn.ReLU(),
            nn.Upsample(scale_factor=2),
            nn.Conv1d(32, channels, 5, padding=2),
        )

    def forward(self, x):  # x: (B, 9, 60)
        return self.decoder(self.encoder(x))

    def anomaly_score(self, x):
        recon = self.forward(x)
        per_channel = torch.mean((recon - x) ** 2, dim=2)
        return torch.mean(per_channel, dim=1)  # → (B,)
```

### 7.3 Training

- **Train ONLY on episodes with no crisis injected.** Crisis episodes go into the eval set.
- MSE reconstruction loss.
- Adam, lr=1e-3, batch 64, 30 epochs.
- Calibrate threshold: pick the 95th percentile of training-set scores → decisions above it count as "anomalous".

### 7.4 Output to RL

A single scalar per tick: `clip(score / threshold, 0, 1)`. The policy learns to weight its action toward conservative options when this is high.

### 7.5 Metrics

- **AUC** on held-out crisis episodes (target: >0.85).
- **Lead time** before the human-eye notices the crisis (target: ≥30 sim-seconds advance warning).

---

## 8. Model 4 — Behaviour Cloning Warm Start

### 8.1 Why

PPO from random initialisation needs ~30 min on a GPU to reach acceptable performance. For a 7-day hackathon, that's an unacceptable iteration cost. Behaviour cloning the **scripted policy** (already in `ai_engine/agent.py`) gives us a usable starting point in 2 minutes of training.

### 8.2 Procedure

1. Run scripted policy for 5K episodes → ~2.4M (state, action) pairs.
2. Train an MLP classifier (same network as PPO's policy head):
   ```python
   model = nn.Sequential(
       nn.Linear(23, 256), nn.Tanh(),
       nn.Linear(256, 256), nn.Tanh(),
       nn.Linear(256, 7),
   )
   loss = nn.CrossEntropyLoss()
   ```
3. Save weights as `models/bc_init.pt`.
4. PPO initialisation: load these weights into the policy network.

### 8.3 Why this works

The scripted policy is suboptimal but **safe and reasonable**. BC gives PPO a starting policy that already knows "wall hot → cool", "PF low → comp" — leaving PPO to discover only the **subtle improvements** (e.g. anticipating peak windows, exploiting forecasts).

### 8.4 Validation

- BC accuracy on held-out scripted-policy frames: target >85%.
- Returns of BC-only policy in eval env: target ≥80% of scripted-policy returns.
- After PPO fine-tunes from BC init: returns should exceed scripted by ≥10% within 200K timesteps (vs. 1M from random init).

---

## 9. Model 5 — Reward Model (Preference Learning)

### 9.1 The problem

The α/β/γ/δ/ε/ζ weights are **subjective**. A plant manager who lost a transformer would weight β higher than one who lost a steel shipment. We can't pin numerical values; we can only ask "which of these two trajectories looks better?"

### 9.2 Bradley-Terry preference model

Collect 200 pairs of 50-frame trajectories. For each pair, a (synthetic for hackathon, human for production) rater picks the preferred one.

```python
# ai_engine/reward_model.py
class PrefRewardModel(nn.Module):
    """Predicts a scalar reward from a trajectory; trained to match preferences."""
    def __init__(self, state_dim=23):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim + 7, 128), nn.ReLU(),  # +7 for action one-hot
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1),
        )

    def trajectory_reward(self, states, actions):
        per_step = self.net(torch.cat([states, F.one_hot(actions, 7)], dim=-1))
        return per_step.sum(dim=1)  # sum over trajectory

    def forward(self, traj_a, traj_b):
        ra = self.trajectory_reward(*traj_a)
        rb = self.trajectory_reward(*traj_b)
        return torch.sigmoid(ra - rb)
```

Loss: **binary cross-entropy** against the human preference label.

### 9.3 Synthetic preference oracle (for hackathon)

We don't have humans. So we use a **synthetic oracle**: trajectories that maintained safe wall temps and avoided PF penalties get labelled "preferred". This is honest about being a stand-in (see plan.md §18 limitations) but proves the pipeline works.

### 9.4 Use during RL training

The learned reward model can either:
- **Replace** the hand-coded reward entirely (pure preference RL), or
- **Re-weight** the existing reward components (interpretable hybrid).

For hackathon: use the **hybrid** — feed M5's predicted weights into the multi-objective formula. Keeps things explainable.

---

## 10. Training Infrastructure

### 10.1 Stack

| Layer | Tool |
|---|---|
| Experiment tracking | TensorBoard (in-repo) + optional W&B |
| Hyperparameter search | Optuna |
| Distributed training (optional) | `SubprocVecEnv` for 4–8 parallel envs |
| Storage | local disk; Parquet files; PyTorch `state_dict` for checkpoints |
| Reproducibility | `python -m torch.use_deterministic_algorithms(True)` + seed everything |

### 10.2 Layout (extending `ai_engine/`)

```
ai_engine/
├── train_ppo.py           # M1 trainer (RL)
├── train_forecaster.py    # M2 trainer
├── train_anomaly.py       # M3 trainer
├── train_bc.py            # M4 trainer
├── train_reward.py        # M5 trainer
├── collect_episodes.py    # data collection harness
├── policies/
│   ├── ppo_policy.py
│   └── bc_policy.py
├── forecaster/
│   └── lstm_forecaster.py
├── anomaly/
│   └── autoencoder.py
├── reward_model.py
├── eval/
│   ├── benchmarks.py
│   ├── metrics.py
│   └── scenarios/         # JSON eval scenarios
├── models/                # checkpoints
└── logs/                  # TensorBoard
```

### 10.3 Compute budget

Single laptop with discrete GPU (RTX 3060+):

| Job | Time |
|---|---|
| Episode collection (50K × 480 steps) | ~20 min |
| M2 forecaster training | ~15 min CPU / 5 min GPU |
| M3 autoencoder training | ~10 min CPU / 3 min GPU |
| M4 behaviour cloning | ~2 min |
| M5 reward model | ~5 min |
| M1 PPO from BC init (200K steps) | ~10 min GPU |
| **End-to-end pipeline** | **~60 min** |

CPU-only fallback: ~2.5 hours total. Achievable on Day 3 of the hackathon.

---

## 11. Curriculum & Domain Randomisation

### 11.1 Curriculum

Three difficulty tiers — agent trains on each in sequence.

| Tier | Crisis prob/ep | TOU mode | Forecast noise | Time budget |
|---|---|---|---|---|
| **Easy** | 0% | off | none | 25% of total steps |
| **Medium** | 20% | optional | mild | 50% of total steps |
| **Hard** | 50% multi-event | on, with 30% transition jitter | strong + occasional dropout | 25% of total steps |

### 11.2 Domain randomisation

Each episode samples from:
- Tariff: {flat 1.60, TOU schedule with ±10% jitter on prices}
- Bath thermal mass: ±10% of rated 185 t
- Sensor noise: Gaussian with σ scaled per channel
- Crisis timing: uniform across heat phases
- Initial bath temperature: U[1200, 1400] °C

This is the **cheapest path to sim-to-real robustness** — the policy learns not to overfit to one specific simulator parameterisation.

---

## 12. Evaluation Framework

### 12.1 Eval scenarios

10 fixed JSON-defined scenarios under `ai_engine/eval/scenarios/`:

| ID | Scenario | What it tests |
|---|---|---|
| S01 | 24-hr nominal, flat tariff, no crisis | Baseline efficiency |
| S02 | 24-hr TOU mode, no crisis | Pre-peak shifting |
| S03 | Wall overheat at 18:00 | β-override |
| S04 | Electrode break in MELT_2 | Recovery + prod continuity |
| S05 | Grid Hz dip 49.6 | Ride-through |
| S06 | Transformer alarm late shift | Derate + reschedule |
| S07 | PF stuck at 0.74 (cap-bank fault) | M5 reward shifts toward PF |
| S08 | Forecast horizon dropout (M2 silent for 5 min) | Uncertainty handling |
| S09 | Multi-crisis (wall+grid in 60 sim-sec) | Priority arbitration |
| S10 | Out-of-distribution batch weight (220 t) | Safety mask kicks in |

### 12.2 Metrics

| Family | Metric |
|---|---|
| **Economic** | EGP saved per heat (vs. no-AI baseline); PF-penalty hours per day |
| **Safety** | Wall temp >250 °C breaches per 1K episodes; bath drops below 1500 °C |
| **Quality** | % heats with final bath in [1600, 1650] °C |
| **Throughput** | Heats per simulated day; backlog at day-end |
| **CO₂** | Tonnes saved per day |
| **Robustness** | Δ-return between train and eval distributions |
| **Calibration** | Brier score on M2's 90% interval |
| **Anomaly** | AUC, lead-time on M3 detection |

### 12.3 Regret analysis

Define the **oracle policy** (full hindsight, optimal actions per scenario via dynamic programming on the simulator). Compare:

```
regret(π) = oracle_return − π_return
```

Track regret per scenario through training. Trends matter more than absolute numbers — flat regret = no learning.

### 12.4 Pre-merge gates

A new model checkpoint can replace `models/opti_twin_ppo.zip` in the demo branch only if:
1. ✅ Beats current champion on ≥7 of 10 scenarios.
2. ✅ No safety breaches across all 10 scenarios in 100 trials.
3. ✅ EGP-saved and CO₂-saved metrics are not negative on any scenario.
4. ✅ Inference latency p99 <5 ms.

---

## 13. Safety, Uncertainty & Action Masking

### 13.1 Hard physical limits (PLC equivalent)

The runtime applies these regardless of policy output:

```python
def apply_action_mask(action_id: int, state: dict) -> int:
    if state["wall_panel_temp"] >= 250:
        return ACTION_EMERGENCY_COOLING
    if state["furnace_bath_temp"] < 1500:
        # never drop power further if bath risks freezing
        if action_id in (ACTION_REDUCE_ARC_POWER, ACTION_PRE_PEAK_DROP):
            return ACTION_HOLD_STEADY
    if state["grid_frequency"] < 49.7:
        return ACTION_GRID_RIDE_THROUGH
    return action_id
```

These are not learned — they are **non-negotiable** envelopes.

### 13.2 Uncertainty-aware masking

If M2's 90% prediction interval for next-30-min price is wider than threshold, the policy is **biased toward HOLD_STEADY**. Implementation: zero out logits for risky actions when `forecast_uncertainty > τ`.

If M3 anomaly score >0.8, similarly bias toward conservative actions.

### 13.3 Auto-rollback

If 3 consecutive ticks show safety-envelope violations, the runtime **freezes the AI toggle to OFF** and surfaces a banner. Operator (or judge) must manually re-enable. No silent recovery.

---

## 14. Sim-to-Real Transfer

(Cross-references `plan.md` §19 — Real-World Deployment Strategy.)

### 14.1 What's different in real deployment

| Aspect | Sim | Real |
|---|---|---|
| Telemetry rate | 3 sec | typically 1 sec from OPC UA |
| Sensor noise | Gaussian + tunable | unknown distribution; calibration drift |
| Action latency | 0 | 100–500 ms PLC round-trip |
| Reward signal | dense (every step) | sparse (energy bill is monthly) |
| Catastrophic failures | tolerated in sim | unacceptable |

### 14.2 Three-step transfer protocol

1. **System identification.** Run the agent in shadow mode for 4–8 weeks. Compare predicted state evolution with real telemetry. Tune simulator parameters to minimise residual.
2. **Domain-randomised retraining.** Re-train PPO on the calibrated simulator with widened randomisation bands.
3. **Conservative deployment.** Start in **advisory mode** (HMI shows action, operator approves). Move to closed-loop only after 3+ months of >60% accept rate.

### 14.3 Drift detection

In production, run two monitors:
- **Distribution drift** on telemetry inputs (KS test on rolling 1-hr windows vs. training distribution).
- **Performance drift** — observed savings vs. M5's predicted reward.

If either exceeds threshold for 24+ hours: alert + auto-fallback to scripted policy.

---

## 15. MLOps & Model Lifecycle

### 15.1 Model versioning

```
models/
├── ppo/
│   ├── v1.0.0_2026-05-04_seed42/opti_twin_ppo.zip
│   ├── v1.1.0_2026-05-06_seed7/opti_twin_ppo.zip
│   └── current → v1.1.0…
├── forecaster/
│   ├── v0.1.0_lstm_baseline/forecaster.pt
│   └── current → …
├── anomaly/
└── reward_model/
```

`current` is a symlink. Rollback = move the symlink.

### 15.2 Model card per release

```
models/ppo/v1.1.0_2026-05-06_seed7/
├── opti_twin_ppo.zip
├── model_card.md          # describes training config, eval results
├── metrics.json           # full eval-scenario scores
└── reproduce.sh           # one-line command to retrain
```

### 15.3 CI gates

Every PR that touches `ai_engine/`:
- Re-trains M3 anomaly detector on a 1K-episode subset (smoke test).
- Runs M1 inference on all 10 eval scenarios → fails if any safety breach.
- Asserts model file size <100 MB (prevents accidental dataset commits).

### 15.4 A/B testing in shadow mode

Once two models exist (champion `v1.1.0` and challenger `v1.2.0`), serve them simultaneously in shadow mode. Score each on the same telemetry stream. Promote challenger only after 2+ weeks of stable improvement on agreed metrics.

---

## 16. 7-Day ML Execution Plan

| Day | Goal | Deliverable |
|---|---|---|
| **D1 (May 1)** | Skeleton + data pipeline scaffolding | `collect_episodes.py` runs end-to-end; produces 100 episodes; Parquet schema validated |
| **D2 (May 2)** | Train M3 + M4 (cheapest models) | `models/bc_init.pt` + `models/anomaly_ae.pt` saved; eval AUC >0.8 |
| **D3 (May 3)** | Train M2 forecaster + M1 PPO from BC init | `models/forecaster.pt` (val pinball <X) + `models/opti_twin_ppo.zip` (returns >scripted) |
| **D4 (May 4)** | Train M5 reward model + integrate forecast/anomaly into PPO obs | `models/reward_model.pt`; PPO retrained with augmented obs |
| **D5 (May 5)** | Eval-scenario harness + first regret analysis | `eval/benchmarks.py` produces the 10-scenario score table |
| **D6 (May 6)** | Hyperparameter search (Optuna) + final PPO run | `models/ppo/v1.0.0_demo/opti_twin_ppo.zip` frozen for demo |
| **D7 (May 7)** | Inference latency profiling, model-card writeup, demo dry-runs | Demo runs with all 5 models active end-to-end |

### Parallelism

D2 and D3 can be parallelised: M3 + M4 train on CPU while M1 + M2 use GPU. Keeps the team unblocked.

---

## 17. Risk Register (ML-Specific)

| ID | Risk | Mitigation |
|---|---|---|
| MR1 | PPO doesn't beat scripted policy | Ship scripted as the demo agent; PPO becomes "v2" stretch |
| MR2 | Forecaster overfits to simulator's tariff schedule | Use domain randomisation on tariff transitions |
| MR3 | Anomaly AE flags every TOU transition as anomalous | Train AE on TOU-mode episodes too; or condition on `tou_mode` flag |
| MR4 | BC init biases PPO away from exploration | Anneal entropy bonus higher early; short BC warm-start (10 epochs only) |
| MR5 | Reward model on synthetic preferences is meaningless | Document as such (plan.md §18 already does); don't over-claim |
| MR6 | Training crashes on team laptops without GPU | All five models trainable on CPU within 3 hours total |
| MR7 | Model files inflate repo > 100 MB | Track only the demo champion in git; rest in `.gitignore` |
| MR8 | Inference latency >5 ms causes dashboard lag | Quantise PPO to ONNX float16; cache forecast outputs across ticks |
| MR9 | Eval scenarios leak into training distribution | Hold S01–S10 RNG seeds out of all `collect_episodes.py` runs |
| MR10 | Action masking masks the wrong action and judges notice | Log every masked action to `decisions.jsonl` with masked-by reason |

---

## 18. References

### Reinforcement Learning
- Schulman et al. (2017). Proximal Policy Optimization Algorithms. arXiv:1707.06347.
- Sutton & Barto (2018). Reinforcement Learning: An Introduction (2nd ed.).
- Stable Baselines3 — <https://stable-baselines3.readthedocs.io/>
- Gymnasium — <https://gymnasium.farama.org/>

### Time-Series Forecasting
- Lim et al. (2021). Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting. International Journal of Forecasting.
- Oreshkin et al. (2020). N-BEATS: Neural basis expansion analysis. ICLR.

### Anomaly Detection
- An & Cho (2015). Variational Autoencoder based Anomaly Detection using Reconstruction Probability. SNU Data Mining Center.
- Munir et al. (2019). DeepAnT: A Deep Learning Approach for Unsupervised Anomaly Detection in Time Series. IEEE Access.

### Behaviour Cloning / Offline RL
- Pomerleau (1991). Efficient Training of Artificial Neural Networks for Autonomous Navigation.
- Levine et al. (2020). Offline Reinforcement Learning: Tutorial, Review, and Perspectives. arXiv:2005.01643.

### Preference Learning / RLHF
- Christiano et al. (2017). Deep Reinforcement Learning from Human Preferences. NeurIPS.
- Ouyang et al. (2022). Training language models to follow instructions with human feedback. NeurIPS.

### Industrial RL Applications
- Spielberg et al. (2017). Deep Reinforcement Learning Approaches for Process Control. IFAC.
- Powell (2023). RL for Process Industries — short review of EAF/cement applications.

### Egyptian Energy & Steel (already in plan.md §20)
- EgyptERA — Current Electricity Tariff Aug 2024
- IEA — Egypt country page
- World Steel Association — Energy fact sheet 2021
- Global Energy Monitor — Ezz Flat Steel Ain Sokhna plant
- AIST / Cappel — EAF Efficiency MENA 2021

### MLOps
- Sculley et al. (2015). Hidden Technical Debt in Machine Learning Systems. NeurIPS.
- Paleyes et al. (2022). Challenges in Deploying Machine Learning. ACM Computing Surveys.

---

*Built with ⚡ by Team Opti-Twin — NextCity AI Hack 2026*
*Five models, one factory, zero black boxes.*
