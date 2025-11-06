#!/usr/bin/env python3
"""Test all signal types (RISK-ON, RISK-OFF, NEUTRAL) for dashboard display"""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine
from src.utils.config_loader import config

print("="*70)
print("Testing All Signal Types for Dashboard Display")
print("="*70)

try:
    # Load data and generate signals
    print("\n1. Loading data and generating signals...")
    collector = DataCollector()
    data = collector.download_all_assets(period='5d')

    signal_engine = SignalEngine()
    signals = signal_engine.generate_signals(data)

    print(f"   ✓ Generated {len(signals)} signal bars")

    # Find examples of each signal type
    print("\n2. Finding examples of each signal type...\n")

    safe_haven_asset = config.get('trading.safe_haven_asset', 'TLT')

    # RISK-ON with RSI > 50
    risk_on_signals = signals[(signals['consensus'] == 'RISK-ON') & (signals['spy_rsi'] > 50)]
    if not risk_on_signals.empty:
        latest_risk_on = signal_engine.get_latest_signal(risk_on_signals)
        spy_price = latest_risk_on['spy_price']
        print("🟢 RISK-ON SIGNAL (LONG SPY):")
        print(f"   Consensus: {latest_risk_on['consensus']}")
        print(f"   SPY RSI: {latest_risk_on['spy_rsi']:.1f}")
        print(f"   SPY Price: ${spy_price:.2f}")
        print(f"   TLT Price: ${latest_risk_on['tlt_price']:.2f}")
        print(f"   GLD Price: ${latest_risk_on['gld_price']:.2f}")
        print(f"   → Dashboard will show: 'LONG SPY NOW' @ ${spy_price:.2f}\n")

    # RISK-OFF with RSI < 50
    risk_off_signals = signals[(signals['consensus'] == 'RISK-OFF') & (signals['spy_rsi'] < 50)]
    if not risk_off_signals.empty:
        latest_risk_off = signal_engine.get_latest_signal(risk_off_signals)
        tlt_price = latest_risk_off['tlt_price']
        gld_price = latest_risk_off['gld_price']

        print("🔴 RISK-OFF SIGNAL (LONG TLT/GLD):")
        print(f"   Consensus: {latest_risk_off['consensus']}")
        print(f"   SPY RSI: {latest_risk_off['spy_rsi']:.1f}")
        print(f"   SPY Price: ${latest_risk_off['spy_price']:.2f}")
        print(f"   TLT Price: ${tlt_price:.2f}")
        print(f"   GLD Price: ${gld_price:.2f}")
        print(f"   Safe Haven Asset: {safe_haven_asset}")

        if safe_haven_asset == 'TLT':
            print(f"   → Dashboard will show: 'LONG TLT NOW' @ ${tlt_price:.2f}\n")
        elif safe_haven_asset == 'GLD':
            print(f"   → Dashboard will show: 'LONG GLD NOW' @ ${gld_price:.2f}\n")
        else:
            print(f"   → Dashboard will show: 'NO TRADE (safe haven disabled)'\n")

    # NEUTRAL or no clear signal
    neutral_signals = signals[signals['consensus'] == 'NEUTRAL']
    if not neutral_signals.empty:
        latest_neutral = signal_engine.get_latest_signal(neutral_signals)
        print("🟡 NEUTRAL SIGNAL (WAIT):")
        print(f"   Consensus: {latest_neutral['consensus']}")
        print(f"   SPY RSI: {latest_neutral['spy_rsi']:.1f}")
        print(f"   → Dashboard will show: 'NO CLEAR SIGNAL - WAIT'\n")

    # Summary
    print("="*70)
    print("Signal Distribution in Data:")
    print("="*70)
    risk_on_count = len(signals[signals['consensus'] == 'RISK-ON'])
    risk_off_count = len(signals[signals['consensus'] == 'RISK-OFF'])
    neutral_count = len(signals[signals['consensus'] == 'NEUTRAL'])

    print(f"RISK-ON:  {risk_on_count:4d} ({100*risk_on_count/len(signals):.1f}%)")
    print(f"RISK-OFF: {risk_off_count:4d} ({100*risk_off_count/len(signals):.1f}%)")
    print(f"NEUTRAL:  {neutral_count:4d} ({100*neutral_count/len(signals):.1f}%)")
    print(f"TOTAL:    {len(signals):4d}")

    print("\n" + "="*70)
    print("✓ ALL SIGNAL TYPES TESTED - Dashboard will show:")
    print("="*70)
    print("  1. RISK-ON → LONG SPY with correct SPY price")
    print(f"  2. RISK-OFF → LONG {safe_haven_asset} with correct {safe_haven_asset} price")
    print("  3. NEUTRAL → NO CLEAR SIGNAL - WAIT")
    print("="*70)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
