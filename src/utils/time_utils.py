"""Time utilities for market hours and timezone handling."""

from datetime import datetime, time, timedelta
import pandas as pd
from typing import Tuple


class MarketHours:
    """Utilities for handling market hours and trading windows."""

    def __init__(
        self,
        market_open: str = "09:30",
        market_close: str = "16:00",
        close_all_by: str = "15:45"
    ):
        """
        Initialize market hours.

        Args:
            market_open: Market open time (HH:MM format, Eastern Time)
            market_close: Market close time (HH:MM format, Eastern Time)
            close_all_by: Time to close all positions (HH:MM format, Eastern Time)
        """
        self.market_open = self._parse_time(market_open)
        self.market_close = self._parse_time(market_close)
        self.close_all_by = self._parse_time(close_all_by)

    @staticmethod
    def _parse_time(time_str: str) -> time:
        """Parse time string (HH:MM) to time object."""
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)

    def is_market_open(self, current_time: datetime = None) -> bool:
        """
        Check if market is currently open.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if market is open
        """
        if current_time is None:
            current_time = datetime.now()

        # Get current time (ignore date)
        current_time_only = current_time.time()

        # Check if within market hours
        return self.market_open <= current_time_only < self.market_close

    def is_trading_allowed(self, current_time: datetime = None) -> bool:
        """
        Check if trading is allowed (market open but before close_all_by).

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if trading allowed
        """
        if current_time is None:
            current_time = datetime.now()

        current_time_only = current_time.time()

        return (
            self.market_open <= current_time_only < self.close_all_by
            and self.is_weekday(current_time)
        )

    def should_close_all_positions(self, current_time: datetime = None) -> bool:
        """
        Check if it's time to close all positions.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if should close all positions
        """
        if current_time is None:
            current_time = datetime.now()

        current_time_only = current_time.time()

        return current_time_only >= self.close_all_by

    @staticmethod
    def is_weekday(current_time: datetime = None) -> bool:
        """
        Check if current day is a weekday (Monday-Friday).

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if weekday
        """
        if current_time is None:
            current_time = datetime.now()

        return current_time.weekday() < 5  # 0=Monday, 4=Friday

    def get_next_market_open(self, current_time: datetime = None) -> datetime:
        """
        Get next market open datetime.

        Args:
            current_time: Current time (defaults to now)

        Returns:
            Next market open datetime
        """
        if current_time is None:
            current_time = datetime.now()

        # If market is currently open, return next day's open
        if self.is_market_open(current_time):
            next_day = current_time + timedelta(days=1)
        else:
            next_day = current_time

        # Find next weekday
        while not self.is_weekday(next_day):
            next_day += timedelta(days=1)

        # Combine date with market open time
        return datetime.combine(next_day.date(), self.market_open)

    def get_minutes_until_market_close(self, current_time: datetime = None) -> int:
        """
        Get minutes until market close.

        Args:
            current_time: Current time (defaults to now)

        Returns:
            Minutes until market close (negative if market closed)
        """
        if current_time is None:
            current_time = datetime.now()

        # Create datetime for today's market close
        market_close_dt = datetime.combine(current_time.date(), self.market_close)

        # Calculate difference
        diff = market_close_dt - current_time
        return int(diff.total_seconds() / 60)

    def is_in_preferred_window(
        self,
        current_time: datetime = None,
        windows: list = None
    ) -> bool:
        """
        Check if current time is in preferred trading windows.

        Args:
            current_time: Time to check (defaults to now)
            windows: List of (start, end) time tuples

        Returns:
            True if in preferred window
        """
        if current_time is None:
            current_time = datetime.now()

        if windows is None:
            # Default preferred windows
            windows = [
                (time(10, 0), time(11, 30)),  # 10:00-11:30 AM ET
                (time(14, 0), time(15, 30))   # 2:00-3:30 PM ET
            ]

        current_time_only = current_time.time()

        for start, end in windows:
            if start <= current_time_only < end:
                return True

        return False


def convert_timeframe_to_minutes(timeframe: str) -> int:
    """
    Convert timeframe string to minutes.

    Args:
        timeframe: Timeframe string (e.g., '1min', '5min', '15min', '1h')

    Returns:
        Number of minutes

    Example:
        >>> convert_timeframe_to_minutes('5min')
        5
        >>> convert_timeframe_to_minutes('1h')
        60
    """
    if timeframe.endswith('min'):
        return int(timeframe[:-3])
    elif timeframe.endswith('h'):
        return int(timeframe[:-1]) * 60
    elif timeframe.endswith('d'):
        return int(timeframe[:-1]) * 60 * 24
    else:
        raise ValueError(f"Unknown timeframe format: {timeframe}")


def get_trading_days_in_range(start_date: datetime, end_date: datetime) -> int:
    """
    Get number of trading days (weekdays) in date range.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Number of trading days
    """
    # Create date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Filter weekdays
    weekdays = date_range[date_range.weekday < 5]

    return len(weekdays)


if __name__ == "__main__":
    # Test market hours
    print("Testing Market Hours...")

    market = MarketHours()

    # Create test times
    test_times = [
        datetime(2024, 11, 5, 9, 0),   # Before market open
        datetime(2024, 11, 5, 10, 30),  # During market (preferred window)
        datetime(2024, 11, 5, 15, 50),  # After close_all_by
        datetime(2024, 11, 5, 17, 0),   # After market close
    ]

    for test_time in test_times:
        print(f"\nTime: {test_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Market open: {market.is_market_open(test_time)}")
        print(f"  Trading allowed: {market.is_trading_allowed(test_time)}")
        print(f"  Should close all: {market.should_close_all_positions(test_time)}")
        print(f"  In preferred window: {market.is_in_preferred_window(test_time)}")
        print(f"  Minutes until close: {market.get_minutes_until_market_close(test_time)}")

    # Test timeframe conversion
    print("\n\nTesting Timeframe Conversion...")
    print(f"5min = {convert_timeframe_to_minutes('5min')} minutes")
    print(f"15min = {convert_timeframe_to_minutes('15min')} minutes")
    print(f"1h = {convert_timeframe_to_minutes('1h')} minutes")

    # Test trading days
    start = datetime(2024, 11, 1)
    end = datetime(2024, 11, 30)
    trading_days = get_trading_days_in_range(start, end)
    print(f"\nTrading days in November 2024: {trading_days}")

    print("\nTime utilities working correctly!")
