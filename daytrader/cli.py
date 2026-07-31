"""Command-line front-end tying account auth to the paper-trading engine.

Examples
--------
Create an account with a password::

    python daytrader_cli.py register --username maryse --password "change-me-please"

Log in and run a market-analysis / day-trading session::

    python daytrader_cli.py trade --username maryse --password "change-me-please" --symbol AAPL
"""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from .auth import AccountManager, AuthError
from .engine import PaperTradingEngine


def _prompt_credentials(args: argparse.Namespace) -> tuple[str, str]:
    username = args.username or input("Username: ")
    password = args.password or getpass.getpass("Password: ")
    return username, password


def cmd_register(args: argparse.Namespace) -> int:
    manager = AccountManager(data_dir=args.data_dir)
    username, password = _prompt_credentials(args)
    try:
        manager.register(username, password, starting_balance=args.balance)
    except AuthError as exc:
        print(f"Registration failed: {exc}")
        return 1
    print(f"Account '{username}' created with a ${args.balance:,.2f} paper-trading balance.")
    print("(Simulated balance only - no real bank/brokerage account is created.)")
    return 0


def cmd_trade(args: argparse.Namespace) -> int:
    manager = AccountManager(data_dir=args.data_dir)
    username, password = _prompt_credentials(args)
    try:
        record = manager.authenticate(username, password)
    except AuthError as exc:
        print(f"Login failed: {exc}")
        return 1

    engine = PaperTradingEngine(username, record.starting_balance, data_dir=args.data_dir)
    result = engine.run_session(args.symbol, risk_fraction=args.risk)

    print(f"\nDay-trading session for {username} on {args.symbol}")
    print("=" * 60)
    recent_trades = result["trades"][-args.show_trades:] if args.show_trades else result["trades"]
    if not recent_trades:
        print("  No BUY/SELL signals triggered this session.")
    for trade in recent_trades:
        print(
            f"  [{trade['index']:>4}] {trade['side']:<4} {trade['quantity']:.4f} "
            f"@ ${trade['price']:.2f}  ({trade['reason']})"
        )
    print("-" * 60)
    print(f"Last price : ${result['last_price']:.2f}")
    print(f"Cash       : ${result['cash']:.2f}")
    print(f"Shares     : {result['shares']:.4f}")
    print(f"Equity     : ${result['equity']:.2f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="daytrader",
        description=(
            "Educational market-analysis and paper-trading tool. "
            "Simulated balances only - never real money."
        ),
    )
    parser.add_argument(
        "--data-dir", type=Path, default=None,
        help="Override where account/portfolio data is stored (defaults to ./daytrader_data).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    register = sub.add_parser("register", help="Create a new account with a password.")
    register.add_argument("--username")
    register.add_argument("--password")
    register.add_argument("--balance", type=float, default=10_000.0)
    register.set_defaults(func=cmd_register)

    trade = sub.add_parser("trade", help="Log in and run a market-analysis/day-trading session.")
    trade.add_argument("--username")
    trade.add_argument("--password")
    trade.add_argument("--symbol", default="AAPL")
    trade.add_argument("--risk", type=float, default=0.5, help="Fraction of cash to risk per BUY signal.")
    trade.add_argument("--show-trades", type=int, default=10, dest="show_trades")
    trade.set_defaults(func=cmd_trade)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
