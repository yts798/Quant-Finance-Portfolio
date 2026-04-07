from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd

class BaseExecutionStrategy(ABC):
    """Base for execution strategies in your quant-finance project.
    Risk-first design: liquidity checks + slippage caps."""
    
    def __init__(self, max_slippage_bps: float = 10.0, max_participation: float = 0.15):
        self.max_slippage_bps = max_slippage_bps      # e.g., 10 bps max deviation
        self.max_participation = max_participation     # never eat more than X% of volume
    
    @abstractmethod
    def generate_schedule(self, 
                         market_data: pd.DataFrame, 
                         order_size: int, 
                         start_ts: pd.Timestamp, 
                         end_ts: pd.Timestamp) -> pd.DataFrame:
        """Return schedule df with columns: timestamp, shares, expected_price, etc."""
        pass
    
    def _risk_check_liquidity(self, market_data: pd.DataFrame, order_size: int) -> None:
        """Reuse or extend your existing risk module here."""
        avg_vol = market_data['volume'].mean()
        if order_size > avg_vol * self.max_participation * len(market_data):
            raise ValueError(f"🚨 RISK BREACH: Order size {order_size} exceeds liquidity limit "
                             f"(max ~{int(avg_vol * self.max_participation * len(market_data))})")