# Opti-Twin — Judges Brief

> **Demo:** NextCity AI Hack 2026, Alamein International University · 2026-05-08
> **Track:** Industry-Driven Challenges
> **Project:** Opti-Twin — Autonomous Energy Intelligence for Smart Manufacturing
> **Use this document:** as the speaker's reference during the demo and Q&A. Every claim is sourced. Every number is either ✔ verified from a public source or ⚠ a transparently-modelled estimate.

---

## 1. The 30-Second Pitch

> "Egyptian Electric Arc Furnaces — like Ezz Flat Steel's 185-tonne furnace at Ain Sokhna — pay 1.60 EGP per kilowatt-hour at a flat industrial tariff, lose money to power-factor penalties below 0.92, and from 2026 will pay an EU carbon price on every tonne of steel they export. Opti-Twin is a digital twin with a reinforcement-learning agent embedded inside it. It reads the furnace every three seconds, decides what arc power, oxygen, and cooling action to take, and **explains every decision in English and Arabic**. The agent shaves 5–10% off the energy bill, holds power factor at the regulator's reference, and protects equipment during crises — all while the operator can override it from the dashboard. The annual modelled upside per furnace is 95–195 million EGP, with payback in under 12 months."

**One-sentence version:** *"Opti-Twin is an industrial digital twin that lets a reinforcement-learning agent run an Egyptian steel furnace 5–10% more cheaply, with a bilingual explanation for every decision."*

---

## 2. Why This Matters — Egypt in 2026

Three independent levers create the business case. Every figure is sourced:

| Lever | Reality | Source |
|---|---|---|
| **Flat industrial tariff** | UHV (220–132 kV) industrial customers pay **1.60 EGP/kWh flat** — no time-of-use split as of August 2024. Every kWh avoided saves 1.60 EGP. | ✔ EgyptERA tariff schedule, August 2024 |
| **Power-factor penalty** | Industrial loads >500 kW are penalised when annual average PF falls below 0.92. EAFs typically run at 0.75–0.85 due to reactive-power swings during melting. | ✔ EgyptERA + "Power factor and your electrical utility bill in Egypt" (ResearchGate / IEEE) |
| **EU CBAM** | Definitive phase from 2026: a carbon price on iron-and-steel imports into the EU. Egypt's grid is **~81% natural-gas fired** (IEA / EIA, 2024) — every kWh saved cuts Scope-2 emissions and CBAM liability on European exports. | ✔ European Commission CBAM framework |

**The modelled facility:** Ezz Flat Steel — Ain Sokhna **EAF #2**. A 185-tonne Danieli furnace, started 2023, allocated 200 MW by Egypt's Supreme Council of Energy, rated 1.6 Mtpa, charges 80 % DRI + 20 % scrap. The same furnace had a transformer failure in November 2024 expected to halt production for ~9 months — a real, recent reminder of why equipment-protection matters. *(Source: Global Energy Monitor; Arab Iron and Steel Union.)*

---

## 3. What Opti-Twin Is

A **4-tier industrial system** glued by Redis Pub/Sub, fully containerized, fully offline:

```
TIER 1 — EDGE
  simulator/  (Python, physics + crisis engine)
  emits factory.telemetry every 3 s on Redis
        │
TIER 2 — STREAMING
  Redis 7 Pub/Sub — channels:
    factory.telemetry  ai.recommendation  ai.safety_rollback
    pricing.live  pricing.forecast  pricing.control
        │
TIER 3 — AI CORE
  ai_engine/  (Python)
    OptiTwinEAFEnv (Gymnasium) · PPO (Stable-Baselines3)
    bilingual EN/AR XAI · safety mask
  pricing/    (Dynamic Pricing Engine — TOU/DR scenarios)
        │
TIER 4 — APPLICATION
  backend/   FastAPI · /api/v1/* + /ws/live-feed
  frontend/  Next.js dashboard
  meilisearch  ←  Opti-Search slice (⌘K palette, EN/AR)
```

**A single command spins it up:** `docker compose up --build` → backend on `:8000`, dashboard on `:3000`, Meili on `:7700`.

---

## 4. The AI Core (For ML-Savvy Judges)

### 4.1 Reinforcement-learning formulation

- **State (32-D continuous + categorical):** bath temperature, wall-panel temperature, arc power, current, voltage, MVA, oxygen flow, electrode wear, power factor, grid frequency, tariff mode, peak/off-peak flag, heat-phase, backlog, crisis flags.
- **Action (5-discrete in code, 7-discrete in spec):** `HOLD_STEADY · REDUCE_ARC_POWER · PRE_PEAK_DROP · RAISE_PF_COMPENSATION · EMERGENCY_COOLING` (+ `GRID_RIDE_THROUGH`, `TRANSFORMER_DERATE` per spec).
- **Multi-objective reward:**

  ```
  R = α·E_saved − β·M_stress − γ·P_delay + δ·Quality − ε·Wear − ζ·PF_penalty
  ```

  All six weights (α–ζ) are exposed as env vars `RL_ALPHA…RL_ZETA` and reflected in the dashboard "reward profile" preset (cost-first, equipment-first, production-first, quality-first).

- **Algorithm:** PPO from Stable-Baselines3, episodic on a 45-65 min heat cycle.

### 4.2 The 5-model stack (planing-v2.md)

| ID | Model | Role |
|---|---|---|
| **M1** | PPO policy | The decision-maker. |
| **M2** | LSTM forecaster | Predicts price, peak windows, bath-temp trajectory. |
| **M3** | Anomaly autoencoder | Flags out-of-distribution telemetry → safety mask. |
| **M4** | Behaviour cloning | Bootstraps from operator logs; warm-starts PPO. |
| **M5** | Preference reward model | Fine-tunes reward weights from human feedback. |

### 4.3 Honest status (D-day −5)

| Component | Status |
|---|---|
| Simulator (physics + 3 crisis types) | ✅ Live |
| Gymnasium env, reward function | ✅ Live |
| **PPO weights `opti_twin_ppo.zip`** | ❌ **Not trained yet — scripted decision-tree policy is the demo fallback** (this is intentional; scripted policy still demonstrates the levers, and is reliable on stage) |
| Bilingual XAI template engine | ✅ Live (template-based EN/AR; LLM rewrite is post-event) |
| Safety mask + override-rollback | ✅ Live |
| Dynamic Pricing Engine (TOU + DR scenarios) | ✅ Live |
| **Opti-Search (⌘K palette, deep-link, EN/AR)** | ✅ **Live (shipped 2026-05-03)** |
| M2–M5 | 🟡 Spec only |

**Rule of the demo:** never claim a model is doing something a model isn't doing. The XAI text comes from templates. The policy is scripted. The reward weights are real and the safety mask is real.

---

## 5. The Six Things to Show On Stage (Demo Flow — 5 min)

The plan.md script is 3 minutes; we now have the **Opti-Search WOW** to add as a sixth beat.

### Beat 1 — Baseline (0:00–0:30)
- Dashboard at `localhost:3000`. Pause for 5 seconds — let the live counters move.
- Speaker: *"This is a real Danieli 185-tonne furnace at Ezz Flat Steel Ain Sokhna. The numbers come from EgyptERA, the IEA, and Global Energy Monitor."*
- Point at the KPI Banner: bath temperature, arc power 90 MW, PF 0.78, cost rate 144,000 EGP/hour at 1.60 EGP/kWh.

### Beat 2 — Activate the AI (0:30–1:15)
- Click **AI Toggle → ON** (Controls panel).
- The XAI Decision Log starts populating. Let one decision land, then read it aloud — both EN and AR.
- Energy chart line dips. PF gauge climbs toward 0.92. "Saved Today" KPI starts ticking.
- Speaker: *"Every decision has a reason in two languages, before the action is taken. There is no black box."*

### Beat 3 — Tariff-Reform / Dynamic Pricing (1:15–2:00)
- Click **Tariff Reform / TOU Mode**.
- Display flips to "Future TOU peak: 2.50 EGP/kWh — modelled per GUC Working Paper #29".
- Agent fires `PRE_PEAK_DROP`. XAI explains: anticipated peak in 30 min, drop 90 → 65 MW now, save 18,000 EGP/hr if peak activates.
- Speaker: *"Egypt does not have industrial TOU pricing today. Academic literature is already proposing it. The day it lands, this furnace is ready."*

### Beat 4 — Crisis Injection (2:00–2:45)
- Click **Inject Wall Overheat** (Controls panel).
- Wall panel temp spikes from 187 °C → 223 °C (red).
- Agent fires `EMERGENCY_COOLING`. XAI: *"Wall panel 223 °C exceeded 200 °C — β-weight override: machine protection overrides energy savings."*
- Temperature drops back to safe range within ~30 simulated seconds.
- Speaker: *"This is the same incident class as the November 2024 transformer failure that took EAF #2 down for nine months."*

### Beat 5 — **Opti-Search ⌘K** (2:45–3:30) *— new flagship moment*
- Press **⌘K**. Command palette pops with the `opti-pop` animation.
- Type `wall overheat`. Three results, < 250 ms. The critical row is visibly heavier — bold title, red border-l, red dot.
- Type `تبريد طارئ` (emergency cooling, in Arabic). Same query, RTL results, an `AR` pill on each row. Saved-search banner above counts critical events this shift.
- Click any result. **The dashboard scrolls and the matching row in the AI Decision Log gets a 2-second flame-ring flash.** The URL updates to `/?ts=...&focus=...` — a bookmarkable deep-link.
- Speaker: *"The agent doesn't just decide — it remembers. Operators ask 'has this happened before?' This answers in 200 milliseconds, in either language."*

### Beat 6 — Closing KPI (3:30–4:00)
- Click **Show Daily Summary**.
  ```
  ⚡ Energy intensity ↓ 8 %    🏭 Production 100 %     🌡️ SAFE
  💰 Modelled saving today: 314,000 EGP
  🔌 PF held at 0.92            ♻️ CO₂ ↓ 6.5 t today
  ```
- Closing line: *"Modelled annual upside per furnace: 95–195 million EGP. Payback under 12 months on a single-furnace pilot."*

---

## 6. Numbers to Memorise

The speaker should be able to recite these without looking:

| Quantity | Value | Where it comes from |
|---|---|---|
| Egyptian UHV industrial tariff | **1.60 EGP/kWh** flat (Aug 2024) | EgyptERA |
| PF reference | **0.92** | EgyptERA |
| EAF energy intensity, baseline | **450 kWh/tonne** | World Steel Association |
| Target reduction | **5–10 %** (literature: 5–15 % achievable) | IEA Iron & Steel Roadmap |
| Furnace capacity (Ezz Ain Sokhna #2) | **185 tonnes**, 1.6 Mtpa | Global Energy Monitor |
| Allocated capacity | **200 MW** | Supreme Council of Energy |
| Egypt grid CO₂ intensity | **0.45–0.50 tCO₂/MWh** | IEA / EIA |
| Egypt grid gas share | **~81 %** | IEA / EIA 2024 |
| Annual electricity bill, one EAF | **~1.15 B EGP** = 450 kWh/t × 1.6 Mtpa × 1.60 EGP/kWh | Derived |
| Modelled savings range | **95–195 M EGP/yr** | Derived (§15.2 of plan.md) |
| Pilot deployment cost | **$200K–500K** | Industry-typical |
| Payback | **< 12 months** | Derived |
| Telemetry rate | **3 seconds** (typical SCADA polling) | — |
| Demo duration | **3–5 minutes** | — |

---

## 7. ROI Stack (One Slide if Asked)

| Lever | Annual upside per furnace | Confidence |
|---|---|---|
| 5–10 % energy intensity reduction | 58–115 M EGP | ⚠ Modelled |
| Power-factor penalty avoidance | 30–60 M EGP | ✔ Mechanism verified, magnitude site-specific |
| Equipment-incident avoidance | 5–20 M EGP | ⚠ Modelled, anchored to Nov-2024 transformer failure |
| CBAM-compliant carbon intensity | Strategic / export-revenue protection | ✔ Mechanism real |
| **Total** | **~95–195 M EGP/yr per furnace** | ⚠ Modelled range |

*(See `plan.md` §15 for the full reasoning.)*

---

## 8. The Five Things That Make This Project Win

1. **Real Egyptian context, not a generic demo.** Ezz Flat Steel is a real plant; EgyptERA is the real regulator; the 1.60 EGP/kWh tariff is verifiable. Judges who know the Egyptian energy sector will recognise the numbers.
2. **Transparent AI.** Every action has an EN+AR reason rendered before the action runs. Operators read it. Auditors read it.
3. **Safety floor that actually fires.** The β-override on wall overheat is not narrative — it's a mask in the code that vetoes the policy when physical limits are crossed.
4. **Opti-Search ⌘K.** Industrial dashboards rarely have real search. A judge with SCADA experience recognises instantly what `⌘K → "wall overheat last shift" → 200 ms` means.
5. **Honest engineering.** PPO weights aren't trained yet — we say so. Numbers are modelled — we mark them. CBAM exposure depends on Ezz's actual EU exports — we say "depends." Judges respect this.

---

## 9. Q & A — The Hard Questions and the Honest Answers

### "Is the AI actually trained?"
> *"Not yet. The PPO weights aren't fit. The demo runs a hand-crafted decision-tree policy through the same Gymnasium environment, the same reward function, and the same safety mask. The architecture is the deliverable; the trained weights are a 1–2 day addition once we have a stable reward curve. We chose to ship a reliable scripted policy to the demo rather than a flaky just-trained one."*

### "Where do the savings numbers come from?"
> *"They are modelled, not measured. The 5–10 % range is what the IEA Iron & Steel Roadmap and World Steel Association literature report for advanced control plus demand response on EAFs. We applied that range to verified Egyptian numbers — EgyptERA's 1.60 EGP/kWh tariff, the 1.6 Mtpa rated capacity from Global Energy Monitor — and called it modelled. We have an EgyptERA tab open if you want to verify."*

### "How do you go from sim to a real factory?"
> *"Three phases. **Shadow mode** — agent reads a SCADA tap, makes recommendations, never actuates; we collect a month of operator vs. agent comparisons. **Advisory mode** — recommendations surface in the operator HMI; operator clicks accept/reject. **Closed loop** — only after the operator and the safety team sign off, and only on a single furnace, with hard physical limits in the PLC layer that the agent cannot override. None of that exists today; the plan to get there does."*

### "Why Reinforcement Learning instead of MPC or rule-based control?"
> *"Three reasons. RL handles multi-objective reward natively — energy, equipment, production, quality, PF, all in one objective. MPC needs the user to write a controller per objective. RL learns from operator demonstrations via behaviour cloning (M4 in our stack). And RL adapts when the tariff changes — flip the TOU flag in the state vector, retrain, done. MPC needs the cost function rewritten."*

### "What if the agent does something dangerous?"
> *"Two layers. The Gymnasium env enforces hard physical limits — temperatures, currents, ramp rates. The action mask vetoes any policy action that would cross them; that veto is logged as `safety_rollback` and is searchable in ⌘K. After three consecutive overrides on the same axis, we publish an alert to the operator. None of this is plan — it's in the indexer code today; you can search for `consecutive overrides` and see it."*

### "What's the moat?"
> *"The bilingual XAI surface and the search index over months of decisions. The RL itself is replicable — what's hard to replicate is **a decision log every operator can read in their language and search in 200 ms**. That's where adoption happens."*

### "Who owns this if it goes commercial?"
> *"Hackathon team retains IP. Pilot conversations go through Ezz Steel ops or the Ministry of Electricity demand-response unit (post-hack roadmap, plan.md §17). Post-hack month 1."*

### "How is this different from a SCADA HMI?"
> *"A SCADA HMI shows the present. Opti-Twin decides about the present, justifies it, remembers it, and lets you search the memory. The decision log is the product."*

### "What if Meilisearch goes down?"
> *"The dashboard renders a soft-fail strip — `Saved-search offline — backend unreachable` — and the search button shows `index down`. The rest of the dashboard runs unaffected. We never silently hide a degradation."*

### "What does the Arabic look like to a non-Arabic-speaker?"
> *"You'll see RTL text rendered correctly in the right places — XAI Log, search results, saved-search banner. There's an EN/AR toggle on the banner. The architecture supports any language whose tokeniser Meilisearch ships — at launch, English and Arabic; Hindi or Urdu would be one config line."*

---

## 10. What's Live Right Now (As of 2026-05-03)

### Built and demonstrable
- 4-tier docker-compose stack (`redis`, `simulator`, `ai_engine`, `backend`, `frontend`, `meilisearch`)
- Live telemetry stream every 3 s, three crisis types (`wall_overheat`, `grid_spike`, `transformer_alarm`)
- Scripted decision-tree policy with bilingual XAI for 5 actions
- Safety mask + safety-rollback alerting after 3 consecutive overrides
- Dynamic Pricing Engine — TOU mode toggle, DR-event scenarios, peak/off-peak indicator
- KPI Banner, Energy Chart, Thermal Gauge, EAF Status Card, XAI Decision Log, Pricing Event Log, System Logs
- **Opti-Search ⌘K palette** (just shipped):
  - Search across decisions / crises / safety-rollbacks
  - Type, severity, and time-range filters (last hour / shift / 24h / 7d / 30d)
  - English + Arabic with proper RTL and language pill
  - Critical results visually heavier (border-l, bold, larger dot)
  - Loading skeletons, soft-fail error strip with retry
  - Click → URL deep-link → dashboard scrolls to matching row + 2 s flame-ring flash
  - Saved-search banner with EN/AR toggle, plural-correct copy, `aria-live`, soft offline strip
  - Live `indexed: N` pill in header, refreshes every 60 s

### Spec only, post-hack
- PPO trained weights (M1) — scripted policy is the fallback today
- LSTM forecaster (M2), anomaly autoencoder (M3), behaviour cloning (M4), preference reward model (M5)
- WS `/ws/search/live`, NL query parser, RBAC, audit chain, CSV/Parquet exports
- DPE pricing-event indexing into Meili (decided out of scope for the 7-day demo)
- Sim-to-real shadow-mode pipeline

---

## 11. What To Do If…

| Situation | Action |
|---|---|
| Internet drops at venue | The system is fully offline; nothing breaks. We pre-pulled all Docker images. |
| WebSocket reconnects mid-demo | Auto-reconnect with backoff is wired; the badge will go amber and back to green. Keep talking. |
| Crisis injection fails to fire | Click the button again; if still nothing, skip beat 4 — the agent's PRE_PEAK_DROP in beat 3 already shows the override mechanism. |
| Meilisearch fails to start (the bind error we hit during dev) | The header shows `index down`. Skip beat 5 — open ⌘K just to show the soft-fail UX, then move on. The rest of the demo is unaffected. |
| Judge wants to see the code | `backend/search/`, `ai_engine/agent.py`, `ai_engine/environment.py`. All open in the IDE on the secondary monitor. |
| Judge asks to type their own search | Hand them the keyboard. The palette is robust to bad queries — empty state shows tip queries in EN and AR. |

---

## 12. Sources (Have These Open in a Second Tab)

- **EgyptERA tariff schedule (August 2024)** — for the 1.60 EGP/kWh and PF 0.92 reference.
- **Global Energy Monitor — Ezz Flat Steel Ain Sokhna entry** — for the 185-tonne furnace, 1.6 Mtpa, 200 MW allocation, Nov-2024 transformer failure.
- **IEA Iron & Steel Roadmap 2024** — for the 5–15 % advanced-control savings range.
- **World Steel Association energy fact sheets** — for the 450 kWh/tonne baseline.
- **IEA Egypt country brief 2024** — for the 81 % gas share.
- **European Commission CBAM framework page** — for the 2026 definitive-phase date.
- **GUC Working Paper #29 — Egyptian peak-load pricing model** — for the tariff-reform scenario.
- **"Power factor and your electrical utility bill in Egypt", ResearchGate** — for the PF penalty mechanism.

`plan.md` §20 has the full bibliography with URLs.

---

## 13. The One Slide That Wins It

If we're given one slide:

```
                          OPTI-TWIN
        Industrial Digital Twin · Reinforcement Learning · Bilingual XAI

   ┌──────────────────────────────────────────────────────────────────┐
   │  EVERY KILOWATT-HOUR YOU AVOID IS 1.60 EGP — VERIFIED.           │
   │  EVERY DECISION IS EXPLAINED IN EN + AR — BEFORE IT FIRES.       │
   │  EVERY DECISION IS SEARCHABLE IN 200 MS — IN EITHER LANGUAGE.    │
   │                                                                  │
   │   95–195 M EGP / year per furnace · payback < 12 months.          │
   │             Modelled on Ezz Flat Steel Ain Sokhna #2.            │
   └──────────────────────────────────────────────────────────────────┘

         docker compose up   →   localhost:3000   →   ⌘K to begin.
```

---

## 14. After the Demo — One-Line Asks

End the pitch with one specific ask, depending on who the judge is:

- **Industry judge (steel / energy):** *"We'd value a 30-minute conversation about a shadow-mode pilot on EAF #2."*
- **Academic judge:** *"Our M2–M5 stack (forecaster, anomaly AE, BC, preference RM) is unbuilt — we'd value a co-authored paper offer."*
- **Investor judge:** *"Pilot economics put payback under 12 months on a single furnace. We're ready for a seed conversation."*
- **Government judge (regulator / ministry):** *"This system is already structured for industrial TOU and demand-response. We'd value a conversation with EgyptERA's demand-response unit."*

---

*Last updated: 2026-05-03. Owned by the Opti-Twin team. For the master plan see `plan.md`. For the AI roadmap see `planing-v2.md`. For the search-engine vertical see `upgrade.md`.*
