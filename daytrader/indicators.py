"""Pure-Python technical indicators used for market analysis and signals."""
from __future__ import annotations


def sma(values: list[float], window: int) -> list[float | None]:
    """Simple moving average."""
    out: list[float | None] = [None] * len(values)
    for i in range(window - 1, len(values)):
        out[i] = sum(values[i - window + 1 : i + 1]) / window
    return out


def ema(values: list[float], window: int) -> list[float | None]:
    """Exponential moving average."""
    out: list[float | None] = [None] * len(values)
    if len(values) < window:
        return out
    k = 2 / (window + 1)
    seed = sum(values[:window]) / window
    out[window - 1] = seed
    prev = seed
    for i in range(window, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(values: list[float], window: int = 14) -> list[float | None]:
    """Relative Strength Index (Wilder's smoothing)."""
    out: list[float | None] = [None] * len(values)
    if len(values) <= window:
        return out

    gains, losses = [], []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains[:window]) / window
    avg_loss = sum(losses[:window]) / window
    out[window] = _rsi_from_avg(avg_gain, avg_loss)

    for i in range(window, len(gains)):
        avg_gain = (avg_gain * (window - 1) + gains[i]) / window
        avg_loss = (avg_loss * (window - 1) + losses[i]) / window
        out[i + 1] = _rsi_from_avg(avg_gain, avg_loss)

    return out


def _rsi_from_avg(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
