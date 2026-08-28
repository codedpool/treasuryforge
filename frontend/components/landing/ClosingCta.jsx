import Image from "next/image";
import Link from "next/link";

export default function ClosingCta() {
  return (
    <section className="relative flex min-h-screen flex-col overflow-hidden bg-ink px-6 py-16 md:px-12">
      <Image src="/sec3.png" alt="" fill priority sizes="100vw" className="object-cover object-left" />

      {/* A watercolor bleed carrying info2.png's actual bottom-edge color
          (#e2bb82, sampled directly from the PNG) down into this section's
          own art, dissolving to nothing by mid-height -- an irregular,
          organic edge rather than a straight gradient line. Only applied
          here, not on WhatWeBuilt's own bottom: info2.png has real content
          (the last table row, the 6th waypoint) close to its bottom edge,
          and this section's top is comparatively open sky/water, so this
          is the side of the seam that can carry a color wash safely. */}
      <div
        className="watercolor-bleed pointer-events-none absolute inset-x-0 top-0 z-10 h-40 md:h-56"
        style={{ "--wc-from": "#e2bb82", "--wc-to": "transparent", "--wc-dir": "to bottom" }}
        aria-hidden="true"
      />

      <div className="relative z-10 flex flex-1 flex-col items-end justify-center">
        <div className="w-full max-w-md text-left">
          <h2 className="font-display text-3xl font-semibold text-paper-ink md:text-5xl">
            The strategy is dumb. The harness is strong.
          </h2>
          <p className="mt-5 text-paper-muted">
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
      </div>

      <footer className="relative z-10 mx-auto mt-16 flex w-full max-w-5xl flex-col items-center justify-between gap-3 border-t border-paper-line/70 pt-8 font-mono text-xs uppercase tracking-wideish text-paper-muted md:flex-row">
        <span>TreasuryForge — built on TrueForge</span>
        <span>Agent Harness Hackathon · WeMakeDevs × TrueFoundry</span>
      </footer>
    </section>
  );
}
