import subprocess
import sys

import pytest

from daytrader.auth import AccountManager, AuthError
from daytrader.engine import PaperTradingEngine
from daytrader.indicators import ema, rsi, sma
from daytrader.market_data import fetch_history
from daytrader.strategy import Signal, generate_signals


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
