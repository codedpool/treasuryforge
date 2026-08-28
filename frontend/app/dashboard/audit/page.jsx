import AuditExport from "@/components/dashboard/AuditExport";

export default function AuditPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl text-paper-ink">Audit export</h1>
        <p className="mt-1 text-sm text-paper-muted">
          Portfolio, performance, risk state, and the full decision log, compiled to Markdown.
        </p>
      </div>
      <AuditExport />
    </div>
  );
}
