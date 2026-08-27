"use client";

import { useTransactions } from "@/lib/api";
import { formatUsd, formatQty, formatTimestamp } from "@/lib/format";
import DataState from "@/components/dashboard/DataState";
import Ledger from "@/components/Ledger";
import Stamp from "@/components/Stamp";

export default function DecisionLog({ limit = 50 }) {
  const { data, error, isLoading } = useTransactions(limit);

  return (
    <DataState isLoading={isLoading} error={error}>
      {data && data.length > 0 ? (
        <div className="space-y-3">
          {data.map((entry) => (
            <Entry key={entry.id} entry={entry} />
          ))}
        </div>
      ) : (
        <Empty />
      )}
    </DataState>
  );
}

function Entry({ entry }) {
  const snapshot = entry.risk_snapshot;
  const breached = snapshot?.any_breach;
  const status = entry.side === "seed" ? null : entry.dry_run ? "dry_run" : "live";

  return (
    <Ledger className="p-4 font-mono text-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[15px] font-semibold text-paper-ink">
              {entry.side.toUpperCase()} {formatQty(entry.quantity, 4)} {entry.asset}
            </span>
            {status ? <Stamp status={status} size="sm" rotate={-3} /> : null}
            {breached ? <Stamp status="breach" size="sm" rotate={3} /> : null}
          </div>
          <p className="mt-1 text-xs text-paper-muted">{formatTimestamp(entry.timestamp)}</p>
        </div>
        <div className="text-right">
          <div className="text-paper-ink">{formatUsd(entry.usd_value)}</div>
          <div className="text-xs text-paper-muted">at {formatUsd(entry.price_usd)}</div>
        </div>
      </div>

      {entry.reason ? (
        <p className="mt-3 border-t border-dashed border-paper-line pt-3 text-xs leading-relaxed text-paper-ink/80">
          {entry.reason}
        </p>
      ) : null}

      {snapshot ? (
        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-dashed border-paper-line pt-3 text-[11px] text-paper-muted">
          <span>Drawdown {snapshot.triggers?.daily_drawdown?.current_pct}%</span>
          <span>Concentration {snapshot.triggers?.concentration?.projected_pct}%</span>
          <span>Loss streak {snapshot.triggers?.consecutive_losses?.streak}</span>
          {snapshot.recommend_sandbox_stress_test ? (
            <span className="text-signal-red-ink">Sandbox stress test recommended</span>
          ) : null}
        </div>
      ) : null}
    </Ledger>
  );
}

function Empty() {
  return (
    <div className="rounded border border-ink-line bg-ink-raised px-4 py-6 text-center">
      <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">No decisions logged yet</p>
      <p className="mt-2 text-sm text-ink-soft">
        The log fills in as the agent proposes trades. Trigger one from the risk panel, or let the agent run.
      </p>
    </div>
  );
}
