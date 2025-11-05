# claude-orderbook# RORO CFD Day Trading Strategy - Complete Specification

**Document Version**: 1.0
**Date**: November 2025
**Trading Style**: High-Frequency Day Trading (1-Minute Bars)
**Instrument**: Contracts for Difference (CFDs)
**Platform**: Trading 212
**Risk Level**: ⚠️ EXTREME - High leverage, high frequency

---

## Table of Contents

1. [Strategy Overview](#strategy-overview)
2. [Core Philosophy](#core-philosophy)
3. [The Three Pillars - Asset Relationships](#the-three-pillars)
4. [Technical Implementation Requirements](#technical-implementation-requirements)
5. [Signal Generation Logic](#signal-generation-logic)
6. [Entry & Exit Rules](#entry-exit-rules)
7. [Risk Management Framework](#risk-management-framework)
8. [Data Requirements](#data-requirements)
9. [System Architecture](#system-architecture)
10. [Critical Success Factors](#critical-success-factors)
11. [Known Limitations & Risks](#known-limitations-risks)

---

## 1. Strategy Overview

### What This Strategy Does

This is a **multivariate correlation-based momentum system** that detects shifts in global investor risk sentiment (Risk-On vs Risk-Off) by monitoring three simultaneous asset relationships in real-time on 1-minute bars.

**The Goal**: Catch intraday momentum waves when the market collectively shifts between:
- **Risk-On** → Growth/equities surge, safe havens decline
- **Risk-Off** → Flight to safety, equities decline, bonds/gold rally

### What Makes This Different

Unlike single-indicator systems (e.g., "just trade VIX"), this requires **multivariate consensus**:
- ✅ **2 out of 3 relationships must confirm** before entry
- ✅ Uses **ratio charts** (relative strength) not absolute prices
- ✅ Smooths 1-minute noise with moving averages
- ✅ Momentum confirmation required

This is like having three independent sensors all pointing to the same weather pattern before you act.

---

## 2. Core Philosophy

### The RORO Framework

**Risk-On/Risk-Off** is the variation in global investor risk aversion. It's not just "stocks up" or "stocks down" - it's about **collective rotation between asset classes**.

Four fundamental categories drive RORO:
1. **Credit Risk** (spreads widening/narrowing)
2. **Equity Volatility** (VIX rising/falling)
3. **Funding/Liquidity Conditions** (money availability)
4. **Currency & Gold Dynamics** (safe haven flows)

### Why Multivariate Matters

**Problem with single indicators**:
- VIX alone only reflects options market participants
- Gold alone can be influenced by dollar movements
- SPY alone doesn't tell you WHY it's moving

**Solution - Three Simultaneous Checks**:
By requiring 2-of-3 relationships to confirm, we ensure the signal represents **broad market consensus**, not a single market segment.

### The 1-Minute Challenge

Trading 1-minute bars introduces:
- ✅ **Speed**: Capture rapid intraday sentiment shifts
- ❌ **Noise**: Massive false signals from random fluctuations
- ❌ **Friction**: Transaction costs eat profits quickly
- ❌ **Slippage**: Execution delays on fast moves

**Strategy Answer**: Use ratio charts + moving averages to filter noise, require consensus for confirmation.

---

## 3. The Three Pillars - Asset Relationships

These are the three correlation pairs monitored simultaneously:

### Pillar 1: Equities vs Long Bonds (SPY vs TLT)

**What it measures**: Core risk appetite - stocks vs ultimate safe haven

| Scenario | Signal | Interpretation |
|----------|--------|----------------|
| **TLT rallies, SPY declines** | Risk-Off | Investors fleeing equities into safety |
| **SPY rallies, TLT declines** | Risk-On | Investors selling bonds to buy stocks |
| **Both rally or both decline** | Mixed/Neutral | Not a clear RORO signal |

**Ratio to Monitor**: `TLT / SPY`
- Rising ratio → Risk-Off (safe haven outperforming)
- Falling ratio → Risk-On (equities outperforming)

**Why this matters**: Most direct measure of equity risk appetite. When bonds outperform stocks, it's the clearest Risk-Off signal.

---

### Pillar 2: Gold vs Equities (GLD vs SPY)

**What it measures**: Flight to safety vs growth appetite

| Scenario | Signal | Interpretation |
|----------|--------|----------------|
| **Gold rallies, SPY declines** | Risk-Off | Classic safe haven bid |
| **SPY rallies, Gold declines** | Risk-On | Growth assets favored over safety |
| **Both rally** | Inflation/Liquidity surge | Complex - may not be pure RORO |

**Ratio to Monitor**: `GLD / SPY`
- Rising ratio → Risk-Off (gold outperforming)
- Falling ratio → Risk-On (stocks outperforming)

**Why this matters**: Gold is the ultimate "fear trade". If gold marches higher while SPY rolls over, it signals more downside coming for equities.

**Note**: Gold can be influenced by:
- Dollar strength/weakness (inverse correlation ~0.7 with EUR/USD)
- Inflation expectations
- Central bank policy

For intraday 1-minute trading, focus on **relative performance vs SPY** rather than absolute gold price.

---

### Pillar 3: Junk Bonds vs Long Bonds (HYG vs TLT)

**What it measures**: Credit risk appetite - willingness to take corporate risk

| Scenario | Signal | Interpretation |
|----------|--------|----------------|
| **HYG declines, TLT rallies** | Risk-Off | Credit markets freezing, flight to quality |
| **HYG rallies, TLT declines** | Risk-On | Investors hunting yield, confident in growth |
| **Both decline** | Rate fears/Complex | May indicate rising rate concerns |

**Ratio to Monitor**: `HYG / TLT`
- Falling ratio → Risk-Off (credit stress)
- Rising ratio → Risk-On (credit confidence)

**Why this matters**: High-yield corporate bonds are extremely sensitive to economic confidence. When HYG sells off while TLT rallies, it's a **caution signal** - credit markets are pricing in trouble.

**Credit Crisis Indicator**: During extreme Risk-Off events (2008, March 2020), HYG can collapse while TLT surges. This pillar gives early warning of credit stress that may not show up in VIX or SPY immediately.

---

## 4. Technical Implementation Requirements

### 4.1 Data Streams Required

For each asset, we need **1-minute bar data** with:
- Open, High, Low, Close (OHLC)
- Volume (optional but helpful)
- Timestamp (synchronized across all assets)

**Assets to stream**:
1. **SPY** - SPDR S&P 500 ETF (or CFD equivalent)
2. **TLT** - iShares 20+ Year Treasury Bond ETF (or CFD equivalent)
3. **GLD** - SPDR Gold Shares ETF (or CFD equivalent)
4. **HYG** - iShares iBoxx High Yield Corporate Bond ETF (or CFD equivalent)

**Data Source Strategy** (free sources):
- Primary: Yahoo Finance (yfinance library) - 1-minute intraday data
- Backup: Alpha Vantage API (free tier: 5 calls/min)
- Realtime: WebSocket connections if available
- Fallback: Scraping/polling every 60 seconds

**Critical Timing Issue**:
- All 4 assets must have synchronized timestamps
- Need to handle missing/delayed data for individual assets
- Maximum acceptable data lag: 10 seconds (for 1-minute strategy)

### 4.2 Ratio Calculations

For each pillar, calculate the **real-time ratio**:

```
Ratio_1 = TLT_close / SPY_close
Ratio_2 = GLD_close / SPY_close
Ratio_3 = HYG_close / TLT_close
```

**Update Frequency**: Every 1-minute bar close (00:00 seconds of each minute)

**Normalization**: Ratios should be normalized to starting value (e.g., 100) for easier visualization and comparison.

### 4.3 Smoothing Indicators

To filter 1-minute noise, apply moving averages to each ratio:

**Fast MA**: 5-period simple moving average (last 5 minutes)
**Slow MA**: 15-period simple moving average (last 15 minutes)

```
For each ratio:
  Fast_MA = SMA(ratio, period=5)
  Slow_MA = SMA(ratio, period=15)
```

**Crossover Detection**:
- **Bullish Cross** (for safe haven ratio): Fast MA crosses above Slow MA
- **Bearish Cross** (for safe haven ratio): Fast MA crosses below Slow MA

### 4.4 Momentum Confirmation

For the primary trade asset (SPY CFD), apply momentum indicator:

**RSI (Relative Strength Index)**:
- Period: 14 bars (14 minutes)
- Overbought: >70
- Oversold: <30

**Alternative Momentum Options**:
- Stochastic Oscillator (14,3,3)
- Rate of Change (ROC) 10-period
- MACD (12,26,9) - may be too slow for 1-minute

**Purpose**: Confirms that the ratio signal is backed by actual momentum in the underlying asset, not just ratio divergence.

---

## 5. Signal Generation Logic

### 5.1 Individual Pillar Signals

Each pillar generates one of three states every minute:

| Pillar State | Condition | Meaning |
|--------------|-----------|---------|
| **RISK-OFF** | Fast MA > Slow MA AND ratio rising | Safe haven outperforming |
| **RISK-ON** | Fast MA < Slow MA AND ratio falling | Risky asset outperforming |
| **NEUTRAL** | No clear crossover or conflicting signals | Mixed/uncertain |

### 5.2 Consensus Requirement (The Core Rule)

**Entry signals require 2-of-3 pillar consensus within a 5-minute observation window**

```
Current_Minute = N

Check pillars at minute N:
  Pillar_1_Signal (TLT/SPY)
  Pillar_2_Signal (GLD/SPY)
  Pillar_3_Signal (HYG/TLT)

Risk_Off_Count = Count(RISK-OFF signals)
Risk_On_Count = Count(RISK-ON signals)

IF Risk_Off_Count >= 2:
  → CONFIRMED RISK-OFF SIGNAL

IF Risk_On_Count >= 2:
  → CONFIRMED RISK-ON SIGNAL

ELSE:
  → NO CONSENSUS (Do not trade)
```

**5-Minute Confirmation Window**:
- Signals must align within 5 consecutive 1-minute bars
- This prevents acting on a single candle that may be noise
- Example: If 2 pillars show Risk-Off at minute N, and the 3rd confirms by minute N+4, that's valid consensus

### 5.3 Momentum Filter

Before executing trade, check SPY momentum:

**For Risk-On Entry (Long SPY)**:
- Require SPY RSI > 50 (momentum is positive)
- Or SPY close > SPY 20-period MA
- This prevents buying into a falling knife

**For Risk-Off Entry (Short SPY or Long TLT/GLD)**:
- Require SPY RSI < 50 (momentum is negative)
- Or SPY close < SPY 20-period MA
- This prevents shorting into a rally

**Optional Enhancement**: Check if SPY broke a key intraday support/resistance level.

---

## 6. Entry & Exit Rules

### 6.1 Entry Conditions

#### RISK-ON ENTRY (Long Equities)

**Conditions**:
1. ✅ 2 of 3 pillars show RISK-ON signal (within 5-minute window)
2. ✅ SPY RSI > 50 OR SPY > 20-period MA
3. ✅ No existing position (or opposite position to close)
4. ✅ Within trading hours (09:30-16:00 ET for US markets)

**Action**:
- **BUY (LONG)** SPY CFD
- Position size: Based on risk calculator (see Risk Management)
- Stop loss: 0.3% below entry (tight for 1-minute trading)
- Take profit: 0.6% above entry (1:2 risk-reward minimum)

**Alternative Assets** (sector rotation):
- QQQ CFD (tech-heavy, more volatile)
- IWM CFD (small caps, higher beta)
- Sector CFDs: XLF (financials), XLK (technology)

#### RISK-OFF ENTRY (Short Equities or Long Safe Havens)

**Conditions**:
1. ✅ 2 of 3 pillars show RISK-OFF signal (within 5-minute window)
2. ✅ SPY RSI < 50 OR SPY < 20-period MA
3. ✅ No existing position (or opposite position to close)
4. ✅ Within trading hours

**Action Option A - Short Equities**:
- **SELL (SHORT)** SPY CFD
- Position size: Based on risk calculator
- Stop loss: 0.3% above entry
- Take profit: 0.6% below entry

**Action Option B - Long Safe Havens**:
- **BUY (LONG)** TLT CFD or GLD CFD
- Safer than shorting, but may be less volatile
- Stop loss: 0.3% below entry
- Take profit: 0.4% above entry (safe havens move slower)

### 6.2 Exit Conditions

Exits can be triggered by multiple conditions (first to trigger closes the position):

#### Exit Type 1: Take Profit Hit
- **SPY Long**: Price reaches entry + 0.6%
- **SPY Short**: Price reaches entry - 0.6%
- Close position immediately, lock in profit

#### Exit Type 2: Stop Loss Hit
- **SPY Long**: Price reaches entry - 0.3%
- **SPY Short**: Price reaches entry + 0.3%
- Close position immediately, accept loss
- **Critical**: NEVER move stop loss further away

#### Exit Type 3: Regime Reversal
- **Current Position**: Long SPY (Risk-On)
- **New Signal**: 2-of-3 pillars flip to Risk-Off
- **Action**: Close long position immediately
- **Optional**: Open opposite position (short SPY) if momentum confirms

- **Current Position**: Short SPY (Risk-Off)
- **New Signal**: 2-of-3 pillars flip to Risk-On
- **Action**: Close short position immediately
- **Optional**: Open opposite position (long SPY) if momentum confirms

#### Exit Type 4: Time-Based Exit
- **End of Day**: Close all positions at 15:45 ET (15 min before market close)
- **Reason**: Avoid overnight CFD swap charges
- **Reason**: Avoid gap risk from overnight news

#### Exit Type 5: Consensus Loss
- **Current Position**: Long SPY (entered on 2-of-3 Risk-On)
- **New Signal**: Pillars go to 0-of-3 or 1-of-3 Risk-On (consensus broken)
- **Action**: Close position (don't wait for full reversal)
- **Reason**: Regime uncertainty = exit

### 6.3 Re-Entry Logic

After an exit, when can we re-enter?

**Cooldown Period**: 5 minutes minimum
- Prevents overtrading on choppy/whipsaw conditions
- If exit was due to stop loss, wait 10 minutes

**Re-Entry Allowed**:
- New consensus signal appears (2-of-3)
- Momentum indicator confirms new direction
- Not within last 30 minutes of trading day

---

## 7. Risk Management Framework

### 7.1 Position Sizing

**Base Rule**: Risk 1% of account per trade (0.5% for beginners)

**Calculation**:
```
Account_Balance = $1,000 (example)
Risk_Per_Trade = 1% = $10

Stop_Loss_Distance = 0.3% (for SPY at $450 = $1.35)

Position_Size = Risk_Amount / Stop_Loss_Distance
Position_Size = $10 / $1.35 = 7.4 shares

With 5x leverage (typical CFD):
  Buying_Power = $1,000 × 5 = $5,000
  Max_Position = $5,000 / $450 = 11 shares

Actual_Position = MIN(7.4, 11) = 7.4 shares (risk-based limit is tighter)
```

**Dynamic Position Sizing** (Advanced):
- Increase size slightly when win rate > 60% over last 20 trades
- Decrease size by 50% after 3 consecutive losses
- Never exceed 2% risk per trade under any circumstance

### 7.2 Leverage Discipline

**Maximum Leverage by Experience**:
- Beginner: 3x maximum
- Intermediate: 5x maximum
- Advanced: 10x maximum
- **NEVER use**: 20x, 50x, 100x (account destruction)

**Leverage Rule**:
- Total exposure (sum of all open positions) should not exceed Account × Leverage Limit
- With $1,000 and 5x leverage, max exposure = $5,000
- If holding multiple CFDs, sum them

### 7.3 Stop-Loss Policy (Non-Negotiable)

**Hard Rules**:
1. ✅ ALWAYS set stop loss when entering trade
2. ✅ NEVER move stop loss further away from entry
3. ✅ NEVER remove stop loss "to give it room"
4. ✅ NEVER hope the trade will come back

**Stop Loss Types**:
- **Fixed %**: 0.3% for 1-minute scalping
- **ATR-based**: 1.0 × ATR(14) for wider stops
- **Technical**: Below recent swing low (long) or above swing high (short)

**Mental Stop vs Hard Stop**:
- Always use **hard stop orders** on platform
- Mental stops fail due to emotion and hesitation
- 1-minute trading moves too fast for manual execution

### 7.4 Drawdown Management

**Maximum Drawdown Limits**:
- **Daily Loss Limit**: Stop trading if down 5% of account in one day
- **Weekly Loss Limit**: Stop trading if down 10% of account in one week
- **Monthly Loss Limit**: Re-evaluate strategy if down 15% in one month

**Drawdown Recovery**:
- After hitting daily limit, STOP trading that day
- Do not try to "make it back" - this causes revenge trading
- Review trades, analyze what went wrong
- Return next day with fresh mind and reduced position size

### 7.5 Friction Management (Critical for 1-Minute Trading)

**Transaction Costs to Monitor**:

1. **Spread** (Bid-Ask):
   - SPY CFD spread: ~$0.01-0.02 (0.002-0.004%)
   - TLT CFD spread: ~$0.03-0.05
   - GLD CFD spread: ~$0.02-0.03
   - HYG CFD spread: ~$0.05-0.10

2. **Commission** (if any):
   - Trading 212 CFDs: Commission-free (spread only)
   - Alternative brokers: $0-2 per trade

3. **Overnight Swap Charges**:
   - Typical: 0.01-0.03% per night
   - **Strategy Answer**: Close all positions before 16:00 ET daily

4. **Slippage**:
   - Market orders on fast moves: 0.01-0.05%
   - Limit orders: 0% (but may not fill)
   - **Strategy Answer**: Use limit orders during low volatility, market orders on breakouts

**Break-Even Calculation**:
```
Per-Trade Cost = Spread + Commission + Slippage
Example: $0.02 spread on $450 SPY = 0.0044%

To break even with 0.3% stop and 0.6% target:
  Average Cost per Round Trip = 0.0044% × 2 = 0.0088%

Win Rate Needed (at 1:2 R:R with 0.0088% friction):
  W × (0.6% - 0.0088%) + (1-W) × (-0.3% - 0.0088%) = 0
  Solving: W ≈ 34% minimum

Target Win Rate: 50%+ for comfortable profit margin
```

**Strategy Viability**:
- With 50% win rate and 1:2 R:R, each winning trade nets ~0.59% after friction
- Each losing trade costs ~0.31%
- Net expectancy per trade: (0.5 × 0.59%) + (0.5 × -0.31%) = +0.14%
- **This is razor-thin** - explains why most 1-minute traders fail

**Optimization**:
- Only trade during high-volume periods (10:00-11:30 ET, 14:00-15:30 ET)
- Avoid trading during lunch (low volume, wide spreads)
- Use limit orders when possible to avoid slippage

### 7.6 Psychological Risk Management

**Rules to Prevent Emotional Decisions**:

1. **No Revenge Trading**: After a loss, follow cooldown period strictly
2. **No FOMO**: Missing a trade is better than forcing a bad trade
3. **No Overconfidence**: After 5 wins in a row, reduce position size (not increase)
4. **No Analysis Paralysis**: If signal is clear, execute within 30 seconds
5. **No Position Monitoring**: Set alerts and walk away - watching leads to early exits

**Daily Routine**:
- Pre-market: Review previous day trades, check economic calendar
- Open: Wait for first 30 minutes (let market establish direction)
- Trading: Focus on 10:00-11:30 and 14:00-15:30 windows
- Close: Exit all positions by 15:45, no exceptions
- Post-market: Log trades, calculate statistics, identify lessons

---

## 8. Data Requirements

### 8.1 Required Data Feeds

| Asset | Ticker | Data Type | Update Frequency | Source |
|-------|--------|-----------|------------------|--------|
| S&P 500 ETF | SPY | 1-min OHLCV | Real-time / 60sec | Yahoo Finance / Alpha Vantage |
| Long Treasury ETF | TLT | 1-min OHLCV | Real-time / 60sec | Yahoo Finance / Alpha Vantage |
| Gold ETF | GLD | 1-min OHLCV | Real-time / 60sec | Yahoo Finance / Alpha Vantage |
| High Yield Bond ETF | HYG | 1-min OHLCV | Real-time / 60sec | Yahoo Finance / Alpha Vantage |

### 8.2 Historical Data for Backtesting

**Minimum Required**:
- Date Range: Last 6 months (covers multiple market regimes)
- Granularity: 1-minute bars
- Market Hours Only: 09:30-16:00 ET (6.5 hours × 60 = 390 bars per day)

**Storage Estimate**:
- 4 assets × 390 bars/day × 126 trading days (6 months) = ~196,000 bars
- Per bar: 6 fields (OHLCV + timestamp) × 8 bytes = 48 bytes
- Total: ~9.4 MB for 6 months of 1-minute data

### 8.3 Data Quality Requirements

**Synchronization**:
- All 4 assets must have data for same timestamp
- Handle missing bars (e.g., low-volume pre-market)
- Forward-fill gaps < 5 minutes
- Skip bar if >5 minute gap (data quality issue)

**Validation**:
- Sanity check: Price change >5% in 1 minute = likely bad data
- Volume = 0 for extended period = stale data
- Timestamp drift between assets <10 seconds acceptable

### 8.4 Real-Time Data Strategy

**Ideal (Best Performance)**:
- WebSocket connections to data provider
- Sub-second latency
- Continuous streaming during market hours

**Realistic (Free Sources)**:
- Poll API every 60 seconds (at :00 seconds)
- Batch request all 4 assets simultaneously
- Process and generate signals within 5 seconds
- Total loop time: 5-10 seconds (acceptable for 1-minute bars)

**Fallback (If API Rate Limited)**:
- Stagger requests: SPY at :00, TLT at :15, GLD at :30, HYG at :45
- Reconstruct "minute" data from staggered sources
- Less accurate but avoids rate limits

---

## 9. System Architecture

### 9.1 Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     RORO TRADING SYSTEM                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Data Collector  │─────▶│  Signal Engine   │─────▶│  Risk Manager    │
│                  │      │                  │      │                  │
│ - Fetch 1-min    │      │ - Calculate      │      │ - Position size  │
│   bars           │      │   ratios         │      │ - Stop loss      │
│ - 4 assets       │      │ - Apply MAs      │      │ - Take profit    │
│ - Sync timestamp │      │ - Check momentum │      │ - Drawdown check │
│ - Validate data  │      │ - Generate 2/3   │      │                  │
│                  │      │   consensus      │      │                  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
         │                         │                         │
         │                         │                         │
         ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Database        │      │  Backtester      │      │  Trade Executor  │
│                  │      │                  │      │                  │
│ - Store bars     │      │ - Historical     │      │ - Paper trade    │
│ - Store signals  │      │   simulation     │      │   first          │
│ - Store trades   │      │ - Performance    │      │ - Manual exec    │
│ - Audit log      │      │   metrics        │      │   for now        │
└──────────────────┘      │ - Optimize       │      │ - Future: API    │
                          │   parameters     │      │   integration    │
                          └──────────────────┘      └──────────────────┘
                                   │                         │
                                   │                         │
                                   ▼                         ▼
                          ┌──────────────────┐      ┌──────────────────┐
                          │  Visualizer      │      │  Alert System    │
                          │                  │      │                  │
                          │ - Live charts    │      │ - Desktop popup  │
                          │ - Ratio plots    │      │ - Sound alert    │
                          │ - P&L tracking   │      │ - Email/SMS      │
                          │ - Dashboard      │      │   (optional)     │
                          └──────────────────┘      └──────────────────┘
```

### 9.2 Module Specifications

#### Module 1: Data Collector
**Inputs**: None (pulls from external APIs)
**Outputs**: DataFrame with OHLCV for 4 assets, synchronized timestamps
**Frequency**: Every 60 seconds during market hours
**Error Handling**: Retry failed requests 3x, skip bar if all fail

#### Module 2: Signal Engine
**Inputs**: Current + historical bars (last 15 minutes minimum)
**Outputs**: Current RORO state (RISK-ON / RISK-OFF / NEUTRAL)
**Processing**:
1. Calculate 3 ratios (TLT/SPY, GLD/SPY, HYG/TLT)
2. Calculate 5-period and 15-period MAs for each ratio
3. Detect MA crossovers for each pillar
4. Count Risk-On and Risk-Off signals
5. Return consensus if 2-of-3 agree

#### Module 3: Risk Manager
**Inputs**: Current account balance, RORO signal, SPY price
**Outputs**: Position size (number of shares/contracts), stop loss price, take profit price
**Rules**:
- Risk 1% per trade
- Apply leverage limits
- Check daily drawdown limit before allowing trade
- Calculate precise stop/target levels

#### Module 4: Trade Executor
**Inputs**: Trade decision from Risk Manager
**Outputs**: Order placed on platform (paper trading initially)
**Phase 1**: Display signal on screen, user executes manually
**Phase 2**: Automated execution via Trading 212 API (if available)
**Phase 3**: Fallback to other broker with API (OANDA, Interactive Brokers)

#### Module 5: Backtester
**Inputs**: Historical 1-minute data (6+ months)
**Outputs**:
- Total return
- Win rate
- Sharpe ratio
- Max drawdown
- Trade log
- Equity curve

**Critical Features**:
- Realistic friction modeling (spread, slippage)
- Proper timestamp handling (no lookahead bias)
- Multiple timeframe results (daily P&L, weekly, monthly)

#### Module 6: Visualizer
**Real-Time Dashboard** showing:
- Current RORO consensus (big indicator: GREEN = Risk-On, RED = Risk-Off, YELLOW = Neutral)
- 3 ratio charts with MA crossovers highlighted
- SPY 1-minute chart with entry/exit points marked
- Current position (if any) with live P&L
- Today's trade log and statistics

**Charting Requirements**:
- Update every minute (not every tick - too resource intensive)
- Clean, minimal design (trader needs quick glance info)
- Color coding: Green = bullish, Red = bearish, Gray = neutral

#### Module 7: Alert System
**Trigger Conditions**:
- 2-of-3 consensus achieved → SOUND ALERT + DESKTOP POPUP
- Stop loss hit → SOUND ALERT (exit immediately)
- Take profit hit → SOUND ALERT (exit immediately)
- Daily loss limit reached → SOUND ALERT (stop trading)

**Alert Content**:
```
🟢 RISK-ON SIGNAL CONFIRMED
Action: LONG SPY CFD
Entry: $450.25
Stop: $448.90 (-0.3%)
Target: $452.95 (+0.6%)
Position Size: 7 shares
Risk: $10.00 (1%)
Time: 10:47:23 ET
```

---

## 10. Critical Success Factors

### What Makes or Breaks This Strategy

#### Factor 1: Data Latency ⚠️ CRITICAL
**Problem**: If data is delayed by even 60 seconds, you're trading on stale signals
**Solution**:
- Verify data timestamps match current time within 10 seconds
- Display "DATA STALE" warning if >30 second delay
- Do NOT trade on stale data (miss opportunity better than bad entry)

#### Factor 2: Execution Speed
**Problem**: 1-minute bars move fast; by the time you decide, price may have moved
**Solution**:
- Pre-calculate position size (don't wait until signal arrives)
- Use hotkeys for instant execution
- Have platform open and ready during trading hours
- Practice execution speed during paper trading phase

#### Factor 3: False Signal Filtering
**Problem**: Even with 2-of-3 consensus, some signals will be false
**Solution**:
- The 5-period and 15-period MAs smooth noise but add lag
- Shorter MAs = more signals but more whipsaws
- Longer MAs = fewer signals but less lag
- Testing required to find optimal MA periods for current market volatility

#### Factor 4: Transaction Costs
**Problem**: 0.01% spread × 2 (entry + exit) = 0.02% per trade
**Impact**: With 50 trades/day, costs = 1% daily (devastating)
**Solution**:
- Aim for <10 trades per day (quality over quantity)
- Only trade when conviction is highest
- Check spread before entering (avoid wide spreads during low volume)

#### Factor 5: Regime Persistence
**Problem**: RORO regimes can last minutes to hours
**Reality Check**:
- True Risk-Off events (panic) are rare (few times per year)
- Most days are choppy/neutral (no clear regime)
- Strategy will have many no-trade days
**Solution**:
- Accept that some days have no consensus signals
- Don't force trades when consensus is weak
- The best trade is sometimes no trade

#### Factor 6: Market Hours Concentration
**Problem**: Not all hours are equal for this strategy
**Best Trading Windows**:
- 10:00-11:30 ET: Post-open momentum established
- 14:00-15:30 ET: Afternoon trends develop
**Avoid**:
- 09:30-10:00 ET: Open volatility, wide spreads
- 12:00-13:30 ET: Lunch doldrums, low volume
- 15:45-16:00 ET: Close positioning, erratic moves

---

## 11. Known Limitations & Risks

### Strategy Limitations

1. **Correlation Breakdown**
   - **Problem**: Assets don't always respect historical correlations
   - **Example**: 2024 saw gold and SPY both rally together (+40% and +13%)
   - **Impact**: Risk-Off signals fail when correlations break down
   - **Mitigation**: Monitor correlation strength, add correlation filter

2. **Whipsaw Risk**
   - **Problem**: Markets can flip Risk-On → Risk-Off → Risk-On within 30 minutes
   - **Impact**: Consecutive stop losses before trend emerges
   - **Mitigation**: Cooldown period after stop loss, reduce size after losses

3. **Low Signal Frequency**
   - **Reality**: 2-of-3 consensus may only occur 5-10 times per day
   - **Impact**: Lots of waiting, temptation to force trades
   - **Mitigation**: Accept this is normal, use time to review other opportunities

4. **Overnight Gap Risk**
   - **Problem**: News breaks after 16:00, market gaps at 09:30 open
   - **Solution**: ALWAYS close positions before 16:00, no exceptions

5. **Flash Crash Events**
   - **Problem**: Rare but catastrophic - market drops 5% in minutes
   - **Impact**: Stop losses may not fill at expected price (slippage)
   - **Mitigation**: Never use excessive leverage, keep stops tight

### Technical Risks

1. **Data Feed Failure**
   - If API goes down mid-day, system blind
   - Solution: Have backup data source ready

2. **Internet Disconnection**
   - With open position, can't monitor or exit
   - Solution: Have mobile hotspot backup, platform mobile app

3. **Platform Outage**
   - Trading 212 servers crash (rare but possible)
   - Solution: Have second broker account for emergency exits

4. **Coding Errors**
   - Bug in signal calculation leads to wrong trades
   - Solution: Extensive backtesting, paper trading before live

### Financial Risks ⚠️

**Maximum Possible Loss**:
- With 5x leverage and poor risk management: **100% account loss possible**
- With proper 1% risk per trade: Requires 100 consecutive losses (statistically improbable)
- Realistic worst case: 20-30% drawdown during bad month

**Expectancy Reality Check**:
```
Win Rate: 50% (realistic for tested strategy)
Avg Win: +0.6% (after friction: +0.59%)
Avg Loss: -0.3% (after friction: -0.31%)

Expectancy per trade = (0.5 × 0.59%) - (0.5 × 0.31%) = +0.14%

With $1,000 account, 1% risk per trade:
  Expected profit per trade = $1,000 × 0.14% × (1% risk) = $0.14

With 10 trades per day:
  Daily expectancy = $1.40
  Monthly (20 days) = $28 (2.8% monthly return)

This is BEFORE accounting for:
  - Losing streaks (variance)
  - Psychological errors
  - Data issues
  - Slippage on fast moves
```

**Real-World Performance Expectation**:
- Good month: +5% to +8%
- Average month: +2% to +3%
- Bad month: -3% to -5%
- Annual: +20% to +40% (if strategy works consistently)

**Comparison to S&P 500**:
- SPY buy-and-hold: ~10% annually (historical average)
- This strategy aims for 20-40% but requires daily work and carries higher risk

---

## Final Assessment: Is This Strategy Worth Pursuing?

### Pros ✅

1. **Multivariate approach reduces false signals** (better than single-indicator systems)
2. **Based on fundamental market relationships** (not arbitrary technical patterns)
3. **Risk-defined**: 1% per trade, clear stops, defined drawdown limits
4. **Backtestable**: Can validate before risking real money
5. **Scalable**: Works with $500 or $50,000 account (% based)

### Cons ❌

1. **Extreme time commitment**: Requires monitoring 09:30-16:00 daily
2. **High stress**: 1-minute trading is mentally exhausting
3. **Thin edge**: Friction eats most of the edge (0.14% expectancy per trade)
4. **Low signal frequency**: 2-of-3 consensus is rare, lots of waiting
5. **Career risk**: Most day traders fail (statistics show 90%+ lose money)

### Recommendation

**If you proceed**:
1. ✅ Build the system completely
2. ✅ Backtest on 6+ months historical data
3. ✅ Paper trade for minimum 2 months
4. ✅ Start live with $500-1000 only
5. ✅ Track every trade, analyze monthly
6. ✅ Quit if down >15% after 3 months

**Alternative approach (less stressful)**:
- Use same RORO logic but on 15-minute or 1-hour bars
- Lower trading frequency, less friction drag
- Can hold positions 2-4 hours instead of minutes
- Easier to backtest and validate

**My honest assessment**:
This is a sophisticated system that **could work** if executed perfectly. But the 1-minute timeframe is brutal - most professionals avoid it. If you're determined, I'll build it exactly as specified. But consider starting with 5-minute or 15-minute bars first, validate the concept, then move to 1-minute if profitable.

---

## Next Steps (After Full Understanding)

1. **Review this document** - confirm I understood correctly
2. **Clarify any misunderstandings** - before we write code
3. **Decide on timeframe** - 1-minute as specified, or start with 5-minute?
4. **Set expectations** - this will take time to build and test properly
5. **Begin development** - start with data collector and signal engine

**I'm ready when you are. Let me know if anything in this document needs correction or clarification.**

---

*End of Strategy Specification Document*
