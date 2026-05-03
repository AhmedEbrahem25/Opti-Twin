# Models directory

Mounted at `/app/models` inside the `ai_engine` container.

## Demo state (2026-05-03)

The trained PPO checkpoint at `opti_twin_ppo.zip.untrained_demo` is parked, not active. The eval harness (`eval_agent.py`) showed it underperforming the scripted policy on the seeded eval set (mean reward 285 vs 843).

**Root cause:** the training env's reward function has no production-rate signal — `production_delay_penalty` keys off `production_backlog`, which the env's `step()` never increments. PPO exploited this by hammering `TRANSFORMER_DERATE` (which caps arc at 75 MW) for cheap energy savings, at the cost of crisis-handling and PF-correction coverage.

**Demo behaviour:** with no `opti_twin_ppo.zip` present, `OptiTwinAgent` (`agent.py:65`) logs *"No PPO model found ... using scripted fallback policy"* and runs the deterministic scripted decision tree — which is what every prior demo iteration ran on. Safety mask + LLM XAI both layer on top regardless of which policy underlies them.

## To re-enable a trained PPO

1. Fix the env reward signal to penalise low arc when the heat needs to progress and when no crisis is active. See `environment.py:_RELEVANT_STATE_KEYS` plus `reward_function.compute_reward`.
2. Re-run `python train_ppo.py` (inside `docker compose run --rm --no-deps ai_engine`).
3. Re-run `python eval_agent.py` and confirm the gate prints `PPO ≥ scripted`.
4. Move the file back: rename `opti_twin_ppo.zip.untrained_demo` (or the freshly-trained zip) to `opti_twin_ppo.zip`.

## Files in this directory

| File | Description |
|---|---|
| `opti_twin_ppo.zip` | Active PPO checkpoint loaded at container startup. Absent in demo state. |
| `opti_twin_ppo.zip.untrained_demo` | Parked checkpoint from the 2026-05-03 200K-step run; underperforms scripted. |
| `.gitkeep` | Keeps the directory under version control. |
