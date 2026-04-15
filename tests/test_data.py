# tests/test_data.py
"""Tests for the data layer: PriceBar, EquityData, DataStore, DataLoader."""

import pytest
from datetime import date, timedelta

from quant_finance.data import PriceBar, EquityData, DataStore, DataLoader


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_bar(d: date, close: float, open_=None, high=None, low=None, vol=1e6, div=0.0) -> PriceBar:
    o = open_ if open_ is not None else close
    h = high if high is not None else close * 1.01
    l = low if low is not None else close * 0.99
    return PriceBar(
        date=d, open_=o, high=h, low=l,
        close=close, adj_close=close, volume=vol, dividend=div
    )


def apple_bars() -> EquityData:
    """5 business days: Mon 6 Jan → Fri 10 Jan 2025."""
    ed = EquityData(ticker="AAPL")
    base = date(2025, 1, 6)  # Monday
    prices = [185.0, 188.0, 187.0, 190.0, 189.0]
    for i, p in enumerate(prices):
        ed.add_bars([make_bar(base + timedelta(days=i), p)])
    return ed


# ─────────────────────────────────────────────────────────────────────────────
# PriceBar
# ─────────────────────────────────────────────────────────────────────────────

class TestPriceBar:
    def test_creation(self):
        bar = make_bar(date(2025, 1, 2), close=150.0, open_=148.0, high=151.0, low=147.0)
        assert bar.close == 150.0
        assert bar.adj_close == 150.0

    def test_typical_price(self):
        bar = make_bar(date(2025, 1, 2), close=150.0, high=152.0, low=148.0)
        assert bar.typical_price == pytest.approx((152.0 + 148.0 + 150.0) / 3)

    def test_hl_range(self):
        bar = make_bar(date(2025, 1, 2), close=150.0, high=152.0, low=148.0)
        assert bar.hl_range == 4.0

    def test_total_return(self):
        bar = make_bar(date(2025, 1, 2), close=155.0)
        assert bar.total_return(150.0) == pytest.approx(5.0 / 150.0)

    def test_invalid_open_rejected(self):
        with pytest.raises(ValueError, match="open_ must be between"):
            PriceBar(
                date=date(2025, 1, 2),
                open_=200.0,  # outside low-high range
                high=150.0,
                low=100.0,
                close=110.0,
                adj_close=110.0,
                volume=1e6,
            )

    def test_repr(self):
        bar = make_bar(date(2025, 1, 2), close=150.0)
        assert "2025-01-02" in repr(bar)
        assert "150" in repr(bar)


# ─────────────────────────────────────────────────────────────────────────────
# EquityData
# ─────────────────────────────────────────────────────────────────────────────

class TestEquityData:
    def test_add_single_bar(self):
        ed = EquityData(ticker="AAPL")
        bar = make_bar(date(2025, 1, 2), close=150.0)
        ed.add_bars([bar])
        assert len(ed) == 1
        assert ed.price_on(date(2025, 1, 2)) == 150.0

    def test_add_multiple_bars(self):
        ed = EquityData(ticker="AAPL")
        bars = [make_bar(date(2025, 1, 2) + timedelta(days=i), close=150.0 + i) for i in range(5)]
        ed.add_bars(bars)
        assert len(ed) == 5

    def test_price_on_missing_date(self):
        ed = apple_bars()
        assert ed.price_on(date(2024, 1, 1)) is None

    def test_ohlcv_on(self):
        ed = apple_bars()
        bar = ed.ohlcv_on(date(2025, 1, 6))
        assert bar is not None
        assert bar.close == 185.0

    def test_dates_sorted(self):
        ed = apple_bars()
        dates = ed.dates()
        assert dates == sorted(dates)

    def test_date_range(self):
        ed = apple_bars()
        # Dates Jan 6-10; query Jan 6-7
        result = ed.date_range(date(2025, 1, 6), date(2025, 1, 7))
        assert len(result) == 2

    def test_latest_and_earliest(self):
        ed = apple_bars()
        assert ed.earliest_date() == date(2025, 1, 6)
        assert ed.latest_date() == date(2025, 1, 10)

    def test_returns(self):
        ed = apple_bars()
        rets = ed.returns()  # lookback=1
        # (188-185)/185, (187-188)/188, (190-187)/187, (189-190)/190
        assert len(rets) == 4
        assert rets[0] == pytest.approx((188.0 - 185.0) / 185.0)

    def test_returns_lookback_2(self):
        ed = apple_bars()
        rets = ed.returns(lookback=2)
        assert len(rets) == 3

    def test_cumulative_return(self):
        ed = apple_bars()
        ret = ed.cumulative_return(date(2025, 1, 6), date(2025, 1, 10))
        # (189 - 185) / 185
        assert ret == pytest.approx((189.0 - 185.0) / 185.0)

    def test_cumulative_return_missing_date(self):
        ed = apple_bars()
        assert ed.cumulative_return(date(2024, 1, 1), date(2025, 1, 2)) is None

    def test_update_equity_price(self):
        from quant_finance.instruments.equity import Equity
        aapl = Equity(ticker="AAPL", current_price=100.0)
        ed = apple_bars()
        success = ed.update_equity_price(aapl, date(2025, 1, 7))
        assert success is True
        assert aapl.current_price == 188.0

    def test_update_equity_price_no_data(self):
        from quant_finance.instruments.equity import Equity
        aapl = Equity(ticker="AAPL", current_price=100.0)
        ed = apple_bars()
        success = ed.update_equity_price(aapl, date(2024, 1, 1))
        assert success is False
        assert aapl.current_price == 100.0  # unchanged

    def test_duplicate_bar_ignored(self):
        ed = EquityData(ticker="AAPL")
        bar = make_bar(date(2025, 1, 2), close=150.0)
        ed.add_bars([bar, bar])
        assert len(ed) == 1

    def test_summary(self):
        ed = apple_bars()
        s = ed.summary()
        assert s["ticker"] == "AAPL"
        assert s["bars"] == 5


# ─────────────────────────────────────────────────────────────────────────────
# DataStore
# ─────────────────────────────────────────────────────────────────────────────

class TestDataStore:
    def test_empty_store(self):
        store = DataStore()
        assert store.tickers() == []
        assert store.dates() == []
        assert len(store) == 0

    def test_add_ticker(self):
        store = DataStore()
        ed = apple_bars()
        store.add_ticker(ed)
        assert store.tickers() == ["AAPL"]
        assert "AAPL" in store.tickers()

    def test_add_multiple_tickers(self):
        store = DataStore()
        msft = EquityData(ticker="MSFT")
        msft.add_bars([make_bar(date(2025, 1, 2), close=400.0)])
        store.add_tickers([apple_bars(), msft])
        assert len(store) == 2
        assert set(store.tickers()) == {"AAPL", "MSFT"}

    def test_get_price(self):
        store = DataStore()
        store.add_ticker(apple_bars())
        assert store.get_price("AAPL", date(2025, 1, 7)) == 188.0
        assert store.get_price("AAPL", date(2024, 1, 1)) is None
        assert store.get_price("MSFT", date(2025, 1, 6)) is None  # no such ticker

    def test_get_ohlcv(self):
        store = DataStore()
        store.add_ticker(apple_bars())
        bar = store.get_ohlcv("AAPL", date(2025, 1, 7))
        assert bar is not None
        assert bar.close == 188.0

    def test_trading_dates(self):
        store = DataStore()
        store.add_ticker(apple_bars())
        dates = store.trading_dates()
        assert len(dates) == 5

    def test_trading_dates_with_start_end(self):
        store = DataStore()
        store.add_ticker(apple_bars())
        # Jan 6-10 in data; query Jan 7-9
        dates = store.trading_dates(start=date(2025, 1, 7), end=date(2025, 1, 9))
        assert dates == [date(2025, 1, 7), date(2025, 1, 8), date(2025, 1, 9)]

    def test_next_trading_date(self):
        store = DataStore()
        store.add_ticker(apple_bars())
        assert store.next_trading_date(date(2025, 1, 5)) == date(2025, 1, 6)  # Sun → Mon
        assert store.next_trading_date(date(2025, 1, 10)) is None  # past end

    def test_prev_trading_date(self):
        store = DataStore()
        store.add_ticker(apple_bars())
        assert store.prev_trading_date(date(2025, 1, 10)) == date(2025, 1, 9)  # prev trading day
        assert store.prev_trading_date(date(2025, 1, 1)) is None  # before start

    def test_update_portfolio_prices(self):
        from quant_finance.instruments.equity import Equity
        from quant_finance.instruments.portfolio import Portfolio

        aapl = Equity(ticker="AAPL", current_price=100.0)
        portfolio = Portfolio(cash=100_000.0)
        from quant_finance.instruments.portfolio import Trade, TradeSide
        portfolio.record_trade(
            Trade(ticker="AAPL", side=TradeSide.BUY, quantity=100,
                  price=185.0, trade_date=date(2025, 1, 6)),
            equity=aapl,
        )

        store = DataStore()
        store.add_ticker(apple_bars())

        result = store.update_portfolio_prices(portfolio, date(2025, 1, 7))
        assert result["AAPL"] is True
        assert aapl.current_price == 188.0
        assert portfolio.positions["AAPL"].market_value == 18800.0

    def test_update_portfolio_prices_partial_failure(self):
        from quant_finance.instruments.equity import Equity
        from quant_finance.instruments.portfolio import Portfolio, Trade, TradeSide

        aapl = Equity(ticker="AAPL", current_price=100.0)
        portfolio = Portfolio(cash=100_000.0)
        portfolio.record_trade(
            Trade(ticker="AAPL", side=TradeSide.BUY, quantity=100,
                  price=185.0, trade_date=date(2025, 1, 6)),
            equity=aapl,
        )

        store = DataStore()
        store.add_ticker(apple_bars())

        # Explicitly pass MSFT (not in store) alongside AAPL
        result = store.update_portfolio_prices(
            portfolio,
            date(2025, 1, 7),
            tickers=["AAPL", "MSFT"],
        )
        assert result["AAPL"] is True
        assert result["MSFT"] is False

    def test_summary(self):
        store = DataStore()
        store.add_ticker(apple_bars())
        msft = EquityData(ticker="MSFT")
        msft.add_bars([make_bar(date(2025, 1, 2), close=400.0)])
        store.add_ticker(msft)

        s = store.summary()
        assert s["num_tickers"] == 2
        assert s["total_bars"] == 6
        assert "AAPL" in s["tickers"]

    def test_repr(self):
        store = DataStore()
        store.add_ticker(apple_bars())
        r = repr(store)
        assert "1 tickers" in r
        assert "5 dates" in r  # 5 dates


# ─────────────────────────────────────────────────────────────────────────────
# DataLoader – Parquet round-trip (no network needed)
# ─────────────────────────────────────────────────────────────────────────────

class TestDataLoaderParquet:
    def test_save_and_load_parquet(self, tmp_path):
        ed = apple_bars()
        ticker = ed.ticker

        # Save via DataLoader (write the parquet file directly using pyarrow)
        import pyarrow as pa
        import pyarrow.parquet as pq

        rows = []
        for bar in [ed.ohlcv_on(d) for d in ed.dates()]:
            rows.append({
                "date": bar.date,
                "open_": bar.open_,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "adj_close": bar.adj_close,
                "volume": bar.volume,
                "dividend": bar.dividend,
            })
        table = pa.Table.from_pylist(rows)
        filepath = tmp_path / f"{ticker}.parquet"
        pq.write_table(table, str(filepath))

        # Load back via DataLoader
        loaded = DataLoader.load(ticker, filepath)
        assert loaded.ticker == "AAPL"
        assert len(loaded) == 5
        assert loaded.price_on(date(2025, 1, 7)) == 188.0

    def test_load_store_from_directory(self, tmp_path):
        import pyarrow as pa
        import pyarrow.parquet as pq

        # Write two parquet files
        for ticker, price in [("AAPL", 185.0), ("MSFT", 400.0)]:
            ed = EquityData(ticker=ticker)
            ed.add_bars([make_bar(date(2025, 1, 2), close=price)])
            rows = []
            for bar in [ed.ohlcv_on(d) for d in ed.dates()]:
                rows.append({
                    "date": bar.date, "open_": bar.open_, "high": bar.high,
                    "low": bar.low, "close": bar.close, "adj_close": bar.adj_close,
                    "volume": bar.volume, "dividend": bar.dividend,
                })
            table = pa.Table.from_pylist(rows)
            pq.write_table(table, str(tmp_path / f"{ticker}.parquet"))

        store = DataLoader.load_store(["AAPL", "MSFT"], tmp_path)
        assert len(store) == 2
        assert store.get_price("AAPL", date(2025, 1, 2)) == 185.0
        assert store.get_price("MSFT", date(2025, 1, 2)) == 400.0
