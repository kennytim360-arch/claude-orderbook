#!/usr/bin/env python3
"""Test if dashboard can fetch live data and generate signals"""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine

print("="*60)
print("Testing Live Data Collection and Signal Generation")
print("="*60)

try:
    # Test data collection
    print("\n1. Testing data collection...")
    collector = DataCollector()
    print("   ✓ DataCollector initialized")

    print("\n2. Fetching live data...")
    data = collector.download_all_assets(period='5d', force_refresh=False)

    if not data or 'SPY' not in data:
        print("   ✗ FAILED: No data returned")
        sys.exit(1)

    print(f"   ✓ Data collected for {len(data)} assets")
    for asset, df in data.items():
        if df is not None and not df.empty:
            print(f"     - {asset}: {len(df)} bars (latest: {df.index[-1]})")
        else:
            print(f"     - {asset}: NO DATA")

    # Test signal generation
    print("\n3. Testing signal generation...")
    signal_engine = SignalEngine()
    signals = signal_engine.generate_signals(data)

    if signals is None or signals.empty:
        print("   ✗ FAILED: No signals generated")
        sys.exit(1)

    print(f"   ✓ Generated {len(signals)} signal bars")

    # Test latest signal
    print("\n4. Testing latest signal retrieval...")
    latest = signal_engine.get_latest_signal(signals)

    if not latest:
        print("   ✗ FAILED: No latest signal")
        sys.exit(1)

    print(f"   ✓ Latest signal retrieved")
    print(f"\n   CONSENSUS: {latest['consensus']}")
    print(f"   SPY RSI: {latest['spy_rsi']:.1f}")

    # Check for price data
    print("\n5. Checking asset prices in signal...")
    print(f"   SPY Price: ${latest.get('spy_price', 'MISSING')}")
    print(f"   TLT Price: ${latest.get('tlt_price', 'MISSING')}")
    print(f"   GLD Price: ${latest.get('gld_price', 'MISSING')}")

    if 'tlt_price' not in latest or 'gld_price' not in latest:
        print("\n   ✗ ERROR: TLT or GLD prices missing from signal!")
        sys.exit(1)

    # Determine what action to take
    print("\n6. Determining trading action...")
    consensus = latest['consensus']
    spy_rsi = latest['spy_rsi']

    from src.utils.config_loader import config
    safe_haven = config.get('trading.safe_haven_asset', 'TLT')

    if consensus == 'RISK-ON' and spy_rsi > 50:
        action = f"LONG SPY @ ${latest['spy_price']:.2f}"
        print(f"   🟢 {action}")
    elif consensus == 'RISK-OFF' and spy_rsi < 50:
        if safe_haven == 'TLT':
            action = f"LONG TLT @ ${latest['tlt_price']:.2f}"
        elif safe_haven == 'GLD':
            action = f"LONG GLD @ ${latest['gld_price']:.2f}"
        else:
            action = "NO TRADE (safe haven disabled)"
        print(f"   🔴 {action}")
    else:
        action = "WAIT (no clear signal)"
        print(f"   🟡 {action}")

    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED - Dashboard should work")
    print("="*60)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
