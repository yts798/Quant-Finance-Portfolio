# core/base_instrument.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional
from enum import Enum, auto
# from .asset_class import AssetClass   # ← new import


class AssetClass(Enum):
    """Mutually exclusive top-level asset classes."""

    EQUITY      = auto()   # stocks, indices, single-name equity derivatives
    RATES       = auto()   # interest rates, bonds, swaps, swaptions, ...
    FX          = auto()   # foreign exchange spots, forwards, FX options
    CREDIT      = auto()   # CDS, defaultable bonds, credit indices
    COMMODITY   = auto()   # futures/options on oil, gold, ags, metals, ...
    INFLATION   = auto()   # inflation-linked bonds, YoY/II swaps
    HYBRID      = auto()   # convertibles, equity+rates hybrids, quantos, ...

    def __str__(self) -> str:
        return self.name.lower()
@dataclass
class MarketDataSnapshot:
    """Simple market data snapshot at pricing time"""
    spot: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float = 0.0
    valuation_date: date = None

    def __post_init__(self):
        if self.valuation_date is None:
            self.valuation_date = date.today()


class BaseInstrument(ABC):
    """
    Abstract base class for all financial instruments.
    """

    # Required: every concrete instrument must declare its asset class
    asset_class: AssetClass

    # Common fields (inherited defaults)
    currency: str = "USD"
    notional: float = 1.0

    @abstractmethod
    def payoff(self, spot: float) -> float:
        pass

    @abstractmethod
    def is_path_dependent(self) -> bool:
        pass

    def expiry(self) -> Optional[date]:
        return getattr(self, 'expiry', None)

    def requires_simulation(self) -> bool:
        return self.is_path_dependent()

    def describe(self) -> str:
        exp = self.expiry()
        exp_str = exp.isoformat() if exp else 'N/A'
        return (
            f"{self.__class__.__name__}("
            f"asset_class={self.asset_class}, "
            f"expiry={exp_str}, "
            f"currency={self.currency}, "
            f"notional={self.notional:.2f}"
            f")"
        )

    def __repr__(self) -> str:
        exp_str = self.expiry().isoformat() if self.expiry() else 'N/A'
        return f"{self.__class__.__name__}(asset_class={self.asset_class}, expiry={exp_str})"