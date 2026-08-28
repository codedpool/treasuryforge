import Image from "next/image";
import ApprovalReceipt from "@/components/landing/ApprovalReceipt";

const STEPS = [
  { title: "Price it", detail: "Live BTC/ETH and NSE equity quotes over MCP, not a guess." },
  {
    title: "Check it",
    detail: "Four computed limits: >5% daily drawdown, >2 losses in a row, >50% concentration, ≥99% sell-all.",
  },
  { title: "Stress it", detail: "Near a limit, a fresh sandbox script runs a cross-asset shock — read-only, no wallet access." },
  { title: "Propose it", detail: "The agent cites the real numbers in its reasoning, not a hunch." },
  { title: "Hold it", detail: "TrueForge's native checkpoint pauses, unconditionally, until a person clears it." },
  { title: "Audit it", detail: "Logged, then reviewed later by a second, separate agent with no access to the first one's conversation." },
];

export default function WhatWeBuilt() {
  return (
    <section id="how-it-works" className="relative flex min-h-screen items-center overflow-hidden bg-ink">
      {/* A hand holding a watching eye out of still water -- the same idea
          this section is making: everything is watched, and something
          still holds before it goes through. The panel sits in the
          picture's own open sky/water on the right, so the hand and eye
          stay fully visible on the left, unobstructed. */}
      <Image src="/sec2.png" alt="" fill priority sizes="100vw" className="object-cover object-left" />

      <div className="relative z-10 w-full px-6 py-20 md:px-12">
        {/* The panel's background belongs to the panel itself, sized by its
            own content via normal document flow -- not a separate
            absolutely-positioned scrim guessing a height, which is exactly
            what made the hero's nav unreadable twice before this. */}
        <div className="ml-auto w-full max-w-2xl rounded-2xl bg-ink/85 p-8 backdrop-blur-md md:p-12">
          <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber">What we actually built</p>
          <h2 className="mt-4 font-display text-3xl font-semibold leading-tight text-ink-bright md:text-4xl">
            It watches everything. It still asks first.
          </h2>
          <p className="mt-5 text-base leading-relaxed text-ink-soft">
            A treasury agent that only chats about trades isn&rsquo;t a
            treasury agent. This one reaches real tools, runs real numbers in
            a real sandbox, and still stops, every single time, for a person
            to say yes.
          </p>

          <ol className="mt-8 divide-y divide-ink-line border-y border-ink-line">
            {STEPS.map((step, i) => (
              <li key={step.title} className="flex gap-4 py-4">
                <span className="font-mono text-sm text-ink-muted">{`0${i + 1}`}</span>
                <div>
                  <span className="font-display text-base text-ink-bright">{step.title}</span>
                  <p className="mt-0.5 text-sm text-ink-muted">{step.detail}</p>
                </div>
              </li>
            ))}
          </ol>

          <div className="mt-10 flex flex-col items-center gap-3">
            <ApprovalReceipt />
            <p className="max-w-xs text-center font-mono text-[11px] uppercase tracking-wideish text-ink-muted">
              Step 05, live — held at amber until a person clears it, stamped the instant they do.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
