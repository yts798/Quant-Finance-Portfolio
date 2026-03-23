# src/quant_finance/instruments/equity/american_call.py

from dataclasses import dataclass
from datetime import date

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass


@dataclass(frozen=True)
class AmericanCall(BaseInstrument):
    """American call option – early exercise possible."""

    strike: float
    expiry: date
    underlying_ticker: str = "SPX"
    dividend_yield: float = 0.0
    current_spot: float | None = None
    asset_class: AssetClass = AssetClass.EQUITY
    contract_multiplier: int = 100

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError("Strike must be positive")
        if self.expiry <= date.today():
            raise ValueError("Expiry must be in the future")

    def payoff(self, spot: float) -> float:
        return max(spot - self.strike, 0.0)

    def is_path_dependent(self) -> bool:
        return True

    def current_intrinsic(self) -> float:
        """Current intrinsic value if we know spot price."""
        if self.current_spot is None:
            return 0.0
        return max(self.current_spot - self.strike, 0.0)

    def __repr__(self) -> str:
        return (
            f"AmericanCall({self.underlying_ticker!r}, "
            f"K={self.strike:.2f}, T={self.expiry:%Y-%m-%d}, "
            f"q={self.dividend_yield:.2%})"
        )