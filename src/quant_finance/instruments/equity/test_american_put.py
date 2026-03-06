# src/quant_finance/instruments/equity/test_american_put.py
# Minimal self-contained test — run this file directly

from datetime import date, timedelta
from dataclasses import dataclass
# ────────────────────────────────────────────────
# Fake minimal versions of the classes we need
# (so you can test even if imports are broken)
# ────────────────────────────────────────────────

class AssetClass:
    EQUITY = "EQUITY"

class BaseInstrument:
    def __init__(self):
        self.currency = "USD"
        self.notional = 1.0
        self.asset_class = AssetClass.EQUITY

    def describe(self):
        return f"{self.__class__.__name__}(asset_class={self.asset_class})"


@dataclass
class AmericanPut(BaseInstrument):
    strike: float
    expiry: date
    underlying_ticker: str = "SPX"

    def payoff(self, spot: float) -> float:
        return max(self.strike - spot, 0.0)

    def is_path_dependent(self) -> bool:
        return True

    def __repr__(self):
        return f"AmericanPut({self.underlying_ticker}, K={self.strike}, T={self.expiry})"


# ────────────────────────────────────────────────
# The actual test code
# ────────────────────────────────────────────────

def test():
    tomorrow = date.today() + timedelta(days=1)

    print("=== American Put test ===\n")

    put = AmericanPut(
        strike=4400.0,
        expiry=tomorrow,
    )

    print("Created:")
    print(" ", put)
    print(f"  {put.describe()}")
    print(f"  Path dependent?   : {put.is_path_dependent()}")
    print(f"  Currency/Notional : {put.currency} / {put.notional}\n")

    print("Payoff examples:")
    print(f"  Spot 4300 → {put.payoff(4300):.2f}   (ITM)")
    print(f"  Spot 4400 → {put.payoff(4400):.2f}   (ATM)")
    print(f"  Spot 4500 → {put.payoff(4500):.2f}   (OTM)\n")

    print("Change any number above (strike, spot values) and run again.")


if __name__ == "__main__":
    test()