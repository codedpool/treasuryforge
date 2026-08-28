import ApprovalReceipt from "@/components/landing/ApprovalReceipt";

const TRIGGERS = [
  { name: "Daily drawdown", threshold: "> 5%", basis: "Current value vs. a lazily-rolled day-start baseline" },
  { name: "Consecutive losses", threshold: "> 2", basis: "Realized P&L of the most recent executed sells" },
  { name: "Single-asset concentration", threshold: "> 50%", basis: "Projected post-trade value of the traded asset" },
  { name: '"Sell all"', threshold: "≥ 99%", basis: "Current holding vs. proposed sell quantity" },
];

export default function RiskAndOversight() {
  return (
    <section id="risk" className="flex min-h-screen flex-col justify-center bg-ink px-6 py-20 md:px-12">
      <div className="mx-auto w-full max-w-5xl">
        <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber">What&rsquo;s actually being watched</p>
        <h2 className="mt-4 max-w-xl font-display text-3xl font-semibold text-ink-bright md:text-4xl">
          Four numbers stand between a proposal and a trade.
        </h2>
        <p className="mt-4 max-w-xl text-ink-soft">
          TrueForge&rsquo;s checkpoint pauses every trade unconditionally — it
          has no notion of &ldquo;only if risky.&rdquo; These numbers exist to
          give the person at the gate something to actually decide on.
        </p>

        <div className="mt-12 grid gap-12 md:grid-cols-[1.1fr_0.9fr] md:items-start md:gap-16">
          <div>
            <div className="divide-y divide-ink-line border-y border-ink-line">
              {TRIGGERS.map((t) => (
                <div key={t.name} className="grid gap-2 py-5 md:grid-cols-[1fr_auto_1.3fr] md:items-center md:gap-6">
                  <span className="font-display text-lg text-ink-bright">{t.name}</span>
                  <span className="font-mono text-sm text-signal-amber">{t.threshold}</span>
                  <span className="text-sm text-ink-muted">{t.basis}</span>
                </div>
              ))}
            </div>

            <div className="mt-10">
              <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber">
                A second agent watches the first
              </p>
              <p className="mt-3 max-w-md text-sm leading-relaxed text-ink-soft">
                On request or its own initiative, the treasury agent delegates
                to a genuinely separate TrueForge sub-agent — no access to the
                parent conversation — to review the last 20 decisions and
                backtest an alternative threshold.
              </p>
              <blockquote className="mt-4 max-w-md border-l-2 border-signal-amber/50 pl-4 text-sm italic leading-relaxed text-ink-soft">
                &ldquo;Reviewed 14 usable decisions. Backtested a 7% daily
                drawdown threshold: would have allowed 2 additional trades,
                both losing. Recommend keeping the 5% limit.&rdquo;
              </blockquote>
            </div>
          </div>

          <div className="flex flex-col items-center gap-3 md:items-end">
            <ApprovalReceipt />
            <p className="max-w-xs text-center font-mono text-[11px] uppercase tracking-wideish text-ink-muted md:text-right">
              The exact shape check_risk_limits returns, replayed on a loop —
              held at amber until a person clears it, stamped the instant they do.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
