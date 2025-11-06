#!/usr/bin/env python3
"""Test GLD signals - Shows what LONG GLD signal looks like"""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine

print("\n" + "="*80)
print("                    TESTING GOLD (GLD) SIGNALS")
print("="*80)

try:
    print("\nLoading LIVE market data from Yahoo Finance...")
    collector = DataCollector()
    data = collector.download_all_assets(period='5d', force_refresh=True)

    if len(data) < 4:
        print("❌ ERROR: Failed to load market data")
        sys.exit(1)

    print("Generating signals...")
    signal_engine = SignalEngine()
    signals = signal_engine.generate_signals(data)

    # Find a RISK-OFF signal to demonstrate
    risk_off_signals = signals[(signals['consensus'] == 'RISK-OFF') & (signals['spy_rsi'] < 50)]

    if risk_off_signals.empty:
        print("\n⚠️  No RISK-OFF signals in recent data")
        print("   GLD would be traded during RISK-OFF periods")
    else:
        latest_risk_off = signal_engine.get_latest_signal(risk_off_signals)

        spy_price = latest_risk_off['spy_price']
        tlt_price = latest_risk_off['tlt_price']
        gld_price = latest_risk_off['gld_price']
        spy_rsi = latest_risk_off['spy_rsi']

        print("\n" + "="*80)
        print("EXAMPLE: RISK-OFF SIGNAL")
        print("="*80)
        print(f"\nConsensus: RISK-OFF")
        print(f"SPY RSI: {spy_rsi:.1f} (below 50 = bearish)")
        print(f"\nAsset Prices:")
        print(f"  SPY: ${spy_price:.2f}")
        print(f"  TLT: ${tlt_price:.2f}")
        print(f"  GLD: ${gld_price:.2f}")

        print("\n" + "="*80)
        print("DEPENDING ON CONFIG SETTING:")
        print("="*80)
        print(f"\nIf safe_haven_asset = 'TLT':")
        print(f"  🔴 LONG TLT @ ${tlt_price:.2f}")
        print(f"\nIf safe_haven_asset = 'GLD':")
        print(f"  🔴 LONG GLD @ ${gld_price:.2f}")

        print("\n" + "="*80)
        print("TO SWITCH TO GOLD:")
        print("="*80)
        print("\n1. Open: config/default_config.yaml")
        print("2. Find the line:")
        print("     safe_haven_asset: 'TLT'")
        print("3. Change to:")
        print("     safe_haven_asset: 'GLD'")
        print("4. Save and restart watch_signals.py")
        print("\n" + "="*80)

    # Check current signal
    latest = signal_engine.get_latest_signal(signals)
    print(f"\n📊 CURRENT SIGNAL: {latest['consensus']}")
    print(f"   SPY RSI: {latest['spy_rsi']:.1f}")
    print(f"   SPY: ${latest['spy_price']:.2f}")
    print(f"   TLT: ${latest['tlt_price']:.2f}")
    print(f"   GLD: ${latest['gld_price']:.2f}")
    print("\n" + "="*80)
    print("✅ GLD SIGNALS ARE SUPPORTED - Just change the config!")
    print("="*80 + "\n")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
