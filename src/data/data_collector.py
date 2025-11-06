"""Data collector for RORO Trading System - supports multiple data sources."""

import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import logger
from src.utils.config_loader import config
from src.data.data_storage import TradingDatabase


class DataCollector:
    """
    Collect market data from multiple sources.

    Supports:
    - Yahoo Finance (free, but may have access issues)
    - CSV files (manual download)
    - Database (previously stored data)
    """

    def __init__(self, db: TradingDatabase = None):
        """
        Initialize data collector.

        Args:
            db: Database instance for storing/retrieving data
        """
        self.db = db or TradingDatabase()
        self.assets = config.get_assets()
        self.timeframe = config.get_timeframe()

        logger.info(f"DataCollector initialized for {self.assets} @ {self.timeframe}")

    def fetch_from_yahoo(
        self,
        symbol: str,
        period: str = '60d',
        interval: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from Yahoo Finance.

        Args:
            symbol: Asset symbol (e.g., 'SPY')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')

        Returns:
            DataFrame with OHLCV data, or None if failed
        """
        if interval is None:
            # Convert our timeframe format to yfinance format
            interval = self.timeframe.replace('min', 'm')

        try:
            logger.info(f"Fetching {symbol} from Yahoo Finance (period={period}, interval={interval})")

            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"No data received for {symbol} from Yahoo Finance")
                return None

            # Normalize column names to title case
            df.columns = df.columns.str.title()

            logger.info(f"✓ Downloaded {len(df)} bars for {symbol} ({df.index[0]} to {df.index[-1]})")

            # Store in database
            self.db.insert_market_data(df, symbol)

            return df

        except Exception as e:
            logger.error(f"Failed to fetch {symbol} from Yahoo Finance: {e}")
            return None

    def load_from_csv(
        self,
        symbol: str,
        csv_path: str,
        date_column: str = 'Date',
        parse_dates: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Load data from CSV file.

        Args:
            symbol: Asset symbol
            csv_path: Path to CSV file
            date_column: Name of date/timestamp column
            parse_dates: Whether to parse dates

        Returns:
            DataFrame with OHLCV data, or None if failed

        CSV Format Expected:
            Date,Open,High,Low,Close,Volume
            2024-11-05 09:30:00,450.00,451.00,449.50,450.50,1000000
        """
        try:
            logger.info(f"Loading {symbol} from CSV: {csv_path}")

            # Read CSV
            df = pd.read_csv(
                csv_path,
                parse_dates=[date_column] if parse_dates else None,
                index_col=date_column if parse_dates else None
            )

            # Normalize column names to title case
            df.columns = df.columns.str.title()

            # Validate required columns
            required_cols = ['Open', 'High', 'Low', 'Close']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                logger.error(f"CSV missing required columns: {missing_cols}")
                return None

            logger.info(f"✓ Loaded {len(df)} bars for {symbol} from CSV")

            # Store in database
            self.db.insert_market_data(df, symbol)

            return df

        except Exception as e:
            logger.error(f"Failed to load {symbol} from CSV: {e}")
            return None

    def load_from_database(
        self,
        symbol: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Optional[pd.DataFrame]:
        """
        Load data from database.

        Args:
            symbol: Asset symbol
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            DataFrame with OHLCV data, or None if no data
        """
        try:
            logger.info(f"Loading {symbol} from database")

            df = self.db.get_market_data(symbol, start_date, end_date)

            if df.empty:
                logger.warning(f"No data found in database for {symbol}")
                return None

            # Normalize column names to title case
            df.columns = df.columns.str.title()

            logger.info(f"✓ Loaded {len(df)} bars for {symbol} from database")

            return df

        except Exception as e:
            logger.error(f"Failed to load {symbol} from database: {e}")
            return None

    def get_data(
        self,
        symbol: str,
        period: str = '60d',
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Get data using fallback strategy.

        Priority:
        1. Database (if not force_refresh)
        2. Yahoo Finance
        3. CSV file (if exists)

        Args:
            symbol: Asset symbol
            period: Time period for Yahoo Finance
            force_refresh: Force download from Yahoo even if data in database

        Returns:
            DataFrame with OHLCV data, or None if all sources fail
        """
        # Try database first (unless force refresh)
        if not force_refresh:
            df = self.load_from_database(symbol)
            if df is not None and not df.empty:
                return df

        # Try Yahoo Finance
        df = self.fetch_from_yahoo(symbol, period=period)
        if df is not None and not df.empty:
            return df

        # Try CSV file in data/historical/
        csv_path = project_root / "data" / "historical" / f"{symbol}_{self.timeframe}.csv"
        if csv_path.exists():
            logger.info(f"Trying CSV file: {csv_path}")
            df = self.load_from_csv(symbol, str(csv_path))
            if df is not None and not df.empty:
                return df

        logger.error(f"All data sources failed for {symbol}")
        return None

    def download_all_assets(
        self,
        period: str = '60d',
        force_refresh: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Download data for all configured assets.

        Args:
            period: Time period
            force_refresh: Force refresh from source

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        logger.info(f"Downloading data for all assets: {self.assets}")

        data = {}

        for symbol in self.assets:
            df = self.get_data(symbol, period=period, force_refresh=force_refresh)
            if df is not None:
                data[symbol] = df
            else:
                logger.warning(f"Failed to get data for {symbol}")

        success_count = len(data)
        total_count = len(self.assets)

        logger.info(f"Download complete: {success_count}/{total_count} assets successful")

        return data

    def validate_data_quality(self, df: pd.DataFrame, symbol: str) -> bool:
        """
        Validate data quality.

        Checks:
        - No null values in OHLC
        - No extreme price changes (>5% per bar)
        - Timestamps are sequential

        Args:
            df: DataFrame to validate
            symbol: Symbol name (for logging)

        Returns:
            True if data passes quality checks
        """
        issues = []

        # Check for nulls
        null_count = df[['Open', 'High', 'Low', 'Close']].isnull().sum().sum()
        if null_count > 0:
            issues.append(f"{null_count} null values in OHLC")

        # Check for extreme price changes
        max_change_pct = config.get('data.max_price_change_pct', 5.0)
        price_changes = df['Close'].pct_change().abs() * 100
        extreme_changes = price_changes[price_changes > max_change_pct]

        if len(extreme_changes) > 0:
            issues.append(f"{len(extreme_changes)} bars with price change >{max_change_pct}%")

        # Check timestamp sequence
        if not df.index.is_monotonic_increasing:
            issues.append("Timestamps are not sequential")

        # Check for duplicate timestamps
        if df.index.duplicated().any():
            dup_count = df.index.duplicated().sum()
            issues.append(f"{dup_count} duplicate timestamps")

        if issues:
            logger.warning(f"Data quality issues for {symbol}: {'; '.join(issues)}")
            return False
        else:
            logger.info(f"✓ Data quality check passed for {symbol}")
            return True


if __name__ == "__main__":
    # Test data collector
    print("Testing Data Collector...")
    print("=" * 60)

    collector = DataCollector()

    # Test with SPY
    print("\n1. Testing data download for SPY...")
    df = collector.get_data('SPY', period='5d')

    if df is not None:
        print(f"✓ Got data: {len(df)} bars")
        print(f"  Date range: {df.index[0]} to {df.index[-1]}")
        print(f"  Latest close: ${df['Close'].iloc[-1]:.2f}")

        # Test validation
        print("\n2. Testing data validation...")
        is_valid = collector.validate_data_quality(df, 'SPY')
        print(f"  Validation: {'✓ PASS' if is_valid else '❌ FAIL'}")
    else:
        print("❌ Failed to get data")
        print("\nNote: If Yahoo Finance doesn't work in your environment,")
        print("you can manually download CSV files and place them in:")
        print(f"  {project_root / 'data' / 'historical' / 'SPY_5min.csv'}")
        print("\nCSV format:")
        print("  Date,Open,High,Low,Close,Volume")
        print("  2024-11-05 09:30:00,450.00,451.00,449.50,450.50,1000000")

    print("\n" + "=" * 60)
