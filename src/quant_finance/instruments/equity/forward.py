# src/quant_finance/instruments/equity/forward.py

from dataclasses import dataclass
from datetime import date
from enum import Enum

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass
from .equity import Equity


class ForwardSide(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class Forward(BaseInstrument):
    """Equity forward contract – obligation to buy (long) or sell (short) at fixed strike."""

    equity: Equity
    strike: float
    expiry: date
    side: ForwardSide = ForwardSide.LONG
    contract_multiplier: int = 1
    asset_class: AssetClass = AssetClass.EQUITY

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError("Strike must be positive")

    @property
    def underlying_ticker(self) -> str:
        return self.equity.ticker

    @property
    def current_spot(self) -> float:
        return self.equity.current_price

    def payoff(self, spot: float) -> float:
        """Forward payoff at maturity."""
        direction = 1 if self.side == ForwardSide.LONG else -1
        return direction * (spot - self.strike) * self.contract_multiplier

    @property
    def current_value(self) -> float:
        """Current unrealized P&L (mark-to-market at today's spot)."""
        return self.payoff(self.equity.current_price)

    def is_path_dependent(self) -> bool:
        return False

    def current_forward_value(self, current_forward_price: float) -> float:
        """Mark-to-market using the current forward price (not spot).

        Useful when you have a forward curve rather than just spot.
        """
        direction = 1 if self.side == ForwardSide.LONG else -1
        return direction * (current_forward_price - self.strike) * self.contract_multiplier

    def expiry_days(self, current_date: date) -> int:
        """Days to expiration from a given date."""
        if self.expiry <= current_date:
            return 0
        return (self.expiry - current_date).days

    def __repr__(self) -> str:
        side_str = "Long" if self.side == ForwardSide.LONG else "Short"
        return (
            f"{side_str}Forward({self.underlying_ticker!r}, "
            f"K={self.strike:.2f}, T={self.expiry:%Y-%m-%d})"
        )
