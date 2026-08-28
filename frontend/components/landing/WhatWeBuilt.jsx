import Image from "next/image";

export default function WhatWeBuilt() {
  return (
    <section id="how-it-works" className="relative flex min-h-screen flex-col bg-paper">
      {/* Fog rising off the lake, thinning as the chart comes into view --
          a real spacer in document flow, not an overlay on either image
          (the previous attempt at a gradient directly over info2.png
          darkened its own title banner). An eased multi-stop gradient
          (holds dark near the hero, dissolves gradually rather than on a
          straight ramp) plus the .mist-seam turbulence texture from
          globals.css for something with actual atmosphere, not a flat
          CSS bar. Fades to fully transparent at its own bottom edge,
          revealing the section's own bg-paper underneath -- no color to
          match by hand. */}
      <div
        className="mist-seam h-28 w-full shrink-0 bg-[linear-gradient(to_bottom,rgb(20,50,75)_0%,rgb(20,50,75)_15%,rgba(20,50,75,0.55)_45%,rgba(20,50,75,0.12)_75%,transparent_100%)] md:h-40"
        aria-hidden="true"
      />
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
