# tests/test_portfolio.py
"""Tests for Portfolio, Position, and Equity backtesting foundations."""

from datetime import date, timedelta

import pytest

from quant_finance.core.asset_class import AssetClass
from quant_finance.instruments.equity.equity import Equity
from quant_finance.instruments.portfolio.portfolio import (
    Portfolio,
    Trade,
    TradeSide,
)
from quant_finance.instruments.portfolio.position import Position


class TestEquity:
    """Tests for Equity instrument."""

    def test_create_equity(self):
        equity = Equity(ticker="AAPL", current_price=150.0, dividend_yield=0.005)
        assert equity.ticker == "AAPL"
        assert equity.current_price == 150.0
        assert equity.dividend_yield == 0.005
        assert equity.asset_class == AssetClass.EQUITY

    def test_update_price(self):
        equity = Equity(ticker="AAPL", current_price=150.0)
        equity.update_price(new_price=155.0)
        assert equity.current_price == 155.0

    def test_update_price_with_history(self):
        equity = Equity(ticker="AAPL", current_price=150.0)
        trade_date = date(2024, 1, 15)
        equity.update_price(new_price=155.0, as_of_date=trade_date)
        assert equity.current_price == 155.0
        assert equity.get_historical_price(trade_date) == 150.0

    def test_negative_price_rejected(self):
        equity = Equity(ticker="AAPL", current_price=150.0)
        with pytest.raises(ValueError, match="Price must be positive"):
            equity.update_price(new_price=-10.0)

    def test_constructor_negative_price_rejected(self):
        with pytest.raises(ValueError, match="Current price must be positive"):
            Equity(ticker="AAPL", current_price=-10.0)


class TestPosition:
    """Tests for Position."""

    def test_create_long_position(self):
        equity = Equity(ticker="AAPL", current_price=150.0)
        pos = Position(equity=equity, quantity=100, average_cost=145.0)
        assert pos.quantity == 100
        assert pos.average_cost == 145.0
        assert pos.market_value == 15000.0
        assert pos.cost_basis == 14500.0
        assert pos.unrealized_pnl() == 500.0

    def test_create_short_position(self):
        equity = Equity(ticker="AAPL", current_price=150.0)
        pos = Position(equity=equity, quantity=-50, average_cost=145.0)
        assert pos.market_value == -7500.0
        assert pos.unrealized_pnl() == -250.0  # short: gain when price falls

    def test_zero_quantity_rejected(self):
        equity = Equity(ticker="AAPL", current_price=150.0)
        with pytest.raises(ValueError, match="Quantity cannot be zero"):
            Position(equity=equity, quantity=0, average_cost=145.0)

    def test_unrealized_pnl_pct(self):
        equity = Equity(ticker="AAPL", current_price=160.0)
        pos = Position(equity=equity, quantity=100, average_cost=145.0)
        assert pos.unrealized_pnl() == 1500.0
        assert pos.unrealized_pnl_pct() == pytest.approx(10.3448, rel=1e-3)

    def test_position_with_entry_date(self):
        equity = Equity(ticker="AAPL", current_price=150.0)
        entry = date(2024, 1, 1)
        pos = Position(equity=equity, quantity=100, average_cost=145.0, entry_date=entry)
        days = pos.holding_period_days(date(2024, 1, 11))
        assert days == 10

    def test_position_to_dict(self):
        equity = Equity(ticker="AAPL", current_price=155.0)
        pos = Position(equity=equity, quantity=100, average_cost=145.0)
        d = pos.to_dict()
        assert d["ticker"] == "AAPL"
        assert d["quantity"] == 100
        assert d["average_cost"] == 145.0
        assert d["market_value"] == 15500.0
        assert d["unrealized_pnl"] == 1000.0


class TestPortfolio:
    """Tests for Portfolio backtesting operations."""

    def test_empty_portfolio(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        assert portfolio.total_value() == 100_000.0
        assert portfolio.total_unrealized_pnl == 0.0
        assert portfolio.total_realized_pnl == 0.0
        assert portfolio.holdings() == []

    def test_record_buy_trade(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        equity = Equity(ticker="AAPL", current_price=150.0)

        trade = Trade(
            ticker="AAPL",
            side=TradeSide.BUY,
            quantity=100,
            price=150.0,
            trade_date=date(2024, 1, 1),
        )
        portfolio.record_trade(trade, equity=equity)

        assert "AAPL" in portfolio.positions
        assert portfolio.positions["AAPL"].quantity == 100
        assert portfolio.positions["AAPL"].average_cost == 150.0
        assert portfolio.cash == 100_000.0 - 15_000.0

    def test_record_sell_trade_realized_pnl(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        equity = Equity(ticker="AAPL", current_price=150.0)

        # Buy at $145
        buy_trade = Trade(
            ticker="AAPL",
            side=TradeSide.BUY,
            quantity=100,
            price=145.0,
            trade_date=date(2024, 1, 1),
        )
        portfolio.record_trade(buy_trade, equity=equity)

        # Sell at $160 → realized P&L = (160 - 145) * 100 = $1,500
        sell_trade = Trade(
            ticker="AAPL",
            side=TradeSide.SELL,
            quantity=100,
            price=160.0,
            trade_date=date(2024, 2, 1),
        )
        portfolio.record_trade(sell_trade, equity=equity)

        assert "AAPL" not in portfolio.positions  # fully closed
        assert portfolio.total_realized_pnl == 1_500.0

    def test_partial_sell(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        equity = Equity(ticker="AAPL", current_price=150.0)

        buy_trade = Trade(
            ticker="AAPL",
            side=TradeSide.BUY,
            quantity=100,
            price=145.0,
            trade_date=date(2024, 1, 1),
        )
        portfolio.record_trade(buy_trade, equity=equity)

        sell_trade = Trade(
            ticker="AAPL",
            side=TradeSide.SELL,
            quantity=40,
            price=160.0,
            trade_date=date(2024, 2, 1),
        )
        portfolio.record_trade(sell_trade, equity=equity)

        assert portfolio.positions["AAPL"].quantity == 60
        assert portfolio.positions["AAPL"].average_cost == 145.0
        assert portfolio.total_realized_pnl == (160.0 - 145.0) * 40

    def test_sell_more_than_held_rejected(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        equity = Equity(ticker="AAPL", current_price=150.0)

        buy_trade = Trade(
            ticker="AAPL",
            side=TradeSide.BUY,
            quantity=100,
            price=145.0,
            trade_date=date(2024, 1, 1),
        )
        portfolio.record_trade(buy_trade, equity=equity)

        sell_trade = Trade(
            ticker="AAPL",
            side=TradeSide.SELL,
            quantity=150,
            price=160.0,
            trade_date=date(2024, 2, 1),
        )
        with pytest.raises(ValueError, match="Cannot sell"):
            portfolio.record_trade(sell_trade, equity=equity)

    def test_unrealized_pnl_with_price_update(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        equity = Equity(ticker="AAPL", current_price=150.0)

        buy_trade = Trade(
            ticker="AAPL",
            side=TradeSide.BUY,
            quantity=100,
            price=145.0,
            trade_date=date(2024, 1, 1),
        )
        portfolio.record_trade(buy_trade, equity=equity)

        # Price rises → unrealized P&L increases
        portfolio.update_prices({"AAPL": 160.0})
        assert portfolio.total_unrealized_pnl == (160.0 - 145.0) * 100

    def test_update_prices_with_history(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        equity = Equity(ticker="AAPL", current_price=150.0)

        buy_trade = Trade(
            ticker="AAPL",
            side=TradeSide.BUY,
            quantity=100,
            price=145.0,
            trade_date=date(2024, 1, 1),
        )
        portfolio.record_trade(buy_trade, equity=equity)

        trade_date = date(2024, 2, 1)
        portfolio.update_prices({"AAPL": 160.0}, trade_date=trade_date)

        assert equity.current_price == 160.0
        assert equity.get_historical_price(trade_date) == 150.0

    def test_holdings(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        aapl = Equity(ticker="AAPL", current_price=150.0)
        msft = Equity(ticker="MSFT", current_price=400.0)

        portfolio.record_trade(
            Trade(ticker="AAPL", side=TradeSide.BUY, quantity=100, price=145.0, trade_date=date(2024, 1, 1)),
            equity=aapl,
        )
        portfolio.record_trade(
            Trade(ticker="MSFT", side=TradeSide.BUY, quantity=50, price=390.0, trade_date=date(2024, 1, 1)),
            equity=msft,
        )

        h = portfolio.holdings()
        assert len(h) == 2
        tickers = {pos["ticker"] for pos in h}
        assert tickers == {"AAPL", "MSFT"}

    def test_realized_pnl_by_ticker(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        equity = Equity(ticker="AAPL", current_price=150.0)

        portfolio.record_trade(
            Trade(ticker="AAPL", side=TradeSide.BUY, quantity=100, price=145.0, trade_date=date(2024, 1, 1)),
            equity=equity,
        )
        portfolio.record_trade(
            Trade(ticker="AAPL", side=TradeSide.SELL, quantity=60, price=160.0, trade_date=date(2024, 2, 1)),
            equity=equity,
        )

        realized = portfolio.realized_pnl_by_ticker()
        assert realized["AAPL"] == (160.0 - 145.0) * 60

    def test_summary(self):
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        equity = Equity(ticker="AAPL", current_price=150.0)

        portfolio.record_trade(
            Trade(ticker="AAPL", side=TradeSide.BUY, quantity=100, price=145.0, trade_date=date(2024, 1, 1)),
            equity=equity,
        )
        portfolio.update_prices({"AAPL": 160.0})

        s = portfolio.summary()
        assert s["name"] == "Test Portfolio"
        assert s["cash"] == 85_500.0
        assert s["positions_value"] == 16_000.0
        assert s["total_value"] == 101_500.0
        assert s["total_unrealized_pnl"] == 1_500.0
        assert s["num_positions"] == 1
        assert s["num_transactions"] == 1

    def test_set_date(self):
        portfolio = Portfolio(name="Test Portfolio")
        portfolio.set_date(date(2024, 3, 1))
        assert portfolio.current_date == date(2024, 3, 1)

    def test_multiple_buys_same_ticker(self):
        """Test averaging down/up across multiple buys."""
        portfolio = Portfolio(name="Test Portfolio", cash=100_000.0)
        equity = Equity(ticker="AAPL", current_price=150.0)

        portfolio.record_trade(
            Trade(ticker="AAPL", side=TradeSide.BUY, quantity=100, price=140.0, trade_date=date(2024, 1, 1)),
            equity=equity,
        )
        portfolio.record_trade(
            Trade(ticker="AAPL", side=TradeSide.BUY, quantity=50, price=150.0, trade_date=date(2024, 1, 15)),
            equity=equity,
        )

        pos = portfolio.positions["AAPL"]
        # (100*140 + 50*150) / 150 = (14000 + 7500) / 150 = 21500/150 = 143.33
        assert pos.quantity == 150
        assert pos.average_cost == pytest.approx(143.333, rel=1e-3)
