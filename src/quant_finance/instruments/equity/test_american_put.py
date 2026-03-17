# src/quant_finance/instruments/equity/test_american_put.py

import sys
import os

# Path fix: add repo root
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
sys.path.insert(0, repo_root)

from datetime import date, timedelta

# Now import should work
from src.quant_finance.instruments.equity.american_put import AmericanPut


def test():
    tomorrow = date.today() + timedelta(days=1)

    print("=== American Put test ===\n")

    put = AmericanPut(
        strike=4400.0,
        expiry=tomorrow,
        underlying_ticker="SPX",
        dividend_yield=0.015,
    )

    print("Created:")
    print(" ", put)
    print(f"  describe():       {put.describe()}")
    print(f"  Path dependent?   : {put.is_path_dependent()}")
    print(f"  Currency/Notional : {put.currency} / {put.notional}\n")

    print("Payoff examples:")
    print(f"  Spot 4300 → {put.payoff(4300):.2f}   (ITM)")
    print(f"  Spot 4400 → {put.payoff(4400):.2f}   (ATM)")
    print(f"  Spot 4500 → {put.payoff(4500):.2f}   (OTM)\n")


if __name__ == "__main__":
    test()