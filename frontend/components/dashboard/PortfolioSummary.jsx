"use client";

import { usePortfolio, useMetrics } from "@/lib/api";
import { formatUsd } from "@/lib/format";
import DataState from "@/components/dashboard/DataState";
import Tally from "@/components/Tally";

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
    <Tally
      items={[
        { label: "Cash", value: formatUsd(portfolio.cash_usd) },
        { label: "Crypto", value: formatUsd(cryptoUsd) },
        { label: "Equities", value: formatUsd(equityUsd) },
        {
          label: "Total value",
          value: formatUsd(portfolio.total_usd),
          tone: "amber",
          sub: metrics
            ? `Total P&L ${formatUsd(metrics.total_pnl_usd, { signed: true })}`
            : undefined,
        },
      ]}
    />
  );
}
