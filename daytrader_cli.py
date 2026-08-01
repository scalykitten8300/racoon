"""Entry point for the day-trading tool.

Usage:
    python daytrader_cli.py register --username <name> --password <pass>
    python daytrader_cli.py trade --username <name> --password <pass> --symbol AAPL
"""
from daytrader.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
