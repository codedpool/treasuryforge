import Image from "next/image";
import Link from "next/link";

export default function Hero() {
  return (
    <section className="relative flex min-h-screen flex-col overflow-hidden bg-ink px-6 pb-16 pt-10 md:px-12 md:pt-14">
      {/* The lake at dusk: a man rowing, at leisure, on the water -- while
          a treasury waits for him back at the cabin. The whole site's
          palette and mood are pulled from this one frame, not chosen
          separately from it. */}
      <Image
        src="/harness3.png"
        alt=""
        fill
        priority
        sizes="100vw"
        className="object-cover object-center"
      />
      {/* Three scrims, each covering a specific zone regardless of exactly
          where words wrap to: a full-width strip for the nav (the previous
          version capped this at max-w-2xl from the left, so the nav's
          right-side links -- sitting near the far right edge -- had no
          scrim under them at all and landed straight on the bright cloud),
          a taller left-anchored one for the headline/subhead, and a bottom
          one for the CTA row. Text also carries its own shadow below as a
          second, independent line of defense, since no scrim geometry is
          ever pixel-perfect across every viewport width. */}
      <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-ink/75 to-transparent md:h-36" />
      <div className="absolute left-0 top-0 h-full w-full max-w-3xl bg-gradient-to-r from-ink/85 via-ink/60 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 h-64 bg-gradient-to-t from-ink/85 to-transparent" />

      <nav className="relative z-10 flex items-center justify-between">
        <Image
          src="/logo.png"
          alt="TreasuryForge"
          width={1239}
          height={1270}
          priority
          className="h-16 w-auto drop-shadow-[0_2px_8px_rgba(0,0,0,0.75)] md:h-20"
        />
        <div className="flex items-center gap-6 font-mono text-xs uppercase tracking-wideish text-ink-bright/90 [text-shadow:0_1px_4px_rgba(20,50,75,0.8)]">
          <a href="#how-it-works" className="hidden hover:text-signal-amber md:inline">
            How it works
          </a>
          <a href="#risk" className="hidden hover:text-signal-amber md:inline">
            Risk limits
          </a>
          <Link
            href="/dashboard"
            className="rounded border border-ink-bright/50 bg-ink/35 px-3 py-1.5 text-ink-bright backdrop-blur-sm transition hover:border-signal-amber hover:text-signal-amber"
          >
            Open dashboard
          </Link>
        </div>
      </nav>

      <div className="relative z-10 flex flex-1 flex-col justify-start pb-16 pt-10 md:pt-14">
        <div className="max-w-xl">
          <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber [text-shadow:0_1px_4px_rgba(20,50,75,0.8)]">
            Built natively on TrueForge
          </p>
          <h1 className="mt-5 font-display text-4xl font-semibold leading-[1.08] text-ink-bright [text-shadow:0_2px_10px_rgba(20,50,75,0.85)] md:text-6xl">
            Go be somewhere else.
            <br />
            Nothing here moves without you.
          </h1>
          <p className="mt-6 max-w-md text-balance text-base leading-relaxed text-ink-bright/90 [text-shadow:0_1px_6px_rgba(20,50,75,0.8)] md:text-lg">
            TreasuryForge watches a simulated cash, crypto, and NSE-equity
            treasury while you&rsquo;re away — pricing every trade, computing
            four risk limits, and holding each one at the gate until you say
            yes.
          </p>
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-4 pt-10">
          <Link
            href="/dashboard"
            className="rounded bg-signal-amber px-5 py-3 font-mono text-sm font-semibold uppercase tracking-wideish text-ink shadow-[0_4px_16px_rgba(0,0,0,0.4)] transition hover:brightness-110"
          >
            Open the dashboard
          </Link>
          <a
            href="#how-it-works"
            className="font-mono text-sm uppercase tracking-wideish text-ink-bright/90 underline decoration-ink-bright/50 underline-offset-4 [text-shadow:0_1px_4px_rgba(20,50,75,0.8)] transition hover:text-signal-amber hover:decoration-signal-amber"
          >
            See how it decides
          </a>
        </div>
      </div>
    </section>
  );
}
