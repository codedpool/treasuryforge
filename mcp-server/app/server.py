"""Wallet + market-data MCP server.

TrueForge only registers *remote* MCP servers (by URL), so this runs over
Streamable HTTP rather than the more common stdio transport -- see
https://trueforge.dev/mcp-servers for the registration side, and
scripts/setup_trueforge.py in the repo root for how this gets registered.

Tool surface:
  - get_portfolio, get_transaction_log, get_crypto_price, get_equity_price,
    check_risk_limits, get_wallet_metrics: read-only.
  - execute_trade: the only tool that writes wallet state. Register it with
    require_approval_for_tools on the TrueForge side so every trade pauses
    for a human checkpoint -- see setup_trueforge.py. TrueForge's checkpoint
    is unconditional (every call pauses, it has no notion of "only if this
    breaches a limit" -- see risk.py's module docstring), so check_risk_limits
    is what turns the plan's four risk triggers into real computed numbers
    the agent must fetch and cite in `reason` before proposing a trade,
    rather than TrueForge enforcing them itself. execute_trade also computes
    its own check_risk_limits snapshot server-side and stores it with the
    transaction, regardless of whether the agent called it or what it
    passed in `reason` -- see execute_trade's docstring below.

Read-only UI routes (for the frontend dashboard, not the agent -- the
dashboard is a plain browser app and can't speak the MCP protocol the tools
above are exposed over, so these are the same underlying functions wrapped
as plain REST):
  - GET /ui/portfolio: wallet.get_portfolio().
  - GET /ui/transactions: wallet.get_transaction_log().
  - GET /ui/metrics: metrics.get_wallet_metrics().
  - GET /ui/risk-summary: risk.portfolio_risk_summary().
  - GET /ui/equity-curve: metrics.get_equity_curve() -- timestamped points
    for the dashboard's P&L chart (get_wallet_metrics only exposes a point
    *count*, not the series itself).

Debug-only routes (never on the live decision path -- see README):
  - POST /debug/reset: wipes and reseeds the wallet.
  - POST /debug/trigger-approval: synthesizes a daily-drawdown breach so a
    demo can reliably show the approval gate firing over a real computed
    number on cue. Never called from the agent's own decision loop.
  - POST /debug/trigger-approval/concentration: same, for the concentration
    trigger (see risk.force_concentration_breach).
  - POST /debug/trigger-approval/sell-all: same, for the sell_all trigger
    (see risk.force_sell_all_breach).
  - POST /debug/trigger-approval/consecutive-losses: same, for the
    consecutive_losses trigger (see risk.force_consecutive_losses_breach) --
    the only one of the four with no natural way to fire on demand at all
    under the default DRY_RUN=true.
  - GET /health: liveness check.

Every route except /health requires the X-Wallet-Secret header (see
config.WALLET_SHARED_SECRET) -- binding to localhost only stops remote
callers, not another local process calling execute_trade directly and
skipping TrueForge's approval checkpoint. TrueForge is configured to send
this automatically (header auth on the MCP server registration); see
scripts/setup_trueforge.py.

Every route on `api` below is a plain `def`, not `async def`, deliberately:
none of them ever `await` anything, and this process runs uvicorn's default
single-worker event loop, so an `async def` route that calls straight into
synchronous SQLite queries and synchronous live-price HTTP calls (as
wallet.get_portfolio() does) would block that one event loop -- and every
other concurrent request, including the agent's own MCP tool calls -- for
the duration (a real Qodo finding, most exposed by the dashboard's
every-15-seconds polling of these same routes). A plain `def` route makes
FastAPI run it in Starlette's threadpool instead, off the event loop.
"""

import hmac

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

from . import config, metrics, risk, wallet
from .pricing_crypto import get_crypto_price as _get_crypto_price
from .pricing_equity import get_equity_price as _get_equity_price

mcp = FastMCP("treasuryforge-wallet")


@mcp.tool
def get_portfolio() -> dict:
    """Current cash, every crypto/equity holding, live USD value of each,
    and total portfolio value. Auto-seeds the wallet on first call."""
    return wallet.get_portfolio()


@mcp.tool
def get_transaction_log(limit: int = 50) -> list[dict]:
    """Most recent wallet transactions (trades and the initial seed), newest first."""
    return wallet.get_transaction_log(limit=limit)


@mcp.tool
def get_crypto_price(symbol: str) -> dict:
    """Current USD price and 24h % change for a crypto symbol (BTC or ETH)."""
    return _get_crypto_price(symbol)


@mcp.tool
def get_equity_price(symbol: str) -> dict:
    """Current price (INR and converted USD), 24h % change, and market_open
    for an NSE equity symbol, e.g. RELIANCE.NS. market_open is false outside
    09:15-15:30 IST on weekdays -- do not propose new equity trades then."""
    return _get_equity_price(symbol)


@mcp.tool
def check_risk_limits(
    asset: str,
    side: str,
    quantity: float | None = None,
    usd_amount: float | None = None,
) -> dict:
    """Computed check of whether a proposed trade would breach a risk limit:
    daily drawdown > 5%, more than 2 consecutive losing trades, resulting
    single-asset allocation > 50%, or selling an entire position. Call this
    with the exact same arguments you're about to pass to execute_trade,
    before proposing it -- cite these numbers (not a guess) in execute_trade's
    reason. Read-only; does not affect approval routing (execute_trade always
    pauses for approval regardless of this result) but if any_breach is true
    you must run a sandbox cross-asset stress test first and cite its
    resulting drawdown number too."""
    return risk.check_risk_limits(asset=asset, side=side, quantity=quantity, usd_amount=usd_amount)


@mcp.tool
def get_wallet_metrics() -> dict:
    """Realized + unrealized P&L, win rate, max drawdown, and an
    unannualized Sharpe ratio, computed from actual transaction and equity
    history -- not your own estimate. Use this (not a guess) when reporting
    performance, e.g. in a self-audit summary."""
    return metrics.get_wallet_metrics()


@mcp.tool
def execute_trade(
    asset: str,
    side: str,
    quantity: float | None = None,
    usd_amount: float | None = None,
    reason: str = "",
) -> dict:
    """Buy or sell a crypto (BTC, ETH) or NSE equity position. The only tool
    that changes wallet state. Provide exactly one of quantity or usd_amount.
    When DRY_RUN is on, the trade is priced and logged but not executed.
    Equity trades are rejected outright while the NSE is closed.

    Computes and stores its own check_risk_limits snapshot for this exact
    trade before executing -- not the agent's job to remember to call it
    first (that's instruction-only, unenforced), and not trusted from the
    agent even if it did, since a tool argument can't be verified server-side.
    If the risk snapshot can't be computed (e.g. a quote is down), the trade
    is refused rather than executed without one -- see risk.py's
    _project_trade for why an unpriced position can't be silently ignored."""
    snapshot = risk.check_risk_limits(asset=asset, side=side, quantity=quantity, usd_amount=usd_amount)
    return wallet.execute_trade(
        asset=asset,
        side=side,
        quantity=quantity,
        usd_amount=usd_amount,
        reason=reason,
        risk_snapshot=snapshot,
        # Reuse the exact price check_risk_limits already fetched, rather than
        # letting execute_trade fetch its own -- otherwise a price move
        # between the two calls could make the stored risk_snapshot and the
        # executed trade disagree about what price the decision was based on.
        price_usd=snapshot["price_usd"],
    )


mcp_app = mcp.http_app(path="/")
api = FastAPI(lifespan=mcp_app.lifespan)
api.mount("/mcp", mcp_app)


@api.middleware("http")
async def require_shared_secret(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    provided = request.headers.get("x-wallet-secret", "")
    if not hmac.compare_digest(provided, config.WALLET_SHARED_SECRET):
        return JSONResponse({"error": "missing or invalid X-Wallet-Secret header"}, status_code=401)
    return await call_next(request)


@api.get("/health")
def health():
    return {"status": "ok", "dry_run": config.DRY_RUN}


@api.get("/ui/portfolio")
def ui_portfolio():
    return wallet.get_portfolio()


@api.get("/ui/transactions")
def ui_transactions(limit: int = 50):
    return wallet.get_transaction_log(limit=limit)


@api.get("/ui/metrics")
def ui_metrics():
    return metrics.get_wallet_metrics()


@api.get("/ui/risk-summary")
def ui_risk_summary():
    return risk.portfolio_risk_summary()


@api.get("/ui/equity-curve")
def ui_equity_curve(limit: int = 2000):
    return metrics.get_equity_curve(limit=limit)


@api.post("/debug/reset")
def debug_reset():
    """Demo/testing only -- wipes the wallet and reseeds it. Never called
    from the agent's own decision loop; see README for why this exists."""
    result = wallet.reset_wallet()
    return {"reset": True, "portfolio": result}


@api.post("/debug/trigger-approval")
def debug_trigger_approval():
    """Demo/testing only -- synthesizes a daily-drawdown breach (see
    risk.force_daily_drawdown_breach) so the agent's next check_risk_limits
    call reports a genuine breach, guaranteeing the approval gate has a real
    computed number to fire on for a demo. Never called from the agent's own
    decision loop; cleared by POST /debug/reset."""
    return risk.force_daily_drawdown_breach()


@api.post("/debug/trigger-approval/concentration")
def debug_trigger_approval_concentration(asset: str = "BTC", margin_pct: float = 1.0):
    """Demo/testing only -- see risk.force_concentration_breach. Never
    called from the agent's own decision loop; cleared by POST /debug/reset."""
    return risk.force_concentration_breach(asset=asset, margin_pct=margin_pct)


@api.post("/debug/trigger-approval/sell-all")
def debug_trigger_approval_sell_all(asset: str = "BTC", quantity: float = 0.05):
    """Demo/testing only -- see risk.force_sell_all_breach. Never called
    from the agent's own decision loop; cleared by POST /debug/reset."""
    return risk.force_sell_all_breach(asset=asset, quantity=quantity)


@api.post("/debug/trigger-approval/consecutive-losses")
def debug_trigger_approval_consecutive_losses(count: int | None = None):
    """Demo/testing only -- see risk.force_consecutive_losses_breach. Never
    called from the agent's own decision loop; cleared by POST /debug/reset."""
    return risk.force_consecutive_losses_breach(count=count)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api, host=config.HOST, port=config.PORT)
