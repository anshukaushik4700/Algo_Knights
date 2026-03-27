═══════════════════════════════════════════════════════════════════════════════
                    PAPER TRADING TEST — COMPLETE GUIDE
═══════════════════════════════════════════════════════════════════════════════

This guide walks you through testing the automation with PAPER TRADING
(simulated trades, no real broker connection, no money at risk)

Expected time to complete: 30-45 minutes


═══════════════════════════════════════════════════════════════════════════════
STEP 1: VERIFY PYTHON & DEPENDENCIES (5 minutes)
═══════════════════════════════════════════════════════════════════════════════

✅ CHECK 1: Python is installed
   Open PowerShell and run:
   
   python --version
   
   Expected output:
   Python 3.8 or higher (e.g., Python 3.10.5)
   
   If not installed:
   Download from https://www.python.org/downloads/
   ⚠️ Check "Add Python to PATH" during install

✅ CHECK 2: Required libraries exist
   Run in PowerShell:
   
   pip list | findstr -E "pandas|numpy|pytz|yfinance"
   
   You should see:
   • pandas
   • numpy  
   • pytz
   • yfinance
   
   If any are missing, install them:
   pip install pandas numpy pytz yfinance


═══════════════════════════════════════════════════════════════════════════════
STEP 2: VERIFY BOT CONFIGURATION (5 minutes)
═══════════════════════════════════════════════════════════════════════════════

✅ CHECK 1: Open the bot file
   In VS Code, open: nifty_atm_automation.py
   
✅ CHECK 2: Verify PAPER_TRADING = True
   Scroll to line ~79, find:
   
   PAPER_TRADING   = True             # ← Must be True
   
   This ensures:
   • No real orders placed
   • No Dhan connection needed
   • Trades simulated in memory
   • Safe to test anything

✅ CHECK 3: Verify other key settings
   Search for the Config class and verify:
   
   DHAN_CLIENT_ID = ""              # Can be blank (not needed for paper)
   DHAN_ACCESS_TOKEN = ""           # Can be blank
   DHAN_API_KEY = ""                # Can be blank
   
   INITIAL_BALANCE = 100000         # Virtual balance for testing
   MAX_TRADES_DAY = 4               # Max 4 trades per day
   EMA_FAST = 20                    # EMA parameters
   EMA_SLOW = 200
   
   These match your backtest ✓


═══════════════════════════════════════════════════════════════════════════════
STEP 3: CREATE TEST DATA FEEDER (10 minutes)
═══════════════════════════════════════════════════════════════════════════════

The bot normally waits for live market data.
For testing, we'll create a TEST FILE that feeds historical data.

✅ CREATE: test_paper_trading.py

Copy this code into a NEW FILE named: test_paper_trading.py

─────────────────────────────────────────────────────────────────────────────
"""
TEST SCRIPT: Feed historical candles to paper trading bot
This simulates real market data for testing
"""

import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
from nifty_atm_automation import TradingBot, Config

def test_paper_trading():
    """
    Run bot with simulated candle data.
    Uses recent historical data to trigger signals.
    """
    print("=" * 80)
    print("🧪 PAPER TRADING TEST — HISTORICAL DATA REPLAY")
    print("=" * 80)
    
    # Initialize bot
    bot = TradingBot()
    
    # Fetch recent 5-min data (last 5 days)
    print("\n📊 Fetching historical data for simulation...")
    df_raw = yf.download(
        Config.SYMBOL,
        interval="5m",
        period="5d",
        auto_adjust=True,
        progress=False
    )
    
    if isinstance(df_raw.columns, pd.MultiIndex):
        df_raw.columns = df_raw.columns.get_level_values(0)
    
    if df_raw.index.tzinfo is None:
        df_raw = df_raw.tz_localize("UTC")
    df_raw = df_raw.tz_convert(Config.IST)
    
    # Filter to market session only
    df_raw = df_raw.between_time("09:15", "15:30")
    df_raw.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
    
    print(f"✅ Downloaded {len(df_raw)} candles")
    print(f"   Date range: {df_raw.index[0]} → {df_raw.index[-1]}")
    
    # Feed candles to bot one by one
    print("\n🔄 Feeding candles to bot (this may take 1-2 minutes)...\n")
    
    for idx, (ts, row) in enumerate(df_raw.iterrows()):
        candle = {
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'timestamp': ts
        }
        
        # Call bot's candle processor
        bot.on_new_candle(candle)
        
        # Print progress every 50 candles
        if (idx + 1) % 50 == 0:
            print(f"   Processed {idx + 1}/{len(df_raw)} candles...")
    
    print(f"\n✅ Simulation complete!")
    
    # Print final results
    print("\n" + "=" * 80)
    print("📊 PAPER TRADING RESULTS")
    print("=" * 80)
    
    summary = bot.paper_engine.get_summary()
    
    if summary:
        print(f"\nTrades Executed:  {summary['total_trades']}")
        print(f"Wins:             {summary['wins']}")
        print(f"Losses:           {summary['losses']}")
        print(f"Win Rate:         {summary['win_rate']:.1f}%")
        print(f"Total P&L:        {summary['total_pnl']:+.1f} points")
        print(f"Avg R-Multiple:   {summary['avg_r']:+.2f}")
        print(f"Final Balance:    {summary['balance']:+.0f} points")
    else:
        print("\n⚠️  No trades executed (not enough signals in data)")
    
    print("\n" + "=" * 80)
    
    # Print trade log
    if bot.paper_engine.trades_log:
        print("\n📝 DETAILED TRADE LOG:")
        print("─" * 80)
        
        for i, trade in enumerate(bot.paper_engine.trades_log, 1):
            print(f"\nTrade #{i}")
            print(f"  Entry:     {trade['entry_price']:.2f}")
            print(f"  SL:        {trade['sl']:.2f}")
            print(f"  Target:    {trade['target']:.2f}")
            print(f"  Exit:      {trade['exit_price']:.2f}")
            print(f"  P&L:       {trade['pnl']:+.2f} points")
            print(f"  R-Mul:     {trade['r_multiple']:+.2f}x")
            print(f"  Result:    {trade['result']}")
            print(f"  Duration:  {(trade['exit_time'] - trade['entry_time']).total_seconds() / 60:.0f} min")
    else:
        print("\n⚠️  No trades logged")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    test_paper_trading()
─────────────────────────────────────────────────────────────────────────────

✅ SAVE THIS FILE
   • Name: test_paper_trading.py
   • Location: Same folder as nifty_atm_automation.py


═══════════════════════════════════════════════════════════════════════════════
STEP 4: RUN THE PAPER TRADING TEST (5 minutes)
═══════════════════════════════════════════════════════════════════════════════

✅ OPEN POWERSHELL
   • Navigate to your bot folder:
   
   cd "C:\Users\hrpan\OneDrive\Desktop\Open-source\Algo_hi_kehde"

✅ RUN THE TEST
   Execute:
   
   python test_paper_trading.py
   
   You'll see:
   
   ════════════════════════════════════════════════════════════════════════════
   🧪 PAPER TRADING TEST — HISTORICAL DATA REPLAY
   ════════════════════════════════════════════════════════════════════════════
   
   📊 Fetching historical data for simulation...
   ✅ Downloaded 500 candles
      Date range: 2026-03-10 09:30:00+05:30 → 2026-03-15 15:30:00+05:30
   
   🔄 Feeding candles to bot (this may take 1-2 minutes)...
   
      Processed 50/500 candles...
      Processed 100/500 candles...
      ...
   
   ✅ Simulation complete!
   
   ════════════════════════════════════════════════════════════════════════════
   📊 PAPER TRADING RESULTS
   ════════════════════════════════════════════════════════════════════════════
   
   Trades Executed:  6
   Wins:             4
   Losses:           2
   Win Rate:         66.7%
   Total P&L:        +45.3 points
   Avg R-Multiple:   +0.87x
   Final Balance:    +45 points
   
   ════════════════════════════════════════════════════════════════════════════

✅ IF THIS WORKS, you're ready for next steps!


═══════════════════════════════════════════════════════════════════════════════
STEP 5: VALIDATE THE RESULTS (10 minutes)
═══════════════════════════════════════════════════════════════════════════════

After running test_paper_trading.py, check:

✅ CHECK 1: Signals were detected
   Look for in console output or check: nifty_atm_trading.log
   
   Search for: "SIGNAL DETECTED"
   
   You should see entries like:
   2026-03-15 10:45:23 | INFO | 📊 SIGNAL DETECTED | C1:True C2:True C3:True C4:True C5:True

✅ CHECK 2: Orders were placed
   Look for: "ENTRY |"
   
   You should see:
   2026-03-15 10:45:23 | INFO | ✅ ENTRY | Order: PAPER_1 | Entry: 20100.50 | SL: 20115.75 | Target: 19937.38 | Risk: 15.25

✅ CHECK 3: Positions were closed
   Look for: "CLOSED |"
   
   You should see:
   2026-03-15 11:15:45 | INFO | ✅ PAPER_1 CLOSED | Result: TARGET | Exit: 19937.38 | P&L: +163.12 pts | R: +10.68 | Balance: +163

✅ CHECK 4: Numbers match your backtest
   Compare the test results with your original backtest results:
   
   nifty_buy_put_backtest.ipynb output
   
   Metrics to compare:
   • Win rate (should be similar)
   • Total P&L (direction should match)
   • Avg R-Multiple (should be close)
   • Types of exits (TARGET, SL, TRAIL_SL, TIME_EXIT)
   
   The numbers may differ slightly due to:
   • Different time period
   • Slippage simulation
   • But the PATTERN should match

✅ CHECK 5: Log file created
   Open: nifty_atm_trading.log
   
   Should contain:
   • All signals detected
   • All orders placed
   • All exits
   • All P&L calculations
   • No ERROR lines (unless expected)


═══════════════════════════════════════════════════════════════════════════════
STEP 6: TEST EDGE CASES (10 minutes)
═══════════════════════════════════════════════════════════════════════════════

Now test specific scenarios to ensure robustness:

✅ TEST 1: Killswitch activation
   Edit: nifty_atm_automation.py
   Change: KILLSWITCH_SL = 2  →  KILLSWITCH_SL = 1 (lower for faster trigger)
   
   Run: python test_paper_trading.py
   
   Look for: "KILLSWITCH ACTIVATED" in logs
   Verify: No more trades placed after 1 consecutive SL

✅ TEST 2: Max trades per day
   Edit: nifty_atm_automation.py
   Change: MAX_TRADES_DAY = 4  →  MAX_TRADES_DAY = 1
   
   Run: python test_paper_trading.py
   
   Look for: "Daily trade limit" warning
   Verify: Only 1 trade per day, others rejected

✅ TEST 3: Entry cutoff time
   Edit: nifty_atm_automation.py
   Change: ENTRY_CUTOFF = time(14, 30)  →  time(12, 0)  (earlier cutoff)
   
   Run: python test_paper_trading.py
   
   Verify: Trades only up to 12 PM, not after


═══════════════════════════════════════════════════════════════════════════════
STEP 7: RUN EXTENDED TEST (Optional, 30+ minutes)
═══════════════════════════════════════════════════════════════════════════════

To test with MORE data and longer timeframe:

✅ MODIFY test_paper_trading.py

Change this line:
   period="5d",  # 5 days
   
To:
   period="30d",  # 30 days (more trades, better statistics)

Then run:
   python test_paper_trading.py
   
This will:
• Test more trading days
• Generate more statistics
• Show consistency over longer period
• Better validate strategy quality


═══════════════════════════════════════════════════════════════════════════════
STEP 8: DOCUMENT YOUR FINDINGS (5 minutes)
═══════════════════════════════════════════════════════════════════════════════

Create a file: PAPER_TRADING_TEST_RESULTS.txt

Record:
─────────────────────────────────────────────────────────────────────────────
DATE: March 15, 2026
ENVIRONMENT: Paper Trading (Simulated)
DATA PERIOD: Last 5 days
TRADES: 6
WIN RATE: 66.7%
TOTAL P&L: +45.3 points
BALANCE: +45 points

OBSERVATIONS:
□ All signals generated correctly
□ SL levels calculated properly
□ Target levels calculated properly  
□ Trailing SL working
□ Killswitch triggered (if applicable)
□ Time exits working
□ No errors in logs

ISSUES FOUND:
□ None (or list any)

STATUS:
✅ READY FOR LIVE DHAN API INTEGRATION
─────────────────────────────────────────────────────────────────────────────


═══════════════════════════════════════════════════════════════════════════════
TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

ISSUE: "ModuleNotFoundError: No module named 'nifty_atm_automation'"
FIX:
   • Verify test_paper_trading.py is in SAME folder as nifty_atm_automation.py
   • Verify you're running from the correct directory
   • Command should be in the folder: cd "C:\Users\hrpan\OneDrive\Desktop\Open-source\Algo_hi_kehde"

ISSUE: "No trades executed (not enough signals in data)"
FIX:
   • Signals depend on market conditions
   • Try with longer period: change period="5d" to period="30d"
   • Or check if your backtest found signals in the same period
   • It's normal if some periods have fewer signals

ISSUE: "KeyError: 'Timestamp'" or "TypeError"
FIX:
   • Make sure nifty_atm_automation.py is in the same folder
   • Make sure you're running from correct directory
   • Check Python version: python --version (should be 3.8+)

ISSUE: "nifty_atm_trading.log not created"
FIX:
   • Check you have write permissions in folder
   • Logger will create file automatically on first log
   • Check console output for actual logs


═══════════════════════════════════════════════════════════════════════════════
SUMMARY: TESTING CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Complete these steps in order:

□ STEP 1: Verify Python & dependencies (5 min)
□ STEP 2: Verify bot configuration (5 min)
□ STEP 3: Create test data feeder (10 min)
□ STEP 4: Run the test (5 min)
□ STEP 5: Validate results (10 min)
□ STEP 6: Test edge cases (10 min)
□ STEP 7: Run extended test [OPTIONAL] (30+ min)
□ STEP 8: Document findings (5 min)

TOTAL TIME: 50 minutes (without optional extended test)


═══════════════════════════════════════════════════════════════════════════════
WHAT'S NEXT AFTER PAPER TRADING TESTS PASS?
═══════════════════════════════════════════════════════════════════════════════

Once you've validated paper trading is working:

1. Keep test file running overnight (optional)
   • Verify bot doesn't crash
   • Check logs for errors

2. Compare with your original backtest
   • Should see similar win rates
   • Should see similar P&L patterns
   • Should see same trade types

3. Move to Dhan API integration
   • Follow ATM_SETUP_GUIDE.md
   • Implement 4 DhanBroker methods
   • Test with real data (but still paper trading on Dhan)

4. Go live
   • Set PAPER_TRADING = False
   • Monitor carefully


═══════════════════════════════════════════════════════════════════════════════
