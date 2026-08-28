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
      <div className="absolute inset-x-0 bottom-0 h-64 bg-gradient-to-t from-ink to-transparent" />

      <nav className="relative z-10 flex items-center justify-between">
        <Image
          src="/logo.png"
          alt="TreasuryForge"
          width={1239}
          height={1270}
          priority
          className="h-16 w-auto drop-shadow-[0_2px_8px_rgba(0,0,0,0.75)] md:h-20"
        />
        <div className="flex items-center rounded-full border border-ink-bright/10 bg-ink/70 py-2.5 pl-2.5 pr-2.5 font-mono text-xs uppercase tracking-wideish text-ink-bright backdrop-blur-md">
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
            Autonomous treasury agent — built on TrueForge
          </p>
          <h1 className="mt-5 font-display text-4xl font-semibold leading-[1.08] text-ink-bright [text-shadow:0_2px_10px_rgba(20,50,75,0.85)] md:text-6xl">
            Everything runs without YOU.
            <br />
            Nothing executes without YOU.
          </h1>
          <p className="mt-6 max-w-md text-balance text-base leading-relaxed text-ink-bright/90 [text-shadow:0_1px_6px_rgba(20,50,75,0.8)] md:text-lg">
            TreasuryForge prices every trade across cash, crypto, and NSE
            equities, computes four risk limits, and stress-tests the risky
            ones — on its own. The one thing it can&rsquo;t do alone is pull
            the trigger: every trade holds at the gate until you say yes.
          </p>
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-4 pt-10">
          <a
            href="#how-it-works"
            className="rounded bg-signal-amber px-5 py-3 font-mono text-sm font-semibold uppercase tracking-wideish text-ink shadow-[0_4px_16px_rgba(0,0,0,0.4)] transition hover:brightness-110"
          >
            See how it works
          </a>
        </div>
      </div>
    </section>
  );
}
