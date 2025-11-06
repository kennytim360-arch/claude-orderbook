#!/usr/bin/env python3
"""Display current trading signal in CLI format (since web dashboard isn't accessible)"""

import sys
sys.path.insert(0, '/home/user/claude-orderbook')

from src.data.data_collector import DataCollector
from src.signals.signal_engine import SignalEngine
from src.utils.config_loader import config
from datetime import datetime

def format_price(price):
    """Format price with color"""
    return f"${price:.2f}"

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

def pick_best_safe_haven(latest, data):
    """
    Intelligently pick between TLT and GLD based on strength.

    Returns: (asset_name, entry_price, reason)
    """
    tlt_price = latest.get('tlt_price')
    gld_price = latest.get('gld_price')

    # Get ratio signals to see which is stronger (1 = bullish, -1 = bearish)
    tlt_spy_signal = latest.get('pillar_tlt_spy', 0)
    gld_spy_signal = latest.get('pillar_gld_spy', 0)

    # Calculate recent momentum
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

    # Score each asset (ratio signal + momentum)
    tlt_score = tlt_spy_signal + (tlt_momentum / 2)
    gld_score = gld_spy_signal + (gld_momentum / 2)

    # Pick the stronger one
    if gld_score > tlt_score:
        reason = f"GLD is stronger (score: {gld_score:.1f} vs TLT: {tlt_score:.1f})"
        return 'GLD', gld_price, reason, gld_score, tlt_score
    else:
        reason = f"TLT is stronger (score: {tlt_score:.1f} vs GLD: {gld_score:.1f})"
        return 'TLT', tlt_price, reason, tlt_score, gld_score

print("\n" + "="*80)
print("                    RORO TRADING SYSTEM - CURRENT SIGNAL")
print("="*80)

try:
    # Load data and generate signals
    print("\nLoading LIVE market data from Yahoo Finance...")
    collector = DataCollector()
    # Force refresh to get LIVE data from Yahoo Finance
    data = collector.download_all_assets(period='5d', force_refresh=True)

    if len(data) < 4:
        print("❌ ERROR: Failed to load market data")
        sys.exit(1)

    print("Generating signals...")
    signal_engine = SignalEngine()
    signals = signal_engine.generate_signals(data)

    # Get latest signal
    latest = signal_engine.get_latest_signal(signals)

    # Get configuration
    safe_haven_asset = config.get('trading.safe_haven_asset', 'TLT')
    account_size = 10000

    consensus = latest['consensus']
    spy_rsi = latest['spy_rsi']
    spy_price = latest['spy_price']
    tlt_price = latest.get('tlt_price', spy_price)
    gld_price = latest.get('gld_price', spy_price)

    # Display market overview
    print("\n" + "="*80)
    print(f"⏰ TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    print(f"\n📊 MARKET STATUS:")
    print(f"   SPY Price:     {format_price(spy_price):>12}   RSI: {spy_rsi:.1f}")
    print(f"   TLT Price:     {format_price(tlt_price):>12}")
    print(f"   GLD Price:     {format_price(gld_price):>12}")

    print(f"\n🎯 CONSENSUS:      {consensus}")
    print(f"💰 ACCOUNT SIZE:   ${account_size:,.0f}")
    print(f"🤖 AUTO-SELECT:    BEST asset chosen intelligently")

    # Determine action
    print("\n" + "="*80)

    if consensus == 'RISK-ON' and spy_rsi > 50:
        # LONG SPY
        sizing = calculate_position_sizing(spy_price, account_size)

        print("🟢 SIGNAL: RISK-ON")
        print("="*80)
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              LONG SPY NOW                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

   📈 ACTION:         BUY {sizing['shares']} SHARES OF SPY

   💵 ENTRY PRICE:    {format_price(spy_price)}
   🛑 STOP LOSS:      {format_price(sizing['stop_loss'])}  (-0.5%)
   🎯 TAKE PROFIT:    {format_price(sizing['take_profit'])}  (+1.0%)

   💰 POSITION SIZE:  {format_price(sizing['position_value'])}
   ⚠️  RISK AMOUNT:   {format_price(sizing['risk_amount'])}  (1% of account)

   ✅ EXECUTE THIS TRADE NOW
        """)

    elif consensus == 'RISK-OFF' and spy_rsi < 50:
        # INTELLIGENTLY PICK BETWEEN TLT AND GLD
        asset_name, entry_price, reason, winner_score, loser_score = pick_best_safe_haven(latest, data)

        sizing = calculate_position_sizing(entry_price, account_size)

        print("🔴 SIGNAL: RISK-OFF")
        print("="*80)
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           LONG {asset_name} NOW                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

   📉 ACTION:         BUY {sizing['shares']} SHARES OF {asset_name}

   💵 ENTRY PRICE:    {format_price(entry_price)}
   🛑 STOP LOSS:      {format_price(sizing['stop_loss'])}  (-0.5%)
   🎯 TAKE PROFIT:    {format_price(sizing['take_profit'])}  (+1.0%)

   💰 POSITION SIZE:  {format_price(sizing['position_value'])}
   ⚠️  RISK AMOUNT:   {format_price(sizing['risk_amount'])}  (1% of account)

   🤖 WHY {asset_name}?        {reason}

   ✅ EXECUTE THIS TRADE NOW
        """)

    else:
        print("🟡 SIGNAL: NEUTRAL / NO CLEAR SIGNAL")
        print("="*80)
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         NO CLEAR SIGNAL - WAIT                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

   ⏸️  ACTION:         DO NOT ENTER ANY TRADES

   📊 REASON:         Consensus is {consensus} with SPY RSI at {spy_rsi:.1f}
                     Wait for a clear RISK-ON or RISK-OFF signal

   🔄 NEXT CHECK:     Run this script again in 5-10 minutes
        """)

    print("="*80)
    print("\n💡 TIP: Run this script anytime with:")
    print("   python show_current_signal.py")
    print("\n📈 STRATEGY: RORO (Risk-On/Risk-Off) with Intelligent Asset Selection")
    print("   - RISK-ON  + RSI>50  → LONG SPY")
    print("   - RISK-OFF + RSI<50  → LONG TLT or GLD (automatically picks BEST)")
    print("   - NEUTRAL            → WAIT")
    print("\n🤖 INTELLIGENT SELECTION: System compares TLT vs GLD strength and picks winner")
    print("="*80 + "\n")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
