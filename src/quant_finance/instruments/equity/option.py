# src/quant_finance/instruments/equity/option.py
"""Option base class and concrete option types."""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from ...core.base_instrument import BaseInstrument
from ...core.asset_class import AssetClass
from .equity import Equity


class ExerciseStyle(Enum):
    EUROPEAN = "european"
    AMERICAN = "american"


# ─────────────────────────────────────────────────────────────────────────────
# Base Option
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Option(BaseInstrument):
    """Equity option – base class for all vanilla and exotic option types."""

    equity: Equity
    strike: float
    expiry: date
    exercise_style: ExerciseStyle = ExerciseStyle.EUROPEAN
    contract_multiplier: int = 100
    asset_class: AssetClass = AssetClass.EQUITY

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError("Strike must be positive")

    @property
    def underlying_ticker(self) -> str:
        return self.equity.ticker

    @property
    def is_american(self) -> bool:
        return self.exercise_style == ExerciseStyle.AMERICAN

    @property
    def is_path_dependent(self) -> bool:
        """American options require lattice/MC due to early exercise."""
        return self.is_american

    @property
    def current_spot(self) -> float:
        """Current spot price from the underlying equity."""
        return self.equity.current_price

    def payoff(self, spot: float) -> float:
        raise NotImplementedError("Subclasses must implement payoff")

    def option_type(self) -> str:
        raise NotImplementedError("Subclasses must return 'call' or 'put'")

    def current_intrinsic(self) -> float:
        raise NotImplementedError("Subclasses must implement current_intrinsic")

    def requires_simulation(self) -> bool:
        return self.is_path_dependent

    def expiry_days(self, current_date: date) -> Optional[int]:
        if self.expiry <= current_date:
            return 0
        return (self.expiry - current_date).days


# ─────────────────────────────────────────────────────────────────────────────
# Vanilla Options
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EuropeanCall(Option):
    """European call option – exercise only at maturity."""

    exercise_style: ExerciseStyle = ExerciseStyle.EUROPEAN

    def payoff(self, spot: float) -> float:
        return max(spot - self.strike, 0.0) * self.contract_multiplier

    def option_type(self) -> str:
        return "call"

    def current_intrinsic(self) -> float:
        return max(self.equity.current_price - self.strike, 0.0) * self.contract_multiplier

    def __repr__(self) -> str:
        return f"EuCall({self.underlying_ticker!r}, K={self.strike:.2f}, T={self.expiry:%Y-%m-%d})"


@dataclass(frozen=True)
class EuropeanPut(Option):
    """European put option – exercise only at maturity."""

    exercise_style: ExerciseStyle = ExerciseStyle.EUROPEAN

    def payoff(self, spot: float) -> float:
        return max(self.strike - spot, 0.0) * self.contract_multiplier

    def option_type(self) -> str:
        return "put"

    def current_intrinsic(self) -> float:
        return max(self.strike - self.equity.current_price, 0.0) * self.contract_multiplier

    def __repr__(self) -> str:
        return f"EuPut({self.underlying_ticker!r}, K={self.strike:.2f}, T={self.expiry:%Y-%m-%d})"


@dataclass(frozen=True)
class AmericanCall(Option):
    """American call option – early exercise possible."""

    exercise_style: ExerciseStyle = ExerciseStyle.AMERICAN

    def payoff(self, spot: float) -> float:
        return max(spot - self.strike, 0.0) * self.contract_multiplier

    def option_type(self) -> str:
        return "call"

    def current_intrinsic(self) -> float:
        return max(self.equity.current_price - self.strike, 0.0) * self.contract_multiplier

    def __repr__(self) -> str:
        return f"AmCall({self.underlying_ticker!r}, K={self.strike:.2f}, T={self.expiry:%Y-%m-%d})"


@dataclass(frozen=True)
class AmericanPut(Option):
    """American put option – early exercise possible."""

    exercise_style: ExerciseStyle = ExerciseStyle.AMERICAN

    def payoff(self, spot: float) -> float:
        return max(self.strike - spot, 0.0) * self.contract_multiplier

    def option_type(self) -> str:
        return "put"

    def current_intrinsic(self) -> float:
        return max(self.strike - self.equity.current_price, 0.0) * self.contract_multiplier

    def __repr__(self) -> str:
        return f"AmPut({self.underlying_ticker!r}, K={self.strike:.2f}, T={self.expiry:%Y-%m-%d})"


# ─────────────────────────────────────────────────────────────────────────────
# Exotic Options – Working
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DigitalCall(Option):
    """Digital (cash-or-nothing) call – pays cash_amount if spot > strike at expiry."""

    cash_amount: float = 1.0

    def payoff(self, spot: float) -> float:
        return self.cash_amount if spot > self.strike else 0.0

    def option_type(self) -> str:
        return "call"

    @property
    def is_path_dependent(self) -> bool:
        return False

    def current_intrinsic(self) -> float:
        return self.cash_amount if self.equity.current_price > self.strike else 0.0

    def __repr__(self) -> str:
        return (
            f"DigitalCall({self.underlying_ticker!r}, K={self.strike:.2f}, "
            f"T={self.expiry:%Y-%m-%d}, cash={self.cash_amount})"
        )


@dataclass(frozen=True)
class DigitalPut(Option):
    """Digital (cash-or-nothing) put – pays cash_amount if spot < strike at expiry."""

    cash_amount: float = 1.0

    def payoff(self, spot: float) -> float:
        return self.cash_amount if spot < self.strike else 0.0

    def option_type(self) -> str:
        return "put"

    @property
    def is_path_dependent(self) -> bool:
        return False

    def current_intrinsic(self) -> float:
        return self.cash_amount if self.equity.current_price < self.strike else 0.0

    def __repr__(self) -> str:
        return (
            f"DigitalPut({self.underlying_ticker!r}, K={self.strike:.2f}, "
            f"T={self.expiry:%Y-%m-%d}, cash={self.cash_amount})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Exotic Options – Placeholders
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BarrierCall(Option):
    """Down-and-Out barrier call – placeholder. Real payoff requires price path."""

    barrier: float = 0.0  # knock-out level

    def payoff(self, spot: float) -> float:
        # PLACEHOLDER: true payoff needs full price path to check barrier breach.
        # Returns standard call payoff; real pricing needs simulation.
        return max(spot - self.strike, 0.0) * self.contract_multiplier

    def option_type(self) -> str:
        return "call"

    @property
    def is_path_dependent(self) -> bool:
        return True

    def current_intrinsic(self) -> float:
        return max(self.equity.current_price - self.strike, 0.0) * self.contract_multiplier

    def __repr__(self) -> str:
        return (
            f"BarrierCall({self.underlying_ticker!r}, K={self.strike:.2f}, "
            f"B={self.barrier:.2f}, T={self.expiry:%Y-%m-%d})"
        )


@dataclass(frozen=True)
class BarrierPut(Option):
    """Down-and-Out barrier put – placeholder. Real payoff requires price path."""

    barrier: float = 0.0  # knock-out level

    def payoff(self, spot: float) -> float:
        # PLACEHOLDER: true payoff needs full price path to check barrier breach.
        return max(self.strike - spot, 0.0) * self.contract_multiplier

    def option_type(self) -> str:
        return "put"

    @property
    def is_path_dependent(self) -> bool:
        return True

    def current_intrinsic(self) -> float:
        return max(self.strike - self.equity.current_price, 0.0) * self.contract_multiplier

    def __repr__(self) -> str:
        return (
            f"BarrierPut({self.underlying_ticker!r}, K={self.strike:.2f}, "
            f"B={self.barrier:.2f}, T={self.expiry:%Y-%m-%d})"
        )


@dataclass(frozen=True)
class LookbackCall(Option):
    """Lookback call (fixed strike) – placeholder. Real payoff requires max spot from path."""

    def payoff(self, spot: float) -> float:
        # PLACEHOLDER: true payoff needs max(spot) over option lifetime from simulation.
        return max(spot - self.strike, 0.0) * self.contract_multiplier

    def option_type(self) -> str:
        return "call"

    @property
    def is_path_dependent(self) -> bool:
        return True

    def current_intrinsic(self) -> float:
        return max(self.equity.current_price - self.strike, 0.0) * self.contract_multiplier

    def __repr__(self) -> str:
        return (
            f"LookbackCall({self.underlying_ticker!r}, K={self.strike:.2f}, "
            f"T={self.expiry:%Y-%m-%d})"
        )


@dataclass(frozen=True)
class LookbackPut(Option):
    """Lookback put (fixed strike) – placeholder. Real payoff requires min spot from path."""

    def payoff(self, spot: float) -> float:
        # PLACEHOLDER: true payoff needs min(spot) over option lifetime from simulation.
        return max(self.strike - spot, 0.0) * self.contract_multiplier

    def option_type(self) -> str:
        return "put"

    @property
    def is_path_dependent(self) -> bool:
        return True

    def current_intrinsic(self) -> float:
        return max(self.strike - self.equity.current_price, 0.0) * self.contract_multiplier

    def __repr__(self) -> str:
        return (
            f"LookbackPut({self.underlying_ticker!r}, K={self.strike:.2f}, "
            f"T={self.expiry:%Y-%m-%d})"
        )
