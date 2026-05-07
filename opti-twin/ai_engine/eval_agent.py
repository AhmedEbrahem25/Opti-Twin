"""
Eval harness — compares the trained PPO against the scripted policy across
seeded episodes. Prints a scoreboard:

  - mean total reward per episode
  - action distribution
  - crisis-handling rate (how often the policy emits the crisis-appropriate
    action when crisis_flags fire)

Demo gate: PPO mean reward must be ≥ scripted mean reward. If not, ship the
demo with the scripted policy (the env work is still durable).

Usage:
    python eval_agent.py                      # 100 episodes
    python eval_agent.py --episodes 30 --model models/opti_twin_ppo.zip
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from agent import OptiTwinAgent
from environment import ACTIONS, OptiTwinEAFEnv


def run_one_episode(env: OptiTwinEAFEnv, agent: OptiTwinAgent, seed: int) -> Tuple[float, Counter, Counter]:
    """Returns (total_reward, action_counts, crisis_handling_counts).

    crisis_handling_counts has 4 keys:
      - "wall_overheat_seen"     : ticks where wall_overheat fired
      - "wall_overheat_handled"  : of those, ticks where action == EMERGENCY_COOLING
      - "grid_spike_seen"        : ticks where grid_spike fired
      - "grid_spike_handled"     : of those, ticks where action == GRID_RIDE_THROUGH
    """
    obs, _ = env.reset(seed=seed)
    total = 0.0
    actions: Counter = Counter()
    crisis: Counter = Counter()
    while True:
        rec = agent.recommend(env._state)
        # Map back to env action id; if scripted emits a label not in ACTIONS, skip to HOLD.
        label = rec.action_label if rec.action_label in ACTIONS else "HOLD_STEADY"
        action_id = ACTIONS.index(label)
        actions[label] += 1

        flags = env._state.get("crisis_flags", {})
        if flags.get("wall_overheat"):
            crisis["wall_overheat_seen"] += 1
            if label == "EMERGENCY_COOLING":
                crisis["wall_overheat_handled"] += 1
        if flags.get("grid_spike"):
            crisis["grid_spike_seen"] += 1
            if label == "GRID_RIDE_THROUGH":
                crisis["grid_spike_handled"] += 1

        obs, r, term, trunc, _ = env.step(action_id)
        total += r
        if term or trunc:
            break
    return total, actions, crisis


def evaluate(label: str, agent: OptiTwinAgent, episodes: int, base_seed: int,
             *, forecaster=None, anomaly_detector=None) -> Dict:
    env = OptiTwinEAFEnv(forecaster=forecaster, anomaly_detector=anomaly_detector)
    rewards: List[float] = []
    actions: Counter = Counter()
    crisis: Counter = Counter()
    for ep in range(episodes):
        r, a, c = run_one_episode(env, agent, seed=base_seed + ep)
        rewards.append(r)
        actions.update(a)
        crisis.update(c)
    return {
        "label": label,
        "mean_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "actions": actions,
        "crisis": crisis,
    }


def _format_actions(counts: Counter) -> str:
    total = sum(counts.values()) or 1
    rows = [f"{lab:<22} {counts.get(lab, 0):6d}  ({counts.get(lab, 0)/total*100:5.1f}%)" for lab in ACTIONS]
    return "\n           ".join(rows)


def _format_crisis(c: Counter) -> str:
    wo_seen = c.get("wall_overheat_seen", 0)
    wo_h = c.get("wall_overheat_handled", 0)
    gs_seen = c.get("grid_spike_seen", 0)
    gs_h = c.get("grid_spike_handled", 0)
    wo_rate = wo_h / wo_seen * 100 if wo_seen else float("nan")
    gs_rate = gs_h / gs_seen * 100 if gs_seen else float("nan")
    return (
        f"wall_overheat: {wo_h}/{wo_seen} handled ({wo_rate:.0f}%)  |  "
        f"grid_spike: {gs_h}/{gs_seen} handled ({gs_rate:.0f}%)"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=100)
    p.add_argument("--model", default=str(HERE / "models" / "opti_twin_ppo.zip"))
    p.add_argument("--seed", type=int, default=1000)
    p.add_argument("--forecaster", default=None,
                   help="Path to M2 forecaster directory (matches training conditions)")
    p.add_argument("--anomaly", default=None,
                   help="Path to M3 anomaly detector directory (matches training conditions)")
    args = p.parse_args()

    forecaster = None
    anomaly_det = None
    if args.forecaster:
        from forecaster.lstm_forecaster import load_forecaster
        forecaster = load_forecaster(args.forecaster)
    if args.anomaly:
        from anomaly.autoencoder import load_anomaly_detector
        anomaly_det = load_anomaly_detector(args.anomaly)

    print(f"[eval] {args.episodes} episodes  base_seed={args.seed}")

    print("[eval] running scripted-policy baseline...")
    scripted = OptiTwinAgent(model_path=None)  # forces fallback
    scr_results = evaluate("scripted", scripted, args.episodes, args.seed,
                           forecaster=forecaster, anomaly_detector=anomaly_det)

    print(f"[eval] running PPO from {args.model}...")
    ppo_agent = OptiTwinAgent(model_path=args.model)
    if ppo_agent.model is None:
        print(f"[eval] WARNING: PPO model not loaded; both columns will be scripted.")
    ppo_results = evaluate("ppo", ppo_agent, args.episodes, args.seed,
                           forecaster=forecaster, anomaly_detector=anomaly_det)

    print()
    print("=" * 78)
    print(f"{'metric':<28} {'scripted':>20} {'ppo':>20}")
    print("=" * 78)
    print(f"{'mean reward':<28} {scr_results['mean_reward']:>20.2f} {ppo_results['mean_reward']:>20.2f}")
    print(f"{'std reward':<28} {scr_results['std_reward']:>20.2f} {ppo_results['std_reward']:>20.2f}")
    print()
    print("action distribution:")
    print(f"  scripted: {_format_actions(scr_results['actions'])}")
    print()
    print(f"  ppo:      {_format_actions(ppo_results['actions'])}")
    print()
    print(f"crisis-handling rate:")
    print(f"  scripted: {_format_crisis(scr_results['crisis'])}")
    print(f"  ppo:      {_format_crisis(ppo_results['crisis'])}")
    print("=" * 78)
    delta = ppo_results['mean_reward'] - scr_results['mean_reward']
    if ppo_results['mean_reward'] >= scr_results['mean_reward']:
        print(f"[gate] PPO >= scripted by {delta:+.2f} -- OK to ship")
    else:
        print(f"[gate] PPO < scripted by {delta:+.2f} -- fall back to scripted policy for demo")


if __name__ == "__main__":
    main()
