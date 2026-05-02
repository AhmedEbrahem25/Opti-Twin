"""
Opti-Twin — FastAPI Gateway (Tier 4)

Endpoints:
  POST /api/v1/telemetry              — receive telemetry from simulator
  GET  /api/v1/recommendation         — last AI decision
  GET  /api/v1/stats                  — running KPIs
  POST /api/v1/ai/toggle              — turn AI on/off
  POST /api/v1/ai/profile             — switch reward profile
  POST /api/v1/sim/inject             — inject crisis event
  POST /api/v1/tariff/mode            — toggle current-flat vs future-TOU
  WS   /ws/live-feed                  — combined telemetry + recommendation stream

  Dynamic Pricing Engine:
  GET  /api/v1/pricing/live           — current live price
  GET  /api/v1/pricing/forecast       — 24h price forecast curve
  GET  /api/v1/pricing/mode           — current DPE mode
  POST /api/v1/pricing/mode           — switch DPE mode
  GET  /api/v1/pricing/revenue        — today's stacked revenue breakdown
  GET  /api/v1/pricing/schedule       — recommended heat schedule
  POST /api/v1/pricing/dr/inject      — inject DR event (demo)
  GET  /api/v1/pricing/dr/events      — DR event history
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api_contracts.schemas import (
    AIToggleRequest,
    CrisisInjectRequest,
    DRInjectRequest,
    KPISnapshot,
    LivePriceResponse,
    PricingEventSearchResult,
    PricingModeRequest,
    ProfileRequest,
    RecommendationOutput,
    RevenueSnapshot,
    TariffModeRequest,
    TelemetryInput,
)
from pricing.demand_response_controller import DemandResponseController
from pricing.event_store import PricingEventStore
from pricing.load_flexibility_scheduler import LoadFlexibilityScheduler
from pricing.price_signal_broker import PriceSignalBroker
from pricing.revenue_optimizer import RevenueOptimizer
from services.kpi_calculator import KPICalculator
from services.redis_broker import RedisBroker

DPE_ENABLED = os.getenv("DPE_ENABLED", "false").lower() == "true"
DPE_PRICE_INTERVAL = int(os.getenv("DPE_PRICE_UPDATE_INTERVAL_SECONDS", "60"))
DPE_FORECAST_INTERVAL = int(os.getenv("DPE_FORECAST_UPDATE_INTERVAL_SECONDS", "1800"))


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("opti-twin-backend")


# ---------- Shared state ----------
class AppState:
    broker: RedisBroker
    kpi: KPICalculator
    last_telemetry: Optional[dict] = None
    last_recommendation: Optional[dict] = None
    ws_clients: set[WebSocket]
    # Dynamic Pricing Engine
    price_broker: PriceSignalBroker
    dr_controller: DemandResponseController
    scheduler: LoadFlexibilityScheduler
    revenue: RevenueOptimizer
    event_store: PricingEventStore
    last_forecast: Optional[dict] = None

    def __init__(self) -> None:
        self.broker = RedisBroker()
        self.kpi = KPICalculator()
        self.last_telemetry = None
        self.last_recommendation = None
        self.ws_clients = set()
        self.price_broker = PriceSignalBroker()
        self.dr_controller = DemandResponseController()
        self.scheduler = LoadFlexibilityScheduler()
        self.revenue = RevenueOptimizer()
        self.event_store = PricingEventStore()
        self.last_forecast = None


state = AppState()


async def consume_redis() -> None:
    log.info("Starting Redis consumer loop")
    async for channel, data in state.broker.subscribe("factory.telemetry", "ai.recommendation"):
        if channel == "factory.telemetry":
            state.last_telemetry = data
            state.kpi.ingest_telemetry(data)
            # Accrue capacity credit every telemetry tick (3 real seconds)
            state.revenue.accrue_capacity_credit()
            await broadcast({"type": "telemetry", "data": data})
        elif channel == "ai.recommendation":
            state.last_recommendation = data
            state.kpi.ingest_recommendation(data)
            # Track energy savings in revenue optimizer
            savings_tick = float(data.get("estimated_savings_egp_per_hour", 0.0)) * (3.0 / 3600.0)
            state.revenue.record_energy_saving(savings_tick)
            await broadcast({"type": "recommendation", "data": data})


async def price_publisher() -> None:
    """Background task: publish live price + forecast to Redis at configured intervals."""
    forecast_counter = 0
    while True:
        try:
            sim_hour: Optional[float] = None
            if state.last_telemetry:
                sim_hour = state.last_telemetry.get("sim_hour")
            price_data = state.price_broker.get_current_price(sim_hour)
            state.event_store.record_price_tick(price_data)
            await state.broker.publish("pricing.live", price_data)
            await broadcast({"type": "pricing", "data": price_data})

            forecast_counter += DPE_PRICE_INTERVAL
            if forecast_counter >= DPE_FORECAST_INTERVAL or state.last_forecast is None:
                forecast_data = state.price_broker.get_forecast(sim_hour)
                state.last_forecast = forecast_data
                state.event_store.record_forecast_update(forecast_data)
                await state.broker.publish("pricing.forecast", forecast_data)
                forecast_counter = 0
        except Exception as exc:
            log.warning("price_publisher error: %s", exc)
        await asyncio.sleep(DPE_PRICE_INTERVAL)


async def broadcast(message: dict) -> None:
    if not state.ws_clients:
        return
    payload = json.dumps(message, default=str)
    dead: list[WebSocket] = []
    for ws in list(state.ws_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.ws_clients.discard(ws)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await state.broker.connect()
    consumer_task = asyncio.create_task(consume_redis())
    pricing_task = asyncio.create_task(price_publisher())
    log.info("Backend ready on :8000 (DPE mode: %s)", state.price_broker.mode)
    try:
        yield
    finally:
        consumer_task.cancel()
        pricing_task.cancel()
        await state.broker.disconnect()


app = FastAPI(
    title="Opti-Twin API",
    description="Industrial digital twin — Egyptian EAF energy intelligence",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- REST endpoints ----------
@app.get("/")
async def root():
    return {
        "service": "opti-twin-backend",
        "version": "2.0.0",
        "tariff_source": "EgyptERA Aug 2024 (1.60 EGP/kWh UHV, flat)",
    }


@app.post("/api/v1/telemetry")
async def post_telemetry(t: TelemetryInput):
    payload = t.model_dump(mode="json")
    state.last_telemetry = payload
    state.kpi.ingest_telemetry(payload)
    # Re-publish to Redis (in case sim couldn't reach Redis directly)
    await state.broker.publish("factory.telemetry", payload)
    return {"ok": True}


@app.get("/api/v1/recommendation")
async def get_recommendation() -> Optional[dict]:
    return state.last_recommendation


@app.get("/api/v1/stats", response_model=KPISnapshot)
async def get_stats() -> KPISnapshot:
    return KPISnapshot(**state.kpi.snapshot())


@app.post("/api/v1/ai/toggle")
async def ai_toggle(req: AIToggleRequest):
    await state.broker.publish("ai.control", {"action": "ai_toggle", "enabled": req.enabled})
    log.info("AI toggle -> %s", req.enabled)
    return {"ok": True, "enabled": req.enabled}


@app.post("/api/v1/ai/profile")
async def ai_profile(req: ProfileRequest):
    await state.broker.publish("ai.control", {"action": "set_profile", "profile": req.profile})
    log.info("AI profile -> %s", req.profile)
    return {"ok": True, "profile": req.profile}


@app.post("/api/v1/sim/inject")
async def sim_inject(req: CrisisInjectRequest):
    await state.broker.publish("sim.control", {"action": "inject", "event": req.event})
    log.info("Crisis inject -> %s", req.event)
    return {"ok": True, "event": req.event}


@app.post("/api/v1/tariff/mode")
async def tariff_mode(req: TariffModeRequest):
    await state.broker.publish("sim.control", {"action": "tou_mode", "enabled": req.enabled})
    log.info("Tariff TOU mode -> %s", req.enabled)
    return {"ok": True, "tou_mode": req.enabled}


# ---------- Dynamic Pricing Engine ----------

@app.get("/api/v1/pricing/live", response_model=LivePriceResponse)
async def pricing_live():
    sim_hour: Optional[float] = state.last_telemetry.get("sim_hour") if state.last_telemetry else None
    return LivePriceResponse(**state.price_broker.get_current_price(sim_hour))


@app.get("/api/v1/pricing/forecast")
async def pricing_forecast():
    if state.last_forecast:
        return state.last_forecast
    sim_hour: Optional[float] = state.last_telemetry.get("sim_hour") if state.last_telemetry else None
    forecast = state.price_broker.get_forecast(sim_hour)
    state.last_forecast = forecast
    return forecast


@app.get("/api/v1/pricing/mode")
async def pricing_get_mode():
    return {"mode": state.price_broker.mode}


@app.post("/api/v1/pricing/mode")
async def pricing_set_mode(req: PricingModeRequest):
    old_mode = state.price_broker.mode
    state.price_broker.set_mode(req.mode)
    if req.mode != old_mode:
        state.event_store.record_mode_change(old_mode, req.mode)
    await state.broker.publish("pricing.control", {"action": "set_mode", "mode": req.mode})
    log.info("DPE mode -> %s", req.mode)
    return {"ok": True, "mode": req.mode}


@app.get("/api/v1/pricing/revenue", response_model=RevenueSnapshot)
async def pricing_revenue():
    snap = state.revenue.snapshot()
    # Merge DR payments from DR controller
    snap["dr_payments_egp"] = max(snap["dr_payments_egp"], state.dr_controller.state.total_payments_today)
    snap["total_revenue_egp"] = (
        snap["energy_savings_egp"] + snap["dr_payments_egp"]
        + snap["capacity_credits_egp"] + snap["ancillary_egp"]
    )
    return RevenueSnapshot(**snap)


@app.get("/api/v1/pricing/schedule")
async def pricing_schedule():
    forecast = state.last_forecast
    if not forecast or not state.last_telemetry:
        return {"slots": [], "savings_vs_backtoback_egp": 0, "note": "No forecast available yet"}
    sim_hour = float(state.last_telemetry.get("sim_hour", 18.0))
    heats_remaining = max(1, 12 - int(state.last_telemetry.get("batches_today", 0)))
    shift_end = sim_hour + 8.0
    slots = state.scheduler.optimize(
        forecast=forecast.get("forecast", []),
        current_hour=sim_hour,
        heats_remaining=min(heats_remaining, 6),
        shift_end_hour=shift_end,
    )
    savings = state.scheduler.savings_vs_backtoback(slots, sim_hour, forecast.get("forecast", []))
    return {
        "slots": [s.to_dict() for s in slots],
        "savings_vs_backtoback_egp": savings,
        "generated_for_hour": round(sim_hour % 24, 2),
    }


@app.post("/api/v1/pricing/dr/inject")
async def dr_inject(req: DRInjectRequest):
    machine_state = state.last_telemetry or {}
    ev = state.dr_controller.inject_event(
        event_type=req.event_type,
        mw_requested=req.mw_requested,
        duration_minutes=req.duration_minutes,
    )
    assessment = state.dr_controller.process_event(ev, machine_state)
    state.event_store.record_dr_event(ev.to_dict(), assessment)
    if ev.status == "ACCEPTED":
        state.revenue.record_dr_payment(ev.payment_earned_egp)
        state.kpi.ingest_dr_payment(ev.payment_earned_egp)
        arc_mw = float(machine_state.get("arc_power_mw", 90.0))
        target_mw = max(60.0, arc_mw - ev.accepted_mw)
        await state.broker.publish("sim.control", {
            "action": "ai_recommendation",
            "recommendation": {"arc_power_mw": target_mw, "cooling_lmin": None, "reactive_comp_mvar": None},
        })
    log.info("DR inject %s -> %s", req.event_type, ev.status)
    return {"event": ev.to_dict(), "assessment": assessment}


@app.get("/api/v1/pricing/dr/events")
async def dr_events():
    return state.dr_controller.snapshot()


@app.get("/api/v1/pricing/events/search", response_model=PricingEventSearchResult)
async def pricing_events_search(
    q: Optional[str] = None,
    event_kind: Optional[str] = None,
    dr_status: Optional[str] = None,
    dr_type: Optional[str] = None,
    is_peak: Optional[bool] = None,
    limit: int = 50,
):
    results = state.event_store.search(
        q=q,
        event_kind=event_kind,
        dr_status=dr_status,
        dr_type=dr_type,
        is_peak=is_peak,
        limit=min(limit, 200),
    )
    return PricingEventSearchResult(
        total=len(results),
        results=results,
        stats=state.event_store.stats(),
    )


# ---------- WebSocket ----------
@app.websocket("/ws/live-feed")
async def ws_live_feed(ws: WebSocket):
    await ws.accept()
    state.ws_clients.add(ws)
    log.info("WS client connected; total=%d", len(state.ws_clients))
    # Push latest snapshot immediately
    if state.last_telemetry:
        await ws.send_text(json.dumps({"type": "telemetry", "data": state.last_telemetry}, default=str))
    if state.last_recommendation:
        await ws.send_text(json.dumps({"type": "recommendation", "data": state.last_recommendation}, default=str))
    try:
        while True:
            # Keep-alive; client doesn't need to send anything
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        state.ws_clients.discard(ws)
        log.info("WS client disconnected; total=%d", len(state.ws_clients))
