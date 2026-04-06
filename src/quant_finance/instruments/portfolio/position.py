
# src/quant_finance/instruments/portfolio/position.py
    
from dataclasses import dataclass
from datetime import date

from ..equity.equity import Equity


@dataclass(frozen=True)
class Position:
    """Represents a single holding in a portfolio."""

    equity: Equity
    quantity: float          # positive = long, negative = short
    average_cost: float      # average purchase price

    def __post_init__(self) -> None:
        if self.quantity == 0:
            raise ValueError("Quantity cannot be zero")

    def current_value(self) -> float:
        """Current market value of this position."""
        return self.quantity * self.equity.current_price

    def unrealized_pnl(self) -> float:
        """Unrealized profit & loss."""
        return self.current_value() - (self.quantity * self.average_cost)

    def __repr__(self) -> str:
        return (
            f"Position({self.equity.ticker}, "
            f"Qty={self.quantity:.0f}, "
            f"AvgCost={self.average_cost:.3f}, "
            
            f"Value={self.current_value():,.2f})"
        )