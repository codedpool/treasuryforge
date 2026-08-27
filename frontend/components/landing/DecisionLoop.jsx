const STEPS = [
  { n: "01", title: "Fetch market data", detail: "Live BTC/ETH and NSE equity quotes over MCP." },
  { n: "02", title: "Compute risk", detail: "check_risk_limits — real numbers, not a guess." },
  { n: "03", title: "Stress test", detail: "Near a limit? A fresh sandbox script runs a cross-asset shock." },
  { n: "04", title: "Propose", detail: "Agent cites the computed numbers in its reason." },
  { n: "05", title: "Approval gate", detail: "TrueForge's native checkpoint pauses, unconditionally." },
  { n: "06", title: "Execute", detail: "The wallet MCP tool is the only path that changes state." },
  { n: "07", title: "Log & audit", detail: "Reasoning, risk snapshot, and outcome recorded; a sub-agent reviews later." },
];

export default function DecisionLoop() {
  return (
    <section id="how-it-works" className="border-b border-ink-line bg-ink-raised px-6 py-20 md:px-12">
      <div className="mx-auto max-w-5xl">
        <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber">The decision loop</p>
        <h2 className="mt-4 max-w-xl font-display text-3xl font-semibold text-ink-bright md:text-4xl">
          Seven steps, every time — the harness doing the work, not this page.
        </h2>

        <ol className="mt-12 grid gap-x-8 gap-y-10 md:grid-cols-7">
          {STEPS.map((step, i) => (
            <li key={step.n} className="relative">
              <div className="flex items-baseline gap-3 md:block md:gap-0">
                <span className="font-mono text-sm text-ink-muted">{step.n}</span>
                <h3 className="font-display text-lg text-ink-bright md:mt-3">{step.title}</h3>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">{step.detail}</p>
              {i < STEPS.length - 1 ? (
                <span
                  aria-hidden
                  className="absolute right-[-1rem] top-1.5 hidden h-px w-8 bg-ink-line md:block"
                />
              ) : null}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
