# src/quant_finance/main.py
from datetime import date, timedelta

from src.quant_finance.instruments.equity import (
    EuropeanCall,
    EuropeanPut,
    AmericanCall,
    AmericanPut,
)


def main():
    # Some future date for testing
    future_date = date.today() + timedelta(days=90)

    print("=== Creating some vanilla options ===\n")

    # European Call
    ec = EuropeanCall(
        strike=4500.0,
        expiry=future_date,
        underlying_ticker="SPX",
        dividend_yield=0.018,  # 1.8%
    )
    print(ec)
    print(f"  Payoff if SPX = 4600: {ec.payoff(4600):.2f}")
    print(f"  Path-dependent? {ec.is_path_dependent()}")
    print(f"  Asset class: {ec.asset_class}")
    print(f"  Currency / Notional: {ec.currency} / {ec.notional}\n")

    # American Put
    ap = AmericanPut(
        strike=4400.0,
        expiry=future_date,
        underlying_ticker="SPX",
    )
    print(ap)
    print(f"  Payoff if SPX = 4300: {ap.payoff(4300):.2f}")
    print(f"  Path-dependent? {ap.is_path_dependent()}")
    print(f"  Asset class: {ap.asset_class}\n")

    # Quick comparison table
    print("Quick comparison:")
    print(f"{'Instrument':<20} {'Path dep?':<12} {'Payoff @ 4550':<15}")
    print("-" * 50)
    spot = 4550.0
    print(f"{ec.__class__.__name__:<20} {str(ec.is_path_dependent()):<12} {ec.payoff(spot):<15.2f}")
    print(f"{ap.__class__.__name__:<20} {str(ap.is_path_dependent()):<12} {ap.payoff(spot):<15.2f}")


if __name__ == "__main__":
    main()