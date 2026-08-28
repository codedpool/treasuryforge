import Image from "next/image";
import Link from "next/link";

export default function WhatWeBuilt() {
  return (
    <section id="how-it-works" className="relative min-h-screen bg-paper">
      <Image
        src="/info2.png"
        alt="TreasuryForge: a six-step chart -- price, check, stress, propose, hold, audit. Every trade is priced over live MCP quotes, checked against four computed limits (>5% daily drawdown, >2 losses in a row, >50% concentration, >=99% sell-all), stress-tested in a sandbox near a limit, proposed with its reasoning, held at TrueForge's approval gate, and logged for a second, separate agent to audit later."
        fill
        sizes="100vw"
        className="object-fill"
      />
      {/* Positioned and sized in percent, not px -- object-fill stretches
          the image to exactly match the section's own dimensions on both
          axes, so a point/width at a given % of the source image lands at
          that same % of the section for any viewport size. Width matches
          the table's own span (~55%-83%); centered under it, not
          left-aligned to its edge. */}
      <Link
        href="#closing"
        className="absolute left-[68.6%] top-[91%] flex w-[27%] -translate-x-1/2 items-center justify-center rounded bg-signal-amber-ink py-2.5 font-mono text-xs font-semibold uppercase tracking-wideish text-paper-raised shadow-[0_4px_14px_rgba(0,0,0,0.35)] transition hover:brightness-110 md:py-3 md:text-sm"
      >
        Continue
      </Link>
    </section>
  );
}
