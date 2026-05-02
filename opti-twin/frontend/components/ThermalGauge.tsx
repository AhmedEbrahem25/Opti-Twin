type Props = {
  bath: number;
  wall: number;
};

function bathColor(t: number): string {
  if (t < 1500) return "#5e7186";
  if (t < 1600) return "#3b82f6";
  if (t <= 1650) return "#10b981";
  return "#ef4444";
}

function wallColor(t: number): string {
  if (t < 180) return "#10b981";
  if (t < 200) return "#f59e0b";
  return "#ef4444";
}

function GaugeBar({
  label,
  value,
  min,
  max,
  unit,
  color,
  warnAt,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  color: string;
  warnAt?: number;
}) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  return (
    <div>
      <div className="flex justify-between text-xs text-steel-100/70 mb-1">
        <span>{label}</span>
        <span style={{ color }}>{value.toFixed(0)} {unit}</span>
      </div>
      <div className="h-3 bg-steel-900 rounded-full overflow-hidden relative">
        <div
          className="h-full transition-all duration-500 ease-out"
          style={{ width: `${pct}%`, background: color }}
        />
        {warnAt !== undefined && (
          <div
            className="absolute top-0 bottom-0 w-px bg-red-400/60"
            style={{ left: `${((warnAt - min) / (max - min)) * 100}%` }}
          />
        )}
      </div>
      <div className="flex justify-between text-[10px] text-steel-100/40 mt-0.5">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

export default function ThermalGauge({ bath, wall }: Props) {
  return (
    <div className="glass rounded-xl p-3 h-72">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-steel-100/80 mb-3">
        Thermal State
      </h3>
      <div className="space-y-5">
        <GaugeBar
          label="Bath Temperature"
          value={bath}
          min={1200}
          max={1700}
          unit="°C"
          color={bathColor(bath)}
          warnAt={1650}
        />
        <GaugeBar
          label="Wall Panel Temperature"
          value={wall}
          min={80}
          max={250}
          unit="°C"
          color={wallColor(wall)}
          warnAt={200}
        />
        <div className="text-xs text-steel-100/60 pt-2 border-t border-white/5">
          <div>Quality window: <span className="text-emerald-400">1,600 – 1,650 °C</span></div>
          <div>Wall safe limit: <span className="text-amber-400">200 °C</span></div>
        </div>
      </div>
    </div>
  );
}
