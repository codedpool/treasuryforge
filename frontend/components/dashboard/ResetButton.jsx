"use client";

import { useState } from "react";
import { useSWRConfig } from "swr";
import { resetWallet } from "@/lib/api";

export default function ResetButton() {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const { mutate } = useSWRConfig();

  async function handleReset() {
    setBusy(true);
    setError(null);
    try {
      await resetWallet();
      await mutate((key) => typeof key === "string" && key.startsWith("/api/wallet/"));
      setOpen(false);
    } catch (err) {
      setError(err.message || "Reset failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded border border-ink-line px-3 py-1.5 font-mono text-xs uppercase tracking-wideish text-ink-muted transition hover:border-signal-red hover:text-signal-red"
      >
        Reset wallet
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="reset-title"
        >
          <div className="grain-ink relative w-full max-w-sm overflow-hidden rounded-lg border border-signal-red-soft bg-ink-raised p-6">
            <div className="relative z-10">
              <h2 id="reset-title" className="font-display text-xl text-ink-bright">
                Reset the wallet?
              </h2>
              <p className="mt-3 text-sm text-ink-soft">
                Wipes every holding, transaction, and equity snapshot, then
                reseeds from the standard $10,000 target allocation. This
                cannot be undone.
              </p>
              {error ? <p className="mt-3 text-sm text-signal-red">{error}</p> : null}
              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  disabled={busy}
                  className="rounded px-3 py-2 font-mono text-xs uppercase tracking-wideish text-ink-muted hover:text-ink-bright"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  disabled={busy}
                  className="rounded bg-signal-red px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wideish text-ink-bright transition hover:brightness-110 disabled:opacity-60"
                >
                  {busy ? "Resetting…" : "Reset wallet"}
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
