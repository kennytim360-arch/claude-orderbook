"""Signal Strength Calculator - Institutional Grade Quantification"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class SignalStrengthCalculator:
    """
    Calculate quantitative strength of RORO signals (0-100 scale).

    Institutional approach: Signal strength determines position sizing.
    Weak signals (< 30) = small positions or skip
    Medium signals (30-70) = standard positions
    Strong signals (> 70) = larger positions with conviction
    """

    def __init__(self):
        """Initialize signal strength calculator."""
        pass

    def calculate_pillar_strength(
        self,
        fast_ma: float,
        slow_ma: float,
        pillar_signal: str
    ) -> float:
        """
        Calculate strength of individual pillar (0-100).

        Args:
            fast_ma: Fast moving average value
            slow_ma: Slow moving average value
            pillar_signal: Direction ('RISK-ON', 'RISK-OFF', 'NEUTRAL')

        Returns:
            Strength score (0-100)
        """
        if pillar_signal == 'NEUTRAL':
            return 0.0

        if slow_ma == 0:
            return 0.0

        # Calculate percentage separation between MAs
        separation = abs((fast_ma - slow_ma) / slow_ma) * 100

        # Cap at reasonable maximum (10% separation = max strength)
        strength = min(separation / 0.10 * 100, 100.0)

        return strength

    def calculate_momentum_strength(self, rsi: float) -> float:
        """
        Calculate RSI momentum strength (0-100).

        Args:
            rsi: RSI value (0-100)

        Returns:
            Momentum strength (0-100)
        """
        # RSI deviation from neutral (50)
        # RSI at 30 or 70 = moderate strength (40)
        # RSI at 20 or 80 = strong strength (60)
        # RSI at 10 or 90 = extreme strength (80)
        # RSI at 0 or 100 = maximum strength (100)

        deviation = abs(rsi - 50)
        strength = deviation * 2  # 0-50 deviation maps to 0-100 strength

        return min(strength, 100.0)

    def calculate_overall_strength(
        self,
        pillar1_strength: float,
        pillar2_strength: float,
        pillar3_strength: float,
        rsi_strength: float,
        consensus_count: int
    ) -> Dict[str, float]:
        """
        Calculate overall signal strength with breakdown.

        Args:
            pillar1_strength: TLT/SPY pillar strength
            pillar2_strength: GLD/SPY pillar strength
            pillar3_strength: HYG/TLT pillar strength
            rsi_strength: RSI momentum strength
            consensus_count: Number of pillars in agreement (2 or 3)

        Returns:
            Dictionary with overall and component strengths
        """
        # Average pillar strength
        pillar_avg = (pillar1_strength + pillar2_strength + pillar3_strength) / 3

        # Consensus bonus: 3/3 agreement is stronger than 2/3
        consensus_multiplier = 1.2 if consensus_count == 3 else 1.0

        # Combined strength: 70% pillars + 30% momentum
        combined = (pillar_avg * 0.7 + rsi_strength * 0.3) * consensus_multiplier

        # Cap at 100
        overall_strength = min(combined, 100.0)

        return {
            'overall': overall_strength,
            'pillar_avg': pillar_avg,
            'rsi': rsi_strength,
            'consensus_bonus': consensus_multiplier
        }

    def get_signal_quality(self, overall_strength: float) -> Tuple[str, str]:
        """
        Get qualitative assessment of signal strength.

        Args:
            overall_strength: Overall strength score (0-100)

        Returns:
            Tuple of (quality_level, description)
        """
        if overall_strength < 20:
            return ('VERY_WEAK', 'Skip or minimal position')
        elif overall_strength < 40:
            return ('WEAK', 'Small position (0.5% risk)')
        elif overall_strength < 60:
            return ('MEDIUM', 'Standard position (1.0% risk)')
        elif overall_strength < 80:
            return ('STRONG', 'Large position (1.5% risk)')
        else:
            return ('VERY_STRONG', 'Maximum position (2.0% risk)')

    def calculate_signal_strength_from_dataframe(
        self,
        signals_df: pd.DataFrame,
        index: int = -1
    ) -> Dict:
        """
        Calculate signal strength from signals DataFrame.

        Args:
            signals_df: DataFrame from SignalEngine.generate_signals()
            index: Row index (-1 for latest)

        Returns:
            Dictionary with strength breakdown
        """
        row = signals_df.iloc[index]

        # Calculate individual pillar strengths
        p1_strength = self.calculate_pillar_strength(
            row['tlt_spy_fast'],
            row['tlt_spy_slow'],
            row['pillar_tlt_spy']
        )

        p2_strength = self.calculate_pillar_strength(
            row['gld_spy_fast'],
            row['gld_spy_slow'],
            row['pillar_gld_spy']
        )

        p3_strength = self.calculate_pillar_strength(
            row['hyg_tlt_fast'],
            row['hyg_tlt_slow'],
            row['pillar_hyg_tlt']
        )

        # Calculate RSI strength
        rsi_strength = self.calculate_momentum_strength(row['spy_rsi'])

        # Calculate overall
        strengths = self.calculate_overall_strength(
            p1_strength,
            p2_strength,
            p3_strength,
            rsi_strength,
            row['consensus_count']
        )

        # Get quality assessment
        quality, description = self.get_signal_quality(strengths['overall'])

        return {
            'overall_strength': strengths['overall'],
            'pillar_tlt_spy': p1_strength,
            'pillar_gld_spy': p2_strength,
            'pillar_hyg_tlt': p3_strength,
            'rsi_strength': rsi_strength,
            'pillar_average': strengths['pillar_avg'],
            'consensus_count': row['consensus_count'],
            'consensus_bonus': strengths['consensus_bonus'],
            'quality': quality,
            'quality_description': description,
            'consensus': row['consensus']
        }
