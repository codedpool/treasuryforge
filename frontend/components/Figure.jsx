/** A large tabular-mono number with an eyebrow label -- the type treatment
 * that carries the product's actual thesis: every number here is computed,
 * not narrated, so the numeral itself is the hero, not a decorative stat
 * card around it. */
export default function Figure({ label, value, sub, tone = "bright", size = "md", className = "" }) {
  const toneClass =
    {
      bright: "text-ink-bright",
      amber: "text-signal-amber",
      green: "text-signal-green",
      red: "text-signal-red",
      muted: "text-ink-soft",
    }[tone] ?? "text-ink-bright";

  const sizeClass =
    {
      lg: "text-4xl md:text-5xl",
      md: "text-2xl md:text-3xl",
      sm: "text-lg",
    }[size] ?? "text-2xl";

  return (
    <div className={className}>
      <div className="font-mono text-[11px] uppercase tracking-wideish text-ink-muted">{label}</div>
      <div className={`tabular-figures mt-1 font-mono font-medium ${sizeClass} ${toneClass}`}>{value}</div>
      {sub ? <div className="mt-1 text-xs text-ink-muted">{sub}</div> : null}
    </div>
  );
}
