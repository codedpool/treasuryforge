const THESIS = [
  {
    title: "Reaching a tool.",
    body: "Live crypto and NSE equity quotes, a paper wallet, and a computed risk check — all MCP tools TrueForge calls natively, not a wrapper around an LLM chat loop.",
  },
  {
    title: "Running code in the sandbox.",
    body: "Before a near-limit trade, the agent generates and runs a fresh cross-asset stress test in TrueForge's sandbox — read-only, no wallet access, a new script every time.",
  },
  {
    title: "Stopping for a person.",
    body: (
      <>
        <code className="text-paper-ink">execute_trade</code> is registered
        with TrueForge&rsquo;s native approval checkpoint — every trade
        pauses, unconditionally, until a human clears it.
      </>
    ),
  },
];

const STEPS = [
  { n: "01", title: "Fetch market data", detail: "Live BTC/ETH and NSE equity quotes over MCP." },
  { n: "02", title: "Compute risk", detail: "check_risk_limits — real numbers, not a guess." },
  { n: "03", title: "Stress test", detail: "Near a limit? A fresh sandbox script runs a cross-asset shock." },
  { n: "04", title: "Propose", detail: "The agent cites the computed numbers in its reason." },
  { n: "05", title: "Approval gate", detail: "TrueForge's native checkpoint pauses, unconditionally." },
  { n: "06", title: "Execute", detail: "The wallet MCP tool is the only path that changes state." },
  { n: "07", title: "Log & audit", detail: "Reasoning and outcome recorded; a second agent reviews later." },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="flex min-h-screen flex-col justify-center bg-paper px-6 py-20 md:px-12">
      <div className="mx-auto w-full max-w-5xl">
        <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber-ink">
          The rule this was built to pass
        </p>
        <blockquote className="mt-5 max-w-3xl font-display text-2xl italic leading-snug text-paper-ink md:text-3xl">
          &ldquo;A judge has to see TrueForge reaching a tool, running code in
          the sandbox, and stopping for a person. If it would work just as
          well as a chat box, change the project.&rdquo;
        </blockquote>
        <p className="mt-4 font-mono text-xs uppercase tracking-wideish text-paper-muted">
          — WeMakeDevs × TrueFoundry, Agent Harness Hackathon
        </p>

        <div className="mt-14 grid gap-8 divide-y divide-paper-line border-y border-paper-line text-sm leading-relaxed text-paper-muted md:grid-cols-3 md:gap-10 md:divide-x md:divide-y-0 md:border-x">
          {THESIS.map((item) => (
            <p key={item.title} className="pt-8 first:pt-0 md:px-8 md:pt-0 md:first:pl-0 md:last:pr-0">
              <span className="font-display text-lg text-paper-ink">{item.title}</span>
              <br />
              {item.body}
            </p>
          ))}
        </div>

        <ol className="mt-14 grid gap-x-10 gap-y-5 divide-y divide-paper-line md:grid-cols-2 md:divide-y-0">
          {STEPS.map((step) => (
            <li key={step.n} className="pt-5 first:pt-0 md:pt-0">
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-sm text-paper-muted">{step.n}</span>
                <span className="font-display text-base text-paper-ink">{step.title}</span>
              </div>
              <p className="mt-1 pl-8 text-sm text-paper-muted">{step.detail}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
