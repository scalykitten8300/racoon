"""Paper-trading engine: simulates day trades against a user's account.

This never touches real money or a real brokerage - it is an
educational simulation that persists per-user portfolio state to disk
so balances/trade history survive between runs.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .config import default_data_dir
from .market_data import fetch_history_with_source
from .strategy import Signal, SignalPoint, generate_signals


@dataclass
class Trade:
    index: int
    symbol: str
    side: str
    price: float
    quantity: float
    reason: str


@dataclass
class Portfolio:
    username: str
    cash: float
    shares: float = 0.0
    trades: list[dict] = field(default_factory=list)


class PaperTradingEngine:
    def __init__(
        self,
        username: str,
        starting_balance: float,
        data_dir: Path | str | None = None,
    ):
        self.username = username
        root = Path(data_dir) if data_dir is not None else default_data_dir()
        self.portfolio_dir = root / "portfolios"
        self.portfolio_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.portfolio_dir / f"{username}.json"
        self.portfolio = self._load(starting_balance)

    def _load(self, starting_balance: float) -> Portfolio:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            return Portfolio(**raw)
        return Portfolio(username=self.username, cash=starting_balance)

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(asdict(self.portfolio), fh, indent=2)

    def _execute(self, point: SignalPoint, symbol: str, risk_fraction: float) -> bool:
        """Fill a single signal against the portfolio. Returns True if a trade happened."""
        if point.signal is Signal.BUY and self.portfolio.shares == 0:
            spend = self.portfolio.cash * risk_fraction
            if spend < 1:
                return False
            qty = spend / point.price
            self.portfolio.cash -= qty * point.price
            self.portfolio.shares += qty
            self.portfolio.trades.append(
                asdict(Trade(point.index, symbol, "BUY", point.price, qty, point.reason))
            )
            return True
        if point.signal is Signal.SELL and self.portfolio.shares > 0:
            qty = self.portfolio.shares
            self.portfolio.cash += qty * point.price
            self.portfolio.shares = 0.0
            self.portfolio.trades.append(
                asdict(Trade(point.index, symbol, "SELL", point.price, qty, point.reason))
            )
            return True
        return False

    def run_session(self, symbol: str, risk_fraction: float = 0.5) -> dict:
        """Fetch a historical window, generate signals, and simulate BUY/SELL fills."""
        if not 0 < risk_fraction <= 1:
            raise ValueError("risk_fraction must be between 0 (exclusive) and 1 (inclusive).")

        candles, source = fetch_history_with_source(symbol)
        closes = [c.close for c in candles]
        signals = generate_signals(closes)

        for point in signals:
            self._execute(point, symbol, risk_fraction)

        last_price = closes[-1]
        equity = self.portfolio.cash + self.portfolio.shares * last_price
        self._save()

        return {
            "symbol": symbol,
            "data_source": source,
            "last_price": last_price,
            "cash": self.portfolio.cash,
            "shares": self.portfolio.shares,
            "equity": equity,
            "trades": self.portfolio.trades,
        }

    def evaluate_latest(self, symbol: str, closes: list[float], risk_fraction: float = 0.5) -> dict:
        """Evaluate only the newest price tick and act on it if it triggers a signal.

        Used by the live-trading loop: ``closes`` is a rolling window that
        grows one tick at a time, and only a signal at the very last index
        is actionable (older signals in the window were already handled on
        previous ticks).
        """
        if not 0 < risk_fraction <= 1:
            raise ValueError("risk_fraction must be between 0 (exclusive) and 1 (inclusive).")

        last_index = len(closes) - 1
        point = next((p for p in generate_signals(closes) if p.index == last_index), None)

        action = "HOLD"
        reason = None
        if point is not None and self._execute(point, symbol, risk_fraction):
            action = point.signal.value
            reason = point.reason

        price = closes[-1]
        equity = self.portfolio.cash + self.portfolio.shares * price
        self._save()

        return {
            "symbol": symbol,
            "price": price,
            "action": action,
            "reason": reason,
            "cash": self.portfolio.cash,
            "shares": self.portfolio.shares,
            "equity": equity,
        }
