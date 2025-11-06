#!/usr/bin/env python3
"""Watch for signal changes - CLEAN OUTPUT VERSION"""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine
from datetime import datetime
import time
import logging

# DISABLE ALL LOGGING OUTPUT
logging.disable(logging.CRITICAL)

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
    """Intelligently pick between TLT and GLD based on strength"""
    tlt_price = float(latest.get('tlt_price'))
    gld_price = float(latest.get('gld_price'))

    tlt_spy_signal = int(latest.get('pillar_tlt_spy', 0))
    gld_spy_signal = int(latest.get('pillar_gld_spy', 0))

    data = latest.get('_raw_data', {})
    tlt_momentum = 0.0
    gld_momentum = 0.0

    if 'TLT' in data and 'GLD' in data:
        tlt_df = data['TLT']
        gld_df = data['GLD']

        if len(tlt_df) >= 5:
            tlt_momentum = float((tlt_df['Close'].iloc[-1] / tlt_df['Close'].iloc[-5] - 1) * 100)
        if len(gld_df) >= 5:
            gld_momentum = float((gld_df['Close'].iloc[-1] / gld_df['Close'].iloc[-5] - 1) * 100)

    tlt_score = float(tlt_spy_signal + (tlt_momentum / 2))
    gld_score = float(gld_spy_signal + (gld_momentum / 2))

    if gld_score > tlt_score:
        return 'GLD', gld_price
    else:
        return 'TLT', tlt_price

def display_signal(latest):
    """Display signal in clean format with entry/exit prices"""
    consensus = latest['consensus']
    spy_rsi = float(latest['spy_rsi'])
    spy_price = float(latest['spy_price'])

    timestamp = datetime.now().strftime('%H:%M:%S')

    print("\n" + "="*80)
    print(f"[{timestamp}] RORO SIGNAL")
    print("="*80)

    if consensus == 'RISK-ON' and spy_rsi > 50:
        sizing = calculate_position_sizing(spy_price)

        print(f"\n🟢 CONSENSUS: RISK-ON")
        print(f"   SPY RSI: {spy_rsi:.1f} (Bullish)")
        print(f"\n📈 ACTION: LONG SPY")
        print(f"   Shares: {sizing['shares']}")
        print(f"   💵 Entry Price:  ${spy_price:.2f}")
        print(f"   🛑 Stop Loss:    ${sizing['stop_loss']:.2f}  (-0.5%)")
        print(f"   🎯 Take Profit:  ${sizing['take_profit']:.2f}  (+1.0%)")
        print(f"   💰 Position Size: ${sizing['position_value']:,.2f}")

        return 'RISK-ON', 'SPY', spy_price, sizing

    elif consensus == 'RISK-OFF' and spy_rsi < 50:
        asset_name, entry_price = pick_best_safe_haven(latest)
        sizing = calculate_position_sizing(entry_price)

        print(f"\n🔴 CONSENSUS: RISK-OFF")
        print(f"   SPY RSI: {spy_rsi:.1f} (Bearish)")
        print(f"\n📉 ACTION: LONG {asset_name}")
        print(f"   Shares: {sizing['shares']}")
        print(f"   💵 Entry Price:  ${entry_price:.2f}")
        print(f"   🛑 Stop Loss:    ${sizing['stop_loss']:.2f}  (-0.5%)")
        print(f"   🎯 Take Profit:  ${sizing['take_profit']:.2f}  (+1.0%)")
        print(f"   💰 Position Size: ${sizing['position_value']:,.2f}")

        return 'RISK-OFF', asset_name, entry_price, sizing

    else:
        print(f"\n🟡 CONSENSUS: NEUTRAL / WAIT")
        print(f"   SPY RSI: {spy_rsi:.1f}")
        print(f"\n⏸️  NO CLEAR SIGNAL - Stay in cash")

        return 'NEUTRAL', 'NONE', 0, None

print("\n" + "="*80)
print("           RORO INSTITUTIONAL TRADING SYSTEM - LIVE MONITOR")
print("="*80)
print("\n💡 INTELLIGENT ASSET SELECTION:")
print("   🟢 RISK-ON  = LONG SPY")
print("   🔴 RISK-OFF = LONG TLT or GLD (auto-selected)")
print("   🟡 NEUTRAL  = WAIT")
print("\n📊 Updates every 60 seconds with latest data")
print("   Press Ctrl+C to stop")
print("="*80)

previous_signal = None

try:
    while True:
        try:
            print("\n[Fetching latest market data...]", end="", flush=True)
            latest = get_signal_summary()
            print("\r" + " "*50 + "\r", end="", flush=True)  # Clear the fetching message

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
                        print(f"\n🚨 NEW TRADE SIGNAL:")
                        print(f"   LONG {new_asset} @ ${new_price:.2f}")
                        print(f"   Stop: ${new_sizing['stop_loss']:.2f}")
                        print(f"   Target: ${new_sizing['take_profit']:.2f}")

                    print("\n" + "!"*80)

                previous_signal = current_signal

        except Exception as e:
            print(f"\n[ERROR] {e}")

        # Wait 60 seconds before next check
        print(f"\n⏳ Next update in 60 seconds...", end="", flush=True)
        time.sleep(60)
        print("\r" + " "*50 + "\r", end="", flush=True)  # Clear the waiting message

except KeyboardInterrupt:
    print("\n\n" + "="*80)
    print("✅ Signal monitor stopped")
    print("="*80 + "\n")
    sys.exit(0)
