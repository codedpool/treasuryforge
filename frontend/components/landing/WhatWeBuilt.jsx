import Image from "next/image";

export default function WhatWeBuilt() {
  return (
    <section id="how-it-works" className="flex min-h-screen items-center justify-center bg-ink">
      <Image
        src="/info2.png"
        alt="TreasuryForge: a six-step chart -- price, check, stress, propose, hold, audit. Every trade is priced over live MCP quotes, checked against four computed limits (>5% daily drawdown, >2 losses in a row, >50% concentration, >=99% sell-all), stress-tested in a sandbox near a limit, proposed with its reasoning, held at TrueForge's approval gate, and logged for a second, separate agent to audit later."
        width={1536}
        height={1024}
        priority
        className="h-auto max-h-screen w-auto max-w-full object-contain"
      />
    </section>
  );
}
