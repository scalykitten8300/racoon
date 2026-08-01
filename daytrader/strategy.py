"""SMA-crossover + RSI signal strategy used to drive the paper-trading engine."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .indicators import rsi, sma


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class SignalPoint:
    index: int
    price: float
    signal: Signal
    reason: str


def generate_signals(
    closes: list[float],
    fast_window: int = 5,
    slow_window: int = 20,
    rsi_window: int = 14,
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0,
) -> list[SignalPoint]:
    """Combine an SMA crossover with RSI extremes into BUY/SELL signals."""
    fast = sma(closes, fast_window)
    slow = sma(closes, slow_window)
    strength = rsi(closes, rsi_window)

    points: list[SignalPoint] = []
    for i in range(1, len(closes)):
        if None in (fast[i], slow[i], fast[i - 1], slow[i - 1], strength[i]):
            continue

        crossed_up = fast[i - 1] <= slow[i - 1] and fast[i] > slow[i]
        crossed_down = fast[i - 1] >= slow[i - 1] and fast[i] < slow[i]

        if crossed_up and strength[i] < rsi_overbought:
            points.append(SignalPoint(
                i, closes[i], Signal.BUY,
                f"SMA{fast_window}/{slow_window} crossed up, RSI={strength[i]:.1f}",
            ))
        elif crossed_down and strength[i] > rsi_oversold:
            points.append(SignalPoint(
                i, closes[i], Signal.SELL,
                f"SMA{fast_window}/{slow_window} crossed down, RSI={strength[i]:.1f}",
            ))
        elif strength[i] < rsi_oversold:
            points.append(SignalPoint(i, closes[i], Signal.BUY, f"RSI oversold ({strength[i]:.1f})"))
        elif strength[i] > rsi_overbought:
            points.append(SignalPoint(i, closes[i], Signal.SELL, f"RSI overbought ({strength[i]:.1f})"))

    return points
