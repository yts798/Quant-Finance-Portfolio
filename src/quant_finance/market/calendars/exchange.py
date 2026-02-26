# Wrapper around exchange_calendars library
# src/quant_finance/market/calendars/exchange.py
import exchange_calendars as xcals
from datetime import date, datetime, time
from typing import Union, Optional

from .base import BusinessCalendar


class ExchangeCalendar(BusinessCalendar):
    """
    Thin wrapper around exchange_calendars.ExchangeCalendar
    Makes it fit our abstract interface + adds some convenience.
    """

    def __init__(self, exchange_code: str):
        """
        Examples:
            - "XHKG"     → Hong Kong Stock Exchange
            - "XNYS"     → NYSE
            - "XAMS"     → Euronext Amsterdam
            - "XSHG"     → Shanghai (SSE)
        Full list: xcals.calendar_names()
        """
        self._cal = xcals.get_calendar(exchange_code)
        self._code = exchange_code

    @property
    def tz(self) -> str:
        return self._cal.tz.zone

    def is_session(self, dt: Union[date, datetime]) -> bool:
        return self._cal.is_session(dt)

    def is_trading_day(self, dt: Union[date, datetime]) -> bool:
        return self.is_session(dt)

    def is_holiday(self, dt: Union[date, datetime]) -> bool:
        return not self.is_session(dt) and not self._cal.is_weekend(dt)

    def is_early_close(self, dt: Union[date, datetime]) -> bool:
        return self._cal.is_early_close(dt)

    def market_open_time(self, dt: date) -> Optional[datetime]:
        if not self.is_session(dt):
            return None
        schedule = self._cal.schedule(start_date=dt, end_date=dt)
        return schedule.loc[dt.date(), "market_open"] if not schedule.empty else None

    def market_close_time(self, dt: date) -> Optional[datetime]:
        if not self.is_session(dt):
            return None
        schedule = self._cal.schedule(start_date=dt, end_date=dt)
        return schedule.loc[dt.date(), "market_close"] if not schedule.empty else None

    def next_open(self, after: datetime) -> datetime:
        return self._cal.next_open(after)

    def previous_close(self, before: datetime) -> datetime:
        return self._cal.previous_close(before)

    def __repr__(self) -> str:
        return f"<ExchangeCalendar {self._code} ({self.tz})>"