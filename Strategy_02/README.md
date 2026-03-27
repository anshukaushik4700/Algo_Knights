## Strategy #2 - NIFTY Buy-Put EMA Pullback Automation

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

### 🔐 Setup for Live Trading (When API Key Ready)

#### 1. Create `.env` at ROOT folder (Algo_Knights/):
```bash
cp .env.template .env
```

#### 2. Add your Dhan API credentials to `.env`:
```
DHAN_CLIENT_ID=your_client_id
DHAN_ACCESS_TOKEN=your_access_token
DHAN_API_KEY=your_api_key
PAPER_TRADING=True
```

Get credentials from: https://login.dhan.co

#### 3. Validate setup:
```bash
python setup_api.py
```

#### 4. Run the bot:
```bash
python run_bot.py
```

### 📁 Files Overview

| File | Purpose |
|------|---------|
| `run_bot.py` | **START HERE** - Main production launcher |
| `paper_trading_dhan.py` | Core trading bot with full API integration |
| `setup_api.py` | API credential validator & connection tester |
| `requirements.txt` | All dependencies |
| `README.md` | This file |
| `paper_trades_*.csv` | Auto-generated trade logs |
| `live_candles_*.csv` | Auto-generated candle logs |
| `paper_log_*.log` | Auto-generated detailed logs |

### 📊 Strategy Details

- **Type:** Bearish EMA 20/200 Pullback
- **Timeframe:** 5-minute candles on NIFTY 50 Index (^NSEI)
- **Instrument:** ATM Put Options (Buy Put = Bearish)
- **Max Capital Risk:** 1% per trade
- **Risk:Reward:** 2.5:1
- **Stop Loss:** EMA20 + 5 points
- **Trailing SL:** Activated at 1.5R profit

### 🔄 Trading Flow

1. **Startup** - Fetches 6 days of historical 5-min data for EMA warmup
2. **Every 5 Minutes** - Checks for entry signals during market hours
3. **Signal Detection** - Verifies all conditions match strategy rules
4. **Trade Entry** - Places buy put order on ATM strike
5. **Position Management** - Tracks SL, Target, Trailing SL
6. **Exit Management** - Auto-exits on SL/Target/Trailing SL/Time
7. **Logging** - Logs all trades to CSV for analysis

### ⏰ Trading Hours

- **9:30 AM** - Market opens, bot becomes active
- **2:45 PM** - Session ends (force exit all positions)
- **Weekends** - Bot waits (no signals generated)

### 📝 Logs & Monitoring

All trading activity goes to CSV files:

**`paper_trades_YYYY-MM-DD.csv`** - Trade-by-trade results
```
trade_id, entry_price, sl, target, exit_price, pnl, r_multiple, result
```

**`live_candles_YYYY-MM-DD.csv`** - 5-min candle data
```
timestamp, open, high, low, close, ema20, ema200
```

**`paper_log_YYYY-MM-DD.log`** - Detailed event log
```
09:30:05 | INFO | 🚀 STARTUP — fetching historical data
09:35:10 | INFO | 🟢 PAPER ENTRY | NIFTY: 20450.50 | SL: 20455.50
09:45:20 | INFO | 🟢 WIN PAPER EXIT | NIFTY PnL: +18.50 pts
```

### ⚙️ Configuration

All parameters are in `paper_trading_dhan.py`:

```python
# Strategy Parameters
EMA_FAST         = 20      # Fast EMA
EMA_SLOW         = 200     # Slow EMA
SL_BUFFER        = 5       # Points above EMA20 for SL
RISK_REWARD      = 2.5     # Risk:Reward ratio
TRAIL_TRIGGER_R  = 1.5     # Start trailing at 1.5R profit

# Trading Capital
CAPITAL          = 100_000 # Virtual capital
RISK_PCT         = 0.01    # 1% risk per trade

# Market Hours
SESSION_START_H  = 9       # 9:30 AM
SESSION_START_M  = 30
SESSION_END_H    = 14      # 2:45 PM
SESSION_END_M    = 45
```

### 🧪 How to Use

**Day 1: Setup**
```bash
pip install -r requirements.txt
python run_bot.py
```

**Days 2-10: Paper Trading**
- Monitor logs and CSV files daily
- Verify signals match your backtest
- Calculate win rate and R-multiple

**Day 11+: After API Key Ready**
- Add credentials to `.env`
- Run `python setup_api.py` to validate
- Switch to live trading

### 🔧 Troubleshooting

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"Dhan SDK not installed"**
```bash
pip install dhanhq
```

**"Credentials not configured"**
- Create `.env` at root: `Algo_Knights/.env`
- Add DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN
- Run: `python setup_api.py`

**No trades in logs**
- Check market hours (9:30 AM - 2:45 PM IST, weekdays only)
- Check `paper_log_*.log` for signal detection messages
- Verify historical data fetched successfully at startup

### 📈 Daily Checklist

After each trading day:
- [ ] Check `paper_trades_*.csv` for all trades
- [ ] Calculate win rate (wins / total trades)
- [ ] Check average R-multiple
- [ ] Verify no errors in `paper_log_*.log`
- [ ] Confirm option premiums were fetched (if live API)

### 🚨 Important Notes

⚠️ **Strategy Logic:**
- All entry/exit conditions from your notebook are PRESERVED
- Only infrastructure and Dhan API integration added
- NO changes to trading logic

⚠️ **Paper Trading:**
- Virtual positions only (no real money)
- Perfect for 10-day validation period
- Start with this before moving to live

⚠️ **Live Trading:**
- Only after 10 days of paper trading
- Requires valid Dhan API credentials
- Real capital at risk!

### 📚 Support

1. **Check logs:** `paper_log_*.log`
2. **Validate setup:** `python setup_api.py`
3. **Review trades:** `paper_trades_*.csv`
4. **Read docs:** This README

### 🎯 Next Steps

1. **Right Now:**
   - `pip install -r requirements.txt`
   - `python run_bot.py`
   - Monitor for 10 days

2. **After 10 Days:**
   - Review paper trading results
   - If confident, buy Dhan API key

3. **When API Key Ready:**
   - Create `.env` at root
   - Add credentials
   - Run `setup_api.py` to validate
   - Start live trading

**Happy Trading! 📈**
