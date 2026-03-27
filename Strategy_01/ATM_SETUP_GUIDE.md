═══════════════════════════════════════════════════════════════════════════════
NIFTY 50 ATM BOT — SETUP & DHAN API INTEGRATION GUIDE
═══════════════════════════════════════════════════════════════════════════════

📋 TABLE OF CONTENTS:
1. What Changed From Backtest → Automation
2. Core Components Explained
3. Dhan API Integration Steps
4. How to Run the Bot
5. Testing & Validation
6. Troubleshooting


═══════════════════════════════════════════════════════════════════════════════
1. WHAT CHANGED FROM BACKTEST → AUTOMATION
═══════════════════════════════════════════════════════════════════════════════

YOUR BACKTEST (nifty_buy_put_backtest.ipynb):
├─ 📦 Batch-processes 60 days of historical data
├─ 🔍 Tests strategy on PAST candles
├─ ✅ Shows if strategy would have worked
└─ 📊 Generates performance reports

↓ TRANSFORMED INTO ↓

AUTOMATION (nifty_atm_automation.py):
├─ 🔴 Connects to LIVE market data feed
├─ 📍 Waits for real candles to close
├─ 🎯 Generates signals in REAL-TIME
├─ 📤 Places ACTUAL orders on broker
├─ 🔄 Manages positions until exit
└─ 💾 Logs every trade & P&L


KEY CHANGES IN DETAIL:
─────────────────────────────────────────────────────────────────────────────

1️⃣  DATA SOURCE
   BEFORE: yf.download() — Historical batch data
   AFTER:  Dhan API        — Live 5-minute candles, one at a time
   
   Impact: Instead of processing all 60 days at once,
           the bot now listens for each candle as it closes.

2️⃣  ENTRY LOGIC
   BEFORE: Check signal once per candle in backtest loop
   AFTER:  Check signal when candle closes, enter immediately if conditions met
   
   Impact: Real-time decision making vs historical analysis

3️⃣  ORDER PLACEMENT
   BEFORE: Virtual entry in memory, manually tracked
   AFTER:  Sends actual PUT orders to Dhan broker
   
   Impact: Orders appear in your trading account

4️⃣  POSITION MANAGEMENT
   BEFORE: Check SL/Target against historical data
   AFTER:  Monitor SL/Target tick-by-tick with live price updates
   
   Impact: Exits happen the MOMENT price hits SL/Target

5️⃣  TRADE LOGGING
   BEFORE: Results stored in Python dataframe
   AFTER:  Logged to file + database for audit trail
   
   Impact: Full compliance & trade history


═══════════════════════════════════════════════════════════════════════════════
2. CORE COMPONENTS EXPLAINED
═══════════════════════════════════════════════════════════════════════════════

┌─ DataManager ────────────────────────────────────┐
│ Purpose: Maintains rolling buffer of last 250    │
│          5-minute candles in memory              │
│                                                  │
│ Key Methods:                                     │
│  • add_candle()      → New candle received       │
│  • _rebuild_dataframe() → Update indicators      │
│  • has_enough_data() → Check if ready for trade  │
│                                                  │
│ Why: EMAs need historical data (20 & 200 period)│
│      Can't calculate EMA200 with only 1 candle  │
└──────────────────────────────────────────────────┘

┌─ SignalGenerator ────────────────────────────────┐
│ Purpose: Detects the 5 entry conditions (C1-C5)  │
│                                                  │
│ Key Methods:                                     │
│  • check_signal()       → Is entry signal valid? │
│  • _check_pullback_validity() → Verify C5       │
│                                                  │
│ Logic: IDENTICAL to your backtest, but runs     │
│        on live data instead of historical       │
└──────────────────────────────────────────────────┘

┌─ PaperTradingEngine ─────────────────────────────┐
│ Purpose: In-memory order management              │
│          Tracks positions until exit             │
│          Calculates P&L                          │
│                                                  │
│ Key Methods:                                     │
│  • create_order()      → Open new position       │
│  • update_position()   → Update SL/Target/Trail  │
│  • force_exit_all()    → Close at session end    │
│  • get_summary()       → P&L summary             │
│                                                  │
│ Why: Useful for backtesting/paper trading        │
│      Later replaced by DhanBroker for live       │
└──────────────────────────────────────────────────┘

┌─ DhanBroker ─────────────────────────────────────┐
│ Purpose: Template for Dhan API integration       │
│          (Will be filled in when you add API)    │
│                                                  │
│ Key Methods (TO BE IMPLEMENTED):                 │
│  • get_live_candle()   → Fetch latest 5min data │
│  • place_order()       → Send order to Dhan      │
│  • cancel_order()      → Cancel order            │
│  • get_position()      → Check position status   │
│                                                  │
│ Why: Separates broker logic from trading logic  │
│      Easy to switch to different broker later    │
└──────────────────────────────────────────────────┘

┌─ TradingBot ─────────────────────────────────────┐
│ Purpose: Main orchestrator that ties everything  │
│          together and runs the continuous loop   │
│                                                  │
│ Key Methods:                                     │
│  • on_new_candle()  → Called when candle closes │
│  • run_live_loop()  → Main loop (runs forever)   │
│  • _fetch_candle()  → Get data from Dhan API    │
│                                                  │
│ Flow:                                            │
│  1. Wait 5 minutes                               │
│  2. Fetch new candle from Dhan                   │
│  3. Add to rolling buffer                        │
│  4. Check signals                                │
│  5. Manage open positions                        │
│  6. Place orders if signal triggered             │
│  7. Log results                                  │
│  8. Repeat                                       │
└──────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
3. DHAN API INTEGRATION STEPS (DETAILED)
═══════════════════════════════════════════════════════════════════════════════

PHASE A: SETUP (One-time, takes 15 minutes)
──────────────────────────────────────────────────────────────────────────────

✅ STEP 1: Create Dhan Account
   • Visit: https://www.dhan.co/
   • Sign up with PAN + Aadhar
   • Complete KYC verification
   • Link bank account

✅ STEP 2: Get API Credentials
   • Login to Dhan platform
   • Go to: Developer → API Credentials
   • Copy these 3 values:
     - Client ID (your account identifier)
     - Access Token (session auth token)
     - API Key (for API requests)
   
   ⚠️  NEVER commit these to git! Keep them SECRET!

✅ STEP 3: Create Environment File (.env)
   • In your project folder, create file: .env
   • Add these lines:
   
   ─────────────────────────────────────
   DHAN_CLIENT_ID=your_client_id_here
   DHAN_ACCESS_TOKEN=your_access_token_here
   DHAN_API_KEY=your_api_key_here
   ─────────────────────────────────────
   
   • Add to .gitignore so it's never uploaded

✅ STEP 4: Install Dhan Python SDK
   • Open terminal in your project folder
   • Run: pip install dhanhq
   
   This installs the official Python library for Dhan API


PHASE B: CODE INTEGRATION (Add Dhan API calls)
──────────────────────────────────────────────────────────────────────────────

You'll modify 4 key methods in DhanBroker class:

┌─────────────────────────────────────────────────────────────────┐
│ METHOD 1: __init__() — Connect to Dhan                          │
├─────────────────────────────────────────────────────────────────┤
│ CURRENT CODE:                                                   │
│   def __init__(self, client_id, access_token, api_key):        │
│       # from dhan import DhanClient                            │
│       # self.client = DhanClient(...)                          │
│                                                                 │
│ REPLACE WITH:                                                   │
│   def __init__(self, client_id, access_token, api_key):        │
│       from dhanhq import DhanClient                            │
│       self.client = DhanClient(client_id, access_token)        │
│       self.api_key = api_key                                   │
│       self.is_connected = True                                  │
│       logger.info("✅ Connected to Dhan API")                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ METHOD 2: get_live_candle() — Fetch 5min data                  │
├─────────────────────────────────────────────────────────────────┤
│ CURRENT: Returns None                                           │
│ REPLACE WITH:                                                   │
│                                                                 │
│ def get_live_candle(self):                                     │
│     """Fetch latest 5-min candle from Dhan."""                 │
│     try:                                                        │
│         # Get historical data (last 100 candles)               │
│         response = self.client.historical_candle(              │
│             security_id="NIFTY 50",                            │
│             exchange_token="NSE",                              │
│             interval="FiveMin",                                │
│             from_date=(today - 1day),  # Yesterday            │
│             to_date=today               # Today               │
│         )                                                       │
│                                                                 │
│         latest = response[-1]  # Get most recent candle        │
│                                                                 │
│         return {                                                │
│             'open': float(latest['open']),                     │
│             'high': float(latest['high']),                     │
│             'low': float(latest['low']),                       │
│             'close': float(latest['close']),                   │
│             'timestamp': latest['timestamp']                   │
│         }                                                       │
│     except Exception as e:                                     │
│         logger.error(f"Failed to fetch candle: {e}")           │
│         return None                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ METHOD 3: place_order() — Submit PUT order                      │
├─────────────────────────────────────────────────────────────────┤
│ def place_order(self, symbol, qty, side, price, order_type):  │
│     """Place PUT order on Dhan."""                             │
│     try:                                                        │
│         # For Nifty PUT options                                │
│         response = self.client.place_order(                    │
│             symbol="NIFTYPUT",           # Put option          │
│             qty=qty,                     # Lot size            │
│             side=side,                   # BUY/SELL            │
│             price=price,                 # Strike level        │
│             order_type=order_type,       # LIMIT/MARKET        │
│             product_type="MIS",          # Intraday            │
│             transaction_type="BUY"       # Always buy PUTs      │
│         )                                                       │
│                                                                 │
│         order_id = response['order_id']                        │
│         logger.info(f"✅ Order placed: {order_id}")            │
│         return order_id                                        │
│                                                                 │
│     except Exception as e:                                     │
│         logger.error(f"Order failed: {e}")                     │
│         return None                                             │
│                                                                 │
│ IMPORTANT: ATM (At The Money) means:                           │
│   • Strike price closest to current Nifty level               │
│   • Auto-calculated based on latest spot price                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ METHOD 4: cancel_order() & get_position()                       │
├─────────────────────────────────────────────────────────────────┤
│ def cancel_order(self, order_id):                              │
│     """Cancel an open order."""                                │
│     try:                                                        │
│         response = self.client.cancel_order(order_id)          │
│         logger.info(f"Cancel order: {order_id}")               │
│         return response['status'] == 'cancelled'               │
│     except Exception as e:                                     │
│         logger.error(f"Cancel failed: {e}")                    │
│         return False                                            │
│                                                                 │
│ def get_position(self, symbol):                                │
│     """Check position status."""                               │
│     try:                                                        │
│         positions = self.client.get_positions()                │
│         for pos in positions:                                  │
│             if pos['symbol'] == symbol:                        │
│                 return {                                       │
│                     'qty': pos['net_qty'],                     │
│                     'ltp': pos['ltp'],                         │
│                     'pnl': pos['pnl']                          │
│                 }                                              │
│         return None                                             │
│     except Exception as e:                                     │
│         logger.error(f"Get position failed: {e}")              │
│         return None                                             │
└─────────────────────────────────────────────────────────────────┘


PHASE C: ACTIVATE DHAN IN MAIN BOT
──────────────────────────────────────────────────────────────────────────────

In TradingBot.run_live_loop():

CHANGE:
   # candle = self._fetch_candle()
   # if candle:
   #     self.on_new_candle(candle)

TO:
   candle = self.dhan.get_live_candle()
   if candle:
       self.on_new_candle(candle)

And in TradingBot._place_real_order():

CHANGE:
   # This will call dhan.place_order() after implementation

TO:
   actual_order_id = self.dhan.place_order(
       symbol=Config.SECURITY_ID,
       qty=1,                    # 1 lot
       side='BUY',              # Buy puts
       price=entry_price
   )
   if actual_order_id:
       logger.info(f"Live order placed: {actual_order_id}")


═══════════════════════════════════════════════════════════════════════════════
4. HOW TO RUN THE BOT
═══════════════════════════════════════════════════════════════════════════════

OPTION A: PAPER TRADING (Risk-free testing)
──────────────────────────────────────────────────────────────────────────────
✅ Recommended for first 2-3 weeks

Steps:
1. Ensure Config.PAPER_TRADING = True (line 79)
2. Keep DHAN credentials blank if not set up yet
3. Run: python nifty_atm_automation.py
4. Watch the logs to verify signals are working
5. Check nifty_atm_trading.log for complete history

What happens:
• No real orders are placed
• Trades are simulated in memory
• P&L is calculated virtually
• Useful for validating signal quality


OPTION B: LIVE TRADING (Real money)
──────────────────────────────────────────────────────────────────────────────
⚠️  Only after paper trading successful for 1+ week

Steps:
1. Complete Phase A & B (Dhan API setup)
2. Set Config.PAPER_TRADING = False (line 79)
3. Verify credentials are loaded from .env
4. Run: python nifty_atm_automation.py
5. Monitor actively for first hour
6. Check live positions in Dhan app simultaneously

What happens:
• Real orders are sent to Dhan
• Funds are required for orders
• P&L is real money
• Session log tracks every trade


═══════════════════════════════════════════════════════════════════════════════
5. TESTING & VALIDATION
═══════════════════════════════════════════════════════════════════════════════

BEFORE GOING LIVE, TEST:

✅ TEST 1: Signal Generation
   Purpose: Verify C1-C5 signals match your backtest
   
   Command:
   ```
   python -c "
   from nifty_atm_automation import *
   # Load historical data and check if same signals fire
   ```

✅ TEST 2: Position Management
   Purpose: Confirm SL/Target/Trailing work correctly
   
   Scenario: Create manual test position
   • Entry: 20000 points
   • SL: 20100 points
   • Target: 19750 points
   • Verify exits at exact right price

✅ TEST 3: Daily Reset
   Purpose: Check counters reset at midnight
   
   Commands:
   • Run bot across midnight
   • Verify consecutive_SL counter resets
   • Verify MAX_TRADES_DAY counter resets

✅ TEST 4: API Connectivity
   Purpose: Verify Dhan connection works
   
   Code:
   ```
   from nifty_atm_automation import DhanBroker, Config
   broker = DhanBroker(Config.DHAN_CLIENT_ID, 
                       Config.DHAN_ACCESS_TOKEN, 
                       Config.DHAN_API_KEY)
   candle = broker.get_live_candle()
   print(f"Latest close: {candle['close']}")
   ```


═══════════════════════════════════════════════════════════════════════════════
6. TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

ISSUE: "No signals being generated"
FIX:
   • Check if has_enough_data() returns True
   • Verify EMA calculations are correct
   • Print all 5 C1-C5 conditions to see which fail
   • Review backtest config — same parameters?

ISSUE: "Orders failing on Dhan"
FIX:
   • Verify credentials in .env file
   • Check Dhan account has funds
   • Ensure symbol/strike are valid
   • Check internet connection
   • Review Dhan API documentation

ISSUE: "SL/Target not hitting"
FIX:
   • Verify price data is real-time
   • Check that candles are actually closing at expected times
   • Confirm SL calculation: SL = max(High, EMA20) + 1.0 point
   • Ensure "at or touch" logic is correct

ISSUE: "Bot crashes or logs errors"
FIX:
   • Check nifty_atm_trading.log for full error
   • Search error message in code comments
   • Add more logger.info() statements for debugging
   • Wrap risky sections in try/except

ISSUE: "How do I monitor live trades?"
FIX:
   • Keep terminal window open (shows real-time logs)
   • Monitor Dhan app simultaneously (see actual orders)
   • Keep nifty_atm_trading.log open in text editor
   • Use `tail -f nifty_atm_trading.log` on Mac/Linux


═══════════════════════════════════════════════════════════════════════════════
NEXT STEPS
═══════════════════════════════════════════════════════════════════════════════

1. ✅ Understand the 4 core components (above)
2. ✅ Set up .env file with Dhan credentials
3. ✅ Fill in the 4 DhanBroker methods (above templates)
4. ✅ Test with paper trading for 1 week
5. ✅ Validate signals match backtest results
6. ✅ Monitor live trading for first month
7. ✅ Adjust parameters based on live performance

Questions? Review the code comments and logs!
