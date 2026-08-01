import subprocess
import sys

import pytest

from daytrader.auth import AccountManager, AuthError
from daytrader.engine import PaperTradingEngine
from daytrader.indicators import ema, rsi, sma
from daytrader.market_data import fetch_history
from daytrader.strategy import Signal, generate_signals
from daytrader import live as live_module


# --- auth -------------------------------------------------------------


def test_register_and_authenticate(tmp_path):
    manager = AccountManager(data_dir=tmp_path)
    manager.register("maryse", "correct-horse-battery")

    record = manager.authenticate("maryse", "correct-horse-battery")
    assert record.username == "maryse"
    assert record.starting_balance == 10_000.0


def test_register_rejects_short_password(tmp_path):
    manager = AccountManager(data_dir=tmp_path)
    with pytest.raises(AuthError):
        manager.register("maryse", "short")


def test_register_rejects_duplicate_username(tmp_path):
    manager = AccountManager(data_dir=tmp_path)
    manager.register("maryse", "correct-horse-battery")
    with pytest.raises(AuthError):
        manager.register("maryse", "another-password")


def test_authenticate_rejects_wrong_password(tmp_path):
    manager = AccountManager(data_dir=tmp_path)
    manager.register("maryse", "correct-horse-battery")
    with pytest.raises(AuthError):
        manager.authenticate("maryse", "wrong-password")


def test_password_never_stored_in_plaintext(tmp_path):
    manager = AccountManager(data_dir=tmp_path)
    manager.register("maryse", "correct-horse-battery")
    raw = (tmp_path / "users.json").read_text()
    assert "correct-horse-battery" not in raw


def test_credentials_persist_across_manager_instances(tmp_path):
    AccountManager(data_dir=tmp_path).register("maryse", "correct-horse-battery")
    reloaded = AccountManager(data_dir=tmp_path)
    reloaded.authenticate("maryse", "correct-horse-battery")


# --- indicators ---------------------------------------------------------


def test_sma_basic():
    values = [1, 2, 3, 4, 5]
    result = sma(values, window=2)
    assert result[0] is None
    assert result[1] == 1.5
    assert result[4] == 4.5


def test_ema_matches_length():
    values = [float(i) for i in range(30)]
    result = ema(values, window=5)
    assert len(result) == len(values)
    assert result[4] is not None


def test_rsi_bounds():
    values = [50 + (i % 3) - 1 for i in range(50)]
    result = rsi(values, window=14)
    for v in result:
        if v is not None:
            assert 0 <= v <= 100


# --- market data ----------------------------------------------------------


def test_fetch_history_returns_requested_periods():
    candles = fetch_history("FAKE_SYMBOL_XYZ", periods=100)
    assert len(candles) == 100
    assert all(c.close > 0 for c in candles)


def test_fetch_history_is_deterministic_for_same_symbol():
    a = fetch_history("AAPL", periods=50)
    b = fetch_history("AAPL", periods=50)
    assert [c.close for c in a] == [c.close for c in b]


# --- strategy ---------------------------------------------------------------


def test_generate_signals_only_emits_buy_or_sell():
    candles = fetch_history("MSFT", periods=200)
    closes = [c.close for c in candles]
    signals = generate_signals(closes)
    assert all(s.signal in (Signal.BUY, Signal.SELL) for s in signals)


# --- engine -------------------------------------------------------------


def test_run_session_updates_equity_and_persists(tmp_path):
    engine = PaperTradingEngine("maryse", starting_balance=10_000.0, data_dir=tmp_path)
    result = engine.run_session("AAPL", risk_fraction=0.5)

    assert result["equity"] > 0
    assert (tmp_path / "portfolios" / "maryse.json").exists()


def test_run_session_rejects_bad_risk_fraction(tmp_path):
    engine = PaperTradingEngine("maryse", starting_balance=10_000.0, data_dir=tmp_path)
    with pytest.raises(ValueError):
        engine.run_session("AAPL", risk_fraction=1.5)


def test_evaluate_latest_only_acts_on_last_index(tmp_path):
    engine = PaperTradingEngine("maryse", starting_balance=1000.0, data_dir=tmp_path)
    # A rising-then-dipping series so a BUY signal can land on the final tick.
    closes = [100.0] * 20 + [95, 93, 91, 89, 87, 90, 94, 99, 105, 111]
    result = engine.evaluate_latest("FAKE", closes, risk_fraction=0.5)

    assert result["price"] == closes[-1]
    assert result["action"] in ("BUY", "SELL", "HOLD")
    assert result["equity"] > 0


def test_evaluate_latest_holds_without_a_signal(tmp_path):
    engine = PaperTradingEngine("maryse", starting_balance=1000.0, data_dir=tmp_path)
    flat = [100.0] * 25
    result = engine.evaluate_latest("FAKE", flat, risk_fraction=0.5)

    assert result["action"] == "HOLD"
    assert result["cash"] == 1000.0
    assert result["shares"] == 0.0


# --- live loop ------------------------------------------------------------


def test_run_live_emits_one_line_per_tick(tmp_path, monkeypatch):
    from daytrader.market_data import Candle

    history = [Candle(index=i, close=100.0 + i * 0.1) for i in range(40)]
    prices = iter([100.5, 101.0, 99.5])

    monkeypatch.setattr(live_module, "fetch_history_with_source", lambda symbol: (history, "coingecko"))
    monkeypatch.setattr(live_module, "fetch_latest_price", lambda symbol, last_price=None: (next(prices), "coingecko"))

    engine = PaperTradingEngine("maryse", starting_balance=1000.0, data_dir=tmp_path)
    lines = []
    live_module.run_live(
        engine, "FAKE", risk_fraction=0.5, interval_seconds=0, iterations=3, on_tick=lines.append,
    )

    assert len(lines) == 4  # warm-up line + 3 ticks
    assert "Warm-up" in lines[0]
    for line in lines[1:]:
        assert "->" in line
        assert "equity=" in line


# --- CLI end-to-end -------------------------------------------------------


def test_cli_register_then_trade(tmp_path):
    data_dir = tmp_path / "data"
    register = subprocess.run(
        [
            sys.executable, "daytrader_cli.py",
            "--data-dir", str(data_dir),
            "register", "--username", "maryse", "--password", "correct-horse-battery",
        ],
        capture_output=True, text=True, check=True,
    )
    assert "Account 'maryse' created" in register.stdout

    trade = subprocess.run(
        [
            sys.executable, "daytrader_cli.py",
            "--data-dir", str(data_dir),
            "trade", "--username", "maryse", "--password", "correct-horse-battery", "--symbol", "AAPL",
        ],
        capture_output=True, text=True, check=True,
    )
    assert "Equity" in trade.stdout
