"""Roll out the simulator and persist transitions to Parquet.

Replaces the inline BC-rollout step in `train_ppo.py:collect_bc_dataset`.
Output: one Parquet file per episode under `data/raw/{difficulty}/`.

Usage:
    python collect_episodes.py --n-episodes 200 --difficulty medium
    python collect_episodes.py --n-episodes 50  --difficulty hard --seed 9000
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pandas as pd

from agent import OptiTwinAgent
from data_pipeline.schema import Difficulty, TransitionRecord
from environment import ACTIONS, OptiTwinEAFEnv

DEFAULT_OUT_ROOT = HERE.parent / "data" / "raw"

# Eval scenarios reserve their own seed namespace so they never leak into training.
# Anything in [EVAL_SEED_FLOOR, EVAL_SEED_FLOOR + EVAL_SEED_RESERVE) is excluded.
EVAL_SEED_FLOOR = 1_000_000
EVAL_SEED_RESERVE = 10_000


def _bump_past_eval_seeds(seed: int) -> int:
    """Skip the eval-seed reservation window if the requested seed lands inside it."""
    if EVAL_SEED_FLOOR <= seed < EVAL_SEED_FLOOR + EVAL_SEED_RESERVE:
        return EVAL_SEED_FLOOR + EVAL_SEED_RESERVE + (seed - EVAL_SEED_FLOOR)
    return seed


def collect_one_episode(
    *,
    episode_id: int,
    seed: int,
    difficulty: Difficulty,
    teacher: OptiTwinAgent,
    env: OptiTwinEAFEnv,
) -> List[TransitionRecord]:
    """Roll the scripted teacher through one episode; return the transitions."""
    rows: List[TransitionRecord] = []
    obs, _ = env.reset(seed=seed)
    step_id = 0
    while True:
        # Snapshot the state BEFORE step() mutates it -- this is what the policy
        # observed and what produces the action.
        state_snapshot = dict(env._state)
        # Deep-copy the crisis_flags subdict (env.step mutates it in place).
        state_snapshot["crisis_flags"] = dict(state_snapshot.get("crisis_flags", {}))

        label = teacher._scripted_policy(env._state)
        if label not in ACTIONS:
            label = "HOLD_STEADY"
        action_id = ACTIONS.index(label)

        _, reward, terminated, truncated, info = env.step(action_id)

        rows.append(TransitionRecord.from_state(
            state_snapshot,
            episode_id=episode_id,
            step_id=step_id,
            difficulty=difficulty,
            ts=time.time(),
            action_label=label,
            action_id=action_id,
            reward_total=float(reward),
            reward_components=dict(info.get("reward_components", {})),
        ))
        step_id += 1
        if terminated or truncated:
            break
    return rows


def write_episode_parquet(rows: List[TransitionRecord], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([r.model_dump() for r in rows])
    # Pyarrow can't serialise dicts of floats by default -- flatten reward_components.
    rc_keys = sorted({k for rc in df["reward_components"] for k in rc.keys()})
    for k in rc_keys:
        df[f"rc_{k}"] = df["reward_components"].apply(lambda rc: float(rc.get(k, 0.0)))
    df = df.drop(columns=["reward_components"])
    df.to_parquet(out_path, index=False)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--n-episodes", type=int, default=100)
    p.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")
    p.add_argument("--seed", type=int, default=42, help="base seed (incremented per episode)")
    p.add_argument("--out", default=str(DEFAULT_OUT_ROOT))
    args = p.parse_args()

    out_dir = Path(args.out) / args.difficulty
    out_dir.mkdir(parents=True, exist_ok=True)

    teacher = OptiTwinAgent(model_path=None)  # forces scripted fallback
    env = OptiTwinEAFEnv()

    print(f"[collect] {args.n_episodes} episodes  difficulty={args.difficulty}  out={out_dir}")
    t0 = time.time()
    total_rows = 0
    for i in range(args.n_episodes):
        seed = _bump_past_eval_seeds(args.seed + i)
        # Use the (post-bump) seed as the canonical episode_id so multiple
        # collection runs into the same difficulty bucket don't collide.
        rows = collect_one_episode(
            episode_id=seed,
            seed=seed,
            difficulty=args.difficulty,
            teacher=teacher,
            env=env,
        )
        write_episode_parquet(rows, out_dir / f"episode_{seed:08d}.parquet")
        total_rows += len(rows)
        if (i + 1) % 25 == 0:
            elapsed = time.time() - t0
            print(f"[collect] {i+1}/{args.n_episodes} eps  {total_rows} rows  ({elapsed:.1f}s)")
    print(f"[collect] done -- {total_rows} rows in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
