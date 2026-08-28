import PortfolioSummary from "@/components/dashboard/PortfolioSummary";
import PnLChart from "@/components/dashboard/PnLChart";
import AllocationChart from "@/components/dashboard/AllocationChart";
import Panel from "@/components/Panel";

export default function OverviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl text-paper-ink">Overview</h1>
        <p className="mt-1 text-sm text-paper-muted">Cash, holdings, and the equity curve — live from the wallet server.</p>
      </div>

      <PortfolioSummary />

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Panel className="p-5">
          <h2 className="font-mono text-xs uppercase tracking-wideish text-paper-muted">Equity curve</h2>
          <div className="mt-4">
            <PnLChart />
          </div>
        </Panel>
        <Panel className="p-5">
          <h2 className="font-mono text-xs uppercase tracking-wideish text-paper-muted">Allocation</h2>
          <div className="mt-4">
            <AllocationChart />
          </div>
        </Panel>
      </div>
    </div>
  );
}
