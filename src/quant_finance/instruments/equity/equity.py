# src/quant_finance/instruments/equity/equity.py

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass


@dataclass
class Equity(BaseInstrument):
    """Cash Equity / Single Stock (the underlying asset)."""

    ticker: str
    current_price: float
    dividend_yield: float = 0.0
    asset_class: AssetClass = AssetClass.EQUITY
    contract_multiplier: int = 1  # usually 1 for shares
    sector: Optional[str] = None
    beta: float = 1.0
    # Historical prices keyed by date (date -> close price)
    price_history: Dict[date, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.current_price <= 0:
            raise ValueError("Current price must be positive")
        if not (0 <= self.dividend_yield <= 1):
            raise ValueError("Dividend yield must be between 0 and 1")

    def update_price(self, new_price: float, as_of_date: Optional[date] = None) -> None:
        """Update the current price, optionally recording in price history."""
        if new_price <= 0:
            raise ValueError("Price must be positive")
        if as_of_date is not None:
            self.price_history[as_of_date] = self.current_price
        self.current_price = new_price

    def get_historical_price(self, trade_date: date) -> Optional[float]:
        """Retrieve historical price for a given date."""
        return self.price_history.get(trade_date)

    def payoff(self, spot: float) -> float:
        """Value of holding the stock."""
        return spot * self.contract_multiplier

    def is_path_dependent(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            f"Equity({self.ticker!r}, "
            f"Price={self.current_price:.2f}, "
            f"q={self.dividend_yield:.2%})"
        )