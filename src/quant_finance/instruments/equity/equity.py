# src/quant_finance/instruments/equity/equity.py

from dataclasses import dataclass
from datetime import date

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass


@dataclass(frozen=True)
class Equity(BaseInstrument):
    """Cash Equity / Single Stock (the underlying asset)."""

    ticker: str
    current_price: float
    dividend_yield: float = 0.0
    asset_class: AssetClass = AssetClass.EQUITY
    contract_multiplier: int = 1   # usually 1 for shares

    def __post_init__(self) -> None:
        if self.current_price <= 0:
            raise ValueError("Current price must be positive")
        if not (0 <= self.dividend_yield <= 1):
            raise ValueError("Dividend yield must be between 0 and 1")

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