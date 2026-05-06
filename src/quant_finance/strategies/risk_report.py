# src/quant_finance/strategies/risk_report.py
"""Risk metrics for strategy evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
from typing import Optional


@dataclass
class RiskReport:
    """Standard risk metrics for a backtest result.

    All metrics are computed from daily NAV (mark-to-market) returns.
    """

    # ── Input summary ────────────────────────────────────────────────────────
    strategy_name: str
    start_date: date
    end_date: date
    trading_days: int
    start_nav: float
    end_nav: float

    # ── Return metrics ──────────────────────────────────────────────────────
    total_return_pct: float       # simple return %
    annualized_return_pct: float  # CAGR %
    sharpe_ratio: float          # annualized (daily ret mean / ret std * sqrt(252))
    sortino_ratio: float          # (mean - target) / downside_std * sqrt(252), target=0

    # ── Drawdown metrics ─────────────────────────────────────────────────────
    max_drawdown_pct: float       # peak-to-trough max %
    max_drawdown_days: int        # days in the worst drawdown
    drawdown_start: Optional[date]
    drawdown_end: Optional[date]

    # ── Risk metrics ─────────────────────────────────────────────────────────
    var_95_pct: float             # 95% Value at Risk (worst daily loss at 95th pct)
    cvar_95_pct: float           # Conditional VaR (avg loss beyond VaR)
    volatility_annualised: float  # daily std * sqrt(252)

    # ── Trade metrics ───────────────────────────────────────────────────────
    total_trades: int
    win_rate_pct: float           # % of positive return days
    profit_factor: float          # gross profit / gross loss

    # ── Benchmark comparison ────────────────────────────────────────────────
    benchmark_return_pct: Optional[float] = None
    alpha_pct: Optional[float] = None        # strategy ret - benchmark ret
    tracking_error: Optional[float] = None    # std(strategy_ret - benchmark_ret)

    @classmethod
    def from_results(
        cls,
        results: list[dict],
        strategy_name: str = "Strategy",
        benchmark_returns: Optional[list[float]] = None,
        risk_free_rate: float = 0.0,  # annual risk-free rate (e.g. 0.04 = 4%)
    ) -> RiskReport:
        """Build a RiskReport from a backtest results list.

        Args:
            results: list of dicts with 'date' and 'nav' keys (e.g. backtester output)
            strategy_name: label for this strategy
            benchmark_returns: optional list of daily benchmark returns aligned with results
            risk_free_rate: annual risk-free rate for Sharpe/Sortino (default 0)
        """
        if not results:
            raise ValueError("results cannot be empty")

        navs = [r["nav"] for r in results]
        dates = [r["date"] for r in results]
        n = len(navs)

        # ── Daily returns ──────────────────────────────────────────────────
        daily_returns = []
        for i in range(1, n):
            ret = (navs[i] - navs[i - 1]) / navs[i - 1]
            daily_returns.append(ret)
        # Also get the return list for benchmark
        if benchmark_returns is not None:
            bench_rets = benchmark_returns[-len(daily_returns):] if len(benchmark_returns) >= len(daily_returns) else benchmark_returns
        else:
            bench_rets = None

        # ── Return metrics ────────────────────────────────────────────────────
        total_return = (navs[-1] - navs[0]) / navs[0]

        # Annualised return: compound daily returns ^ (252 / n)
        if n > 1:
            cumulative = navs[-1] / navs[0]
            ann_return = cumulative ** (252 / n) - 1
        else:
            ann_return = 0.0

        # Volatility
        if len(daily_returns) > 1:
            mean_ret = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_ret) ** 2 for r in daily_returns) / len(daily_returns)
            daily_std = math.sqrt(variance) if variance > 0 else 0.0
            vol_ann = daily_std * math.sqrt(252)
        else:
            mean_ret = 0.0
            daily_std = 0.0
            vol_ann = 0.0

        # Sharpe ratio
        rf_daily = risk_free_rate / 252
        excess_ret = mean_ret - rf_daily
        sharpe = (excess_ret / daily_std * math.sqrt(252)) if daily_std > 0 else 0.0

        # Sortino ratio (downside deviation — only negative returns)
        downside_returns = [r for r in daily_returns if r < 0]
        if len(downside_returns) > 1:
            down_std = math.sqrt(
                sum(r ** 2 for r in downside_returns) / len(daily_returns)
            )
            sortino = (excess_ret / down_std * math.sqrt(252)) if down_std > 0 else 0.0
        else:
            sortino = 0.0

        # ── Drawdown metrics ─────────────────────────────────────────────────
        peak = navs[0]
        peak_idx = 0
        max_dd = 0.0
        max_dd_start = dates[0]
        max_dd_end = dates[0]
        current_dd_start = dates[0]

        for i, (d, nav) in enumerate(zip(dates, navs)):
            if nav > peak:
                peak = nav
                peak_idx = i
                current_dd_start = d

            dd = (nav - peak) / peak
            if dd < max_dd:
                max_dd = dd
                max_dd_start = current_dd_start
                max_dd_end = d

        # Drawdown duration: count days from peak to trough
        peak_date_idx = dates.index(max_dd_start) if max_dd_start in dates else 0
        trough_date_idx = dates.index(max_dd_end) if max_dd_end in dates else 0
        max_dd_days = max(0, trough_date_idx - peak_date_idx)

        # ── Risk metrics ──────────────────────────────────────────────────────
        # VaR and CVaR at 95%
        if daily_returns:
            sorted_rets = sorted(daily_returns)
            var_idx = int(len(sorted_rets) * 0.05)
            var_95 = abs(sorted_rets[var_idx]) if var_idx < len(sorted_rets) else 0.0
            cvar_95 = (
                abs(sum(sorted_rets[:var_idx]) / var_idx)
                if var_idx > 0
                else 0.0
            )
        else:
            var_95 = 0.0
            cvar_95 = 0.0

        # ── Trade / win metrics ───────────────────────────────────────────────
        positive_days = sum(1 for r in daily_returns if r > 0)
        win_rate = (positive_days / len(daily_returns) * 100) if daily_returns else 0.0

        gross_profit = sum(r for r in daily_returns if r > 0)
        gross_loss = abs(sum(r for r in daily_returns if r < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # ── Benchmark comparison ────────────────────────────────────────────
        alpha = None
        tracking_err = None
        bench_return_pct = None
        if bench_rets is not None and len(bench_rets) == len(daily_returns):
            bench_return_pct = (sum(bench_rets) / len(bench_rets)) * 100  # avg daily
            alpha = total_return - sum(bench_rets) / len(bench_rets)
            # Tracking error
            diffs = [daily_returns[i] - bench_rets[i] for i in range(len(daily_returns))]
            te = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs)) * math.sqrt(252) if diffs else 0.0
            tracking_err = te

        return cls(
            strategy_name=strategy_name,
            start_date=dates[0],
            end_date=dates[-1],
            trading_days=n,
            start_nav=navs[0],
            end_nav=navs[-1],
            total_return_pct=total_return * 100,
            annualized_return_pct=ann_return * 100,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown_pct=max_dd * 100,
            max_drawdown_days=max_dd_days,
            drawdown_start=max_dd_start,
            drawdown_end=max_dd_end,
            var_95_pct=var_95 * 100,
            cvar_95_pct=cvar_95 * 100,
            volatility_annualised=vol_ann * 100,
            total_trades=0,  # will be set externally if needed
            win_rate_pct=win_rate,
            profit_factor=profit_factor,
            benchmark_return_pct=bench_return_pct,
            alpha_pct=alpha * 100 if alpha is not None else None,
            tracking_error=tracking_err,
        )

    def summary(self) -> dict:
        """Return all metrics as a flat dict."""
        return {
            "strategy": self.strategy_name,
            "period": f"{self.start_date} -> {self.end_date}",
            "trading_days": self.trading_days,
            "start_nav": self.start_nav,
            "end_nav": self.end_nav,
            "total_return_pct": round(self.total_return_pct, 2),
            "annualized_return_pct": round(self.annualized_return_pct, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "sortino_ratio": round(self.sortino_ratio, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "max_drawdown_days": self.max_drawdown_days,
            "drawdown_period": (
                f"{self.drawdown_start} -> {self.drawdown_end}"
                if self.drawdown_start and self.drawdown_end
                else "N/A"
            ),
            "var_95_pct": round(self.var_95_pct, 2),
            "cvar_95_pct": round(self.cvar_95_pct, 2),
            "volatility_ann_pct": round(self.volatility_annualised, 2),
            "win_rate_pct": round(self.win_rate_pct, 1),
            "profit_factor": round(self.profit_factor, 2),
            "alpha_pct": round(self.alpha_pct, 2) if self.alpha_pct is not None else None,
            "tracking_error": round(self.tracking_error, 2) if self.tracking_error is not None else None,
        }

    def __repr__(self) -> str:
        return f"RiskReport({self.strategy_name!r}, Sharpe={self.sharpe_ratio:.2f}, MaxDD={self.max_drawdown_pct:.1f}%)"
