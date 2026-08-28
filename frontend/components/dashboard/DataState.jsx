import { isWalletUnreachable } from "@/lib/api";

/** Wraps a panel's data-dependent content with the three states every
 * dashboard page needs to handle honestly: still loading, the wallet
 * server isn't running, or some other error. Written from the operator's
 * side of the screen -- what happened, and what to do about it. */
export default function DataState({ isLoading, error, children }) {
  if (isLoading) {
    return <p className="font-mono text-xs uppercase tracking-wideish text-paper-muted">Loading…</p>;
  }
  if (error) {
    if (isWalletUnreachable(error)) {
      return (
        <div className="rounded border border-signal-red-ink/30 bg-signal-red/10 px-4 py-3">
          <p className="text-sm text-signal-red-ink">Wallet server isn&rsquo;t reachable.</p>
          <p className="mt-1 text-xs text-paper-muted">
            Start it with <code className="text-paper-ink/80">cd mcp-server &amp;&amp; python -m app.server</code>{" "}
            and check <code className="text-paper-ink/80">WALLET_SERVER_URL</code>/
            <code className="text-paper-ink/80">WALLET_SHARED_SECRET</code> in the frontend&rsquo;s{" "}
            <code className="text-paper-ink/80">.env.local</code>.
          </p>
        </div>
      );
    }
    return (
      <div className="rounded border border-signal-red-ink/30 bg-signal-red/10 px-4 py-3">
        <p className="text-sm text-signal-red-ink">{error.message || "Something went wrong."}</p>
      </div>
    );
  }
  return children;
}
