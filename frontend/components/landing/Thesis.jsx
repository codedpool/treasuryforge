export default function Thesis() {
  return (
    <section className="border-b border-ink-line bg-ink px-6 py-20 md:px-12">
      <div className="mx-auto max-w-3xl">
        <p className="font-mono text-xs uppercase tracking-stamp text-ink-muted">
          The rule this was built to pass
        </p>
        <blockquote className="mt-6 font-display text-2xl italic leading-snug text-ink-bright md:text-3xl">
          &ldquo;A judge has to see TrueForge reaching a tool, running code
          in the sandbox, and stopping for a person. If it would work just
          as well as a chat box, change the project.&rdquo;
        </blockquote>
        <p className="mt-5 font-mono text-xs uppercase tracking-wideish text-ink-muted">
          — WeMakeDevs × TrueFoundry, Agent Harness Hackathon
        </p>

        <div className="mt-12 grid gap-8 border-t border-ink-line pt-10 text-sm leading-relaxed text-ink-soft md:grid-cols-3 md:gap-10">
          <p>
            <span className="font-display text-lg text-ink-bright">Reaching a tool.</span>
            <br />
            Live crypto and NSE equity quotes, a paper wallet, and a
            computed risk check — all MCP tools TrueForge calls natively,
            not a wrapper around an LLM chat loop.
          </p>
          <p>
            <span className="font-display text-lg text-ink-bright">Running code in the sandbox.</span>
            <br />
            Before a near-limit trade, the agent generates and runs a fresh
            cross-asset stress test in TrueForge&rsquo;s sandbox — read-only,
            no wallet access, a new script every time.
          </p>
          <p>
            <span className="font-display text-lg text-ink-bright">Stopping for a person.</span>
            <br />
            <code className="text-ink-bright">execute_trade</code> is
            registered with TrueForge&rsquo;s native approval checkpoint —
            every trade pauses, unconditionally, until a human clears it.
          </p>
        </div>
      </div>
    </section>
  );
}
