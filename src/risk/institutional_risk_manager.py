"""Institutional Risk Manager - Dynamic Position Sizing & Leverage Control"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional


class InstitutionalRiskManager:
    """
    Institutional-grade risk management with dynamic position sizing.

    Key Features:
    - Signal-strength based position sizing
    - Leverage control (max 10x for CFDs)
    - ATR-based stops
    - Risk-adjusted take profits
    - Portfolio heat management
    """

    def __init__(
        self,
        account_size: float = 10000,
        max_leverage: float = 10.0,
        max_portfolio_risk: float = 3.0,  # Max 3% total portfolio risk
        base_risk_percent: float = 1.0
    ):
        """
        Initialize institutional risk manager.

        Args:
            account_size: Account size in dollars
            max_leverage: Maximum leverage allowed (10x institutional standard)
            max_portfolio_risk: Maximum total portfolio risk percentage
            base_risk_percent: Base risk per trade (1% standard)
        """
        self.account_size = account_size
        self.max_leverage = max_leverage
        self.max_portfolio_risk = max_portfolio_risk
        self.base_risk_percent = base_risk_percent

    def calculate_risk_percent_from_strength(
        self,
        signal_strength: float
    ) -> float:
        """
        Calculate risk percentage based on signal strength.

        Institutional Approach:
        - Weak signals (< 30): 0.5% risk
        - Medium signals (30-60): 1.0% risk
        - Strong signals (60-80): 1.5% risk
        - Very strong signals (> 80): 2.0% risk

        Args:
            signal_strength: Signal strength (0-100)

        Returns:
            Risk percentage for this trade
        """
        if signal_strength < 30:
            return 0.5
        elif signal_strength < 60:
            return 1.0
        elif signal_strength < 80:
            return 1.5
        else:
            return 2.0

    def calculate_atr_stop_loss(
        self,
        entry_price: float,
        atr: float,
        direction: str = 'LONG',
        atr_multiplier: float = 2.0
    ) -> float:
        """
        Calculate ATR-based stop loss (institutional standard).

        Args:
            entry_price: Entry price
            atr: Average True Range
            direction: 'LONG' or 'SHORT'
            atr_multiplier: ATR multiplier (2.0 = 2x ATR)

        Returns:
            Stop loss price
        """
        stop_distance = atr * atr_multiplier

        if direction == 'LONG':
            stop_loss = entry_price - stop_distance
        else:  # SHORT
            stop_loss = entry_price + stop_distance

        return stop_loss

    def calculate_dynamic_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str = 'LONG',
        risk_reward_ratio: float = 2.0
    ) -> float:
        """
        Calculate take profit based on risk/reward ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            direction: 'LONG' or 'SHORT'
            risk_reward_ratio: Target R:R ratio (2.0 = 2:1)

        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio

        if direction == 'LONG':
            take_profit = entry_price + reward
        else:  # SHORT
            take_profit = entry_price - reward

        return take_profit

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        signal_strength: float,
        leverage: float = 1.0
    ) -> Dict:
        """
        Calculate institutional-grade position size.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            signal_strength: Signal strength (0-100)
            leverage: Leverage to use (1.0-10.0)

        Returns:
            Dictionary with position details
        """
        # Validate leverage
        if leverage > self.max_leverage:
            leverage = self.max_leverage

        # Get risk percent based on signal strength
        risk_percent = self.calculate_risk_percent_from_strength(signal_strength)

        # Calculate risk amount in dollars
        risk_amount = self.account_size * (risk_percent / 100)

        # Calculate risk per share/contract
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share == 0:
            return None

        # Calculate base shares (no leverage)
        base_shares = int(risk_amount / risk_per_share)

        # Apply leverage
        leveraged_shares = int(base_shares * leverage)

        # Calculate notional exposure
        notional_exposure = leveraged_shares * entry_price

        # Calculate margin requirement (inverse of leverage)
        margin_required = notional_exposure / leverage

        # Validate margin requirement doesn't exceed account
        if margin_required > self.account_size:
            # Reduce position to fit account
            leveraged_shares = int((self.account_size / entry_price) * leverage)
            notional_exposure = leveraged_shares * entry_price
            margin_required = notional_exposure / leverage

        return {
            'shares': leveraged_shares,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'risk_amount': risk_amount,
            'risk_percent': risk_percent,
            'leverage': leverage,
            'notional_exposure': notional_exposure,
            'margin_required': margin_required,
            'risk_per_share': risk_per_share,
            'signal_strength': signal_strength
        }

    def calculate_institutional_position(
        self,
        entry_price: float,
        atr: float,
        signal_strength: float,
        direction: str = 'LONG',
        leverage: float = 1.0,
        atr_multiplier: float = 2.0,
        risk_reward_ratio: float = 2.0
    ) -> Dict:
        """
        Complete institutional position calculation.

        Args:
            entry_price: Entry price
            atr: Average True Range
            signal_strength: Signal strength (0-100)
            direction: 'LONG' or 'SHORT'
            leverage: Leverage to use
            atr_multiplier: ATR stop multiplier
            risk_reward_ratio: R:R target

        Returns:
            Complete position specification
        """
        # Calculate ATR-based stop
        stop_loss = self.calculate_atr_stop_loss(
            entry_price, atr, direction, atr_multiplier
        )

        # Calculate take profit
        take_profit = self.calculate_dynamic_take_profit(
            entry_price, stop_loss, direction, risk_reward_ratio
        )

        # Calculate position size
        position = self.calculate_position_size(
            entry_price, stop_loss, signal_strength, leverage
        )

        if position is None:
            return None

        # Add TP to position
        position['take_profit'] = take_profit
        position['direction'] = direction
        position['atr'] = atr
        position['atr_multiplier'] = atr_multiplier
        position['risk_reward_ratio'] = risk_reward_ratio

        return position

    def estimate_atr_from_price(
        self,
        current_price: float,
        percent: float = 1.0
    ) -> float:
        """
        Estimate ATR when actual ATR is unavailable.

        Quick approximation: ATR ≈ 1% of price for most liquid assets.

        Args:
            current_price: Current asset price
            percent: Percentage to use (default 1%)

        Returns:
            Estimated ATR
        """
        return current_price * (percent / 100)


class CFDPositionManager:
    """
    Specialized manager for CFD trading with leverage.

    CFD (Contract For Difference) allows leverage trading.
    Institutional standard: Max 10x leverage with strict controls.
    """

    def __init__(self, max_leverage: float = 10.0):
        """
        Initialize CFD position manager.

        Args:
            max_leverage: Maximum leverage (10x institutional standard)
        """
        self.max_leverage = max_leverage

    def calculate_cfd_position(
        self,
        entry_price: float,
        account_size: float,
        risk_percent: float,
        leverage: float,
        stop_loss: float
    ) -> Dict:
        """
        Calculate CFD position with leverage.

        Args:
            entry_price: Entry price
            account_size: Account size
            risk_percent: Risk percentage
            leverage: Desired leverage
            stop_loss: Stop loss price

        Returns:
            CFD position specification
        """
        # Enforce leverage limit
        if leverage > self.max_leverage:
            leverage = self.max_leverage

        # Calculate risk amount
        risk_amount = account_size * (risk_percent / 100)

        # Calculate risk per contract
        risk_per_contract = abs(entry_price - stop_loss)

        if risk_per_contract == 0:
            return None

        # Calculate contracts
        contracts = int(risk_amount / risk_per_contract)

        # Apply leverage
        leveraged_contracts = int(contracts * leverage)

        # Calculate exposure and margin
        notional_exposure = leveraged_contracts * entry_price
        margin_required = notional_exposure / leverage

        return {
            'contracts': leveraged_contracts,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'leverage': leverage,
            'notional_exposure': notional_exposure,
            'margin_required': margin_required,
            'risk_amount': risk_amount,
            'risk_percent': risk_percent
        }
