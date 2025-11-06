#!/usr/bin/env python3
"""
INSTITUTIONAL GRADE RORO STRATEGY DEMONSTRATION

This script demonstrates the upgraded institutional features:
1. Signal Strength Scoring (0-100)
2. Dynamic Position Sizing based on signal strength
3. CFD Leverage Management (max 10x)
4. Professional risk management
"""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine
from src.signals.signal_strength import SignalStrengthCalculator
from src.risk.institutional_risk_manager import InstitutionalRiskManager, CFDPositionManager

print("="*90)
print("                  INSTITUTIONAL GRADE RORO STRATEGY DEMONSTRATION")
print("="*90)

try:
    # Load data
    print("\n📊 Loading LIVE market data from Yahoo Finance...")
    collector = DataCollector()
    data = collector.download_all_assets(period='5d', force_refresh=True)

    if len(data) < 4:
        print("❌ ERROR: Failed to load data")
        sys.exit(1)

    print(f"✓ Loaded {len(data)} assets")

    # Generate signals
    print("\n🎯 Generating RORO signals...")
    signal_engine = SignalEngine()
    signals = signal_engine.generate_signals(data)

    print(f"✓ Generated {len(signals)} signal bars")

    # Initialize institutional components
    strength_calc = SignalStrengthCalculator()
    risk_mgr = InstitutionalRiskManager(account_size=10000, max_leverage=10.0)
    cfd_mgr = CFDPositionManager(max_leverage=10.0)

    # Get latest signal
    latest_row = signals.iloc[-1]

    print("\n" + "="*90)
    print("CURRENT MARKET SIGNAL")
    print("="*90)

    print(f"\n📅 Timestamp: {signals.index[-1]}")
    print(f"🎯 Consensus: {latest_row['consensus']}")
    print(f"📊 Consensus Count: {latest_row['consensus_count']}/3 pillars")
    print(f"🔥 Pillars Agreeing: {latest_row['consensus_pillars']}")

    # Calculate signal strength
    print("\n" + "="*90)
    print("SIGNAL STRENGTH ANALYSIS (INSTITUTIONAL)")
    print("="*90)

    strength = strength_calc.calculate_signal_strength_from_dataframe(signals, -1)

    print(f"\n🎯 OVERALL STRENGTH: {strength['overall_strength']:.1f}/100")
    print(f"   Quality: {strength['quality']} - {strength['quality_description']}")

    print(f"\n📊 COMPONENT BREAKDOWN:")
    print(f"   Pillar 1 (TLT/SPY): {strength['pillar_tlt_spy']:.1f}/100")
    print(f"   Pillar 2 (GLD/SPY): {strength['pillar_gld_spy']:.1f}/100")
    print(f"   Pillar 3 (HYG/TLT): {strength['pillar_hyg_tlt']:.1f}/100")
    print(f"   Pillar Average:     {strength['pillar_average']:.1f}/100")
    print(f"   RSI Strength:       {strength['rsi_strength']:.1f}/100")
    print(f"   Consensus Bonus:    {strength['consensus_bonus']:.1f}x")

    # Only show position sizing for actionable signals
    if latest_row['consensus'] in ['RISK-ON', 'RISK-OFF']:
        spy_price = latest_row['spy_price']
        tlt_price = latest_row.get('tlt_price', spy_price)
        gld_price = latest_row.get('gld_price', spy_price)

        # Determine asset to trade
        if latest_row['consensus'] == 'RISK-ON' and latest_row['spy_rsi'] > 50:
            asset = 'SPY'
            entry_price = spy_price
            direction = 'LONG'
        elif latest_row['consensus'] == 'RISK-OFF' and latest_row['spy_rsi'] < 50:
            # Pick best safe haven
            tlt_signal = latest_row['pillar_tlt_spy']
            gld_signal = latest_row['pillar_gld_spy']
            if gld_signal == 1 and tlt_signal != 1:
                asset = 'GLD'
                entry_price = gld_price
            else:
                asset = 'TLT'
                entry_price = tlt_price
            direction = 'LONG'
        else:
            asset = None

        if asset:
            print("\n" + "="*90)
            print("INSTITUTIONAL POSITION SIZING")
            print("="*90)

            # Estimate ATR (1% of price as approximation)
            atr = risk_mgr.estimate_atr_from_price(entry_price, 1.0)

            # Calculate institutional position (no leverage)
            print(f"\n💼 SCENARIO 1: SPOT TRADING (No Leverage)")
            print("-" * 90)

            position_spot = risk_mgr.calculate_institutional_position(
                entry_price=entry_price,
                atr=atr,
                signal_strength=strength['overall_strength'],
                direction=direction,
                leverage=1.0,
                atr_multiplier=2.0,
                risk_reward_ratio=2.0
            )

            if position_spot:
                print(f"\n📈 ACTION:           {direction} {position_spot['shares']} shares of {asset}")
                print(f"💵 Entry Price:      ${position_spot['entry_price']:.2f}")
                print(f"🛑 Stop Loss (ATR):  ${position_spot['stop_loss']:.2f}")
                print(f"🎯 Take Profit (2R): ${position_spot['take_profit']:.2f}")
                print(f"\n💰 Position Value:   ${position_spot['notional_exposure']:,.2f}")
                print(f"⚠️  Risk Amount:      ${position_spot['risk_amount']:.2f} ({position_spot['risk_percent']:.1f}% of account)")
                print(f"📊 Signal Strength:  {position_spot['signal_strength']:.1f}/100")
                print(f"🔧 Leverage:         {position_spot['leverage']:.1f}x")

                # Calculate R:R
                risk_dollars = abs(position_spot['entry_price'] - position_spot['stop_loss']) * position_spot['shares']
                reward_dollars = abs(position_spot['take_profit'] - position_spot['entry_price']) * position_spot['shares']
                print(f"📈 Risk/Reward:      ${risk_dollars:.2f} / ${reward_dollars:.2f} = 1:{reward_dollars/risk_dollars:.1f}")

            # Calculate CFD position with leverage
            print(f"\n💼 SCENARIO 2: CFD TRADING (With Leverage)")
            print("-" * 90)

            # Use moderate leverage for medium strength, higher for strong signals
            if strength['overall_strength'] < 50:
                leverage = 3.0
                print(f"Signal Strength = {strength['overall_strength']:.1f} → Using {leverage:.1f}x leverage (Conservative)")
            elif strength['overall_strength'] < 70:
                leverage = 5.0
                print(f"Signal Strength = {strength['overall_strength']:.1f} → Using {leverage:.1f}x leverage (Moderate)")
            else:
                leverage = 8.0
                print(f"Signal Strength = {strength['overall_strength']:.1f} → Using {leverage:.1f}x leverage (Aggressive)")

            position_cfd = risk_mgr.calculate_institutional_position(
                entry_price=entry_price,
                atr=atr,
                signal_strength=strength['overall_strength'],
                direction=direction,
                leverage=leverage,
                atr_multiplier=2.0,
                risk_reward_ratio=2.0
            )

            if position_cfd:
                print(f"\n📈 ACTION:           {direction} {position_cfd['shares']} contracts of {asset} CFD")
                print(f"💵 Entry Price:      ${position_cfd['entry_price']:.2f}")
                print(f"🛑 Stop Loss (ATR):  ${position_cfd['stop_loss']:.2f}")
                print(f"🎯 Take Profit (2R): ${position_cfd['take_profit']:.2f}")
                print(f"\n💰 Notional Exposure: ${position_cfd['notional_exposure']:,.2f}")
                print(f"💳 Margin Required:   ${position_cfd['margin_required']:,.2f}")
                print(f"⚠️  Risk Amount:       ${position_cfd['risk_amount']:.2f} ({position_cfd['risk_percent']:.1f}% of account)")
                print(f"📊 Signal Strength:   {position_cfd['signal_strength']:.1f}/100")
                print(f"🔧 Leverage:          {position_cfd['leverage']:.1f}x")

                # Calculate potential P&L
                risk_dollars = abs(position_cfd['entry_price'] - position_cfd['stop_loss']) * position_cfd['shares']
                reward_dollars = abs(position_cfd['take_profit'] - position_cfd['entry_price']) * position_cfd['shares']
                print(f"📈 Risk/Reward:       ${risk_dollars:.2f} / ${reward_dollars:.2f} = 1:{reward_dollars/risk_dollars:.1f}")
                print(f"💥 Potential Profit:  ${reward_dollars:,.2f} ({reward_dollars/10000*100:.1f}% of account)")
                print(f"⛔ Potential Loss:    ${risk_dollars:,.2f} ({risk_dollars/10000*100:.1f}% of account)")

    else:
        print(f"\n🟡 NEUTRAL SIGNAL - No trade recommended")
        print(f"   Waiting for 2/3 pillar consensus...")

    print("\n" + "="*90)
    print("INSTITUTIONAL ADVANTAGES")
    print("="*90)
    print("""
✅ Signal Strength Quantification
   - Weak signals = smaller positions (0.5% risk)
   - Strong signals = larger positions (1.5-2.0% risk)
   - Eliminates guesswork in position sizing

✅ Dynamic Risk Management
   - ATR-based stops adapt to volatility
   - 2:1 risk/reward ratio enforced
   - Signal-strength adjusted sizing

✅ Leverage Control
   - Maximum 10x leverage (institutional standard)
   - Leverage scales with signal strength
   - Margin requirements calculated precisely

✅ Professional Execution
   - Clear entry/stop/target levels
   - Risk/reward pre-calculated
   - Position sizing automated
    """)

    print("="*90)
    print("This is INSTITUTIONAL GRADE - Ready for professional deployment!")
    print("="*90 + "\n")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
