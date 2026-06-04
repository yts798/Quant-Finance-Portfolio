"""
workfile_viz.py
===============
Demo: generate all visualization charts from a live backtest run.

Charts produced:
  - NAV chart: strategy vs benchmark (SPY buy-hold)
  - Price chart: SPY line + SMA20/SMA50 overlays
  - Candlestick: SPY candlestick + volume
  - Drawdown: portfolio drawdown % over time
  - Returns hist: daily return distribution with VaR 5%

Usage:
    python workfile_viz.py
    # PNGs saved to ./output/
"""

from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive: write to PNG, no display

from quant_finance.data import DataLoader, DataStore
from quant_finance.instruments.equity import Equity
from quant_finance.instruments.portfolio import Portfolio
from quant_finance.strategies import RiskReport
from quant_finance.visualization import (
    plot_nav,
    plot_price,
    plot_drawdown,
    plot_returns_hist,
    plot_rolling_sharpe,
    plot_rolling_volatility,
    plot_rolling_drawdown,
    ChartConfig,
)

# ── Config ─────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
TICKER = "SPY"
START_DATE = date(2025, 3, 1)
END_DATE = date(2025, 12, 31)


# ── Load data ───────────────────────────────────────────────────────────────────
print("Loading data...")
store = DataLoader.load_store([TICKER], DATA_DIR)
print(f"  DataStore: {store}")

# ── Build equities & portfolio ─────────────────────────────────────────────────
equities = {}
first_date = store.next_trading_date(START_DATE) or START_DATE
for ticker in store.tickers():
    price = store.get_price(ticker, first_date)
    equities[ticker] = Equity(ticker=ticker, current_price=price)

portfolio = Portfolio(name="Visualization Demo", cash=100_000.0)

# ── Run backtest (buy-and-hold) ────────────────────────────────────────────────
print("Running buy-and-hold backtest...")

trade_date = first_date
spy_price = store.get_price(TICKER, trade_date)

# Buy-and-hold: invest 95% of cash on day 1
from quant_finance.instruments.portfolio.portfolio import Trade, TradeSide
trade = Trade(ticker=TICKER, side=TradeSide.BUY,
              quantity=int(portfolio.cash * 0.95 / spy_price),
              price=spy_price, trade_date=trade_date)
portfolio.record_trade(trade, equity=equities[TICKER])

# Daily mark-to-market
results = []
trading_dates = store.trading_dates(start=trade_date, end=END_DATE)

for d in trading_dates:
    store.update_portfolio_prices(portfolio, d)
    results.append({
        "date": d,
        "nav": portfolio.total_value(),
        "trade": "",
    })

# ── Benchmark (SPY buy-hold) ─────────────────────────────────────────────────
spy_bars = store.equity_data(TICKER).date_range(start=trade_date, end=END_DATE)
spy_prices = [store.get_price(TICKER, d) for d in spy_bars]
benchmark_returns = [
    (spy_prices[i] - spy_prices[i - 1]) / spy_prices[i - 1]
    for i in range(1, len(spy_prices))
]

# ── Risk report ───────────────────────────────────────────────────────────────
report = RiskReport.from_results(
    results=results,
    strategy_name="Buy & Hold SPY",
    benchmark_returns=benchmark_returns,
    risk_free_rate=0.042,
)

# ── Chart configs ─────────────────────────────────────────────────────────────
nav_cfg = ChartConfig(
    title="Strategy NAV vs Benchmark",
    ylabel="NAV ($)",
    figsize=(12, 6),
)
price_cfg = ChartConfig(
    title=f"{TICKER} Price",
    ylabel="Price ($)",
    figsize=(14, 7),
)
dd_cfg = ChartConfig(
    title="Portfolio Drawdown",
    ylabel="Drawdown (%)",
    figsize=(12, 5),
)
hist_cfg = ChartConfig(
    title="Daily Returns Distribution",
    ylabel="Frequency",
    figsize=(12, 5),
)

# ── Generate charts ───────────────────────────────────────────────────────────
print("Generating charts...")
OUTPUT_DIR.mkdir(exist_ok=True)

# 1. NAV chart
fig_nav = plot_nav(results, benchmark_returns=benchmark_returns, config=nav_cfg)
fig_nav.savefig(OUTPUT_DIR / "nav_chart.png", dpi=150)
print("  Saved: output/nav_chart.png")

# 2. Price line chart with SMAs
fig_price = plot_price(store, TICKER, start=START_DATE, end=END_DATE,
                       config=price_cfg, candlestick=False)
fig_price.savefig(OUTPUT_DIR / "price_chart.png", dpi=150)
print("  Saved: output/price_chart.png")

# 3. Candlestick chart
fig_candle = plot_price(store, TICKER, start=START_DATE, end=END_DATE,
                        config=price_cfg, candlestick=True)
fig_candle.savefig(OUTPUT_DIR / "candlestick_chart.png", dpi=150)
print("  Saved: output/candlestick_chart.png")

# 4. Drawdown chart
navs = [r["nav"] for r in results]
dates = [r["date"] for r in results]
fig_dd = plot_drawdown(navs, dates=dates, config=dd_cfg)
fig_dd.savefig(OUTPUT_DIR / "drawdown_chart.png", dpi=150)
print("  Saved: output/drawdown_chart.png")

# 5. Returns histogram with VaR
fig_hist = plot_returns_hist(navs, config=hist_cfg, bins=40)
fig_hist.savefig(OUTPUT_DIR / "returns_hist.png", dpi=150)
print("  Saved: output/returns_hist.png")

# 6. Rolling Sharpe
fig_rs = plot_rolling_sharpe(navs, window=20, risk_free_rate=0.042,
                              config=ChartConfig(title="Rolling Sharpe (20-day)", ylabel="Sharpe"))
fig_rs.savefig(OUTPUT_DIR / "rolling_sharpe.png", dpi=150)
print("  Saved: output/rolling_sharpe.png")

# 7. Rolling Volatility
fig_rv = plot_rolling_volatility(navs, window=20,
                                  config=ChartConfig(title="Rolling Volatility (20-day)", ylabel="Vol (%)"))
fig_rv.savefig(OUTPUT_DIR / "rolling_volatility.png", dpi=150)
print("  Saved: output/rolling_volatility.png")

# 8. Rolling Max Drawdown
fig_rd = plot_rolling_drawdown(navs, window=20,
                               config=ChartConfig(title="Rolling Max Drawdown (20-day)", ylabel="Max DD (%)"))
fig_rd.savefig(OUTPUT_DIR / "rolling_drawdown.png", dpi=150)
print("  Saved: output/rolling_drawdown.png")

# ── Print summary ─────────────────────────────────────────────────────────────
print("\nRisk Report")
print("=" * 50)
s = report.summary()
for k, v in s.items():
    print(f"  {k:<30} {v}")

print(f"\nCharts saved to: {OUTPUT_DIR}/")
print("  - nav_chart.png")
print("  - price_chart.png")
print("  - candlestick_chart.png")
print("  - drawdown_chart.png")
print("  - returns_hist.png")
print("  - rolling_sharpe.png")
print("  - rolling_volatility.png")
print("  - rolling_drawdown.png")
print("\nDone.")