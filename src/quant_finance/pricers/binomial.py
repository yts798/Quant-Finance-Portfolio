import numpy as np
from ..core.base_pricer import BasePricer
from ..core.base_instrument import BaseInstrument, MarketDataSnapshot


class BinomialPricer(BasePricer):
    """Cox-Ross-Rubinstein binomial tree pricer"""

    def __init__(self, n_steps: int = 100):
        self.n_steps = n_steps

    def price(self, instrument: BaseInstrument, market: MarketDataSnapshot) -> float:
        S = market.spot
        K = instrument.strike
        T = (instrument.expiry - market.valuation_date).days / 365.25
        r = market.risk_free_rate
        sigma = market.volatility
        q = market.dividend_yield

        dt = T / self.n_steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp((r - q) * dt) - d) / (u - d)

        # Stock prices at maturity
        stock_prices = S * u**np.arange(self.n_steps, -1, -2) * d**np.arange(0, self.n_steps + 1, 2)

        # Option values at maturity
        if "Call" in instrument.__class__.__name__:
            option_values = np.maximum(stock_prices - K, 0)
        else:
            option_values = np.maximum(K - stock_prices, 0)

        # Backward induction
        for _ in range(self.n_steps):
            option_values = np.exp(-r * dt) * (
                p * option_values[:-1] + (1 - p) * option_values[1:]
            )
            # Early exercise for American (simple check)
            if "American" in instrument.__class__.__name__:
                exercise = np.maximum(
                    (stock_prices[:-1] - K if "Call" in instrument.__class__.__name__ else K - stock_prices[:-1]),
                    0
                )
                option_values = np.maximum(option_values, exercise)

        return option_values[0]