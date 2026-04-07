import pandas as pd
from .base import BaseExecutionStrategy

class VWAPStrategy(BaseExecutionStrategy):
    """Volume-Weighted Average Price execution.
    Slices based on volume profile — ideal for hiding in liquidity.
    Integrates with your quant-finance backtester."""
    
    def calculate_vwap(self, df: pd.DataFrame) -> float:
        """Benchmark VWAP for the period."""
        return (df['close'] * df['volume']).sum() / df['volume'].sum()
    
    def generate_schedule(self,
                         market_data: pd.DataFrame,
                         order_size: int,
                         start_ts: pd.Timestamp,
                         end_ts: pd.Timestamp) -> pd.DataFrame:
        self._risk_check_liquidity(market_data, order_size)
        
        # Filter to execution window (assumes market_data has datetime index or 'timestamp' col)
        mask = (market_data.index >= start_ts) & (market_data.index <= end_ts)
        window = market_data.loc[mask].copy()
        
        if window.empty or window['volume'].sum() == 0:
            raise ValueError("No volume in execution window — high non-execution risk!")
        
        total_vol = window['volume'].sum()
        window['volume_weight'] = window['volume'] / total_vol
        window['shares'] = (window['volume_weight'] * order_size).round().astype(int)
        
        # Risk cap per slice
        window['shares'] = window['shares'].clip(upper=int(order_size * self.max_participation))
        
        # Expected price per slice (cumulative VWAP)
        window['expected_price'] = (window['close'] * window['volume']).cumsum() / window['volume'].cumsum()
        
        print(f"✅ VWAP schedule generated | Order: {order_size} shares | Benchmark VWAP: {self.calculate_vwap(window):.4f}")
        return window[['shares', 'expected_price', 'close', 'volume']]