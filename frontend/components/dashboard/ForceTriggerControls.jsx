"use client";

import { useState } from "react";
import { useSWRConfig } from "swr";
import { forceTrigger } from "@/lib/api";
import Panel from "@/components/Panel";

const TRIGGERS = [
  { key: "daily-drawdown", label: "Daily drawdown" },
  { key: "concentration", label: "Concentration" },
  { key: "sell-all", label: "Sell-all" },
  { key: "consecutive-losses", label: "Consecutive losses" },
];

/** Debug/demo only, same as the routes it calls -- never part of the
 * agent's own decision loop. Lets a demo trip any of the four risk
 * triggers on cue instead of hoping the agent proposes a risky trade
 * naturally on camera. See mcp-server/app/server.py's own module docstring. */
export default function ForceTriggerControls() {
  const [pending, setPending] = useState(null);
  const [result, setResult] = useState(null);
  const { mutate } = useSWRConfig();

  async function trigger(key) {
    setPending(key);
    setResult(null);
    try {
      const data = await forceTrigger(key);
      setResult({ key, ok: true, note: data.note });
      await mutate((swrKey) => typeof swrKey === "string" && swrKey.startsWith("/api/wallet/"));
    } catch (err) {
      setResult({ key, ok: false, note: err.message });
    } finally {
      setPending(null);
    }
  }

  return (
    <Panel className="p-4">
      <p className="font-mono text-xs uppercase tracking-wideish text-ink-muted">Force a trigger — demo only</p>
      <p className="mt-2 text-xs text-ink-muted">
        Never called from the agent&rsquo;s own decision loop. Synthesizes a real breach so the panel above (and the
        next proposed trade) has a genuine computed number to show. Cleared by resetting the wallet.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {TRIGGERS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => trigger(t.key)}
            disabled={pending !== null}
            className="rounded border border-ink-line px-3 py-1.5 font-mono text-xs uppercase tracking-wideish text-ink-soft transition hover:border-signal-amber hover:text-signal-amber disabled:opacity-50"
          >
            {pending === t.key ? "Forcing…" : t.label}
          </button>
        ))}
      </div>
      {result ? (
        <p className={`mt-3 text-xs ${result.ok ? "text-signal-green" : "text-signal-red"}`}>
          {result.ok ? result.note : `Failed: ${result.note}`}
        </p>
      ) : null}
    </Panel>
  );
}
