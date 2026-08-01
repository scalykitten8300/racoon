"""Market data acquisition with graceful fallback to a synthetic feed.

Historical data is fetched from real providers, in order:

1. ``yfinance`` (stocks/ETFs) - only used if the package is installed
   and the provider is reachable.
2. CoinGecko's public REST API (crypto) - no API key required, uses
   only the standard library.

If both real sources are unavailable (offline sandbox, provider
outage/blocking, unknown symbol, ...) we fall back to a deterministic
synthetic random-walk feed so the rest of the tool (indicators,
signals, paper trading) keeps working end to end. Callers can check
``fetch_history_with_source`` to know whether a result is real market
data or the synthetic fallback.
"""
from __future__ import annotations

import json
import math
import random
import urllib.error
import urllib.request
from dataclasses import dataclass

# Common crypto tickers -> CoinGecko coin ids. CoinGecko is used because,
# unlike most stock-data providers, its public API works without an API
# key and isn't blocked by bot-protection on typical sandboxed networks.
_COINGECKO_IDS = {
    "BTC": "bitcoin", "BTC-USD": "bitcoin", "XBT": "bitcoin",
    "ETH": "ethereum", "ETH-USD": "ethereum",
    "SOL": "solana", "SOL-USD": "solana",
    "DOGE": "dogecoin", "DOGE-USD": "dogecoin",
    "ADA": "cardano", "ADA-USD": "cardano",
    "XRP": "ripple", "XRP-USD": "ripple",
    "BNB": "binancecoin", "BNB-USD": "binancecoin",
    "LTC": "litecoin", "LTC-USD": "litecoin",
    "MATIC": "matic-network", "MATIC-USD": "matic-network",
    "DOT": "polkadot", "DOT-USD": "polkadot",
    "AVAX": "avalanche-2", "AVAX-USD": "avalanche-2",
    "LINK": "chainlink", "LINK-USD": "chainlink",
}


@dataclass
class Candle:
    index: int
    close: float


def fetch_history(symbol: str, periods: int = 200) -> list[Candle]:
    candles, _source = fetch_history_with_source(symbol, periods)
    return candles


def fetch_history_with_source(symbol: str, periods: int = 200) -> tuple[list[Candle], str]:
    """Return (candles, source) where source is 'yfinance', 'coingecko', or 'synthetic'."""
    try:
        candles = _fetch_stock_history(symbol, periods)
        if len(candles) >= 30:
            return candles, "yfinance"
    except Exception:
        pass

    try:
        candles = _fetch_crypto_history(symbol, periods)
        if len(candles) >= 30:
            return candles, "coingecko"
    except Exception:
        pass

    return _synthetic_history(symbol, periods), "synthetic"


def fetch_intraday_history_with_source(symbol: str, periods: int = 200) -> tuple[list[Candle], str]:
    """Like ``fetch_history_with_source`` but on an intraday timescale.

    The live loop appends price ticks seconds/minutes apart, so warming
    it up with daily candles would make the indicators compare a 45s
    move against a full trading day. This returns ~5-minute bars
    instead, which is the granularity live ticks actually extend.
    """
    try:
        candles = _fetch_stock_intraday(symbol, periods)
        if len(candles) >= 30:
            return candles, "yfinance"
    except Exception:
        pass

    try:
        candles = _fetch_crypto_intraday(symbol, periods)
        if len(candles) >= 30:
            return candles, "coingecko"
    except Exception:
        pass

    return _synthetic_history(symbol, periods), "synthetic"


def _fetch_stock_intraday(symbol: str, periods: int) -> list[Candle]:
    import yfinance as yf  # optional dependency, imported lazily

    data = yf.download(symbol, period="1d", interval="5m", progress=False)
    if data is None or data.empty:
        raise ValueError("no data returned")
    closes = data["Close"].tail(periods)
    return [Candle(index=i, close=float(v)) for i, v in enumerate(closes)]


def _fetch_crypto_intraday(symbol: str, periods: int) -> list[Candle]:
    coin_id = _COINGECKO_IDS.get(symbol.upper())
    if coin_id is None:
        raise ValueError(f"unknown crypto symbol: {symbol}")

    # days=1 is the only free-tier window that returns ~5-minute bars;
    # days>=2 downgrades to hourly and days>=90 to daily.
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        f"?vs_currency=usd&days=1"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "daytrader-tool/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.load(response)

    prices = payload.get("prices", [])
    if not prices:
        raise ValueError("no price data returned")
    closes = [p[1] for p in prices][-periods:]
    return [Candle(index=i, close=round(float(v), 2)) for i, v in enumerate(closes)]


def _fetch_stock_history(symbol: str, periods: int) -> list[Candle]:
    import yfinance as yf  # optional dependency, imported lazily

    data = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if data is None or data.empty:
        raise ValueError("no data returned")
    closes = data["Close"].tail(periods)
    return [Candle(index=i, close=float(v)) for i, v in enumerate(closes)]


def _fetch_crypto_history(symbol: str, periods: int) -> list[Candle]:
    coin_id = _COINGECKO_IDS.get(symbol.upper())
    if coin_id is None:
        raise ValueError(f"unknown crypto symbol: {symbol}")

    days = max(30, min(periods, 365))
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        f"?vs_currency=usd&days={days}&interval=daily"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "daytrader-tool/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.load(response)

    prices = payload.get("prices", [])
    if not prices:
        raise ValueError("no price data returned")
    closes = [p[1] for p in prices][-periods:]
    return [Candle(index=i, close=round(float(v), 2)) for i, v in enumerate(closes)]


def fetch_latest_price(symbol: str, last_price: float | None = None) -> tuple[float, str]:
    """Return (price, source) for the current/most-recent price of ``symbol``.

    Used by the live-trading loop to poll one fresh tick at a time,
    as opposed to ``fetch_history`` which pulls a whole historical
    window for backtesting.
    """
    try:
        return _fetch_stock_latest_price(symbol), "yfinance"
    except Exception:
        pass

    try:
        return _fetch_crypto_latest_price(symbol), "coingecko"
    except Exception:
        pass

    return _synthetic_latest_price(symbol, last_price), "synthetic"


def _fetch_stock_latest_price(symbol: str) -> float:
    import yfinance as yf  # optional dependency, imported lazily

    ticker = yf.Ticker(symbol)
    price = ticker.fast_info.get("last_price")
    if price is None:
        raise ValueError("no live price returned")
    return round(float(price), 2)


def _fetch_crypto_latest_price(symbol: str) -> float:
    coin_id = _COINGECKO_IDS.get(symbol.upper())
    if coin_id is None:
        raise ValueError(f"unknown crypto symbol: {symbol}")

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    request = urllib.request.Request(url, headers={"User-Agent": "daytrader-tool/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.load(response)

    price = payload.get(coin_id, {}).get("usd")
    if price is None:
        raise ValueError("no live price returned")
    return round(float(price), 2)


def _synthetic_latest_price(symbol: str, last_price: float | None) -> float:
    seed = sum(ord(c) for c in symbol.upper()) or 1
    base = last_price if last_price is not None else 50.0 + (seed % 150)
    shock = random.gauss(0, base * 0.003)
    return round(max(0.01, base + shock), 2)


def _synthetic_history(symbol: str, periods: int) -> list[Candle]:
    """Deterministic per-symbol synthetic random walk used as an offline fallback."""
    seed = sum(ord(c) for c in symbol.upper()) or 1
    rng = random.Random(seed)
    price = 50.0 + (seed % 150)
    candles = []
    for i in range(periods):
        drift = math.sin(i / 12.0) * 0.3
        shock = rng.gauss(0, 1.2)
        price = max(1.0, price + drift + shock)
        candles.append(Candle(index=i, close=round(price, 2)))
    return candles
