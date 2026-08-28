import Link from "next/link";

export default function ClosingCta() {
  return (
    <section className="flex min-h-screen flex-col justify-center bg-paper px-6 py-20 md:px-12">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="font-display text-3xl font-semibold text-paper-ink md:text-5xl">
          The strategy is dumb. The harness is strong.
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-paper-muted">
          Open the dashboard to see the live portfolio, the decision log, the
          approval queue, and the risk panel — reading the same data the
          agent itself works from.
        </p>
        <div className="mt-10">
          <Link
            href="/dashboard"
            className="inline-block rounded bg-signal-amber-ink px-6 py-3 font-mono text-sm font-semibold uppercase tracking-wideish text-paper-raised transition hover:brightness-110"
          >
            Open the dashboard
          </Link>
        </div>
      </div>

      <footer className="mx-auto mt-24 flex w-full max-w-5xl flex-col items-center justify-between gap-3 border-t border-paper-line pt-8 font-mono text-xs uppercase tracking-wideish text-paper-muted md:flex-row">
        <span>TreasuryForge — built on TrueForge</span>
        <span>Agent Harness Hackathon · WeMakeDevs × TrueFoundry</span>
      </footer>
    </section>
  );
}
