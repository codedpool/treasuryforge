import threading
import time

import httpx

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}

_COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

# CoinGecko's free tier rate-limits aggressively (429s well within normal use),
# and a single dashboard page load fans out to several server-side calls that
# each independently re-price the same two assets -- get_portfolio,
# check_risk_limits, get_wallet_metrics, and get_equity_curve all call
# get_portfolio, which calls this. A short per-asset cache turns that fan-out
# back into effectively one real upstream call per TTL window; 30s is well
# under CoinGecko's own quote update cadence, so this doesn't misprice
# anything, and matches the other documented "honest simplifications" (see
# README's Design decisions) rather than pretending trades price off a
# millisecond-fresh feed the free tier can't actually sustain.
#
# The lock serializes the whole check-fetch-update sequence, not just the
# cache mutation: FastAPI runs these as sync routes in a thread pool, and
# the dashboard's portfolio/metrics/risk/equity-curve requests land within
# milliseconds of each other, all wanting the same two ids. Without it,
# they'd all see the same expired entries and all fire a duplicate CoinGecko
# request before any of them finished populating the cache -- exactly the
# burst this cache exists to prevent. With it, the first caller through a
# cold/expired window does the one real fetch; everyone else blocks briefly
# and then reads what it just cached, with no network call of their own.
_CACHE_TTL_SECONDS = 30.0
_cache: dict[str, tuple[float, dict]] = {}
_lock = threading.Lock()


def _fetch(ids: list[str]) -> dict[str, dict]:
    with _lock:
        now = time.monotonic()
        stale = [i for i in ids if i not in _cache or now - _cache[i][0] > _CACHE_TTL_SECONDS]

        if stale:
            resp = httpx.get(
                _COINGECKO_URL,
                params={"ids": ",".join(stale), "vs_currencies": "usd", "include_24hr_change": "true"},
                timeout=10.0,
            )
            resp.raise_for_status()
            payload = resp.json()
            now = time.monotonic()
            for coingecko_id in stale:
                data = payload.get(coingecko_id)
                if data:
                    _cache[coingecko_id] = (now, data)
                else:
                    # CoinGecko's response didn't include this id -- drop the
                    # old (now-expired) entry instead of continuing to serve
                    # it indefinitely. Callers below treat a missing id as
                    # "price unavailable", same as before this cache existed.
                    _cache.pop(coingecko_id, None)

        return {i: _cache[i][1] for i in ids if i in _cache}


def get_crypto_price(symbol: str) -> dict:
    """Current USD price and 24h % change for a crypto symbol (BTC, ETH)."""
    symbol = symbol.upper()
    coingecko_id = COINGECKO_IDS.get(symbol)
    if coingecko_id is None:
        raise ValueError(f"Unsupported crypto symbol: {symbol}. Supported: {list(COINGECKO_IDS)}")

    data = _fetch([coingecko_id]).get(coingecko_id)
    if not data:
        raise RuntimeError(f"CoinGecko returned no data for {symbol}")

    return {
        "symbol": symbol,
        "price_usd": data["usd"],
        "change_24h_pct": data.get("usd_24h_change"),
        "source": "coingecko",
    }


def get_crypto_prices(symbols: list[str]) -> dict[str, dict]:
    """Batch version of get_crypto_price -- one CoinGecko call for all symbols."""
    symbols = [s.upper() for s in symbols]
    ids = [COINGECKO_IDS[s] for s in symbols if s in COINGECKO_IDS]
    if not ids:
        return {}

    fetched = _fetch(ids)

    out = {}
    for symbol in symbols:
        coingecko_id = COINGECKO_IDS.get(symbol)
        data = fetched.get(coingecko_id) if coingecko_id else None
        if not data:
            continue
        out[symbol] = {
            "symbol": symbol,
            "price_usd": data["usd"],
            "change_24h_pct": data.get("usd_24h_change"),
            "source": "coingecko",
        }
    return out
