# src/quant_finance/instruments/equity/digital_call.py

from dataclasses import dataclass
from datetime import date

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass


@dataclass(frozen=True)
class DigitalCall(BaseInstrument):
    """Digital (cash-or-nothing) call – pays fixed amount if ITM at expiry."""

    strike: float
    expiry: date
    underlying_ticker: str = "SPX"
    dividend_yield: float = 0.0
    current_spot: float | None = None
    asset_class: AssetClass = AssetClass.EQUITY
    contract_multiplier: int = 1
    cash_amount: float = 1.0           # payout if ITM (e.g. 1 or notional)

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError("Strike must be positive")
        if self.expiry <= date.today():
            raise ValueError("Expiry must be in the future")
        if self.cash_amount <= 0:
            raise ValueError("Cash amount must be positive")

    def payoff(self, spot: float) -> float:
        return self.cash_amount if spot > self.strike else 0.0

    def is_path_dependent(self) -> bool:
        return False

    def current_intrinsic(self) -> float:
        """Current 'intrinsic' – would pay out now if exercised today."""
        if self.current_spot is None:
            return 0.0
        return self.cash_amount if self.current_spot > self.strike else 0.0

    def __repr__(self) -> str:
        return (
            f"DigitalCall({self.underlying_ticker!r}, "
            f"K={self.strike:.2f}, T={self.expiry:%Y-%m-%d}, "
            f"q={self.dividend_yield:.2%}, "
            f"cash={self.cash_amount})"
        )