from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class MarketDataSnapshot:
    """Simple market data snapshot at pricing time"""
    spot: float                    # underlying price
    risk_free_rate: float          # continuous risk-free rate
    volatility: float              # implied volatility (flat for now)
    dividend_yield: float = 0.0    # continuous dividend yield
    valuation_date: date = None    # defaults to today if None

    def __post_init__(self):
        if self.valuation_date is None:
            self.valuation_date = date.today()


class BaseInstrument(ABC):
    """
    Abstract base class for all financial instruments.
    
    Every derivative should inherit from this.
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

    # ────────────────────────────────────────────────
    # Removed abstract @property expiry
    # ────────────────────────────────────────────────
    # Now expiry is just a conventional field that concrete classes should provide.
    # This avoids instantiation errors while keeping the base clean.
    # You can still document it or add a type hint in subclasses if desired.

    def __repr__(self) -> str:
        # Safe repr even if subclass doesn't have expiry
        expiry_str = getattr(self, 'expiry', 'N/A')
        return f"{self.__class__.__name__}(expiry={expiry_str})"