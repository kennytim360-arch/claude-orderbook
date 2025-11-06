#!/usr/bin/env python3
"""
Test safe haven trading strategies.

Compares:
1. SPY LONG-ONLY (sit flat on RISK-OFF)
2. SPY + TLT (LONG TLT on RISK-OFF)
3. SPY + GLD (LONG GLD on RISK-OFF)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime

from src.data.data_storage import TradingDatabase
from src.signals.signal_engine import SignalEngine
from src.backtest.backtester import Backtester
from src.backtest.performance import PerformanceMetrics
from src.utils.logger import logger
from src.utils.config_loader import config


def load_data():
    """Load historical data for all assets."""
    db = TradingDatabase()

    assets = ['SPY', 'TLT', 'GLD', 'HYG']
    asset_data = {}

    logger.info("Loading historical data...")

    for asset in assets:
        df = db.get_market_data(asset)

        if df is None or df.empty:
            logger.warning(f"No data for {asset} - trying CSV fallback")
            csv_path = project_root / f'data/historical/{asset}_5min.csv'
            if csv_path.exists():
                df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                logger.info(f"✓ Loaded {asset} from CSV: {len(df)} bars")
            else:
                raise ValueError(f"No data available for {asset}")
        else:
            logger.info(f"✓ Loaded {asset} from database: {len(df)} bars")

        asset_data[asset] = df

    return asset_data


def generate_signals(asset_data):
    """Generate RORO signals."""
    logger.info("Generating signals...")

    engine = SignalEngine()

    signals_df = engine.generate_signals(asset_data)

    logger.info(f"✓ Generated {len(signals_df)} signals")

    # Signal distribution
    signal_counts = signals_df['consensus'].value_counts()
    logger.info(f"  Signal distribution:")
    for signal, count in signal_counts.items():
        pct = (count / len(signals_df)) * 100
        logger.info(f"    {signal}: {count} ({pct:.1f}%)")

    return signals_df


def run_backtest(signals_df, asset_data, safe_haven_asset='none', label=''):
    """Run backtest with specified configuration."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running backtest: {label}")
    logger.info(f"  Safe haven asset: {safe_haven_asset}")
    logger.info(f"{'='*60}")

    # Create backtester
    backtester = Backtester(
        initial_capital=1000,
        risk_per_trade_pct=1.0,
        stop_loss_pct=0.5,
        take_profit_pct=1.0,
        spread_pct=0.002,
        slippage_pct=0.01
    )

    # Run backtest
    equity_curve = backtester.run(
        signals_df=signals_df,
        asset_data=asset_data,
        safe_haven_asset=safe_haven_asset
    )

    # Get trades DataFrame
    trades_df = backtester.get_trades_df()

    # Analyze performance
    metrics = PerformanceMetrics.calculate_all_metrics(
        equity_curve=equity_curve,
        trades_df=trades_df,
        initial_capital=backtester.initial_capital
    )

    return {
        'metrics': metrics,
        'trades': trades_df,
        'equity_curve': equity_curve,
        'backtester': backtester
    }


def print_comparison(results):
    """Print comparison of all strategies."""
    print("\n" + "="*80)
    print("STRATEGY COMPARISON - Safe Haven Trading Analysis")
    print("="*80)

    print(f"\n{'Metric':<25} {'SPY Only':<15} {'SPY + TLT':<15} {'SPY + GLD':<15}")
    print("-"*80)

    metrics_to_compare = [
        ('Total Return %', 'total_return_pct'),
        ('Win Rate %', 'win_rate'),
        ('Sharpe Ratio', 'sharpe_ratio'),
        ('Max Drawdown %', 'max_drawdown_pct'),
        ('Profit Factor', 'profit_factor'),
        ('Total Trades', 'total_trades'),
        ('Avg Trade Return %', 'avg_return_pct'),
        ('Expectancy $', 'expectancy')
    ]

    for display_name, metric_key in metrics_to_compare:
        spy_only = results['spy_only']['metrics'].get(metric_key, 0)
        spy_tlt = results['spy_tlt']['metrics'].get(metric_key, 0)
        spy_gld = results['spy_gld']['metrics'].get(metric_key, 0)

        # Format based on metric type
        if 'pct' in metric_key or 'rate' in metric_key:
            print(f"{display_name:<25} {spy_only:>14.2f} {spy_tlt:>14.2f} {spy_gld:>14.2f}")
        elif metric_key == 'total_trades':
            print(f"{display_name:<25} {spy_only:>14.0f} {spy_tlt:>14.0f} {spy_gld:>14.0f}")
        else:
            print(f"{display_name:<25} {spy_only:>14.2f} {spy_tlt:>14.2f} {spy_gld:>14.2f}")

    print("-"*80)

    # Determine winner
    returns = {
        'SPY Only': results['spy_only']['metrics'].get('total_return_pct', 0),
        'SPY + TLT': results['spy_tlt']['metrics'].get('total_return_pct', 0),
        'SPY + GLD': results['spy_gld']['metrics'].get('total_return_pct', 0)
    }

    winner = max(returns, key=returns.get)
    print(f"\n🏆 WINNER: {winner} (+{returns[winner]:.2f}%)")
    print("="*80)

    # Trade breakdown by asset
    print("\n" + "="*80)
    print("TRADE BREAKDOWN BY ASSET")
    print("="*80)

    for strategy_name, strategy_key in [('SPY Only', 'spy_only'), ('SPY + TLT', 'spy_tlt'), ('SPY + GLD', 'spy_gld')]:
        trades_df = results[strategy_key]['trades']

        if not trades_df.empty and 'asset' in trades_df.columns:
            print(f"\n{strategy_name}:")

            asset_breakdown = trades_df.groupby('asset').agg({
                'pnl': ['count', 'sum', 'mean'],
                'pnl_pct': 'mean'
            }).round(2)

            for asset in asset_breakdown.index:
                count = asset_breakdown.loc[asset, ('pnl', 'count')]
                total_pnl = asset_breakdown.loc[asset, ('pnl', 'sum')]
                avg_pnl = asset_breakdown.loc[asset, ('pnl', 'mean')]
                avg_pct = asset_breakdown.loc[asset, ('pnl_pct', 'mean')]

                # Win rate for this asset
                asset_trades = trades_df[trades_df['asset'] == asset]
                wins = (asset_trades['pnl'] > 0).sum()
                win_rate = (wins / count * 100) if count > 0 else 0

                print(f"  {asset}: {count:.0f} trades | Win Rate: {win_rate:.1f}% | "
                      f"Total P&L: ${total_pnl:.2f} | Avg: ${avg_pnl:.2f} ({avg_pct:+.2f}%)")
        else:
            print(f"\n{strategy_name}: Only SPY trades (no asset column in old data)")

    print("="*80)


def main():
    """Main execution."""
    print("\n" + "="*80)
    print("SAFE HAVEN TRADING STRATEGY TESTING")
    print("="*80)
    print("\nTesting three configurations:")
    print("  1. SPY LONG-ONLY (sit flat on RISK-OFF) - Original")
    print("  2. SPY + TLT (LONG TLT on RISK-OFF) - New")
    print("  3. SPY + GLD (LONG GLD on RISK-OFF) - New")
    print("\n" + "="*80)

    try:
        # Load data
        asset_data = load_data()

        # Generate signals
        signals_df = generate_signals(asset_data)

        # Run backtests
        results = {}

        # 1. SPY LONG-ONLY (original)
        results['spy_only'] = run_backtest(
            signals_df, asset_data,
            safe_haven_asset='none',
            label='SPY LONG-ONLY (Original)'
        )

        # 2. SPY + TLT
        results['spy_tlt'] = run_backtest(
            signals_df, asset_data,
            safe_haven_asset='TLT',
            label='SPY + TLT (Safe Haven)'
        )

        # 3. SPY + GLD
        results['spy_gld'] = run_backtest(
            signals_df, asset_data,
            safe_haven_asset='GLD',
            label='SPY + GLD (Safe Haven)'
        )

        # Print comparison
        print_comparison(results)

        # Recommendation
        print("\n" + "="*80)
        print("RECOMMENDATION")
        print("="*80)

        spy_only_return = results['spy_only']['metrics'].get('total_return_pct', 0)
        tlt_return = results['spy_tlt']['metrics'].get('total_return_pct', 0)
        gld_return = results['spy_gld']['metrics'].get('total_return_pct', 0)

        if tlt_return > spy_only_return and tlt_return > gld_return:
            print("✅ SWITCH TO SPY + TLT")
            print(f"   Improvement: +{tlt_return - spy_only_return:.2f}% over SPY-only")
            print("   Update config: safe_haven_asset: 'TLT'")
        elif gld_return > spy_only_return and gld_return > tlt_return:
            print("✅ SWITCH TO SPY + GLD")
            print(f"   Improvement: +{gld_return - spy_only_return:.2f}% over SPY-only")
            print("   Update config: safe_haven_asset: 'GLD'")
        else:
            print("⚠️  KEEP SPY LONG-ONLY")
            print("   Safe haven trading does not improve returns in backtest")
            print("   Keep config: safe_haven_asset: 'none'")

        print("="*80)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
