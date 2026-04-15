# src/quant_finance/instruments/portfolio/portfolio.py

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from ..equity.equity import Equity
from .position import Position


class TradeSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Trade:
    """Records a single trade transaction."""

    ticker: str
    side: TradeSide
    quantity: float
    price: float
    trade_date: date

    @property
    def value(self) -> float:
        """Total value of the trade (positive for buy, negative for sell)."""
        sign = 1 if self.side == TradeSide.BUY else -1
        return sign * self.quantity * self.price


@dataclass
class Portfolio:
    """Portfolio containing multiple positions + cash with realized P&L tracking."""

    name: str = "My Portfolio"
    positions: Dict[str, Position] = field(default_factory=dict)
    transactions: List[Trade] = field(default_factory=list)
    cash: float = 0.0
    current_date: Optional[date] = None  # backtest date marker

    def set_date(self, trade_date: date) -> None:
        """Set the current backtest date."""
        self.current_date = trade_date

    def update_prices(self, prices: Dict[str, float], trade_date: Optional[date] = None) -> None:
        """Bulk-update equity prices for all positions (mark-to-market).

        Args:
            prices: dict mapping ticker -> new price
            trade_date: optional date to record in price history
        """
        for ticker, new_price in prices.items():
            if ticker in self.positions:
                self.positions[ticker].equity.update_price(new_price, trade_date)

    def holdings(self) -> List[Dict]:
        """Return a list-of-dicts table of all open positions."""
        return [pos.to_dict() for pos in self.positions.values()]

    def add_position(self, position: Position) -> None:
        """Add or update a position (no transaction recorded)."""
        self.positions[position.equity.ticker] = position

    def record_trade(self, trade: Trade, equity: Optional[Equity] = None) -> None:
        """Record a trade and update positions and cash accordingly.

        Args:
            trade: the trade to record
            equity: the Equity instrument (required for BUY of new ticker,
                    optional for SELL or adding to existing position)
        """
        self.transactions.append(trade)
        self._apply_trade(trade, equity)

    def _apply_trade(self, trade: Trade, equity: Optional[Equity]) -> None:
        """Apply a trade to the portfolio, updating positions and cash."""
        ticker = trade.ticker

        if trade.side == TradeSide.BUY:
            self._add_to_position(ticker, trade.quantity, trade.price, equity, trade.trade_date)
            self.cash -= trade.value
        else:
            self._reduce_position(ticker, trade.quantity, trade.price)
            self.cash += abs(trade.value)

    def _add_to_position(
        self,
        ticker: str,
        quantity: float,
        price: float,
        equity: Optional[Equity],
        trade_date: Optional[date] = None,
    ) -> None:
        """Add shares to an existing position or create a new one."""
        if ticker in self.positions:
            pos = self.positions[ticker]
            total_cost = pos.cost_basis + quantity * price
            new_quantity = pos.quantity + quantity
            new_avg_cost = total_cost / new_quantity
            self.positions[ticker] = Position(
                equity=pos.equity,
                quantity=new_quantity,
                average_cost=new_avg_cost,
                entry_date=pos.entry_date,  # preserve original entry date
            )
        else:
            if equity is None:
                raise ValueError(
                    f"Equity for {ticker} must be provided when opening a new position. "
                    "Call record_trade(trade, equity=equity)."
                )
            self.positions[ticker] = Position(
                equity=equity,
                quantity=quantity,
                average_cost=price,
                entry_date=trade_date,
            )

    def _reduce_position(self, ticker: str, quantity: float, price: float) -> float:
        """Reduce a position. Returns the realized P&L from the sale."""
        if ticker not in self.positions:
            raise ValueError(f"No position found for {ticker}")

        pos = self.positions[ticker]
        if abs(quantity) > abs(pos.quantity):
            raise ValueError(
                f"Cannot sell {quantity} shares of {ticker}: only {pos.quantity} shares held"
            )

        realized_pnl = (price - pos.average_cost) * quantity
        new_quantity = pos.quantity - quantity

        if new_quantity == 0:
            del self.positions[ticker]
        else:
            self.positions[ticker] = Position(
                equity=pos.equity,
                quantity=new_quantity,
                average_cost=pos.average_cost,
                entry_date=pos.entry_date,
            )

        return realized_pnl

    @property
    def total_realized_pnl(self) -> float:
        """Total realized P&L from all closed trades."""
        return sum(self.realized_pnl_by_ticker().values())

    def realized_pnl_by_ticker(self) -> Dict[str, float]:
        """Realized P&L broken down by ticker."""
        result: Dict[str, float] = {}

        # Track running cost basis per ticker to compute realized P&L
        cost_basis_per_share: Dict[str, float] = {}
        shares_held: Dict[str, float] = {}

        for trade in self.transactions:
            ticker = trade.ticker

            if trade.side == TradeSide.BUY:
                if ticker not in shares_held:
                    shares_held[ticker] = 0.0
                    cost_basis_per_share[ticker] = 0.0

                old_shares = shares_held[ticker]
                old_cost = cost_basis_per_share[ticker]
                new_shares = old_shares + trade.quantity
                new_cost = (old_cost * old_shares + trade.quantity * trade.price) / new_shares

                shares_held[ticker] = new_shares
                cost_basis_per_share[ticker] = new_cost

            else:  # SELL
                if ticker not in shares_held or shares_held[ticker] == 0:
                    raise ValueError(f"Sell trade for {ticker} but no shares held")

                pnl = (trade.price - cost_basis_per_share[ticker]) * trade.quantity
                result[ticker] = result.get(ticker, 0.0) + pnl
                shares_held[ticker] -= trade.quantity

        return result

    @property
    def total_unrealized_pnl(self) -> float:
        """Total unrealized profit & loss across all open positions."""
        return sum(pos.unrealized_pnl() for pos in self.positions.values())

    def total_value(self) -> float:
        """Total portfolio value = cash plus sum of all position values."""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value

    def total_cost_basis(self) -> float:
        """Total cost basis of all open positions."""
        return sum(pos.cost_basis for pos in self.positions.values())

    def summary(self) -> Dict:
        """Return a summary dict of portfolio metrics."""
        realized = self.realized_pnl_by_ticker()
        return {
            "name": self.name,
            "cash": self.cash,
            "positions_value": sum(pos.market_value for pos in self.positions.values()),
            "total_value": self.total_value(),
            "total_realized_pnl": sum(realized.values()),
            "total_unrealized_pnl": self.total_unrealized_pnl,
            "total_cost_basis": self.total_cost_basis(),
            "num_positions": len(self.positions),
            "num_transactions": len(self.transactions),
        }

    def __repr__(self) -> str:
        return (
            f"Portfolio('{self.name}', "
            f"Positions={len(self.positions)}, "
            f"Cash=${self.cash:,.2f}, "
            f"Total Value=${self.total_value():,.2f})"
        )
