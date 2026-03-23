# src/quant_finance/instruments/equity/forward.py

from dataclasses import dataclass
from datetime import date

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass


@dataclass(frozen=True)
class Forward(BaseInstrument):
    """Equity forward contract – obligation to buy/sell underlying at fixed strike."""

    strike: float
    expiry: date
    underlying_ticker: str = "SPX"
    dividend_yield: float = 0.0
    current_spot: float | None = None
    asset_class: AssetClass = AssetClass.EQUITY
    contract_multiplier: int = 1  # usually 1 for forwards (not 100 like options)

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError("Strike must be positive")
        if self.expiry <= date.today():
            raise ValueError("Expiry must be in the future")

    def payoff(self, spot: float) -> float:
        """Long forward payoff: profit/loss at maturity."""
        return spot - self.strike

    def is_path_dependent(self) -> bool:
        return False

    def current_value(self) -> float:
        """Current unrealized P&L if we know the spot price."""
        if self.current_spot is None:
            return 0.0
        return self.current_spot - self.strike

    def __repr__(self) -> str:
        return (
            f"Forward({self.underlying_ticker!r}, "
            f"K={self.strike:.2f}, T={self.expiry:%Y-%m-%d}, "
            f"q={self.dividend_yield:.2%})"
        )