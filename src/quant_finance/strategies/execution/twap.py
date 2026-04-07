import pandas as pd
from .base import BaseExecutionStrategy

class TWAPStrategy(BaseExecutionStrategy):
    """Time-Weighted Average Price execution.
    Even time slices — simple and robust when volume is noisy."""
    
    def generate_schedule(self,
                         market_data: pd.DataFrame,
                         order_size: int,
                         start_ts: pd.Timestamp,
                         end_ts: pd.Timestamp) -> pd.DataFrame:
        self._risk_check_liquidity(market_data, order_size)
        
        mask = (market_data.index >= start_ts) & (market_data.index <= end_ts)
        window = market_data.loc[mask].copy()
        
        if window.empty:
            raise ValueError("Empty window for TWAP — check your data timestamps!")
        
        num_slices = len(window)
        base_shares = order_size // num_slices
        remainder = order_size % num_slices
        
        window['shares'] = base_shares
        window.iloc[:remainder, window.columns.get_loc('shares')] += 1
        
        # Risk cap
        max_per_slice = int(window['volume'].mean() * self.max_participation)
        window['shares'] = window['shares'].clip(upper=max_per_slice)
        
        window['expected_price'] = window['close'].expanding().mean()  # or rolling if preferred
        
        print(f"✅ TWAP schedule generated | Order: {order_size} shares | {num_slices} slices")
        return window[['shares', 'expected_price', 'close', 'volume']]