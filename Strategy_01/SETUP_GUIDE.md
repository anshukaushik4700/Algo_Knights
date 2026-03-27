## 🚀 API AUTOMATION SETUP GUIDE

**Status:** Your strategy is now **FULLY API-AUTOMATED** ✅

---

## 📋 Project Structure

```
Strategy_01/
├── run_bot.py                    ← START HERE (main launcher)
├── nifty_atm_automation.py       ← Core bot with full API integration
├── setup_api.py                  ← API credential validator
├── test_paper_trading.py         ← Backtest on historical data
├── requirements.txt              ← Install dependencies
├── .env.example                  ← Configuration template
├── .gitignore                    ← Ignore sensitive files
├── README.md                     ← Full documentation
├── nifty_atm_trading.log        ← Auto-generated trading log
└── SETUP_GUIDE.md               ← This file
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
- Bot checks for signals every 5 minutes during market hours (9:30 AM - 3:30 PM IST)
- Places virtual orders (no real money)
- Tracks P&L in paper mode
- Logs all trades to `nifty_atm_trading.log`

### Step 3: Monitor Paper Trading

**Watch the logs:**
```bash
# Linux/Mac: tail -f nifty_atm_trading.log
# Windows: Type nifty_atm_trading.log
```

**After each trading day, check:**
- ✅ How many signals were detected
- ✅ Win rate and average R-multiple
- ✅ Any errors or connection issues
- ✅ P&L performance

(Check `nifty_atm_trading.log` for all details)

### Step 4: Backtest Your Strategy (Optional)

Test on 30 days of historical data:
```bash
python test_paper_trading.py
```

This simulates your strategy on past market data and shows all trades + P&L.

---

## 🔐 Phase 2: LIVE TRADING - After 10 Days Paper Validation

### When to Switch?

Only switch to live trading after:
- ✅ **10+ trades** executed in paper mode
- ✅ **40%+ win rate** consistently achieved
- ✅ **Avg R-Multiple ≥ 1.0x** (profit >= risk)
- ✅ **Verified signal accuracy** matches your backtest
- ✅ **Confident in strategy performance**

### Step 1: Buy Dhan API Key

1. Go to: https://www.dhan.co/
2. Sign up and complete KYC
3. Go to: Settings > API Keys
4. Copy:
   - Client ID
   - Access Token
   - API Key

### Step 2: Set API Credentials

**Create `.env` file:**
```bash
cp .env.example .env
```

**Edit `.env` and add:**
```
DHAN_CLIENT_ID=your_client_id_here
DHAN_ACCESS_TOKEN=your_access_token_here
DHAN_API_KEY=your_api_key_here
```

**Save the file** (DO NOT commit to git!)

### Step 3: Validate API Connection

```bash
python setup_api.py
```

This will:
- ✅ Check if credentials are set
- ✅ Test connection to Dhan API
- ✅ Verify market data access
- ✅ Confirm configuration

### Step 4: Switch to Live Trading

Edit `.env` and change:
```
PAPER_TRADING=False
```

### Step 5: Start Live Trading

```bash
python run_bot.py
```

**Important:** The script will ask for confirmation before trading with real money. Type the exact phrase to confirm.

---

## 🧭 Trading Flow

### What the Bot Does Every 5 Minutes:

1. **Fetch Data** - Gets latest 5-min candle via Dhan API
2. **Calculate EMAs** - EMA20 and EMA200 from last 200 candles
3. **Check Signals** - Verifies all 5 entry conditions (C1-C5)
4. **Place Order** - If signal found and conditions met:
   - Calculates Stop Loss (EMA20 + 1 point)
   - Calculates Target (SL - 2.5× risk)
   - Places BUY PUT order via Dhan API
   - Records entry in paper engine
5. **Manage Positions** - For open trades:
   - Checks if Stop Loss is hit → Exit
   - Checks if Target is hit → Exit
   - Activates Trailing SL at 1.5R profit
   - Logs all updates
6. **Force Exits** - At 3:15 PM closes any remaining positions

### Market Hours

- **9:15 AM** - Market opens, bot becomes active
- **9:30 AM** - Entry window opens (can place new orders)
- **2:30 PM** - No new entries (manage existing only)
- **3:15 PM** - Force exit all remaining positions
- **3:30 PM** - Market closes, bot sleeps

### Killswitch

After 2 consecutive Stop Loss hits:
- ⛔ No more entries for the day
- Resets next day at 9:15 AM
- Prevents emotional over-trading

---

## 📊 Configuration

### Strategy Parameters (in `.env`):

```
EMA_FAST=20              # Fast EMA for entry signal
EMA_SLOW=200             # Slow EMA for trend
MAX_TRADES_DAY=4         # Max orders per trading day
RR_RATIO=2.5             # Risk:Reward ratio
KILLSWITCH_SL=2          # SL hits before stopping
SL_BUFFER=1.0            # Points above EMA20 for SL
TRAIL_TRIGGER_R=1.5      # Activate trailing at 1.5R profit
```

### Market Hours (in `.env`):

```
SESSION_START=09:30      # Entry window opens
ENTRY_CUTOFF=14:30       # No new entries after this
FORCE_EXIT_TIME=15:15    # Force close all positions
SESSION_END=15:30        # Market closes
```

---

## 🔧 Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Dhan SDK not installed"
```bash
pip install dhanhq
```

### "Can't connect to Dhan API"
1. Check internet connection
2. Verify credentials in `.env` are correct
3. Run: `python setup_api.py`
4. Check if Dhan API server is up (https://www.dhan.co)

### "No signals detected in paper trading"
1. Check market hours (9:30 AM - 3:30 PM IST, weekdays only)
2. Run backtest: `python test_paper_trading.py`
3. Check logs: `nifty_atm_trading.log`
4. Market may not have matching signals that day

### "Orders not placing in live mode"
1. Verify `.env` has PAPER_TRADING=False
2. Check Dhan API credentials
3. Verify you have confirmed "YES, TRADE LIVE"
4. Check account balance on Dhan platform
5. Check logs: `nifty_atm_trading.log`

---

## 📝 Logs

All activity logged to `nifty_atm_trading.log`:

```
2024-03-27 09:35:22 | INFO | 🚀 BOT STARTED | Mode: PAPER TRADING
2024-03-27 09:45:10 | INFO | 📊 SIGNAL DETECTED | C1:T C2:T C3:T C4:T C5:T
2024-03-27 09:45:11 | INFO | ✅ ENTRY | Order: PAPER_001 | Entry: 20450.50 | SL: 20453.50 | Target: 20434.12
2024-03-27 10:15:30 | INFO | ✅ PAPER_001 CLOSED | Result: TARGET | Exit: 20434.12 | P&L: +16.38 | R: +1.36
2024-03-27 15:15:00 | INFO | ⏰ Force exit time reached - closing all positions
```

**Check logs daily to:**
- Verify signals are being detected
- Confirm trades match your backtest
- Monitor P&L
- Identify any errors

---

## ⚠️ Important Notes

### Before Going Live:
- ✅ Run 10+ days in paper trading mode
- ✅ Validate all signals match your backtest
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
- Max 4 trades per day
- Fixed stop loss distance
- Automatic trailing stop loss
- Force exits at 3:15 PM
- Killswitch after 2 SL hits

---

## 🎯 30-Day Checklist

### Week 1 (Paper Trading)
- [ ] Installed dependencies
- [ ] Ran bot in paper mode
- [ ] Got 5+ signals
- [ ] Reviewed logs for accuracy
- [ ] Compared with backtest results

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
- [ ] Ran setup_api.py successfully
- [ ] All checks passing

### Day 31+ (Live Trading)
- [ ] Switched to live mode
- [ ] Got first live signal
- [ ] Order placed successfully
- [ ] Monitoring live trades
- [ ] Reviewing results daily

---

## 🚀 Advanced Usage

### Run as Scheduled Task (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9:10 AM (Mon-Fri)
4. Set action: Run program
   - Program: `python`
   - Arguments: `run_bot.py`
   - Directory: `C:\Users\hrpan\OneDrive\Desktop\Open-source\Algo_trade\Algo_Knights\Strategy_01`

### Run in Background (Linux/Mac)

```bash
nohup python run_bot.py > nifty_bot.log 2>&1 &
```

### Monitor with Separate Terminal

```bash
tail -f nifty_atm_trading.log
```

---

## 📈 Performance Monitoring

### Daily Check:
```bash
# Check number of trades
grep "ENTRY\|CLOSED" nifty_atm_trading.log | wc -l

# Check P&L
grep "P&L:" nifty_atm_trading.log | tail

# Check win rate
grep "CLOSED" nifty_atm_trading.log | grep "pnl:+" | wc -l
```

### Weekly Summary:
Review `nifty_atm_trading.log` for:
- Total signals per day
- Entry accuracy (do conditions match?)
- Win rate trend
- Average R-multiple
- Any error messages

---

## 🔗 Resources

- **Dhan Platform:** https://www.dhan.co
- **API Docs:** https://docs.dhan.co
- **Check Market Status:** https://www.nseindia.com
- **NIFTY 50 Data:** https://finance.yahoo.com (symbol: ^NSEI)

---

## ✅ Next Steps

1. **Right Now:**
   - [ ] Install dependencies: `pip install -r requirements.txt`
   - [ ] Run bot: `python run_bot.py`
   - [ ] Monitor for 10 days

2. **After 10 Days:**
   - [ ] Review paper trading results
   - [ ] If confident, proceed to live setup
   - [ ] Buy Dhan API key

3. **When API Key Ready:**
   - [ ] Create `.env` file
   - [ ] Add credentials
   - [ ] Run `setup_api.py` to validate
   - [ ] Switch to live mode
   - [ ] Start live trading

---

**Good luck with your automated trading! 🎯📈**

For questions, check the logs: `nifty_atm_trading.log`
