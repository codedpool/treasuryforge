"""Shared pytest fixtures.

Every test runs against an isolated, throwaway SQLite database (never the
real dev wallet.db) and mocked price functions (never real network calls
to CoinGecko/Yahoo/Twelve Data) -- deterministic, fast, and safe to run in
CI without hitting the same rate limits this project ran into during
development (see difficulties.md, not part of this repo).
"""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db, wallet  # noqa: E402

BTC_PRICE = 80_000.0
ETH_PRICE = 4_000.0
EQUITY_PRICE_INR = {
    "RELIANCE.NS": 2_500.0,
    "TCS.NS": 3_500.0,
    "INFY.NS": 1_500.0,
    "HDFCBANK.NS": 1_600.0,
}
FX_INR_PER_USD = 83.0


def _crypto_price(symbol: str) -> dict:
    price = {"BTC": BTC_PRICE, "ETH": ETH_PRICE}[symbol.upper()]
    return {"symbol": symbol.upper(), "price_usd": price, "change_24h_pct": 0.0, "source": "mock"}


def _crypto_prices(symbols: list[str]) -> dict[str, dict]:
    return {s.upper(): _crypto_price(s) for s in symbols}


def _equity_price(symbol: str, *, open_market: bool = True) -> dict:
    price_inr = EQUITY_PRICE_INR[symbol.upper()]
    return {
        "symbol": symbol.upper(),
        "price_inr": price_inr,
        "price_usd": price_inr / FX_INR_PER_USD,
        "change_24h_pct": 0.0,
        "market_open": open_market,
        "source": "mock",
    }


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """A fresh, schema-initialized SQLite database for one test, with
    db.get_conn patched to always return it -- never touches the real
    wallet.db or any other test's state."""
    db_path = tmp_path / "test_wallet.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(db.SCHEMA)
    conn.commit()
    db._run_migrations(conn)

    monkeypatch.setattr(db, "get_conn", lambda: conn)
    yield conn
    conn.close()


@pytest.fixture
def mock_prices(monkeypatch):
    """Deterministic prices for every tradable asset, no network calls.
    Patches the names as imported into wallet.py/seed.py, not the
    pricing_* modules themselves -- `from .pricing_crypto import
    get_crypto_price` binds the name into each importing module's own
    namespace, so that's what has to be patched for callers to see it."""
    from app import seed

    monkeypatch.setattr(wallet, "get_crypto_price", _crypto_price)
    monkeypatch.setattr(wallet, "get_crypto_prices", _crypto_prices)
    monkeypatch.setattr(wallet, "get_equity_price", _equity_price)
    monkeypatch.setattr(wallet, "market_open", lambda: True)
    monkeypatch.setattr(seed, "get_crypto_prices", _crypto_prices)
    monkeypatch.setattr(seed, "get_equity_price", _equity_price)


@pytest.fixture
def seeded_wallet(isolated_db, mock_prices):
    """A freshly seeded wallet (cash/BTC/ETH/equities at the standard
    target allocation) ready for a test to trade against."""
    wallet._ensure_seeded()
    return isolated_db
