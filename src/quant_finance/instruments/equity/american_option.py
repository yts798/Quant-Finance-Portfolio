from datetime import date
from dataclasses import dataclass
from ...core.base_instrument import BaseInstrument, MarketDataSnapshot

@dataclass
class AmericanCall(BaseInstrument):
    """American call option – allows early exercise"""
    strike: float
    expiry_date: date
    underlying_ticker: str = "AAPL"

    def payoff(self, spot: float) -> float:
        # At any time (including maturity), holder can exercise
        return max(spot - self.strike, 0.0)

    @property
    def expiry(self) -> date:
        return self.expiry_date

    def is_path_dependent(self) -> bool:
        return False   # still not path-dependent, but early exercise matters


@dataclass
class AmericanPut(BaseInstrument):
    """American put option – early exercise often optimal"""
    strike: float
    expiry_date: date
    underlying_ticker: str = "AAPL"

    def payoff(self, spot: float) -> float:
        return max(self.strike - spot, 0.0)

    @property
    def expiry(self) -> date:
        return self.expiry_date

    def is_path_dependent(self) -> bool:
        return False