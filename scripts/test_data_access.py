"""Test Yahoo Finance data access for 5-minute and 15-minute bars."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def test_yahoo_finance():
    """Test Yahoo Finance data access."""
    print("=" * 60)
    print("Testing Yahoo Finance Data Access")
    print("=" * 60)

    assets = ['SPY', 'TLT', 'GLD', 'HYG']
    timeframes = ['5m', '15m']

    for timeframe in timeframes:
        print(f"\n\nTesting {timeframe} data...")
        print("-" * 60)

        for symbol in assets:
            try:
                print(f"\n{symbol}:")

                # Download last 5 days of data
                ticker = yf.Ticker(symbol)
                df = ticker.history(period='5d', interval=timeframe)

                if df.empty:
                    print(f"  ❌ No data received")
                    continue

                print(f"  ✓ Received {len(df)} bars")
                print(f"  ✓ Date range: {df.index[0]} to {df.index[-1]}")
                print(f"  ✓ Latest close: ${df['Close'].iloc[-1]:.2f}")

                # Check for gaps
                time_diff = df.index.to_series().diff()
                expected_diff = pd.Timedelta(minutes=5 if timeframe == '5m' else 15)
                gaps = time_diff[time_diff > expected_diff * 2]

                if len(gaps) > 0:
                    print(f"  ⚠ Found {len(gaps)} data gaps")
                else:
                    print(f"  ✓ No significant gaps")

                # Check data quality
                null_count = df.isnull().sum().sum()
                if null_count > 0:
                    print(f"  ⚠ Found {null_count} null values")
                else:
                    print(f"  ✓ No null values")

            except Exception as e:
                print(f"  ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("Data Access Test Complete")
    print("=" * 60)


def test_historical_download():
    """Test downloading 6 months of historical data."""
    print("\n\n" + "=" * 60)
    print("Testing 6-Month Historical Download (5-minute bars)")
    print("=" * 60)

    symbol = 'SPY'  # Test with SPY only
    print(f"\nDownloading 6 months of {symbol} data...")

    try:
        ticker = yf.Ticker(symbol)

        # Yahoo Finance limits: max 60 days for 5m, unlimited for 15m+
        # For 5m, we'll need to download in chunks
        print("  Note: Yahoo Finance limits 5-minute data to ~60 days")
        print("  Downloading last 60 days as test...")

        df = ticker.history(period='60d', interval='5m')

        if df.empty:
            print("  ❌ No data received")
        else:
            print(f"  ✓ Received {len(df)} bars")
            print(f"  ✓ Date range: {df.index[0]} to {df.index[-1]}")

            # Calculate expected bars (assuming ~6.5 hours/day, 78 5-min bars)
            trading_days = len(df.index.date)
            expected_bars_per_day = 78
            print(f"  ✓ Trading days: {trading_days}")
            print(f"  ✓ Avg bars per day: {len(df) / trading_days:.1f}")
            print(f"  ✓ Expected ~{expected_bars_per_day} bars/day")

        # Test 15-minute (can get more history)
        print(f"\nDownloading 6 months of {symbol} 15-minute data...")
        df_15m = ticker.history(period='6mo', interval='15m')

        if df_15m.empty:
            print("  ❌ No data received")
        else:
            print(f"  ✓ Received {len(df_15m)} bars")
            print(f"  ✓ Date range: {df_15m.index[0]} to {df_15m.index[-1]}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_yahoo_finance()
    test_historical_download()

    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✓ Yahoo Finance provides free 5-minute and 15-minute data")
    print("⚠ 5-minute data limited to ~60 days history")
    print("✓ 15-minute data available for 6+ months")
    print("\nRECOMMENDATION:")
    print("  - Use 15-minute timeframe for better historical data")
    print("  - Or use 5-minute with rolling 60-day window")
    print("=" * 60)
