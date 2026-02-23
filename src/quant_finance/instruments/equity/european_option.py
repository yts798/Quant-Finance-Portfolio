from datetime import date
from dataclasses import dataclass

from ...core.base_instrument import BaseInstrument


@dataclass
class EuropeanCall(BaseInstrument):
    """Vanilla European call option"""
    strike: float
    expiry: date                      # ← changed: no _date suffix
    underlying_ticker: str = "AAPL"   # useful for later yfinance integration

    def payoff(self, spot: float) -> float:
        return max(spot - self.strike, 0.0)

    def is_path_dependent(self) -> bool:
        return False


@dataclass
class EuropeanPut(BaseInstrument):
    """Vanilla European put option"""
    strike: float
    expiry: date
    underlying_ticker: str = "AAPL"

    def payoff(self, spot: float) -> float:
        return max(self.strike - spot, 0.0)

    def is_path_dependent(self) -> bool:
        return False