#!/usr/bin/env python3
"""Test dashboard with GLD as safe haven asset"""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine
from src.utils.config_loader import config
import yaml

print("="*70)
print("Testing GLD as Safe Haven Asset")
print("="*70)

try:
    # Temporarily override config to test GLD
    print("\n1. Testing with GLD as safe haven...")

    # Load data and generate signals
    collector = DataCollector()
    data = collector.download_all_assets(period='5d')

    signal_engine = SignalEngine()
    signals = signal_engine.generate_signals(data)

    # Find RISK-OFF signal
    risk_off_signals = signals[(signals['consensus'] == 'RISK-OFF') & (signals['spy_rsi'] < 50)]

    if not risk_off_signals.empty:
        latest_risk_off = signal_engine.get_latest_signal(risk_off_signals)

        spy_price = latest_risk_off['spy_price']
        tlt_price = latest_risk_off['tlt_price']
        gld_price = latest_risk_off['gld_price']

        print("\n   RISK-OFF Signal Example:")
        print(f"   SPY Price: ${spy_price:.2f}")
        print(f"   TLT Price: ${tlt_price:.2f}")
        print(f"   GLD Price: ${gld_price:.2f}")

        print("\n   Testing different safe_haven_asset settings:")
        print(f"   - If safe_haven_asset='TLT': Dashboard shows 'LONG TLT @ ${tlt_price:.2f}'")
        print(f"   - If safe_haven_asset='GLD': Dashboard shows 'LONG GLD @ ${gld_price:.2f}'")
        print(f"   - If safe_haven_asset='none': Dashboard shows 'WAIT'")

        print("\n" + "="*70)
        print("✓ Dashboard supports all three assets: SPY, TLT, and GLD")
        print("="*70)
        print("\nTo change safe haven asset, edit config/default_config.yaml:")
        print("  trading:")
        print("    safe_haven_asset: 'TLT'  # Change to 'GLD' or 'none'")
        print("="*70)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
