import Image from "next/image";
import Link from "next/link";

export default function ClosingCta() {
  return (
    <section id="closing" className="relative flex min-h-screen flex-col overflow-hidden bg-ink px-6 py-16 md:px-12">
      <Image src="/sec3.png" alt="" fill priority sizes="100vw" className="object-cover object-left" />

      <div className="relative z-10 flex flex-1 flex-col items-end justify-center">
        <div className="w-full max-w-md text-left">
          {/* Sits on a photo of variable brightness, not a flat color --
              same problem the hero had, same fix: text carries its own
              shadow rather than depending on the exact pixels behind it.
              A soft light halo (not a dark shadow -- the text is already
              dark) keeps it crisp against the warm gradient regardless of
              viewport crop. */}
          <h2 className="font-display text-3xl font-semibold text-paper-ink [text-shadow:0_2px_20px_rgba(243,234,214,0.9)] md:text-5xl">
            The strategy is dumb. The harness is strong.
          </h2>
          <p className="mt-5 text-ink [text-shadow:0_1px_14px_rgba(243,234,214,0.85)]">
            Open the dashboard to see the live portfolio, the decision log, the
            approval queue, and the risk panel — reading the same data the
            agent itself works from.
          </p>
          <div className="mt-10">
            <Link
              href="/dashboard"
              className="inline-block rounded bg-signal-amber-ink px-6 py-3 font-mono text-sm font-semibold uppercase tracking-wideish text-paper-raised shadow-[0_6px_20px_rgba(0,0,0,0.35)] transition hover:brightness-110"
            >
              Open the dashboard
            </Link>
          </div>
        </div>
      </div>

      <footer className="relative z-10 mx-auto mt-16 flex w-full max-w-5xl flex-col items-center justify-between gap-3 border-t border-paper-line/70 pt-8 font-mono text-xs uppercase tracking-wideish text-ink [text-shadow:0_1px_10px_rgba(243,234,214,0.85)] md:flex-row">
        <span>TreasuryForge — built on TrueForge</span>
        <span>Agent Harness Hackathon · WeMakeDevs × TrueFoundry</span>
      </footer>
    </section>
  );
}
