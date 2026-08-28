import Image from "next/image";

export default function WhatWeBuilt() {
  return (
    <section id="how-it-works" className="relative min-h-screen bg-ink pt-20 md:pt-28">
      {/* The previous attempt at a blend put a darkening gradient directly
          on top of the image -- fine for a photo, wrong for this one,
          since every pixel of an infographic is informational and the
          title banner sits right where that gradient was strongest. The
          hero's own bottom edge is now full-opacity ink (not ink/85), and
          this section opens with flat ink of the exact same color/opacity
          for the height of its top padding -- two adjacent regions of an
          identical flat color join with no visible seam at all, and the
          image itself starts completely undimmed once they're behind it. */}
      <div className="relative h-[calc(100vh-5rem)] w-full overflow-hidden md:h-[calc(100vh-7rem)]">
        <Image
          src="/info2.png"
          alt="TreasuryForge: a six-step chart -- price, check, stress, propose, hold, audit. Every trade is priced over live MCP quotes, checked against four computed limits (>5% daily drawdown, >2 losses in a row, >50% concentration, >=99% sell-all), stress-tested in a sandbox near a limit, proposed with its reasoning, held at TrueForge's approval gate, and logged for a second, separate agent to audit later."
          fill
          priority
          sizes="100vw"
          className="object-cover object-center"
        />
      </div>
    </section>
  );
}
