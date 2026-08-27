"use client";

import { usePortfolio } from "@/lib/api";

export default function StatusBadge() {
  const { data, error, isLoading } = usePortfolio();

  if (isLoading) {
    return <Dot tone="muted" label="Connecting…" />;
  }
  if (error) {
    return <Dot tone="red" label="Wallet server unreachable" />;
  }
  return <Dot tone={data?.dry_run ? "amber" : "green"} label={data?.dry_run ? "DRY_RUN" : "Live trading"} />;
}

function Dot({ tone, label }) {
  const toneClass =
    { muted: "bg-ink-muted", red: "bg-signal-red", amber: "bg-signal-amber", green: "bg-signal-green" }[tone] ??
    "bg-ink-muted";
  return (
    <span className="flex items-center gap-2 font-mono text-xs uppercase tracking-wideish text-ink-muted">
      <span className={`h-1.5 w-1.5 rounded-full ${toneClass}`} aria-hidden />
      {label}
    </span>
  );
}
