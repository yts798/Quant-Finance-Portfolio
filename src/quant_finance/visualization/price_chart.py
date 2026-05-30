# src/quant_finance/visualization/price_chart.py
"""Price chart — line or candlestick with SMA overlays and volume."""

from datetime import date
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

from .charts import ChartConfig, prepare_price_data, use_style


def plot_price(
    store,
    ticker: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    config: Optional[ChartConfig] = None,
    candlestick: bool = False,
) -> plt.Figure:
    """Plot price history for a ticker with volume bars and optional SMAs.

    Args:
        store: DataStore instance
        ticker: ticker symbol (e.g. "SPY")
        start: start date (default: earliest available)
        end: end date (default: latest available)
        config: optional ChartConfig
        candlestick: if True, draw OHLC candlesticks; else draw line chart

    Returns:
        matplotlib Figure
    """
    use_style()
    cfg = config or ChartConfig(title=f"{ticker} Price", ylabel="Price ($)")

    dates, opens, highs, lows, closes, volumes = prepare_price_data(store, ticker, start, end)

    if not dates:
        fig, ax = plt.subplots(figsize=cfg.figsize)
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        return fig

    if candlestick:
        return _candlestick(dates, opens, highs, lows, closes, volumes, cfg)
    else:
        return _line_chart(dates, closes, volumes, cfg)


def _line_chart(dates, closes, volumes, cfg):
    """Line chart with volume subplot."""
    fig, (ax_price, ax_vol) = plt.subplots(
        2, 1, figsize=cfg.figsize,
        gridspec_kw={"height_ratios": [4, 1]}, sharex=True,
    )

    ax_price.plot(dates, closes, color="#2196F3", linewidth=1.5)

    # SMAs
    if len(closes) >= 20:
        sma20 = _sma(closes, 20)
        ax_price.plot(dates[-len(sma20):], sma20, color="#FF9800", linewidth=1.2,
                      label="SMA 20", linestyle="--")
    if len(closes) >= 50:
        sma50 = _sma(closes, 50)
        ax_price.plot(dates[-len(sma50):], sma50, color="#9C27B0", linewidth=1.2,
                      label="SMA 50", linestyle="--")

    ax_price.set_ylabel(cfg.ylabel or "Adj Close ($)", fontsize=cfg.fontsize)
    ax_price.legend(loc=cfg.legend_loc)
    cfg.apply(ax_price)
    ax_price.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.2f}"))

    # Volume bars
    ax_vol.bar(dates, volumes, color="#90A4AE", width=1.0, alpha=0.7)
    ax_vol.set_ylabel("Volume", fontsize=cfg.fontsize)
    ax_vol.set_xlabel(cfg.xlabel, fontsize=cfg.fontsize)
    ax_vol.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))

    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def _candlestick(dates, opens, highs, lows, closes, volumes, cfg):
    """Candlestick chart with volume subplot."""
    import matplotlib.dates as mdates

    fig, (ax_price, ax_vol) = plt.subplots(
        2, 1, figsize=cfg.figsize,
        gridspec_kw={"height_ratios": [4, 1]}, sharex=True,
    )

    # Convert dates to matplotlib format
    x = [mdates.date2num(d) for d in dates]

    # Draw candlesticks
    for i, (xi, o, h, l, c) in enumerate(zip(x, opens, highs, lows, closes)):
        color = "#4CAF50" if c >= o else "#F44336"
        # Body
        body_bottom = min(o, c)
        body_height = max(abs(c - o), 0.01)
        rect = Rectangle(
            (xi - 0.3, body_bottom), 0.6, body_height,
            linewidth=0.5, facecolor=color, edgecolor=color
        )
        ax_price.add_patch(rect)
        # High-low wick
        ax_price.plot([xi, xi], [l, h], color=color, linewidth=0.8)

    ax_price.set_xlim(min(x) - 1, max(x) + 1)
    ax_price.set_ylim(min(lows) * 0.98, max(highs) * 1.02)
    ax_price.set_ylabel(cfg.ylabel or "Price ($)", fontsize=cfg.fontsize)
    ax_price.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.2f}"))

    # Volume bars colored by up/down day
    for i, (xi, o, c, v) in enumerate(zip(x, opens, closes, volumes)):
        color = "#4CAF50" if c >= o else "#F44336"
        ax_vol.add_patch(Rectangle((xi - 0.3, 0), 0.6, v, facecolor=color, alpha=0.6))

    ax_vol.set_ylabel("Volume", fontsize=cfg.fontsize)
    ax_vol.set_xlabel(cfg.xlabel, fontsize=cfg.fontsize)
    ax_vol.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))

    # Format x-axis as dates
    ax_price.xaxis_date()
    ax_price.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()

    cfg.apply(ax_price)
    fig.tight_layout()
    return fig


def _sma(prices: list[float], window: int) -> list[float]:
    """Simple moving average."""
    return [
        sum(prices[i - window + 1:i + 1]) / window
        for i in range(window - 1, len(prices))
    ]