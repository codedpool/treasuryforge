"use client";

import { usePortfolio, useMetrics } from "@/lib/api";
import { formatUsd } from "@/lib/format";
import DataState from "@/components/dashboard/DataState";
import Panel from "@/components/Panel";
import Figure from "@/components/Figure";

export default function PortfolioSummary() {
  const portfolio = usePortfolio();
  const metrics = useMetrics();

  return (
    <DataState isLoading={portfolio.isLoading} error={portfolio.error}>
      {portfolio.data ? <Cards portfolio={portfolio.data} metrics={metrics.data} /> : null}
    </DataState>
  );
}

function Cards({ portfolio, metrics }) {
  const cryptoUsd = (portfolio.positions || [])
    .filter((p) => p.asset_class === "crypto")
    .reduce((sum, p) => sum + (p.usd_value || 0), 0);
  const equityUsd = (portfolio.positions || [])
    .filter((p) => p.asset_class === "equity")
    .reduce((sum, p) => sum + (p.usd_value || 0), 0);

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <Panel className="p-4">
        <Figure label="Cash" value={formatUsd(portfolio.cash_usd)} />
      </Panel>
      <Panel className="p-4">
        <Figure label="Crypto" value={formatUsd(cryptoUsd)} />
      </Panel>
      <Panel className="p-4">
        <Figure label="Equities" value={formatUsd(equityUsd)} />
      </Panel>
      <Panel className="p-4">
        <Figure
          label="Total value"
          value={formatUsd(portfolio.total_usd)}
          tone="amber"
          sub={
            metrics
              ? `Total P&L ${formatUsd(metrics.total_pnl_usd, { signed: true })}`
              : undefined
          }
        />
      </Panel>
    </div>
  );
}
