import numpy as np
from scipy.stats import norm
from ..core.base_pricer import BasePricer
from ..core.base_instrument import BaseInstrument, MarketDataSnapshot
from ..instruments.equity.european_option import EuropeanCall, EuropeanPut


class BlackScholesPricer(BasePricer):
    """Analytic Black-Scholes pricer for European vanilla options"""

    def price(self, instrument: BaseInstrument, market: MarketDataSnapshot) -> float:
        if not isinstance(instrument, (EuropeanCall, EuropeanPut)):
            raise TypeError("BlackScholesPricer only supports European vanilla options")

        S = market.spot
        K = instrument.strike
        T = (instrument.expiry - market.valuation_date).days / 365.25
        r = market.risk_free_rate
        sigma = market.volatility
        q = market.dividend_yield

        if T <= 0:
            if isinstance(instrument, EuropeanCall):
                return max(S - K, 0.0)
            else:
                return max(K - S, 0.0)

        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if isinstance(instrument, EuropeanCall):
            price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # Put
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

        return price

    def delta(self, instrument: BaseInstrument, market: MarketDataSnapshot) -> float:
        # Simplified – full implementation later if needed
        return 0.5  # placeholder