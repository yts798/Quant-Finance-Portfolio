from datetime import date, timedelta

from src.quant_finance.core.base_instrument import BaseInstrument
from quant_finance.core.asset_class import AssetClass
from quant_finance.instruments.equity.american_put import AmericanPut

def main():
    # Create a realistic option
    expiry = date.today() + timedelta(days=90)
    print(1)
    put = AmericanPut(
        strike=4400.0,
        expiry=expiry,
        underlying_ticker="SPX",
        dividend_yield=0.015,
    )
    print("=== American Put Test ===")
    print(f"Object:          {put}")

if __name__ == "__main__":
    main()