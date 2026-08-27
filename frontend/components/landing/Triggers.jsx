import Stamp from "@/components/Stamp";

const TRIGGERS = [
  { name: "Daily drawdown", threshold: "> 5%", basis: "Current value vs. a lazily-rolled day-start baseline" },
  { name: "Consecutive losses", threshold: "> 2", basis: "Realized P&L of the most recent executed sells" },
  { name: "Single-asset concentration", threshold: "> 50%", basis: "Projected post-trade value of the traded asset" },
  { name: '"Sell all"', threshold: "≥ 99%", basis: "Current holding vs. proposed sell quantity" },
];

export default function Triggers() {
  return (
    <section id="risk" className="border-b border-ink-line bg-ink px-6 py-20 md:px-12">
      <div className="mx-auto max-w-4xl">
        <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber">Risk limits</p>
        <h2 className="mt-4 font-display text-3xl font-semibold text-ink-bright md:text-4xl">
          Four triggers. Every one, a real computed number.
        </h2>
        <p className="mt-4 max-w-2xl text-ink-soft">
          TrueForge&rsquo;s checkpoint pauses every trade unconditionally —
          it has no notion of &ldquo;only if risky.&rdquo; So these numbers
          exist to give the human at the gate something to actually decide
          on, cited in the proposal itself.
        </p>

        <div className="mt-10 divide-y divide-ink-line border-y border-ink-line">
          {TRIGGERS.map((t) => (
            <div key={t.name} className="grid gap-3 py-5 md:grid-cols-[1fr_auto_1.3fr] md:items-center md:gap-6">
              <span className="font-display text-lg text-ink-bright">{t.name}</span>
              <span className="font-mono text-sm text-signal-amber">{t.threshold}</span>
              <span className="text-sm text-ink-muted">{t.basis}</span>
            </div>
          ))}
        </div>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <span className="text-sm text-ink-muted">Each has a debug endpoint to force it on cue for a demo:</span>
          <Stamp status="pending" label="Hold for approval" size="sm" rotate={-3} />
          <Stamp status="breach" label="Limit breached" size="sm" rotate={2} />
        </div>
      </div>
    </section>
  );
}
