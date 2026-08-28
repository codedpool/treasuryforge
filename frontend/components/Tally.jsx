import Panel from "@/components/Panel";
import Figure from "@/components/Figure";

/** One tally line instead of a grid of separate stat cards -- the numbers
 * here are entries in a single ledger, divided by hairlines, not
 * independent dashboard widgets competing for their own borders. */
export default function Tally({ items, className = "" }) {
  return (
    <Panel
      className={[
        "divide-y divide-paper-line sm:flex sm:divide-x sm:divide-y-0",
        className,
      ].join(" ")}
    >
      {items.map((item) => (
        <div key={item.label} className="flex-1 p-4">
          <Figure {...item} />
        </div>
      ))}
    </Panel>
  );
}
