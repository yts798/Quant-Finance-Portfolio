# src/quant_finance/instruments/equity/test_american_put.py
# Simple test that uses your real AmericanPut class

from datetime import date, timedelta

# Import from the same folder (relative import)
from .american_put import AmericanPut


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

    print("Change strike, expiry days, or spot values above → save → run again.")


if __name__ == "__main__":
    test()