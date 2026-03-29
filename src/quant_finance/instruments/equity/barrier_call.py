# src/quant_finance/instruments/equity/barrier_call.py

from dataclasses import dataclass
from datetime import date

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass


@dataclass(frozen=True)
class BarrierCall(BaseInstrument):
    """Down-and-Out Barrier Call – knocks out if spot hits barrier during life."""

    barrier: float                    # knock-out level
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
        if self.barrier <= 0:
            raise ValueError("Barrier must be positive")
        if self.expiry <= date.today():
            raise ValueError("Expiry must be in the future")

    def payoff(self, spot: float) -> float:
        """Placeholder: real version needs full path to check if barrier was hit."""
        return max(spot - self.strike, 0.0)

    def is_path_dependent(self) -> bool:
        return True

    def current_intrinsic(self) -> float:
        if self.current_spot is None:
            return 0.0
        return max(self.current_spot - self.strike, 0.0)

    def __repr__(self) -> str:
        return (
            f"BarrierCall({self.underlying_ticker!r}, "
            f"K={self.strike:.2f}, B={self.barrier:.2f}, "
            f"T={self.expiry:%Y-%m-%d}, q={self.dividend_yield:.2%})"
        )