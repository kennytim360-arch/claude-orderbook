# RORO Trading System - Development Plan

**Project**: RORO CFD Day Trading Strategy Implementation
**Version**: 1.0
**Date**: November 2025
**Estimated Timeline**: 6-8 weeks (full implementation + testing)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Development Phases](#development-phases)
3. [Phase Details & Task Breakdown](#phase-details--task-breakdown)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Testing Strategy](#testing-strategy)
7. [Risk Mitigation](#risk-mitigation)
8. [Timeline & Milestones](#timeline--milestones)
9. [Success Criteria](#success-criteria)
10. [Plan Review & Assessment](#plan-review--assessment)

---

## 1. Project Overview

### Goal
Build a fully functional, backtested, and paper-trading-ready RORO (Risk-On/Risk-Off) trading system that:
- Monitors 4 asset relationships in real-time (1-minute bars)
- Generates 2-of-3 consensus signals
- Manages risk automatically
- Provides visual dashboard and alerts
- Can be backtested thoroughly before live deployment

### Approach
Iterative development with emphasis on:
1. **Build incrementally** - Each phase produces working module
2. **Test continuously** - Unit tests + integration tests at each phase
3. **Validate early** - Backtest core logic before adding complexity
4. **Paper trade extensively** - Minimum 2 months before considering live trading

---

## 2. Development Phases

### Phase 0: Project Setup & Infrastructure (Week 1)
**Duration**: 3-5 days
**Goal**: Establish project foundation, dependencies, and data access

### Phase 1: Data Collection Module (Week 1-2)
**Duration**: 5-7 days
**Goal**: Reliable real-time and historical data ingestion for 4 assets

### Phase 2: Signal Engine Core (Week 2-3)
**Duration**: 7-10 days
**Goal**: Calculate ratios, moving averages, and generate 2-of-3 consensus signals

### Phase 3: Backtesting Framework (Week 3-4)
**Duration**: 7-10 days
**Goal**: Historical simulation with realistic friction modeling and performance metrics

### Phase 4: Risk Management System (Week 4-5)
**Duration**: 5-7 days
**Goal**: Position sizing, stop-loss, take-profit, drawdown controls

### Phase 5: Visualization & Dashboard (Week 5-6)
**Duration**: 7-10 days
**Goal**: Real-time charts, ratio plots, trade log, live P&L display

### Phase 6: Alert System (Week 6)
**Duration**: 3-5 days
**Goal**: Desktop notifications, sound alerts, email/SMS (optional)

### Phase 7: Paper Trading Integration (Week 6-7)
**Duration**: 5-7 days
**Goal**: Manual execution interface with signal tracking and performance logging

### Phase 8: Testing & Optimization (Week 7-8)
**Duration**: 7-14 days
**Goal**: Parameter optimization, stress testing, edge case handling

### Phase 9: Documentation & Deployment (Week 8)
**Duration**: 3-5 days
**Goal**: User manual, deployment scripts, monitoring setup

---

## 3. Phase Details & Task Breakdown

### Phase 0: Project Setup & Infrastructure

#### Tasks:
- [x] **0.1**: Initialize Git repository
- [ ] **0.2**: Set up Python virtual environment (Python 3.10+)
- [ ] **0.3**: Create project directory structure
- [ ] **0.4**: Install core dependencies (pandas, numpy, yfinance, matplotlib)
- [ ] **0.5**: Set up configuration management (YAML/JSON config files)
- [ ] **0.6**: Create logging infrastructure
- [ ] **0.7**: Set up database (SQLite for development, PostgreSQL optional)
- [ ] **0.8**: Write README with setup instructions
- [ ] **0.9**: Create .env template for API keys

#### Deliverables:
- Working development environment
- Project skeleton with all directories
- Configuration system functional
- Database schema created

#### Dependencies:
None (starting point)

---

### Phase 1: Data Collection Module

#### Tasks:
- [ ] **1.1**: Research and test Yahoo Finance API (yfinance library)
- [ ] **1.2**: Research and test Alpha Vantage API (backup source)
- [ ] **1.3**: Implement DataCollector class with error handling
- [ ] **1.4**: Create data synchronization logic (ensure timestamps align)
- [ ] **1.5**: Implement data validation (sanity checks for price spikes)
- [ ] **1.6**: Create historical data downloader (6+ months, 1-minute bars)
- [ ] **1.7**: Implement data storage (save to database and/or CSV)
- [ ] **1.8**: Create data retrieval functions (query by date range)
- [ ] **1.9**: Handle missing data (forward-fill, interpolation)
- [ ] **1.10**: Write unit tests for data collector
- [ ] **1.11**: Test real-time data polling (60-second loop during market hours)
- [ ] **1.12**: Measure data latency and log timestamps

#### Deliverables:
- `data_collector.py` module
- Historical data downloaded and stored (SPY, TLT, GLD, HYG)
- Real-time data polling script functional
- Data quality validation passing

#### Dependencies:
- Phase 0 complete

#### Key Decisions:
- **Primary data source**: Yahoo Finance (yfinance) - free, no API key needed
- **Backup source**: Alpha Vantage (requires free API key, 5 calls/min limit)
- **Storage format**: SQLite database + CSV backup
- **Data validation threshold**: Flag price changes >5% in 1 minute

---

### Phase 2: Signal Engine Core

#### Tasks:
- [ ] **2.1**: Implement ratio calculation (TLT/SPY, GLD/SPY, HYG/TLT)
- [ ] **2.2**: Implement moving average calculation (SMA 5 and 15 periods)
- [ ] **2.3**: Implement MA crossover detection
- [ ] **2.4**: Create individual pillar signal generation (RISK-ON/RISK-OFF/NEUTRAL)
- [ ] **2.5**: Implement 2-of-3 consensus logic
- [ ] **2.6**: Add momentum indicator (RSI 14-period for SPY)
- [ ] **2.7**: Implement momentum filter for entry confirmation
- [ ] **2.8**: Create SignalEngine class with clean interface
- [ ] **2.9**: Write unit tests for all signal calculations
- [ ] **2.10**: Test with historical data (verify signal accuracy)
- [ ] **2.11**: Create signal visualization (plot ratios with MA crossovers)
- [ ] **2.12**: Log all signals to database for analysis

#### Deliverables:
- `signal_engine.py` module
- Working 2-of-3 consensus signal generation
- RSI momentum confirmation functional
- Signal history logged and queryable

#### Dependencies:
- Phase 1 complete (need data to generate signals)

#### Key Decisions:
- **MA periods**: Start with 5 and 15 (can optimize later)
- **Momentum indicator**: RSI 14-period (standard setting)
- **Signal persistence**: Store every signal, not just entry/exit
- **Consensus window**: 5 minutes (configurable)

---

### Phase 3: Backtesting Framework

#### Tasks:
- [ ] **3.1**: Design backtester architecture (event-driven vs vectorized)
- [ ] **3.2**: Implement historical data replay with proper timestamp handling
- [ ] **3.3**: Integrate signal engine with backtester
- [ ] **3.4**: Implement order execution simulation (market orders)
- [ ] **3.5**: Add spread modeling (bid-ask spread simulation)
- [ ] **3.6**: Add slippage modeling (realistic execution costs)
- [ ] **3.7**: Add commission modeling (if applicable)
- [ ] **3.8**: Implement position tracking (entry, exit, P&L)
- [ ] **3.9**: Calculate performance metrics (total return, win rate, Sharpe, max drawdown)
- [ ] **3.10**: Create equity curve visualization
- [ ] **3.11**: Generate trade log with all entry/exit details
- [ ] **3.12**: Implement parameter sweep for optimization
- [ ] **3.13**: Add walk-forward analysis capability
- [ ] **3.14**: Test on multiple market regimes (trending, choppy, volatile)
- [ ] **3.15**: Validate no lookahead bias (critical!)

#### Deliverables:
- `backtester.py` module
- Performance metrics calculation functional
- Equity curve and trade log generation
- Initial backtest results on 6-month historical data

#### Dependencies:
- Phase 1 complete (historical data)
- Phase 2 complete (signal generation)

#### Key Decisions:
- **Backtester type**: Vectorized for speed (pandas-based)
- **Friction modeling**: Spread = 0.004% for SPY (configurable per asset)
- **Slippage**: 0.01% for market orders (aggressive assumption)
- **Performance period**: Last 6 months minimum, ideally 1-2 years
- **No lookahead prevention**: Use only data available at bar close time

#### Critical Validation:
- Compare manual calculation vs backtester output for sample trades
- Verify stop-loss and take-profit execution timing
- Ensure overnight positions are closed (if strategy requires)

---

### Phase 4: Risk Management System

#### Tasks:
- [ ] **4.1**: Implement position size calculator (based on % risk per trade)
- [ ] **4.2**: Add leverage limit enforcement
- [ ] **4.3**: Calculate stop-loss price based on entry and risk %
- [ ] **4.4**: Calculate take-profit price based on entry and reward:risk ratio
- [ ] **4.5**: Implement daily drawdown monitoring
- [ ] **4.6**: Implement weekly/monthly drawdown monitoring
- [ ] **4.7**: Create trading halt mechanism (when loss limit hit)
- [ ] **4.8**: Add cooldown period enforcement (after stop-loss)
- [ ] **4.9**: Implement dynamic position sizing (reduce after losses)
- [ ] **4.10**: Create risk report (exposure, current risk, daily P&L)
- [ ] **4.11**: Write unit tests for all risk calculations
- [ ] **4.12**: Integrate with backtester to test risk rules

#### Deliverables:
- `risk_manager.py` module
- Position sizing working correctly
- Drawdown limits enforced in backtests
- Risk report generation functional

#### Dependencies:
- Phase 3 complete (need backtester to validate risk rules)

#### Key Decisions:
- **Default risk per trade**: 1% of account
- **Maximum risk per trade**: 2% (configurable but enforced)
- **Daily loss limit**: 5% of account
- **Leverage limits**: 5x default (configurable by user experience level)
- **Stop-loss distance**: 0.3% for SPY (tight for 1-minute trading)
- **Take-profit distance**: 0.6% (1:2 risk:reward ratio)

---

### Phase 5: Visualization & Dashboard

#### Tasks:
- [ ] **5.1**: Choose visualization library (Plotly vs Matplotlib vs Dash)
- [ ] **5.2**: Create real-time ratio chart (3 ratios with MAs)
- [ ] **5.3**: Create SPY price chart with entry/exit markers
- [ ] **5.4**: Implement live P&L display (current position)
- [ ] **5.5**: Create RORO consensus indicator (big visual: GREEN/RED/YELLOW)
- [ ] **5.6**: Build trade log table (today's trades)
- [ ] **5.7**: Add statistics panel (win rate, daily P&L, trades count)
- [ ] **5.8**: Implement auto-refresh (every minute)
- [ ] **5.9**: Create equity curve chart (cumulative P&L)
- [ ] **5.10**: Add historical performance table (daily/weekly/monthly)
- [ ] **5.11**: Design clean, minimal UI (quick-glance info)
- [ ] **5.12**: Test dashboard performance (low CPU usage required)

#### Deliverables:
- `dashboard.py` module or web-based dashboard
- Real-time visualization of all 3 ratios
- Live trade monitoring
- Performance statistics display

#### Dependencies:
- Phase 2 complete (need signals to display)
- Phase 4 complete (need risk metrics to display)

#### Key Decisions:
- **Technology**: Plotly Dash (web-based, modern, interactive)
- **Update frequency**: Every 60 seconds (aligned with data updates)
- **Color scheme**: Green = Risk-On, Red = Risk-Off, Yellow = Neutral
- **Layout**: Single-page dashboard (no navigation needed)

#### UI Components:
1. **Top banner**: Current RORO consensus (large, obvious)
2. **Left panel**: 3 ratio charts stacked vertically
3. **Right panel**: SPY chart + current position + statistics
4. **Bottom section**: Trade log table

---

### Phase 6: Alert System

#### Tasks:
- [ ] **6.1**: Implement desktop notification system (cross-platform)
- [ ] **6.2**: Add sound alerts (different sounds for different events)
- [ ] **6.3**: Create alert for 2-of-3 consensus signal
- [ ] **6.4**: Create alert for stop-loss hit
- [ ] **6.5**: Create alert for take-profit hit
- [ ] **6.6**: Create alert for daily loss limit reached
- [ ] **6.7**: Add email notification (optional, using SMTP)
- [ ] **6.8**: Add SMS notification (optional, using Twilio API)
- [ ] **6.9**: Implement alert cooldown (prevent spam)
- [ ] **6.10**: Test alerts on all platforms (Windows/Mac/Linux)
- [ ] **6.11**: Create alert configuration (enable/disable specific alerts)

#### Deliverables:
- `alert_system.py` module
- Desktop notifications functional
- Sound alerts working
- Email/SMS optional features implemented

#### Dependencies:
- Phase 2 complete (need signals to trigger alerts)

#### Key Decisions:
- **Desktop notifications**: Use `plyer` library (cross-platform)
- **Sound alerts**: Use `pygame` or `playsound` library
- **Email**: SMTP with Gmail (user provides credentials)
- **SMS**: Twilio API (optional, user provides API key)
- **Alert priority**: Critical = sound + notification, Info = notification only

#### Alert Types:
1. **CRITICAL**: 2-of-3 consensus, stop-loss hit, daily limit reached
2. **WARNING**: Consensus broken, position underwater
3. **INFO**: Take-profit hit, trade closed

---

### Phase 7: Paper Trading Integration

#### Tasks:
- [ ] **7.1**: Design paper trading interface (display signals, user executes)
- [ ] **7.2**: Create trade logging system (manual entry confirmation)
- [ ] **7.3**: Implement position tracking (current holdings)
- [ ] **7.4**: Add paper account balance management
- [ ] **7.5**: Create execution confirmation dialog (show all trade details)
- [ ] **7.6**: Implement trade tracking (entry price, time, exit price, P&L)
- [ ] **7.7**: Add hotkey support for quick execution
- [ ] **7.8**: Create end-of-day summary report
- [ ] **7.9**: Implement trade journal (notes for each trade)
- [ ] **7.10**: Test paper trading workflow (simulate full day)
- [ ] **7.11**: Research Trading 212 API (if available for automation)
- [ ] **7.12**: Research alternative broker APIs (OANDA, Interactive Brokers)

#### Deliverables:
- `paper_trading.py` module
- Manual execution interface functional
- Trade tracking and P&L calculation working
- Daily summary reports generated

#### Dependencies:
- Phase 2 complete (signals)
- Phase 4 complete (risk management)
- Phase 5 complete (dashboard for monitoring)
- Phase 6 complete (alerts to notify user)

#### Key Decisions:
- **Phase 1 approach**: Manual execution (user clicks button when alert sounds)
- **Phase 2 approach** (future): Automated execution via broker API
- **Paper account size**: Start with $1,000 virtual balance
- **Execution tracking**: Log both signal generation time and actual execution time
- **Slippage recording**: Track difference between signal price and execution price

#### Paper Trading Requirements:
- Minimum 2 months paper trading before considering live trading
- Target metrics: Win rate >50%, Sharpe >1.5, max drawdown <15%
- Track psychological performance (did I follow the rules?)

---

### Phase 8: Testing & Optimization

#### Tasks:
- [ ] **8.1**: Run comprehensive backtests (1-2 years historical data)
- [ ] **8.2**: Test multiple MA period combinations (3/10, 5/15, 7/20)
- [ ] **8.3**: Test different risk:reward ratios (1:1, 1:2, 1:3)
- [ ] **8.4**: Test different stop-loss distances (0.2%, 0.3%, 0.5%)
- [ ] **8.5**: Analyze performance by time of day (find best trading windows)
- [ ] **8.6**: Analyze performance by market regime (trending vs choppy)
- [ ] **8.7**: Test edge cases (missing data, stale data, API failures)
- [ ] **8.8**: Stress test with extreme volatility periods (March 2020, etc.)
- [ ] **8.9**: Test correlation breakdown scenarios (gold + SPY both rallying)
- [ ] **8.10**: Measure system performance (CPU usage, memory, latency)
- [ ] **8.11**: Optimize code for speed (critical for 1-minute trading)
- [ ] **8.12**: Create parameter sensitivity analysis report
- [ ] **8.13**: Document optimal parameter set based on testing
- [ ] **8.14**: Run Monte Carlo simulation (assess randomness impact)
- [ ] **8.15**: Compare against buy-and-hold SPY benchmark

#### Deliverables:
- Comprehensive testing report
- Optimal parameter set documented
- Performance comparison vs benchmark
- Edge case handling verified

#### Dependencies:
- All previous phases complete

#### Key Metrics to Optimize For:
- **Win rate**: Target >50%
- **Sharpe ratio**: Target >1.5
- **Max drawdown**: Target <15%
- **Profit factor**: Target >1.5 (gross profit / gross loss)
- **Expectancy**: Target >0.1% per trade

#### Testing Periods:
1. **Bull market**: 2023 (SPY +26%)
2. **Bear market**: 2022 (SPY -18%)
3. **Volatile period**: March 2020 (COVID crash)
4. **Choppy period**: 2015-2016 (sideways)

---

### Phase 9: Documentation & Deployment

#### Tasks:
- [ ] **9.1**: Write user installation guide (step-by-step)
- [ ] **9.2**: Write user operation manual (how to run system daily)
- [ ] **9.3**: Document all configuration options
- [ ] **9.4**: Create troubleshooting guide (common issues)
- [ ] **9.5**: Write API documentation (for developers)
- [ ] **9.6**: Create deployment scripts (setup.sh, run.sh)
- [ ] **9.7**: Write system monitoring guide (health checks)
- [ ] **9.8**: Document live trading transition checklist
- [ ] **9.9**: Create backup and disaster recovery procedures
- [ ] **9.10**: Package system for distribution (requirements.txt, setup.py)
- [ ] **9.11**: Create demo video (optional but helpful)
- [ ] **9.12**: Write FAQ document

#### Deliverables:
- Complete user manual
- Installation scripts
- System ready for paper trading deployment
- Documentation for future maintenance

#### Dependencies:
- All previous phases complete

---

## 4. Technology Stack

### Core Programming
- **Language**: Python 3.10+
- **Package manager**: pip with virtual environment

### Data & Computation
- **Data manipulation**: pandas, numpy
- **Data sources**: yfinance (Yahoo Finance), alpha_vantage (backup)
- **Database**: SQLite (development), PostgreSQL (optional production)
- **Technical indicators**: pandas_ta or ta-lib

### Visualization
- **Dashboard**: Plotly Dash (web-based, interactive)
- **Charts**: Plotly (modern, fast)
- **Alternative**: Matplotlib (fallback if Dash too heavy)

### Backtesting
- **Framework**: Custom vectorized backtester (pandas-based)
- **Alternative**: Backtrader (if custom proves insufficient)

### Alerts
- **Desktop notifications**: plyer (cross-platform)
- **Sound alerts**: pygame or playsound
- **Email**: smtplib (built-in)
- **SMS**: Twilio (optional)

### Testing
- **Unit tests**: pytest
- **Code coverage**: pytest-cov
- **Linting**: pylint, black (code formatting)

### Utilities
- **Configuration**: PyYAML or JSON
- **Logging**: Python logging module
- **Scheduling**: APScheduler (for periodic tasks)
- **Date/Time**: pandas Timestamp, datetime

---

## 5. Project Structure

```
claude-orderbook/
│
├── README.md                          # Project overview and setup
├── DEVELOPMENT_PLAN.md               # This document
├── STRATEGY_SPEC.md                  # Original strategy specification
├── requirements.txt                   # Python dependencies
├── .env.template                      # Environment variables template
├── .gitignore                        # Git ignore rules
│
├── config/
│   ├── default_config.yaml           # Default configuration
│   ├── backtest_config.yaml          # Backtesting parameters
│   └── live_config.yaml              # Live trading parameters
│
├── data/
│   ├── historical/                    # Downloaded historical data
│   │   ├── SPY_1min.csv
│   │   ├── TLT_1min.csv
│   │   ├── GLD_1min.csv
│   │   └── HYG_1min.csv
│   ├── database/
│   │   └── trading.db                # SQLite database
│   └── logs/
│       └── system.log                # System logs
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_collector.py         # Real-time data fetching
│   │   ├── data_storage.py           # Database operations
│   │   ├── data_validator.py         # Data quality checks
│   │   └── historical_downloader.py  # Bulk historical download
│   │
│   ├── signals/
│   │   ├── __init__.py
│   │   ├── signal_engine.py          # Core signal generation
│   │   ├── ratio_calculator.py       # Ratio calculations
│   │   ├── indicators.py             # Technical indicators (MA, RSI)
│   │   └── consensus.py              # 2-of-3 consensus logic
│   │
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── backtester.py             # Main backtesting engine
│   │   ├── performance.py            # Performance metrics
│   │   ├── friction.py               # Spread/slippage modeling
│   │   └── optimizer.py              # Parameter optimization
│   │
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── risk_manager.py           # Position sizing and limits
│   │   ├── position.py               # Position tracking
│   │   └── drawdown.py               # Drawdown monitoring
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── paper_trading.py          # Paper trading interface
│   │   ├── order_manager.py          # Order tracking
│   │   └── broker_api.py             # Future: broker integration
│   │
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── dashboard.py              # Main dashboard app
│   │   ├── charts.py                 # Chart components
│   │   └── reports.py                # Report generation
│   │
│   ├── alerts/
│   │   ├── __init__.py
│   │   ├── alert_manager.py          # Alert coordination
│   │   ├── notifications.py          # Desktop notifications
│   │   ├── sounds.py                 # Sound alerts
│   │   └── email_sms.py              # Email/SMS (optional)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config_loader.py          # Configuration management
│       ├── logger.py                 # Logging setup
│       ├── time_utils.py             # Market hours, timezone handling
│       └── validators.py             # Input validation
│
├── tests/
│   ├── __init__.py
│   ├── test_data_collector.py
│   ├── test_signal_engine.py
│   ├── test_backtester.py
│   ├── test_risk_manager.py
│   └── integration/
│       └── test_full_pipeline.py
│
├── scripts/
│   ├── setup_environment.sh          # Initial setup script
│   ├── download_historical_data.py   # One-time data download
│   ├── run_backtest.py               # Run backtesting
│   ├── run_paper_trading.py          # Start paper trading
│   └── run_dashboard.py              # Launch dashboard
│
├── notebooks/
│   ├── 01_data_exploration.ipynb     # Data quality analysis
│   ├── 02_signal_analysis.ipynb      # Signal performance analysis
│   ├── 03_backtest_results.ipynb     # Backtest visualization
│   └── 04_optimization.ipynb         # Parameter optimization
│
└── docs/
    ├── USER_MANUAL.md                # How to use the system
    ├── API_REFERENCE.md              # Developer documentation
    ├── TROUBLESHOOTING.md            # Common issues
    └── LIVE_TRADING_CHECKLIST.md    # Pre-live trading checks
```

---

## 6. Testing Strategy

### Unit Testing
- **Coverage target**: >80% for core modules (signal engine, risk manager)
- **Framework**: pytest
- **Approach**: Test each function with known inputs/outputs

**Key modules requiring extensive unit tests**:
1. Ratio calculations (precise math)
2. Moving average calculations
3. Signal generation logic
4. Position sizing calculations
5. Stop-loss/take-profit calculations

### Integration Testing
- **Test full pipeline**: Data → Signals → Risk → Execution
- **Test with real historical data**: Verify system works end-to-end
- **Test edge cases**: Missing data, API failures, extreme volatility

### Backtesting Validation
- **Manual verification**: Calculate a few trades by hand, compare to backtester
- **Known outcomes test**: Test on period where we know what happened
- **Lookahead bias check**: Ensure no future data used in decisions

### Paper Trading Validation
- **Live monitoring**: Run system in paper mode for 2+ months
- **Compare to backtest**: Are live results similar to backtest? (they should be)
- **Track execution quality**: Slippage, timing, missed signals

### Performance Testing
- **Latency measurement**: Time from data arrival to signal generation (<1 second target)
- **CPU/Memory usage**: Should not exceed 50% on modest hardware
- **Dashboard responsiveness**: Updates within 1 second of new data

---

## 7. Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data feed failure | Medium | Critical | Backup data source (Alpha Vantage), alerts on data staleness |
| API rate limiting | High | Medium | Respect rate limits, implement exponential backoff, cache data |
| Calculation errors | Low | Critical | Extensive unit testing, manual verification, code review |
| Dashboard crashes | Medium | Low | Error handling, automatic restart, logging |
| Database corruption | Low | High | Regular backups, transaction safety, data validation |

### Strategy Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Whipsaw trades | High | Medium | Cooldown periods, tighter consensus requirements |
| Correlation breakdown | Medium | High | Monitor correlation strength, add correlation filter |
| Low signal frequency | High | Low | Accept this is normal, don't force trades |
| Overfitting in backtest | Medium | Critical | Walk-forward analysis, multiple test periods, out-of-sample testing |
| Black swan events | Low | Critical | Position sizing limits, never exceed 2% risk per trade |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| User doesn't follow rules | High | High | Automated enforcement where possible, alerts, journaling |
| Emotional trading | High | Critical | Paper trading for 2+ months first, daily review habit |
| System not monitored | Medium | Medium | Mobile alerts, redundant notification methods |
| Gradual strategy decay | Medium | High | Monthly performance review, re-optimization quarterly |

---

## 8. Timeline & Milestones

### Week 1: Foundation
- **Days 1-2**: Project setup, environment, dependencies
- **Days 3-5**: Data collector implementation
- **Milestone**: Successfully download 6 months historical data for all 4 assets

### Week 2: Core Logic
- **Days 6-10**: Signal engine implementation
- **Milestone**: Generate accurate 2-of-3 consensus signals on historical data

### Week 3: Validation
- **Days 11-15**: Backtesting framework
- **Milestone**: Run first full backtest on 6-month period, get performance metrics

### Week 4: Risk
- **Days 16-20**: Risk management system
- **Milestone**: Backtest with full risk controls, verify position sizing correct

### Week 5: Visualization
- **Days 21-25**: Dashboard and charts
- **Milestone**: Real-time dashboard running, updating every minute

### Week 6: Alerts & Integration
- **Days 26-30**: Alert system and paper trading interface
- **Milestone**: Receive alerts, execute paper trades, track results

### Week 7: Testing
- **Days 31-35**: Comprehensive testing and optimization
- **Milestone**: System tested on multiple market periods, optimal parameters identified

### Week 8: Documentation & Deployment
- **Days 36-40**: Documentation, deployment scripts, final polish
- **Milestone**: System ready for 2-month paper trading period

### Post-Development: Paper Trading Period
- **Months 3-4**: Daily paper trading, performance tracking, refinement
- **Milestone**: Achieve target metrics (>50% win rate, Sharpe >1.5, drawdown <15%)

### Future: Live Trading Decision
- **Month 5**: Review paper trading results, decide whether to go live
- **If successful**: Start with small real account ($500-1000), continue monitoring

---

## 9. Success Criteria

### Phase-Level Success Criteria

**Phase 0-1**: Data Collection
- ✅ Download 6+ months historical data for SPY, TLT, GLD, HYG
- ✅ Data quality checks passing (no gaps >5 minutes)
- ✅ Real-time data polling working with <10 second latency

**Phase 2**: Signal Engine
- ✅ Ratios calculated correctly (manual verification on sample data)
- ✅ Moving averages matching expected values
- ✅ 2-of-3 consensus signals generated accurately

**Phase 3**: Backtesting
- ✅ Backtest completes on 6-month period without errors
- ✅ Performance metrics calculated correctly
- ✅ No lookahead bias detected (manual inspection)
- ✅ Trade log matches manual calculation for sample trades

**Phase 4**: Risk Management
- ✅ Position sizing within 1% of manual calculation
- ✅ Stop-loss and take-profit prices correct
- ✅ Drawdown limits enforced in backtests

**Phase 5**: Visualization
- ✅ Dashboard loads in <5 seconds
- ✅ Charts update every minute automatically
- ✅ All data displayed correctly (no visual glitches)

**Phase 6**: Alerts
- ✅ Alerts trigger on correct conditions
- ✅ No false alerts (extensive testing)
- ✅ Alerts received within 5 seconds of signal

**Phase 7**: Paper Trading
- ✅ Trades logged correctly
- ✅ P&L calculation matches expectations
- ✅ End-of-day summary accurate

**Phase 8**: Testing & Optimization
- ✅ System tested on 1+ year historical data
- ✅ Parameter optimization completed
- ✅ Edge cases handled gracefully

**Phase 9**: Documentation
- ✅ User can install and run system following documentation
- ✅ All features documented

### Overall Project Success Criteria

**Technical Success**:
1. ✅ System runs reliably for 8 hours straight (market open to close)
2. ✅ Data updates every minute with <10 second latency
3. ✅ Signals generated accurately (matches manual calculation)
4. ✅ No crashes or critical errors during 1-week test period
5. ✅ Dashboard responsive (<1 second update time)

**Backtest Performance** (necessary but not sufficient):
1. ✅ Win rate: >45% (accounting for friction)
2. ✅ Sharpe ratio: >1.0 (risk-adjusted returns positive)
3. ✅ Max drawdown: <20% (tolerable loss)
4. ✅ Profit factor: >1.3 (gross profit / gross loss)
5. ✅ Trades per day: 5-15 (not too few, not too many)

**Paper Trading Success** (2-month period):
1. ✅ Win rate: >50% (real execution vs backtest)
2. ✅ Sharpe ratio: >1.5 (better risk-adjusted returns)
3. ✅ Max drawdown: <15% (controlled risk)
4. ✅ User followed rules >95% of time (discipline)
5. ✅ No single day loss >5% (risk management working)

**Go/No-Go Decision** (after paper trading):
- **GO LIVE**: If all paper trading success criteria met consistently for 2 months
- **CONTINUE PAPER**: If close but not quite there, extend paper trading
- **RE-EVALUATE**: If win rate <45% or drawdown >20%, strategy may not work
- **ABANDON**: If consistent losses for 2 months, strategy fundamentally flawed

---

## 10. Plan Review & Assessment

### Plan Strengths ✅

1. **Incremental Development**
   - Each phase produces working module
   - Can test as we go, catch issues early
   - Reduces risk of building something that doesn't work

2. **Testing Emphasis**
   - Unit tests, integration tests, backtests, paper trading
   - Multiple validation layers before risking money
   - Appropriate for high-risk trading system

3. **Realistic Timeline**
   - 6-8 weeks for full system is achievable
   - Not rushed (quality over speed)
   - Includes 2-month paper trading before live (critical)

4. **Clear Dependencies**
   - Each phase builds on previous
   - No circular dependencies
   - Can work sequentially without confusion

5. **Comprehensive Documentation**
   - User manual, API docs, troubleshooting guide
   - Future-proofs the system (can maintain later)

### Plan Weaknesses / Risks ⚠️

1. **Aggressive Timeline for Solo Developer**
   - 6-8 weeks is tight for one person
   - Risk: Might take 10-12 weeks realistically
   - Mitigation: Focus on core features first, add nice-to-haves later

2. **Data Source Reliability Unknown**
   - Yahoo Finance may have rate limits or downtime
   - Alpha Vantage free tier is 5 calls/min (very limiting)
   - Mitigation: Test data sources early (Phase 1), have multiple backups

3. **1-Minute Timeframe Challenges**
   - Strategy spec acknowledges this is extremely difficult
   - Most professionals avoid 1-minute trading
   - Mitigation: Build flexibility to test on 5-min or 15-min bars

4. **No Broker API Research Yet**
   - Trading 212 may not have public API
   - May need to switch brokers for automation
   - Mitigation: Phase 7 includes API research, can pivot if needed

5. **Optimization Risk (Overfitting)**
   - Too much parameter tweaking can lead to curve-fitted results
   - Results look great in backtest, fail in live trading
   - Mitigation: Walk-forward analysis, out-of-sample testing, keep parameters simple

6. **User Discipline Not Addressed**
   - System can be perfect, but if user doesn't follow rules, will fail
   - Psychology is biggest factor in trading success
   - Mitigation: Paper trading emphasis, trade journaling, automated enforcement where possible

### Critical Assumptions to Validate Early

1. **Assumption**: Yahoo Finance provides reliable 1-minute intraday data
   - **Validation**: Test in Phase 1, Week 1
   - **Fallback**: Use Alpha Vantage or switch to 5-minute bars

2. **Assumption**: 2-of-3 consensus actually reduces false signals
   - **Validation**: Backtest in Phase 3, compare 1-of-3 vs 2-of-3 vs 3-of-3
   - **Fallback**: Adjust consensus requirement based on results

3. **Assumption**: Strategy has positive expectancy after friction
   - **Validation**: Backtest in Phase 3 with realistic spread/slippage
   - **Fallback**: If negative expectancy, try different timeframe or parameters

4. **Assumption**: RORO correlations are stable enough to trade
   - **Validation**: Analyze rolling correlation in Phase 8
   - **Fallback**: Add correlation strength filter, avoid trading when correlations break down

### Recommended Adjustments to Plan

#### Adjustment 1: Add Early Feasibility Check
**Insert before Phase 2**:
- **Task**: Quick feasibility backtest (simple version)
- **Goal**: Validate core concept works before investing more time
- **Method**: Simple ratio crossover backtest (without all bells and whistles)
- **Decision point**: If results terrible, pivot to different timeframe or strategy

#### Adjustment 2: Make Timeframe Configurable
**Throughout development**:
- Don't hardcode 1-minute bars
- Build system to work with any timeframe (1min, 5min, 15min, 1hour)
- Allows testing on multiple timeframes to find what works best

#### Adjustment 3: Prioritize Phase 3 (Backtesting)
**Rationale**:
- Can't validate strategy without backtesting
- Everything else (dashboard, alerts) is decoration if strategy doesn't work
- Consider doing "minimum viable backtest" even earlier (after Phase 1)

#### Adjustment 4: Add Monthly Review Checkpoints
**After each major milestone**:
- Week 2: Review data quality and signal generation
- Week 4: Review backtest results, decide if strategy viable
- Week 6: Review paper trading setup
- Week 8: Review full system, decide on paper trading start date

### Plan Assessment Summary

**Overall Grade**: 7.5/10

**What's Good**:
- Comprehensive coverage of all necessary components
- Realistic about risks and challenges
- Emphasizes testing and validation (critical for trading systems)
- Clear success criteria and go/no-go decision points

**What Could Be Better**:
- Timeline might be optimistic (8-10 weeks more realistic for solo dev)
- Could benefit from earlier feasibility check
- Data source reliability needs early validation
- User discipline/psychology aspects underdeveloped

**Key Risk**: Building a sophisticated system that looks professional but doesn't make money because the underlying strategy doesn't have edge in 1-minute timeframe.

**Mitigation**: Early and frequent backtesting, willingness to pivot to different timeframe (5-min, 15-min) if 1-minute proves unviable.

**Recommendation**: Proceed with plan, but:
1. Add early feasibility backtest (after Phase 1)
2. Build timeframe flexibility from the start
3. Be prepared for 10-12 week timeline (not 6-8)
4. Consider starting with 5-minute or 15-minute bars if 1-minute results disappointing

---

## Next Steps

1. **Review this plan with stakeholder** (you)
2. **Confirm timeline expectations** (6-8 weeks realistic? Or plan for longer?)
3. **Discuss timeframe flexibility** (willing to test 5-min/15-min if 1-min doesn't work?)
4. **Begin Phase 0** (project setup)
5. **Set up first checkpoint** (after Phase 1, review data quality)

**Ready to proceed when you are!**

---

*End of Development Plan*
