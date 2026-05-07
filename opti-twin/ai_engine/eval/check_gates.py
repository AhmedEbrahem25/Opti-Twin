"""Pre-merge gate checker (planing-v2.md §12.4).

Reads a scoreboard JSON and exits non-zero unless ALL gates pass:
  1. PPO wins >= 7 of 10 scenarios.
  2. Zero PPO safety breaches across the whole scoreboard.
  3. PPO total reward not negative on any scenario.
  4. p99 inference latency < 5 ms on every scenario.

Usage:
    python -m eval.check_gates eval/results/scoreboard.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

GATE_MIN_WINS = 7
GATE_MAX_LATENCY_MS = 5.0


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m eval.check_gates <scoreboard.json>")
        return 2
    payload = json.loads(Path(sys.argv[1]).read_text())
    summary = payload["summary"]
    rows = summary["rows"]
    ppo = payload["ppo"]

    failures: list[str] = []
    if summary["ppo_scenario_wins"] < GATE_MIN_WINS:
        failures.append(f"wins {summary['ppo_scenario_wins']}/{len(rows)} < {GATE_MIN_WINS}")
    if summary["ppo_total_safety_breaches"] > 0:
        failures.append(f"safety breaches: {summary['ppo_total_safety_breaches']}")
    for r, full in zip(rows, ppo):
        if r["ppo_total"] < 0:
            failures.append(f"{r['id']}: PPO total reward negative ({r['ppo_total']})")
        if r["ppo_p99_ms"] >= GATE_MAX_LATENCY_MS:
            failures.append(f"{r['id']}: p99 latency {r['ppo_p99_ms']}ms >= {GATE_MAX_LATENCY_MS}")

    if failures:
        print("[gates] FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("[gates] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
