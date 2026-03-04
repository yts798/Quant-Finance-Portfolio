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

    # Common fields — subclasses inherit these defaults (override as needed)
    currency: str = "USD"
    notional: float = 1.0
    # You can add more later: e.g. trade_date: date = field(default_factory=date.today)

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
    # Conventional helpers (not abstract — safe to call on any instance)
    # ────────────────────────────────────────────────

    def expiry(self) -> Optional[date]:
        """Safe accessor for expiry date if the subclass defines it."""
        return getattr(self, 'expiry', None)

    def requires_simulation(self) -> bool:
        """Alias for is_path_dependent() — clearer intent for pricing engines."""
        return self.is_path_dependent()

    def describe(self) -> str:
        """Human-readable summary — great for debugging / logging."""
        exp = self.expiry()
        exp_str = exp.isoformat() if exp else 'N/A'
        return (
            f"{self.__class__.__name__}("
            f"expiry={exp_str}, "
            f"currency={self.currency}, "
            f"notional={self.notional:.2f}"
            f")"
        )

    def __repr__(self) -> str:
        # Keep your safe repr, but now we can lean on describe() if wanted
        exp_str = self.expiry().isoformat() if self.expiry() else 'N/A'
        return f"{self.__class__.__name__}(expiry={exp_str})"