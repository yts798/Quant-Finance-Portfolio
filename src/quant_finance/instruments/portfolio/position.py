
# src/quant_finance/instruments/portfolio/position.py

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..equity.equity import Equity


@dataclass(frozen=True)
class Position:
    """Represents a single holding in a portfolio."""

    equity: Equity
    quantity: float  # positive = long, negative = short
    average_cost: float  # average purchase price per share
    entry_date: Optional[date] = None  # date the position was opened

    def __post_init__(self) -> None:
        if self.quantity == 0:
            raise ValueError("Quantity cannot be zero")

    @property
    def market_value(self) -> float:
        """Current market value of this position (mark-to-market)."""
        return self.quantity * self.equity.current_price

    @property
    def cost_basis(self) -> float:
        """Total cost of this position."""
        return self.quantity * self.average_cost

    def unrealized_pnl(self) -> float:
        """Unrealized profit & loss."""
        return self.market_value - self.cost_basis

    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L as a percentage of cost basis."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl() / self.cost_basis) * 100

    def holding_period_days(self, current_date: date) -> Optional[int]:
        """Number of days since entry (requires current_date)."""
        if self.entry_date is None:
            return None
        return (current_date - self.entry_date).days

    def to_dict(self) -> dict:
        """Serialize position to a dict."""
        return {
            "ticker": self.equity.ticker,
            "quantity": self.quantity,
            "average_cost": self.average_cost,
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pnl": self.unrealized_pnl(),
            "unrealized_pnl_pct": self.unrealized_pnl_pct(),
        }

    def __repr__(self) -> str:
        return (
            f"Position({self.equity.ticker}, "
            f"Qty={self.quantity:.0f}, "
            f"AvgCost={self.average_cost:.2f}, "
            f"Value={self.market_value:,.2f})"
        )