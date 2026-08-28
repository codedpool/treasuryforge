import QuantDesk from "@/components/dashboard/QuantDesk";

export default function QuantDeskPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl text-paper-ink">Quant Desk</h1>
        <p className="mt-1 text-sm text-paper-muted">
          The sandbox&rsquo;s cross-asset stress tests — where they run, and which decisions asked for one.
        </p>
      </div>
      <QuantDesk />
    </div>
  );
}
