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
_CACHE_TTL_SECONDS = 30.0
_cache: dict[str, tuple[float, dict]] = {}


def _fetch(ids: list[str]) -> dict[str, dict]:
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
        for coingecko_id in stale:
            data = payload.get(coingecko_id)
            if data:
                _cache[coingecko_id] = (now, data)

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
