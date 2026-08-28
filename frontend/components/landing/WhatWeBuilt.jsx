import Image from "next/image";

export default function WhatWeBuilt() {
  return (
    <section id="how-it-works" className="relative min-h-screen overflow-hidden bg-ink">
      {/* Full-bleed, same treatment as the hero. The earlier overflow bug
          came from stacking a text panel taller than one viewport on top
          of the image -- with no other content in this section now, a
          plain min-h-screen + fill can't be pushed past 100vh the way it
          was before. */}
      <Image
        src="/info2.png"
        alt="TreasuryForge: a six-step chart -- price, check, stress, propose, hold, audit. Every trade is priced over live MCP quotes, checked against four computed limits (>5% daily drawdown, >2 losses in a row, >50% concentration, >=99% sell-all), stress-tested in a sandbox near a limit, proposed with its reasoning, held at TrueForge's approval gate, and logged for a second, separate agent to audit later."
        fill
        priority
        sizes="100vw"
        className="object-cover object-center"
      />
      {/* Blends the seam with the hero above: the hero already fades to
          solid ink at its own bottom edge, so fading from that same ink
          back into this section's image reads as one continuous
          darkening across the boundary, not a hard cut between two
          different photos. */}
      <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-ink to-transparent md:h-56" />
    </section>
  );
}
