"""The paper wallet. This module is the only place that mutates wallet
state -- every other module (pricing, seed) only reads or is read from here.
"""

import math
import threading
from datetime import datetime, timezone

from . import config, db, seed
from .pricing_crypto import get_crypto_price, get_crypto_prices
from .pricing_equity import NSE_TICKERS, get_equity_price, market_open

CRYPTO_ASSETS = ["BTC", "ETH"]
TRADABLE_ASSETS = CRYPTO_ASSETS + NSE_TICKERS

# Serializes the read-balances -> compute -> write sequence in execute_trade.
# Each thread has its own sqlite connection (see db.py), so without this,
# two overlapping trades could both read the same starting balance and one
# write could clobber the other.
_trade_lock = threading.Lock()


def _ensure_seeded() -> None:
    if not seed.is_initialized():
        seed.seed_wallet()


def _price_usd(asset: str) -> dict:
    if asset in CRYPTO_ASSETS:
        return get_crypto_price(asset)
    if asset in NSE_TICKERS:
        return get_equity_price(asset)
    raise ValueError(f"Unknown tradable asset: {asset}")


def get_portfolio() -> dict:
    """Cash, every holding, current USD value of each, and portfolio total."""
    _ensure_seeded()
    conn = db.get_conn()
    rows = conn.execute("SELECT asset, quantity FROM holdings").fetchall()
    holdings_by_asset = {r["asset"]: r["quantity"] for r in rows}

    cash = holdings_by_asset.pop("CASH", 0.0)
    crypto_prices = get_crypto_prices(CRYPTO_ASSETS)

    positions = []
    total_usd = cash

    for asset in CRYPTO_ASSETS:
        quantity = holdings_by_asset.get(asset, 0.0)
        price = crypto_prices.get(asset, {}).get("price_usd")
        usd_value = quantity * price if price is not None else None
        if usd_value is not None:
            total_usd += usd_value
        positions.append({
            "asset": asset,
            "asset_class": "crypto",
            "quantity": quantity,
            "price_usd": price,
            "usd_value": usd_value,
            "change_24h_pct": crypto_prices.get(asset, {}).get("change_24h_pct"),
        })

    for asset in NSE_TICKERS:
        quantity = holdings_by_asset.get(asset, 0.0)
        try:
            quote = get_equity_price(asset)
        except Exception as exc:  # quote source down -- don't fail the whole portfolio
            positions.append({
                "asset": asset,
                "asset_class": "equity",
                "quantity": quantity,
                "price_usd": None,
                "usd_value": None,
                "change_24h_pct": None,
                "market_open": None,
                "error": str(exc),
            })
            continue
        usd_value = quantity * quote["price_usd"]
        total_usd += usd_value
        positions.append({
            "asset": asset,
            "asset_class": "equity",
            "quantity": quantity,
            "price_usd": quote["price_usd"],
            "price_inr": quote["price_inr"],
            "usd_value": usd_value,
            "change_24h_pct": quote["change_24h_pct"],
            "market_open": quote["market_open"],
        })

    return {
        "cash_usd": cash,
        "positions": positions,
        "total_usd": total_usd,
        "dry_run": config.DRY_RUN,
    }


def get_transaction_log(limit: int = 50) -> list[dict]:
    _ensure_seeded()
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT id, timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run "
        "FROM transactions ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def execute_trade(
    asset: str,
    side: str,
    quantity: float | None = None,
    usd_amount: float | None = None,
    reason: str = "",
) -> dict:
    """The only tool that changes wallet state.

    Exactly one of quantity / usd_amount must be given. When DRY_RUN is on
    (the default), the trade is priced and logged with dry_run=1 but cash
    and holdings are left untouched.
    """
    _ensure_seeded()

    asset = asset.upper()
    side = side.lower()
    if asset not in TRADABLE_ASSETS:
        raise ValueError(f"Unknown tradable asset: {asset}. Supported: {TRADABLE_ASSETS}")
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
    if (quantity is None) == (usd_amount is None):
        raise ValueError("Provide exactly one of quantity or usd_amount")

    amount: float = quantity if quantity is not None else usd_amount  # type: ignore[assignment]
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError(f"quantity/usd_amount must be a finite positive number, got {amount}")

    if asset in NSE_TICKERS and not market_open():
        raise ValueError(
            f"NSE is closed (09:15-15:30 IST, weekdays). Cannot trade {asset} right now -- "
            "hold or monitor the existing position instead."
        )

    quote = _price_usd(asset)
    price_usd = float(quote["price_usd"])

    if quantity is None:
        assert usd_amount is not None
        quantity = usd_amount / price_usd
    quantity = float(quantity)
    usd_value = quantity * price_usd

    conn = db.get_conn()
    now = datetime.now(timezone.utc).isoformat()

    if config.DRY_RUN:
        conn.execute(
            "INSERT INTO transactions (timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
            (now, asset, side, quantity, price_usd, usd_value, reason),
        )
        conn.commit()
        return {
            "dry_run": True,
            "executed": False,
            "asset": asset,
            "side": side,
            "quantity": quantity,
            "price_usd": price_usd,
            "usd_value": usd_value,
            "reason": reason,
            "message": "DRY_RUN is on: this trade was priced and logged but not executed.",
        }

    with _trade_lock:
        cash_row = conn.execute("SELECT quantity FROM holdings WHERE asset = 'CASH'").fetchone()
        cash = cash_row["quantity"] if cash_row else 0.0
        holding_row = conn.execute("SELECT quantity FROM holdings WHERE asset = ?", (asset,)).fetchone()
        holding_qty = holding_row["quantity"] if holding_row else 0.0

        if side == "buy":
            if usd_value > cash + 1e-9:
                raise ValueError(f"Insufficient cash: need ${usd_value:.2f}, have ${cash:.2f}")
            new_cash = cash - usd_value
            new_holding = holding_qty + quantity
        else:
            if quantity > holding_qty + 1e-9:
                raise ValueError(f"Insufficient {asset}: trying to sell {quantity}, hold {holding_qty}")
            new_cash = cash + usd_value
            new_holding = holding_qty - quantity

        conn.execute(
            "INSERT INTO holdings (asset, quantity) VALUES ('CASH', ?) "
            "ON CONFLICT(asset) DO UPDATE SET quantity = excluded.quantity",
            (new_cash,),
        )
        conn.execute(
            "INSERT INTO holdings (asset, quantity) VALUES (?, ?) "
            "ON CONFLICT(asset) DO UPDATE SET quantity = excluded.quantity",
            (asset, new_holding),
        )
        conn.execute(
            "INSERT INTO transactions (timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
            (now, asset, side, quantity, price_usd, usd_value, reason),
        )
        conn.commit()

    return {
        "dry_run": False,
        "executed": True,
        "asset": asset,
        "side": side,
        "quantity": quantity,
        "price_usd": price_usd,
        "usd_value": usd_value,
        "reason": reason,
        "cash_usd_after": new_cash,
        "holding_after": new_holding,
    }


def reset_wallet() -> dict:
    seed.reset_and_reseed()
    return get_portfolio()
