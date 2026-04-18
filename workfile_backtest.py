"""
workfile_backtest.py
===================
Downloads US equity data and runs a simple buy-and-hold backtest.

Usage:
    python workfile_backtest.py

What it does:
    1. Downloads daily OHLCV data via yfinance (AAPL, MSFT, GOOGL, SPY)
    2. Saves to Parquet files in ./data/
    3. Loads into a DataStore
    4. Runs a simple backtest over 2025 (buy-and-hold SPY)
    5. Prints daily NAV and a final performance summary
"""

from datetime import date
from pathlib import Path

# ── Project imports ────────────────────────────────────────────────────────────
from quant_finance.data import DataLoader, DataStore
from quant_finance.instruments.equity import Equity
from quant_finance.instruments.portfolio import Portfolio, Trade, TradeSide

# ── Configuration ───────────────────────────────────────────────────────────────
TICKERS = ["AAPL", "MSFT", "GOOGL", "SPY"]
DATA_DIR = Path("data")
START = "2025-01-01"
END = "2025-12-31"
BACKTEST_START = date(2025, 1, 2)  # first trading day after New Year
BACKTEST_END = date(2025, 12, 31)

# ── Step 1: Download data ──────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1 — Download data from Yahoo Finance")
print("=" * 60)

loader = DataLoader()
print(f"Downloading {TICKERS} from {START} to {END} ...")
cache = loader.download(TICKERS, start=START, end=END, progress=True)

for ticker, df in cache.items():
    print(f"  {ticker}: {len(df)} bars downloaded")

# ── Step 2: Save to Parquet ────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 2 — Save to Parquet files")
print("=" * 60)

DATA_DIR.mkdir(parents=True, exist_ok=True)
saved = loader.save_all(DATA_DIR)
for ticker, path in saved.items():
    print(f"  Saved: {path}")

# ── Step 3: Load into DataStore ───────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 3 — Load into DataStore")
print("=" * 60)

store = loader.to_store()
print(f"  DataStore: {store}")

# Show date range
dates = store.trading_dates()
print(f"  Trading days: {dates[0]} -> {dates[-1]}  ({len(dates)} days)")
print(f"  Tickers: {store.tickers()}")

# ── Step 4: Build Equity instruments ─────────────────────────────────────────
print()
print("=" * 60)
print("STEP 4 — Create Equity instruments")
print("=" * 60)

equities: dict[str, Equity] = {}
for ticker in TICKERS:
    price = store.get_price(ticker, BACKTEST_START)
    eq = Equity(ticker=ticker, current_price=price)
    equities[ticker] = eq
    print(f"  {ticker}: initial price = ${price:.2f}")

# ── Step 5: Backtest ───────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 5 — Run backtest: Buy & Hold SPY")
print("=" * 60)

portfolio = Portfolio(name="Buy & Hold SPY", cash=100_000.0)
trade_date = store.next_trading_date(BACKTEST_START) or BACKTEST_START

# Buy 100 shares of SPY on the first day
spy_price = store.get_price("SPY", trade_date)
trade = Trade(
    ticker="SPY",
    side=TradeSide.BUY,
    quantity=100,
    price=spy_price,
    trade_date=trade_date,
)
portfolio.record_trade(trade, equity=equities["SPY"])
print(f"  Bought 100 SPY @ ${spy_price:.2f} on {trade_date}")
print(f"  Cash after trade: ${portfolio.cash:,.2f}")
print()

# ── Step 6: Run daily mark-to-market loop ─────────────────────────────────────
results: list[dict] = []

trading_dates = store.trading_dates(start=trade_date, end=BACKTEST_END)

for d in trading_dates:
    # Mark-to-market: push today's close price into all equities
    store.update_portfolio_prices(portfolio, d)

    # Record daily snapshot
    results.append({
        "date": d,
        "nav": portfolio.total_value(),
        "cash": portfolio.cash,
        "positions_value": sum(pos.market_value for pos in portfolio.positions.values()),
        "unrealized_pnl": portfolio.total_unrealized_pnl,
        "spy_price": equities["SPY"].current_price,
    })

# ── Step 7: Print results ─────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 7 — Daily NAV")
print("=" * 60)
print(f"{'Date':<12} {'SPY Price':>12} {'Positions':>14} {'Cash':>14} {'NAV':>14} {'Unreal. P&L':>14}")
print("-" * 80)

# Print first 10 and last 5 days
for row in results[:10]:
    print(
        f"{str(row['date']):<12}"
        f"{row['spy_price']:>12.2f}"
        f"{row['positions_value']:>14,.2f}"
        f"{row['cash']:>14,.2f}"
        f"{row['nav']:>14,.2f}"
        f"{row['unrealized_pnl']:>14,.2f}"
    )

if len(results) > 15:
    print("  ...")

for row in results[-5:]:
    print(
        f"{str(row['date']):<12}"
        f"{row['spy_price']:>12.2f}"
        f"{row['positions_value']:>14,.2f}"
        f"{row['cash']:>14,.2f}"
        f"{row['nav']:>14,.2f}"
        f"{row['unrealized_pnl']:>14,.2f}"
    )

# ── Step 8: Performance summary ────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 8 — Performance Summary")
print("=" * 60)

first_nav = results[0]["nav"]
last_nav = results[-1]["nav"]
total_return = (last_nav - first_nav) / first_nav * 100
total_pnl = last_nav - first_nav

# Also check SPY price return
first_spy = results[0]["spy_price"]
last_spy = results[-1]["spy_price"]
spy_return = (last_spy - first_spy) / first_spy * 100

print(f"  Strategy : Buy & Hold SPY")
print(f"  Period   : {results[0]['date']} -> {results[-1]['date']}")
print(f"  Days     : {len(results)}")
print(f"  Start NAV: ${first_nav:,.2f}")
print(f"  End NAV  : ${last_nav:,.2f}")
print(f"  Total P&L: ${total_pnl:,.2f}")
print(f"  Return   : {total_return:.2f}%")
print()
print(f"  SPY Price: ${first_spy:.2f} -> ${last_spy:.2f}  ({spy_return:.2f}%)")
print(f"  Benchmark: Buy & hold return = SPY return")
print(f"  Alpha    : {total_return - spy_return:.2f}%")
print()
print("  Portfolio summary:")
s = portfolio.summary()
for k, v in s.items():
    print(f"    {k}: {v}")
print()
print("Done.")
