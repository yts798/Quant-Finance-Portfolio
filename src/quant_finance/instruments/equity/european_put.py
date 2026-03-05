from dataclasses import dataclass
from datetime import date

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass


@dataclass(frozen=True)
class EuropeanPut(BaseInstrument):
    """Vanilla European put option – exercise only at maturity."""

    asset_class: AssetClass = AssetClass.EQUITY

    strike: float
    expiry: date
    underlying_ticker: str = "SPX"
    dividend_yield: float = 0.0

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError("Strike must be positive")
        if self.expiry <= date.today():
            raise ValueError("Expiry must be in the future")

    def payoff(self, spot: float) -> float:
        return max(self.strike - spot, 0.0)

    def is_path_dependent(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            f"EuropeanPut({self.underlying_ticker!r}, "
            f"K={self.strike:.2f}, T={self.expiry:%Y-%m-%d}, "
            f"q={self.dividend_yield:.2%})"
        )