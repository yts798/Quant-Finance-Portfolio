# src/quant_finance/visualization/charts.py
"""Shared chart components and data preparation helpers."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# ─────────────────────────────────────────────────────────────────────────────
# ChartConfig
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ChartConfig:
    """Configuration for a single chart."""

    title: str = ""
    xlabel: str = "Date"
    ylabel: str = ""
    figsize: tuple[float, float] = (12, 6)
    style: str = "seaborn-v0_8-darkgrid"
    legend_loc: str = "best"
    grid: bool = True
    fontsize: int = 10

    def apply(self, ax: plt.Axes) -> None:
        ax.set_title(self.title, fontsize=self.fontsize + 2)
        ax.set_xlabel(self.xlabel, fontsize=self.fontsize)
        ax.set_ylabel(self.ylabel, fontsize=self.fontsize)
        if self.grid:
            ax.grid(True, alpha=0.3)
        if self.legend_loc != "none" and ax.get_legend_handles_labels()[1]:
            ax.legend(loc=self.legend_loc)


# ─────────────────────────────────────────────────────────────────────────────
# NAV data preparation
# ─────────────────────────────────────────────────────────────────────────────

def prepare_nav_data(results: list[dict]) -> tuple[list[date], list[float]]:
    """Extract dates and NAV series from backtest results."""
    dates = [r["date"] for r in results]
    navs = [r["nav"] for r in results]
    return dates, navs


def prepare_benchmark_nav(
    navs: list[float],
    benchmark_returns: list[float],
) -> tuple[list[float], float]:
    """Build benchmark NAV series from strategy start NAV and benchmark returns.

    Returns (bench_navs, bench_final) aligned to strategy NAV length.
    """
    if not benchmark_returns:
        return [], navs[0]

    start_nav = navs[0]
    bench_navs = [start_nav]
    for ret in benchmark_returns:
        bench_navs.append(bench_navs[-1] * (1 + ret))

    # Align: benchmark has N+1 navs for N returns, match to strategy length
    diff = len(bench_navs) - len(navs)
    if diff > 0:
        bench_navs = bench_navs[:len(navs)]
    return bench_navs, bench_navs[-1] if bench_navs else start_nav


# ─────────────────────────────────────────────────────────────────────────────
# Price data preparation
# ─────────────────────────────────────────────────────────────────────────────

def prepare_price_data(store, ticker: str, start: Optional[date] = None, end: Optional[date] = None):
    """Load OHLCV + volume data from a DataStore for a given ticker and date range.

    Returns (dates, opens, highs, lows, closes, volumes).
    """
    ed = store.equity_data(ticker)
    if start is None:
        start = ed.earliest_date() or date(2000, 1, 1)
    if end is None:
        end = ed.latest_date() or date(2099, 12, 31)

    dates = ed.date_range(start=start, end=end)

    opens, highs, lows, closes, volumes = [], [], [], [], []
    for d in dates:
        bar = ed.ohlcv_on(d)
        if bar is not None:
            opens.append(bar.open_)
            highs.append(bar.high)
            lows.append(bar.low)
            closes.append(bar.adj_close)
            volumes.append(bar.volume)
        else:
            opens.append(0.0)
            highs.append(0.0)
            lows.append(0.0)
            closes.append(0.0)
            volumes.append(0.0)

    return dates, opens, highs, lows, closes, volumes


# ─────────────────────────────────────────────────────────────────────────────
# Drawdown data preparation
# ─────────────────────────────────────────────────────────────────────────────

def prepare_drawdown_data(navs: list[float], dates: Optional[list[date]] = None):
    """Compute drawdown series (peak-to-trough %).

    Returns (drawdown_dates, drawdowns) where each drawdown is
    the % below the running peak at that point.
    """
    drawdowns = []
    peak = navs[0] if navs else 0.0

    for nav in navs:
        if nav > peak:
            peak = nav
        dd = (nav - peak) / peak if peak != 0 else 0.0
        drawdowns.append(dd)

    return drawdowns


# ─────────────────────────────────────────────────────────────────────────────
# Daily returns preparation
# ─────────────────────────────────────────────────────────────────────────────

def prepare_daily_returns(navs: list[float]) -> list[float]:
    """Compute daily simple returns from NAV series."""
    returns = []
    for i in range(1, len(navs)):
        ret = (navs[i] - navs[i - 1]) / navs[i - 1]
        returns.append(ret)
    return returns


# ─────────────────────────────────────────────────────────────────────────────
# Style helpers
# ─────────────────────────────────────────────────────────────────────────────

def use_style(style: str = "seaborn-v0_8-darkgrid") -> None:
    """Activate a matplotlib style if available, skip silently if not."""
    try:
        plt.style.use(style)
    except Exception:
        pass  # fallback to default if style not found