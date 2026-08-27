"use client";

import { useTrueforgeSessions, isTrueforgeUnreachable, useTransactions, TRUEFORGE_PUBLIC_URL } from "@/lib/api";
import { formatTimestamp } from "@/lib/format";
import Panel from "@/components/Panel";
import Ledger from "@/components/Ledger";
import Stamp from "@/components/Stamp";

export default function ApprovalQueue() {
  return (
    <div className="space-y-6">
      <TrueforgeStatus />
      <RecentBreaches />
    </div>
  );
}

function TrueforgeStatus() {
  const { data, error, isLoading } = useTrueforgeSessions();
  const sessions = Array.isArray(data) ? data : Array.isArray(data?.sessions) ? data.sessions : null;

  return (
    <Panel className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">TrueForge connection</p>
          <p className="mt-1 text-sm text-ink-soft">
            {isLoading
              ? "Checking…"
              : error
              ? isTrueforgeUnreachable(error)
                ? "Not reachable — start TrueForge to see live sessions and act on checkpoints."
                : "TrueForge returned an error."
              : `Connected — ${sessions?.length ?? 0} session${sessions?.length === 1 ? "" : "s"} known.`}
          </p>
        </div>
        <a
          href={TRUEFORGE_PUBLIC_URL}
          target="_blank"
          rel="noreferrer"
          className="rounded border border-ink-line px-3 py-1.5 font-mono text-xs uppercase tracking-wideish text-ink-soft transition hover:border-signal-amber hover:text-signal-amber"
        >
          Open TrueForge ↗
        </a>
      </div>

      <p className="mt-4 border-t border-ink-line pt-4 text-xs text-ink-muted">
        TrueForge owns the approval checkpoint itself, not this dashboard — a paused turn lives in its own
        session trace. Approve or reject a pending trade in TrueForge&rsquo;s own built-in UI; this panel shows
        connectivity and, below, the risk-flagged decisions that would have needed one.
      </p>

      {sessions && sessions.length > 0 ? (
        <ul className="mt-4 divide-y divide-ink-line border-t border-ink-line font-mono text-xs">
          {sessions.slice(0, 8).map((s, i) => (
            <li key={s.id ?? i} className="flex items-center justify-between gap-4 py-2 text-ink-soft">
              <span className="truncate">{s.name || s.id || `session ${i + 1}`}</span>
              {s.status ? <span className="text-ink-muted">{s.status}</span> : null}
            </li>
          ))}
        </ul>
      ) : null}
    </Panel>
  );
}

function RecentBreaches() {
  const { data, error, isLoading } = useTransactions(50);
  const breaches = (data || []).filter((t) => t.risk_snapshot?.any_breach);

  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">Recent risk-flagged decisions</p>
      {isLoading ? (
        <p className="mt-3 font-mono text-xs text-ink-muted">Loading…</p>
      ) : error ? null : breaches.length === 0 ? (
        <p className="mt-3 text-sm text-ink-soft">
          None of the last 50 decisions breached a limit — nothing here would have needed the gate.
        </p>
      ) : (
        <div className="mt-3 space-y-3">
          {breaches.map((t) => (
            <Ledger key={t.id} className="flex items-center justify-between gap-4 p-4 font-mono text-sm">
              <div>
                <p className="text-paper-ink">
                  {t.side.toUpperCase()} {t.asset}
                </p>
                <p className="mt-1 text-xs text-paper-muted">{formatTimestamp(t.timestamp)}</p>
              </div>
              <Stamp status={t.dry_run ? "dry_run" : "live"} size="sm" rotate={-3} />
            </Ledger>
          ))}
        </div>
      )}
    </div>
  );
}
