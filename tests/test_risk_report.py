# tests/test_risk_report.py
"""Tests for RiskReport risk metrics."""

import pytest
from datetime import date

from quant_finance.strategies import RiskReport


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _flat_results(start_nav: float, navs: list[float], start_date: date = date(2025, 1, 1)):
    """Build a results list from a flat NAV series."""
    return [{"date": start_date, "nav": navs[0]}]


def make_results(navs: list[float], start: date = date(2025, 1, 1)) -> list[dict]:
    return [{"date": start, "nav": nav} for nav in navs]


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestRiskReportBasics:
    def test_total_return(self):
        results = make_results([100_000.0, 110_000.0, 115_000.0])
        report = RiskReport.from_results(results, strategy_name="Test")
        assert report.start_nav == 100_000.0
        assert report.end_nav == 115_000.0
        assert abs(report.total_return_pct - 15.0) < 0.01

    def test_negative_return(self):
        results = make_results([100_000.0, 90_000.0, 85_000.0])
        report = RiskReport.from_results(results, strategy_name="Test")
        assert abs(report.total_return_pct - (-15.0)) < 0.01

    def test_cagr_single_period(self):
        """NAV goes from 100 to 121 in ~252 trading days → ~10% CAGR."""
        navs = [100_000.0] + [100_000.0 * (1.10 ** (i / 252)) for i in range(1, 253)]
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test")
        assert abs(report.annualized_return_pct - 10.0) < 1.0  # within 1%

    def test_trading_days_count(self):
        navs = [100_000.0] * 10
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test")
        assert report.trading_days == 10


class TestSharpeSortino:
    def test_sharpe_zero_volatility(self):
        """Flat NAV → zero std → Sharpe = 0 (guard against div-by-zero)."""
        results = make_results([100_000.0] * 20)
        report = RiskReport.from_results(results, strategy_name="Test", risk_free_rate=0.0)
        assert report.sharpe_ratio == 0.0

    def test_sharpe_with_positive_returns(self):
        """Constant 1% daily return → high Sharpe."""
        # 10 days: each day +1%
        navs = [100_000.0]
        for _ in range(9):
            navs.append(navs[-1] * 1.01)
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test", risk_free_rate=0.0)
        assert report.sharpe_ratio > 0

    def test_sortino_zero_when_all_positive(self):
        """No downside returns → Sortino = 0 (guard against div-by-zero)."""
        navs = [100_000.0]
        for _ in range(9):
            navs.append(navs[-1] * 1.01)
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test")
        assert report.sortino_ratio == 0.0

    def test_sortino_finite_with_losses(self):
        """With at least 2 downside returns, Sortino is computed."""
        # 6 days: +1%, -3%, +1%, -2%, +1%, +1%
        # Downside returns: -3%, -2%  (2 values → enough for downside std)
        navs = [100_000.0]
        navs.append(navs[-1] * 1.01)   # day 1
        navs.append(navs[-1] * 0.97)   # day 2  ← loss -3%
        navs.append(navs[-1] * 1.01)   # day 3
        navs.append(navs[-1] * 0.98)   # day 4  ← loss -2%
        navs.append(navs[-1] * 1.01)   # day 5
        navs.append(navs[-1] * 1.01)   # day 6
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test", risk_free_rate=0.0)
        assert report.sortino_ratio != 0.0  # computed, not zero


class TestDrawdown:
    def test_max_drawdown_simple(self):
        """NAV: 100 → 110 → 90 → 100 → 85 → 100."""
        # Day 0: 100_000 (peak)
        # Day 1: 110_000 (new peak 110)
        # Day 2: 90_000  (dd = -18.2%)
        # Day 3: 100_000 (new peak 110)
        # Day 4: 85_000  (dd = -22.7%)
        # Day 5: 100_000 (new peak 110)
        results = make_results([100_000.0, 110_000.0, 90_000.0, 100_000.0, 85_000.0, 100_000.0])
        report = RiskReport.from_results(results, strategy_name="Test")
        # Worst drawdown: 85/110 - 1 ≈ -22.7%
        assert report.max_drawdown_pct < -22.0
        assert report.max_drawdown_pct > -23.0

    def test_no_drawdown_climbing_nav(self):
        """Strictly climbing NAV → max_drawdown = 0."""
        navs = [100_000.0, 105_000.0, 110_000.0, 115_000.0]
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test")
        assert report.max_drawdown_pct == 0.0


class TestVaRCVaR:
    def test_var_95_one_percent_daily(self):
        """With 5% of 100 returns = 5 tail entries, VaR captures the -5% loss days."""
        # 101 navs → 100 daily returns. 5% of 100 = 5 → index 5 (0-based) = 6th worst
        # Place 6 losses at -5% in a sea of +1% days
        navs = [100_000.0]
        for i in range(100):
            if i == 20 or i == 40 or i == 60 or i == 70 or i == 80 or i == 90:
                navs.append(navs[-1] * 0.95)  # -5% loss days
            else:
                navs.append(navs[-1] * 1.01)  # +1% days
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test")
        assert report.var_95_pct > 4.0  # worst tail losses captured
        assert report.cvar_95_pct > 4.0

    def test_var_empty_returns(self):
        """Single NAV → no daily returns → VaR/CVaR = 0."""
        results = make_results([100_000.0])
        report = RiskReport.from_results(results, strategy_name="Test")
        assert report.var_95_pct == 0.0
        assert report.cvar_95_pct == 0.0


class TestWinRateProfitFactor:
    def test_win_rate_calculation(self):
        """5 days: +, +, -, +, -  → 60% win rate."""
        navs = [100_000.0]
        navs.append(navs[-1] * 1.02)   # +
        navs.append(navs[-1] * 1.02)   # +
        navs.append(navs[-1] * 0.98)   # -
        navs.append(navs[-1] * 1.02)   # +
        navs.append(navs[-1] * 0.98)   # -
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test")
        assert report.win_rate_pct == 60.0

    def test_profit_factor_all_winners(self):
        """All positive → profit factor = inf."""
        navs = [100_000.0]
        for _ in range(9):
            navs.append(navs[-1] * 1.01)
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test")
        assert report.profit_factor == float("inf")

    def test_profit_factor_all_losers(self):
        """All negative → profit factor = 0."""
        navs = [100_000.0]
        for _ in range(9):
            navs.append(navs[-1] * 0.99)
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test")
        assert report.profit_factor == 0.0


class TestBenchmark:
    def test_alpha_positive(self):
        """Strategy beats benchmark → positive alpha."""
        # Strategy: +10% cumulative
        strat_rets = [0.10]
        # Benchmark: +5% cumulative
        bench_rets = [0.05]
        navs = [100_000.0, 110_000.0]
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test", benchmark_returns=strat_rets[:-1])
        # Actually need aligned returns: pass returns for dates 1..N
        # Let's do it properly: 3 NAV points → 2 daily returns
        navs = [100_000.0, 105_000.0, 110_000.0]  # strategy +10%
        bench_rets = [0.02, 0.03]                  # benchmark +5%
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test", benchmark_returns=bench_rets)
        assert report.alpha_pct is not None
        assert report.alpha_pct > 0  # strategy beat benchmark

    def test_alpha_negative(self):
        """Strategy underperforms benchmark → negative alpha."""
        navs = [100_000.0, 105_000.0, 107_000.0]  # strategy +7%
        bench_rets = [0.02, 0.05]                  # benchmark +7% too... let's do +10%
        bench_rets = [0.02, 0.08]                  # benchmark +10%
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test", benchmark_returns=bench_rets)
        assert report.alpha_pct is not None
        assert report.alpha_pct < 0  # strategy trail benchmark

    def test_tracking_error(self):
        """Tracking error is positive when strategy deviates from benchmark."""
        navs = [100_000.0, 102_000.0, 104_000.0, 106_000.0]  # strategy +6%
        bench_rets = [0.02, 0.02, 0.02, 0.02]                  # benchmark +2% per day
        results = make_results(navs)
        report = RiskReport.from_results(results, strategy_name="Test", benchmark_returns=bench_rets)
        assert report.tracking_error is not None
        assert report.tracking_error > 0


class TestSummary:
    def test_summary_contains_all_keys(self):
        results = make_results([100_000.0, 110_000.0, 115_000.0])
        report = RiskReport.from_results(results, strategy_name="Test Strategy")
        s = report.summary()
        expected_keys = [
            "strategy", "period", "trading_days", "start_nav", "end_nav",
            "total_return_pct", "annualized_return_pct", "sharpe_ratio",
            "sortino_ratio", "max_drawdown_pct", "max_drawdown_days",
            "drawdown_period", "var_95_pct", "cvar_95_pct",
            "volatility_ann_pct", "win_rate_pct", "profit_factor",
        ]
        for key in expected_keys:
            assert key in s, f"Missing key: {key}"