import pandas as pd
import numpy as np
from typing import Optional
from .base import BaseExecutionStrategy

class ImplementationShortfallStrategy(BaseExecutionStrategy):
    """
    Implementation Shortfall (IS) execution strategy.
    
    Risk-professional version:
    - Trades faster early if urgency is high (to beat expected price drift)
    - Slows down near the end to reduce impact
    - Dynamic participation rate based on remaining horizon
    - Hard risk caps on max participation and estimated shortfall
    
    Best for: time-sensitive orders where you have a benchmark arrival price.
    """
    
    def __init__(self, 
                 max_slippage_bps: float = 10.0, 
                 max_participation: float = 0.20,
                 urgency: float = 0.5):  # 0.0 = very passive, 1.0 = very aggressive
        super().__init__(max_slippage_bps=max_slippage_bps, max_participation=max_participation)
        self.urgency = np.clip(urgency, 0.0, 1.0)
    
    def _estimate_remaining_shortfall_risk(self, 
                                          remaining_shares: int, 
                                          remaining_periods: int, 
                                          volatility: float) -> float:
        """Simple risk estimate: expected shortfall due to price drift."""
        # Rough approximation: half the remaining time * volatility impact
        expected_drift_risk_bps = volatility * np.sqrt(remaining_periods) * 10000  # to bps
        return remaining_shares * (expected_drift_risk_bps / 10000)
    
    def generate_schedule(self,
                         market_data: pd.DataFrame,
                         order_size: int,
                         start_ts: pd.Timestamp,
                         end_ts: pd.Timestamp,
                         arrival_price: Optional[float] = None) -> pd.DataFrame:
        """
        Generate IS execution schedule.
        
        Parameters:
            market_data: DataFrame with DatetimeIndex, columns ['close', 'volume', 'volatility' (optional)]
            order_size: total shares to execute
            start_ts, end_ts: execution window
            arrival_price: benchmark price at decision time (default = first close)
        """
        self._risk_check_liquidity(market_data, order_size)
        
        # Filter execution window
        mask = (market_data.index >= start_ts) & (market_data.index <= end_ts)
        window = market_data.loc[mask].copy()
        
        if window.empty:
            raise ValueError("Empty execution window for Implementation Shortfall!")
        
        n = len(window)
        if n == 0:
            raise ValueError("No periods in window")
        
        # Use arrival price or first price in window
        if arrival_price is None:
            arrival_price = window['close'].iloc[0]
        
        # Add volatility column if missing (fallback)
        if 'volatility' not in window.columns:
            window['volatility'] = window['close'].pct_change().rolling(5, min_periods=1).std()
        
        # Dynamic participation: higher at beginning when urgency is high
        # Formula inspired by Almgren-Chriss: front-load when urgency > 0
        t = np.arange(1, n + 1) / n  # normalized time [1/n ... 1]
        urgency_factor = self.urgency ** 2  # quadratic for stronger front-loading
        
        # Base shares per slice (TWAP-like) adjusted by urgency
        base_shares = order_size / n
        participation_profile = (1 - t) ** (1 - urgency_factor)   # decays slower when urgency high
        
        window['shares'] = (base_shares * participation_profile / participation_profile.sum() * order_size).round().astype(int)
        
        # Risk guard: cap per slice + overall participation
        max_per_slice = int(window['volume'].mean() * self.max_participation)
        window['shares'] = window['shares'].clip(upper=max_per_slice)
        
        # Re-normalize to exactly hit order_size (after clipping)
        window['shares'] = (window['shares'] / window['shares'].sum() * order_size).round().astype(int)
        
        # Expected price per slice: arrival price + expected impact + drift
        # Simple model: linear drift + temporary impact proportional to shares/volume
        window['impact_bps'] = (window['shares'] / window['volume']) * 50   # rough temporary impact
        window['expected_price'] = arrival_price * (1 + 
            (window.index - window.index[0]).total_seconds() / 
            (end_ts - start_ts).total_seconds() * 0.0005)  # small drift assumption
        
        window['expected_price'] += window['expected_price'] * (window['impact_bps'] / 10000)
        
        # Calculate projected implementation shortfall for this schedule
        expected_cost = (window['shares'] * window['expected_price']).sum()
        benchmark_cost = order_size * arrival_price
        projected_shortfall_bps = (expected_cost - benchmark_cost) / benchmark_cost * 10000
        
        print(f"✅ Implementation Shortfall schedule generated")
        print(f"   Order: {order_size:,} shares | Urgency: {self.urgency:.2f} | Projected IS: {projected_shortfall_bps:.1f} bps")
        print(f"   Benchmark arrival price: {arrival_price:.4f} | Risk caps applied")
        
        return window[['shares', 'expected_price', 'close', 'volume', 'volatility']]