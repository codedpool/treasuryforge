import Image from "next/image";

export default function WhatWeBuilt() {
  return (
    <section id="how-it-works" className="relative flex min-h-screen flex-col bg-paper">
      {/* A purpose-painted transition image (navy water/shore easing into
          parchment gold) instead of a CSS-built gradient/texture -- a real
          spacer in document flow, not an overlay on either image. */}
      <div className="relative h-48 w-full shrink-0 md:h-64">
        <Image src="/transition.png" alt="" fill priority sizes="100vw" className="object-cover object-center" />
      </div>
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
