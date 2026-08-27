"use client";

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { useEquityCurve } from "@/lib/api";
import { formatUsd, formatTimestamp } from "@/lib/format";
import DataState from "@/components/dashboard/DataState";

export default function PnLChart() {
  const { data, error, isLoading } = useEquityCurve();

  return (
    <DataState isLoading={isLoading} error={error}>
      {data && data.length > 1 ? <Chart points={data} /> : <Sparse points={data} />}
    </DataState>
  );
}

function Chart({ points }) {
  const rows = points.map((p) => ({ ...p, t: formatTimestamp(p.timestamp) }));
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#D99A3C" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#D99A3C" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#262B3A" strokeDasharray="3 5" vertical={false} />
          <XAxis
            dataKey="t"
            tick={{ fill: "#8891A6", fontSize: 11, fontFamily: "var(--font-mono)" }}
            axisLine={{ stroke: "#262B3A" }}
            tickLine={false}
            minTickGap={40}
          />
          <YAxis
            tick={{ fill: "#8891A6", fontSize: 11, fontFamily: "var(--font-mono)" }}
            axisLine={false}
            tickLine={false}
            width={70}
            tickFormatter={(v) => formatUsd(v)}
          />
          <Tooltip
            contentStyle={{
              background: "#13161F",
              border: "1px solid #262B3A",
              borderRadius: 6,
              fontFamily: "var(--font-mono)",
              fontSize: 12,
            }}
            labelStyle={{ color: "#8891A6" }}
            formatter={(value) => [formatUsd(value), "Total"]}
          />
          <Area type="monotone" dataKey="total_usd" stroke="#D99A3C" strokeWidth={2} fill="url(#equityFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function Sparse({ points }) {
  return (
    <div className="flex h-64 flex-col items-center justify-center gap-2 text-center">
      <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">
        Not enough history for a curve yet
      </p>
      <p className="max-w-xs text-xs text-ink-muted">
        {points?.length === 1
          ? "One snapshot recorded so far — trade, or wait for the next periodic snapshot."
          : "No equity snapshots recorded yet."}
      </p>
    </div>
  );
}
