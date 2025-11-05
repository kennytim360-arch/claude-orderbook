"""RORO Signal Engine - Core trading logic."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.signals.indicators import sma, rsi, get_ma_position
from src.utils.logger import logger, log_signal
from src.utils.config_loader import config


class SignalEngine:
    """
    RORO Signal Generation Engine.

    Implements the 3-pillar, 2-of-3 consensus strategy:
    - Pillar 1: TLT/SPY ratio (Bonds vs Equities)
    - Pillar 2: GLD/SPY ratio (Gold vs Equities)
    - Pillar 3: HYG/TLT ratio (Junk Bonds vs Safe Bonds)

    Signals:
    - RISK-ON: 2+ pillars show risk appetite
    - RISK-OFF: 2+ pillars show risk aversion
    - NEUTRAL: No consensus
    """

    def __init__(self):
        """Initialize signal engine with configuration."""
        self.fast_period, self.slow_period = config.get_ma_periods()
        self.rsi_period = config.get('signals.rsi_period', 14)
        self.consensus_required = config.get('signals.consensus_required', 2)

        logger.info(
            f"SignalEngine initialized: "
            f"MA({self.fast_period}/{self.slow_period}), "
            f"RSI({self.rsi_period}), "
            f"Consensus({self.consensus_required}/3)"
        )

    def calculate_ratio(
        self,
        numerator: pd.DataFrame,
        denominator: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate price ratio between two assets.

        Args:
            numerator: DataFrame for numerator asset
            denominator: DataFrame for denominator asset

        Returns:
            DataFrame with ratio and moving averages
        """
        # Calculate ratio
        ratio = numerator['Close'] / denominator['Close']

        # Normalize to 100 at start for easier interpretation
        ratio = (ratio / ratio.iloc[0]) * 100

        # Calculate moving averages
        fast_ma = sma(ratio, self.fast_period)
        slow_ma = sma(ratio, self.slow_period)

        # Combine into DataFrame
        df = pd.DataFrame({
            'ratio': ratio,
            'fast_ma': fast_ma,
            'slow_ma': slow_ma
        })

        return df

    def generate_pillar_signal(
        self,
        ratio_df: pd.DataFrame,
        pillar_name: str
    ) -> pd.Series:
        """
        Generate signal for individual pillar.

        Args:
            ratio_df: DataFrame with ratio, fast_ma, slow_ma
            pillar_name: Name of pillar (for logging)

        Returns:
            Series with:
            - 'RISK-OFF' if fast_ma > slow_ma (safe haven outperforming)
            - 'RISK-ON' if fast_ma < slow_ma (risky asset outperforming)
            - 'NEUTRAL' if no clear signal or insufficient data
        """
        signals = pd.Series('NEUTRAL', index=ratio_df.index)

        # Get MA position
        position = get_ma_position(ratio_df['fast_ma'], ratio_df['slow_ma'])

        # For safe haven ratios (TLT/SPY, GLD/SPY, HYG/TLT):
        # Rising ratio (fast > slow) = safe haven outperforming = RISK-OFF
        # Falling ratio (fast < slow) = risky asset outperforming = RISK-ON

        signals[position == 1] = 'RISK-OFF'   # Fast MA above slow MA
        signals[position == -1] = 'RISK-ON'   # Fast MA below slow MA

        return signals

    def calculate_consensus(
        self,
        pillar1_signal: str,
        pillar2_signal: str,
        pillar3_signal: str
    ) -> Tuple[str, int, str]:
        """
        Calculate 2-of-3 consensus.

        Args:
            pillar1_signal: TLT/SPY signal
            pillar2_signal: GLD/SPY signal
            pillar3_signal: HYG/TLT signal

        Returns:
            Tuple of (consensus_signal, count, description)
        """
        signals = [pillar1_signal, pillar2_signal, pillar3_signal]

        risk_off_count = signals.count('RISK-OFF')
        risk_on_count = signals.count('RISK-ON')

        if risk_off_count >= self.consensus_required:
            pillar_names = []
            if pillar1_signal == 'RISK-OFF':
                pillar_names.append('TLT/SPY')
            if pillar2_signal == 'RISK-OFF':
                pillar_names.append('GLD/SPY')
            if pillar3_signal == 'RISK-OFF':
                pillar_names.append('HYG/TLT')

            return ('RISK-OFF', risk_off_count, ', '.join(pillar_names))

        elif risk_on_count >= self.consensus_required:
            pillar_names = []
            if pillar1_signal == 'RISK-ON':
                pillar_names.append('TLT/SPY')
            if pillar2_signal == 'RISK-ON':
                pillar_names.append('GLD/SPY')
            if pillar3_signal == 'RISK-ON':
                pillar_names.append('HYG/TLT')

            return ('RISK-ON', risk_on_count, ', '.join(pillar_names))

        else:
            return ('NEUTRAL', 0, 'No consensus')

    def generate_signals(
        self,
        data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Generate trading signals from market data.

        Args:
            data: Dictionary mapping symbol to DataFrame
                  Must include: 'SPY', 'TLT', 'GLD', 'HYG'

        Returns:
            DataFrame with signals and ratios
        """
        # Validate required data
        required = ['SPY', 'TLT', 'GLD', 'HYG']
        missing = [sym for sym in required if sym not in data]
        if missing:
            raise ValueError(f"Missing required symbols: {missing}")

        logger.info("Generating RORO signals...")

        # Get asset data
        spy = data['SPY']
        tlt = data['TLT']
        gld = data['GLD']
        hyg = data['HYG']

        # Ensure same date range (use intersection)
        common_index = spy.index.intersection(tlt.index).intersection(gld.index).intersection(hyg.index)

        if len(common_index) == 0:
            raise ValueError("No common timestamps between assets")

        # Filter to common dates
        spy = spy.loc[common_index]
        tlt = tlt.loc[common_index]
        gld = gld.loc[common_index]
        hyg = hyg.loc[common_index]

        logger.info(f"  Common data points: {len(common_index)}")

        # Calculate ratios
        logger.info("  Calculating ratios...")
        ratio_tlt_spy = self.calculate_ratio(tlt, spy)
        ratio_gld_spy = self.calculate_ratio(gld, spy)
        ratio_hyg_tlt = self.calculate_ratio(hyg, tlt)

        # Generate pillar signals
        logger.info("  Generating pillar signals...")
        pillar1 = self.generate_pillar_signal(ratio_tlt_spy, 'TLT/SPY')
        pillar2 = self.generate_pillar_signal(ratio_gld_spy, 'GLD/SPY')
        pillar3 = self.generate_pillar_signal(ratio_hyg_tlt, 'HYG/TLT')

        # Calculate SPY momentum (RSI)
        logger.info("  Calculating SPY momentum...")
        spy_rsi = rsi(spy, self.rsi_period)

        # Calculate consensus for each timestamp
        logger.info("  Calculating consensus...")
        consensus_signals = []
        consensus_counts = []
        consensus_pillars = []

        for i in range(len(common_index)):
            signal, count, pillars = self.calculate_consensus(
                pillar1.iloc[i],
                pillar2.iloc[i],
                pillar3.iloc[i]
            )
            consensus_signals.append(signal)
            consensus_counts.append(count)
            consensus_pillars.append(pillars)

        # Create signals DataFrame
        signals_df = pd.DataFrame({
            # Ratios
            'ratio_tlt_spy': ratio_tlt_spy['ratio'],
            'ratio_gld_spy': ratio_gld_spy['ratio'],
            'ratio_hyg_tlt': ratio_hyg_tlt['ratio'],

            # Ratio MAs
            'tlt_spy_fast': ratio_tlt_spy['fast_ma'],
            'tlt_spy_slow': ratio_tlt_spy['slow_ma'],
            'gld_spy_fast': ratio_gld_spy['fast_ma'],
            'gld_spy_slow': ratio_gld_spy['slow_ma'],
            'hyg_tlt_fast': ratio_hyg_tlt['fast_ma'],
            'hyg_tlt_slow': ratio_hyg_tlt['slow_ma'],

            # Pillar signals
            'pillar_tlt_spy': pillar1,
            'pillar_gld_spy': pillar2,
            'pillar_hyg_tlt': pillar3,

            # Consensus
            'consensus': consensus_signals,
            'consensus_count': consensus_counts,
            'consensus_pillars': consensus_pillars,

            # SPY data
            'spy_price': spy['Close'],
            'spy_rsi': spy_rsi
        }, index=common_index)

        # Count signals
        risk_on_signals = (signals_df['consensus'] == 'RISK-ON').sum()
        risk_off_signals = (signals_df['consensus'] == 'RISK-OFF').sum()
        neutral_signals = (signals_df['consensus'] == 'NEUTRAL').sum()

        logger.info(f"  ✓ Signals generated:")
        logger.info(f"    RISK-ON:  {risk_on_signals}")
        logger.info(f"    RISK-OFF: {risk_off_signals}")
        logger.info(f"    NEUTRAL:  {neutral_signals}")

        return signals_df

    def get_latest_signal(self, signals_df: pd.DataFrame) -> Dict:
        """
        Get the most recent signal.

        Args:
            signals_df: DataFrame from generate_signals()

        Returns:
            Dictionary with latest signal info
        """
        if signals_df.empty:
            return None

        latest = signals_df.iloc[-1]

        signal_info = {
            'timestamp': signals_df.index[-1],
            'consensus': latest['consensus'],
            'consensus_count': latest['consensus_count'],
            'pillars': latest['consensus_pillars'],
            'spy_price': latest['spy_price'],
            'spy_rsi': latest['spy_rsi'],
            'pillar_tlt_spy': latest['pillar_tlt_spy'],
            'pillar_gld_spy': latest['pillar_gld_spy'],
            'pillar_hyg_tlt': latest['pillar_hyg_tlt']
        }

        return signal_info

    def check_momentum_filter(
        self,
        consensus: str,
        spy_rsi: float
    ) -> Tuple[bool, str]:
        """
        Check if SPY momentum confirms the signal.

        Args:
            consensus: RORO consensus signal
            spy_rsi: SPY RSI value

        Returns:
            Tuple of (passes_filter, reason)
        """
        rsi_threshold = config.get('signals.rsi_bullish_threshold', 50)

        if consensus == 'RISK-ON':
            # For Risk-On, want bullish momentum
            if spy_rsi > rsi_threshold:
                return (True, f"SPY RSI {spy_rsi:.1f} > {rsi_threshold} (bullish)")
            else:
                return (False, f"SPY RSI {spy_rsi:.1f} < {rsi_threshold} (not bullish enough)")

        elif consensus == 'RISK-OFF':
            # For Risk-Off, want bearish momentum
            if spy_rsi < rsi_threshold:
                return (True, f"SPY RSI {spy_rsi:.1f} < {rsi_threshold} (bearish)")
            else:
                return (False, f"SPY RSI {spy_rsi:.1f} > {rsi_threshold} (not bearish enough)")

        else:  # NEUTRAL
            return (False, "No consensus signal")


if __name__ == "__main__":
    # Test signal engine
    print("Testing RORO Signal Engine...")
    print("=" * 60)

    from src.data.data_collector import DataCollector

    # Load sample data
    print("\n1. Loading sample data...")
    collector = DataCollector()
    data = collector.download_all_assets(period='60d')

    if len(data) < 4:
        print("❌ Failed to load all required assets")
        sys.exit(1)

    print(f"   ✓ Loaded {len(data)} assets")

    # Generate signals
    print("\n2. Generating signals...")
    engine = SignalEngine()
    signals = engine.generate_signals(data)

    print(f"   ✓ Generated signals for {len(signals)} timestamps")

    # Get latest signal
    print("\n3. Latest signal:")
    latest = engine.get_latest_signal(signals)
    print(f"   Timestamp: {latest['timestamp']}")
    print(f"   Consensus: {latest['consensus']} ({latest['consensus_count']}/3)")
    print(f"   Pillars: {latest['pillars']}")
    print(f"   SPY Price: ${latest['spy_price']:.2f}")
    print(f"   SPY RSI: {latest['spy_rsi']:.1f}")

    # Check momentum filter
    print("\n4. Momentum filter check:")
    passes, reason = engine.check_momentum_filter(latest['consensus'], latest['spy_rsi'])
    print(f"   Passes: {'✓ YES' if passes else '❌ NO'}")
    print(f"   Reason: {reason}")

    # Show some statistics
    print("\n5. Signal statistics:")
    print(signals[['consensus', 'consensus_count']].value_counts().sort_index())

    # Show recent signals
    print("\n6. Last 10 signals:")
    print(signals[['consensus', 'spy_price', 'spy_rsi']].tail(10))

    print("\n" + "=" * 60)
    print("Signal Engine working correctly!")
