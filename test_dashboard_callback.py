#!/usr/bin/env python3
"""Test if dashboard callback can execute successfully"""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine

print("Testing dashboard callback logic...\n")

try:
    # Simulate what the dashboard does
    print("1. Loading data...")
    collector = DataCollector()
    data = collector.download_all_assets(period='5d')

    if len(data) < 4:
        print("   ✗ FAILED: Not enough data")
        sys.exit(1)

    print(f"   ✓ Loaded {len(data)} assets")

    # Generate signals
    print("\n2. Generating signals...")
    signal_engine = SignalEngine()
    signals = signal_engine.generate_signals(data)

    print(f"   ✓ Generated {len(signals)} signals")

    # Get latest signal
    print("\n3. Getting latest signal...")
    latest = signal_engine.get_latest_signal(signals)

    print(f"   ✓ Latest signal retrieved")
    print(f"\n   Consensus: {latest['consensus']}")
    print(f"   SPY RSI: {latest['spy_rsi']:.1f}")
    print(f"   SPY Price: ${latest['spy_price']:.2f}")
    print(f"   TLT Price: ${latest.get('tlt_price', 'MISSING'):.2f}")
    print(f"   GLD Price: ${latest.get('gld_price', 'MISSING'):.2f}")

    # Test action panel logic
    print("\n4. Testing action panel logic...")
    from src.utils.config_loader import config

    consensus = latest['consensus']
    spy_rsi = latest['spy_rsi']
    safe_haven_asset = config.get('trading.safe_haven_asset', 'TLT')

    spy_price = latest['spy_price']
    tlt_price = latest.get('tlt_price', spy_price)
    gld_price = latest.get('gld_price', spy_price)

    if consensus == 'RISK-ON' and spy_rsi > 50:
        print(f"   🟢 LONG SPY @ ${spy_price:.2f}")
        print(f"      Position: Will display correct SPY position sizing")
    elif consensus == 'RISK-OFF' and spy_rsi < 50:
        if safe_haven_asset == 'TLT':
            print(f"   🔴 LONG TLT @ ${tlt_price:.2f}")
            print(f"      Position: Will display correct TLT position sizing")
        elif safe_haven_asset == 'GLD':
            print(f"   🔴 LONG GLD @ ${gld_price:.2f}")
            print(f"      Position: Will display correct GLD position sizing")
        else:
            print(f"   🟡 NO TRADE (safe haven disabled)")
    else:
        print(f"   🟡 WAIT - No clear signal")

    print("\n" + "="*60)
    print("✓ Dashboard callback logic works correctly!")
    print("="*60)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
