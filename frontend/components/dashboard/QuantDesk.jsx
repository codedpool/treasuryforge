"use client";

import { useTransactions, TRUEFORGE_PUBLIC_URL } from "@/lib/api";
import { formatTimestamp } from "@/lib/format";
import DataState from "@/components/dashboard/DataState";
import Panel from "@/components/Panel";
import Ledger from "@/components/Ledger";

export default function QuantDesk() {
  const { data, error, isLoading } = useTransactions(50);
  const flagged = (data || []).filter((t) => t.risk_snapshot?.recommend_sandbox_stress_test);

  return (
    <DataState isLoading={isLoading} error={error}>
      <div className="space-y-6">
        <Panel className="p-5">
          <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">Where the scripts live</p>
          <p className="mt-2 text-sm text-ink-soft">
            The generated stress-test code and its output are saved in TrueForge&rsquo;s own session trace, not a
            second copy in this wallet — that&rsquo;s the actual audit trail, and duplicating it here would just be
            a second, driftable source of truth.
          </p>
          <a
            href={TRUEFORGE_PUBLIC_URL}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-block rounded border border-ink-line px-3 py-1.5 font-mono text-xs uppercase tracking-wideish text-ink-soft transition hover:border-signal-amber hover:text-signal-amber"
          >
            Open TrueForge&rsquo;s trace ↗
          </a>
        </Panel>

        <div>
          <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">
            Decisions that called for a stress test
          </p>
          {flagged.length === 0 ? (
            <p className="mt-3 text-sm text-ink-soft">
              None of the last 50 decisions breached a limit, so none recommended one.
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              {flagged.map((t) => (
                <Ledger key={t.id} className="p-4 font-mono text-sm">
                  <div className="flex items-baseline justify-between">
                    <span className="text-paper-ink">
                      {t.side.toUpperCase()} {t.asset}
                    </span>
                    <span className="text-xs text-paper-muted">{formatTimestamp(t.timestamp)}</span>
                  </div>
                  <p className="mt-2 text-xs text-paper-muted">
                    Concentration {t.risk_snapshot.triggers?.concentration?.projected_pct}% · Drawdown{" "}
                    {t.risk_snapshot.triggers?.daily_drawdown?.current_pct}%
                  </p>
                </Ledger>
              ))}
            </div>
          )}
        </div>
      </div>
    </DataState>
  );
}
