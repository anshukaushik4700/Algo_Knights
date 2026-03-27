## 🚀 STRATEGY #2 API AUTOMATION SETUP GUIDE

**Status:** Your strategy is now **FULLY API-AUTOMATED** ✅

---

## 📋 Project Structure

```
Strategy_02/
├── run_bot.py                    ← START HERE (main launcher)
├── paper_trading_dhan.py         ← Core bot with full API integration
├── setup_api.py                  ← API credential validator
├── requirements.txt              ← Install dependencies
├── .gitignore                    ← Ignore sensitive files
├── README.md                     ← Full documentation
├── SETUP_GUIDE.md               ← This file
├── paper_trades_*.csv           ← Auto-generated trade logs
├── live_candles_*.csv           ← Auto-generated candle data
└── paper_log_*.log              ← Auto-generated error logs
```

---

## ✅ Phase 1: PAPER TRADING (10 Days) - NO REAL MONEY

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run in Paper Trading Mode
```bash
python run_bot.py
```

✅ **That's it!** Your bot is now running with VIRTUAL money.

**What happens:**
- Bot wakes up at 9:30 AM IST
- Checks for signals every 5 minutes during market hours
- Places virtual trades on ATM puts (no real money)
- Exits trades based on SL/Target/Trailing SL
- Logs all trades to `paper_trades_*.csv`

### Step 3: Monitor Paper Trading

**Watch the logs:**
```bash
# Linux/Mac: 
tail -f paper_log_*.log

# Windows: Type the filename
```

**After each trading day, check:**
- ✅ How many signals were detected
- ✅ Win rate and average R-multiple
- ✅ Any errors or connection issues
- ✅ P&L performance

(Check `paper_trades_*.csv` for all details)

---

## 🔐 Phase 2: LIVE TRADING - After 10 Days Paper Validation

### When to Switch?

Only switch to live trading after:
- ✅ **10+ trades** executed in paper mode
- ✅ **40%+ win rate** consistently achieved
- ✅ **Avg R-Multiple ≥ 1.0x** (profit >= risk)
- ✅ **Verified signal accuracy** matches your notebook
- ✅ **Confident in strategy performance**

### Step 1: Buy Dhan API Key

1. Go to: https://login.dhan.co/
2. Complete KYC verification
3. Generate API credentials:
   - Client ID
   - Access Token
   - API Key

### Step 2: Set API Credentials

**Create `.env` file at ROOT (Algo_Knights/):**
```bash
cp .env.template .env
```

**Edit `.env` and add:**
```
DHAN_CLIENT_ID=your_client_id_here
DHAN_ACCESS_TOKEN=your_access_token_here
DHAN_API_KEY=your_api_key_here
PAPER_TRADING=True
```

**Save the file** (DO NOT commit to git!)

### Step 3: Validate API Connection

```bash
python setup_api.py
```

This will:
- ✅ Check credentials are set
- ✅ Test connection to Dhan API
- ✅ Verify NIFTY spot price access
- ✅ Confirm configuration is ready

### Step 4: Switch to Live Trading

Edit `.env` and change:
```
PAPER_TRADING=False
```

### Step 5: Start Live Trading

```bash
python run_bot.py
```

**Important:** The script will ask for confirmation before trading with real money.

---

## 🧭 Trading Flow

### What the Bot Does Every 5 Minutes:

1. **Fetch Data** - Gets latest 5-min candle via Dhan API
2. **Calculate Indicators** - EMA20 and EMA200
3. **Check Signals** - Verifies all entry conditions from your notebook
4. **Place Orders** - If signal found and conditions met:
   - Calculates Stop Loss (EMA20 + 5 points)
   - Calculates Target (SL - 2.5× risk)
   - Finds ATM PUT strike price
   - Places buy put order
5. **Manage Positions** - For open trades:
   - Checks if Stop Loss is hit → Exit
   - Checks if Target is hit → Exit
   - Activates Trailing SL at 1.5R profit
   - Logs all updates
6. **Force Exits** - At 2:45 PM closes any remaining positions

### Market Hours

- **9:30 AM** - Market opens, bot becomes active
- **2:45 PM** - Force exit all remaining positions
- **Weekends** - Bot waits, no signals generated

---

## 📊 Understanding the Logs

### `paper_trades_YYYY-MM-DD.csv`

```
trade_id,entry_price,sl,target,exit_price,nifty_pnl_pts,r_multiple,result,exit_reason
STR2_1,20450.50,20455.50,20434.12,20434.12,18.50,1.23,WIN,TARGET
STR2_2,20425.75,20430.75,20408.13,20430.75,-5.00,-0.33,LOSS,SL
```

**Columns:**
- `trade_id` - Unique trade identifier
- `entry_price` - NIFTY entry level
- `sl` - Stop loss level
- `target` - Profit target
- `exit_price` - Actual exit level
- `nifty_pnl_pts` - Profit/loss in points
- `r_multiple` - R-multiple (profit / risk)
- `result` - WIN or LOSS
- `exit_reason` - TARGET / SL / EOD / TRAIL_SL

### `paper_log_YYYY-MM-DD.log`

```
09:30:05 INFO 🚀 STARTUP — fetching historical data for EMA warmup …
09:30:12 INFO ✅ Warmup done — 1,250 bars loaded
09:35:10 INFO ⏰ Tick at 09:35:10
09:35:15 INFO 🟢 PAPER ENTRY #1
         Entry: 20450.50 | SL: 20455.50 | Target: 20434.12
09:45:20 INFO 🟢 WIN PAPER EXIT #1 (TARGET)
         NIFTY PnL: +18.50 pts | R: +1.23x
```

---

## 🔧 Configuration

### Strategy Parameters (in `paper_trading_dhan.py`):

```python
EMA_FAST        = 20      # Fast EMA for entry signal
EMA_SLOW        = 200     # Slow EMA for trend
SL_BUFFER       = 5       # Points above EMA20 for SL
RISK_REWARD     = 2.5     # Risk:Reward ratio
TRAIL_TRIGGER_R = 1.5     # Activate trailing at 1.5R
```

### Market Hours (in `paper_trading_dhan.py`):

```python
SESSION_START_H  = 9      # Entry window opens
SESSION_START_M  = 30
SESSION_END_H    = 14     # Session ends (force exit)
SESSION_END_M    = 45
```

---

## 🧪 Understanding Strategy Logic

Your Strategy_02 notebook logic is **100% preserved**:

| Aspect | Status |
|--------|--------|
| Signal Detection | ✅ SAME |
| EMA Calculations | ✅ SAME |
| Position Sizing | ✅ SAME |
| SL/Target Logic | ✅ SAME |
| Trailing SL | ✅ SAME |

**What changed:**
- ❌ Trading Logic: NO CHANGES
- ✅ Infrastructure: Added Dhan API integration
- ✅ Automation: Added scheduler for continuous operation
- ✅ Credentials: Added environment variable support

---

## 📈 30-Day Checklist

### Week 1 (Paper Trading)
- [ ] Installed dependencies
- [ ] Ran bot in paper mode
- [ ] Got 5+ signals
- [ ] Reviewed logs for accuracy
- [ ] Compared with notebook results

### Week 2-3 (Paper Trading)
- [ ] Got 10+ total signals
- [ ] Win rate >= 40%
- [ ] Avg R-Multiple >= 1.0x
- [ ] No major issues/errors
- [ ] Feels confident in strategy

### Week 4 (Preparation for Live)
- [ ] Bought Dhan API key
- [ ] Created `.env` file
- [ ] Verified API credentials
- [ ] Ran `setup_api.py` successfully
- [ ] All checks passing

### Day 31+ (Live Trading)
- [ ] Switched to live mode
- [ ] Got first live signal
- [ ] Order placed successfully
- [ ] Monitoring live trades
- [ ] Reviewing results daily

---

## ⚠️ Important Notes

### Before Going Live:
- ✅ Run 10+ days in paper trading mode
- ✅ Validate all signals match your notebook
- ✅ Achieve 40%+ win rate
- ✅ Review trailing SL logic
- ✅ Understand how to stop bot quickly (Ctrl+C)

### During Live Trading:
- 🔴 **NEVER leave bot unattended during market hours**
- 🔴 **Start with small position size**
- 🔴 **Monitor logs continuously**
- 🔴 **Have exit strategy ready**
- 🔴 **Don't overtrade**

### Risk Management:
- Max 1% per trade risk
- Fixed stop loss distance
- Automatic trailing stop loss
- Force exits at 2:45 PM
- No consecutive signal stacking

---

## 🎯 Advanced Usage

### Run as Scheduled Task (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9:25 AM (Mon-Fri)
4. Set action: Run program
   - Program: `python`
   - Arguments: `run_bot.py`
   - Directory: `C:\...\Strategy_02`

### Run in Background (Linux/Mac)

```bash
nohup python run_bot.py > strategy2_bot.log 2>&1 &
```

### Monitor with Separate Terminal

```bash
tail -f paper_log_*.log
```

---

## 🔗 Resources

- **Dhan Platform:** https://www.dhan.co
- **API Dashboard:** https://login.dhan.co
- **Market Status:** https://www.nseindia.com
- **NIFTY Data:** https://finance.yahoo.com (symbol: ^NSEI)

---

## ✅ Next Steps

1. **Right Now:**
   - [ ] `pip install -r requirements.txt`
   - [ ] `python run_bot.py`
   - [ ] Monitor for 10 days

2. **After 10 Days:**
   - [ ] Review paper trading results
   - [ ] If confident, proceed to live setup
   - [ ] Buy Dhan API key

3. **When API Key Ready:**
   - [ ] Create `.env` file
   - [ ] Add credentials
   - [ ] Run `setup_api.py` to validate
   - [ ] Switch to live trading

---

**Good luck with Strategy_02! 🎯📈**

For questions, check the logs: `paper_log_*.log`
