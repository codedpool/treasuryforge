"""Wallet + market-data MCP server.

TrueForge only registers *remote* MCP servers (by URL), so this runs over
Streamable HTTP rather than the more common stdio transport -- see
https://trueforge.dev/mcp-servers for the registration side, and
scripts/setup_trueforge.py in the repo root for how this gets registered.

Tool surface:
  - get_portfolio, get_transaction_log, get_crypto_price, get_equity_price:
    read-only.
  - execute_trade: the only tool that writes wallet state. Register it with
    require_approval_for_tools on the TrueForge side so every trade pauses
    for a human checkpoint -- see setup_trueforge.py.

Debug-only routes (never on the live decision path -- see README):
  - POST /debug/reset: wipes and reseeds the wallet.
  - GET /health: liveness check.
"""

from fastapi import FastAPI
from fastmcp import FastMCP

from . import config, wallet
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
    Equity trades are rejected outright while the NSE is closed."""
    return wallet.execute_trade(
        asset=asset, side=side, quantity=quantity, usd_amount=usd_amount, reason=reason
    )


mcp_app = mcp.http_app(path="/")
api = FastAPI(lifespan=mcp_app.lifespan)
api.mount("/mcp", mcp_app)


@api.get("/health")
async def health():
    return {"status": "ok", "dry_run": config.DRY_RUN}


@api.post("/debug/reset")
async def debug_reset():
    """Demo/testing only -- wipes the wallet and reseeds it. Never called
    from the agent's own decision loop; see README for why this exists."""
    result = wallet.reset_wallet()
    return {"reset": True, "portfolio": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api, host="0.0.0.0", port=config.PORT)
