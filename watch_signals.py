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

    return latest

def display_signal(latest):
    """Display signal in compact format"""
    consensus = latest['consensus']
    spy_rsi = latest['spy_rsi']
    spy_price = latest['spy_price']
    tlt_price = latest.get('tlt_price', spy_price)
    gld_price = latest.get('gld_price', spy_price)

    safe_haven_asset = config.get('trading.safe_haven_asset', 'TLT')
    timestamp = datetime.now().strftime('%H:%M:%S')

    print(f"\n[{timestamp}] Consensus: {consensus:10s} | SPY RSI: {spy_rsi:5.1f} | ", end="")

    if consensus == 'RISK-ON' and spy_rsi > 50:
        sizing = calculate_position_sizing(spy_price)
        print(f"🟢 LONG SPY @ ${spy_price:.2f} ({sizing['shares']} shares)")
        return 'RISK-ON', 'SPY', spy_price, sizing

    elif consensus == 'RISK-OFF' and spy_rsi < 50:
        if safe_haven_asset == 'TLT':
            entry_price = tlt_price
            asset_name = 'TLT'
        elif safe_haven_asset == 'GLD':
            entry_price = gld_price
            asset_name = 'GLD'
        else:
            print(f"🟡 WAIT (safe haven disabled)")
            return 'RISK-OFF', 'NONE', 0, None

        sizing = calculate_position_sizing(entry_price)
        print(f"🔴 LONG {asset_name} @ ${entry_price:.2f} ({sizing['shares']} shares)")
        return 'RISK-OFF', asset_name, entry_price, sizing

    else:
        print(f"🟡 WAIT (no clear signal)")
        return 'NEUTRAL', 'NONE', 0, None

print("\n" + "="*80)
print("               RORO SIGNAL MONITOR (Updates every 60 seconds)")
print("="*80)
print("\nWatching for signal changes... Press Ctrl+C to stop\n")
print("Legend:")
print("  🟢 RISK-ON  = LONG SPY")
print("  🔴 RISK-OFF = LONG TLT/GLD")
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
