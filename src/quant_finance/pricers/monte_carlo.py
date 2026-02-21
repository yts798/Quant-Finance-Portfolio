from datetime import date, timedelta
import numpy as np

from src.quant_finance.core.base_instrument import MarketDataSnapshot
from src.quant_finance.instruments.equity.european_option import EuropeanCall
from src.quant_finance.instruments.equity.american_option import AmericanPut
from src.quant_finance.pricers.black_scholes import BlackScholesPricer
from src.quant_finance.pricers.binomial import BinomialPricer


def main():
    # Market data (later → yfinance)
    market = MarketDataSnapshot(
        spot=185.50,
        risk_free_rate=0.042,
        volatility=0.285,
        dividend_yield=0.005,
        valuation_date=date.today()
    )

    # European Call example
    expiry = date.today() + timedelta(days=45)
    euro_call = EuropeanCall(strike=190.0, expiry_date=expiry)

    # American Put example (to show early exercise)
    amer_put = AmericanPut(strike=180.0, expiry_date=expiry)

    # Pricers
    bs = BlackScholesPricer()
    binom_fast = BinomialPricer(n_steps=50)
    binom_accurate = BinomialPricer(n_steps=200)

    print("=== European Call ===")
    print(f"Black-Scholes:     ${bs.price(euro_call, market):.4f}")
    print(f"Binomial (50 steps): ${binom_fast.price(euro_call, market):.4f}")
    print(f"Binomial (200 steps):${binom_accurate.price(euro_call, market):.4f}")

    print("\n=== American Put ===")
    print(f"Binomial (50 steps): ${binom_fast.price(amer_put, market):.4f}")
    print(f"Binomial (200 steps):${binom_accurate.price(amer_put, market):.4f}")
    # Note: BlackScholes would underprice American Put due to early exercise


if __name__ == "__main__":
    main()