"""Test different strategy parameters to find profitable settings."""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine
from src.backtest.backtester import Backtester
from src.backtest.performance import PerformanceMetrics


def run_backtest_with_params(
    data,
    signals,
    initial_capital=1000,
    risk_pct=1.0,
    stop_loss_pct=0.5,
    take_profit_pct=1.0,
    long_only=False,
    description=""
):
    """Run backtest with specific parameters."""

    class ModifiedBacktester(Backtester):
        """Modified backtester with LONG-only option."""

        def __init__(self, *args, long_only=False, **kwargs):
            super().__init__(*args, **kwargs)
            self.long_only = long_only

        def run(self, signals_df, spy_data):
            """Override run to support LONG-only."""
            # Same as parent but skip SHORT trades if long_only
            common_index = signals_df.index.intersection(spy_data.index)
            signals_df = signals_df.loc[common_index]
            spy_data = spy_data.loc[common_index]

            self.current_capital = self.initial_capital
            self.trades = []
            self.current_trade = None
            self.equity_curve = []

            for timestamp in common_index:
                signal = signals_df.loc[timestamp]
                price_bar = spy_data.loc[timestamp]

                current_price = price_bar['Close']
                high = price_bar['High']
                low = price_bar['Low']

                # Check exits
                if self.current_trade is not None:
                    exit_info = self.check_exit(timestamp, current_price, high, low)
                    if exit_info:
                        exit_reason, exit_price = exit_info
                        self.close_trade(timestamp, exit_price, exit_reason)

                # Check entries
                consensus = signal['consensus']
                spy_rsi = signal['spy_rsi']

                if self.current_trade is None:
                    if consensus == 'RISK-ON' and spy_rsi > 50:
                        self.open_trade(timestamp, current_price, 'LONG', momentum_confirmed=True)

                    elif consensus == 'RISK-OFF' and spy_rsi < 50 and not self.long_only:
                        # Only SHORT if not long_only
                        self.open_trade(timestamp, current_price, 'SHORT', momentum_confirmed=True)

                # Check signal reversals
                elif self.current_trade is not None:
                    if self.current_trade.direction == 'LONG' and consensus == 'RISK-OFF':
                        self.close_trade(timestamp, current_price, 'SIGNAL_REVERSAL')
                    elif self.current_trade.direction == 'SHORT' and consensus == 'RISK-ON':
                        self.close_trade(timestamp, current_price, 'SIGNAL_REVERSAL')

                # Record equity
                current_equity = self.current_capital
                if self.current_trade is not None:
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

            # Close final trade
            if self.current_trade is not None:
                final_price = spy_data['Close'].iloc[-1]
                self.close_trade(common_index[-1], final_price, 'END_OF_DATA')

            import pandas as pd
            equity_df = pd.DataFrame(self.equity_curve)
            equity_df.set_index('timestamp', inplace=True)

            return equity_df

    backtester = ModifiedBacktester(
        initial_capital=initial_capital,
        risk_per_trade_pct=risk_pct,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        long_only=long_only
    )

    equity_curve = backtester.run(signals, data['SPY'])
    trades_df = backtester.get_trades_df()

    metrics = PerformanceMetrics.calculate_all_metrics(
        equity_curve,
        trades_df,
        initial_capital
    )

    return metrics, trades_df


if __name__ == "__main__":
    print("=" * 70)
    print("STRATEGY OPTIMIZATION - Testing Different Parameters")
    print("=" * 70)

    # Load data once
    print("\nLoading data...")
    collector = DataCollector()
    data = collector.download_all_assets(period='60d')

    engine = SignalEngine()
    signals = engine.generate_signals(data)
    print("✓ Data loaded\n")

    # Test configurations
    tests = [
        {
            'name': '1. BASELINE (Current Settings)',
            'params': {
                'risk_pct': 1.0,
                'stop_loss_pct': 0.5,
                'take_profit_pct': 1.0,
                'long_only': False
            }
        },
        {
            'name': '2. LONG ONLY (Skip SHORT trades)',
            'params': {
                'risk_pct': 1.0,
                'stop_loss_pct': 0.5,
                'take_profit_pct': 1.0,
                'long_only': True
            }
        },
        {
            'name': '3. WIDER STOPS (1% SL, 2% TP)',
            'params': {
                'risk_pct': 1.0,
                'stop_loss_pct': 1.0,
                'take_profit_pct': 2.0,
                'long_only': False
            }
        },
        {
            'name': '4. LONG ONLY + WIDER STOPS',
            'params': {
                'risk_pct': 1.0,
                'stop_loss_pct': 1.0,
                'take_profit_pct': 2.0,
                'long_only': True
            }
        },
        {
            'name': '5. CONSERVATIVE (0.5% risk)',
            'params': {
                'risk_pct': 0.5,
                'stop_loss_pct': 0.5,
                'take_profit_pct': 1.0,
                'long_only': True
            }
        },
    ]

    results = []

    for test in tests:
        print("=" * 70)
        print(test['name'])
        print("=" * 70)

        metrics, trades = run_backtest_with_params(
            data, signals, **test['params']
        )

        results.append({
            'name': test['name'],
            'return': metrics['total_return_pct'],
            'trades': metrics['total_trades'],
            'win_rate': metrics['win_rate'],
            'sharpe': metrics['sharpe_ratio'],
            'max_dd': metrics['max_drawdown_pct'],
            'profit_factor': metrics['profit_factor']
        })

        print(f"\n  Return: {metrics['total_return_pct']:+.2f}%")
        print(f"  Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  Sharpe: {metrics['sharpe_ratio']:.2f}")
        print(f"  Max DD: {metrics['max_drawdown_pct']:.2f}%")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        print()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY - BEST TO WORST")
    print("=" * 70)

    # Sort by return
    results_sorted = sorted(results, key=lambda x: x['return'], reverse=True)

    print(f"\n{'Test':<40} {'Return':<10} {'Sharpe':<8} {'Trades':<8} {'Win%'}")
    print("-" * 70)

    for r in results_sorted:
        print(f"{r['name']:<40} {r['return']:>+7.2f}%  {r['sharpe']:>6.2f}  {r['trades']:>6}  {r['win_rate']:>5.1f}%")

    print("\n" + "=" * 70)

    best = results_sorted[0]
    print(f"\n✅ BEST CONFIGURATION: {best['name']}")
    print(f"   Return: {best['return']:+.2f}%")
    print(f"   Sharpe: {best['sharpe']:.2f}")
    print(f"   Win Rate: {best['win_rate']:.1f}%")
    print("\n" + "=" * 70)
