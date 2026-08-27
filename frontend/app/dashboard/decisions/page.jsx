import DecisionLog from "@/components/dashboard/DecisionLog";

export default function DecisionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl text-ink-bright">Decision log</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Every trade and seed allocation, newest first — including the exact risk numbers computed at the time.
        </p>
      </div>
      <DecisionLog limit={50} />
    </div>
  );
}
