import { formatUsd, formatPct, formatQty, formatTimestamp } from "@/lib/format";

export function buildAuditMarkdown({ portfolio, metrics, risk, transactions, transactionsLimit }) {
  const lines = [];
  const now = new Date().toISOString();

  lines.push("# TreasuryForge — audit export");
  lines.push("");
  lines.push(`Generated ${now}`);
  lines.push("");

  lines.push("## Portfolio");
  lines.push("");
  if (portfolio) {
    lines.push(`- Cash: ${formatUsd(portfolio.cash_usd)}`);
    lines.push(`- Total value: ${formatUsd(portfolio.total_usd)}`);
    lines.push(`- Day-start baseline: ${formatUsd(portfolio.day_start_value_usd)}`);
    lines.push(`- Mode: ${portfolio.dry_run ? "DRY_RUN" : "Live"}`);
    lines.push("");
    lines.push("| Asset | Class | Quantity | Price (USD) | Value (USD) |");
    lines.push("|---|---|---|---|---|");
    for (const p of portfolio.positions || []) {
      lines.push(
        `| ${p.asset} | ${p.asset_class} | ${formatQty(p.quantity)} | ${
          p.price_usd != null ? formatUsd(p.price_usd) : "no quote"
        } | ${p.usd_value != null ? formatUsd(p.usd_value) : "—"} |`
      );
    }
  } else {
    lines.push("_Not available._");
  }
  lines.push("");

  lines.push("## Performance");
  lines.push("");
  if (metrics) {
    lines.push(`- Realized P&L: ${formatUsd(metrics.realized_pnl_usd, { signed: true })}`);
    lines.push(`- Unrealized P&L: ${formatUsd(metrics.unrealized_pnl_usd, { signed: true })}`);
    lines.push(`- Total P&L: ${formatUsd(metrics.total_pnl_usd, { signed: true })}`);
    lines.push(`- Win rate: ${metrics.win_rate != null ? formatPct(metrics.win_rate * 100) : "n/a"}`);
    lines.push(`- Closed trades: ${metrics.closed_trades}`);
    lines.push(`- Max drawdown: ${formatPct(metrics.max_drawdown_pct)}`);
    lines.push(`- Sharpe (unannualized): ${metrics.sharpe_ratio_unannualized ?? "n/a"}`);
  } else {
    lines.push("_Not available._");
  }
  lines.push("");

  lines.push("## Risk state");
  lines.push("");
  if (risk) {
    lines.push(
      `- Daily drawdown: ${formatPct(risk.daily_drawdown.current_pct)} of ${formatPct(
        risk.daily_drawdown.limit_pct
      )} limit — ${risk.daily_drawdown.breached ? "BREACHED" : "within limit"}`
    );
    lines.push(
      `- Consecutive losses: ${risk.consecutive_losses.streak} of ${risk.consecutive_losses.limit} limit — ${
        risk.consecutive_losses.breached ? "BREACHED" : "within limit"
      }`
    );
    lines.push(`- Concentration limit: ${formatPct(risk.concentration_limit_pct)}`);
    lines.push(`- Sell-all threshold: ${formatPct(risk.sell_all_threshold_pct)}`);
  } else {
    lines.push("_Not available._");
  }
  lines.push("");

  lines.push("## Decision log");
  lines.push("");
  if (transactions && transactions.length > 0) {
    if (transactionsLimit && transactions.length >= transactionsLimit) {
      lines.push(
        `_Showing the most recent ${transactions.length} transactions (the requested limit). Older ` +
          "transactions may exist and are not included in this export._"
      );
      lines.push("");
    }
    lines.push("| Time | Side | Asset | Quantity | Price | Value | Mode | Reason |");
    lines.push("|---|---|---|---|---|---|---|---|");
    for (const t of transactions) {
      const mode = t.side === "seed" ? "seed" : t.dry_run ? "dry_run" : "live";
      lines.push(
        `| ${formatTimestamp(t.timestamp)} | ${t.side} | ${t.asset} | ${formatQty(t.quantity, 4)} | ${formatUsd(
          t.price_usd
        )} | ${formatUsd(t.usd_value)} | ${mode} | ${(t.reason || "").replace(/\|/g, "/")} |`
      );
    }
  } else {
    lines.push("_No transactions recorded._");
  }
  lines.push("");

  return lines.join("\n");
}
