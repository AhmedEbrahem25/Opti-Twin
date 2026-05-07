# Models directory

Mounted at `/app/models` inside the `ai_engine` container.

## Layout (planing-v2.md §15.1)

```
models/
├── ppo/                          # PPO policies (M1)
│   ├── v0.1.0_bc-init_seed42/    # 32-D obs, BC-init only
│   ├── v0.2.0_full-stack_seed42/ # 39-D obs, M2/M3 active
│   ├── v0.2.1_low-entropy_seed42/# tuning experiment
│   └── v1.0.0_demo/              # final demo build (Optuna-tuned, 300K steps)
├── forecaster/                   # M2 LSTM
│   └── v0.1.0/                   # forecaster.pt + feature_columns.json
├── anomaly/                      # M3 autoencoder
│   └── v0.1.0/                   # autoencoder.pt + threshold.json
├── bc/                           # M4 warm-start
│   ├── v0.1.0/                   # 32-D legacy
│   └── v0.2.0/                   # 39-D current
├── reward_model/                 # M5 preference model
│   └── v0.1.0/                   # reward_model.pt + meta.json
└── opti_twin_ppo.zip             # symlink/copy: agent_service loads this path
```

## Active demo state

`agent_service.py` loads `MODEL_PATH` (default `/app/models/opti_twin_ppo.zip`).
For the demo:
1. Copy or symlink `models/ppo/v1.0.0_demo/opti_twin_ppo.zip` to `models/opti_twin_ppo.zip`.
2. Set `FORECASTER_PATH=/app/models/forecaster/v0.1.0` (default).
3. Set `ANOMALY_PATH=/app/models/anomaly/v0.1.0` (default).

If `opti_twin_ppo.zip` is absent, the agent logs *"using scripted fallback policy"*
and runs the deterministic scripted decision tree -- safety mask + LLM XAI still
layer on top. This is the fallback in planing-v2.md §17 risk MR1.

## Demo gates

A new PPO checkpoint can replace the demo only if `eval/check_gates.py` exits
zero on the scoreboard JSON. Gates per planing-v2.md §12.4:

1. PPO wins >= 7 of 10 scenarios.
2. Zero PPO safety breaches across the scoreboard.
3. PPO total reward not negative on any scenario.
4. p99 inference latency < 5 ms (`python -m eval.latency`).

## Model versioning rules

- `current` should be a copy or symlink, never the canonical artefact location.
- Each checkpoint dir contains `model_card.md`, `metrics.json` (the relevant
  scoreboard slice), and `tuned_params.json` (when Optuna was used).
- Files larger than 100 MB are not tracked in git -- see `.gitignore`.

## Phase 0 fix history

- 2026-05-07 -- env `production_backlog` accumulator wired to arc-power-driven
  heat progress; per-step `production_delay_penalty` coefficient rescaled
  500.0 -> 5.0 to match the realistic backlog amplitude. See
  `reward_function.py` and `environment.py` for details.
