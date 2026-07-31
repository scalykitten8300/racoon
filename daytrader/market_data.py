"""Market data acquisition with graceful fallback to a synthetic feed.

Real-time/historical data is fetched via yfinance when it is installed
and network access is available. When either is missing (offline
sandbox, no dependency, provider outage, unknown ticker, ...) we fall
back to a deterministic synthetic random-walk feed so the rest of the
tool (indicators, signals, paper trading) keeps working end to end.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Candle:
    index: int
    close: float


def fetch_history(symbol: str, periods: int = 200) -> list[Candle]:
    try:
        candles = _fetch_real_history(symbol, periods)
        if len(candles) < 30:
            raise ValueError("not enough real data returned")
        return candles
    except Exception:
        return _synthetic_history(symbol, periods)


def _fetch_real_history(symbol: str, periods: int) -> list[Candle]:
    import yfinance as yf  # optional dependency, imported lazily

    data = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if data is None or data.empty:
        raise ValueError("no data returned")
    closes = data["Close"].tail(periods)
    return [Candle(index=i, close=float(v)) for i, v in enumerate(closes)]


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
