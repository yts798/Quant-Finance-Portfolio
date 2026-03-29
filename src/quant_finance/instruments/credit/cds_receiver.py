# src/quant_finance/instruments/credit/cds_receiver_option.py

from dataclasses import dataclass
from datetime import date

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass
from .cds import CDS


@dataclass(frozen=True)
class CDSReceiverOption(BaseInstrument):
    """Receiver CDS Option – right to sell protection at fixed strike spread."""

    underlying_cds: CDS
    strike_spread: float
    expiry: date
    asset_class: AssetClass = AssetClass.CREDIT

    def __post_init__(self) -> None:
        if self.strike_spread < 0:
            raise ValueError("Strike spread cannot be negative")
        if self.expiry >= self.underlying_cds.expiry:
            raise ValueError("Option expiry must be before CDS expiry")

    def payoff(self, market_spread: float) -> float:
        """Payoff if exercised into the CDS at option expiry."""
        if market_spread < self.strike_spread:
            # Positive value for receiver
            return self.underlying_cds.notional * (self.strike_spread - market_spread) * 0.01
        return 0.0

    def is_path_dependent(self) -> bool:
        return True

    def __repr__(self) -> str:
        return (
            f"CDSReceiverOption({self.underlying_cds.reference_entity!r}, "
            f"StrikeSpread={self.strike_spread:.2%}, "
            f"OptionExpiry={self.expiry:%Y-%m-%d})"
        )