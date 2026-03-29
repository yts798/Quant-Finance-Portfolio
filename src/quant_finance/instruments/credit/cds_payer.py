# src/quant_finance/instruments/credit/cds_payer_option.py

from dataclasses import dataclass
from datetime import date

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass
from .cds import CDS   # import the underlying CDS


@dataclass(frozen=True)
class CDSPayerOption(BaseInstrument):
    """Payer CDS Option – right to buy protection at fixed strike spread."""

    underlying_cds: CDS
    strike_spread: float          # strike spread (in decimal)
    expiry: date                  # option expiry (usually before CDS start)
    asset_class: AssetClass = AssetClass.CREDIT

    def __post_init__(self) -> None:
        if self.strike_spread < 0:
            raise ValueError("Strike spread cannot be negative")
        if self.expiry >= self.underlying_cds.expiry:
            raise ValueError("Option expiry must be before CDS expiry")

    def payoff(self, market_spread: float) -> float:
        """Payoff if exercised into the CDS at option expiry."""
        # Simplified: value of entering CDS at strike vs current market spread
        # In full model, this is the present value of the CDS at exercise
        if market_spread > self.strike_spread:
            # Positive value for payer (protection is more expensive)
            return self.underlying_cds.notional * (market_spread - self.strike_spread) * 0.01
        return 0.0

    def is_path_dependent(self) -> bool:
        return True   # depends on spread evolution

    def __repr__(self) -> str:
        return (
            f"CDSPayerOption({self.underlying_cds.reference_entity!r}, "
            f"StrikeSpread={self.strike_spread:.2%}, "
            f"OptionExpiry={self.expiry:%Y-%m-%d})"
        )