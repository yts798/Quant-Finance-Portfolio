# src/quant_finance/instruments/equity/equity_data.py

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

from .price_bar import PriceBar


@dataclass
class EquityData:
    """All price bars for a single ticker, indexed by date.

    Provides O(1) date lookups and efficient date-range queries.
    Bars are stored sorted by date internally.
    """

    ticker: str
    bars: Dict[date, PriceBar] = field(default_factory=dict)
    _sorted_dates: List[date] = field(default_factory=list, repr=False)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _insert_bar(self, bar: PriceBar) -> None:
        """Insert a bar and maintain sorted date index."""
        if bar.date in self.bars:
            return  # already inserted
        self.bars[bar.date] = bar
        bisect.insort(self._sorted_dates, bar.date)

    # ── Bulk operations ───────────────────────────────────────────────────────

    def add_bars(self, bars: List[PriceBar]) -> None:
        """Add multiple bars at once (more efficient than individual adds)."""
        for bar in bars:
            self._insert_bar(bar)

    # ── Queries ──────────────────────────────────────────────────────────────

    def price_on(self, trade_date: date) -> Optional[float]:
        """Adjusted close price on a given date, or None if no data."""
        bar = self.bars.get(trade_date)
        return bar.adj_close if bar else None

    def ohlcv_on(self, trade_date: date) -> Optional[PriceBar]:
        """Full OHLCV bar on a given date."""
        return self.bars.get(trade_date)

    def has_date(self, trade_date: date) -> bool:
        """True if data exists for this date."""
        return trade_date in self.bars

    def dates(self) -> List[date]:
        """All available dates, sorted ascending."""
        return list(self._sorted_dates)

    def date_range(self, start: date, end: date) -> List[date]:
        """All dates in [start, end] inclusive that have data."""
        left = bisect.bisect_left(self._sorted_dates, start)
        right = bisect.bisect_right(self._sorted_dates, end)
        return self._sorted_dates[left:right]

    def latest_date(self) -> Optional[date]:
        """Most recent date in the dataset."""
        return self._sorted_dates[-1] if self._sorted_dates else None

    def earliest_date(self) -> Optional[date]:
        """Earliest date in the dataset."""
        return self._sorted_dates[0] if self._sorted_dates else None

    # ── Returns & statistics ─────────────────────────────────────────────────

    def returns(self, lookback: int = 1) -> List[float]:
        """Simple returns for each day vs the prior `lookback` day.

        Returns list aligned with self.dates()[lookback:].
        """
        dates = self._sorted_dates
        if len(dates) <= lookback:
            return []

        result = []
        for i in range(lookback, len(dates)):
            prev_bar = self.bars[dates[i - lookback]]
            curr_bar = self.bars[dates[i]]
            ret = (curr_bar.adj_close - prev_bar.adj_close) / prev_bar.adj_close
            result.append(ret)
        return result

    def cumulative_return(self, start: date, end: date) -> Optional[float]:
        """Cumulative return from start to end date (inclusive)."""
        start_price = self.price_on(start)
        end_price = self.price_on(end)
        if start_price is None or end_price is None:
            return None
        return (end_price - start_price) / start_price

    def volatility(self, lookback: int = 20) -> Optional[float]:
        """Annualised volatility over the last `lookback` days.

        Uses simple daily returns and annualises by sqrt(252).
        """
        import statistics
        rets = self.returns(lookback=lookback)
        if len(rets) < 2:
            return None
        return statistics.stdev(rets) * (252 ** 0.5)

    # ── Update Equity instrument ─────────────────────────────────────────────

    def update_equity_price(self, equity, trade_date: date) -> bool:
        """Update an Equity instrument's current_price to this date's close.

        Returns True if updated, False if no data for that date.
        """
        bar = self.bars.get(trade_date)
        if bar is None:
            return False
        equity.update_price(bar.adj_close, trade_date)
        return True

    # ── Summary ──────────────────────────────────────────────────────────────

    def summary(self) -> Dict:
        """One-line summary of this ticker."""
        n = len(self.bars)
        if n == 0:
            return {"ticker": self.ticker, "bars": 0}
        return {
            "ticker": self.ticker,
            "bars": n,
            "start": self.earliest_date().isoformat() if self.earliest_date() else None,
            "end": self.latest_date().isoformat() if self.latest_date() else None,
        }

    def __len__(self) -> int:
        return len(self.bars)

    def __repr__(self) -> str:
        n = len(self.bars)
        if n == 0:
            return f"EquityData({self.ticker!r}, empty)"
        return (
            f"EquityData({self.ticker!r}, {n} bars "
            f"[{self.earliest_date()} → {self.latest_date()}])"
        )
