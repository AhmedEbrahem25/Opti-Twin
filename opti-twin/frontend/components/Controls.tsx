import { useState } from "react";
import { api } from "../lib/api";

const PROFILES = [
  { id: "default", label: "Default" },
  { id: "cost_first", label: "Cost-first" },
  { id: "equipment_sensitive", label: "Equipment-sensitive" },
  { id: "production_critical", label: "Production-critical" },
  { id: "quality_focused", label: "Quality-focused" },
];

const CRISES = [
  { id: "wall_overheat", label: "Wall overheat" },
  { id: "electrode_break", label: "Electrode break" },
  { id: "grid_spike", label: "Grid Hz spike" },
  { id: "transformer_alarm", label: "Transformer alarm" },
];

export default function Controls() {
  const [aiOn, setAiOn] = useState(false);
  const [tou, setTou] = useState(false);
  const [profile, setProfile] = useState("default");
  const [busy, setBusy] = useState<string | null>(null);

  async function toggleAI() {
    setBusy("ai");
    try {
      await api.toggleAI(!aiOn);
      setAiOn(!aiOn);
    } finally {
      setBusy(null);
    }
  }

  async function toggleTOU() {
    setBusy("tou");
    try {
      await api.setTariffMode(!tou);
      setTou(!tou);
    } finally {
      setBusy(null);
    }
  }

  async function changeProfile(p: string) {
    setBusy("profile");
    try {
      await api.setProfile(p);
      setProfile(p);
    } finally {
      setBusy(null);
    }
  }

  async function inject(event: string) {
    setBusy("inject");
    try {
      await api.injectCrisis(event);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="glass rounded-xl p-4 mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
      <div>
        <div className="text-xs uppercase text-steel-100/60 mb-2">AI Agent</div>
        <button
          onClick={toggleAI}
          disabled={busy === "ai"}
          className={`w-full py-3 rounded-lg font-semibold transition ${
            aiOn
              ? "bg-flame-500 hover:bg-flame-600 text-white"
              : "bg-steel-700 hover:bg-steel-500 text-steel-100"
          }`}
        >
          {aiOn ? "🤖 ON" : "AI: OFF"}
        </button>
      </div>

      <div>
        <div className="text-xs uppercase text-steel-100/60 mb-2">Tariff Mode</div>
        <button
          onClick={toggleTOU}
          disabled={busy === "tou"}
          className={`w-full py-3 rounded-lg font-semibold transition ${
            tou
              ? "bg-amber-500 hover:bg-amber-600 text-white"
              : "bg-steel-700 hover:bg-steel-500 text-steel-100"
          }`}
        >
          {tou ? "TOU Reform Mode" : "Flat (current 1.60)"}
        </button>
      </div>

      <div>
        <div className="text-xs uppercase text-steel-100/60 mb-2">Reward Profile</div>
        <select
          value={profile}
          onChange={(e) => changeProfile(e.target.value)}
          disabled={busy === "profile"}
          className="w-full py-3 rounded-lg bg-steel-700 text-steel-100 px-3 outline-none"
        >
          {PROFILES.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <div className="text-xs uppercase text-steel-100/60 mb-2">Inject Crisis</div>
        <select
          onChange={(e) => {
            if (e.target.value) {
              inject(e.target.value);
              e.target.value = "";
            }
          }}
          disabled={busy === "inject"}
          className="w-full py-3 rounded-lg bg-red-700/70 hover:bg-red-700 text-white px-3 outline-none"
          defaultValue=""
        >
          <option value="" disabled>
            Choose event…
          </option>
          {CRISES.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
