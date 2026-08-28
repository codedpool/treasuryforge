import Image from "next/image";

export default function WhatWeBuilt() {
  return (
    <section id="how-it-works" className="relative flex min-h-screen flex-col bg-paper">
      {/* A real spacer in document flow, not an overlay on top of either
          image -- the previous blend attempt darkened info2.png's own
          title banner because it sat on top of the image's content. This
          sits *between* the hero and the image instead, so neither one is
          touched, while still giving the seam a soft navy-to-paper fade. */}
      <div className="h-10 w-full shrink-0 bg-gradient-to-b from-ink to-paper md:h-16" aria-hidden="true" />
      <div className="relative flex-1">
        <Image
          src="/info2.png"
          alt="TreasuryForge: a six-step chart -- price, check, stress, propose, hold, audit. Every trade is priced over live MCP quotes, checked against four computed limits (>5% daily drawdown, >2 losses in a row, >50% concentration, >=99% sell-all), stress-tested in a sandbox near a limit, proposed with its reasoning, held at TrueForge's approval gate, and logged for a second, separate agent to audit later."
          fill
          priority
          sizes="100vw"
          className="object-fill"
        />
      </div>
    </section>
  );
}
