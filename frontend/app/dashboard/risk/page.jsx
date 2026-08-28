import RiskPanel from "@/components/dashboard/RiskPanel";
import ForceTriggerControls from "@/components/dashboard/ForceTriggerControls";

export default function RiskPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl text-paper-ink">Risk panel</h1>
        <p className="mt-1 text-sm text-paper-muted">
          The four computed triggers TrueForge&rsquo;s approval gate has no notion of on its own.
        </p>
      </div>
      <RiskPanel />
      <ForceTriggerControls />
    </div>
  );
}
