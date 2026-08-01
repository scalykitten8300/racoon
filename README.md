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
- **Real data, with fallback**: tries real prices first - `yfinance`
  for stocks/ETFs, then [CoinGecko](https://www.coingecko.com/) (no API
  key needed) for crypto (BTC, ETH, SOL, ...) - and only falls back to
  a deterministic synthetic feed if both are unreachable, so the tool
  keeps working offline (`daytrader/market_data.py`). Every result
  reports which source was actually used.
- **Live mode**: watch the bot poll fresh prices and print every
  BUY/SELL/HOLD decision as it happens (`daytrader/live.py`).

### Usage

Create an account:

```bash
python daytrader_cli.py register --username maryse --password "change-me-please" --balance 1000
```

Log in and run a one-shot market-analysis / backtest session on a symbol:

```bash
python daytrader_cli.py trade --username maryse --password "change-me-please" --symbol BTC
```

Log in and watch the bot trade **live**, tick by tick, until you stop it (Ctrl+C):

```bash
python daytrader_cli.py live --username maryse --password "change-me-please" --symbol BTC --interval 30
```

Add `--iterations N` to stop automatically after N checks instead of running
until interrupted.

Account and portfolio data is stored under `daytrader_data/` (ignored by
git). Use `--data-dir` to point at a different location.

## Tests

```bash
pytest
```
