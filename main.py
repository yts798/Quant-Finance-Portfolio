"""
main.py - Entry point to price a European call option using Black-Scholes

Run with:
    python main.py
"""

from datetime import date, timedelta
import numpy as np
from scipy.stats import norm

# ── Import our own modules ───────────────────────────────────────────────
from src.quant_finance.core.base_instrument import BaseInstrument, MarketDataSnapshot
from src.quant_finance.instruments.equity.european_option import EuropeanCall


def black_scholes_call_price(
    S: float,           # spot price
    K: float,           # strike
    T: float,           # time to expiry in years
    r: float,           # risk-free rate (continuous)
    sigma: float,       # volatility (annualized)
    q: float = 0.0      # dividend yield (continuous)
) -> float:
    """
    Classic Black-Scholes formula for European call
    """
    if T <= 0:
        return max(S - K, 0.0)

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    call_price = (
        S * np.exp(-q * T) * norm.cdf(d1)
        - K * np.exp(-r * T) * norm.cdf(d2)
    )
    return call_price

def main():
    # ── Example market data (you will replace this with yfinance later) ──
    market = MarketDataSnapshot(
        spot=185.50,                    # current AAPL price (example)
        risk_free_rate=0.042,           # ~4.2% US treasury / SOFR approx
        volatility=0.285,               # implied vol ~28.5%
        dividend_yield=0.005,           # AAPL approximate yield
        valuation_date=date.today()
    )

    # ── Create the instrument ────────────────────────────────────────────
    expiry_in_days = 45
    expiry_date = date.today() + timedelta(days=expiry_in_days)

    call_option = EuropeanCall(
        strike=190.0,
        expiry_date=expiry_date,
        underlying_ticker="AAPL"
    )

    # ── Compute time to expiry in years ──────────────────────────────────
    days_to_expiry = (call_option.expiry - market.valuation_date).days
    T_years = days_to_expiry / 365.25

    # ── Price it ─────────────────────────────────────────────────────────
    price = black_scholes_call_price(
        S=market.spot,
        K=call_option.strike,
        T=T_years,
        r=market.risk_free_rate,
        sigma=market.volatility,
        q=market.dividend_yield
    )

    # ── Output ───────────────────────────────────────────────────────────
    print(f"{'='*60}")
    print(f"European Call Option Pricing (Black-Scholes)")
    print(f"{'='*60}")
    print(f"Underlying:          {call_option.underlying_ticker}")
    print(f"Spot price:          ${market.spot:.2f}")
    print(f"Strike:              ${call_option.strike:.2f}")
    print(f"Expiry date:         {call_option.expiry}")
    print(f"Days to expiry:      {days_to_expiry}")
    print(f"Risk-free rate:      {market.risk_free_rate:.3%}")
    print(f"Volatility:          {market.volatility:.1%}")
    print(f"Dividend yield:      {market.dividend_yield:.2%}")
    print(f"{'-'*60}")
    print(f"**Call Price**:      **${price:.4f}**")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()