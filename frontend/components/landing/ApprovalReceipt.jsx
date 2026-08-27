"use client";

import { useEffect, useRef, useState } from "react";
import Stamp from "@/components/Stamp";
import Ledger from "@/components/Ledger";

// One scripted decision, replayed on a loop -- real numbers from the kind
// of proposal check_risk_limits actually produces, not placeholder text.
const STEPS = [
  { phase: "propose", holdMs: 1900 },
  { phase: "compute", holdMs: 1900 },
  { phase: "pending", holdMs: 2400 },
  { phase: "approved", holdMs: 2600 },
];

export default function ApprovalReceipt() {
  const [stepIndex, setStepIndex] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(false);
  const timeoutRef = useRef(null);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
    const onChange = (e) => setReducedMotion(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    if (reducedMotion) return undefined;
    const step = STEPS[stepIndex];
    timeoutRef.current = setTimeout(() => {
      setStepIndex((i) => (i + 1) % STEPS.length);
    }, step.holdMs);
    return () => clearTimeout(timeoutRef.current);
  }, [stepIndex, reducedMotion]);

  const phase = reducedMotion ? "approved" : STEPS[stepIndex].phase;
  const showRisk = phase !== "propose";
  const showStamp = phase === "pending" || phase === "approved";
  const stampStatus = phase === "approved" ? "approved" : "pending";
  const stampAnimKey = `${phase}`;

  return (
    <div className="relative">
      <Ledger className="w-full max-w-sm p-6 font-mono text-sm">
        <div className="flex items-baseline justify-between border-b border-dashed border-paper-line pb-3">
          <span className="text-[11px] uppercase tracking-stamp text-paper-muted">Proposal No. 0417</span>
          <span className="text-[11px] text-paper-muted">DRY_RUN</span>
        </div>

        <dl className="mt-4 space-y-2.5">
          <Row label="Asset" value="BTC" />
          <Row label="Side" value="Buy" />
          <Row label="Amount" value="$1,840.00" />
          <Row label="Reason" value="24h momentum +6.1%" small />
        </dl>

        <div
          className={[
            "mt-4 space-y-2 overflow-hidden border-t border-dashed border-paper-line pt-3 transition-[max-height,opacity] duration-500",
            showRisk ? "max-h-40 opacity-100" : "max-h-0 opacity-0",
          ].join(" ")}
          aria-hidden={!showRisk}
        >
          <Row label="Daily drawdown" value="4.8% → 5.6%" tone="red" />
          <Row label="Concentration" value="42% → 51%" tone="red" />
          <Row label="Consecutive losses" value="0" tone="green" />
        </div>

        <div className="mt-5 flex min-h-[76px] items-center justify-end border-t border-dashed border-paper-line pt-4">
          {showStamp ? (
            <Stamp key={stampAnimKey} status={stampStatus} rotate={-6} animate={!reducedMotion} />
          ) : (
            <span className="text-[11px] uppercase tracking-stamp text-paper-muted">Awaiting risk check…</span>
          )}
        </div>
      </Ledger>

      <p className="mt-3 text-center font-mono text-[11px] uppercase tracking-wideish text-ink-muted">
        A real check_risk_limits shape, replayed
      </p>
    </div>
  );
}

function Row({ label, value, tone, small }) {
  const toneClass =
    tone === "red" ? "text-signal-red-ink" : tone === "green" ? "text-signal-green-ink" : "text-paper-ink";
  return (
    <div className="flex items-baseline justify-between gap-4">
      <dt className="text-paper-muted">{label}</dt>
      <dd className={`${toneClass} ${small ? "text-xs" : ""} text-right`}>{value}</dd>
    </div>
  );
}
