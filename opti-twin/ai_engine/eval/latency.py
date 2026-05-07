"""Latency profiler for the live recommendation path (planing-v2.md §12.4 gate).

Times `agent.recommend(state)` end-to-end (includes M2/M3 inference, safety
mask, XAI template). Reports p50/p95/p99/max over `--n-calls` ticks.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List

HERE = Path(__file__).resolve().parent
ENGINE_DIR = HERE.parent
sys.path.insert(0, str(ENGINE_DIR))

import numpy as np

from agent import OptiTwinAgent
from environment import OptiTwinEAFEnv


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=str(ENGINE_DIR / "models" / "opti_twin_ppo.zip"))
    p.add_argument("--forecaster", default=str(ENGINE_DIR / "models" / "forecaster" / "v0.1.0"))
    p.add_argument("--anomaly", default=str(ENGINE_DIR / "models" / "anomaly" / "v0.1.0"))
    p.add_argument("--n-calls", type=int, default=10_000)
    p.add_argument("--out", default=str(HERE / "results" / "latency.json"))
    args = p.parse_args()

    agent = OptiTwinAgent(
        model_path=args.model if Path(args.model).exists() else None,
        forecaster_path=args.forecaster if Path(args.forecaster).exists() else None,
        anomaly_path=args.anomaly if Path(args.anomaly).exists() else None,
    )

    # Drive a real env so M2/M3 windows fill realistically.
    env = OptiTwinEAFEnv()
    env.reset(seed=999)

    timings: List[float] = []
    last_state = env._state.copy()
    for tick in range(args.n_calls):
        t0 = time.perf_counter()
        agent.recommend(last_state)
        timings.append((time.perf_counter() - t0) * 1000.0)
        # Step env to advance state for the next tick.
        env.step(0)
        last_state = env._state.copy()
        # Reset every episode so M2/M3 windows reinitialise periodically.
        if env._step >= env._max_steps - 1:
            env.reset(seed=999 + tick)
            last_state = env._state.copy()

    arr = np.array(timings)
    summary = {
        "model": args.model,
        "n_calls": int(len(arr)),
        "p50_ms": float(np.percentile(arr, 50)),
        "p95_ms": float(np.percentile(arr, 95)),
        "p99_ms": float(np.percentile(arr, 99)),
        "max_ms": float(arr.max()),
        "mean_ms": float(arr.mean()),
        "gate_5ms_p99": bool(np.percentile(arr, 99) < 5.0),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2))

    print(f"[latency] n={summary['n_calls']}  "
          f"p50={summary['p50_ms']:.2f}ms  p95={summary['p95_ms']:.2f}ms  "
          f"p99={summary['p99_ms']:.2f}ms  max={summary['max_ms']:.2f}ms")
    print(f"[latency] gate (p99 < 5ms): {'PASS' if summary['gate_5ms_p99'] else 'FAIL'}")
    print(f"[latency] saved -> {out_path}")


if __name__ == "__main__":
    main()
