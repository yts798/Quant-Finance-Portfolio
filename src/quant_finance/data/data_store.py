# src/quant_finance/data/data_store.py

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set

from .equity_data import EquityData
from .price_bar import PriceBar


@dataclass
class DataStore:
    """In-memory store of price data for all tickers.

    Acts as the single source of truth for your backtest's market data.
    """

    data: Dict[str, EquityData] = field(default_factory=dict)
    _all_dates: List[date] = field(default_factory=list, repr=False)

    # ── Registration ──────────────────────────────────────────────────────────

    def add_ticker(self, equity_data: EquityData) -> None:
        """Register an EquityData object under its ticker."""
        self.data[equity_data.ticker] = equity_data
        self._rebuild_date_index()

    def add_tickers(self, equity_data_list: List[EquityData]) -> None:
        """Register multiple EquityData objects at once."""
        for ed in equity_data_list:
            self.add_ticker(ed)

    # ── Accessors ────────────────────────────────────────────────────────────

    def tickers(self) -> List[str]:
        """All registered tickers, sorted alphabetically."""
        return sorted(self.data.keys())

    def has_ticker(self, ticker: str) -> bool:
        return ticker in self.data

    def equity_data(self, ticker: str) -> EquityData:
        """Get EquityData for a ticker. Raises KeyError if not found."""
        return self.data[ticker]

    def get_price(self, ticker: str, trade_date: date) -> Optional[float]:
        """Adj-close price for ticker on trade_date, or None if no data."""
        return self.data[ticker].price_on(trade_date) if ticker in self.data else None

    def get_ohlcv(self, ticker: str, trade_date: date) -> Optional[PriceBar]:
        """Full OHLCV bar for ticker on trade_date."""
        return self.data[ticker].ohlcv_on(trade_date) if ticker in self.data else None

    def has_date(self, trade_date: date) -> bool:
        """True if at least one ticker has data on this date."""
        return trade_date in self._all_dates

    # ── Date index ───────────────────────────────────────────────────────────

    def dates(self) -> List[date]:
        """All dates where at least one ticker has data, sorted ascending."""
        return list(self._all_dates)

    def trading_dates(
        self,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> List[date]:
        """All trading dates in [start, end] inclusive that have data.

        If start/end are None, returns all dates.
        """
        dates = self._all_dates
        if not dates:
            return []
        lo = 0 if start is None else bisect.bisect_left(dates, start)
        hi = len(dates) if end is None else bisect.bisect_right(dates, end)
        return dates[lo:hi]

    def next_trading_date(self, trade_date: date) -> Optional[date]:
        """The next date in the store on or after trade_date."""
        idx = bisect.bisect_right(self._all_dates, trade_date)
        return self._all_dates[idx] if idx < len(self._all_dates) else None

    def prev_trading_date(self, trade_date: date) -> Optional[date]:
        """The previous date in the store on or before trade_date."""
        idx = bisect.bisect_left(self._all_dates, trade_date) - 1
        return self._all_dates[idx] if idx >= 0 else None

    # ── Bulk updates ──────────────────────────────────────────────────────────

    def update_portfolio_prices(
        self,
        portfolio,
        trade_date: date,
        tickers: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """Update all Equity.current_price for a portfolio on a given date.

        Args:
            portfolio: Portfolio instance with Equity objects in its positions
            trade_date: date to update prices to
            tickers: if None, updates all positions; if provided, only those tickers

        Returns:
            Dict mapping ticker → whether update succeeded (False = no data for that date)
        """
        tickers_to_update = tickers or list(portfolio.positions.keys())
        result = {}
        for ticker in tickers_to_update:
            if ticker in self.data:
                success = self.data[ticker].update_equity_price(
                    portfolio.positions[ticker].equity,
                    trade_date,
                )
                result[ticker] = success
            else:
                result[ticker] = False
        return result

    # ── Summary ──────────────────────────────────────────────────────────────

    def summary(self) -> Dict:
        """Summary of all tickers and date range."""
        tickers = self.tickers()
        if not tickers:
            return {"tickers": [], "date_range": None, "total_bars": 0}
        all_dates = self._all_dates
        return {
            "tickers": tickers,
            "num_tickers": len(tickers),
            "date_range": (
                (all_dates[0].isoformat(), all_dates[-1].isoformat())
                if all_dates else None
            ),
            "num_trading_days": len(all_dates),
            "total_bars": sum(len(ed) for ed in self.data.values()),
            "bars_per_ticker": {
                ticker: len(self.data[ticker])
                for ticker in tickers
            },
        }

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        n = len(self.data)
        if n == 0:
            return "DataStore(empty)"
        return f"DataStore({n} tickers, {len(self._all_dates)} dates)"

    # ── Internal ─────────────────────────────────────────────────────────────

    def _rebuild_date_index(self) -> None:
        """Rebuild the union of all dates from all tickers."""
        all_dates: Set[date] = set()
        for ed in self.data.values():
            all_dates.update(ed.dates())
        self._all_dates = sorted(all_dates)
