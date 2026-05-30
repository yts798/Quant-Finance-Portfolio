# src/quant_finance/visualization/risk_chart.py
"""Risk charts — drawdown area chart and returns histogram with VaR."""

from datetime import date
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from .charts import ChartConfig, prepare_drawdown_data, prepare_daily_returns, use_style


def plot_drawdown(
    navs: list[float],
    dates: Optional[list[date]] = None,
    config: Optional[ChartConfig] = None,
) -> plt.Figure:
    """Drawdown area chart — shows % below peak over time.

    Args:
        navs: list of NAV values
        dates: optional list of dates (aligned with navs). If None, uses index.
        config: optional ChartConfig

    Returns:
        matplotlib Figure
    """
    use_style()
    cfg = config or ChartConfig(title="Drawdown", ylabel="Drawdown (%)")

    drawdowns = prepare_drawdown_data(navs)
    if dates is None:
        dates = list(range(len(drawdowns)))

    fig, ax = plt.subplots(figsize=cfg.figsize)

    ax.fill_between(dates, [d * 100 for d in drawdowns], 0,
                    color="#F44336", alpha=0.3, label="Drawdown")
    ax.plot(dates, [d * 100 for d in drawdowns], color="#F44336", linewidth=1.0)

    # Mark worst drawdown
    min_dd = min(drawdowns)
    min_idx = drawdowns.index(min_dd)
    ax.annotate(
        f"Max DD: {min_dd * 100:.1f}%",
        xy=(dates[min_idx], min_dd * 100),
        xytext=(10, -20), textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color="#F44336"),
        fontsize=cfg.fontsize,
        color="#F44336",
    )

    ax.set_ylabel("Drawdown (%)", fontsize=cfg.fontsize)
    cfg.apply(ax)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def plot_returns_hist(
    navs: list[float],
    config: Optional[ChartConfig] = None,
    bins: int = 40,
) -> plt.Figure:
    """Histogram of daily returns with VaR 5% and mean markers.

    Args:
        navs: list of NAV values
        config: optional ChartConfig
        bins: number of histogram bins (default 40)

    Returns:
        matplotlib Figure
    """
    use_style()
    cfg = config or ChartConfig(title="Daily Returns Distribution", ylabel="Frequency")

    returns = prepare_daily_returns(navs)

    fig, ax = plt.subplots(figsize=cfg.figsize)

    ax.hist(returns, bins=bins, color="#90A4AE", edgecolor="white", alpha=0.8)

    # VaR 5% — value at risk (5th percentile, shown as loss)
    if returns:
        sorted_rets = sorted(returns)
        var_idx = max(0, int(len(sorted_rets) * 0.05) - 1)
        var_5 = sorted_rets[var_idx]
        ax.axvline(var_5, color="#F44336", linewidth=2, linestyle="--",
                  label=f"VaR 5%: {var_5 * 100:.2f}%")

        # Mean
        mean_ret = sum(returns) / len(returns)
        ax.axvline(mean_ret, color="#4CAF50", linewidth=2, linestyle="--",
                  label=f"Mean: {mean_ret * 100:.2f}%")

        # +/- 1 std
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        std = variance ** 0.5
        ax.axvline(mean_ret + std, color="#FF9800", linewidth=1.2, linestyle=":",
                   label=f"+1 Std: {(mean_ret + std) * 100:.2f}%")
        ax.axvline(mean_ret - std, color="#FF9800", linewidth=1.2, linestyle=":",
                   label=f"-1 Std: {(mean_ret - std) * 100:.2f}%")

    ax.set_xlabel("Daily Return (%)", fontsize=cfg.fontsize)
    ax.set_ylabel("Frequency", fontsize=cfg.fontsize)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x * 100:.1f}%"))
    cfg.apply(ax)
    ax.legend(loc=cfg.legend_loc)

    fig.tight_layout()
    return fig