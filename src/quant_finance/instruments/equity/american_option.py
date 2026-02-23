# src/quant_finance/instruments/equity/american_option.py
from datetime import date
from dataclasses import dataclass

from ...core.base_instrument import BaseInstrument


@dataclass
class AmericanCall(BaseInstrument):
    strike: float
    expiry: date
    underlying_ticker: str = "AAPL"

    def payoff(self, spot: float) -> float:
        return max(spot - self.strike, 0.0)

    def is_path_dependent(self) -> bool:
        return False  # but early exercise check is in pricer


@dataclass
class AmericanPut(BaseInstrument):
    strike: float
    expiry: date
    underlying_ticker: str = "AAPL"

    def payoff(self, spot: float) -> float:
        return max(self.strike - spot, 0.0)

    def is_path_dependent(self) -> bool:
        return False