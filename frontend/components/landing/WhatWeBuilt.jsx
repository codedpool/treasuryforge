import { Fragment } from "react";
import Image from "next/image";
import ApprovalReceipt from "@/components/landing/ApprovalReceipt";

const STEPS = ["Price", "Check", "Stress", "Propose", "Hold", "Audit"];

export default function WhatWeBuilt() {
  return (
    <section id="how-it-works" className="relative min-h-screen overflow-hidden bg-ink">
      {/* Capped to exactly one viewport (h-screen on its own wrapper, not
          tied to the section's actual content height) -- fill previously
          sized itself to the section, and content taller than 100vh was
          stretching the crop, which could push the hand and eye out of
          frame entirely. If content below ever needs more room than one
          viewport, it now continues on the section's flat bg-ink, not on a
          distorted image. */}
      <div className="absolute inset-x-0 top-0 h-screen">
        <Image src="/sec2.png" alt="" fill priority sizes="100vw" className="object-cover object-left" />
      </div>

      <div className="relative z-10 flex min-h-screen w-full items-center px-6 py-16 md:px-12">
        <div className="ml-auto w-full max-w-2xl rounded-2xl bg-ink/85 p-8 backdrop-blur-md md:p-10">
          <p className="font-mono text-xs uppercase tracking-stamp text-signal-amber">What we actually built</p>
          <h2 className="mt-4 font-display text-3xl font-semibold leading-tight text-ink-bright md:text-4xl">
            It watches everything. It still asks first.
          </h2>
          <p className="mt-5 text-base leading-relaxed text-ink-soft">
            A treasury agent that only chats about trades isn&rsquo;t a
            treasury agent. This one reaches real tools, runs real numbers,
            and still stops, every single time, for a person to say yes.
          </p>

          <div className="mt-9 flex flex-wrap items-start gap-y-6">
            {STEPS.map((step, i) => (
              <Fragment key={step}>
                <div className="flex w-16 flex-col items-center gap-2 text-center md:w-[4.5rem]">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full border border-signal-amber/60 font-mono text-xs text-ink-bright">
                    {i + 1}
                  </span>
                  <span className="font-display text-xs leading-tight text-ink-bright md:text-sm">{step}</span>
                </div>
                {i < STEPS.length - 1 ? (
                  <span
                    className="mt-[18px] h-px w-3 shrink-0 border-t border-dashed border-ink-line/70 md:w-5"
                    aria-hidden
                  />
                ) : null}
              </Fragment>
            ))}
          </div>

          <p className="mt-6 text-sm leading-relaxed text-ink-muted">
            Checked on every proposal: <span className="text-ink-soft">&gt;5% daily drawdown</span> ·{" "}
            <span className="text-ink-soft">&gt;2 losses in a row</span> ·{" "}
            <span className="text-ink-soft">&gt;50% concentration</span> ·{" "}
            <span className="text-ink-soft">&ge;99% sell-all</span>. Near a limit, a sandbox stress test runs before
            the agent proposes; every decision is logged and later reviewed by a second, separate agent.
          </p>

          <div className="mt-8 flex flex-col items-center gap-3">
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
