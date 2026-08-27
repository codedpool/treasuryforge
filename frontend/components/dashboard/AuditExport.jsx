"use client";

import { useState } from "react";
import { usePortfolio, useMetrics, useRiskSummary, useTransactions } from "@/lib/api";
import { buildAuditMarkdown } from "@/lib/auditExport";
import DataState from "@/components/dashboard/DataState";
import Panel from "@/components/Panel";

export default function AuditExport() {
  const portfolio = usePortfolio();
  const metrics = useMetrics();
  const risk = useRiskSummary();
  const transactions = useTransactions(200);
  const [copied, setCopied] = useState(false);

  const loading = portfolio.isLoading || metrics.isLoading || risk.isLoading || transactions.isLoading;
  const error = portfolio.error;

  return (
    <DataState isLoading={loading} error={error}>
      {portfolio.data ? (
        <Body
          markdown={buildAuditMarkdown({
            portfolio: portfolio.data,
            metrics: metrics.data,
            risk: risk.data,
            transactions: transactions.data,
          })}
          copied={copied}
          setCopied={setCopied}
        />
      ) : null}
    </DataState>
  );
}

function Body({ markdown, copied, setCopied }) {
  async function handleCopy() {
    await navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `treasuryforge-audit-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.md`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleDownload}
          className="rounded bg-signal-amber px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wideish text-ink transition hover:brightness-110"
        >
          Download .md
        </button>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded border border-ink-line px-4 py-2 font-mono text-xs uppercase tracking-wideish text-ink-soft transition hover:border-signal-amber hover:text-signal-amber"
        >
          {copied ? "Copied" : "Copy to clipboard"}
        </button>
      </div>

      <Panel className="max-h-[32rem] overflow-auto p-4">
        <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-ink-soft">{markdown}</pre>
      </Panel>
    </div>
  );
}
