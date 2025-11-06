#!/usr/bin/env python3
"""Test what the dashboard actually shows."""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.signals.signal_engine import SignalEngine
from src.utils.config_loader import config
import pandas as pd

# Load CSV data
print("Loading data...")
data = {}
for asset in ['SPY', 'TLT', 'GLD', 'HYG']:
    df = pd.read_csv(f'/home/user/claude-orderbook/data/historical/{asset}_5min.csv', index_col=0, parse_dates=True)
    data[asset] = df

# Generate signals
print("Generating signals...")
engine = SignalEngine()
signals = engine.generate_signals(data)
latest_signal = engine.get_latest_signal(signals)

# Get config
safe_haven_asset = config.get('trading.safe_haven_asset', 'TLT')

# Simulate dashboard logic
consensus = latest_signal['consensus']
spy_price = latest_signal['spy_price']
tlt_price = latest_signal['tlt_price']
gld_price = latest_signal['gld_price']
spy_rsi = latest_signal['spy_rsi']

print("\n" + "="*60)
print("DASHBOARD WOULD SHOW:")
print("="*60)
print(f"Consensus: {consensus}")
print(f"SPY RSI: {spy_rsi:.1f}")
print(f"Safe Haven Asset: {safe_haven_asset}")
print()

# Determine what dashboard shows
if consensus == 'RISK-ON' and spy_rsi > 50:
    print("🟢 BANNER: LONG SPY NOW")
    print(f"   Asset: SPY")
    print(f"   Entry Price: ${spy_price:.2f}")
    print(f"   Stop Loss: ${spy_price * 0.995:.2f} (-0.5%)")
    print(f"   Take Profit: ${spy_price * 1.01:.2f} (+1.0%)")

elif consensus == 'RISK-OFF' and spy_rsi < 50 and safe_haven_asset != 'none':
    entry_price = tlt_price if safe_haven_asset == 'TLT' else gld_price
    print(f"🔴 BANNER: LONG {safe_haven_asset} NOW")
    print(f"   Asset: {safe_haven_asset}")
    print(f"   Entry Price: ${entry_price:.2f}")
    print(f"   Stop Loss: ${entry_price * 0.995:.2f} (-0.5%)")
    print(f"   Take Profit: ${entry_price * 1.01:.2f} (+1.0%)")

elif consensus == 'RISK-OFF':
    print(f"🔴 BANNER: STAY FLAT / EXIT LONGS")
    print(f"   (safe_haven_asset={safe_haven_asset})")

else:
    print("🟡 BANNER: NO CLEAR SIGNAL - WAIT")

print("="*60)
print()

# Now test RISK-OFF scenario by forcing it
print("\n" + "="*60)
print("SIMULATING RISK-OFF SIGNAL:")
print("="*60)

# Find a RISK-OFF signal in the data
risk_off_signals = signals[signals['consensus'] == 'RISK-OFF']
if len(risk_off_signals) > 0:
    test_signal = risk_off_signals.iloc[-1]
    test_dict = {
        'consensus': 'RISK-OFF',
        'spy_price': test_signal['spy_price'],
        'tlt_price': test_signal['tlt_price'],
        'gld_price': test_signal['gld_price'],
        'spy_rsi': 45.0  # Simulate bearish RSI
    }

    print(f"Consensus: {test_dict['consensus']}")
    print(f"SPY RSI: {test_dict['spy_rsi']:.1f}")
    print(f"Safe Haven Asset: {safe_haven_asset}")
    print()

    if safe_haven_asset != 'none':
        entry_price = test_dict['tlt_price'] if safe_haven_asset == 'TLT' else test_dict['gld_price']
        print(f"🔴 BANNER: LONG {safe_haven_asset} NOW")
        print(f"   Asset: {safe_haven_asset}")
        print(f"   Entry Price: ${entry_price:.2f}")
        print(f"   Stop Loss: ${entry_price * 0.995:.2f} (-0.5%)")
        print(f"   Take Profit: ${entry_price * 1.01:.2f} (+1.0%)")
    else:
        print(f"🔴 BANNER: STAY FLAT / EXIT LONGS")

print("="*60)
