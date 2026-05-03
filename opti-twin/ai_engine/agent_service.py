"""
AI Engine service entry-point.

Subscribes to the `factory.telemetry` Redis channel, computes a recommendation
for each frame, publishes:
  - `ai.recommendation`   — for the backend to broadcast over WS
  - `sim.control`         — for the simulator to apply (when AI toggle is ON)
  - `opti-twin.logs`      — structured log stream for backend aggregation
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from typing import Any, Dict, Optional

import redis

import logger as _logger_mod
from agent import OptiTwinAgent
from environment import update_forecast_cache
from llm_xai import LLMXAIWorker, XAIJob, excerpt_state
from reward_function import RewardWeights

REDIS_HOST  = os.getenv("REDIS_HOST", "redis")
REDIS_PORT  = int(os.getenv("REDIS_PORT", "6379"))
MODEL_PATH  = os.getenv("MODEL_PATH", "/app/models/opti_twin_ppo.zip")

log: Any = None  # set after Redis connect in main()


def make_weights_from_env() -> RewardWeights:
    return RewardWeights(
        alpha=float(os.getenv("RL_ALPHA", "1.0")),
        beta=float(os.getenv("RL_BETA", "0.9")),
        gamma=float(os.getenv("RL_GAMMA", "1.8")),
        delta=float(os.getenv("RL_DELTA", "0.7")),
        epsilon=float(os.getenv("RL_EPSILON", "0.5")),
        zeta=float(os.getenv("RL_ZETA", "0.8")),
    )


SAFETY_ROLLBACK_THRESHOLD = 3  # planing-v2.md §13.3


class AIService:
    def __init__(self, r: redis.Redis, agent: OptiTwinAgent) -> None:
        self.r     = r
        self.agent = agent
        self.ai_enabled = False
        self._lock = threading.Lock()
        self._rec_count  = 0
        self._hold_count = 0
        self._consecutive_overrides = 0
        self._rollback_announced = False  # latch so we emit one event per streak
        self._last_action_label: Optional[str] = None
        self.llm_xai = LLMXAIWorker(r)
        self.llm_xai.start()

    # ── Control channel ───────────────────────────────────────────────────────

    def handle_control(self, data: Dict[str, Any]) -> None:
        with self._lock:
            action = data.get("action")
            if action == "ai_toggle":
                self.ai_enabled = bool(data.get("enabled"))
                log.info("AI toggled → enabled=%s", self.ai_enabled)
                self.r.publish("sim.control", json.dumps({
                    "action": "ai_toggle",
                    "enabled": self.ai_enabled,
                }))
            elif action == "set_profile":
                profile = data.get("profile", "default")
                self.agent.update_weights(RewardWeights.preset(profile))
                log.info("Reward profile → %s", profile)
            elif action == "tou_mode":
                self.r.publish("sim.control", json.dumps(data))
                log.debug("TOU mode forwarded to simulator: %s", data.get("enabled"))

    def control_listener(self) -> None:
        pubsub = self.r.pubsub()
        pubsub.subscribe("ai.control")
        log.info("Subscribed to ai.control")
        for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                data = json.loads(msg["data"])
            except Exception:
                continue
            self.handle_control(data)

    def pricing_listener(self) -> None:
        pubsub = self.r.pubsub()
        pubsub.subscribe("pricing.forecast")
        log.info("Subscribed to pricing.forecast")
        for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                data = json.loads(msg["data"])
                update_forecast_cache(data)
                log.debug("Forecast cache updated — steps=%d", len(data.get("forecast", [])))
            except Exception as exc:
                log.warning("pricing_listener error: %s", exc)

    # ── Telemetry → recommendation ─────────────────────────────────────────────

    def telemetry_loop(self) -> None:
        pubsub = self.r.pubsub()
        pubsub.subscribe("factory.telemetry")
        log.info("Subscribed to factory.telemetry — waiting for frames")
        for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                state = json.loads(msg["data"])
            except Exception as exc:
                log.error("Bad telemetry frame: %s", exc)
                continue

            rec = self.agent.recommend(state)
            self._rec_count += 1

            # Track consecutive safety overrides — emit a rollback event on streaks
            # past the threshold (planing-v2.md §13.3).
            if rec.safety_overridden:
                self._consecutive_overrides += 1
                if (
                    self._consecutive_overrides >= SAFETY_ROLLBACK_THRESHOLD
                    and not self._rollback_announced
                ):
                    rollback_payload = {
                        "timestamp": state.get("timestamp"),
                        "machine_id": state.get("machine_id"),
                        "consecutive_overrides": self._consecutive_overrides,
                        "reason": rec.safety_reason,
                        "level": "critical",
                    }
                    try:
                        self.r.publish("ai.safety_rollback", json.dumps(rollback_payload))
                        log.warning(
                            "Safety rollback announced — %d consecutive overrides (reason=%s)",
                            self._consecutive_overrides, rec.safety_reason,
                        )
                    except Exception as exc:
                        log.error("Publish ai.safety_rollback failed: %s", exc)
                    self._rollback_announced = True
            else:
                self._consecutive_overrides = 0
                self._rollback_announced = False

            # Enqueue LLM XAI enrichment ONLY on action transitions, so we don't
            # call the LLM on every HOLD_STEADY tick. No-op if worker disabled.
            if rec.action_label != self._last_action_label:
                self.llm_xai.submit(XAIJob(
                    timestamp=state.get("timestamp"),
                    machine_id=state.get("machine_id"),
                    action_label=rec.action_label,
                    raw_action_label=rec.raw_action_label,
                    safety_overridden=rec.safety_overridden,
                    safety_reason=rec.safety_reason,
                    dominant_reason=rec.dominant_reason,
                    machine_health=rec.machine_health,
                    reward_components=rec.reward_components,
                    state_excerpt=excerpt_state(state),
                ))
                self._last_action_label = rec.action_label

            payload = {
                "timestamp":                     state.get("timestamp"),
                "machine_id":                    state.get("machine_id"),
                "action_label":                  rec.action_label,
                "action_magnitude_pct":          rec.action_magnitude_pct,
                "estimated_savings_egp_per_hour": rec.estimated_savings_egp_per_hour,
                "pf_penalty_avoided_egp":        rec.pf_penalty_avoided_egp,
                "co2_saved_kg":                  rec.co2_saved_kg,
                "xai_reason":                    rec.xai_reason_en,
                "xai_reason_ar":                 rec.xai_reason_ar,
                "machine_health":                rec.machine_health,
                "production_status":             rec.production_status,
                "reward_components":             rec.reward_components,
                "dominant_reason":               rec.dominant_reason,
                "ai_enabled":                    self.ai_enabled,
                "safety_overridden":             rec.safety_overridden,
                "safety_reason":                 rec.safety_reason,
                "raw_action_label":              rec.raw_action_label,
            }

            if rec.action_label != "HOLD_STEADY":
                log.info(
                    "Recommendation: %s  magnitude=%+.0f%%  savings=%.0f EGP/hr  health=%s",
                    rec.action_label, rec.action_magnitude_pct,
                    rec.estimated_savings_egp_per_hour, rec.machine_health,
                )
            else:
                self._hold_count += 1
                if self._hold_count % 20 == 0:
                    log.debug(
                        "HOLD_STEADY streak=%d  total_recs=%d  health=%s",
                        self._hold_count, self._rec_count, rec.machine_health,
                    )

            try:
                self.r.publish("ai.recommendation", json.dumps(payload))
            except Exception as exc:
                log.error("Publish ai.recommendation failed: %s", exc)

            if self.ai_enabled and rec.action_label != "HOLD_STEADY":
                ctrl = {
                    "action": "ai_recommendation",
                    "recommendation": {
                        "arc_power_mw":      rec.arc_power_mw,
                        "cooling_lmin":      rec.cooling_lmin,
                        "reactive_comp_mvar": rec.reactive_comp_mvar,
                    },
                }
                try:
                    self.r.publish("sim.control", json.dumps(ctrl))
                except Exception as exc:
                    log.error("Publish sim.control failed: %s", exc)


def main() -> None:
    global log

    # Bootstrap a temporary console-only logger before Redis is available
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s INFO     \033[36m[ai-engine]\033[0m  %(message)s",
        datefmt="%H:%M:%S",
    )
    pre_log = logging.getLogger("ai.startup")
    pre_log.info("Opti-Twin AI engine starting...")

    weights = make_weights_from_env()
    agent   = OptiTwinAgent(weights=weights, model_path=MODEL_PATH)

    # Wait for Redis
    r: redis.Redis | None = None
    for attempt in range(20):
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            r.ping()
            pre_log.info("Connected to Redis at %s:%s", REDIS_HOST, REDIS_PORT)
            break
        except Exception as exc:
            pre_log.warning("Redis not ready (%s) — retry %d/20", exc, attempt + 1)
            time.sleep(2)
    else:
        pre_log.critical("FATAL: cannot reach Redis after 20 retries")
        sys.exit(1)

    # Switch to full structured logger (with Redis publisher)
    log = _logger_mod.setup_logging(redis_client=r)
    log.info(
        "AI engine ready — model=%s  profile=default  LOG_LEVEL=%s",
        MODEL_PATH, os.getenv("LOG_LEVEL", "INFO"),
    )

    svc = AIService(r, agent)

    threading.Thread(target=svc.control_listener,  daemon=True).start()
    threading.Thread(target=svc.pricing_listener,  daemon=True).start()

    svc.telemetry_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if log:
            log.info("AI engine stopped by user")
