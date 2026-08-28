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
      {/* A left-anchored scrim for the headline/subhead, and a bottom one
          for the CTA row. The nav doesn't rely on either -- see below: a
          fading gradient sized to *guess* the nav's height was the exact
          bug just fixed (by the time the gradient reaches the nav's actual
          content, especially near its bottom edge, it had already faded
          most of the way to transparent). A pill with its own flat,
          un-faded background is immune to that mismatch by construction. */}
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
        <div className="flex items-center gap-5 rounded-full border border-ink-bright/10 bg-ink/70 py-2.5 pl-5 pr-2.5 font-mono text-xs uppercase tracking-wideish text-ink-bright backdrop-blur-md md:gap-6">
          <a href="#how-it-works" className="hidden hover:text-signal-amber md:inline">
            How it works
          </a>
          <a href="#risk" className="hidden hover:text-signal-amber md:inline">
            Risk limits
          </a>
          <Link
            href="/dashboard"
            className="rounded-full bg-signal-amber px-3.5 py-1.5 text-ink transition hover:brightness-110"
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
