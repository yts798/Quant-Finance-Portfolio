from datetime import date, timedelta

from quant_finance.core.base_instrument import BaseInstrument
from quant_finance.core.asset_class import AssetClass
from quant_finance.instruments.equity import (
    EuropeanCall,
    EuropeanPut,
    AmericanCall,
    AmericanPut,
    Forward,
    DigitalCall,
    DigitalPut
)
def main():
    expiry = date.today() + timedelta(days=60)
    spot = 4500.0
    next_month = date.today() + timedelta(days=30)
    print("=== Vanilla Options Test ===\n")
    ap = AmericanPut(strike=4550, expiry=expiry, current_spot=spot)
    ec = EuropeanCall(strike=4450, expiry=expiry, current_spot=spot)
    ep = EuropeanPut(strike=4550, expiry=expiry, current_spot=spot)
    ac = AmericanCall(strike=4450, expiry=expiry, current_spot=spot)
    fwd = Forward(
        strike=4500.0,
        expiry=next_month,
        underlying_ticker="SPX",
        current_spot=4520.0,
    )


    print(f"Spot price: {spot:.2f}\n")

    for opt in [ec, ep, ac, ap]:
        print(f"{opt.__class__.__name__}:")
        print(f"  {opt}")
        print(f"  Intrinsic: {opt.current_intrinsic():.2f}")
        print(f"  Path dep?  {opt.is_path_dependent()}")
        print()

    print("=== Equity Forward Test ===")
    print(f"Object:          {fwd}")
    print(f"Current value:   {fwd.current_value():.2f}")
    print(f"Path dependent?  {fwd.is_path_dependent()}\n")

    print("Payoff examples (at maturity):")
    print(f"  Spot 4300 → {fwd.payoff(4300):.2f}  (loss)")
    print(f"  Spot 4500 → {fwd.payoff(4500):.2f}  (breakeven)")
    print(f"  Spot 4700 → {fwd.payoff(4700):.2f}  (profit)\n")

    dc = DigitalCall(
        strike=4500.0,
        expiry=next_month,
        underlying_ticker="SPX",
        cash_amount=100.0,
        current_spot=4520.0,
    )

    dp = DigitalPut(
        strike=4550.0,
        expiry=next_month,
        underlying_ticker="SPX",
        cash_amount=100.0,
        current_spot=4520.0,
    )

    print("=== Digital Options Test ===\n")

    print("DigitalCall:")
    print(f"  {dc}")
    print(f"  Current payout: {dc.current_intrinsic():.2f}")
    print(f"  Path dep?       {dc.is_path_dependent()}\n")

    print("DigitalPut:")
    print(f"  {dp}")
    print(f"  Current payout: {dp.current_intrinsic():.2f}")
    print(f"  Path dep?       {dp.is_path_dependent()}\n")

    print("Payoff examples (at expiry):")
    print(f"Spot 4300 → DC: {dc.payoff(4300):.2f} | DP: {dp.payoff(4300):.2f}")
    print(f"Spot 4500 → DC: {dc.payoff(4500):.2f} | DP: {dp.payoff(4500):.2f}")
    print(f"Spot 4600 → DC: {dc.payoff(4600):.2f} | DP: {dp.payoff(4600):.2f}")


if __name__ == "__main__":
    main()