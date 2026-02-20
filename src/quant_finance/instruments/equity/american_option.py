from datetime import date
from dataclasses import dataclass
from ...core.base_instrument import BaseInstrument, MarketDataSnapshot


@dataclass
class EuropeanCall(BaseInstrument):
    """Vanilla European call option"""
    strike: float
    expiry_date: date
    underlying_ticker: str = "AAPL"   # for data fetching later

    def payoff(self, spot: float) -> float:
        return max(spot - self.strike, 0.0)

    @property
    def expiry(self) -> date:
        return self.expiry_date

    def is_path_dependent(self) -> bool:
        return False


@dataclass
class EuropeanPut(BaseInstrument):
    """Vanilla European put option"""
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