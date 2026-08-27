import httpx

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}

_COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


def get_crypto_price(symbol: str) -> dict:
    """Current USD price and 24h % change for a crypto symbol (BTC, ETH)."""
    symbol = symbol.upper()
    coingecko_id = COINGECKO_IDS.get(symbol)
    if coingecko_id is None:
        raise ValueError(f"Unsupported crypto symbol: {symbol}. Supported: {list(COINGECKO_IDS)}")

    resp = httpx.get(
        _COINGECKO_URL,
        params={
            "ids": coingecko_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
        timeout=10.0,
    )
    resp.raise_for_status()
    data = resp.json().get(coingecko_id)
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

    resp = httpx.get(
        _COINGECKO_URL,
        params={
            "ids": ",".join(ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
        timeout=10.0,
    )
    resp.raise_for_status()
    payload = resp.json()

    out = {}
    for symbol in symbols:
        coingecko_id = COINGECKO_IDS.get(symbol)
        data = payload.get(coingecko_id) if coingecko_id else None
        if not data:
            continue
        out[symbol] = {
            "symbol": symbol,
            "price_usd": data["usd"],
            "change_24h_pct": data.get("usd_24h_change"),
            "source": "coingecko",
        }
    return out
