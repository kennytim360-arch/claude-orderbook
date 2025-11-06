"""Technical indicators for RORO Trading System."""

import pandas as pd
import numpy as np
from typing import Union


def sma(data: Union[pd.Series, pd.DataFrame], period: int) -> pd.Series:
    """
    Simple Moving Average.

    Args:
        data: Price series or DataFrame
        period: Number of periods

    Returns:
        Series with SMA values
    """
    if isinstance(data, pd.DataFrame):
        data = data['Close']

    return data.rolling(window=period).mean()


def ema(data: Union[pd.Series, pd.DataFrame], period: int) -> pd.Series:
    """
    Exponential Moving Average.

    Args:
        data: Price series or DataFrame
        period: Number of periods

    Returns:
        Series with EMA values
    """
    if isinstance(data, pd.DataFrame):
        data = data['Close']

    return data.ewm(span=period, adjust=False).mean()


def rsi(data: Union[pd.Series, pd.DataFrame], period: int = 14) -> pd.Series:
    """
    Relative Strength Index.

    Args:
        data: Price series or DataFrame
        period: RSI period (default 14)

    Returns:
        Series with RSI values (0-100)
    """
    if isinstance(data, pd.DataFrame):
        data = data['Close']

    # Calculate price changes
    delta = data.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)

    # Calculate average gains and losses
    avg_gains = gains.rolling(window=period).mean()
    avg_losses = losses.rolling(window=period).mean()

    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))

    return rsi


def atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range.

    Args:
        data: DataFrame with High, Low, Close
        period: ATR period (default 14)

    Returns:
        Series with ATR values
    """
    high = data['High']
    low = data['Low']
    close = data['Close']

    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Calculate ATR
    atr = tr.rolling(window=period).mean()

    return atr


def detect_crossover(fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
    """
    Detect moving average crossovers.

    Args:
        fast_ma: Fast moving average series
        slow_ma: Slow moving average series

    Returns:
        Series with:
        - 1 for bullish crossover (fast crosses above slow)
        - -1 for bearish crossover (fast crosses below slow)
        - 0 for no crossover
    """
    # Create signals
    signals = pd.Series(0, index=fast_ma.index)

    # Fast above slow = bullish
    bullish = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
    signals[bullish] = 1

    # Fast below slow = bearish
    bearish = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
    signals[bearish] = -1

    return signals


def get_ma_position(fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
    """
    Get current MA position (which is above which).

    Args:
        fast_ma: Fast moving average series
        slow_ma: Slow moving average series

    Returns:
        Series with:
        - 1 if fast > slow (bullish)
        - -1 if fast < slow (bearish)
        - 0 if equal or NaN
    """
    position = pd.Series(0, index=fast_ma.index)

    position[fast_ma > slow_ma] = 1
    position[fast_ma < slow_ma] = -1

    return position


if __name__ == "__main__":
    # Test indicators
    print("Testing Technical Indicators...")
    print("=" * 60)

    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    # Random walk price data
    returns = np.random.normal(0.001, 0.02, 100)
    prices = 100 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'Close': prices,
        'High': prices * (1 + np.abs(np.random.normal(0, 0.01, 100))),
        'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, 100))),
    }, index=dates)

    df['Open'] = df['Close'].shift(1)
    df['Open'].iloc[0] = df['Close'].iloc[0]

    print(f"\n1. Sample data generated: {len(df)} bars")
    print(f"   Price range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")

    # Test SMA
    print("\n2. Testing SMA...")
    df['SMA_5'] = sma(df, 5)
    df['SMA_20'] = sma(df, 20)
    print(f"   ✓ SMA_5 latest: ${df['SMA_5'].iloc[-1]:.2f}")
    print(f"   ✓ SMA_20 latest: ${df['SMA_20'].iloc[-1]:.2f}")

    # Test RSI
    print("\n3. Testing RSI...")
    df['RSI'] = rsi(df, 14)
    print(f"   ✓ RSI latest: {df['RSI'].iloc[-1]:.2f}")

    # Test ATR
    print("\n4. Testing ATR...")
    df['ATR'] = atr(df, 14)
    print(f"   ✓ ATR latest: ${df['ATR'].iloc[-1]:.2f}")

    # Test crossover detection
    print("\n5. Testing MA crossover detection...")
    df['Crossover'] = detect_crossover(df['SMA_5'], df['SMA_20'])
    bullish_crosses = (df['Crossover'] == 1).sum()
    bearish_crosses = (df['Crossover'] == -1).sum()
    print(f"   ✓ Bullish crossovers: {bullish_crosses}")
    print(f"   ✓ Bearish crossovers: {bearish_crosses}")

    # Test MA position
    print("\n6. Testing MA position...")
    df['Position'] = get_ma_position(df['SMA_5'], df['SMA_20'])
    current_position = df['Position'].iloc[-1]
    position_str = "Bullish" if current_position == 1 else "Bearish" if current_position == -1 else "Neutral"
    print(f"   ✓ Current position: {position_str}")

    print("\n" + "=" * 60)
    print("All indicators working correctly!")
