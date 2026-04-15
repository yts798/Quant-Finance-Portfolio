# src/quant_finance/data/price_bar.py

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class PriceBar:
    """Single OHLCV bar for one trading day.

    All prices are in the same currency as the asset.
    adj_close is the dividend/split-adjusted close — use this for returns.
    """

    date: date
    open_: float
    high: float
    low: float
    close: float
    adj_close: float  # adjusted close — use this for returns/backtesting
    volume: float
    dividend: float = 0.0  # dividend per share on ex-date

    def __post_init__(self) -> None:
        if self.date is None:
            raise ValueError("date cannot be None")
        if not (self.low <= self.open_ <= self.high):
            raise ValueError("open_ must be between low and high")
        if not (self.low <= self.close <= self.high):
            raise ValueError("close must be between low and high")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")

    @property
    def typical_price(self) -> float:
        """(High + Low + Close) / 3"""
        return (self.high + self.low + self.close) / 3.0

    @property
    def hl_range(self) -> float:
        """High - Low range."""
        return self.high - self.low

    @property
    def oc_range(self) -> float:
        """Absolute open - close range."""
        return abs(self.close - self.open_)

    def total_return(self, prev_adj_close: float) -> float:
        """Simple return from previous adjusted close to this adj_close."""
        return (self.adj_close - prev_adj_close) / prev_adj_close

    def __repr__(self) -> str:
        return (
            f"PriceBar({self.date:%Y-%m-%d}, "
            f"O={self.open_:.2f}, H={self.high:.2f}, L={self.low:.2f}, "
            f"C={self.close:.2f}, AdjC={self.adj_close:.2f}, V={self.volume:.0f})"
        )
