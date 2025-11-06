#!/usr/bin/env python3
"""Watch for signal changes and display alerts (CLI dashboard alternative)"""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine
from src.utils.config_loader import config
from datetime import datetime
import time

def calculate_position_sizing(entry_price, account_size=10000, risk_percent=1.0,
                               stop_loss_percent=0.5, take_profit_percent=1.0):
    """Calculate position sizing"""
    risk_amount = account_size * (risk_percent / 100)
    stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
    take_profit_price = entry_price * (1 + take_profit_percent / 100)
    risk_per_share = entry_price - stop_loss_price
    shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
    position_value = shares * entry_price

    return {
        'shares': shares,
        'position_value': position_value,
        'stop_loss': stop_loss_price,
        'take_profit': take_profit_price,
        'risk_amount': risk_amount
    }

def get_signal_summary():
    """Get current signal summary"""
    collector = DataCollector()
    # Force refresh to get LIVE data from Yahoo Finance
    data = collector.download_all_assets(period='5d', force_refresh=True)

    if len(data) < 4:
        return None

    signal_engine = SignalEngine()
    signals = signal_engine.generate_signals(data)
    latest = signal_engine.get_latest_signal(signals)

    # Add raw data for intelligent asset selection
    latest['_raw_data'] = data

    return latest

def pick_best_safe_haven(latest):
    """
    Intelligently pick between TLT and GLD based on strength.

    Returns: (asset_name, entry_price, reason)
    """
    tlt_price = latest.get('tlt_price')
    gld_price = latest.get('gld_price')

    # Get ratio signals to see which is stronger (1 = bullish, -1 = bearish)
    tlt_spy_signal = latest.get('pillar_tlt_spy', 0)
    gld_spy_signal = latest.get('pillar_gld_spy', 0)

    # Calculate recent momentum from raw data if available
    data = latest.get('_raw_data', {})
    tlt_momentum = 0
    gld_momentum = 0

    if 'TLT' in data and 'GLD' in data:
        # Calculate 5-period momentum
        tlt_df = data['TLT']
        gld_df = data['GLD']

        if len(tlt_df) >= 5:
            tlt_momentum = (tlt_df['Close'].iloc[-1] / tlt_df['Close'].iloc[-5] - 1) * 100
        if len(gld_df) >= 5:
            gld_momentum = (gld_df['Close'].iloc[-1] / gld_df['Close'].iloc[-5] - 1) * 100

    # Score each asset (ratio signal + momentum/2)
    tlt_score = tlt_spy_signal + (tlt_momentum / 2)
    gld_score = gld_spy_signal + (gld_momentum / 2)

    # Pick the stronger one
    if gld_score > tlt_score:
        reason = f"GLD stronger (score: {gld_score:.1f} vs TLT: {tlt_score:.1f})"
        return 'GLD', gld_price, reason
    else:
        reason = f"TLT stronger (score: {tlt_score:.1f} vs GLD: {gld_score:.1f})"
        return 'TLT', tlt_price, reason

def display_signal(latest):
    """Display signal in compact format"""
    consensus = latest['consensus']
    spy_rsi = latest['spy_rsi']
    spy_price = latest['spy_price']
    tlt_price = latest.get('tlt_price', spy_price)
    gld_price = latest.get('gld_price', spy_price)

    timestamp = datetime.now().strftime('%H:%M:%S')

    print(f"\n[{timestamp}] Consensus: {consensus:10s} | SPY RSI: {spy_rsi:5.1f} | ", end="")

    if consensus == 'RISK-ON' and spy_rsi > 50:
        sizing = calculate_position_sizing(spy_price)
        print(f"🟢 LONG SPY @ ${spy_price:.2f} ({sizing['shares']} shares)")
        return 'RISK-ON', 'SPY', spy_price, sizing

    elif consensus == 'RISK-OFF' and spy_rsi < 50:
        # INTELLIGENTLY PICK BETWEEN TLT AND GLD
        asset_name, entry_price, reason = pick_best_safe_haven(latest)

        sizing = calculate_position_sizing(entry_price)
        print(f"🔴 LONG {asset_name} @ ${entry_price:.2f} ({sizing['shares']} shares) - {reason}")
        return 'RISK-OFF', asset_name, entry_price, sizing

    else:
        print(f"🟡 WAIT (no clear signal)")
        return 'NEUTRAL', 'NONE', 0, None

print("\n" + "="*80)
print("           RORO SIGNAL MONITOR (Updates every 60 seconds)")
print("="*80)
print("\nWatching for signal changes... Press Ctrl+C to stop\n")
print("💡 INTELLIGENT ASSET SELECTION:")
print("  🟢 RISK-ON  = LONG SPY")
print("  🔴 RISK-OFF = Automatically picks BEST between TLT & GLD")
print("  🟡 NEUTRAL  = WAIT")
print("\n" + "="*80)

previous_signal = None

try:
    while True:
        try:
            latest = get_signal_summary()

            if latest:
                current_signal = display_signal(latest)

                # Alert on signal change
                if previous_signal and previous_signal != current_signal:
                    print("\n" + "!"*80)
                    print("⚠️  SIGNAL CHANGE DETECTED!")
                    print("!"*80)

                    old_type, old_asset, old_price, old_sizing = previous_signal
                    new_type, new_asset, new_price, new_sizing = current_signal

                    print(f"\nOLD: {old_type} → {old_asset}")
                    print(f"NEW: {new_type} → {new_asset}")

                    if new_asset != 'NONE' and new_sizing:
                        print(f"\n🚨 ACTION REQUIRED:")
                        print(f"   BUY {new_sizing['shares']} shares of {new_asset} @ ${new_price:.2f}")
                        print(f"   Stop Loss: ${new_sizing['stop_loss']:.2f}")
                        print(f"   Take Profit: ${new_sizing['take_profit']:.2f}")

                    print("\n" + "!"*80 + "\n")

                previous_signal = current_signal

        except Exception as e:
            print(f"\n[ERROR] {e}")

        # Wait 60 seconds before next check
        time.sleep(60)

except KeyboardInterrupt:
    print("\n\n" + "="*80)
    print("Signal monitor stopped.")
    print("="*80 + "\n")
    sys.exit(0)
