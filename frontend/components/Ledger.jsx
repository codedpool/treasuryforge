/** A vellum document surface -- the decision log, the audit export, the
 * hero's mock receipt. Anything meant to feel like a real, stamped record
 * rather than app chrome sits on paper, not ink.
 *
 * Renders children directly -- see Panel's docstring for why there's no
 * wrapping div around them. */
export default function Ledger({ children, className = "", as: Tag = "div", ...rest }) {
  return (
    <Tag
      className={[
        "grain-paper relative overflow-hidden rounded-sm border border-paper-line bg-paper text-paper-ink shadow-[0_12px_30px_-16px_rgba(0,0,0,0.6)]",
        className,
      ].join(" ")}
      {...rest}
    >
      {children}
    </Tag>
  );
}
