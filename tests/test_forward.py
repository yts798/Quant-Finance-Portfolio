# tests/test_forward.py
"""Tests for Forward instrument."""

from datetime import date

from quant_finance.instruments.equity import Equity, Forward, ForwardSide


class TestForward:
    def test_long_forward_payoff(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), side=ForwardSide.LONG)
        # Spot > strike → profit
        assert fwd.payoff(160.0) == 15.0
        # Spot < strike → loss
        assert fwd.payoff(140.0) == -5.0
        # Spot == strike → breakeven
        assert fwd.payoff(145.0) == 0.0

    def test_short_forward_payoff(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), side=ForwardSide.SHORT)
        # Short profits when spot falls
        assert fwd.payoff(140.0) == 5.0
        # Short loses when spot rises
        assert fwd.payoff(160.0) == -15.0
        # Breakeven
        assert fwd.payoff(145.0) == 0.0

    def test_current_value_live_from_equity(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert fwd.current_value == 5.0  # 150 - 145

        aapl.update_price(160.0)
        assert fwd.current_value == 15.0  # 160 - 145

    def test_current_spot_live_from_equity(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert fwd.current_spot == 150.0

        aapl.update_price(155.0)
        assert fwd.current_spot == 155.0

    def test_underlying_ticker_from_equity(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert fwd.underlying_ticker == "AAPL"

    def test_is_not_path_dependent(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert fwd.is_path_dependent() is False

    def test_expiry_days(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        today = date(2025, 4, 15)
        assert fwd.expiry_days(today) == 61

    def test_expiry_days_expired(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        after_expiry = date(2025, 7, 1)
        assert fwd.expiry_days(after_expiry) == 0

    def test_repr_long(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert "LongForward" in repr(fwd)
        assert "AAPL" in repr(fwd)

    def test_repr_short(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), side=ForwardSide.SHORT)
        assert "ShortForward" in repr(fwd)

    def test_negative_strike_rejected(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        with __import__("pytest").raises(ValueError, match="Strike must be positive"):
            Forward(equity=aapl, strike=-10.0, expiry=date(2025, 6, 15))

    def test_current_forward_value(self):
        """Mark-to-market using forward price instead of spot."""
        aapl = Equity(ticker="AAPL", current_price=150.0)
        fwd = Forward(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        # Forward price = 148, contract strike = 145 → long gains 3
        assert fwd.current_forward_value(148.0) == 3.0
        assert fwd.current_forward_value(142.0) == -3.0
