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
      {/* The sky's upper-left quadrant is already the darkest, cleanest
          part of the frame -- that's where the copy lives, so only a light
          scrim is needed there, not a wall-to-wall darkening that would
          flatten the clouds, the trees, or the water. */}
      <div className="absolute inset-x-0 top-0 h-[55%] w-full max-w-2xl bg-gradient-to-br from-ink/55 via-ink/15 to-transparent md:h-[65%]" />
      <div className="absolute inset-x-0 bottom-0 h-56 bg-gradient-to-t from-ink/70 to-transparent" />

      <nav className="relative z-10 flex items-center justify-between">
        <Image
          src="/logo.png"
          alt="TreasuryForge"
          width={1239}
          height={1270}
          priority
          className="h-16 w-auto drop-shadow-[0_2px_8px_rgba(0,0,0,0.65)] md:h-20"
        />
        <div className="flex items-center gap-6 font-mono text-xs uppercase tracking-wideish text-ink-soft">
          <a href="#how-it-works" className="hidden hover:text-ink-bright md:inline">
            How it works
          </a>
          <a href="#risk" className="hidden hover:text-ink-bright md:inline">
            Risk limits
          </a>
          <Link
            href="/dashboard"
            className="rounded border border-ink-soft/40 px-3 py-1.5 text-ink-bright transition hover:border-signal-amber hover:text-signal-amber"
          >
            Open dashboard
          </Link>
        </div>
      </nav>

      <div className="relative z-10 flex flex-1 flex-col justify-start pb-16 pt-10 md:pt-14">
        <div className="max-w-xl">
          <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber">
            Built natively on TrueForge
          </p>
          <h1 className="mt-5 font-display text-4xl font-semibold leading-[1.08] text-ink-bright md:text-6xl">
            Go be somewhere else.
            <br />
            Nothing here moves without you.
          </h1>
          <p className="mt-6 max-w-md text-balance text-base leading-relaxed text-ink-soft md:text-lg">
            TreasuryForge watches a simulated cash, crypto, and NSE-equity
            treasury while you&rsquo;re away — pricing every trade, computing
            four risk limits, and holding each one at the gate until you say
            yes.
          </p>
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-4 pt-10">
          <Link
            href="/dashboard"
            className="rounded bg-signal-amber px-5 py-3 font-mono text-sm font-semibold uppercase tracking-wideish text-ink transition hover:brightness-110"
          >
            Open the dashboard
          </Link>
          <a
            href="#how-it-works"
            className="font-mono text-sm uppercase tracking-wideish text-ink-soft underline decoration-ink-soft/40 underline-offset-4 transition hover:text-ink-bright"
          >
            See how it decides
          </a>
        </div>
      </div>
    </section>
  );
}
