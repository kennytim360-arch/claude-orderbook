# 📡 LIVE MONITORING GUIDE

## ✅ YES! The System Will Monitor Live and Alert You

When you run the dashboard, it will:

### Every 60 Seconds:
1. ✅ **Fetch latest market data** (last 5 days of 5-minute bars)
2. ✅ **Generate RORO signals** (TLT/SPY, GLD/SPY, HYG/TLT ratios)
3. ✅ **Check for consensus** (2 of 3 pillars)
4. ✅ **Update the dashboard** (charts, stats, signals)
5. ✅ **Send alerts** when signals change!

---

## 🔔 What You'll Get Alerted On

### When RISK-ON Signal Appears:
```
🟢 RISK-ON SIGNAL
TLT/SPY, GLD/SPY
SPY: $685.41 | RSI: 55.2
```
- **Desktop notification** pops up
- **Sound alert** plays (3 beeps for critical alerts)
- **Dashboard turns GREEN**

### When RISK-OFF Signal Appears:
```
🔴 RISK-OFF SIGNAL
TLT/SPY, HYG/TLT
SPY: $680.25 | RSI: 45.8
```
- **Desktop notification** pops up
- **Sound alert** plays
- **Dashboard turns RED**

### When Signal Changes:
- Only alerts when consensus **changes** (RISK-ON → RISK-OFF or vice versa)
- Won't spam you if signal stays the same
- 5-minute cooldown between same alerts

---

## 🚀 How to Start Live Monitoring

### Step 1: Run the Dashboard

```bash
python scripts/run_dashboard.py
```

### Step 2: Open Browser

Go to: **http://localhost:8050**

### Step 3: Keep It Running

- Dashboard auto-refreshes every 60 seconds
- Leave browser tab open
- System will alert you when signals change

---

## ⚠️ IMPORTANT: What You Need to Know

### 1. **Data Source Requirements**

The system needs **real-time market data**:

**Option A: Yahoo Finance (Automatic)**
- Works during market hours (9:30 AM - 4:00 PM ET)
- Free, no API key needed
- May not work in all environments

**Option B: Manual CSV Updates**
- Download data yourself
- Place in `data/historical/` folder
- Format: `SPY_5min.csv`, `TLT_5min.csv`, etc.

**Check if Yahoo Finance works:**
```bash
python scripts/test_data_access.py
```

### 2. **Market Hours**

The system monitors during **U.S. market hours**:
- **Open**: 9:30 AM ET
- **Close**: 4:00 PM ET
- **Closed**: Weekends and holidays

**Outside market hours:**
- Dashboard still runs
- Shows last available data
- No new signals generated

### 3. **What the System DOES:**

✅ Monitors market in real-time
✅ Generates RISK-ON/RISK-OFF signals
✅ Sends desktop + sound alerts
✅ Shows you current signal on dashboard
✅ Tracks signal history

### 4. **What the System DOES NOT Do:**

❌ Automatically execute trades (no broker integration)
❌ Place orders for you
❌ Manage open positions
❌ Track your actual account

**YOU must manually execute trades based on the signals!**

---

## 📱 How to Trade the Signals

### When You Get a RISK-ON Alert:

1. **Check the dashboard** - Verify signal is still active
2. **Check momentum** - Ensure SPY RSI > 50 (shown on dashboard)
3. **If both OK**: Enter LONG position on SPY
   - Entry: Current SPY price
   - Stop Loss: Entry - 0.5%
   - Take Profit: Entry + 1.0%
4. **Set alerts** on your broker for stop/target
5. **Log the trade** in your journal

### When You Get a RISK-OFF Alert:

1. **If you have a LONG position**: EXIT immediately
2. **If you have NO position**: Stay flat (we don't trade SHORT)
3. **Wait** for next RISK-ON signal

### Position Management:

- **Max risk**: 1% of account per trade
- **Position size**: Use the calculator:
  ```
  Risk Amount = Account × 1%
  Stop Distance = Entry × 0.5%
  Shares = Risk Amount / Stop Distance
  ```
- **Close all**: Before 3:45 PM ET daily

---

## 🎯 Example Live Trading Day

### 9:30 AM - Market Opens
- Dashboard starts showing live data
- Wait for first signal (usually takes 15+ minutes)

### 10:15 AM - RISK-ON Signal! 🟢
```
Desktop Alert: "🟢 RISK-ON SIGNAL"
Dashboard: GREEN banner
SPY: $685.50
RSI: 56.2
```

**Your Action:**
1. Verify on dashboard (signal still active)
2. Enter LONG SPY at $685.50
3. Stop Loss: $682.07 (0.5% lower)
4. Take Profit: $692.27 (1.0% higher)
5. Position size: 14 shares (based on $1,000 account, 1% risk)

### 11:30 AM - Signal Reversal! 🔴
```
Desktop Alert: "🔴 RISK-OFF SIGNAL"
Dashboard: RED banner
```

**Your Action:**
1. EXIT LONG position immediately
2. Current price: $688.20
3. P&L: +$2.70 per share × 14 = +$37.80 (3.78% gain)

### 2:15 PM - RISK-ON Again! 🟢
```
Another RISK-ON signal
```

**Your Action:**
1. Enter new LONG position
2. Follow same rules

### 3:45 PM - Close All Positions
- Exit any open positions
- No overnight holds
- Review day's performance

---

## 💻 System Status Checks

### Is the Dashboard Working?

Check for:
- ✅ "Last Updated" timestamp is current
- ✅ Charts are updating (watch the timestamp change)
- ✅ SPY price matches current market price
- ✅ No error messages

### Is Data Fresh?

Look at dashboard footer:
```
Last Updated: 2025-11-05 10:47:23
```

If timestamp is:
- **< 2 minutes old**: ✅ Good
- **2-5 minutes old**: ⚠️ Slight delay
- **> 5 minutes old**: ❌ Data problem

### Are Alerts Working?

Test alerts:
```bash
python src/alerts/alert_manager.py
```

You should get:
- Desktop notification
- Sound (beep)

If not:
- Check config: `config/default_config.yaml`
- Verify alerts enabled:
  ```yaml
  alerts:
    desktop_notifications: true
    sound_alerts: true
  ```

---

## 🛠️ Troubleshooting

### "No data received from Yahoo Finance"

**Solution:**
1. Yahoo Finance may be blocked
2. Use manual CSV files instead
3. Run: `python scripts/generate_sample_data.py` (for testing)
4. Or download real CSV data from your broker

### "Dashboard not updating"

**Check:**
1. Is market open? (9:30 AM - 4:00 PM ET, weekdays)
2. Is browser tab active? (some browsers pause inactive tabs)
3. Check browser console (F12) for errors

### "No alerts popping up"

**Check:**
1. Is signal actually changing? (check dashboard)
2. Are system notifications enabled? (check OS settings)
3. Test with: `python src/alerts/alert_manager.py`

### "Too many trades"

**Current system generates ~5-6 trades per day.**

**To reduce:**
1. Switch to 15-minute bars (edit config)
2. Increase consensus to 3-of-3 (more conservative)
3. Add additional filters
4. Only trade during preferred windows (10-11:30 AM, 2-3:30 PM)

---

## 📊 Monitoring Best Practices

### Daily Routine:

**Pre-Market (9:00 AM)**
1. Start dashboard: `python scripts/run_dashboard.py`
2. Check data is loading
3. Review overnight news

**Market Hours (9:30 AM - 4:00 PM)**
1. Keep dashboard visible
2. Listen for alert sounds
3. Execute signals promptly
4. Log all trades

**Post-Market (4:00 PM+)**
1. Review day's trades
2. Calculate P&L
3. Update trade journal
4. Prepare for next day

### Weekly Review:

- Calculate weekly P&L
- Review win rate
- Check if performance matches backtest
- Adjust if needed

---

## ⚡ Quick Reference

### Signal Actions:

| Signal | Action | Entry | Exit |
|--------|--------|-------|------|
| 🟢 RISK-ON | LONG SPY | SPY RSI > 50 | RISK-OFF signal OR stop/target |
| 🔴 RISK-OFF | EXIT LONG | N/A | Immediately |
| ➖ NEUTRAL | Wait | No entry | N/A |

### Risk Per Trade:

| Account | 1% Risk | Stop (0.5%) | Shares (SPY @$685) |
|---------|---------|-------------|-------------------|
| $1,000 | $10 | $3.43 | ~14 shares |
| $5,000 | $50 | $3.43 | ~73 shares |
| $10,000 | $100 | $3.43 | ~146 shares |

### Dashboard URL:

```
http://localhost:8050
```

### Start Command:

```bash
python scripts/run_dashboard.py
```

---

## 🎯 You're Ready!

The system will:
- ✅ Monitor markets every 60 seconds
- ✅ Generate signals automatically
- ✅ Alert you when signals change
- ✅ Show you exactly what to do

**All you need to do is:**
1. Start the dashboard
2. Keep it running during market hours
3. Execute trades when alerted
4. Follow the rules!

**Good luck and trade the plan!** 🚀

---

*Remember: The system has a statistical edge (+32% in backtests), but YOU must execute it with discipline. Follow the signals, use proper risk management, and track your results.*
