# src/quant_finance/visualization/nav_chart.py
"""NAV line chart — strategy NAV vs benchmark, with trade markers."""

from datetime import date
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .charts import ChartConfig, prepare_nav_data, prepare_benchmark_nav, use_style


def plot_nav(
    results: list[dict],
    benchmark_returns: Optional[list[float]] = None,
    config: Optional[ChartConfig] = None,
) -> plt.Figure:
    """Plot strategy NAV over time with optional benchmark overlay.

    Args:
        results: list of dicts with 'date', 'nav', and optionally 'trade' keys
        benchmark_returns: optional list of daily benchmark returns (aligned with results[1:])
        config: optional ChartConfig

    Returns:
        matplotlib Figure
    """
    use_style()
    cfg = config or ChartConfig(title="Portfolio NAV", ylabel="NAV ($)")

    dates, navs = prepare_nav_data(results)
    bench_navs, bench_final = prepare_benchmark_nav(navs, benchmark_returns or [])

    fig, ax = plt.subplots(figsize=cfg.figsize)

    # Strategy NAV
    ax.plot(dates, navs, color="#2196F3", linewidth=1.8, label="Strategy", zorder=3)

    # Benchmark NAV
    if bench_navs and len(bench_navs) == len(dates):
        ax.plot(dates, bench_navs, color="#FF9800", linewidth=1.2, linestyle="--",
                label="Benchmark", zorder=2)

    # Trade markers
    for r in results:
        trade_str = r.get("trade", "")
        if not trade_str:
            continue
        if "BUY" in trade_str.upper():
            ax.axvline(r["date"], color="#4CAF50", alpha=0.4, linewidth=1)
            ax.plot(r["date"], r["nav"], "^", color="#4CAF50", markersize=8, zorder=5)
        elif "SELL" in trade_str.upper():
            ax.axvline(r["date"], color="#F44336", alpha=0.4, linewidth=1)
            ax.plot(r["date"], r["nav"], "v", color="#F44336", markersize=8, zorder=5)

    # Return labels
    total_ret = (navs[-1] - navs[0]) / navs[0] * 100
    ax.annotate(
        f"Return: {total_ret:.1f}%\nStart: ${navs[0]:,.0f}\nEnd: ${navs[-1]:,.0f}",
        xy=(0.98, 0.95), xycoords="axes fraction",
        ha="right", va="top",
        fontsize=cfg.fontsize,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.8),
    )

    cfg.apply(ax)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.autofmt_xdate()
    ax.legend(loc=cfg.legend_loc)

    fig.tight_layout()
    return fig