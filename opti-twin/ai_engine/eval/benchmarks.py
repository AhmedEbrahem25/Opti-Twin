"""10-scenario eval scoreboard (planing-v2.md §12).

Runs scripted and PPO against the same scenarios under identical seeds and
crisis schedules, and emits a JSON scoreboard with the metric families from
planing-v2.md §12.2.

Usage:
    python -m eval.benchmarks --model models/ppo/v0.2.1_low-entropy_seed42/opti_twin_ppo.zip
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
ENGINE_DIR = HERE.parent
sys.path.insert(0, str(ENGINE_DIR))

import numpy as np

from agent import OptiTwinAgent
from environment import ACTIONS, OptiTwinEAFEnv

SCENARIOS_DIR = HERE / "scenarios"


def load_scenarios() -> List[Dict[str, Any]]:
    files = sorted(SCENARIOS_DIR.glob("S*.json"))
    return [json.loads(p.read_text()) for p in files]


def _apply_initial_overrides(env: OptiTwinEAFEnv, overrides: Dict[str, Any]) -> None:
    for k, v in overrides.items():
        env._state[k] = v


def _maybe_inject_crisis(env: OptiTwinEAFEnv, schedule: List[Dict], tick: int) -> None:
    """Force-inject crises by patching state directly. Mirrors env's stochastic
    injection but is deterministic."""
    for ev in schedule:
        if int(ev["tick"]) != tick:
            continue
        kind = ev["type"]
        mag = float(ev.get("magnitude", 1.0))
        flags = env._state["crisis_flags"]
        if kind == "wall_overheat":
            env._state["wall_panel_temp"] = float(env._state["wall_panel_temp"]) + mag
            flags["wall_overheat"] = True
        elif kind == "grid_spike":
            env._state["grid_frequency"] = 50.0 - mag
            env._grid_spike_ticks_remaining = max(env._grid_spike_ticks_remaining, 5)
            flags["grid_spike"] = True
        elif kind == "transformer_alarm":
            flags["transformer_alarm"] = True
        elif kind == "electrode_consumption":
            env._state["electrode_consumption_kg"] = mag
        elif kind == "forecast_dropout":
            # Stale forecast: clear cache; agent should fall back to live price.
            from environment import _forecast_cache, _forecast_lock  # noqa
            with _forecast_lock:
                _forecast_cache.clear()


def run_scenario(
    sc: Dict[str, Any],
    agent: OptiTwinAgent,
    *,
    forecaster=None,
    anomaly_detector=None,
) -> Dict[str, Any]:
    env = OptiTwinEAFEnv(
        forecaster=forecaster,
        anomaly_detector=anomaly_detector,
        difficulty=sc.get("difficulty", "medium"),
    )
    env._max_steps = int(sc.get("duration_steps", 480))
    env.reset(seed=int(sc["seed"]))
    _apply_initial_overrides(env, sc.get("initial_state_overrides", {}))

    schedule = sc.get("crisis_schedule", [])

    actions: Counter = Counter()
    safety_breaches = 0
    quality_steps = 0
    pf_violations = 0
    total_reward = 0.0
    total_energy_savings = 0.0
    bath_below_floor = 0
    rec_latencies_ms: List[float] = []

    for tick in range(env._max_steps):
        _maybe_inject_crisis(env, schedule, tick)

        t0 = time.perf_counter()
        rec = agent.recommend(env._state)
        rec_latencies_ms.append((time.perf_counter() - t0) * 1000.0)

        label = rec.action_label if rec.action_label in ACTIONS else "HOLD_STEADY"
        actions[label] += 1
        action_id = ACTIONS.index(label)

        # Step + reward
        _, reward, term, trunc, info = env.step(action_id)
        total_reward += float(reward)

        rc = info.get("reward_components", {})
        total_energy_savings += float(rc.get("energy_savings_egp", 0.0))
        if rc.get("quality_bonus", 0.0) > 0.5:
            quality_steps += 1
        if env._state.get("wall_panel_temp", 0.0) >= 250.0 and label != "EMERGENCY_COOLING":
            safety_breaches += 1
        if env._state.get("furnace_bath_temp", 1600.0) < 1500.0:
            bath_below_floor += 1
        if env._state.get("power_factor", 0.92) < 0.92 and env._state.get("arc_power_mw", 0.0) * 1000.0 > 500.0:
            pf_violations += 1

        if term or trunc:
            break

    return {
        "scenario_id": sc["id"],
        "scenario_name": sc["name"],
        "mean_reward": total_reward / max(1, env._step),
        "total_reward": total_reward,
        "total_energy_savings_egp": total_energy_savings,
        "quality_steps": quality_steps,
        "pf_violations": pf_violations,
        "safety_breaches": safety_breaches,
        "bath_below_floor_ticks": bath_below_floor,
        "heats_completed": int(env._state.get("batches_today", 0)),
        "final_backlog": int(env._state.get("production_backlog", 0)),
        "actions": dict(actions),
        "latency_ms_p50": float(np.percentile(rec_latencies_ms, 50)) if rec_latencies_ms else 0.0,
        "latency_ms_p99": float(np.percentile(rec_latencies_ms, 99)) if rec_latencies_ms else 0.0,
    }


def score_table(scripted_results: List[Dict], ppo_results: List[Dict]) -> Dict[str, Any]:
    """Side-by-side scoreboard. PPO wins a scenario when its total_reward
    is >= scripted's AND it has zero new safety breaches."""
    rows = []
    ppo_wins = 0
    safety_breaches_total = 0
    for s, p in zip(scripted_results, ppo_results):
        ppo_won = (p["total_reward"] >= s["total_reward"]) and (p["safety_breaches"] == 0)
        if ppo_won:
            ppo_wins += 1
        safety_breaches_total += int(p["safety_breaches"])
        rows.append({
            "id": s["scenario_id"],
            "name": s["scenario_name"],
            "scripted_total": round(float(s["total_reward"]), 2),
            "ppo_total": round(float(p["total_reward"]), 2),
            "delta": round(float(p["total_reward"] - s["total_reward"]), 2),
            "ppo_won": ppo_won,
            "ppo_safety_breaches": int(p["safety_breaches"]),
            "ppo_p99_ms": round(p["latency_ms_p99"], 2),
        })
    return {
        "rows": rows,
        "ppo_scenario_wins": ppo_wins,
        "ppo_total_safety_breaches": safety_breaches_total,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=str(ENGINE_DIR / "models" / "opti_twin_ppo.zip"))
    p.add_argument("--forecaster", default=str(ENGINE_DIR / "models" / "forecaster" / "v0.1.0"))
    p.add_argument("--anomaly", default=str(ENGINE_DIR / "models" / "anomaly" / "v0.1.0"))
    p.add_argument("--out", default=str(HERE / "results" / "scoreboard.json"))
    args = p.parse_args()

    forecaster = None
    anomaly_det = None
    if args.forecaster and Path(args.forecaster).exists():
        from forecaster.lstm_forecaster import load_forecaster
        forecaster = load_forecaster(args.forecaster)
    if args.anomaly and Path(args.anomaly).exists():
        from anomaly.autoencoder import load_anomaly_detector
        anomaly_det = load_anomaly_detector(args.anomaly)

    scenarios = load_scenarios()
    print(f"[bench] running {len(scenarios)} scenarios")

    print("[bench] scripted...")
    scripted = OptiTwinAgent(model_path=None,
                             forecaster_path=args.forecaster,
                             anomaly_path=args.anomaly)
    scripted_results = [
        run_scenario(sc, scripted, forecaster=forecaster, anomaly_detector=anomaly_det)
        for sc in scenarios
    ]

    print(f"[bench] PPO from {args.model}")
    ppo = OptiTwinAgent(model_path=args.model,
                        forecaster_path=args.forecaster,
                        anomaly_path=args.anomaly)
    ppo_results = [
        run_scenario(sc, ppo, forecaster=forecaster, anomaly_detector=anomaly_det)
        for sc in scenarios
    ]

    table = score_table(scripted_results, ppo_results)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "model": args.model,
        "n_scenarios": len(scenarios),
        "summary": table,
        "scripted": scripted_results,
        "ppo": ppo_results,
    }, indent=2))

    print()
    print("=" * 90)
    print(f"{'id':<5} {'name':<48} {'scripted':>11} {'ppo':>11} {'delta':>11} {'won':>6}")
    print("=" * 90)
    for row in table["rows"]:
        won = "yes" if row["ppo_won"] else "no"
        print(
            f"{row['id']:<5} {row['name'][:48]:<48} "
            f"{row['scripted_total']:>11.2f} {row['ppo_total']:>11.2f} {row['delta']:>11.2f} {won:>6}"
        )
    print("=" * 90)
    print(f"PPO scenario wins: {table['ppo_scenario_wins']}/{len(scenarios)}")
    print(f"PPO total safety breaches: {table['ppo_total_safety_breaches']}")
    print(f"Wrote scoreboard -> {out_path}")


if __name__ == "__main__":
    main()
