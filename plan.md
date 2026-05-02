# 🏭 OPTI-TWIN — ULTRA MASTER PLAN (Evidence-Backed Edition)
> **Project:** Opti-Twin · Autonomous Energy Intelligence for Smart Manufacturing
> **Event:** NextCity AI Hack 2026 (May 7–8) · Alamein International University
> **Track:** Industry-Driven Challenges
> **Selected Machine:** Electric Arc Furnace (EAF) — modelled on Ezz Flat Steel, Ain Sokhna
> **Plan Version:** 2.0 (verified) · **Created:** 2026-05-01 · **Status:** Active build phase
> **Days to Demo:** 7

> **Editorial note (v2.0):** This revision corrects multiple factual errors from v1.0 that were based on assumed rather than verified data — most critically, the time-of-use industrial tariff structure. Egyptian industrial customers on Ultra-High and High-Voltage feeders are billed at a **flat tariff** (no peak/off-peak split for industry as of August 2024). All key figures have been re-anchored to authoritative sources (EgyptERA, IEA, World Steel Association, Global Energy Monitor, EEHC) and clearly labelled ✔ verified or ⚠ estimated. The economic value proposition has been re-framed accordingly to remain credible for investor and pilot-discussion settings.

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Catalogue (Every Pain Point We Solve)](#2-problem-catalogue)
3. [Solution Architecture (4-Tier System)](#3-solution-architecture)
4. [The Machine — EAF Deep Dive](#4-the-machine--eaf-deep-dive)
5. [Egyptian Industrial Context (Verified)](#5-egyptian-industrial-context)
6. [Dataset Catalogue (All Sources)](#6-dataset-catalogue)
7. [RL Formulation (State, Action, Reward)](#7-rl-formulation)
8. [Simulation Engine Design](#8-simulation-engine-design)
9. [Backend & API Contracts](#9-backend--api-contracts)
10. [Frontend Dashboard](#10-frontend-dashboard)
11. [DevOps, Docker, and Environment](#11-devops-docker-and-environment)
12. [7-Day Execution Roadmap](#12-7-day-execution-roadmap)
13. [Team & Ownership](#13-team--ownership)
14. [Risk Register & Mitigations](#14-risk-register--mitigations)
15. [Success Metrics & Judge-Facing KPIs](#15-success-metrics--judge-facing-kpis)
16. [Demo Script (3 Minutes)](#16-demo-script)
17. [Post-Hackathon Roadmap](#17-post-hackathon-roadmap)
18. [Assumptions & Limitations](#18-assumptions--limitations) **[NEW]**
19. [Real-World Deployment Strategy](#19-real-world-deployment-strategy) **[NEW]**
20. [Sources & References](#20-sources--references) **[NEW]**
21. [Appendix: Glossary](#21-appendix-glossary)

---

## 1. Executive Summary

Egyptian heavy industry — and steel manufacturing in particular — operates under structural electricity-cost and emissions pressures that are widely under-managed at the shop-floor control layer. For a single Electric Arc Furnace (EAF) of the size and class operated by Ezz Flat Steel at the Ain Sokhna complex (185-tonne furnaces, ~200 MW allocated capacity per Supreme Council of Energy decision for the 2023 expansion (Source: Arab Iron and Steel Union; Global Energy Monitor)), three independent levers create a credible business case for an embedded optimization agent:

1. **Industrial-tariff exposure at flat rate.** As of EgyptERA's August 2024 schedule, Ultra-High Voltage (220–132 kV) industrial customers pay **160.0 piasters/kWh = 1.60 EGP/kWh** as a flat tariff with no time-of-use split (Source: EgyptERA Tariff schedule, August 2024). Every kWh avoided is a 1.60 EGP saving — and electricity is by far the dominant variable cost in EAF steelmaking.
2. **Power-factor penalties for industrial loads >500 kW.** Egypt actively penalizes low average annual power factor; tariffs are referenced to a 0.92 power factor and EAFs typically operate at 0.75–0.85 due to severe reactive-power swings during melting (Source: EgyptERA tariff schedule; "Power factor and your electrical utility bill in Egypt", IEEE / ResearchGate).
3. **EU CBAM exposure.** The EU Carbon Border Adjustment Mechanism enters its definitive phase from 2026, applying a carbon price to imports of carbon-intensive products including iron and steel. With Egypt's grid being ~81% natural-gas-fired (Source: IEA / EIA Egypt country brief, 2024), every kWh saved by an EAF directly cuts Scope 2 emissions and the resulting CBAM liability on European exports.

**Opti-Twin** is a Multi-Objective Reinforcement Learning (MORL) agent embedded inside an Industrial Digital Twin. It reads simulated furnace telemetry every 3 seconds, predicts an optimal arc-power / oxygen / cooling action, and emits both the action and a **human-readable XAI justification** (English + Arabic). The α/β/γ/δ/ε reward weights are exposed in the dashboard so each factory tunes the system to its own priorities (cost-first, equipment-first, production-first, quality-first).

### 1.1 Headline KPIs (Estimated, Demoable)

The figures below are **modelled estimates based on industry-typical EAF parameters** (Source: World Steel Association energy fact sheets; Wikipedia EAF article; IEA Iron & Steel Roadmap), applied to the Ain-Sokhna-class furnace footprint. They are conservative, internally consistent, and intended for technical-review and pilot-discussion settings — not as guarantees.

| Metric | Baseline (industry-typical) | With Opti-Twin (target) | Δ | Confidence |
|---|---|---|---|---|
| Energy intensity | 450 kWh/t (Source: worldsteel; Wikipedia) | 405 kWh/t | **−10%** | ⚠ Estimated; literature reports 5–15% savings from advanced control / DR programs |
| Annual electricity bill (one EAF) | ~1.15 billion EGP (450 kWh/t × 1.6 Mtpa × 1.60 EGP/kWh) | ~1.04 billion EGP | **−115M EGP** | ⚠ Estimated |
| Power-factor uplift | 0.78 (typical EAF average) | 0.92 (tariff reference) | Penalty avoidance | ✔ Direct bill impact (verified mechanism) |
| Annual CO₂ emissions (Scope 2) | ~360,000 tCO₂ (720 GWh × 0.5 tCO₂/MWh) | ~324,000 tCO₂ | **−36,000 tCO₂/yr** | ⚠ Estimated |
| Production throughput | 1.6 Mtpa (rated) | 1.6 Mtpa | **= 100%** | Constraint, not goal |
| Thermal-stress incidents | Industry baseline | <0.5/wk in sim | **Reduced** | ⚠ Sim-only metric |

**Why this wins NextCity AI Hack 2026:** the system is grounded in (i) a real Egyptian factory class, (ii) verified Egyptian tariff and grid data, (iii) industry-standard EAF parameters, and (iv) a credible deployment path (shadow-mode → advisory → closed-loop). The demo is 3 minutes, fully offline, and the WOW moment — AI toggle ON, energy curve flattens, β-override on a wall-overheat event — is intuitive to non-specialist judges.

---

## 2. Problem Catalogue

Every problem Opti-Twin attacks, grouped by stakeholder. Each row maps to at least one feature in §3 or §7.

### 2.1 Economic & Financial Problems

| # | Problem | Magnitude | Affected Party | Opti-Twin Lever | Source |
|---|---|---|---|---|---|
| P1 | **Flat-tariff energy bill exposure** — every kWh costs 1.60 EGP for UHV industrial users | ~1.15B EGP/yr per 185-t EAF at 1.6 Mtpa, 450 kWh/t | Plant CFO | RL agent reduces total kWh through process optimization | ✔ EgyptERA Aug 2024 |
| P2 | **Power-factor penalties (loads >500 kW)** — penalty escalates if not corrected within 3 months; supply termination after 6 months | Documented; case-by-case | Energy manager | Reactive-power / tap-changer / capacitor-bank action | ✔ "Power factor and your electrical utility bill in Egypt", ResearchGate |
| P3 | **No real-time cost telemetry on the shop floor** — bills land monthly, not minute-by-minute | Decisions made blind | Shift supervisor | Live `KPIBanner` in EGP/hour | — |
| P4 | **Demand-charge / contracted-capacity exposure** — exceeding contracted MW triggers penalties under bilateral PPAs (varies by contract) | Contract-specific | Procurement | Power-factor + tap-changer control; ramp-rate limits | ⚠ Contract-dependent; mechanism standard internationally |
| P5 | **EU CBAM exposure (definitive phase from 2026)** — carbon price on iron & steel imports into the EU | ESG / export revenue at risk | C-suite | Energy reduction directly cuts Scope 2 CO₂ → CBAM liability | ✔ European Commission CBAM framework |
| P6 | **Future tariff-reform risk** — Egyptian academic literature (Ahmed et al., GUC working paper #29) documents that Egyptian electricity is priced below cost and proposes a peak-load pricing model that could cut required capacity expansion by 2,000–3,000 MW | Tariff reform is plausible within 3–5 years | Strategic planning | RL agent already structured to handle TOU when it arrives | ✔ GUC Working Paper "The Egyptian Electricity Market: Designing a Prudent Peak Load Pricing Model" |

### 2.2 Operational Problems

| # | Problem | Symptom | Opti-Twin Lever |
|---|---|---|---|
| P7 | **Conflicting KPIs across silos** — cost, throughput, and equipment health are managed by different teams | Local optima, global loss | Single MORL reward function |
| P8 | **Manual heat scheduling** — supervisors decide ad-hoc when to start the next batch | Sub-optimal sequencing | Scheduling policy in action space |
| P9 | **Heat-duration variance (45–65 min)** — unpredictable energy bills | Cannot forecast cost | Phase-aware physics simulator + RL planner |
| P10 | **Reactive emergency handling** — wall overheat / electrode break / grid spike treated post-hoc | Avg ~500K EGP repair per incident (industry estimate ⚠) | β-weight overrides + crisis events in sim |
| P11 | **Sub-optimal power factor (0.75–0.85 typical)** — penalty exposure | Direct bill add-on | Capacitor bank + tap changer in action space |

### 2.3 Equipment-Health Problems

| # | Problem | Damage Mode | Opti-Twin Lever |
|---|---|---|---|
| P12 | **Wall panel overheat** — water-cooled panels degrade at sustained >250°C | Panel replacement cost (industry-typical, ⚠ varies) + downtime | β-weight kicks in at 200°C threshold |
| P13 | **Electrode fracture** — graphite electrodes break under thermal/mechanical stress | UHP electrodes ~$3,000–6,000/t (Source: Mordor Intelligence graphite electrode market report) | ε-weight reduces consumption rate |
| P14 | **Refractory lining wear** — bath temperature spikes accelerate erosion | Reline interval typically every 600–1,000 heats (Source: Vesuvius/RHI Magnesita technical literature) | Bath-temp band reward (1,600–1,650 °C) |
| P15 | **Transformer thermal aging** — sustained near-rated MVA shortens insulation life | EAF #2 at Ezz Ain Sokhna suffered a transformer failure in November 2024 expected to halt production for ~9 months (Source: Global Energy Monitor) | Tap-changer / active-power smoothing |
| P16 | **Grid-frequency events (49.5–50.5 Hz)** — Hz dips can trip the furnace | Lost heat = scrap loss | Frequency in state vector |

### 2.4 Production & Supply-Chain Problems

| # | Problem | Effect | Opti-Twin Lever |
|---|---|---|---|
| P17 | **Heat backlog cascading** — one delayed heat cascades into shift/day overruns | Late deliveries to rolling mill | γ-weight (production delay) |
| P18 | **Steel quality drift** — bath outside 1,600–1,650 °C produces off-spec heat | Scrap or re-heat | δ-weight (quality bonus) |
| P19 | **Scrap / DRI mix variance** — Ezz Ain Sokhna runs 80% DRI + 20% scrap (Source: Global Energy Monitor); different feedstock densities change melt time | Fixed schedules misfire | Charge-weight in action space |
| P20 | **Oxygen lance over/under-use** — wastes O₂ or slows melt | 5–10% melt-time variance (industry-typical, ⚠) | Oxygen injection in action space |

### 2.5 Sustainability & ESG Problems

| # | Problem | Stake | Opti-Twin Lever | Source |
|---|---|---|---|---|
| P21 | **Scope 2 CO₂ emissions** — Egypt grid is ~81% natural gas (2024), with grid CO₂ intensity ~0.45–0.5 tCO₂/MWh | EU CBAM, ESG reporting | kWh savings → direct CO₂ savings | ✔ IEA / EIA / Climatiq |
| P22 | **Water consumption for cooling** — Ain Sokhna region is water-stressed | Sustainability ratings | Cooling-water flow in action space | — |
| P23 | **Local emissions footprint** — heavy industry near Sokhna & Suez logistics hub | Community / regulator | Off-shifting of high-load operations once TOU arrives | — |

### 2.6 AI/ML & Trust Problems

| # | Problem | Why It Blocks Adoption | Opti-Twin Lever |
|---|---|---|---|
| P24 | **Black-box AI** — operators won't trust an unexplainable agent next to a 1,650 °C bath | Adoption = 0% | XAI engine produces EN+AR reasons per action |
| P25 | **No safety floor** — RL agents can take catastrophic actions during exploration | Hard veto needed | Action masking + hard physical limits in env (see §7.2) |
| P26 | **No simulation-to-real transfer story** — pilot reviewers will ask "does this work outside the sim?" | Credibility gap | Shadow-mode deployment plan in §19 |
| P27 | **Fragile reward tuning** — α/β/γ tuning is currently a research problem | Hard to tune onsite | Preset profiles (cost-first, equipment-first, production-first, quality-first) |

### 2.7 Hackathon-Specific Operational Risks

| # | Problem | Mitigation |
|---|---|---|
| P28 | Demo network/internet failure on stage | Run fully local in Docker; no external API calls at demo time |
| P29 | Live RL training divergence on stage | Ship pre-trained `opti_twin_ppo.zip`, freeze inference only |
| P30 | Time-warp drift on slow laptops | Decouple display clock from physics `dt` (see §8.1); benchmark on team laptops |
| P31 | Frontend WS reconnect during demo | Auto-reconnect with exponential backoff + offline replay file |
| P32 | Judges asking "what about cost of this system?" | ROI pitch: §15.2 — power-factor penalty avoidance + 5–10% energy efficiency typically delivers payback <12 months on a single-furnace deployment |

---

## 3. Solution Architecture

Opti-Twin is a **4-Tier Enterprise Architecture** (Edge → Streaming → AI Core → Application), every tier independently containerized.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    OPTI-TWIN — ENTERPRISE ARCHITECTURE                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

 ┌──────────────────────────────────────────────────────────────────────────┐
 │  TIER 1 — EDGE LAYER (Data Source)                                       │
 │  factory_sim.py + machines/eaf_machine.py + eaf_thermal_model.py         │
 │  Emits JSON telemetry every 3 seconds (simulating typical SCADA polling) │
 └────────────────────────────────┬─────────────────────────────────────────┘
                                  │  WebSocket / JSON (Event-Driven)
 ┌────────────────────────────────▼─────────────────────────────────────────┐
 │  TIER 2 — STREAMING LAYER                                                │
 │  Redis 7 Pub/Sub  ·  channel: factory.telemetry                          │
 │  Decouples edge from AI. Bounded-buffer back-pressure. Horizontal-scale. │
 └────────────────────────────────┬─────────────────────────────────────────┘
                                  │
 ┌────────────────────────────────▼─────────────────────────────────────────┐
 │  TIER 3 — AI CORE (The Brain)                                            │
 │  • OptiTwinEAFEnv (Gymnasium custom env)                                 │
 │  • PPO agent (Stable Baselines3, pre-trained)                            │
 │  • XAI engine — generates EN + AR explanations per action                │
 │  • Reward: R = α·E_saved − β·M_stress − γ·P_delay + δ·Quality − ε·Wear   │
 └────────────────────────────────┬─────────────────────────────────────────┘
                                  │  Pydantic-validated REST + WebSocket
 ┌────────────────────────────────▼─────────────────────────────────────────┐
 │  TIER 4 — APPLICATION LAYER                                              │
 │  ┌───────────────────────────┐    ┌─────────────────────────────────┐    │
 │  │ FastAPI Gateway           │    │ Next.js / React Dashboard       │    │
 │  │ POST /api/v1/telemetry    │    │ EAFStatusCard · ThermalGauge    │    │
 │  │ GET  /api/v1/recommendation│   │ EnergyChart · XAIDecisionLog    │    │
 │  │ WS   /ws/live-feed        │    │ KPIBanner · AIToggle            │    │
 │  │ localhost:8000/docs       │    │ localhost:3000                  │    │
 │  └───────────────────────────┘    └─────────────────────────────────┘    │
 └──────────────────────────────────────────────────────────────────────────┘

 🐳  Single command: `docker-compose up --build`
```

### 3.1 Why 4 Tiers (Not a Monolith)

| Decision | Rationale |
|---|---|
| Edge isolated as own container | Real factories deploy edge agents on shop-floor PCs; matching topology is consistent with modern IIoT reference architectures (ISA-95 levels 1–2 separation) |
| Redis as broker (not direct HTTP) | Survives bursts, retries, lets us add machines later without code changes — pattern consistent with industrial publish-subscribe brokers (MQTT/AMQP) |
| AI core separate from API | Lets ML iterate without breaking backend; mirrors real-world ML model serving |
| Pydantic at every boundary | Catches malformed payloads before they hit the RL state vector; protects model from garbage-in |

### 3.2 Data Flow Contract

```
[factory_sim] ──POST /api/v1/telemetry──► [FastAPI]
                                              │
                                              ▼
                                      [Redis Pub/Sub]
                                              │
                                              ▼
                                      [RL Agent reads state]
                                              │
                                              ▼
                              [Computes action + XAI reason]
                                              │
[Dashboard] ◄──WS /ws/live-feed────── [FastAPI broadcasts]
```

---

## 4. The Machine — EAF Deep Dive

### 4.1 Why EAF and Why Ezz Flat Steel — Ain Sokhna

| Criterion | Detail | Source |
|---|---|---|
| Machine | Electric Arc Furnace | — |
| Reference factory | Ezz Flat Steel — Ain Sokhna Complex, Suez Governorate | ✔ Global Energy Monitor; Ezz Steel official site |
| Number of EAFs at site | 2 (EAF 1 since 2014; EAF 2 since 2023) | ✔ GEM |
| Furnace size (per EAF) | 185 tonnes | ✔ GEM |
| Annual capacity | EAF 1: 1.28 Mtpa · EAF 2: 1.6 Mtpa · Total 2.88 Mtpa | ✔ GEM |
| Manufacturer | Danieli | ✔ GEM |
| Allocated power (EAF 2 / 2023) | 200 MW (Supreme Council of Energy decision) | ✔ Arab Iron and Steel Union |
| Feedstock mix | 80% DRI + 20% scrap (DRI from on-site Danieli HYL Energiron III, 1.95 Mtpa) | ✔ GEM |
| Energy intensity (industry-typical for modern UHP EAF) | 400–500 kWh/t (range 300–700 kWh/t) | ✔ World Steel Association; Wikipedia EAF |
| Strategic fit | Largest single industrial electricity consumer class in Egypt; ISO 50001 certified site (energy management system already in place) | ✔ GEM |

> **Important correction from v1.0:** the original document understated the furnace size (cited "80–120 tons / 80–120 MW") and named "Ezz Steel — Ein El-Sokhna Complex" generically. The Ezz Flat Steel Ain Sokhna site actually runs 185-t Danieli furnaces with the 2023 unit allocated 200 MW. In addition, the November 2024 transformer failure on EAF 2 (Source: GEM) is precisely the type of equipment-health incident that motivates the β-weight in our reward function.

### 4.2 Real Physical Parameters (Calibrated to Modern UHP EAF)

| Parameter | Value | Source / Note |
|---|---|---|
| Installed transformer capacity | 150–250 MVA class | ⚠ Industry-typical for 185-t UHP furnace; exact Ezz value not public |
| Actual arc power range | 80–180 MW (we model 60–110 MW for hackathon clarity) | ⚠ Conservative cap for visual readability of dashboard |
| Target bath temperature | 1,600–1,650 °C | ✔ Standard EAF tap temperature (worldsteel) |
| Maximum wall panel temperature | 250 °C (water-cooled) | ⚠ Industry-typical; values vary by panel design |
| Batch / heat size | 80–185 t scrap-equivalent | ✔ GEM (185-t furnaces, partial heels common) |
| Heat duration | 45–65 min (tap-to-tap) | ✔ Typical UHP EAF (worldsteel) |
| Energy consumption per heat | 400–500 kWh/t | ✔ worldsteel; Wikipedia |
| Arc current | 50,000–80,000 A | ✔ UHP EAF typical |
| Power factor | 0.75–0.85 (uncompensated) | ✔ "EAF reactive energy compensation" literature |
| Graphite electrodes | 3 × ⌀ 600–700 mm | ✔ UHP UCAR / GrafTech specs |
| Electrode consumption | 1.2–2.0 kg/t (modern UHP) — older furnaces 4–8 kg/t | ✔ Mordor Intelligence; ResearchGate |
| Tariff reference power factor | 0.92 | ✔ EgyptERA Aug 2024 |

### 4.3 Heat Phases (Modelled in `eaf_machine.py`)

1. **CHARGING** (0–5 min) — scrap dropped via overhead crane; arc off.
2. **BORE-DOWN** (5–15 min) — arcs ignite, drilling channels into scrap; high voltage / low current.
3. **MELTING_PHASE_1** (15–30 min) — bulk melting; max power.
4. **MELTING_PHASE_2** (30–45 min) — flat bath forming; oxygen injection peaks.
5. **REFINING** (45–55 min) — temperature trim to 1,630 °C; chemistry adjustment.
6. **TAPPING** (55–60 min) — molten steel poured into ladle; furnace tilts.

Highest-value RL interventions occur in phases 3–5, where arc power is highest and bath thermal mass tolerates moderate power-cycling without quality damage.

### 4.4 Simplified Physics Model — Bath Temperature Dynamics

> **Label:** This is a **simplified zero-dimensional energy-balance model** used only for hackathon-level visualization. It is NOT a substitute for a CFD or finite-element thermal model. The coefficients are seeded from textbook thermodynamic relationships (specific heat of steel, oxygen combustion enthalpy) and tuned for visual realism, not for engineering certification. Real EAF process models (e.g. Danieli Q-MELT, IBSE Steeluniversity) include slag chemistry, electrode radiation factors, water-cooled panel heat transfer, and post-combustion dynamics — all out of scope here.

```python
# eaf_thermal_model.py — simplified bath temperature update equation
# References:
#   - Specific heat of liquid steel: ~0.50 kJ/(kg·°C) (industry constant)
#   - Oxygen combustion enthalpy: ~9 kJ per Nm³ O₂ for stoichiometric C+O₂
#     (we use 2.5 kJ/Nm³ as an effective bath-coupled value to account for
#     post-combustion losses and slag absorption — empirical tuning)
#   - Wall heat-loss fraction: 0.10–0.20 of input energy is industry-typical
#     for water-cooled panels (we use 0.15)

SPECIFIC_HEAT_STEEL   = 0.50   # kJ/(kg·°C) — reference constant
HEAT_LOSS_COEFFICIENT = 0.15   # fractional wall heat loss (tuned)
OXYGEN_HEAT_GAIN      = 2.5    # kJ per m³/hr·s effective; bath-coupled

def update_bath_temp(T, P_mw, batch_t, O2_m3hr, cool_lmin, dt=3.0):
    """Returns new bath temperature in °C. Simplified — see §4.4 caveats."""
    mass_kg   = batch_t * 1000
    q_arc     = P_mw * 1000 * dt                            # kJ in dt sec
    q_oxygen  = O2_m3hr * OXYGEN_HEAT_GAIN * (dt / 3600)    # kJ
    q_loss    = (T - 25) * HEAT_LOSS_COEFFICIENT * dt * 0.5
    q_cooling = cool_lmin * 0.07 * dt
    q_net     = q_arc + q_oxygen - q_loss - q_cooling
    delta_T   = q_net / (mass_kg * SPECIFIC_HEAT_STEEL)
    return min(T + delta_T, 1700.0)                         # physical ceiling
```

### 4.5 Crisis Events Injected During Demo

| Event | Trigger | Telemetry effect | Expected AI response |
|---|---|---|---|
| `wall_overheat` | Operator panel button | `wall_panel_temp` ramps 187 → 223 °C | EMERGENCY_COOLING (+120 l/min); reduce O₂ |
| `electrode_break` | Random or button | `electrode_consumption_rate` spikes; `arc_current` drops one phase | Reduce arc power; alert operator |
| `grid_spike` | Random or button | `grid_frequency` drops 49.98 → 49.6 Hz | Drop to safe-power mode; ride-through |
| `transformer_alarm` | Random or button | Transformer winding temp rises | Reduce tap; cap MVA — anchored to GEM-reported Nov 2024 EAF 2 transformer failure |

---

## 5. Egyptian Industrial Context

### 5.1 The Tariff Schedule (Verified, August 2024)

> ✔ **Source:** EgyptERA "Current Electricity Tariff" page, August 2024 schedule (egyptera.org/en/TarrifAug2024.aspx). All figures cross-checked with the August 2024 announcement.

```
╔══════════════════════════════════════════════════════════════════════════╗
║       EGYPTIAN INDUSTRIAL ELECTRICITY TARIFF — VERIFIED Aug 2024        ║
║                                                                          ║
║   Regulator:       EgyptERA (Egyptian Electric Utility & Consumer       ║
║                    Protection Regulatory Agency)                         ║
║   Transmission:    EETC (Egyptian Electricity Transmission Company,     ║
║                    independent TSO since 2015 Electricity Law)          ║
║   Holding parent:  EEHC (Egyptian Electricity Holding Company)          ║
╠════════════════════════════╦══════════════════╦══════════════════════════╣
║  Voltage Class             ║  Tariff (EGP/kWh)║  Notes                   ║
╠════════════════════════════╬══════════════════╬══════════════════════════╣
║  Ultra/Extra HV (220–132 kV)║      1.60        ║  Flat rate; PF ref 0.92  ║
║  High Voltage   (66–33 kV) ║      1.74        ║  Flat rate; PF ref 0.92  ║
║  Medium Voltage (22–11 kV) ║      1.94        ║  Flat rate; PF ref 0.92  ║
╠════════════════════════════╩══════════════════╩══════════════════════════╣
║  Customer service fee:    35 EGP/month (all HV/UHV/MV industrial users) ║
║  Power factor:            Penalty on industrial loads >500 kW with PF   ║
║                           below 0.92 reference (Source: ResearchGate    ║
║                           "Power factor and your electrical utility     ║
║                           bill in Egypt").                              ║
╚══════════════════════════════════════════════════════════════════════════╝
```

> ✔ **Critical correction from v1.0:** Egyptian Ultra-High Voltage industrial customers are **billed at a flat tariff** (1.60 EGP/kWh as of Aug 2024). There is no published peak / off-peak split for industrial UHV customers in the EgyptERA schedule. The "1.0 / 1.2 / 2.5 EGP" three-tier schedule used in earlier project drafts was assumed and is not supported by the regulator's published rates. We retain a TOU schedule in the **simulator** to demonstrate readiness for tariff reform (see §5.4) but no longer present TOU as a current regulatory fact.

### 5.2 Real Annual Bill (Modelled Estimate)

> ⚠ **Estimated.** The bill below assumes industry-typical parameters applied to Ezz Flat Steel EAF 2 (1.6 Mtpa rated, started 2023). It is illustrative for ROI discussion, not a quote.

```
Assumptions (industry-typical):
  Annual production:   1.6 Mtpa            (Source: GEM, EAF 2)
  Energy intensity:    450 kWh/t           (Source: worldsteel; midpoint 400–500)
  → Annual electricity: 720 GWh
  Tariff:              1.60 EGP/kWh        (Source: EgyptERA Aug 2024, UHV)
  → Gross bill:        720 GWh × 1.60 = 1.152 billion EGP/yr
  Power-factor uplift: ~3–5% net bill add-on if uncompensated
                       (Source: ResearchGate "PF correction in Egypt")
  → PF-uncomp. bill:   ~1.18–1.21 billion EGP/yr per furnace

Opti-Twin target savings (modelled):
  Energy efficiency:   5–10% kWh/t reduction (literature: advanced control
                       + DR can reach 5–15% in EAF — IEA Iron & Steel 2024)
  → Energy savings:    58–115 million EGP/yr
  PF uplift:           Avoid ~30–60 million EGP/yr penalty bracket (⚠ varies)
  → Total upside:      ~90–175 million EGP/yr per furnace (estimated range)
```

### 5.3 Egypt's Generation Mix (Verified, 2024)

> ✔ **Source:** IEA Egypt country page; EIA Egypt Country Analysis Brief (Aug 2024); lowcarbonpower.org Egypt 2024.

| Source | Share of generation 2024 |
|---|---|
| Natural gas | **~81.3%** |
| Oil | ~7.5% |
| Hydropower | ~7% |
| Wind | ~3% |
| Solar | ~2% |

Implication: Egypt's grid is **heavily gas-dominant**, so kWh saved by an EAF translates almost directly into avoided gas combustion and CO₂ emissions.

### 5.4 Future Tariff Reform — Why Time-of-Use is Plausible

Egyptian academic literature explicitly proposes time-of-use industrial pricing as a way to reduce required peak capacity. The German University in Cairo working paper "The Egyptian Electricity Market: Designing a Prudent Peak Load Pricing Model" (Working Paper #29) estimates that introducing peak-load pricing could reduce required capacity expansion by 2,000–3,000 MW. Combined with ongoing IMF-aligned subsidy reform, **a TOU industrial tariff in the 3–5 year horizon is a realistic planning assumption**. Opti-Twin's RL state vector and reward function are explicitly structured to ingest a TOU price signal the day it is published — no architecture change required.

### 5.5 Daily / Hourly Cost Snapshot (For Dashboard, Modelled)

```
At 90 MW continuous draw and 1.60 EGP/kWh flat:
  Hourly:       90,000 kW × 1.60 EGP/kWh   = 144,000 EGP/hour
  Daily:        144,000 × 24                = 3.456 million EGP/day
  At 85% util:                                ~2.94 million EGP/day
  Annual:       ~1.07 billion EGP/year (single furnace)
```

These are the numbers the live dashboard counts up against. Every percent of efficiency saves ~10.7 million EGP/year per furnace.

### 5.6 Stakeholder Map

| Stakeholder | Cares About | Pitch Hook |
|---|---|---|
| Plant CFO | EGP saved | "5–10% kWh/t reduction = 60–115M EGP/yr/furnace, modelled" |
| Energy manager | Power factor compliance | "PF target 0.92 maintained automatically" |
| Shift supervisor | Hitting heat targets | "Production stays at 100%, RL γ-weight ensures it" |
| Maintenance lead | Equipment lifespan | "Wall stress incidents −90% (sim metric)" |
| Sustainability officer | Scope 2 CO₂ | "10% kWh saved = ~36,000 tCO₂/yr; CBAM-relevant" |
| C-suite (export-facing) | EU CBAM exposure | "Lower carbon intensity per tonne shipped to EU" |
| EgyptERA / Ministry of Electricity | Demand-side management | "Voluntary peak-shaving pilot for large industrial users" |

---

## 6. Dataset Catalogue

This section enumerates every dataset, public source, or synthetic data generator the project depends on, why it matters, and how we use it. Where public data is unavailable, we synthesize but anchor each generator to a verified reference parameter.

### 6.1 Tariff & Grid Data

| ID | Dataset | Source | Use | Status |
|---|---|---|---|---|
| **D1** | Egyptian industrial tariff schedule (Aug 2024) | ✔ EgyptERA — egyptera.org/en/TarrifAug2024.aspx | Hard-coded into `egypt_grid_pricing.py`; drives cost calculation | Verified, transcribed |
| **D2** | Egyptian grid frequency time-series | ⚠ Synthetic; Gaussian noise around 50 Hz with rare 49.6 Hz dips, calibrated against ENTSO-E European grid patterns as a stand-in | State variable `grid_frequency` | Synthesized (no public real-time Egyptian Hz feed available) |
| **D3** | Future TOU schedule (proposed) | ⚠ Modelled from GUC Working Paper #29 (Ahmed et al.) | Dashboard "Tariff Reform Mode" toggle showing readiness | Proposal-derived |
| **D4** | EU CBAM carbon price schedule | ✔ European Commission CBAM regulation | ROI calculator linking kWh saved → tCO₂ → CBAM liability | Public schedule |
| **D5** | Egypt grid mix 2024 (81% gas, 7.5% oil, 7% hydro, 3% wind, 2% solar) | ✔ IEA Egypt country page; EIA Egypt brief; lowcarbonpower.org | Carbon-intensity calculation | Verified |
| **D6** | Egypt grid CO₂ emission factor | ✔ IEA / Climatiq: 0.45 kgCO₂/kWh (2017 baseline); Mansoura University research: ~0.50 kgCO₂/kWh | Scope 2 CO₂ counter on dashboard | Modelled within 0.45–0.50 range |
| **D7** | Egypt power-factor penalty rules (>500 kW industrial loads) | ✔ EgyptERA tariff doc + ResearchGate "Power factor and your electrical utility bill in Egypt" | PF lever in action space + penalty in reward | Verified mechanism |

### 6.2 EAF Operational Data

| ID | Dataset | Source | Use |
|---|---|---|---|
| **D8** | EAF heat profile (phase durations, power curves) | ✔ World Steel Association energy fact sheets; AIST EAF Efficiency presentation (Cappel, 2021); Wikipedia | Calibrate heat phase durations & power curves |
| **D9** | Power-curve per phase | ⚠ Synthesized from Cappel AIST presentation + textbook (Jones, Bowman, "EAF Steelmaking") | Sets max/min arc power per phase |
| **D10** | Oxygen-injection schedule | ⚠ Synthesized from More-Oxy / Linde EAF case studies | Default O₂ ramp curve |
| **D11** | Electrode consumption baseline | ✔ Mordor Intelligence graphite electrode market report; ResearchGate consumption studies — modern UHP: 1.2–2.0 kg/t | Sim baseline = 1.7 kg/t |
| **D12** | Wall-panel temperature dynamics | ⚠ Heat-transfer literature on water-cooled panels | Loss coefficient in thermal model |
| **D13** | Refractory wear curve | ⚠ Vesuvius / RHI Magnesita technical literature | Out of scope for v1; future stretch |
| **D14** | Ezz Ain Sokhna site specifics | ✔ Global Energy Monitor (gem.wiki/Ezz_Flat_Steel_Ain_Sokhna_plant); Arab Iron and Steel Union | Furnace size, capacity, manufacturer |

### 6.3 Public Reference Datasets (For Calibration & Credibility)

| ID | Dataset | Source | Use |
|---|---|---|---|
| **D15** | World Steel Association — Energy in the Steel Industry (2021 fact sheet) | ✔ worldsteel.org | Energy intensity benchmarks |
| **D16** | World Steel — World Steel in Figures 2024 / 2025 | ✔ worldsteel.org | EAF share of global production (29.1% in 2024) |
| **D17** | World Steel — Sustainability Indicators 2024 | ✔ worldsteel.org | Industry CO₂ intensity benchmarks |
| **D18** | IEA — Iron & Steel Roadmap | ✔ iea.org | Macro context; sector decarbonization pathways |
| **D19** | IEA Emissions Factors database (2025 edition) | ✔ iea.org/data-and-statistics/data-product/emissions-factors-2025 | Country-specific grid CO₂ |
| **D20** | EIA Egypt Country Analysis Brief (Aug 2024) | ✔ eia.gov/international/analysis/country/EGY | Generation mix |
| **D21** | EEHC Annual Report 2024 | ✔ eehc.gov.eg | Sector overview |
| **D22** | World Economic Forum Net-Zero Industry Tracker — Steel (2024) | ✔ weforum.org | Strategic context |
| **D23** | NREL industrial demand-response datasets | ✔ nrel.gov/grid/data-tools | Reference shapes for industrial load curves |
| **D24** | ENTSO-E transparency platform | ✔ transparency.entsoe.eu | European grid frequency reference for D2 synthesis |

### 6.4 Synthetic Data Generators (We Own These)

| Module | Generates | Realism Anchor |
|---|---|---|
| `simulator/factory_sim.py` | Top-level 3-second telemetry loop | Wall-clock + time-warp |
| `simulator/machines/eaf_machine.py` | Heat-phase state machine | Phase durations from D8/D15 |
| `simulator/machines/eaf_thermal_model.py` | Bath temperature dynamics | Energy-balance ODE (§4.4) |
| `simulator/machines/egypt_grid_pricing.py` | EGP/kWh per timestamp | D1 (current flat rate) + D3 (future TOU mode) |
| `simulator/events/overheat_event.py` | Wall-temp ramp-up | Linear injection |
| `simulator/events/electrode_break.py` | Phase-current dropout | Stochastic Bernoulli |
| `simulator/events/grid_spike_event.py` | Hz dip | Linear ramp ± noise |
| `simulator/events/transformer_alarm.py` | Transformer winding temp rise | Anchored to GEM-reported Nov 2024 EAF 2 incident |

### 6.5 RL Training Data

| ID | Dataset | Source | Volume | Use |
|---|---|---|---|---|
| **D25** | Synthetic episode replay | Generated by `OptiTwinEAFEnv.reset()` × ~50,000 episodes | ~500K transitions | PPO offline training |
| **D26** | Curriculum pack | Easy → Medium → Hard episode configs | 3 difficulty tiers | Curriculum learning |
| **D27** | Adversarial events pack | Replay of crisis events with random insertion | ~5K transitions | Robustness / safety training |
| **D28** | Pre-trained weights | `ai_engine/models/opti_twin_ppo.zip` | ~30 MB | Shipped with repo for instant demo |

### 6.6 XAI Reason Templates (Treated as Data)

| ID | Dataset | Use |
|---|---|---|
| **D29** | Reason template library — English | XAI engine fills slots based on action + state |
| **D30** | Reason template library — Arabic | Arabic-native team review; bilingual XAI |
| **D31** | Action label dictionary | Maps action vector → human-readable label |

### 6.7 Dashboard / Demo Assets

| ID | Asset | Source | Use |
|---|---|---|---|
| **D32** | Hero photo of EAF / steel plant | Wikimedia Commons (with attribution) | Dashboard hero + pitch deck |
| **D33** | Sample telemetry replay file | Captured 5-min run from sim | Fallback for demo if simulator crashes |
| **D34** | Pitch deck slides | Built in Figma/Slides | Judge handoff |

### 6.8 Datasets We Are NOT Using (and Why)

| Excluded | Why |
|---|---|
| Real proprietary Ezz Steel SCADA data | Not publicly available; pre-hackathon NDA infeasible |
| Vibration / acoustic furnace data | Out of scope for a 7-day build |
| Camera/vision feed of the bath | Hardware-specific |
| Ladle metallurgy data | Outside our control surface |
| Real-time ENTSO-E-style Egyptian grid feed | No public Egyptian equivalent of ENTSO-E transparency platform exists |

---

## 7. RL Formulation

### 7.1 Observation Space (State Vector)

| Group | Variable | Type | Range / Units |
|---|---|---|---|
| Economics | `current_electricity_price` | float | 1.60 EGP/kWh (current flat); reserved bands for future TOU |
| Economics | `is_peak_hour_flag` | bool | 0 (current) / 1 (TOU mode for testing) |
| Economics | `grid_frequency` | float | 49.5 – 50.5 Hz |
| Thermal | `furnace_bath_temp` | float | 1,200 – 1,680 °C |
| Thermal | `electrode_temp` | float | 1,500 – 3,000 °C |
| Thermal | `wall_panel_temp` | float | 80 – 250 °C |
| Thermal | `cooling_water_outlet_temp` | float | 25 – 55 °C |
| Production | `heat_progress_pct` | float | 0 – 100 |
| Production | `current_batch_weight` | float | 80 – 185 t |
| Production | `batches_completed_today` | int | 0 – 24 |
| Production | `production_backlog` | int | 0 – 5 |
| Electrical | `arc_power_mw` | float | 0 – 200 MW |
| Electrical | `power_factor` | float | 0.6 – 0.95 (penalty bracket below 0.92) |
| Electrical | `energy_this_heat_kwh` | float | 0 – 100,000 |
| Electrodes | `electrode_position_mm` | float | 0 – 500 |
| Electrodes | `electrode_consumption_rate` | float | kg/min |

Total: **16-D continuous + 1 boolean** observation, normalized to [0, 1] before PPO.

### 7.2 Action Space (Hybrid Multi-Discrete)

```python
actions = {
    "arc_power_setpoint":   range(60, 110, 5),   # MW (visual cap; site can run higher)
    "reactive_power_comp":  range(0, 30, 5),     # MVAR — capacitor banks
    "tap_changer_position": range(1, 25),         # int
    "charge_weight":        range(80, 185, 5),    # tons
    "heat_schedule":        ["start", "pause", "accelerate", "hold"],
    "oxygen_injection":     range(0, 500, 50),    # m³/hr
    "cooling_water_flow":   range(100, 400, 20),  # l/min
}
```

**Action masking:** any action that would push `wall_panel_temp > 250 °C`, `bath_temp < 1,500 °C`, or violate transformer thermal limits is masked at runtime — the agent literally cannot select unsafe actions.

### 7.3 Reward Function

```
R = α · E_saved_egp
  − β · M_stress_composite
  − γ · P_delay_penalty
  + δ · Quality_bonus
  − ε · Electrode_waste
  − ζ · PF_penalty            [NEW v2.0]
```

**Component definitions (v2.0):**

```
E_saved_egp     = (baseline_kwh − actual_kwh) × 1.60 EGP/kWh
                  (uses current verified flat tariff; agent generalizes if
                  TOU is enabled in the env)
M_stress        = max(0, wall_temp − 200) × 0.01
                + max(0, electrode_temp − 2800) × 0.001
P_delay_penalty = batches_behind_schedule × 500   (EGP equivalent)
Quality_bonus   = 1.0 if 1,600 ≤ final_bath_temp ≤ 1,650 else 0.0
Electrode_waste = electrode_consumption_rate × current_arc_power × 0.1
PF_penalty      = max(0, 0.92 − current_pf) × bill_estimate × 0.05
                  (anchors to verified Egyptian PF penalty mechanism)
```

**Default weights:** α = 1.0, β = 0.9, γ = 1.8, δ = 0.7, ε = 0.5, ζ = 0.8

**Preset profiles (selectable from dashboard):**

| Profile | α | β | γ | δ | ε | ζ | When to use |
|---|---|---|---|---|---|---|---|
| Cost-first | 2.0 | 0.5 | 1.0 | 0.5 | 0.3 | 1.5 | Mature factory, good equipment |
| Equipment-sensitive | 0.8 | 2.0 | 1.0 | 0.7 | 1.0 | 0.5 | Aging furnace, post-incident (e.g. Nov 2024 transformer) |
| Production-critical | 0.8 | 0.8 | 2.5 | 0.7 | 0.3 | 0.5 | Tight shipment SLAs |
| Quality-focused | 0.8 | 0.9 | 1.0 | 2.0 | 0.5 | 0.5 | High-grade steel orders |

### 7.4 Training Setup

| Item | Choice | Rationale |
|---|---|---|
| Algorithm | PPO (Stable Baselines3) | Stable, tunable, well-documented |
| Policy | MlpPolicy (2 × 256) | Sufficient for 16-D obs |
| Episode length | 1 simulated day = 480 steps (3 sim-min/step) | Captures full daily cycle |
| Total timesteps | 1M (curriculum) | ~30 min on RTX 3060 |
| Curriculum | Easy (no events) → Medium (1 event/episode) → Hard (multi-event) | Standard practice |
| Evaluation | 100-episode rolling mean reward | TensorBoard tracked |
| Save trigger | Every 100K timesteps + best-mean checkpoint | Multiple fallbacks |

### 7.5 XAI Engine (Reason Generator)

The XAI engine is a **template-based explainer** seeded by reward-component contributions. It is NOT an LLM — judges and operators expect deterministic, auditable reasons.

```python
def generate_reason(action, state, reward_components):
    dominant = argmax(reward_components.contributions)
    template = TEMPLATES[action.label][dominant]
    return template.format(**state.as_dict())
```

Example output:

```
[18:00:03] ACTION: REDUCE_ARC_POWER + RAISE_PF_COMPENSATION
MAGNITUDE: 90 MW → 75 MW (−17%); reactive comp +10 MVAR
REASON: Power factor 0.81 below 0.92 reference; Egyptian
        UHV tariff penalty bracket. Bath at 1,548 °C — safe
        for moderate reduction (>1,500 °C maintains liquidity).
        Backlog = 0. Estimated bill impact: −2,400 EGP/hr.
HEALTH: SAFE ✅
```

---

## 8. Simulation Engine Design

### 8.1 Time Model

| Concept | Real-world | Simulated |
|---|---|---|
| Real wall-clock second | 1 s | 15 simulated minutes (display only) |
| Physics integration step `dt` | — | Fixed at 3 sim-seconds; independent of display warp |
| Demo: 17:45 → 18:00 (peak start, when in TOU mode) | ~60 real s | 15 sim min |
| Demo: full 24 h | ~96 real s | 24 sim h |

> **Important:** `SIM_TIME_WARP_MINUTES=15` means the **clock display** advances 15× faster, but the physics integration step `dt` stays 3 seconds (sim time) per tick. This keeps the thermal model numerically stable and makes the simulator deterministic regardless of host CPU speed.

### 8.2 Telemetry Payload (Every 3 sec Real-Time)

```json
{
  "machine_id":               "EAF_02_EZZ_AIN_SOKHNA",
  "machine_type":             "Electric Arc Furnace",
  "factory":                  "Ezz Flat Steel — Ain Sokhna Complex",
  "manufacturer":             "Danieli",
  "rated_capacity_tpa":       1600000,
  "timestamp":                "2026-05-07T18:32:07Z",
  "arc_power_mw":             87.3,
  "energy_kwh":               43650.0,
  "energy_this_heat_kwh":     18420.0,
  "power_factor":             0.81,
  "pf_penalty_bracket":       true,
  "furnace_bath_temp":        1548.2,
  "electrode_temp":           2650.0,
  "wall_panel_temp":          187.4,
  "cooling_water_outlet_temp": 42.1,
  "heat_progress_pct":        72.4,
  "current_batch_weight":     180.0,
  "batches_today":            6,
  "production_backlog":       0,
  "electricity_price":        1.60,
  "tariff_class":             "UHV_220-132kV",
  "tou_mode":                 false,
  "grid_frequency":           49.98,
  "electrode_position_mm":    245.0,
  "electrode_consumption_kg": 0.043,
  "oxygen_injection_m3hr":    320.0,
  "status":                   "MELTING_PHASE_2"
}
```

### 8.3 Crisis Injection API

```http
POST /api/v1/sim/inject  { "event": "wall_overheat" | "electrode_break" | "grid_spike" | "transformer_alarm" }
```

Used by the dashboard "Inject Crisis" button. The simulator listens on this internal endpoint and modifies its state machine accordingly.

---

## 9. Backend & API Contracts

### 9.1 Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/telemetry` | Edge → backend telemetry ingest |
| GET | `/api/v1/recommendation` | Latest AI decision for current state |
| GET | `/api/v1/stats` | Aggregated KPIs (savings, batches, alerts) |
| POST | `/api/v1/ai/toggle` | Turn AI agent ON/OFF |
| POST | `/api/v1/ai/profile` | Switch reward preset |
| POST | `/api/v1/sim/inject` | Inject crisis event |
| POST | `/api/v1/tariff/mode` | Toggle current-flat vs future-TOU tariff (planning mode) |
| WS | `/ws/live-feed` | Realtime stream → dashboard |

### 9.2 Pydantic Schemas

```python
class TelemetryInput(BaseModel):
    machine_id: str
    timestamp: datetime
    arc_power_mw: float = Field(ge=0, le=250)
    furnace_bath_temp: float = Field(ge=0, le=1700)
    wall_panel_temp: float = Field(ge=0, le=300)
    power_factor: float = Field(ge=0, le=1)
    electricity_price: float = Field(ge=0)        # 1.60 default (EGP/kWh, UHV)
    tariff_class: Literal["UHV_220-132kV", "HV_66-33kV", "MV_22-11kV"]
    tou_mode: bool = False
    # ... full set per §8.2

class RecommendationOutput(BaseModel):
    timestamp: datetime
    action_label: str
    action_magnitude_pct: float
    estimated_savings_egp_per_hour: float
    pf_penalty_avoided_egp: float
    co2_saved_kg: float
    xai_reason: str           # English
    xai_reason_ar: str        # Arabic
    machine_health: Literal["SAFE", "WARNING", "CRITICAL"]
    production_status: Literal["ON_TRACK", "AT_RISK", "BEHIND"]
    reward_components: dict[str, float]

class KPISnapshot(BaseModel):
    egp_saved_today: float
    batches_completed: int
    avg_arc_power_mw: float
    avg_power_factor: float
    co2_saved_kg: float
    thermal_incidents_today: int
```

### 9.3 Logging

JSON logs, one decision per line, pushed both to stdout and `logs/decisions.jsonl`. Each entry includes timestamp, action, reason, savings_est, reward_components. Used for post-hoc analysis and audit trail (a deployment requirement under typical industrial change-control regimes).

---

## 10. Frontend Dashboard

### 10.1 Layout (Single Page)

```
┌───────────────────────────────────────────────────────────────────────┐
│  KPIBanner: 💰 Saved Today | ⚡ Cost Now | 🏭 Health | 🌡️ Bath | PF │
├──────────────────────┬───────────────────────┬────────────────────────┤
│   EnergyChart        │   ThermalGauge        │  EAFStatusCard         │
│   (live, 5-min       │   (1,200 – 1,680 °C  │   - Heat phase         │
│    rolling window)   │    bath; 80–250 wall) │   - Progress %         │
│                      │                       │   - Batch #            │
├──────────────────────┴───────────────────────┴────────────────────────┤
│  XAIDecisionLog (newest on top, EN + AR toggle)                       │
├───────────────────────────────────────────────────────────────────────┤
│  Controls: AIToggle | Inject Crisis ▼ | Reward Profile ▼ | Tariff Mode│
└───────────────────────────────────────────────────────────────────────┘
```

### 10.2 Components

| Component | Lib | Notes |
|---|---|---|
| `EnergyChart.tsx` | Recharts | Red zone overlay only when `tou_mode=true` |
| `ThermalGauge.tsx` | react-gauge-component / custom SVG | Two needles: bath, wall |
| `EAFStatusCard.tsx` | Tailwind | Phase, progress %, batch #, manufacturer = Danieli |
| `XAIDecisionLog.tsx` | Virtuoso | Auto-scrolls; EN/AR toggle |
| `KPIBanner.tsx` | Tailwind grid | Animated counter on EGP saved + PF gauge |
| `AIToggle.tsx` | Tailwind switch | POST /api/v1/ai/toggle |
| `CrisisInjector.tsx` | Tailwind dropdown | POST /api/v1/sim/inject |
| `ProfileSelector.tsx` | Tailwind select | POST /api/v1/ai/profile |
| `TariffModeSelector.tsx` | Tailwind toggle | "Current (Flat 1.60 EGP)" vs "Reform Mode (TOU)" |

### 10.3 WebSocket Client

```typescript
const ws = new ReconnectingWebSocket('ws://localhost:8000/ws/live-feed');
ws.onmessage = (msg) => dispatch(JSON.parse(msg.data));
```

Auto-reconnect, exponential backoff. Dashboard never goes blank during demo.

---

## 11. DevOps, Docker, and Environment

### 11.1 docker-compose.yml (final shape)

```yaml
version: "3.9"
services:
  redis:
    image: redis:7-alpine
    networks: [opti-twin-network]

  ai_engine:
    build: ./ai_engine
    environment:
      - RL_ALPHA=1.0
      - RL_BETA=0.9
      - RL_GAMMA=1.8
      - RL_DELTA=0.7
      - RL_EPSILON=0.5
      - RL_ZETA=0.8
      - MACHINE_TYPE=EAF
      - MODEL_PATH=/app/models/opti_twin_ppo.zip
    depends_on: [redis]
    networks: [opti-twin-network]

  simulator:
    build: ./simulator
    environment:
      - SIM_MACHINE=EAF_02_EZZ_AIN_SOKHNA
      - SIM_INTERVAL_SECONDS=3
      - SIM_TIME_WARP_MINUTES=15
      - SIM_START_HOUR=17.75
      - TARIFF_CLASS=UHV_220-132kV
      - TARIFF_RATE_EGP_PER_KWH=1.60
      - TOU_MODE_DEFAULT=false
      - PF_REFERENCE=0.92
      - GRID_CO2_INTENSITY_KG_PER_KWH=0.50
      - EAF_RATED_TPA=1600000
      - EAF_FURNACE_SIZE_T=185
      - EAF_MAX_POWER_MW=110
      - EAF_MIN_POWER_MW=60
      - FURNACE_MAX_WALL_TEMP=250
      - FURNACE_TARGET_BATH_TEMP=1630
    depends_on: [backend]
    networks: [opti-twin-network]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [redis]
    networks: [opti-twin-network]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
    networks: [opti-twin-network]

networks:
  opti-twin-network:
    driver: bridge
```

### 11.2 CI / Local Validation

| Check | Tool | When |
|---|---|---|
| Backend unit tests | pytest | Pre-commit |
| Schema validation | mypy + pydantic-strict | CI |
| Frontend type check | tsc --noEmit | CI |
| Integration smoke | docker-compose up + 30 s health probe | CI nightly |
| Tariff sanity test | Assert simulator emits 1.60 EGP/kWh in current mode | CI |

### 11.3 Repo Hygiene

- `.gitignore`: `.env`, `node_modules/`, `__pycache__/`, `*.zip` (except `ai_engine/models/opti_twin_ppo.zip`).
- Direct commit for the 30 MB pre-trained model.
- Demo branch `demo-day` frozen on Day 6.

---

## 12. 7-Day Execution Roadmap

| Day | Date | Goal | Owner | Done When |
|---|---|---|---|---|
| **D1** | May 1 (today) | Lock plan v2.0; scaffold all 4 services with stubs; docker-compose up green | Tech Lead | All 4 containers healthy |
| **D2** | May 2 | EAF simulator emits realistic telemetry every 3 s with verified tariff (1.60 EGP/kWh flat) | Backend/Sim | Telemetry visible via `redis-cli SUBSCRIBE factory.telemetry` |
| **D3** | May 3 | Custom Gym env + reward function (incl. PF penalty); PPO begins training | AI/ML | TensorBoard shows monotonically improving reward |
| **D4** | May 4 | Backend endpoints + Pydantic schemas + WS broadcast; XAI engine v1 (English) | Tech Lead | Dashboard receives recommendation messages over WS |
| **D5** | May 5 | Dashboard MVP: chart, gauge, log, toggle, tariff-mode selector — wired live | Frontend | Toggle AI → action in log → chart flattens |
| **D6** | May 6 | Crisis events; AR translations; preset profiles; pre-trained model frozen; pitch deck v1 | All | Demo script run-through ×3 with no human intervention |
| **D7** | May 7 | Demo dress rehearsal; capture fallback `demo_replay.jsonl`; final polish | All | Demo runs in 3:00 ± 0:15 |

### Critical Path

```
[Sim emits] → [Backend ingests] → [AI returns action] → [WS broadcast] → [Dashboard renders]
                                       ↑
                  [PPO trained model loaded — D3 in parallel]
```

Anything not on this path (preset profiles, AR translations, electrode-break event) is **stretch** — cut without remorse if D5 slips.

---

## 13. Team & Ownership

| Role | Owner | Owns | Day-by-day deliverable |
|---|---|---|---|
| Tech Lead / Architect | TBD | `docker-compose.yml`, `backend/main.py`, `schemas.py` | D1 scaffold → D4 endpoints → D7 polish |
| AI / ML Engineer | TBD | `ai_engine/environment.py`, `ai_engine/agent.py`, `reward_function.py`, training pipeline | D2 env stub → D3 train → D6 freeze model |
| Frontend Engineer | TBD | `frontend/components/` | D2 layout shell → D5 live-wired → D6 polish |
| Backend / Simulator | TBD | `simulator/factory_sim.py`, `simulator/machines/`, `services/redis_broker.py` | D2 telemetry → D4 events → D6 inject API |

### Communication Cadence

- 09:00 daily standup (15 min): yesterday / today / blockers.
- Slack/Discord channel `#opti-twin`.
- Demo dry-runs: D6 18:00, D7 09:00, D7 14:00.

---

## 14. Risk Register & Mitigations

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | PPO training diverges or under-performs | M | H | Curriculum + reward clipping; fallback to scripted policy | AI/ML |
| R2 | Time-warp causes physics instability | L | H | Fix `dt=3 s` regardless of warp; unit tests on `update_bath_temp` | Sim |
| R3 | Demo laptop can't run all 5 containers | L | H | Pre-test on every team laptop D5; backup laptop ready | Tech Lead |
| R4 | WebSocket connection drops mid-demo | M | M | Auto-reconnect + offline replay fallback file | Frontend |
| R5 | Judges question realism of savings claim | M | M | Source every figure; cite EgyptERA, worldsteel, IEA inline; show §15.2 ROI | All |
| R6 | Wall overheat event fires too early/late | L | L | Manual button trigger only during demo | Sim |
| R7 | AR translations lag English | M | L | Ship EN-only if translator unavailable; AR is stretch | XAI |
| R8 | Internet down at venue | M | H | Fully offline; no external API calls; pre-pull all Docker images | Tech Lead |
| R9 | Team member illness | L | H | Cross-train: each owner has a backup who can demo | All |
| R10 | Reward weights cause agent oscillation | M | M | Action-rate-of-change penalty; EMA smoothing on actions | AI/ML |
| R11 | Pydantic schema mismatch between sim & backend | M | M | Single shared `schemas.py`; sim imports from same package | Tech Lead |
| R12 | Judges challenge tariff numbers | L | H | Have EgyptERA Aug 2024 page open in second tab as proof | Tech Lead |

---

## 15. Success Metrics & Judge-Facing KPIs

### 15.1 What the Judges See on the Dashboard

```
┌──────────────────────────────────────────────────┐
│  ⚡ Energy Intensity     ↓ 8% (450 → 414 kWh/t)  │
│  🏭 Production           = 100% (ON TRACK)       │
│  🌡️  Furnace Health      = SAFE ✅                │
│  💰  Saved Today          = 314,000 EGP (model.) │
│  🔌 Power Factor         = 0.92 (target met)     │
│  🔩  Electrode Lifespan   ↑ 12% (longer)         │
│  ♻️  CO₂ Saved Today      = 6.5 tonnes           │
└──────────────────────────────────────────────────┘
```

> ⚠ All daily numbers are **modelled estimates** during a simulated 24-hour cycle, not measurements from a live factory.

### 15.2 ROI Stack for Pilot Discussions

| Lever | Annual upside per furnace | Confidence |
|---|---|---|
| 5–10% energy intensity reduction | 58–115M EGP | ⚠ Modelled (literature: 5–15% achievable with advanced control) |
| Power-factor penalty avoidance | 30–60M EGP | ✔ Mechanism verified (Egypt PF rules); magnitude varies by site |
| Equipment-incident avoidance | 5–20M EGP | ⚠ Modelled (anchored to Nov 2024 transformer-failure precedent) |
| CBAM-compliant lower carbon intensity | Strategic / export-revenue protection | ✔ Mechanism real |
| **Estimated total** | **~95–195M EGP/yr per furnace** | ⚠ Modelled range |

> Realistic pilot economics: a closed-loop deployment cost of $200–500K (incl. integration, change-management, validation) pays back in <12 months on a single 1.6 Mtpa furnace, even at the conservative end of the range.

### 15.3 Internal Hackathon Success Bar

| Bar | Required for | Status target |
|---|---|---|
| Bronze | Working dockerized end-to-end | D5 |
| Silver | AI toggle visibly changes behavior | D5 |
| Gold | Crisis event handled by β-override on demo | D6 |
| Platinum | EN+AR XAI + 4 reward profiles + CO₂ counter + tariff-mode toggle | D7 stretch |

### 15.4 Pre-Demo Readiness Checklist

```
□ docker-compose up --build runs without errors
□ EAF_02 sends data every 3 seconds on Redis channel: factory.telemetry
□ Dashboard displays: bath temperature, arc power, current price (1.60 EGP/kWh)
□ AI Toggle actually changes agent behavior
□ XAI Log shows logical, human-readable reasons in English
□ "Inject Wall Overheat" raises wall_panel_temp above 200°C
□ KPI "Total Saved Today" accumulates in EGP with realistic numbers
□ Power Factor gauge moves toward 0.92 when AI is on
□ Tariff-mode toggle switches between flat (current) and TOU (future) without breaking
□ AI responds to wall overheat with EMERGENCY_COOLING within 3 seconds
□ Pre-trained model loads at container startup (no live training)
□ Demo replay fallback file (demo_replay.jsonl) ready
□ Pitch deck PDF on USB stick (offline backup)
□ EgyptERA Aug 2024 tariff page bookmarked for source-questioning judges
```

---

## 16. Demo Script

```
┌──────────────────────────────────────────────────────────────────────┐
│               DEMO SCRIPT — EAF EDITION — 3 MINUTES                 │
│              For Judges at NextCity AI Hack 2026                     │
└──────────────────────────────────────────────────────────────────────┘

  STEP 1 — Baseline (0:00 – 0:40)
  ─────────────────────────────────
  ► Show dashboard: EAF_02 (Ezz Flat Steel Ain Sokhna, 1.6 Mtpa)
    running at 90 MW, power factor 0.78
  ► KPI: "Current cost rate: 1.60 EGP/kWh (UHV flat tariff,
           EgyptERA Aug 2024) = 144,000 EGP/hour"
  ► KPI: "Power factor 0.78 — below 0.92 reference, in penalty bracket"
  ► Say: "This is a model of a real Danieli 185-tonne furnace at
           Ezz Flat Steel Ain Sokhna, started 2023, allocated
           200 MW by the Supreme Council of Energy. The numbers
           on this dashboard come from EgyptERA, the IEA, and
           Global Energy Monitor — all sourced."

  STEP 2 — Activate AI Agent (0:40 – 1:30)
  ──────────────────────────────────────────
  ► Press AI Toggle → ON
  ► XAI Log populates instantly (EN + AR side-by-side):
      [time] ACTION: REDUCE_ARC_POWER (−12%) + RAISE_PF_COMPENSATION
             REASON: PF 0.78 below 0.92 reference, penalty bracket.
                     Bath at 1,548°C, safe for moderate reduction.
                     Backlog = 0.
             EST. BILL IMPACT: −2,400 EGP/hr
  ► Energy chart visibly drops; PF gauge climbs toward 0.92
  ► "Total Saved Today" KPI begins climbing

  STEP 3 — Switch to Tariff-Reform Mode (1:30 – 2:00)
  ──────────────────────────────────────────────────────
  ► Click "Tariff Reform Mode (TOU)" toggle
  ► Display flips: "Future TOU price: 2.50 EGP/kWh peak (modelled
                    per GUC Working Paper #29 proposal)"
  ► AI immediately reduces arc power further; XAI explains:
      ACTION: PRE-PEAK ENERGY-INTENSITY DROP
      REASON: Anticipated TOU peak in 30 min (planning mode).
              Furnace already over halfway through heat. Dropping
              arc power 90 → 65 MW saves est. 18,000 EGP/hr if
              TOU activates. Reform-readiness demonstrated.
  ► Say: "When Egypt introduces industrial TOU pricing — and
           academic literature is already proposing it — this
           system is already designed for it."

  STEP 4 — Inject Wall Overheat Crisis (2:00 – 2:35)
  ────────────────────────────────────────────────────
  ► Press "Inject Wall Overheat"
  ► Wall panel temp spikes: 187°C → 223°C  (limit: 200°C!)
  ► XAI Log responds:
      ACTION: EMERGENCY_COOLING (+120 l/min)
      REASON: Wall panel 223°C exceeded 200°C threshold.
              β-weight override: machine protection overrides
              energy savings. Avoiding incident class similar
              to Nov 2024 EAF #2 transformer failure.
  ► Temperature drops back to safe range within 30 sim seconds

  STEP 5 — Closing KPI Reveal (2:35 – 3:00)
  ───────────────────────────────────────────
  ► Click "Show Daily Summary"
  ► Final card animates in:
      ⚡ Energy intensity ↓8% | 🏭 Prod 100% | 🌡️ SAFE
      💰 Modelled saving: 314,000 EGP today
      🔌 PF held at 0.92 | ♻️ CO₂ ↓6.5 t today
  ► Closing line: "Modelled annual upside: 95–195 million EGP
                   per furnace, with payback under 12 months
                   on a real pilot."
```

---

## 17. Post-Hackathon Roadmap

| Phase | Item | Why |
|---|---|---|
| Month 1 | Outreach to Ezz Steel ops / Ministry of Electricity demand-response unit | Get a shadow-mode pilot conversation started |
| Month 1–2 | Sim-to-real PPO transfer using shadow-mode logs (read-only SCADA tap) | Prove out without touching production |
| Month 3 | Add second machine type (rolling-mill reheat furnace) | Multi-machine fleet optimization |
| Month 4 | CBAM dashboard tying kWh saved → tCO₂ → CBAM price | Sustainability monetization for export-facing CFOs |
| Month 6 | Edge-deployment binary (no cloud needed) | Enterprise-sales requirement for industrial buyers |
| Month 9 | Multi-tenant offering for SME factories | Scale beyond Ezz-class sites |

---

## 18. Assumptions & Limitations

This section is required reading before any technical or investor discussion.

### 18.1 Synthetic-Data Limitations

* **No real SCADA data.** Opti-Twin v1.0 is trained and evaluated entirely on a synthetic simulator. We do not have access to real Ezz Steel (or any other) shop-floor telemetry. Any sim-to-real transfer will require a shadow-mode deployment phase (see §19).
* **Physics model is zero-dimensional.** The bath thermal model in §4.4 is a single-volume energy-balance equation. It does not capture spatial gradients, slag dynamics, electrode shadowing, or post-combustion. Real EAF simulators (e.g. Danieli Q-MELT) are CFD-based.
* **No real grid-frequency feed.** Egypt does not publish a real-time grid frequency stream comparable to ENTSO-E. We synthesize a Gaussian-noise feed around 50 Hz, calibrated to ENTSO-E shapes as a stand-in.
* **No real heat-by-heat scrap chemistry.** We model batch weight and feedstock mix at coarse granularity only.

### 18.2 Tariff & Regulatory Assumptions

* **Egyptian industrial UHV tariff is flat at 1.60 EGP/kWh (Aug 2024)** — verified from EgyptERA. Future revisions are likely; we re-fetch on every deploy.
* **Time-of-use industrial pricing does not currently exist** for Ultra-High Voltage customers in Egypt. Our "Tariff Reform Mode" is a planning scenario based on academic proposals (GUC Working Paper #29), not a current rate.
* **Power-factor penalty mechanism is real** for industrial loads >500 kW (per EgyptERA tariff doc and ResearchGate publication "Power factor and your electrical utility bill in Egypt"), but the exact site-specific penalty depends on each customer's bilateral PPA terms — magnitudes in §15.2 are illustrative.
* **CBAM exposure** depends on Ezz's actual EU export volume, which is not public.

### 18.3 Modelled Numbers vs. Verified Numbers

| Class | Examples |
|---|---|
| ✔ Verified | Tariff (1.60 EGP/kWh), PF reference (0.92), grid mix (~81% gas), Ezz furnace size (185 t), Ezz EAF 2 capacity (1.6 Mtpa), Danieli manufacturer, Nov 2024 transformer failure on EAF 2 |
| ⚠ Estimated | Annual savings range (95–195M EGP), CO₂ saved per day, "thermal incidents −90%", power-factor penalty magnitude |
| 🔧 Synthesized | All telemetry streams (the sim is the data source) |

### 18.4 What This Project Does NOT Claim

* Does **not** claim the agent will work on a real furnace without further engineering, validation, and a shadow-mode phase.
* Does **not** claim Ezz Steel uses or endorses this system.
* Does **not** claim the displayed daily savings are achievable in production without a multi-month pilot.
* Does **not** publish proprietary or NDA-protected data.

---

## 19. Real-World Deployment Strategy

This section turns the hackathon prototype into a credible pilot conversation. It anticipates the standard questions a CTO, plant manager, or process-engineering lead will ask.

### 19.1 Three-Phase Deployment

```
PHASE 1 — SHADOW MODE  (3–6 months)
  ▸ Read-only SCADA tap (OPC UA / Modbus gateway)
  ▸ Agent computes recommendations; operator sees them on a side
    monitor; agent never writes to the PLC
  ▸ Goal: validate that the agent's recommendations align with
    operator best-practice in 90%+ of decisions, and that the
    energy-savings forecast tracks real bills

PHASE 2 — ADVISORY MODE  (3–6 months)
  ▸ Recommendations presented in the operator HMI with one-click
    "ACCEPT" / "OVERRIDE" buttons
  ▸ All accepts/overrides logged for retraining
  ▸ Goal: 60%+ accept rate; documented operator-trust level

PHASE 3 — CLOSED-LOOP  (after 6+ months of advisory)
  ▸ Agent writes setpoints directly via constrained interface
    (whitelist of safe action ranges only)
  ▸ Hard physical limits enforced by PLC, not agent
  ▸ Operator can hit master-stop at any time
  ▸ Continuous monitoring with auto-rollback to manual mode on
    any safety-envelope violation
```

### 19.2 SCADA & PLC Integration

| Layer | Standard | Use |
|---|---|---|
| Field bus | Modbus / Profibus / Profinet | Existing factory wiring; do not modify |
| SCADA gateway | OPC UA (IEC 62541) | Industry-standard read/write; supported by Danieli Q-Suite, Siemens SIMATIC, ABB 800xA |
| Edge agent | Containerized Python; OPC UA client (asyncua) | Reads telemetry, posts to backend |
| PLC interface (Phase 3 only) | OPC UA write tags with whitelist | Constrained setpoint writes only; PLC enforces safety |

> **Cybersecurity note:** all OPC UA connections use mutual TLS with certificates managed by the customer's PKI. The Opti-Twin container runs in a DMZ with read-only access by default. Phase 3 closed-loop write access is gated by a customer-side firewall ACL.

### 19.3 Safety Constraints (Hard Floor — Non-Negotiable)

| Constraint | Enforcement |
|---|---|
| Wall panel temp must never exceed 250 °C | PLC hard limit + agent action-mask |
| Bath temp must never drop below 1,500 °C during a heat | Agent action-mask |
| Transformer rated MVA must not be exceeded | PLC hard limit |
| Arc current must not exceed transformer secondary rating | PLC hard limit |
| Operator master-stop overrides agent always | Hardwired, not software |
| Agent commanded power-rate-of-change capped (no step changes) | Software low-pass filter |
| Auto-rollback to manual mode on N consecutive safety-envelope violations | Software watchdog |

### 19.4 Change Management

* Operator training: 2-day classroom + 1-week supervised shadow shifts.
* Joint commissioning protocol with the SCADA vendor (Danieli, Siemens, ABB).
* Rollback procedure: single button takes the system back to baseline manual control with no data loss.
* Quarterly model retrain on the customer's actual data, with regression testing against a frozen safety-test pack.

### 19.5 Validation & Audit

* All decisions logged in the customer's Historian (PI System / Wonderware).
* Monthly KPI reconciliation: model-claimed savings vs. metered savings vs. invoiced electricity bill.
* External energy-management audit annually (ISO 50001-aligned; Ezz Ain Sokhna is already ISO 50001 certified per GEM).

---

## 20. Sources & References

All figures in this document are anchored to one or more of the references below. Where two or more sources disagreed, we used the most recent and authoritative.

### 20.1 Energy & Tariff (Egypt)

* **EgyptERA — Egyptian Electric Utility & Consumer Protection Regulatory Agency.** "Current Electricity Tariff", August 2024 schedule. <https://egyptera.org/en/TarrifAug2024.aspx>
* **EgyptERA.** Annual electricity tariff page (2024). <https://egyptera.org/en/Tarrif2024N.aspx>
* **EEHC — Egyptian Electricity Holding Company.** Annual Report 2024. <https://www.eehc.gov.eg/CMSEehc/Files/AnnualReport2024En.pdf>
* **Wikipedia.** "Egyptian Electricity Holding Company". <https://en.wikipedia.org/wiki/Egyptian_Electricity_Holding_Company>
* **Global Transmission Report.** "Egypt unbundles EETC, establishes independent transmission operator." <https://globaltransmission.info/egypt-unbundles-eetc-establishes-independent-transmission-operator/>
* **Trade.gov (US Commerce Dept).** Egypt — Electricity and Renewable Energy. <https://www.trade.gov/country-commercial-guides/egypt-electricity-and-renewable-energy>
* **Zawya.** "Understanding Egypt's electricity tariff increases". <https://www.zawya.com/en/economy/north-africa/understanding-egypts-electricity-tariff-increases-mmvvqa6k>
* **Riad-Riad.** "Electricity and Renewable Energy Regulations in Egypt — update". <https://riad-riad.com/electricity-and-renewable-energy-regulations-egypt-update/>
* **Ahmed et al., German University in Cairo — Working Paper #29.** "The Egyptian Electricity Market: Designing a Prudent Peak Load Pricing Model." <https://ideas.repec.org/p/guc/wpaper/29.html>
* **El Bahay & El Magd / ResearchGate.** "Power factor and your electrical utility bill in Egypt." <https://www.researchgate.net/publication/3274579_Power_factor_and_your_electrical_utility_bill_in_Egypt>
* **El-Hagry / ResearchGate.** "The Most Economical Power Factor Correction According to Tariff Structures in Egypt." <https://www.researchgate.net/publication/3275059_The_Most_Economical_Power_Factor_Correction_According_to_Tariff_Structures_in_Egypt>
* **GlobalPetrolPrices.com.** Egypt electricity prices, September 2025. <https://www.globalpetrolprices.com/Egypt/electricity_prices/>

### 20.2 Energy & Carbon (International)

* **IEA — International Energy Agency.** Egypt country page (electricity, emissions, natural gas). <https://www.iea.org/countries/egypt>; <https://www.iea.org/countries/egypt/emissions>; <https://www.iea.org/countries/egypt/natural-gas>
* **IEA.** Emissions Factors 2025 (data product). <https://www.iea.org/data-and-statistics/data-product/emissions-factors-2025>
* **IEA.** Future of Electricity in MENA — executive summary. <https://www.iea.org/reports/the-future-of-electricity-in-the-middle-east-and-north-africa/executive-summary>
* **EIA — US Energy Information Administration.** Egypt Country Analysis Brief, August 2024. <https://www.eia.gov/international/content/analysis/countries_long/Egypt/pdf/Egypt.pdf>
* **Ember.** Egypt country profile. <https://ember-energy.org/countries-and-regions/egypt/>
* **Climatiq.** Emission Factor — Electricity supplied from grid, Egypt. <https://www.climatiq.io/data/emission-factor/2c8aa104-7e2e-4bae-af32-c054e9bc4d7f>
* **Lowcarbonpower.org.** Egypt electricity generation mix 2024. <https://lowcarbonpower.org/region/Egypt>
* **Our World in Data.** Egypt CO₂ profile. <https://ourworldindata.org/co2/country/egypt>
* **European Commission.** Carbon Border Adjustment Mechanism (CBAM). <https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en>

### 20.3 Steel Industry (EAF Specifics)

* **World Steel Association.** Energy use in the steel industry — fact sheet (2021). <https://worldsteel.org/wp-content/uploads/Fact-sheet-energy-in-the-steel-industry-2021-1.pdf>
* **World Steel Association.** World Steel in Figures 2024 / 2025. <https://worldsteel.org/data/world-steel-in-figures/world-steel-in-figures-2024/>
* **World Steel Association.** Sustainability Indicators report 2024. <https://worldsteel.org/wp-content/uploads/Sustainability-Indicators-report-2024.pdf>
* **World Economic Forum.** Steel Industry Net-Zero Tracker 2024. <https://reports.weforum.org/docs/WEF_Net_Zero_Industry_Tracker_2024_Steel.pdf>
* **AIST / Cappel.** EAF Efficiency presentation, MENA 2021. <https://www.aist.org/AIST/aist/AIST/Conferences_Exhibitions/MENA/Presentations/AIST_MENA_EAF-Efficiency_Cappel.pdf>
* **Wikipedia.** Electric arc furnace. <https://en.wikipedia.org/wiki/Electric_arc_furnace>
* **GMK Center.** "The share of EAF in global steel production in 2024 increased to 29.1%." <https://gmk.center/en/news/the-share-of-eaf-in-global-steel-production-in-2024-increased-to-29-1/>
* **Mordor Intelligence.** Graphite Electrode Market Report. <https://www.mordorintelligence.com/industry-reports/graphite-electrode-market>
* **Sangraf / Graptek / NL Graphite.** Graphite electrode product literature.
* **IRENA.** Iron and steel decarbonization. <https://www.irena.org/Decarbonising-hard-to-abate-sectors-with-renewables-Enablers-and-recommendations/Industry-sector/Iron-and-steel>

### 20.4 Ezz Steel & Site Specifics

* **Global Energy Monitor.** Ezz Flat Steel Ain Sokhna plant. <https://www.gem.wiki/Ezz_Flat_Steel_Ain_Sokhna_plant>
* **Global Energy Monitor.** Al-Ezz Dekheila Steel Alexandria plant. <https://www.gem.wiki/Al-Ezz_Dekheila_Steel_Alexandria_plant>
* **Ezz Steel.** Suez steelmaking plant. <https://www.ezzsteel.com/ezz-steel-plants/suez-steelmaking-plant>
* **Arab Iron and Steel Union.** Prime Minister visits Ezz Steel in Ain Sokhna. <https://aisusteel.org/en/25087/>
* **More-Oxy.** M-ONE injection technology upgrade at Ezz Flat Steel, Egypt. <https://more-oxy.com/m-one-injection-technology-upgrading-improve-performances-at-ezz-flat-steel-egypt/>
* **Wikipedia.** Ezz Steel. <https://en.wikipedia.org/wiki/Ezz_Steel>

### 20.5 AI / ML / RL

* **Stable Baselines3.** PPO documentation. <https://stable-baselines3.readthedocs.io/>
* **Gymnasium.** Custom environment guide. <https://gymnasium.farama.org/>
* **Schulman et al. (2017).** Proximal Policy Optimization Algorithms. arXiv:1707.06347.
* **Sutton & Barto (2018).** Reinforcement Learning: An Introduction (2nd ed.).

### 20.6 Standards & Compliance

* **IEC 62541.** OPC Unified Architecture.
* **ISO 50001.** Energy management systems. (Ezz Ain Sokhna site is certified per GEM.)
* **ISO 14001.** Environmental management systems. (Ezz Ain Sokhna certified.)
* **ISA-95.** Enterprise-control system integration.

---

## 21. Appendix: Glossary

| Term | Meaning |
|---|---|
| **EAF** | Electric Arc Furnace — uses graphite electrodes & high current to melt scrap (and DRI in Ezz's case) into steel |
| **Heat** | One full melt cycle (45–65 min) producing 80–185 t of liquid steel |
| **Tap** | Pouring molten steel from furnace into ladle |
| **Bath** | The molten metal pool inside the furnace |
| **Tap-changer** | Transformer setting that adjusts secondary voltage to control arc power |
| **Power factor** | Ratio of real to apparent power; <1 means reactive losses on the bill |
| **MORL** | Multi-Objective Reinforcement Learning |
| **PPO** | Proximal Policy Optimization (RL algorithm) |
| **XAI** | Explainable AI — producing human-readable reasons for each decision |
| **CBAM** | EU Carbon Border Adjustment Mechanism — carbon price on iron/steel imports |
| **SCADA** | Supervisory Control and Data Acquisition — industrial control system layer |
| **MVA / MVAR** | Megavolt-amperes / Megavolt-amperes reactive — apparent / reactive power |
| **Refractory** | Heat-resistant lining inside the furnace shell |
| **Slag** | Non-metallic byproduct floating on the bath; managed via oxygen lancing |
| **DRI** | Direct Reduced Iron — alternative iron-making feedstock to scrap |
| **UHV / HV / MV** | Ultra-High / High / Medium Voltage — Egyptian tariff classes |
| **EgyptERA** | Egyptian Electric Utility & Consumer Protection Regulatory Agency |
| **EETC** | Egyptian Electricity Transmission Company (independent TSO since 2015) |
| **EEHC** | Egyptian Electricity Holding Company (parent of generation/distribution) |
| **TOU** | Time-of-Use pricing |
| **OPC UA** | OPC Unified Architecture — IEC 62541; standard SCADA interface |
| **PPA** | Power Purchase Agreement — bilateral electricity supply contract |
| **GEM** | Global Energy Monitor — public infrastructure database |

---

*Built with ⚡ by Team Opti-Twin — NextCity AI Hack 2026*
*Transforming Egyptian manufacturing, one optimized watt at a time.*

**v2.0 changelog (May 1, 2026):** Replaced fictional 1.0/1.2/2.5 EGP/kWh time-of-use schedule with verified flat 1.60 EGP/kWh UHV tariff (EgyptERA Aug 2024). Corrected grid operator references (EETC independent TSO; not "North Delta Electricity Company"). Re-anchored Ezz Steel furnace specs to Global Energy Monitor (185-t Danieli furnaces, 1.6 Mtpa EAF 2). Added power-factor penalty as primary verified economic lever. Added CBAM and tariff-reform as forward-looking levers. Added §18 Assumptions & Limitations, §19 Real-World Deployment Strategy, §20 Sources & References. Added ζ (PF) reward weight. All headline KPIs re-stated as ⚠ modelled estimates with confidence labels.
  Sources:
  - https://egyptera.org/en/TarrifAug2024.aspx
  - https://www.gem.wiki/Ezz_Flat_Steel_Ain_Sokhna_plant
  - https://www.gem.wiki/Ezz_Flat_Steel_Ain_Sokhna_plant
  - https://www.iea.org/countries/egypt
  - https://www.eia.gov/international/content/analysis/countries_long/Egypt/pdf/Egypt.pdf
  - https://www.climatiq.io/data/emission-factor/2c8aa104-7e2e-4bae-af32-c054e9bc4d7f
  - https://ideas.repec.org/p/guc/wpaper/29.html
  - https://www.researchgate.net/publication/3274579_Power_factor_and_your_electrical_utility_bill_in_Egypt
  - https://worldsteel.org/wp-content/uploads/Fact-sheet-energy-in-the-steel-industry-2021-1.pdf
  - https://www.aist.org/AIST/aist/AIST/Conferences_Exhibitions/MENA/Presentations/AIST_MENA_EAF-Efficiency_Cappel.pdf
  - https://en.wikipedia.org/wiki/Electric_arc_furnace
  - https://www.mordorintelligence.com/industry-reports/graphite-electrode-market
  - https://globaltransmission.info/egypt-unbundles-eetc-establishes-independent-transmission-operator/
  - https://aisusteel.org/en/25087/
  - https://ember-energy.org/countries-and-regions/egypt/
  - https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en