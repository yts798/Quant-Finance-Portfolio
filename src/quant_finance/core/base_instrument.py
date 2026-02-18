from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class MarketDataSnapshot:
    """Simple market data at pricing time"""
    spot: float                    # underlying price
    risk_free_rate: float          # continuous risk-free rate
    volatility: float              # implied volatility (flat for now)
    dividend_yield: float = 0.0    # continuous dividend yield
    valuation_date: date = None    # defaults to today


class BaseInstrument(ABC):
    """
    Abstract base class for all financial instruments.
    
    Every derivative (option, swap, CDS, future, etc.) should inherit from this.
    """

    @abstractmethod
    def payoff(self, spot: float) -> float:
        """
        Payoff at maturity given the final underlying price.
        For path-dependent instruments this is called at the end of each path.
        """
        pass

    @abstractmethod
    def is_path_dependent(self) -> bool:
        """
        True if the instrument needs the full price path to compute payoff
        (Asian, lookback, barrier with knock-out/in, etc.)
        False for European/American vanilla options, forwards, etc.
        """
        pass

    @property
    @abstractmethod
    def expiry(self) -> date:
        """Expiry/maturity date of the instrument"""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(expiry={self.expiry})"