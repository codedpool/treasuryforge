"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { usePortfolio } from "@/lib/api";
import { formatUsd } from "@/lib/format";
import DataState from "@/components/dashboard/DataState";

const COLORS = { Cash: "#24496B", Crypto: "#6B4A17", Equity: "#1F3D33" };

export default function AllocationChart() {
  const { data, error, isLoading } = usePortfolio();

  return (
    <DataState isLoading={isLoading} error={error}>
      {data ? <Chart portfolio={data} /> : null}
    </DataState>
  );
}

function Chart({ portfolio }) {
  const buckets = { Cash: portfolio.cash_usd || 0, Crypto: 0, Equity: 0 };
  for (const p of portfolio.positions || []) {
    if (p.usd_value == null) continue;
    if (p.asset_class === "crypto") buckets.Crypto += p.usd_value;
    else buckets.Equity += p.usd_value;
  }
  const rows = Object.entries(buckets)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));

  if (rows.length === 0) {
    return <p className="font-mono text-xs uppercase tracking-wideish text-paper-muted">No holdings yet.</p>;
  }

  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row">
      <div className="h-48 w-48 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={rows} dataKey="value" nameKey="name" innerRadius={52} outerRadius={80} paddingAngle={2}>
              {rows.map((r) => (
                <Cell key={r.name} fill={COLORS[r.name]} stroke="#FAF5E9" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "#FAF5E9",
                border: "1px solid #DCC9A0",
                borderRadius: 6,
                fontFamily: "var(--font-mono)",
                fontSize: 12,
              }}
              itemStyle={{ color: "#1C3348" }}
              formatter={(value) => formatUsd(value)}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="space-y-2 font-mono text-sm">
        {rows.map((r) => (
          <li key={r.name} className="flex items-center gap-2.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: COLORS[r.name] }} aria-hidden />
            <span className="text-paper-ink/80">{r.name}</span>
            <span className="text-paper-ink">{formatUsd(r.value)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
