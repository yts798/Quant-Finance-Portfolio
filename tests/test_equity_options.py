# tests/test_equity_options.py
"""Tests for Equity and Option instruments."""

from datetime import date

from quant_finance.instruments.equity import (
    Equity,
    EuropeanCall,
    EuropeanPut,
    AmericanCall,
    DigitalCall,
    DigitalPut,
    BarrierCall,
    BarrierPut,
    LookbackCall,
    LookbackPut,
)


class TestEquity:
    def test_equity_price_updates(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        assert aapl.current_price == 150.0

        aapl.update_price(155.0)
        assert aapl.current_price == 155.0

    def test_equity_price_history(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        trade_date = date(2024, 1, 15)
        aapl.update_price(new_price=155.0, as_of_date=trade_date)
        assert aapl.get_historical_price(trade_date) == 150.0
        assert aapl.current_price == 155.0


class TestDigitalCall:
    def test_itm_pays(self):
        aapl = Equity(ticker="AAPL", current_price=160.0)
        dc = DigitalCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), cash_amount=100.0)
        assert dc.current_intrinsic() == 100.0
        assert dc.payoff(160.0) == 100.0

    def test_otm_pays_zero(self):
        aapl = Equity(ticker="AAPL", current_price=140.0)
        dc = DigitalCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), cash_amount=100.0)
        assert dc.current_intrinsic() == 0.0
        assert dc.payoff(140.0) == 0.0

    def test_at_strike_is_zero(self):
        aapl = Equity(ticker="AAPL", current_price=145.0)
        dc = DigitalCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), cash_amount=100.0)
        # Digital call: spot > strike → pays; spot <= strike → 0
        assert dc.payoff(145.0) == 0.0

    def test_repr(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        dc = DigitalCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), cash_amount=100.0)
        assert "DigitalCall" in repr(dc)
        assert "AAPL" in repr(dc)

    def test_option_type_and_path_dep(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        dc = DigitalCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert dc.option_type() == "call"
        assert dc.is_path_dependent is False
        assert dc.requires_simulation() is False


class TestDigitalPut:
    def test_itm_pays(self):
        aapl = Equity(ticker="AAPL", current_price=140.0)
        dp = DigitalPut(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), cash_amount=100.0)
        assert dp.current_intrinsic() == 100.0
        assert dp.payoff(140.0) == 100.0

    def test_otm_pays_zero(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        dp = DigitalPut(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), cash_amount=100.0)
        assert dp.current_intrinsic() == 0.0
        assert dp.payoff(150.0) == 0.0

    def test_at_strike_is_zero(self):
        aapl = Equity(ticker="AAPL", current_price=145.0)
        dp = DigitalPut(equity=aapl, strike=145.0, expiry=date(2025, 6, 15), cash_amount=100.0)
        # Digital put: spot < strike → pays; spot >= strike → 0
        assert dp.payoff(145.0) == 0.0

    def test_option_type_and_path_dep(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        dp = DigitalPut(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert dp.option_type() == "put"
        assert dp.is_path_dependent is False
        assert dp.requires_simulation() is False


class TestVanillaOptions:
    def test_european_call_intrinsic(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        call = EuropeanCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert call.current_intrinsic() == 500.0  # (150-145) * 1 * 100

    def test_european_put_intrinsic(self):
        aapl = Equity(ticker="AAPL", current_price=140.0)
        put = EuropeanPut(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert put.current_intrinsic() == 500.0  # (145-140) * 1 * 100

    def test_american_call_path_dependent(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        amc = AmericanCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert amc.is_path_dependent is True
        assert amc.requires_simulation() is True

    def test_european_call_not_path_dependent(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        ec = EuropeanCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert ec.is_path_dependent is False
        assert ec.requires_simulation() is False

    def test_put_payoff(self):
        aapl = Equity(ticker="AAPL", current_price=140.0)
        put = EuropeanPut(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert put.payoff(140.0) == 500.0  # (145-140)*100
        assert put.payoff(150.0) == 0.0    # OTM

    def test_call_payoff(self):
        aapl = Equity(ticker="AAPL", current_price=160.0)
        call = EuropeanCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert call.payoff(160.0) == 1500.0  # (160-145)*100
        assert call.payoff(140.0) == 0.0     # OTM


class TestExoticPlaceholders:
    def test_barrier_call_repr(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        bc = BarrierCall(equity=aapl, strike=145.0, barrier=130.0, expiry=date(2025, 6, 15))
        assert "BarrierCall" in repr(bc)
        assert "AAPL" in repr(bc)

    def test_barrier_put_repr(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        bp = BarrierPut(equity=aapl, strike=155.0, barrier=160.0, expiry=date(2025, 6, 15))
        assert "BarrierPut" in repr(bp)

    def test_lookback_call_repr(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        lc = LookbackCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert "LookbackCall" in repr(lc)

    def test_lookback_put_repr(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        lp = LookbackPut(equity=aapl, strike=155.0, expiry=date(2025, 6, 15))
        assert "LookbackPut" in repr(lp)

    def test_barrier_is_path_dependent(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        bc = BarrierCall(equity=aapl, strike=145.0, barrier=130.0, expiry=date(2025, 6, 15))
        assert bc.is_path_dependent is True
        assert bc.requires_simulation() is True

    def test_lookback_is_path_dependent(self):
        aapl = Equity(ticker="AAPL", current_price=150.0)
        lc = LookbackCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        assert lc.is_path_dependent is True
        assert lc.requires_simulation() is True

    def test_all_share_same_equity(self):
        """All option types referencing same underlying share the same Equity object."""
        aapl = Equity(ticker="AAPL", current_price=150.0)
        opts = [
            EuropeanCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15)),
            EuropeanPut(equity=aapl, strike=155.0, expiry=date(2025, 6, 15)),
            DigitalCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15)),
            DigitalPut(equity=aapl, strike=155.0, expiry=date(2025, 6, 15)),
            BarrierCall(equity=aapl, strike=145.0, barrier=130.0, expiry=date(2025, 6, 15)),
            BarrierPut(equity=aapl, strike=155.0, barrier=160.0, expiry=date(2025, 6, 15)),
            LookbackCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15)),
            LookbackPut(equity=aapl, strike=155.0, expiry=date(2025, 6, 15)),
        ]
        for opt in opts:
            assert opt.equity is aapl
            assert opt.current_spot == 150.0

    def test_price_update_propagates(self):
        """Changing equity price updates all option intrinsics."""
        aapl = Equity(ticker="AAPL", current_price=140.0)
        call = EuropeanCall(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))
        put = EuropeanPut(equity=aapl, strike=145.0, expiry=date(2025, 6, 15))

        assert call.current_intrinsic() == 0.0  # OTM
        assert put.current_intrinsic() == 500.0  # ITM

        aapl.update_price(160.0)

        assert call.current_intrinsic() == 1500.0  # now ITM
        assert put.current_intrinsic() == 0.0       # now OTM
