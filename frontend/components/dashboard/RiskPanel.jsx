"use client";

import { useRiskSummary, useMetrics } from "@/lib/api";
import { formatPct, formatUsd } from "@/lib/format";
import DataState from "@/components/dashboard/DataState";
import Panel from "@/components/Panel";
import Figure from "@/components/Figure";
import Stamp from "@/components/Stamp";

export default function RiskPanel() {
  const risk = useRiskSummary();
  const metrics = useMetrics();

  return (
    <DataState isLoading={risk.isLoading} error={risk.error}>
      {risk.data ? <Body risk={risk.data} metrics={metrics.data} /> : null}
    </DataState>
  );
}

function Body({ risk, metrics }) {
  const dd = risk.daily_drawdown;
  const cl = risk.consecutive_losses;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <TriggerCard
          title="Daily drawdown"
          breached={dd.breached}
          value={formatPct(dd.current_pct)}
          limit={`Limit ${formatPct(dd.limit_pct)}`}
          detail={`Day start ${formatUsd(dd.day_start_value_usd)} → now ${formatUsd(dd.current_total_usd)}`}
        />
        <TriggerCard
          title="Consecutive losses"
          breached={cl.breached}
          value={String(cl.streak)}
          limit={`Limit > ${cl.limit}`}
          detail="Realized sells only — DRY_RUN sells are correctly excluded."
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel className="p-4">
          <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">Concentration limit</p>
          <p className="mt-2 text-sm text-ink-soft">
            Single-asset allocation over{" "}
            <span className="font-mono text-ink-bright">{formatPct(risk.concentration_limit_pct)}</span> of the
            portfolio, evaluated per proposed trade — see the decision log for the value at each trade.
          </p>
        </Panel>
        <Panel className="p-4">
          <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">Sell-all threshold</p>
          <p className="mt-2 text-sm text-ink-soft">
            Selling{" "}
            <span className="font-mono text-ink-bright">{formatPct(risk.sell_all_threshold_pct)}</span> or more of a
            held position, evaluated per proposed sell.
          </p>
        </Panel>
      </div>

      {metrics ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Panel className="p-4">
            <Figure label="Max drawdown" value={formatPct(metrics.max_drawdown_pct)} size="sm" />
          </Panel>
          <Panel className="p-4">
            <Figure
              label="Sharpe (unannualized)"
              value={metrics.sharpe_ratio_unannualized ?? "—"}
              size="sm"
            />
          </Panel>
          <Panel className="p-4">
            <Figure label="Win rate" value={metrics.win_rate != null ? formatPct(metrics.win_rate * 100) : "—"} size="sm" />
          </Panel>
          <Panel className="p-4">
            <Figure label="Closed trades" value={String(metrics.closed_trades)} size="sm" />
          </Panel>
        </div>
      ) : null}
    </div>
  );
}

function TriggerCard({ title, breached, value, limit, detail }) {
  return (
    <Panel className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">{title}</p>
          <p className="tabular-figures mt-1 font-mono text-2xl text-ink-bright">{value}</p>
          <p className="mt-1 text-xs text-ink-muted">{limit}</p>
        </div>
        <Stamp status={breached ? "breach" : "safe"} size="sm" rotate={breached ? 3 : -3} />
      </div>
      <p className="mt-3 border-t border-ink-line pt-3 text-xs text-ink-muted">{detail}</p>
    </Panel>
  );
}
