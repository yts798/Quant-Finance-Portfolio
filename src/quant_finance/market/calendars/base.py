# Abstract base class for all calendars
# src/quant_finance/market/calendars/base.py
from abc import ABC, abstractmethod
from datetime import date, datetime, time
from typing import Union, Optional, List


class BusinessCalendar(ABC):
    """
    Abstract base for any trading/business day calendar.
    Compatible with exchange_calendars style but more general.
    """

    @abstractmethod
    def is_session(self, dt: Union[date, datetime]) -> bool:
        """True if this is a full trading session day (open + close)."""
        pass

    @abstractmethod
    def is_trading_day(self, dt: Union[date, datetime]) -> bool:
        """Alias for is_session — most people mean this."""
        return self.is_session(dt)

    @abstractmethod
    def is_holiday(self, dt: Union[date, datetime]) -> bool:
        """True if market is fully closed (holiday or weekend)."""
        pass

    @abstractmethod
    def is_early_close(self, dt: Union[date, datetime]) -> bool:
        """True if market closes early on this day."""
        pass

    @abstractmethod
    def market_open_time(self, dt: date) -> Optional[datetime]:
        """Return open time (with tz) on this date, or None if closed."""
        pass

    @abstractmethod
    def market_close_time(self, dt: date) -> Optional[datetime]:
        """Return close time (with tz) on this date, or None if closed."""
        pass

    @abstractmethod
    def next_open(self, after: datetime) -> datetime:
        """Next trading session open after the given datetime."""
        pass

    @abstractmethod
    def previous_close(self, before: datetime) -> datetime:
        """Previous trading session close before the given datetime."""
        pass

    @property
    @abstractmethod
    def tz(self) -> str:
        """Timezone name, e.g. 'Asia/Hong_Kong'"""
        pass