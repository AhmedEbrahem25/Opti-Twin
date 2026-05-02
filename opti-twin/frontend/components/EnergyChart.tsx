import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceArea,
} from "recharts";

type Point = { t: number; mw: number; price: number; bath: number };

export default function EnergyChart({ data, peakActive }: { data: Point[]; peakActive: boolean }) {
  return (
    <div className="glass rounded-xl p-3 h-72">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-steel-100/80">
          Arc Power (MW) · 6-min rolling
        </h3>
        <span className="text-xs text-steel-100/50">
          {peakActive ? "🔴 TOU peak active" : "Flat tariff"}
        </span>
      </div>
      <ResponsiveContainer width="100%" height="88%">
        <LineChart data={data}>
          <CartesianGrid stroke="#243044" strokeDasharray="3 3" />
          <XAxis
            dataKey="t"
            tickFormatter={(t) => new Date(t).toLocaleTimeString().slice(3, 8)}
            stroke="#5e7186"
            fontSize={11}
          />
          <YAxis
            stroke="#5e7186"
            fontSize={11}
            domain={[0, 120]}
            label={{ value: "MW", position: "insideTopLeft", fill: "#5e7186", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ background: "#16202c", border: "1px solid #2a3950" }}
            labelFormatter={(t) => new Date(t).toLocaleTimeString()}
          />
          {peakActive && (
            <ReferenceArea
              y1={0}
              y2={120}
              fill="#ff6b1a"
              fillOpacity={0.06}
              ifOverflow="extendDomain"
            />
          )}
          <Line
            type="monotone"
            dataKey="mw"
            stroke="#ff8a3d"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
