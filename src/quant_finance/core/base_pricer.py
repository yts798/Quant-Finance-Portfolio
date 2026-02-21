from abc import ABC, abstractmethod
from ..core.base_instrument import BaseInstrument, MarketDataSnapshot


class BasePricer(ABC):
    """
    Abstract base class for all pricing engines.
    Every pricer must implement price() and (optionally) greeks.
    """

    @abstractmethod
    def price(self, instrument: BaseInstrument, market: MarketDataSnapshot) -> float:
        """Return the price of the instrument under given market data"""
        pass

    def delta(self, instrument: BaseInstrument, market: MarketDataSnapshot) -> float:
        """Default stub – override in concrete pricers when possible"""
        return 0.0

    def vega(self, instrument: BaseInstrument, market: MarketDataSnapshot) -> float:
        return 0.0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"