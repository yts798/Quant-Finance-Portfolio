# src/quant_finance/instruments/credit/cds.py

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass


@dataclass(frozen=True)
class CDS(BaseInstrument):
    """Single-Name Credit Default Swap (Protection Buyer perspective)."""

    reference_entity: str
    expiry: date
    notional: float = 1_000_000.0
    coupon: float = 0.01           # annual spread in decimal (100bps = 0.01)
    recovery_rate: float = 0.40
    upfront: float = 0.0           # upfront payment (can be positive or negative)
    start_date: Optional[date] = None
    asset_class: AssetClass = AssetClass.CREDIT

    def __post_init__(self) -> None:
        if self.notional <= 0:
            raise ValueError("Notional must be positive")
        if not (0 <= self.recovery_rate <= 1):
            raise ValueError("Recovery rate must be between 0 and 1")
        if self.expiry <= date.today():
            raise ValueError("Expiry must be in the future")
        if self.start_date is None:
            object.__setattr__(self, "start_date", date.today())

    def payoff(self, default_happened: bool, default_time: Optional[date] = None) -> float:
        """
        Simplified net payoff for Protection Buyer.
        In full model, we need to calculate accrued premium and exact timing.
        """
        if default_happened:
            # Protection leg: Seller pays Loss Given Default
            protection_leg = self.notional * (1 - self.recovery_rate)
            # Premium leg: Buyer has paid some coupons until default
            # For simplicity, we ignore accrued for now
            return protection_leg - self.upfront
        else:
            # No default: Buyer loses all premiums + upfront
            return -self.upfront

    def is_path_dependent(self) -> bool:
        return True   # Default timing matters

    def __repr__(self) -> str:
        return (
            f"CDS({self.reference_entity!r}, "
            f"Expiry={self.expiry:%Y-%m-%d}, "
            f"Coupon={self.coupon:.2%}, "
            f"RR={self.recovery_rate:.0%}, "
            f"Upfront={self.upfront:.2f})"
        )