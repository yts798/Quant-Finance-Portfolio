# src/quant_finance/data/data_loader.py

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yfinance as yf

from .data_store import DataStore
from .equity_data import EquityData
from .price_bar import PriceBar


class DataLoader:
    """Downloads US equity data from Yahoo Finance and stores to Parquet.

    Usage:
        loader = DataLoader()
        loader.download(["AAPL", "MSFT"], start="2025-01-01", end="2025-12-31")
        loader.save_all("data/")
        store = loader.to_store()

        # Or load from disk:
        store = DataLoader.load_store(["AAPL", "MSFT"], "data/")
    """

    def __init__(self):
        self._cache: Dict[str, pd.DataFrame] = {}  # ticker → raw yfinance DataFrame

    # ── Download ─────────────────────────────────────────────────────────────

    def download(
        self,
        tickers: Union[str, List[str]],
        start: Union[str, date],
        end: Union[str, date],
        progress: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """Download OHLCV data from Yahoo Finance.

        Args:
            tickers: single ticker str or list of tickers
            start: start date (str "YYYY-MM-DD" or date)
            end: end date (str "YYYY-MM-DD" or date)
            progress: whether to show yfinance progress bar

        Returns:
            Dict mapping ticker → raw yfinance DataFrame (indexed by date)
        """
        if isinstance(tickers, str):
            tickers = [tickers]

        # yfinance download
        df = yf.download(
            tickers=tickers,
            start=start,
            end=end,
            progress=progress,
            auto_adjust=False,  # keep adj_close column
        )

        # yfinance returns a MultiIndex (Ticker, Date) when multiple tickers
        if isinstance(df.columns, pd.MultiIndex):
            for ticker in tickers:
                self._cache[ticker] = df[ticker].reset_index()
        else:
            # Single ticker — df.columns is a simple Index
            self._cache[tickers[0]] = df.reset_index()

        return self._cache

    def download_one(
        self,
        ticker: str,
        start: Union[str, date],
        end: Union[str, date],
    ) -> pd.DataFrame:
        """Download data for a single ticker. Returns raw DataFrame."""
        result = self.download([ticker], start=start, end=end)
        return result[ticker]

    # ── Convert to PriceBar ──────────────────────────────────────────────────

    def to_price_bars(self, ticker: str) -> List[PriceBar]:
        """Convert a cached yfinance DataFrame to a list of PriceBar."""
        if ticker not in self._cache:
            raise ValueError(f"No cached data for {ticker}. Call download() first.")

        df = self._cache[ticker]
        bars = []

        for _, row in df.iterrows():
            trade_date = row["Date"].date() if hasattr(row["Date"], "date") else row["Date"]

            bar = PriceBar(
                date=trade_date,
                open_=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                adj_close=float(row["Adj Close"]),
                volume=float(row["Volume"]),
                dividend=float(row.get("Dividends", 0.0)),
            )
            bars.append(bar)

        return bars

    def to_equity_data(self, ticker: str) -> EquityData:
        """Convert cached yfinance data to EquityData."""
        bars = self.to_price_bars(ticker)
        ed = EquityData(ticker=ticker)
        ed.add_bars(bars)
        return ed

    def to_store(self, tickers: Optional[List[str]] = None) -> DataStore:
        """Build a DataStore from all cached tickers (or a subset)."""
        store = DataStore()
        keys = tickers or list(self._cache.keys())
        for ticker in keys:
            if ticker in self._cache:
                store.add_ticker(self.to_equity_data(ticker))
        return store

    # ── Download + save ──────────────────────────────────────────────────────

    def download_and_save(
        self,
        tickers: Union[str, List[str]],
        start: Union[str, date],
        end: Union[str, date],
        directory: Union[str, Path],
        progress: bool = True,
    ) -> DataStore:
        """Convenience: download → save parquet → return DataStore."""
        self.download(tickers, start=start, end=end, progress=progress)
        self.save_all(directory)
        return self.to_store()

    # ── Parquet I/O ──────────────────────────────────────────────────────────

    PARQUET_SCHEMA = pa.schema(
        [
            ("date", pa.date32()),
            ("open_", pa.float64()),
            ("high", pa.float64()),
            ("low", pa.float64()),
            ("close", pa.float64()),
            ("adj_close", pa.float64()),
            ("volume", pa.float64()),
            ("dividend", pa.float64()),
        ]
    )

    def save(self, ticker: str, filepath: Union[str, Path]) -> None:
        """Save one ticker's cached data to a Parquet file.

        Raises ValueError if ticker not in cache.
        """
        if ticker not in self._cache:
            raise ValueError(f"No cached data for {ticker}. Call download() first.")

        df = self._cache[ticker].copy()
        df["date"] = pd.to_datetime(df["Date"]).dt.date
        df = df.rename(columns={"Dividends": "dividend"})
        table = pa.Table.from_pandas(df[["date", "open_", "high", "low", "close", "adj_close", "volume", "dividend"]], schema=self.PARQUET_SCHEMA)
        pq.write_table(table, filepath, version="2.6")

    def save_all(self, directory: Union[str, Path]) -> Dict[str, Path]:
        """Save all cached tickers to individual Parquet files.

        Files are named {ticker}.parquet inside the given directory.
        Returns dict mapping ticker → filepath.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        saved = {}
        for ticker in self._cache:
            filepath = directory / f"{ticker}.parquet"
            self.save(ticker, filepath)
            saved[ticker] = filepath

        return saved

    # ── Parquet load ──────────────────────────────────────────────────────────

    @staticmethod
    def load(ticker: str, filepath: Union[str, Path]) -> EquityData:
        """Load one ticker's data from a Parquet file into EquityData."""
        filepath = Path(filepath)
        table = pq.read_table(filepath)
        df = table.to_pandas()

        bars = []
        for _, row in df.iterrows():
            bar = PriceBar(
                date=row["date"].date() if hasattr(row["date"], "date") else row["date"],
                open_=float(row["open_"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                adj_close=float(row["adj_close"]),
                volume=float(row["volume"]),
                dividend=float(row.get("dividend", 0.0)),
            )
            bars.append(bar)

        ed = EquityData(ticker=ticker)
        ed.add_bars(bars)
        return ed

    @staticmethod
    def load_store(
        tickers: Optional[List[str]],
        directory: Union[str, Path],
    ) -> DataStore:
        """Load all .parquet files from a directory into a DataStore.

        If tickers is None, loads every .parquet file found.
        """
        directory = Path(directory)
        store = DataStore()

        if tickers is None:
            tickers = [p.stem for p in directory.glob("*.parquet")]

        for ticker in tickers:
            filepath = directory / f"{ticker}.parquet"
            if filepath.exists():
                store.add_ticker(DataLoader.load(ticker, filepath))

        return store
