import Ledger from "@/components/Ledger";

export default function SelfAudit() {
  return (
    <section className="border-b border-ink-line bg-ink-raised px-6 py-20 md:px-12">
      <div className="mx-auto grid max-w-5xl gap-12 md:grid-cols-2 md:items-center">
        <div>
          <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber">The self-audit sub-agent</p>
          <h2 className="mt-4 font-display text-3xl font-semibold text-ink-bright md:text-4xl">
            A second, genuinely separate agent reviews the first one.
          </h2>
          <p className="mt-5 text-ink-soft">
            On request or its own initiative, the treasury agent delegates
            to a TrueForge sub-agent via{" "}
            <code className="text-ink-bright">create_sub_agent</code> — a
            real child thread with no access to the parent conversation,
            given a fully self-contained task: review the last 20 decisions,
            run a sandbox backtest of an alternative threshold, and report
            what it found.
          </p>
        </div>

        <Ledger className="p-6 font-mono text-sm">
          <p className="text-[11px] uppercase tracking-stamp text-paper-muted">Self-audit — excerpt</p>
          <p className="mt-4 leading-relaxed text-paper-ink">
            &ldquo;Reviewed 14 usable decisions (6 excluded, no risk snapshot).
            Backtested a 7% daily-drawdown threshold against the same
            history: would have allowed 2 additional trades, both losing.
            Recommend keeping the 5% limit.&rdquo;
          </p>
        </Ledger>
      </div>
    </section>
  );
}
