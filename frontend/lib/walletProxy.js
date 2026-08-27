import "server-only";

const WALLET_SERVER_URL = (process.env.WALLET_SERVER_URL || "http://127.0.0.1:4001").replace(/\/$/, "");
const WALLET_SHARED_SECRET = process.env.WALLET_SHARED_SECRET || "";

/**
 * Every Next.js route handler under app/api/wallet/** calls through here
 * instead of fetching the wallet server directly. WALLET_SHARED_SECRET is a
 * server-only env var (no NEXT_PUBLIC_ prefix) -- it never reaches the
 * browser bundle. The browser talks to our own /api/wallet/* routes, which
 * attach the secret on this end; see mcp-server's own README for why that
 * secret exists at all (it's what stops a local process from calling
 * execute_trade directly and skipping TrueForge's approval checkpoint).
 */
// A stalled-but-accepted upstream connection (as opposed to a refused one)
// would otherwise hang this fetch -- and the Next.js request/dashboard
// loading state along with it -- indefinitely (a real Qodo finding).
// proxyResponse.js's existing try/catch already turns any thrown fetch
// error, abort included, into a wallet_unreachable response; this is the
// only change needed to make that path actually reachable on a stall.
const WALLET_FETCH_TIMEOUT_MS = 10_000;

export async function walletFetch(path, init = {}) {
  return fetch(`${WALLET_SERVER_URL}${path}`, {
    ...init,
    headers: {
      ...(init.headers || {}),
      "X-Wallet-Secret": WALLET_SHARED_SECRET,
      ...(init.body ? { "Content-Type": "application/json" } : {}),
    },
    cache: "no-store",
    signal: init.signal ?? AbortSignal.timeout(WALLET_FETCH_TIMEOUT_MS),
  });
}
