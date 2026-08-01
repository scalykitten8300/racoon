"""Live-trading loop: polls fresh price ticks and prints each action taken.

This is what powers ``daytrader_cli.py live`` - it lets you watch the bot
work in real time instead of only seeing a backtest summary at the end.
Still 100% paper trading: no real brokerage or real money is involved.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable

from .engine import PaperTradingEngine
from .market_data import fetch_history_with_source, fetch_latest_price

MAX_WINDOW = 300

_SOURCE_LABELS = {
    "yfinance": "real: Yahoo Finance",
    "coingecko": "real: CoinGecko",
    "synthetic": "synthetic fallback",
}


def run_live(
    engine: PaperTradingEngine,
    symbol: str,
    risk_fraction: float = 0.5,
    interval_seconds: float = 30.0,
    iterations: int | None = None,
    on_tick: Callable[[str], None] = print,
) -> None:
    candles, source = fetch_history_with_source(symbol)
    closes = [c.close for c in candles]
    on_tick(
        f"Warm-up: loaded {len(closes)} historical points for {symbol} "
        f"({_SOURCE_LABELS.get(source, source)})."
    )

    tick = 0
    try:
        while iterations is None or tick < iterations:
            tick += 1
            price, price_source = fetch_latest_price(symbol, last_price=closes[-1])
            closes.append(price)
            if len(closes) > MAX_WINDOW:
                closes = closes[-MAX_WINDOW:]

            result = engine.evaluate_latest(symbol, closes, risk_fraction=risk_fraction)
            on_tick(_format_tick(symbol, price, price_source, result))

            if iterations is None or tick < iterations:
                time.sleep(interval_seconds)
    except KeyboardInterrupt:
        on_tick("Stopped by user. Portfolio state saved.")


def _format_tick(symbol: str, price: float, price_source: str, result: dict) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = (
        f"[{timestamp}] {symbol} = ${price:,.2f} ({_SOURCE_LABELS.get(price_source, price_source)}) "
        f"-> {result['action']}"
    )
    if result.get("reason"):
        line += f" ({result['reason']})"
    line += f" | cash=${result['cash']:.2f} shares={result['shares']:.4f} equity=${result['equity']:.2f}"
    return line
