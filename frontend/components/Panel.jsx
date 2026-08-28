/** A lighter parchment surface: raised paper, hairline border, faint
 * grain. Use for UI chrome -- charts, forms, nav -- as opposed to Ledger,
 * which sits one shade deeper and is for content meant to read as a real
 * record. Both live in the same paper family now; the distinction is
 * weight (raised vs. base), not a separate dark/light surface.
 *
 * Renders children directly (no wrapping div) so a consumer's own layout
 * classes in `className` (flex, grid, justify-between, ...) apply to the
 * real children, not to a single opaque wrapper. The grain texture is a
 * ::before pseudo-element pinned behind everything with z-index: -1 (see
 * globals.css) rather than a z-10 wrapper around content -- that was the
 * original approach and it silently broke every consumer that passed a
 * flex/grid className, since Tailwind's layout utilities only affect an
 * element's *direct* children. */
export default function Panel({ children, className = "", as: Tag = "div", ...rest }) {
  return (
    <Tag
      className={[
        "grain-paper relative overflow-hidden rounded-lg border border-paper-line bg-paper-raised",
        className,
      ].join(" ")}
      {...rest}
    >
      {children}
    </Tag>
  );
}
