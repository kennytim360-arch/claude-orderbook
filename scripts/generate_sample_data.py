"""Generate sample data for testing when Yahoo Finance is unavailable."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent
data_dir = project_root / "data" / "historical"
data_dir.mkdir(parents=True, exist_ok=True)


def generate_sample_data(
    symbol: str,
    base_price: float,
    num_days: int = 60,
    timeframe_minutes: int = 5,
    volatility: float = 0.01
):
    """
    Generate sample OHLCV data with realistic price movement.

    Args:
        symbol: Asset symbol
        base_price: Starting price
        num_days: Number of trading days to generate
        timeframe_minutes: Bar size in minutes (5 or 15)
        volatility: Daily volatility (0.01 = 1%)
    """
    print(f"Generating {num_days} days of {timeframe_minutes}-min data for {symbol}...")

    # Generate timestamps (market hours: 9:30 AM - 4:00 PM ET)
    timestamps = []
    current_date = datetime.now() - timedelta(days=num_days)

    for day in range(num_days):
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        # Market hours: 9:30 - 16:00 (6.5 hours = 390 minutes)
        market_open = current_date.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = current_date.replace(hour=16, minute=0, second=0, microsecond=0)

        current_time = market_open
        while current_time < market_close:
            timestamps.append(current_time)
            current_time += timedelta(minutes=timeframe_minutes)

        current_date += timedelta(days=1)

    num_bars = len(timestamps)
    print(f"  Generated {num_bars} bars")

    # Generate price data with realistic movement
    np.random.seed(42)  # For reproducibility

    # Random walk with drift
    returns = np.random.normal(
        loc=0.0001,  # Slight upward drift
        scale=volatility / np.sqrt(390 / timeframe_minutes),  # Scaled to bar size
        size=num_bars
    )

    # Calculate prices
    close_prices = base_price * np.exp(np.cumsum(returns))

    # Generate OHLC from close prices
    data = []
    for i, (timestamp, close) in enumerate(zip(timestamps, close_prices)):
        # Random intrabar movement
        bar_range = close * np.random.uniform(0.001, 0.003)  # 0.1-0.3% range

        high = close + np.random.uniform(0, bar_range)
        low = close - np.random.uniform(0, bar_range)
        open_price = close + np.random.uniform(-bar_range/2, bar_range/2)

        # Ensure OHLC relationships are valid
        high = max(high, open_price, close)
        low = min(low, open_price, close)

        volume = int(np.random.lognormal(mean=14, sigma=0.5))  # Realistic volume distribution

        data.append({
            'Date': timestamp,
            'Open': round(open_price, 2),
            'High': round(high, 2),
            'Low': round(low, 2),
            'Close': round(close, 2),
            'Volume': volume
        })

    # Create DataFrame
    df = pd.DataFrame(data)

    # Save to CSV
    filename = f"{symbol}_{timeframe_minutes}min.csv"
    filepath = data_dir / filename
    df.to_csv(filepath, index=False)

    print(f"  ✓ Saved to {filepath}")
    print(f"  Price range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")
    print(f"  Final close: ${df['Close'].iloc[-1]:.2f}")

    return df


if __name__ == "__main__":
    print("=" * 60)
    print("Generating Sample Market Data")
    print("=" * 60)
    print()

    # Generate data for all assets
    assets = [
        ('SPY', 450.00),   # S&P 500 ETF
        ('TLT', 95.00),    # Long Treasury ETF
        ('GLD', 185.00),   # Gold ETF
        ('HYG', 75.00),    # High Yield Bond ETF
    ]

    for symbol, base_price in assets:
        # Generate both 5-min and 15-min data
        for timeframe in [5, 15]:
            generate_sample_data(
                symbol=symbol,
                base_price=base_price,
                num_days=60,
                timeframe_minutes=timeframe,
                volatility=0.01  # 1% daily volatility
            )
        print()

    print("=" * 60)
    print("Sample data generation complete!")
    print(f"Files saved to: {data_dir}")
    print()
    print("You can now use the data collector with CSV files:")
    print("  collector.load_from_csv('SPY', 'data/historical/SPY_5min.csv')")
    print("=" * 60)
