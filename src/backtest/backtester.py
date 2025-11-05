"""Backtesting engine for RORO Trading System."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import logger
from src.utils.config_loader import config


class Trade:
    """Represents a single trade."""

    def __init__(
        self,
        entry_time: datetime,
        entry_price: float,
        direction: str,
        quantity: float,
        stop_loss: float,
        take_profit: float
    ):
        """
        Initialize trade.

        Args:
            entry_time: Trade entry timestamp
            entry_price: Entry price
            direction: 'LONG' or 'SHORT'
            quantity: Number of shares/contracts
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.direction = direction
        self.quantity = quantity
        self.stop_loss = stop_loss
        self.take_profit = take_profit

        self.exit_time = None
        self.exit_price = None
        self.exit_reason = None
        self.pnl = 0.0
        self.pnl_pct = 0.0
        self.status = 'OPEN'

    def close(self, exit_time: datetime, exit_price: float, reason: str):
        """
        Close the trade.

        Args:
            exit_time: Exit timestamp
            exit_price: Exit price
            reason: Exit reason (TP, SL, SIGNAL, EOD)
        """
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = reason
        self.status = 'CLOSED'

        # Calculate P&L
        if self.direction == 'LONG':
            self.pnl = (exit_price - self.entry_price) * self.quantity
            self.pnl_pct = ((exit_price / self.entry_price) - 1) * 100
        else:  # SHORT
            self.pnl = (self.entry_price - exit_price) * self.quantity
            self.pnl_pct = ((self.entry_price / exit_price) - 1) * 100

    def to_dict(self) -> Dict:
        """Convert trade to dictionary."""
        return {
            'entry_time': self.entry_time,
            'entry_price': self.entry_price,
            'direction': self.direction,
            'quantity': self.quantity,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'exit_time': self.exit_time,
            'exit_price': self.exit_price,
            'exit_reason': self.exit_reason,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'status': self.status
        }


class Backtester:
    """
    Backtesting engine for RORO strategy.

    Simulates trading with:
    - Signal-based entries
    - Stop loss and take profit exits
    - Realistic friction (spread, slippage)
    - Position sizing based on risk
    """

    def __init__(
        self,
        initial_capital: float = 1000,
        risk_per_trade_pct: float = 1.0,
        stop_loss_pct: float = 0.5,
        take_profit_pct: float = 1.0,
        spread_pct: float = 0.002,
        slippage_pct: float = 0.01
    ):
        """
        Initialize backtester.

        Args:
            initial_capital: Starting account balance
            risk_per_trade_pct: % of account to risk per trade
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            spread_pct: Bid-ask spread percentage
            slippage_pct: Slippage percentage
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade_pct = risk_per_trade_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.spread_pct = spread_pct
        self.slippage_pct = slippage_pct

        self.trades: List[Trade] = []
        self.current_trade: Optional[Trade] = None
        self.equity_curve = []

        logger.info(
            f"Backtester initialized: "
            f"Capital=${initial_capital:.2f}, "
            f"Risk={risk_per_trade_pct}%, "
            f"SL={stop_loss_pct}%, TP={take_profit_pct}%"
        )

    def calculate_position_size(self, entry_price: float) -> float:
        """
        Calculate position size based on risk management.

        Args:
            entry_price: Entry price

        Returns:
            Number of shares to trade
        """
        # Risk amount in dollars
        risk_amount = self.current_capital * (self.risk_per_trade_pct / 100)

        # Stop loss distance in dollars
        stop_loss_distance = entry_price * (self.stop_loss_pct / 100)

        # Position size = risk / stop distance
        position_size = risk_amount / stop_loss_distance

        return position_size

    def apply_spread(self, price: float, direction: str) -> float:
        """
        Apply bid-ask spread to price.

        Args:
            price: Market price
            direction: 'BUY' or 'SELL'

        Returns:
            Adjusted price
        """
        if direction == 'BUY':
            # Buy at ask (higher)
            return price * (1 + self.spread_pct / 100)
        else:  # SELL
            # Sell at bid (lower)
            return price * (1 - self.spread_pct / 100)

    def apply_slippage(self, price: float, direction: str) -> float:
        """
        Apply slippage to price.

        Args:
            price: Market price
            direction: 'BUY' or 'SELL'

        Returns:
            Adjusted price
        """
        if direction == 'BUY':
            # Slippage makes buys more expensive
            return price * (1 + self.slippage_pct / 100)
        else:  # SELL
            # Slippage makes sells cheaper
            return price * (1 - self.slippage_pct / 100)

    def get_execution_price(self, market_price: float, direction: str) -> float:
        """
        Get realistic execution price with spread and slippage.

        Args:
            market_price: Market price
            direction: 'BUY' or 'SELL'

        Returns:
            Execution price
        """
        # Apply spread
        price = self.apply_spread(market_price, direction)

        # Apply slippage
        price = self.apply_slippage(price, direction)

        return price

    def open_trade(
        self,
        timestamp: datetime,
        market_price: float,
        direction: str,
        momentum_confirmed: bool = True
    ):
        """
        Open a new trade.

        Args:
            timestamp: Trade timestamp
            market_price: Current market price
            direction: 'LONG' or 'SHORT'
            momentum_confirmed: Whether momentum filter passed
        """
        # Skip if momentum not confirmed
        if not momentum_confirmed:
            return

        # Skip if already in a trade
        if self.current_trade is not None:
            return

        # Get execution price
        entry_price = self.get_execution_price(
            market_price,
            'BUY' if direction == 'LONG' else 'SELL'
        )

        # Calculate position size
        quantity = self.calculate_position_size(entry_price)

        # Calculate stop loss and take profit
        if direction == 'LONG':
            stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
            take_profit = entry_price * (1 + self.take_profit_pct / 100)
        else:  # SHORT
            stop_loss = entry_price * (1 + self.stop_loss_pct / 100)
            take_profit = entry_price * (1 - self.take_profit_pct / 100)

        # Create trade
        trade = Trade(
            entry_time=timestamp,
            entry_price=entry_price,
            direction=direction,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.current_trade = trade

        logger.debug(
            f"OPEN {direction}: {quantity:.2f} @ ${entry_price:.2f} "
            f"| SL: ${stop_loss:.2f} | TP: ${take_profit:.2f}"
        )

    def check_exit(
        self,
        timestamp: datetime,
        current_price: float,
        high: float,
        low: float
    ) -> Optional[Tuple[str, float]]:
        """
        Check if trade should be exited.

        Args:
            timestamp: Current timestamp
            current_price: Current close price
            high: Bar high
            low: Bar low

        Returns:
            Tuple of (exit_reason, exit_price) or None
        """
        if self.current_trade is None:
            return None

        trade = self.current_trade

        if trade.direction == 'LONG':
            # Check stop loss (use low of bar)
            if low <= trade.stop_loss:
                return ('STOP_LOSS', trade.stop_loss)

            # Check take profit (use high of bar)
            if high >= trade.take_profit:
                return ('TAKE_PROFIT', trade.take_profit)

        else:  # SHORT
            # Check stop loss (use high of bar)
            if high >= trade.stop_loss:
                return ('STOP_LOSS', trade.stop_loss)

            # Check take profit (use low of bar)
            if low <= trade.take_profit:
                return ('TAKE_PROFIT', trade.take_profit)

        return None

    def close_trade(
        self,
        timestamp: datetime,
        exit_price: float,
        reason: str
    ):
        """
        Close current trade.

        Args:
            timestamp: Exit timestamp
            exit_price: Exit price
            reason: Exit reason
        """
        if self.current_trade is None:
            return

        # Apply execution costs to exit
        adjusted_exit_price = self.get_execution_price(
            exit_price,
            'SELL' if self.current_trade.direction == 'LONG' else 'BUY'
        )

        # Close trade
        self.current_trade.close(timestamp, adjusted_exit_price, reason)

        # Update capital
        self.current_capital += self.current_trade.pnl

        # Store trade
        self.trades.append(self.current_trade)

        logger.debug(
            f"CLOSE: {reason} @ ${adjusted_exit_price:.2f} "
            f"| P&L: ${self.current_trade.pnl:.2f} ({self.current_trade.pnl_pct:+.2f}%)"
        )

        self.current_trade = None

    def run(
        self,
        signals_df: pd.DataFrame,
        spy_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Run backtest on historical data.

        Args:
            signals_df: DataFrame with signals (from SignalEngine)
            spy_data: SPY price data (for trade execution)

        Returns:
            DataFrame with equity curve
        """
        logger.info("Starting backtest...")
        logger.info(f"  Data points: {len(signals_df)}")

        # Ensure same index
        common_index = signals_df.index.intersection(spy_data.index)
        signals_df = signals_df.loc[common_index]
        spy_data = spy_data.loc[common_index]

        # Initialize
        self.current_capital = self.initial_capital
        self.trades = []
        self.current_trade = None
        self.equity_curve = []

        previous_consensus = 'NEUTRAL'

        for timestamp in common_index:
            signal = signals_df.loc[timestamp]
            price_bar = spy_data.loc[timestamp]

            current_price = price_bar['Close']
            high = price_bar['High']
            low = price_bar['Low']

            # Check if current trade should be exited
            if self.current_trade is not None:
                exit_info = self.check_exit(timestamp, current_price, high, low)

                if exit_info:
                    exit_reason, exit_price = exit_info
                    self.close_trade(timestamp, exit_price, exit_reason)

            # Check for new signal
            consensus = signal['consensus']
            spy_rsi = signal['spy_rsi']

            # Entry conditions
            if self.current_trade is None:
                if consensus == 'RISK-ON' and spy_rsi > 50:
                    self.open_trade(timestamp, current_price, 'LONG', momentum_confirmed=True)

                elif consensus == 'RISK-OFF' and spy_rsi < 50:
                    self.open_trade(timestamp, current_price, 'SHORT', momentum_confirmed=True)

            # Exit on signal reversal
            elif self.current_trade is not None:
                # If LONG and signal flips to RISK-OFF
                if self.current_trade.direction == 'LONG' and consensus == 'RISK-OFF':
                    self.close_trade(timestamp, current_price, 'SIGNAL_REVERSAL')

                # If SHORT and signal flips to RISK-ON
                elif self.current_trade.direction == 'SHORT' and consensus == 'RISK-ON':
                    self.close_trade(timestamp, current_price, 'SIGNAL_REVERSAL')

            # Record equity
            current_equity = self.current_capital
            if self.current_trade is not None:
                # Calculate unrealized P&L
                if self.current_trade.direction == 'LONG':
                    unrealized_pnl = (current_price - self.current_trade.entry_price) * self.current_trade.quantity
                else:
                    unrealized_pnl = (self.current_trade.entry_price - current_price) * self.current_trade.quantity

                current_equity += unrealized_pnl

            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': current_equity,
                'cash': self.current_capital,
                'in_trade': self.current_trade is not None
            })

            previous_consensus = consensus

        # Close any remaining open trade at end
        if self.current_trade is not None:
            final_price = spy_data['Close'].iloc[-1]
            self.close_trade(common_index[-1], final_price, 'END_OF_DATA')

        # Convert to DataFrame
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)

        logger.info(f"✓ Backtest complete: {len(self.trades)} trades executed")

        return equity_df

    def get_trades_df(self) -> pd.DataFrame:
        """Get trades as DataFrame."""
        if not self.trades:
            return pd.DataFrame()

        trades_data = [trade.to_dict() for trade in self.trades]
        return pd.DataFrame(trades_data)


if __name__ == "__main__":
    # Test backtester
    print("Testing Backtester...")
    print("=" * 60)

    from src.data.data_collector import DataCollector
    from src.signals.signal_engine import SignalEngine

    # Load data
    print("\n1. Loading data...")
    collector = DataCollector()
    data = collector.download_all_assets(period='60d')
    print(f"   ✓ Loaded {len(data)} assets")

    # Generate signals
    print("\n2. Generating signals...")
    engine = SignalEngine()
    signals = engine.generate_signals(data)
    print(f"   ✓ Generated {len(signals)} signals")

    # Run backtest
    print("\n3. Running backtest...")
    backtester = Backtester(
        initial_capital=1000,
        risk_per_trade_pct=1.0,
        stop_loss_pct=0.5,
        take_profit_pct=1.0,
        spread_pct=0.002,
        slippage_pct=0.01
    )

    equity_curve = backtester.run(signals, data['SPY'])

    # Show results
    print(f"\n4. Results:")
    print(f"   Initial Capital: ${backtester.initial_capital:.2f}")
    print(f"   Final Capital: ${backtester.current_capital:.2f}")
    print(f"   Total Return: {((backtester.current_capital / backtester.initial_capital) - 1) * 100:.2f}%")
    print(f"   Total Trades: {len(backtester.trades)}")

    if backtester.trades:
        trades_df = backtester.get_trades_df()
        wins = len(trades_df[trades_df['pnl'] > 0])
        losses = len(trades_df[trades_df['pnl'] <= 0])
        win_rate = (wins / len(trades_df)) * 100

        print(f"   Wins: {wins}")
        print(f"   Losses: {losses}")
        print(f"   Win Rate: {win_rate:.1f}%")

        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] <= 0]['pnl'].mean() if losses > 0 else 0

        print(f"   Avg Win: ${avg_win:.2f}")
        print(f"   Avg Loss: ${avg_loss:.2f}")

    print("\n" + "=" * 60)
