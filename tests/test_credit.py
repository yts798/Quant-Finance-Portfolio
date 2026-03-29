# test_cds.py
# Simple test script for CDS (Credit Default Swap)
# Run with: python test_cds.py

from datetime import date, timedelta

from quant_finance.instruments.credit.cds import CDS
from quant_finance.instruments.credit.cds_payer import CDSPayerOption
from quant_finance.instruments.credit.cds_receiver import CDSReceiverOption

def main():
    expiry = date.today() + timedelta(days=365)   # 1 year CDS

    print("=== CDS Test ===\n")

    # Create a CDS where we are the Protection Buyer
    cds = CDS(
        reference_entity="Tesla",
        expiry=expiry,
        notional=10_000_000.0,      # $10 million notional
        coupon=0.0125,              # 125 basis points (1.25%)
        recovery_rate=0.40,         # 40% recovery assumption
        upfront=0.0,                # No upfront for this example
    )

    print("Created CDS:")
    print(f"  {cds}")
    print(f"  Notional:          ${cds.notional:,.0f}")
    print(f"  Coupon (spread):   {cds.coupon:.2%}")
    print(f"  Recovery Rate:     {cds.recovery_rate:.0%}")
    print(f"  Upfront:           ${cds.upfront:.2f}")
    print(f"  Path dependent?    {cds.is_path_dependent()}\n")

    # Test payoff scenarios
    print("Payoff Scenarios (from Protection Buyer view):")
    print("-" * 60)
    print(f"No default until expiry      → Payoff: {cds.payoff(default_happened=False):.2f}")
    print(f"Default occurs               → Payoff: {cds.payoff(default_happened=True):.2f}")
    print()

    # Example with different recovery rate
    cds_high_recovery = CDS(
        reference_entity="Tesla",
        expiry=expiry,
        notional=10_000_000.0,
        coupon=0.0080,          # lower spread because lower risk
        recovery_rate=0.60,     # higher recovery
        upfront=0.0,
    )

    print("With higher recovery (60%):")
    print(f"  Default payoff: {cds_high_recovery.payoff(default_happened=True):.2f} "
          f"(less protection needed)")

    print("\nDone. Try changing coupon, recovery_rate, or notional → save → run again.")

    payer_option = CDSPayerOption(
        underlying_cds=cds,
        strike_spread=0.0100,    # 100 bps strike
        expiry=expiry - timedelta(days=180),   # option expires 6 months earlier
    )

    # 3. Receiver CDS Option
    receiver_option = CDSReceiverOption(
        underlying_cds=cds,
        strike_spread=0.0140,    # 140 bps strike
        expiry=expiry - timedelta(days=180),
    )

    print("2. Payer CDS Option (right to buy protection):")
    print(f"  {payer_option}")
    print(f"  Payoff if market spread = 80bps  : {payer_option.payoff(0.0080):,.2f}")
    print(f"  Payoff if market spread = 150bps : {payer_option.payoff(0.0150):,.2f}\n")

    print("3. Receiver CDS Option (right to sell protection):")
    print(f"  {receiver_option}")
    print(f"  Payoff if market spread = 80bps  : {receiver_option.payoff(0.0080):,.2f}")
    print(f"  Payoff if market spread = 150bps : {receiver_option.payoff(0.0150):,.2f}\n")

    print("Key Takeaways:")
    print("• CDS pays when default happens")
    print("• Payer Option profits when credit spreads widen")
    print("• Receiver Option profits when credit spreads tighten")
    print("\nChange strike_spread or coupon → save → run again to see payoff changes.")


if __name__ == "__main__":
    main()