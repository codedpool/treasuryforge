import Link from "next/link";
import ApprovalReceipt from "@/components/landing/ApprovalReceipt";

export default function Hero() {
  return (
    <section className="grain-ink relative overflow-hidden border-b border-ink-line bg-ink px-6 pb-20 pt-10 md:px-12 md:pt-14">
      <nav className="relative z-10 flex items-center justify-between font-mono text-xs uppercase tracking-wideish text-ink-muted">
        <span className="text-ink-bright">TreasuryForge</span>
        <div className="flex items-center gap-6">
          <a href="#how-it-works" className="hidden hover:text-ink-bright md:inline">
            How it works
          </a>
          <a href="#risk" className="hidden hover:text-ink-bright md:inline">
            Risk limits
          </a>
          <Link
            href="/dashboard"
            className="rounded border border-ink-line px-3 py-1.5 text-ink-bright transition hover:border-signal-amber hover:text-signal-amber"
          >
            Open dashboard
          </Link>
        </div>
      </nav>

      <div className="relative z-10 mt-16 grid gap-14 md:mt-24 md:grid-cols-[1.1fr_0.9fr] md:items-center md:gap-10">
        <div>
          <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber">
            Built natively on TrueForge
          </p>
          <h1 className="mt-5 max-w-xl font-display text-4xl font-semibold leading-[1.08] text-ink-bright md:text-6xl">
            An agent that reaches for the trade, and stops for you.
          </h1>
          <p className="mt-6 max-w-lg text-balance text-base leading-relaxed text-ink-soft md:text-lg">
            TreasuryForge manages a simulated cash, crypto, and NSE equity
            treasury. Every proposal is priced, checked against four
            computed risk limits, and held for a human at the gate — not a
            chat box that happens to place trades.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Link
              href="/dashboard"
              className="rounded bg-signal-amber px-5 py-3 font-mono text-sm font-semibold uppercase tracking-wideish text-ink transition hover:brightness-110"
            >
              Open the dashboard
            </Link>
            <a
              href="#how-it-works"
              className="font-mono text-sm uppercase tracking-wideish text-ink-soft underline decoration-ink-line underline-offset-4 transition hover:text-ink-bright"
            >
              See the decision loop
            </a>
          </div>
        </div>

        <div className="flex justify-center md:justify-end">
          <ApprovalReceipt />
        </div>
      </div>
    </section>
  );
}
