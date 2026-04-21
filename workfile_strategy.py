"""
workfile_strategy.py
====================
Moving Average Crossover strategy on SPY.

Signal rules:
  - BUY  when 20-day SMA crosses ABOVE 50-day SMA  (golden cross)
  - SELL when 20-day SMA crosses BELOW 50-day SMA  (death cross)

Infrastructure used:
  DataStore   — historical prices
  Portfolio   — positions, cash, realised/unrealised P&L
  Signal     — the signal generated each day
  Backtester — the daily loop
"""

from datetime import date, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# ── Project imports ────────────────────────────────────────────────────────────
from quant_finance.data import DataLoader, DataStore
from quant_finance.instruments.equity import Equity
from quant_finance.instruments.portfolio import Portfolio, Trade, TradeSide


# ─────────────────────────────────────────────────────────────────────────────
# Strategy: Moving Average Crossover
# ─────────────────────────────────────────────────────────────────────────────

class SignalSide(Enum):
    LONG = "long"
    FLAT = "flat"
    SHORT = "short"  # not used in this strategy, but available


@dataclass
class Signal:
    """A trading signal for one ticker on one date."""

    date: date
    ticker: str
    side: SignalSide
    price: float
    reason: str = ""


@dataclass
class MAInput:
    """Sliding window of prices needed to compute SMAs."""

    ticker: str
    prices: list[float] = field(default_factory=list)  # ordered oldest → newest
    window_short: int = 20
    window_long: int = 50

    def add(self, price: float) -> None:
        self.prices.append(price)

    def sma_short(self) -> float | None:
        if len(self.prices) < self.window_short:
            return None
        return sum(self.prices[-self.window_short:]) / self.window_short

    def sma_long(self) -> float | None:
        if len(self.prices) < self.window_long:
            return None
        return sum(self.prices[-self.window_long:]) / self.window_long

    @property
    def is_ready(self) -> bool:
        """True once we have enough data for both SMAs."""
        return len(self.prices) >= self.window_long

    def crossover(
        self, prev_short: float | None, prev_long: float | None
    ) -> SignalSide | None:
        """Detect if a crossover occurred today.

        Returns the new side to trade into, or None if no signal.
        """
        short = self.sma_short()
        long = self.sma_long()
        if short is None or long is None:
            return None

        # Golden cross: short crosses above long
        if prev_short is not None and prev_long is not None:
            was_above = prev_short >= prev_long
            is_above = short >= long
            if not was_above and is_above:
                return SignalSide.LONG
            if was_above and not is_above:
                return SignalSide.FLAT  # exit long → flat

        return None


# ─────────────────────────────────────────────────────────────────────────────
# Backtester
# ─────────────────────────────────────────────────────────────────────────────

class Backtester:
    """Simple event-driven backtester.

    Runs a strategy over a DataStore and feeds results into a Portfolio.
    """

    def __init__(
        self,
        store: DataStore,
        portfolio: Portfolio,
        equities: dict[str, Equity],
        strategy: callable,  # (equities, store, date, portfolio) -> Signal | None
    ):
        self.store = store
        self.portfolio = portfolio
        self.equities = equities
        self.strategy = strategy
        self._position = SignalSide.FLAT  # current strategy position

    def run(self, start: date, end: date) -> list[dict]:
        """Run the backtest from start to end (inclusive).

        Returns a list of daily snapshots.
        """
        results: list[dict] = []
        trading_dates = self.store.trading_dates(start=start, end=end)

        for d in trading_dates:
            # 1. Mark-to-market — push today's close into all equities
            self.store.update_portfolio_prices(self.portfolio, d)

            # 2. Generate signal for today (strategy receives all prior data)
            signal = self.strategy(
                equities=self.equities,
                store=self.store,
                date=d,
                portfolio=self.portfolio,
            )

            # 3. Execute signal → trade
            executed_trade: Trade | None = None
            if signal is not None and signal.side != self._position:
                executed_trade = self._execute(signal, d)

            # 4. Record snapshot
            spy_price = self.equities["SPY"].current_price

            trade_desc = ""
            if executed_trade is not None:
                trade_desc = (
                    f"{executed_trade.side.value.upper()} "
                    f"{executed_trade.quantity} @ ${executed_trade.price:.2f}"
                )

            results.append(
                {
                    "date": d,
                    "spy_price": spy_price,
                    "signal": signal.side.value if signal else self._position.value,
                    "position": self._position.value,
                    "nav": self.portfolio.total_value(),
                    "cash": self.portfolio.cash,
                    "positions_value": sum(
                        p.market_value for p in self.portfolio.positions.values()
                    ),
                    "unrealised_pnl": self.portfolio.total_unrealized_pnl,
                    "realised_pnl": self.portfolio.total_realized_pnl,
                    "trade": trade_desc,
                }
            )

            # 5. Update strategy position state
            if signal is not None:
                self._position = signal.side

        return results

    def _execute(self, signal: Signal, d: date) -> Trade | None:
        """Execute a signal. Returns the Trade if executed, or None if no trade."""
        ticker = signal.ticker

        if signal.side == SignalSide.LONG:
            quantity = int(self.portfolio.cash * 0.95 / signal.price)
            if quantity == 0:
                return None
            trade = Trade(
                ticker=ticker,
                side=TradeSide.BUY,
                quantity=quantity,
                price=signal.price,
                trade_date=d,
            )
            self.portfolio.record_trade(trade, equity=self.equities[ticker])
            return trade

        elif signal.side == SignalSide.FLAT:
            if ticker in self.portfolio.positions:
                qty = self.portfolio.positions[ticker].quantity
                trade = Trade(
                    ticker=ticker,
                    side=TradeSide.SELL,
                    quantity=qty,
                    price=signal.price,
                    trade_date=d,
                )
                self.portfolio.record_trade(trade, equity=self.equities[ticker])
                return trade

        return None


# ─────────────────────────────────────────────────────────────────────────────
# Strategy factory
# ─────────────────────────────────────────────────────────────────────────────

def ma_crossover_strategy(
    equities: dict[str, Equity],
    store: DataStore,
    date: date,
    portfolio: Portfolio,
    ticker: str = "SPY",
    window_short: int = 20,
    window_long: int = 50,
) -> Signal | None:
    """Moving Average Crossover strategy.

    Generates a BUY signal when the short SMA crosses above the long SMA.
    Generates a SELL (FLAT) signal when it crosses back below.
    Requires window_long days of price history before generating signals.
    """
    # Use close price from store for accurate historical prices
    hist = store.equity_data(ticker).date_range(
        start=date - timedelta(days=window_long * 2),
        end=date,
    )
    prices = [store.get_price(ticker, d) for d in hist]
    prices = [p for p in prices if p is not None]

    if len(prices) < window_long:
        return None

    short_sma = sum(prices[-window_short:]) / window_short
    long_sma = sum(prices[-window_long:]) / window_long

    # Previous day SMAs
    if len(prices) > window_long:
        prev_prices = prices[:-1]
        prev_short = sum(prev_prices[-window_short:]) / window_short
        prev_long = sum(prev_prices[-window_long:]) / window_long
    else:
        prev_short, prev_long = None, None

    price = store.get_price(ticker, date)
    if price is None:
        return None

    # Crossover detection
    if prev_short is not None and prev_long is not None:
        was_above = prev_short >= prev_long
        is_above = short_sma >= long_sma

        if not was_above and is_above:
            return Signal(date=date, ticker=ticker, side=SignalSide.LONG, price=price,
                          reason=f"Golden cross: SMA{window_short}={short_sma:.2f} > SMA{window_long}={long_sma:.2f}")
        if was_above and not is_above:
            return Signal(date=date, ticker=ticker, side=SignalSide.FLAT, price=price,
                          reason=f"Death cross: SMA{window_short}={short_sma:.2f} < SMA{window_long}={long_sma:.2f}")

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    DATA_DIR = Path("data")
    TICKER = "SPY"
    START_DATE = date(2025, 3, 1)   # wait for 50-day SMA to warm up
    END_DATE = date(2025, 12, 31)

    print("=" * 65)
    print("Moving Average Crossover Backtest")
    print("=" * 65)

    # ── Load data ──────────────────────────────────────────────────────────────
    print("\n[1] Loading data from Parquet files ...")
    store = DataLoader.load_store([TICKER], DATA_DIR)
    dates = store.trading_dates(start=START_DATE, end=END_DATE)
    print(f"    Store: {store}")
    print(f"    Backtest period: {START_DATE} -> {END_DATE}  ({len(dates)} trading days)")

    # ── Build equities ─────────────────────────────────────────────────────────
    equities = {}
    for ticker in store.tickers():
        price = store.get_price(ticker, store.next_trading_date(START_DATE) or START_DATE)
        equities[ticker] = Equity(ticker=ticker, current_price=price)

    # ── Create portfolio ───────────────────────────────────────────────────────
    portfolio = Portfolio(name="MA Crossover SPY", cash=100_000.0)
    print(f"\n[2] Portfolio: starting cash = ${portfolio.cash:,.2f}")

    # ── Run backtest ──────────────────────────────────────────────────────────
    print("\n[3] Running backtest ...")

    backtester = Backtester(
        store=store,
        portfolio=portfolio,
        equities=equities,
        strategy=ma_crossover_strategy,
    )

    results = backtester.run(start=START_DATE, end=END_DATE)

    # ── Print daily log ───────────────────────────────────────────────────────
    print("\n[4] Daily log:")
    print(f"{'Date':<12} {'SPY':>8} {'Signal':>6} {'Position':>8} {'NAV':>12} {'Unreal. P&L':>12} {'Realised P&L':>12} {'Trade'}")
    print("-" * 100)

    for row in results:
        trade_str = f"  <- {row['trade']}" if row["trade"] else ""
        print(
            f"{str(row['date']):<12}"
            f"{row['spy_price']:>8.2f}"
            f"{row['signal']:>6}"
            f"{row['position']:>8}"
            f"{row['nav']:>12,.2f}"
            f"{row['unrealised_pnl']:>12,.2f}"
            f"{row['realised_pnl']:>12,.2f}"
            f"{trade_str}"
        )

    # ── Performance summary ────────────────────────────────────────────────────
    first = results[0]
    last = results[-1]

    total_return = (last["nav"] - first["nav"]) / first["nav"] * 100
    spy_ret = (last["spy_price"] - first["spy_price"]) / first["spy_price"] * 100

    trades = [r for r in results if r["trade"]]
    wins = sum(1 for r in results if "BUY" in r["trade"] or "SELL" in r["trade"])

    print("\n[5] Performance Summary")
    print("=" * 65)
    print(f"  Strategy        : MA Crossover (SMA20 / SMA50) on {TICKER}")
    print(f"  Period          : {first['date']} -> {last['date']}")
    print(f"  Trading days    : {len(results)}")
    print(f"  Total trades    : {len(trades)}")
    print(f"  Start NAV       : ${first['nav']:,.2f}")
    print(f"  End NAV         : ${last['nav']:,.2f}")
    print(f"  Strategy return : {total_return:.2f}%")
    print(f"  SPY buy-hold    : {spy_ret:.2f}%")
    print(f"  Alpha           : {total_return - spy_ret:.2f}%")
    print(f"  Max unreal. P&L : ${max(r['unrealised_pnl'] for r in results):,.2f}")
    print(f"  Min unreal. P&L : ${min(r['unrealised_pnl'] for r in results):,.2f}")
    print()
    s = portfolio.summary()
    for k, v in s.items():
        print(f"  {k}: {v}")

    print("\nDone.")
