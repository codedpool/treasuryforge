"""Deterministic seed state for the paper wallet.

The plan this was built from originally specified a literal fixed seed
($10,000 cash, 0.5 BTC, 2 ETH, a few equity shares). That produces a wildly
unbalanced day-0 portfolio: 0.5 BTC alone is worth several times $10,000 at
any realistic BTC price, so crypto would dominate 80%+ of the portfolio from
the first run, permanently tripping the plan's own ">50% single-asset
allocation" approval trigger and making the equity slice a rounding error --
directly undercutting the "multi-asset treasury" framing this project is
built around.

Fixed here by seeding from USD target *weights* instead of fixed quantities:
quantities are computed from live prices at first-run, so the seed lands at
a genuinely diversified allocation regardless of what BTC/ETH/equities are
trading at when someone runs this.
"""

from datetime import datetime, timezone

from . import db
from .pricing_crypto import get_crypto_prices
from .pricing_equity import NSE_TICKERS, get_equity_price

TOTAL_USD = 10_000.0

TARGET_ALLOCATION_USD = {
    "cash": 5_000.0,   # 50%
    "crypto": 3_000.0,  # 30%
    "equity": 2_000.0,  # 20%
}
assert sum(TARGET_ALLOCATION_USD.values()) == TOTAL_USD

CRYPTO_SPLIT = {"BTC": 0.6, "ETH": 0.4}  # of the crypto bucket, by USD value


def is_initialized() -> bool:
    return db.get_meta("initialized") == "true"


def seed_wallet() -> None:
    """Populate a fresh wallet from live prices. No-op if already seeded."""
    if is_initialized():
        return

    conn = db.get_conn()
    now = datetime.now(timezone.utc).isoformat()

    def insert_holding(asset: str, quantity: float) -> None:
        conn.execute(
            "INSERT INTO holdings (asset, quantity) VALUES (?, ?) "
            "ON CONFLICT(asset) DO UPDATE SET quantity = excluded.quantity",
            (asset, quantity),
        )

    # Cash
    insert_holding("CASH", TARGET_ALLOCATION_USD["cash"])
    conn.execute(
        "INSERT INTO transactions (timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run) "
        "VALUES (?, 'CASH', 'seed', ?, 1.0, ?, 'initial seed allocation', 0)",
        (now, TARGET_ALLOCATION_USD["cash"], TARGET_ALLOCATION_USD["cash"]),
    )

    # Crypto
    crypto_prices = get_crypto_prices(list(CRYPTO_SPLIT))
    for symbol, weight in CRYPTO_SPLIT.items():
        usd_target = TARGET_ALLOCATION_USD["crypto"] * weight
        price_usd = crypto_prices[symbol]["price_usd"]
        quantity = usd_target / price_usd
        insert_holding(symbol, quantity)
        conn.execute(
            "INSERT INTO transactions (timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run) "
            "VALUES (?, ?, 'seed', ?, ?, ?, 'initial seed allocation', 0)",
            (now, symbol, quantity, price_usd, usd_target),
        )

    # Equities: equal split across the fixed universe
    equity_usd_each = TARGET_ALLOCATION_USD["equity"] / len(NSE_TICKERS)
    for symbol in NSE_TICKERS:
        quote = get_equity_price(symbol)
        price_usd = quote["price_usd"]
        quantity = equity_usd_each / price_usd
        insert_holding(symbol, quantity)
        conn.execute(
            "INSERT INTO transactions (timestamp, asset, side, quantity, price_usd, usd_value, reason, dry_run) "
            "VALUES (?, ?, 'seed', ?, ?, ?, 'initial seed allocation', 0)",
            (now, symbol, quantity, price_usd, equity_usd_each),
        )

    db.set_meta("initialized", "true")
    db.set_meta("seed_date", now)
    conn.commit()


def reset_and_reseed() -> None:
    db.reset_all()
    seed_wallet()
