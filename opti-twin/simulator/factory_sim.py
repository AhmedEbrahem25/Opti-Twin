"""
Opti-Twin — Factory Simulator (Tier 1, Edge Layer)

Drives an Electric Arc Furnace simulation, emits telemetry every
SIM_INTERVAL_SECONDS to the backend over HTTP, and listens to a Redis
control channel for AI recommendations and crisis-event injections.

Verified anchors:
  - Tariff: EgyptERA Aug 2024 (1.60 EGP/kWh UHV flat)
  - Furnace: Ezz Flat Steel Ain Sokhna EAF #2 (Source: Global Energy Monitor)
  - Energy intensity: 400-500 kWh/t typical (Source: World Steel Association)
"""

from __future__ import annotations

import json
import os
import sys
import time
import threading
from datetime import datetime, timezone
from typing import Any, Dict

import redis
import requests

import logger as _logger_mod
from machines.eaf_machine import EAFMachine, EAFState
from machines.egypt_grid_pricing import EgyptGridPricing


# ---------- Config ----------
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
REDIS_HOST  = os.getenv("REDIS_HOST", "redis")
REDIS_PORT  = int(os.getenv("REDIS_PORT", "6379"))

SIM_MACHINE            = os.getenv("SIM_MACHINE", "EAF_02_EZZ_AIN_SOKHNA")
SIM_INTERVAL_SECONDS   = float(os.getenv("SIM_INTERVAL_SECONDS", "3"))
SIM_TIME_WARP_MINUTES  = float(os.getenv("SIM_TIME_WARP_MINUTES", "15"))
SIM_START_HOUR         = float(os.getenv("SIM_START_HOUR", "17.75"))

TARIFF_CLASS           = os.getenv("TARIFF_CLASS", "UHV_220-132kV")
TARIFF_RATE_FALLBACK   = float(os.getenv("TARIFF_RATE_EGP_PER_KWH", "1.60"))
TOU_MODE_DEFAULT       = os.getenv("TOU_MODE_DEFAULT", "false").lower() == "true"
PF_REFERENCE           = float(os.getenv("PF_REFERENCE", "0.92"))

GRID_CO2_KG_PER_KWH    = float(os.getenv("GRID_CO2_INTENSITY_KG_PER_KWH", "0.50"))
EAF_RATED_TPA          = int(os.getenv("EAF_RATED_TPA", "1600000"))
EAF_FURNACE_SIZE_T     = int(os.getenv("EAF_FURNACE_SIZE_T", "185"))

HEARTBEAT_EVERY_TICKS  = 10   # log a brief status every N ticks

# Module-level logger (set after Redis connect)
log: Any = None


# ---------- Setup ----------
def make_machine() -> EAFMachine:
    s = EAFState(
        machine_id=SIM_MACHINE,
        rated_capacity_tpa=EAF_RATED_TPA,
        furnace_size_t=EAF_FURNACE_SIZE_T,
    )
    return EAFMachine(s)


def make_pricing() -> EgyptGridPricing:
    return EgyptGridPricing(tariff_class=TARIFF_CLASS, tou_mode=TOU_MODE_DEFAULT)


def sim_time_now(start_hour: float, real_seconds_elapsed: float) -> float:
    sim_minutes_elapsed = real_seconds_elapsed * SIM_TIME_WARP_MINUTES
    return (start_hour + sim_minutes_elapsed / 60.0) % 24.0


# ---------- Telemetry payload ----------
def build_telemetry(
    machine: EAFMachine,
    pricing: EgyptGridPricing,
    sim_hour: float,
) -> Dict[str, Any]:
    s = machine.state
    live_price, live_is_peak, live_label = get_live_price(sim_hour, pricing)
    snap = pricing.price_at(sim_hour)
    pf_penalty = pricing.power_factor_penalty_egp_per_hour(s.power_factor, s.arc_power_mw)
    return {
        "machine_id":           s.machine_id,
        "machine_type":         "Electric Arc Furnace",
        "factory":              s.factory,
        "manufacturer":         s.manufacturer,
        "rated_capacity_tpa":   s.rated_capacity_tpa,
        "timestamp":            datetime.now(timezone.utc).isoformat(),
        "sim_hour":             round(sim_hour, 3),
        "arc_power_mw":         round(s.arc_power_mw, 2),
        "energy_kwh":           round(s.energy_kwh_today, 1),
        "energy_this_heat_kwh": round(s.energy_this_heat_kwh, 1),
        "power_factor":         round(s.power_factor, 3),
        "pf_penalty_bracket":   s.power_factor < PF_REFERENCE,
        "pf_penalty_egp_per_hour_est": round(pf_penalty, 1),
        "reactive_power_comp_mvar":    round(s.reactive_power_comp_mvar, 2),
        "tap_changer_position": s.tap_changer_position,
        "furnace_bath_temp":    round(s.bath_temp_c, 1),
        "electrode_temp":       round(s.electrode_temp_c, 1),
        "wall_panel_temp":      round(s.wall_panel_temp_c, 1),
        "cooling_water_outlet_temp": round(s.cooling_water_outlet_c, 1),
        "heat_progress_pct":    round(s.heat_progress_pct, 1),
        "current_batch_weight": round(s.current_batch_weight, 1),
        "batches_today":        s.batches_today,
        "production_backlog":   s.production_backlog,
        "idle_minutes_today":   round(s.idle_minutes_today, 2),
        "cycle_efficiency_pct": round(s.cycle_efficiency_pct, 1),
        "thermal_stress_index": round(s.thermal_stress_index, 1),
        "vibration_mm_s":       round(s.vibration_mm_s, 2),
        "electricity_price":    round(live_price, 3),
        "tariff_class":         snap.tariff_class,
        "tou_mode":             snap.tou_mode,
        "is_peak":              live_is_peak,
        "tariff_label":         live_label,
        "grid_frequency":       round(s.grid_frequency_hz, 3),
        "grid_co2_kg_per_kwh":  GRID_CO2_KG_PER_KWH,
        "electrode_position_mm":         round(s.electrode_position_mm, 1),
        "electrode_consumption_kg":      round(s.electrode_consumption_rate_kg_per_min, 4),
        "electrode_consumption_today_kg": round(s.electrode_consumption_today_kg, 2),
        "oxygen_injection_m3hr":         round(s.oxygen_injection_m3hr, 0),
        "cooling_water_flow_lmin":       round(s.cooling_water_flow_lmin, 0),
        "status":    s.phase.value,
        "ai_active": s.ai_active,
        "crisis_flags": {
            "wall_overheat":     s.crisis_wall_overheat,
            "electrode_break":   s.crisis_electrode_break,
            "grid_spike":        s.crisis_grid_spike,
            "transformer_alarm": s.crisis_transformer_alarm,
        },
    }


# ---------- Live price cache ----------
_live_price_cache: dict = {}
_live_price_lock  = threading.Lock()


def pricing_listener(r: redis.Redis) -> None:
    pubsub = r.pubsub()
    pubsub.subscribe("pricing.live")
    log.info("Subscribed to pricing.live")
    for msg in pubsub.listen():
        if msg.get("type") != "message":
            continue
        try:
            data = json.loads(msg["data"])
            with _live_price_lock:
                _live_price_cache.update(data)
            log.debug(
                "Price cache updated: %.3f EGP/kWh  peak=%s  source=%s",
                data.get("price_egp_kwh", 0), data.get("is_peak"), data.get("price_source"),
            )
        except Exception as exc:
            log.warning("pricing_listener parse error: %s", exc)


def get_live_price(sim_hour: float, pricing: EgyptGridPricing) -> tuple:
    with _live_price_lock:
        if _live_price_cache and _live_price_cache.get("price_source", "flat") != "flat":
            return (
                _live_price_cache.get("price_egp_kwh", TARIFF_RATE_FALLBACK),
                _live_price_cache.get("is_peak", False),
                _live_price_cache.get("label", "Dynamic"),
            )
    snap = pricing.price_at(sim_hour)
    return snap.rate_egp_per_kwh, snap.is_peak, snap.label


# ---------- Control channel ----------
def control_listener(machine: EAFMachine, pricing: EgyptGridPricing, r: redis.Redis) -> None:
    pubsub = r.pubsub()
    pubsub.subscribe("sim.control")
    log.info("Subscribed to sim.control")
    for msg in pubsub.listen():
        if msg.get("type") != "message":
            continue
        try:
            data = json.loads(msg["data"])
        except Exception as exc:
            log.warning("Bad control message: %s", exc)
            continue

        action = data.get("action")
        if action == "inject":
            event = data.get("event", "")
            machine.inject_event(event)
            log.warning("Crisis event injected: %s", event)
        elif action == "ai_toggle":
            enabled = bool(data.get("enabled"))
            if enabled:
                machine.state.ai_active = True
            else:
                machine.clear_ai()
            log.info("AI active → %s", machine.state.ai_active)
        elif action == "ai_recommendation":
            rec = data.get("recommendation", {})
            machine.apply_ai_recommendation(
                arc_power_mw=rec.get("arc_power_mw"),
                cooling_lmin=rec.get("cooling_lmin"),
                reactive_comp_mvar=rec.get("reactive_comp_mvar"),
            )
            log.debug(
                "AI recommendation applied: arc_mw=%s  cooling=%s  comp=%s",
                rec.get("arc_power_mw"), rec.get("cooling_lmin"), rec.get("reactive_comp_mvar"),
            )
        elif action == "tou_mode":
            pricing.set_tou_mode(bool(data.get("enabled")))
            log.info("TOU mode → %s", pricing.tou_mode)


# ---------- Main loop ----------
def main() -> None:
    global log

    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s INFO     \033[33m[simulator]\033[0m  %(message)s",
        datefmt="%H:%M:%S",
    )
    pre_log = logging.getLogger("sim.startup")
    pre_log.info("Opti-Twin EAF simulator starting: %s", SIM_MACHINE)
    pre_log.info(
        "Config: tariff=%s @ %.2f EGP/kWh  TOU=%s  interval=%.1fs  warp=%gmin/sec",
        TARIFF_CLASS, TARIFF_RATE_FALLBACK, TOU_MODE_DEFAULT,
        SIM_INTERVAL_SECONDS, SIM_TIME_WARP_MINUTES,
    )

    machine = make_machine()
    pricing = make_pricing()

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

    # Switch to full structured logger with Redis publisher
    log = _logger_mod.setup_logging(redis_client=r)
    log.info(
        "Simulator ready — machine=%s  LOG_LEVEL=%s",
        SIM_MACHINE, os.getenv("LOG_LEVEL", "INFO"),
    )

    threading.Thread(target=control_listener, args=(machine, pricing, r), daemon=True).start()
    threading.Thread(target=pricing_listener, args=(r,), daemon=True).start()

    start_real = time.time()
    tick       = 0
    last_phase = None

    while True:
        loop_start   = time.time()
        real_elapsed = loop_start - start_real
        sim_hour     = sim_time_now(SIM_START_HOUR, real_elapsed)

        machine.step(SIM_INTERVAL_SECONDS, SIM_TIME_WARP_MINUTES)
        payload = build_telemetry(machine, pricing, sim_hour)

        # Log phase transitions
        current_phase = machine.state.phase.value
        if current_phase != last_phase:
            log.info(
                "Phase transition: %s → %s  heat_progress=%.0f%%  bath=%.0f°C",
                last_phase or "START", current_phase,
                machine.state.heat_progress_pct, machine.state.bath_temp_c,
            )
            last_phase = current_phase

        # Log periodic heartbeat
        if tick % HEARTBEAT_EVERY_TICKS == 0:
            cf = payload["crisis_flags"]
            any_crisis = any(cf.values())
            log.debug(
                "Tick %d  sim_hour=%.2fh  phase=%-18s  P=%.1fMW  "
                "bath=%.0f°C  wall=%.0f°C  PF=%.2f  price=%.3f EGP/kWh%s",
                tick, sim_hour, current_phase,
                machine.state.arc_power_mw, machine.state.bath_temp_c,
                machine.state.wall_panel_temp_c, machine.state.power_factor,
                payload["electricity_price"],
                "  ⚠ CRISIS" if any_crisis else "",
            )

        # Publish telemetry
        try:
            r.publish("factory.telemetry", json.dumps(payload))
        except Exception as exc:
            log.error("Redis publish failed: %s", exc)

        # Push to backend (best-effort)
        try:
            requests.post(f"{BACKEND_URL}/api/v1/telemetry", json=payload, timeout=2.0)
        except Exception:
            pass

        tick += 1
        elapsed   = time.time() - loop_start
        sleep_for = max(0.0, SIM_INTERVAL_SECONDS - elapsed)
        time.sleep(sleep_for)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if log:
            log.info("Simulator stopped by user")
