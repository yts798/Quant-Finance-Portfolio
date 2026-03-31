# src/quant_finance/instruments/portfolio/portfolio.py

from dataclasses import dataclass, field
from typing import Dict, List

from .position import Position


@dataclass
class Portfolio:
    """Portfolio containing multiple positions + cash."""

    name: str = "My Portfolio"
    positions: Dict[str, Position] = field(default_factory=dict)
    cash: float = 0.0

    def add_position(self, position: Position) -> None:
        """Add or update a position."""
        self.positions[position.equity.ticker] = position

    def total_value(self) -> float:
        """Total portfolio value = cash + sum of all position values."""
        positions_value = sum(pos.current_value() for pos in self.positions.values())
        return self.cash + positions_value

    def total_unrealized_pnl(self) -> float:
        """Total unrealized profit & loss across all positions."""
        return sum(pos.unrealized_pnl() for pos in self.positions.values())

    def __repr__(self) -> str:
        return (
            f"Portfolio('{self.name}', "
            f"Positions={len(self.positions)}, "
            f"Cash=${self.cash:,.2f}, "
            f"Total Value=${self.total_value():,.2f})"
        )
    
    