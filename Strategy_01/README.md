## NIFTY ATM Automated Trading Bot - API Edition

**Status:** ✅ **FULLY AUTOMATED WITH API SUPPORT**

### ⚡ Quick Start (Paper Trading Mode)

#### 1. Install dependencies:
```bash
pip install -r requirements.txt
```

#### 2. Run the bot:
```bash
python run_bot.py
```

**That's it!** The bot will start in **PAPER TRADING MODE** (virtual, no real money).

### 🔐 Setup for Live Trading (When you buy API key)

#### 1. Create `.env` file:
```bash
cp .env.example .env
```

#### 2. Add your Dhan API credentials to `.env`:
```
DHAN_CLIENT_ID=your_client_id
DHAN_ACCESS_TOKEN=your_access_token
DHAN_API_KEY=your_api_key
```

Get credentials from: https://www.dhan.co/settings/api-keys

#### 3. Validate setup:
```bash
python setup_api.py
```

#### 4. After 10 days of paper trading validation, switch to live:
Edit `.env` and change:
```
PAPER_TRADING=False
```

Then run:
```bash
python run_bot.py
```

### 📁 Files Overview

| File | Purpose |
|------|---------|
| `run_bot.py` | **START HERE** - Main production launcher |
| `nifty_atm_automation.py` | Core trading bot with full API integration |
| `test_paper_trading.py` | Backtest script (test with historical data) |
| `setup_api.py` | API credential validator & connection tester |
| `.env.example` | Configuration template |
| `requirements.txt` | All dependencies |
| `nifty_atm_trading.log` | Auto-generated trading log |

### 📊 Trading Modes Explained

#### 🟢 Paper Trading (Default - SAFE)
- Virtual trading with fake money
- No real capital at risk
- Perfect for testing strategy
- **Use this for first 10 days**
- Logs all trades for analysis

#### 🔴 Live Trading (After 10 days validation)
- Real market API connection
- REAL capital at risk
- Only enable after confident in strategy
- Requires valid Dhan API credentials
- **Use with extreme caution**

### 🎯 Strategy Details

- **Type:** Bearish EMA 20/200 Pullback
- **Timeframe:** 5-minute candles on NIFTY 50 Index (^NSEI)
- **Signal:** 5 conditions check (C1-C5)
- **Max Trades/Day:** 4
- **Risk:Reward:** 1:2.5
- **Stop Loss:** EMA20 + 1 point buffer
- **Trailing SL:** Activated at 1.5R profit
- **Killswitch:** After 2 consecutive SL losses

### 🔄 Trading Flow

1. **Data Collection** - Fetches 5-min candles every 5 minutes
2. **Signal Detection** - Checks all 5 entry conditions
3. **Order Placement** - Places order via Dhan API (or paper records it)
4. **Position Management** - Tracks SL, Target, Trailing SL
5. **Exit Management** - Auto-exits on SL/Target/Trailing SL/Time
6. **Logging** - All trades logged to `nifty_atm_trading.log`

### 🧪 Testing the Strategy

**Run backtest on historical data:**
```bash
python test_paper_trading.py
```

This will:
- Download 30 days of 5-min data
- Process through bot logic
- Show all trades and P&L
- Compare with your backtest results

### 🚀 Automation

The bot runs **24/7** but only trades during market hours:
- **9:15 AM** - Market opens, bot becomes active
- **2:30 PM** - No new entries (only manage existing positions)
- **3:15 PM** - Force exit all remaining positions
- **3:30 PM** - Market closes, bot sleeps

**To run as automatic task:**

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create task to run `python run_bot.py` at 9:10 AM daily (Mon-Fri)

**Linux/Mac (Crontab):**
```bash
10 9 * * 1-5 cd /path/to/Strategy_01 && python run_bot.py
```

### 📝 Logs & Monitoring

All trading activity goes to `nifty_atm_trading.log`:
```
2024-03-27 09:35:22 | INFO | 📊 SIGNAL DETECTED
2024-03-27 09:35:23 | INFO | ✅ ENTRY | Order: PAPER_1 | Entry: 20450.50 | SL: 20453.50 | Target: 20434.12
2024-03-27 14:45:10 | INFO | ✅ PAPER_1 CLOSED | Result: TARGET | Exit: 20434.12 | P&L: +16.38 | R: +1.36
```

### ⚙️ Configuration

Edit `nifty_atm_automation.py` or set in `.env`:

```python
# Strategy Parameters
EMA_FAST = 20          # Fast moving average
EMA_SLOW = 200         # Slow moving average
MAX_TRADES_DAY = 4     # Max entries per day
RR_RATIO = 2.5         # Risk:Reward ratio
KILLSWITCH_SL = 2      # Consecutive SL limit

# Market Hours (IST - Indian Standard Time)
SESSION_START = 09:30
ENTRY_CUTOFF = 14:30
FORCE_EXIT_TIME = 15:15
SESSION_END = 15:30
```

### 🔧 Troubleshooting

**"Dhan SDK not installed"**
```bash
pip install dhanhq
```

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**API connection fails**
- Check .env file has correct credentials
- Run: `python setup_api.py`
- Verify internet connection

**No signals detected**
- Check market hours (9:30 - 3:30 PM IST weekdays only)
- Run backtest: `python test_paper_trading.py`
- Check `nifty_atm_trading.log` for errors

### 📈 30-Day Paper Trading Validation Checklist

Before switching to live trading, validate:

- [ ] **10+ trades executed** in paper mode
- [ ] **Win rate >= 40%** consistently
- [ ] **Avg R-Multiple >= 1.0x** (profit at least equals risk)
- [ ] **No excessive SL hits** (check killswitch activations)
- [ ] **Logs confirm correct signal detection** (check nifty_atm_trading.log)
- [ ] **Time-based exits working** (force exit at 3:15 PM)
- [ ] **API connection stable** (if pre-testing with credentials)

### 🚨 Important Notes

⚠️ **Before using live trading:**
1. Paper trade for minimum 10 days
2. Validate all signals match your backtest
3. Understand how to stop the bot quickly
4. Start with small position size
5. Never leave bot unattended during market hours

⚠️ **Market hours only:**
- Bot runs 24/7 but trades only during IST market hours
- Weekend/holiday: Bot waits, logs "Market closed"

⚠️ **Killswitch feature:**
- Bot stops trading after 2 consecutive SL hits
- Prevents emotional over-trading
- Resets daily at 9:15 AM

### 📚 Support

1. **Check logs:** `nifty_atm_trading.log`
2. **Test strategy:** `python test_paper_trading.py`
3. **Validate setup:** `python setup_api.py`
4. **Read docs:** This README + `.env.example`

### 🎓 Next Steps

1. **Now:** Run bot in paper trading mode
2. **Day 3:** Check logs, validate signals match backtest
3. **Day 7:** Review trades, calculate win rate
4. **Day 10:** If confident, buy Dhan API key
5. **Day 11:** Setup credentials, move to live trading
6. **Day 15+:** Monitor live trades, adjust if needed

**Happy Trading! 📈**
