const STATUS = {
  pending: { label: "Hold for approval", tone: "text-signal-amber-ink" },
  approved: { label: "Cleared", tone: "text-signal-green-ink" },
  breach: { label: "Limit breached", tone: "text-signal-red-ink" },
  safe: { label: "Within limits", tone: "text-signal-green-ink" },
  dry_run: { label: "Simulated", tone: "text-paper-muted" },
  live: { label: "Executed", tone: "text-signal-green-ink" },
  rejected: { label: "Rejected", tone: "text-signal-red-ink" },
};

/**
 * The one visual idea every status indicator in the product shares: an
 * official ink stamp, not a colored pill. TreasuryForge's actual thesis is
 * "the agent proposes, the numbers get computed, and something stops for a
 * person" -- the stamp landing is that stop, rendered literally, everywhere
 * a decision has an outcome (hero, decision log, approval queue, risk
 * panel).
 */
export default function Stamp({
  status = "pending",
  label,
  code,
  rotate = -4,
  size = "sm",
  animate = false,
  className = "",
}) {
  const cfg = STATUS[status] ?? STATUS.pending;
  const text = label ?? cfg.label;

  const sizing =
    size === "lg"
      ? "gap-1 rounded-2xl border-[3px] px-8 py-5 text-lg md:text-xl"
      : "gap-1 rounded-md border-2 px-2.5 py-1 text-[10px] md:text-[11px]";

  return (
    <span
      style={{ "--stamp-rot": `${rotate}deg`, transform: `rotate(${rotate}deg)` }}
      className={[
        "relative inline-flex select-none flex-col items-center justify-center whitespace-nowrap",
        "border-current font-mono font-semibold uppercase leading-none tracking-stamp",
        "outline outline-1 outline-offset-[3px] outline-current/50",
        cfg.tone,
        sizing,
        animate ? "animate-stamp-land" : "",
        className,
      ].join(" ")}
      role="status"
    >
      <span>{text}</span>
      {code ? (
        <span className="mt-1.5 text-[0.65em] tracking-wideish opacity-70">{code}</span>
      ) : null}
    </span>
  );
}

export { STATUS as STAMP_STATUS };
