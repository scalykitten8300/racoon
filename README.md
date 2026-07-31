# Racoon

This repository contains a small Pygame game where a tiny mushroom with a blonde bowl cut escapes a slice of orange cheese.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python mushroom_escape.py
```

Use the arrow keys to move the mushroom and avoid the cheese.

## Day-trading tool (`daytrader/`)

An educational, **simulated** market-analysis and day-trading tool. It is
not connected to any real bank or brokerage - no real account or real
money is ever involved. It provides:

- **Accounts with passwords**: local accounts secured with salted
  PBKDF2-HMAC-SHA256 password hashing (`daytrader/auth.py`).
- **Market analysis**: SMA/EMA/RSI technical indicators
  (`daytrader/indicators.py`) computed over historical price data.
- **Signal generation**: an SMA-crossover + RSI strategy that emits
  BUY/SELL signals (`daytrader/strategy.py`).
- **Paper-trading engine**: simulates trades against a per-user virtual
  cash balance and persists the resulting portfolio/trade history
  (`daytrader/engine.py`).
- **Data fallback**: tries to fetch real prices via `yfinance` if it's
  installed and reachable, and otherwise falls back to a deterministic
  synthetic price feed so the tool keeps working offline
  (`daytrader/market_data.py`).

### Usage

Create an account:

```bash
python daytrader_cli.py register --username maryse --password "change-me-please"
```

Log in and run a market-analysis / day-trading session on a symbol:

```bash
python daytrader_cli.py trade --username maryse --password "change-me-please" --symbol AAPL
```

Account and portfolio data is stored under `daytrader_data/` (ignored by
git). Use `--data-dir` to point at a different location.

## Tests

```bash
pytest
```
