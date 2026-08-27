from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from . import config

NSE_TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

_IST = ZoneInfo("Asia/Kolkata")
_YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
_YAHOO_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TreasuryForge/0.1)"}
_TWELVEDATA_URL = "https://api.twelvedata.com/quote"


def market_open(now: datetime | None = None) -> bool:
    """NSE regular trading hours: 09:15-15:30 IST, Monday-Friday.

    Deliberately ignores exchange holidays / circuit-breaker halts (out of
    scope) -- this is a weekday-and-clock-time check only, computed
    independently of whatever a quote source's own market-state field says,
    so it stays deterministic and testable offline.
    """
    now = (now or datetime.now(_IST)).astimezone(_IST)
    if now.weekday() >= 5:  # Sat=5, Sun=6
        return False
    open_t = now.replace(hour=9, minute=15, second=0, microsecond=0)
    close_t = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return open_t <= now <= close_t


def _from_yahoo(symbol: str) -> dict:
    resp = httpx.get(
        _YAHOO_URL.format(symbol=symbol),
        headers=_YAHOO_HEADERS,
        timeout=10.0,
    )
    resp.raise_for_status()
    payload = resp.json()
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        error = (payload.get("chart") or {}).get("error")
        raise RuntimeError(f"Yahoo returned no data for {symbol}: {error}")

    meta = result[0]["meta"]
    price_inr = meta["regularMarketPrice"]
    prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
    change_pct = None
    if prev_close:
        change_pct = (price_inr - prev_close) / prev_close * 100

    return {"price_inr": price_inr, "change_24h_pct": change_pct, "source": "yahoo"}


def _from_twelvedata(symbol: str) -> dict:
    if not config.TWELVEDATA_API_KEY:
        raise RuntimeError("Twelve Data fallback not configured (TWELVEDATA_API_KEY unset)")

    bare_symbol = symbol.removesuffix(".NS").removesuffix(".BO")
    resp = httpx.get(
        _TWELVEDATA_URL,
        params={
            "symbol": bare_symbol,
            "exchange": "NSE",
            "apikey": config.TWELVEDATA_API_KEY,
        },
        timeout=10.0,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") == "error" or "close" not in payload:
        raise RuntimeError(f"Twelve Data returned no data for {symbol}: {payload}")

    price_inr = float(payload["close"])
    prev_close = payload.get("previous_close")
    change_pct = None
    if prev_close:
        change_pct = (price_inr - float(prev_close)) / float(prev_close) * 100

    return {"price_inr": price_inr, "change_24h_pct": change_pct, "source": "twelvedata"}


def get_equity_price(symbol: str) -> dict:
    """Current price (INR from the exchange, USD for internal tracking) and
    24h % change for an NSE equity symbol, e.g. RELIANCE.NS.

    USD is the notional unit everything else in the wallet is tracked in;
    the INR figure is carried along for display only, converted at the fixed
    FX_INR_PER_USD constant (FX risk is explicitly out of scope -- see README).
    """
    symbol = symbol.upper()
    if symbol not in NSE_TICKERS:
        raise ValueError(f"Unsupported equity symbol: {symbol}. Supported: {NSE_TICKERS}")

    try:
        quote = _from_yahoo(symbol)
    except Exception:
        quote = _from_twelvedata(symbol)

    price_inr = quote["price_inr"]
    return {
        "symbol": symbol,
        "price_inr": price_inr,
        "price_usd": price_inr / config.FX_INR_PER_USD,
        "change_24h_pct": quote["change_24h_pct"],
        "market_open": market_open(),
        "source": quote["source"],
    }
