import ApprovalQueue from "@/components/dashboard/ApprovalQueue";

export default function ApprovalsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl text-ink-bright">Approval queue</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Where a proposed trade actually stops — and where it stopped historically.
        </p>
      </div>
      <ApprovalQueue />
    </div>
  );
}
