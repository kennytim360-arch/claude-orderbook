"""Performance metrics calculation for backtesting."""

import pandas as pd
import numpy as np
from typing import Dict, Optional


class PerformanceMetrics:
    """Calculate trading performance metrics."""

    @staticmethod
    def calculate_all_metrics(
        equity_curve: pd.DataFrame,
        trades_df: pd.DataFrame,
        initial_capital: float,
        risk_free_rate: float = 0.0
    ) -> Dict:
        """
        Calculate comprehensive performance metrics.

        Args:
            equity_curve: DataFrame with equity over time
            trades_df: DataFrame with trade history
            initial_capital: Starting capital
            risk_free_rate: Risk-free rate for Sharpe (annual)

        Returns:
            Dictionary with all metrics
        """
        metrics = {}

        # Basic Returns
        final_equity = equity_curve['equity'].iloc[-1]
        total_return = ((final_equity / initial_capital) - 1) * 100
        metrics['initial_capital'] = initial_capital
        metrics['final_equity'] = final_equity
        metrics['total_return_pct'] = total_return
        metrics['total_pnl'] = final_equity - initial_capital

        # Trade Statistics
        if not trades_df.empty:
            metrics['total_trades'] = len(trades_df)
            metrics['winning_trades'] = len(trades_df[trades_df['pnl'] > 0])
            metrics['losing_trades'] = len(trades_df[trades_df['pnl'] <= 0])
            metrics['win_rate'] = (metrics['winning_trades'] / metrics['total_trades']) * 100

            # P&L Statistics
            wins = trades_df[trades_df['pnl'] > 0]
            losses = trades_df[trades_df['pnl'] <= 0]

            metrics['avg_win'] = wins['pnl'].mean() if len(wins) > 0 else 0
            metrics['avg_loss'] = losses['pnl'].mean() if len(losses) > 0 else 0
            metrics['avg_win_pct'] = wins['pnl_pct'].mean() if len(wins) > 0 else 0
            metrics['avg_loss_pct'] = losses['pnl_pct'].mean() if len(losses) > 0 else 0

            metrics['largest_win'] = trades_df['pnl'].max()
            metrics['largest_loss'] = trades_df['pnl'].min()

            # Profit Factor
            gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
            gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 0
            metrics['gross_profit'] = gross_profit
            metrics['gross_loss'] = gross_loss
            metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')

            # Average trade
            metrics['avg_trade_pnl'] = trades_df['pnl'].mean()
            metrics['avg_trade_pnl_pct'] = trades_df['pnl_pct'].mean()

            # Expectancy
            if metrics['win_rate'] > 0:
                expectancy = (
                    (metrics['win_rate'] / 100) * metrics['avg_win'] +
                    ((100 - metrics['win_rate']) / 100) * metrics['avg_loss']
                )
                metrics['expectancy'] = expectancy
            else:
                metrics['expectancy'] = 0

        else:
            # No trades
            metrics['total_trades'] = 0
            metrics['winning_trades'] = 0
            metrics['losing_trades'] = 0
            metrics['win_rate'] = 0
            metrics['profit_factor'] = 0
            metrics['expectancy'] = 0

        # Drawdown Analysis
        equity_series = equity_curve['equity']
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100

        metrics['max_drawdown_pct'] = drawdown.min()
        metrics['avg_drawdown_pct'] = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0

        # Find max drawdown period
        max_dd_idx = drawdown.idxmin()
        max_dd_value = drawdown.min()
        metrics['max_dd_date'] = max_dd_idx

        # Sharpe Ratio (annualized)
        returns = equity_series.pct_change().dropna()
        if len(returns) > 0:
            # Assuming 5-min bars, ~78 bars per day, ~252 trading days
            bars_per_year = 78 * 252
            excess_returns = returns - (risk_free_rate / bars_per_year)
            sharpe_ratio = excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0
            metrics['sharpe_ratio'] = sharpe_ratio * np.sqrt(bars_per_year)
        else:
            metrics['sharpe_ratio'] = 0

        # Sortino Ratio (only downside deviation)
        if len(returns) > 0:
            downside_returns = returns[returns < 0]
            downside_std = downside_returns.std() if len(downside_returns) > 0 else returns.std()
            sortino_ratio = returns.mean() / downside_std if downside_std > 0 else 0
            metrics['sortino_ratio'] = sortino_ratio * np.sqrt(bars_per_year)
        else:
            metrics['sortino_ratio'] = 0

        # Calmar Ratio (return / max drawdown)
        if metrics['max_drawdown_pct'] != 0:
            metrics['calmar_ratio'] = abs(total_return / metrics['max_drawdown_pct'])
        else:
            metrics['calmar_ratio'] = 0

        # Trade Duration
        if not trades_df.empty and 'entry_time' in trades_df.columns and 'exit_time' in trades_df.columns:
            trades_df['duration'] = pd.to_datetime(trades_df['exit_time']) - pd.to_datetime(trades_df['entry_time'])
            avg_duration = trades_df['duration'].mean()
            metrics['avg_trade_duration_minutes'] = avg_duration.total_seconds() / 60 if pd.notna(avg_duration) else 0
        else:
            metrics['avg_trade_duration_minutes'] = 0

        return metrics

    @staticmethod
    def print_metrics(metrics: Dict):
        """Print metrics in readable format."""
        print("\n" + "=" * 60)
        print("PERFORMANCE METRICS")
        print("=" * 60)

        print("\n📊 RETURNS")
        print(f"  Initial Capital:     ${metrics['initial_capital']:,.2f}")
        print(f"  Final Equity:        ${metrics['final_equity']:,.2f}")
        print(f"  Total P&L:           ${metrics['total_pnl']:+,.2f}")
        print(f"  Total Return:        {metrics['total_return_pct']:+.2f}%")

        print("\n📈 TRADE STATISTICS")
        print(f"  Total Trades:        {metrics['total_trades']}")
        print(f"  Winning Trades:      {metrics['winning_trades']}")
        print(f"  Losing Trades:       {metrics['losing_trades']}")
        print(f"  Win Rate:            {metrics['win_rate']:.1f}%")

        if metrics['total_trades'] > 0:
            print("\n💰 P&L ANALYSIS")
            print(f"  Gross Profit:        ${metrics['gross_profit']:,.2f}")
            print(f"  Gross Loss:          ${metrics['gross_loss']:,.2f}")
            print(f"  Profit Factor:       {metrics['profit_factor']:.2f}")
            print(f"  Expectancy:          ${metrics['expectancy']:.2f} per trade")

            print("\n🎯 TRADE AVERAGES")
            print(f"  Avg Win:             ${metrics['avg_win']:.2f} ({metrics['avg_win_pct']:+.2f}%)")
            print(f"  Avg Loss:            ${metrics['avg_loss']:.2f} ({metrics['avg_loss_pct']:+.2f}%)")
            print(f"  Avg Trade:           ${metrics['avg_trade_pnl']:.2f} ({metrics['avg_trade_pnl_pct']:+.2f}%)")
            print(f"  Largest Win:         ${metrics['largest_win']:.2f}")
            print(f"  Largest Loss:        ${metrics['largest_loss']:.2f}")

        print("\n📉 RISK METRICS")
        print(f"  Max Drawdown:        {metrics['max_drawdown_pct']:.2f}%")
        print(f"  Avg Drawdown:        {metrics['avg_drawdown_pct']:.2f}%")
        print(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio:       {metrics['sortino_ratio']:.2f}")
        print(f"  Calmar Ratio:        {metrics['calmar_ratio']:.2f}")

        if metrics['total_trades'] > 0:
            print("\n⏱️  TRADE DURATION")
            print(f"  Avg Trade Duration:  {metrics['avg_trade_duration_minutes']:.0f} minutes")

        print("\n" + "=" * 60)

    @staticmethod
    def analyze_trades_by_exit_reason(trades_df: pd.DataFrame):
        """Analyze trades grouped by exit reason."""
        if trades_df.empty:
            return

        print("\n" + "=" * 60)
        print("TRADES BY EXIT REASON")
        print("=" * 60)

        exit_reasons = trades_df.groupby('exit_reason').agg({
            'pnl': ['count', 'sum', 'mean'],
            'pnl_pct': 'mean'
        }).round(2)

        print(exit_reasons)

        print("\n" + "=" * 60)

    @staticmethod
    def analyze_trades_by_direction(trades_df: pd.DataFrame):
        """Analyze trades by direction (LONG vs SHORT)."""
        if trades_df.empty:
            return

        print("\n" + "=" * 60)
        print("TRADES BY DIRECTION")
        print("=" * 60)

        for direction in ['LONG', 'SHORT']:
            subset = trades_df[trades_df['direction'] == direction]
            if len(subset) > 0:
                wins = len(subset[subset['pnl'] > 0])
                total = len(subset)
                win_rate = (wins / total) * 100 if total > 0 else 0
                avg_pnl = subset['pnl'].mean()

                print(f"\n{direction}:")
                print(f"  Trades: {total}")
                print(f"  Wins: {wins}")
                print(f"  Win Rate: {win_rate:.1f}%")
                print(f"  Avg P&L: ${avg_pnl:+.2f}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    # Test performance metrics
    print("Testing Performance Metrics...")

    from src.data.data_collector import DataCollector
    from src.signals.signal_engine import SignalEngine
    from src.backtest.backtester import Backtester

    # Load data
    collector = DataCollector()
    data = collector.download_all_assets(period='60d')

    # Generate signals
    engine = SignalEngine()
    signals = engine.generate_signals(data)

    # Run backtest
    backtester = Backtester(
        initial_capital=1000,
        risk_per_trade_pct=1.0,
        stop_loss_pct=0.5,
        take_profit_pct=1.0
    )
    equity_curve = backtester.run(signals, data['SPY'])
    trades_df = backtester.get_trades_df()

    # Calculate metrics
    metrics = PerformanceMetrics.calculate_all_metrics(
        equity_curve,
        trades_df,
        backtester.initial_capital
    )

    # Print metrics
    PerformanceMetrics.print_metrics(metrics)

    # Additional analysis
    PerformanceMetrics.analyze_trades_by_exit_reason(trades_df)
    PerformanceMetrics.analyze_trades_by_direction(trades_df)
