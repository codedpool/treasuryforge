import Image from "next/image";

export default function WhatWeBuilt() {
  return (
    <section
      id="how-it-works"
      className="flex min-h-screen items-center justify-center bg-ink px-6 py-10 md:px-12"
    >
      {/* Sized in viewport units with a hard cap, not by its content -- an
          image at a fixed aspect ratio (object-contain, never cropped,
          since every part of this chart carries real information) can't
          overflow the way the previous text panel did. */}
      <div className="relative h-[85vh] w-full max-w-6xl">
        <Image
          src="/info2.png"
          alt="TreasuryForge: a six-step chart -- price, check, stress, propose, hold, audit. Every trade is priced over live MCP quotes, checked against four computed limits (>5% daily drawdown, >2 losses in a row, >50% concentration, >=99% sell-all), stress-tested in a sandbox near a limit, proposed with its reasoning, held at TrueForge's approval gate, and logged for a second, separate agent to audit later."
          fill
          sizes="100vw"
          className="object-contain"
        />
      </div>
    </section>
  );
}
