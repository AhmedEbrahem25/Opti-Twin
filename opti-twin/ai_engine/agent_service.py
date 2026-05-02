"""
AI Engine service entry-point.

Subscribes to the `factory.telemetry` Redis channel, computes a recommendation
for each frame, publishes:
  - `ai.recommendation`   — for the backend to broadcast over WS
  - `sim.control`         — for the simulator to apply (when AI toggle is ON)
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
import threading
import time
from typing import Any, Dict, Optional

import redis

from agent import OptiTwinAgent
from environment import update_forecast_cache
from reward_function import RewardWeights


REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/opti_twin_ppo.zip")


def make_weights_from_env() -> RewardWeights:
    return RewardWeights(
        alpha=float(os.getenv("RL_ALPHA", "1.0")),
        beta=float(os.getenv("RL_BETA", "0.9")),
        gamma=float(os.getenv("RL_GAMMA", "1.8")),
        delta=float(os.getenv("RL_DELTA", "0.7")),
        epsilon=float(os.getenv("RL_EPSILON", "0.5")),
        zeta=float(os.getenv("RL_ZETA", "0.8")),
    )


class AIService:
    def __init__(self, r: redis.Redis, agent: OptiTwinAgent) -> None:
        self.r = r
        self.agent = agent
        self.ai_enabled = False  # toggled by /api/v1/ai/toggle
        self._lock = threading.Lock()

    # ---- Profile / weights / toggle handling ----
    def handle_control(self, data: Dict[str, Any]) -> None:
        with self._lock:
            action = data.get("action")
            if action == "ai_toggle":
                self.ai_enabled = bool(data.get("enabled"))
                print(f"[ai] enabled={self.ai_enabled}", flush=True)
                # Forward to simulator so it knows to clear AI override on OFF
                self.r.publish("sim.control", json.dumps({
                    "action": "ai_toggle",
                    "enabled": self.ai_enabled,
                }))
            elif action == "set_profile":
                profile = data.get("profile", "default")
                self.agent.update_weights(RewardWeights.preset(profile))
                print(f"[ai] reward profile -> {profile}", flush=True)
            elif action == "tou_mode":
                # Just forward to simulator
                self.r.publish("sim.control", json.dumps(data))

    def control_listener(self) -> None:
        pubsub = self.r.pubsub()
        pubsub.subscribe("ai.control")
        for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                data = json.loads(msg["data"])
            except Exception:
                continue
            self.handle_control(data)

    def pricing_listener(self) -> None:
        """Subscribe to pricing.forecast and update the observation cache."""
        pubsub = self.r.pubsub()
        pubsub.subscribe("pricing.forecast")
        print("[ai] subscribed to pricing.forecast", flush=True)
        for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                data = json.loads(msg["data"])
                update_forecast_cache(data)
            except Exception:
                pass

    # ---- Telemetry → recommendation ----
    def telemetry_loop(self) -> None:
        pubsub = self.r.pubsub()
        pubsub.subscribe("factory.telemetry")
        print("[ai] subscribed to factory.telemetry", flush=True)
        for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                state = json.loads(msg["data"])
            except Exception as exc:
                print(f"[ai] bad telemetry: {exc}", flush=True)
                continue

            rec = self.agent.recommend(state)
            payload = {
                "timestamp": state.get("timestamp"),
                "machine_id": state.get("machine_id"),
                "action_label": rec.action_label,
                "action_magnitude_pct": rec.action_magnitude_pct,
                "estimated_savings_egp_per_hour": rec.estimated_savings_egp_per_hour,
                "pf_penalty_avoided_egp": rec.pf_penalty_avoided_egp,
                "co2_saved_kg": rec.co2_saved_kg,
                "xai_reason": rec.xai_reason_en,
                "xai_reason_ar": rec.xai_reason_ar,
                "machine_health": rec.machine_health,
                "production_status": rec.production_status,
                "reward_components": rec.reward_components,
                "dominant_reason": rec.dominant_reason,
                "ai_enabled": self.ai_enabled,
            }

            # Always broadcast recommendation (so dashboard can show it greyed-out
            # when AI is off — useful for "compare" view).
            try:
                self.r.publish("ai.recommendation", json.dumps(payload))
            except Exception as exc:
                print(f"[ai] publish recommendation failed: {exc}", flush=True)

            # Apply to simulator only when AI is enabled
            if self.ai_enabled and rec.action_label != "HOLD_STEADY":
                ctrl = {
                    "action": "ai_recommendation",
                    "recommendation": {
                        "arc_power_mw": rec.arc_power_mw,
                        "cooling_lmin": rec.cooling_lmin,
                        "reactive_comp_mvar": rec.reactive_comp_mvar,
                    },
                }
                try:
                    self.r.publish("sim.control", json.dumps(ctrl))
                except Exception as exc:
                    print(f"[ai] publish sim.control failed: {exc}", flush=True)


def main() -> None:
    print("[ai] Opti-Twin AI engine starting...", flush=True)
    weights = make_weights_from_env()
    agent = OptiTwinAgent(weights=weights, model_path=MODEL_PATH)

    for attempt in range(20):
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            r.ping()
            print(f"[ai] connected to Redis at {REDIS_HOST}:{REDIS_PORT}", flush=True)
            break
        except Exception as exc:
            print(f"[ai] redis not ready ({exc}), retry {attempt+1}/20", flush=True)
            time.sleep(2)
    else:
        print("[ai] FATAL: cannot reach Redis", flush=True)
        sys.exit(1)

    svc = AIService(r, agent)

    # Spawn control + pricing listeners
    threading.Thread(target=svc.control_listener, daemon=True).start()
    threading.Thread(target=svc.pricing_listener, daemon=True).start()

    # Telemetry consumer (main thread)
    svc.telemetry_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[ai] stopped by user", flush=True)
