"""
═══════════════════════════════════════════════════════════════════════════════
    NIFTY 50 — BUY PUT STRATEGY — AUTOMATED PAPER TRADING (ATM) SYSTEM
═══════════════════════════════════════════════════════════════════════════════
Strategy: Bearish EMA 20 / EMA 200 Pullback on 5-Minute Chart
Mode: Live Paper Trading (Orders via Dhan API)
Timeframe: 5-minute | Index: ^NSEI | Style: Buy Put (bearish)
═══════════════════════════════════════════════════════════════════════════════

This script converts the backtest into real-time automated trading.
It runs continuously and places/manages orders based on live market signals.
"""

import warnings
warnings.filterwarnings('ignore')

import sys
import json
import logging
from datetime import datetime, time, timedelta
import pytz
import pandas as pd
import numpy as np
from collections import deque
import time as time_module

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 1: IMPORT DHAN API (will be installed later)
# ─────────────────────────────────────────────────────────────────────────────
# Dhan API import will be added after you set up credentials
# from dhan import DhanClient

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING SETUP
# ─────────────────────────────────────────────────────────────────────────────

# Fix Unicode emoji display on Windows
import sys, io
if sys.stdout and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('nifty_atm_trading.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION & PARAMETERS (Same as backtest + additions)
# ─────────────────────────────────────────────────────────────────────────────

class Config:
    """All trading configuration in one place - EDIT THESE VALUES"""
    
    # ── Symbol & Timeframe ────────────────────────────────
    SYMBOL          = "^NSEI"          # Nifty 50 Index
    SECURITY_ID     = "NIFTY"          # Dhan Security ID (will add)
    INTERVAL        = "5m"             # 5-minute candles
    CANDLES_BUFFER  = 250              # Keep last 250 candles in memory
    
    # ── EMA Parameters ────────────────────────────────────
    EMA_FAST        = 20               # Fast EMA
    EMA_SLOW        = 200              # Slow EMA
    WARMUP          = 200              # Discard first 200 candles
    
    # ── Timezone ──────────────────────────────────────────
    IST             = pytz.timezone("Asia/Kolkata")
    
    # ── Market Hours ──────────────────────────────────────
    SESSION_START   = time(9, 30)      # No entries before 9:30 AM IST
    ENTRY_CUTOFF    = time(14, 30)     # No new entries at 2:30 PM IST
    FORCE_EXIT_TIME = time(15, 15)     # Force close all trades at 3:15 PM IST
    SESSION_END     = time(15, 30)     # End of session
    MARKET_OPEN     = time(9, 15)      # Market opens
    
    # ── Position Management ───────────────────────────────
    MAX_TRADES_DAY  = 4                # Max 4 active trades per day
    KILLSWITCH_SL   = 2                # Stop after 2 consecutive SLs
    PULLBACK_WINDOW = 5                # Candles for C5 validity
    
    # ── Risk Management ──────────────────────────────────
    SL_BUFFER       = 1.0              # Points above EMA20 for SL
    RR_RATIO        = 2.5              # Risk:Reward ratio
    TRAIL_TRIGGER_R = 1.5              # Activate trailing after 1.5R
    MAX_EMA_DISTANCE= 10.0             # Max points below EMA20 at entry
    
    # ── DHAN API CREDENTIALS ──────────────────────────────
    # ⚠️  DO NOT commit these to git! Use environment variables
    DHAN_CLIENT_ID  = ""               # Set via environment variable
    DHAN_ACCESS_TOKEN = ""             # Set via environment variable
    DHAN_API_KEY    = ""               # Set via environment variable
    
    # ── Paper Trading ─────────────────────────────────────
    PAPER_TRADING   = True             # Set False for live trading (use with caution!)
    INITIAL_BALANCE = 100000           # Virtual balance for P&L tracking
    
    @staticmethod
    def load_dhan_credentials():
        """Load Dhan credentials from environment variables or config file."""
        import os
        Config.DHAN_CLIENT_ID = os.getenv('DHAN_CLIENT_ID', '')
        Config.DHAN_ACCESS_TOKEN = os.getenv('DHAN_ACCESS_TOKEN', '')
        Config.DHAN_API_KEY = os.getenv('DHAN_API_KEY', '')
        
        if not all([Config.DHAN_CLIENT_ID, Config.DHAN_ACCESS_TOKEN, Config.DHAN_API_KEY]):
            logger.warning("⚠️  Dhan credentials not fully configured. Paper trading mode active.")
            Config.PAPER_TRADING = True


# ─────────────────────────────────────────────────────────────────────────────
#  DATA MANAGER — Maintains rolling buffer of candles
# ─────────────────────────────────────────────────────────────────────────────

class DataManager:
    """
    Manages live candle data.
    ✅ Converted from batch download to real-time streaming
    """
    
    def __init__(self):
        self.candles = deque(maxlen=Config.CANDLES_BUFFER)  # Rolling buffer
        self.df = pd.DataFrame()  # Current dataframe
        self.last_update = None
        logger.info("DataManager initialized with rolling buffer")
    
    def add_candle(self, o, h, l, c, timestamp):
        """Add new candle to buffer and update dataframe."""
        self.candles.append({
            'Open': o,
            'High': h,
            'Low': l,
            'Close': c,
            'Timestamp': timestamp
        })
        self._rebuild_dataframe()
        self.last_update = timestamp
    
    def _rebuild_dataframe(self):
        """Rebuild dataframe from candle buffer."""
        if not self.candles:
            return
        
        self.df = pd.DataFrame(list(self.candles))
        self.df['Timestamp'] = pd.to_datetime(self.df['Timestamp'])
        self.df.set_index('Timestamp', inplace=True)
        
        # Add EMAs
        if len(self.df) > 1:
            self.df['EMA20'] = self.df['Close'].ewm(span=Config.EMA_FAST, adjust=False).mean()
            self.df['EMA200'] = self.df['Close'].ewm(span=Config.EMA_SLOW, adjust=False).mean()
    
    def get_dataframe(self):
        """Return current dataframe with EMAs."""
        return self.df.copy()
    
    def has_enough_data(self):
        """Check if buffer has minimum candles for warmup."""
        return len(self.candles) >= Config.WARMUP + 10


# ─────────────────────────────────────────────────────────────────────────────
#  SIGNAL GENERATOR — Detects entry signals (same logic as backtest)
# ─────────────────────────────────────────────────────────────────────────────

class SignalGenerator:
    """
    Detects C1-C5 signals from live candles.
    ✅ Uses exact same logic as backtest
    """
    
    def __init__(self, data_manager):
        self.dm = data_manager
    
    def check_signal(self, latest_candle_idx=-1):
        """
        Check if latest candle has all 5 conditions met.
        Returns: True if signal, False otherwise
        """
        df = self.dm.get_dataframe()
        
        if len(df) < Config.WARMUP + 1:
            return False
        
        row = df.iloc[latest_candle_idx]
        
        # C1: Close below BOTH EMAs
        c1 = row['Close'] < row['EMA20'] and row['Close'] < row['EMA200']
        
        # C2: Bearish candle (red)
        c2 = row['Close'] < row['Open']
        
        # C3: Candle touches EMA20
        c3 = (row['High'] >= row['EMA20']) or (row['Close'] <= row['EMA20'])
        
        # C4: Not too far below EMA20
        c4 = row['Close'] >= (row['EMA20'] - Config.MAX_EMA_DISTANCE)
        
        # C5: Last N candles had close <= EMA20
        c5 = self._check_pullback_validity(df, latest_candle_idx)
        
        signal = c1 and c2 and c3 and c4 and c5
        
        if signal:
            logger.info(f"📊 SIGNAL DETECTED | C1:{c1} C2:{c2} C3:{c3} C4:{c4} C5:{c5}")
        
        return signal
    
    def _check_pullback_validity(self, df, idx):
        """Check C5: Last N candles all had close <= their EMA20."""
        if idx - Config.PULLBACK_WINDOW < 0:
            return False
        
        prev_closes = df['Close'].iloc[idx-Config.PULLBACK_WINDOW:idx].values
        prev_ema = df['EMA20'].iloc[idx-Config.PULLBACK_WINDOW:idx].values
        
        return all(prev_closes <= prev_ema)


# ─────────────────────────────────────────────────────────────────────────────
#  PAPER TRADING ENGINE (In-Memory Order Management)
# ─────────────────────────────────────────────────────────────────────────────

class PaperTradingEngine:
    """
    ✅ CORE: Manages in-memory paper trading
    Tracks positions, calculates P&L, manages exits.
    This REPLACES manual order placement during testing phase.
    """
    
    def __init__(self):
        self.positions = {}  # {order_id: position_dict}
        self.trades_log = []  # All completed trades
        self.today_trades = 0
        self.consecutive_sl = 0
        self.killswitch_active = False
        self.order_counter = 0
        self.balance = Config.INITIAL_BALANCE
        logger.info(f"Paper Trading Engine started | Balance: {self.balance}")
    
    def create_order(self, entry_price, highest_point, ema20, current_time):
        """Create a new entry order in paper mode."""
        if self.killswitch_active:
            logger.warning("⛔ Killswitch active - no new entries")
            return None
        
        if self.today_trades >= Config.MAX_TRADES_DAY:
            logger.warning(f"⚠️  Daily trade limit ({Config.MAX_TRADES_DAY}) reached")
            return None
        
        # Calculate SL and Target
        sl = max(highest_point, ema20) + Config.SL_BUFFER
        risk = sl - entry_price
        
        if risk <= 0:
            logger.warning("Invalid risk calculation - skipping entry")
            return None
        
        target = entry_price - (Config.RR_RATIO * risk)
        
        self.order_counter += 1
        order_id = f"PAPER_{self.order_counter}"
        
        position = {
            'order_id': order_id,
            'entry_price': entry_price,
            'sl': sl,
            'target': target,
            'risk': risk,
            'entry_time': current_time,
            'trail_active': False,
            'trail_sl': sl,
            'status': 'ACTIVE'
        }
        
        self.positions[order_id] = position
        self.today_trades += 1
        
        logger.info(
            f"✅ ENTRY | Order: {order_id} | Entry: {entry_price:.2f} | "
            f"SL: {sl:.2f} | Target: {target:.2f} | Risk: {risk:.2f}"
        )
        return order_id
    
    def update_position(self, current_price, current_ema20, current_time):
        """Update all open positions - check SL, Target, Trailing SL."""
        for order_id, pos in list(self.positions.items()):
            if pos['status'] != 'ACTIVE':
                continue
            
            # Activate trailing after 1.5R
            if not pos['trail_active']:
                profit = pos['entry_price'] - current_price
                if profit >= Config.TRAIL_TRIGGER_R * pos['risk']:
                    pos['trail_active'] = True
                    logger.info(f"🔔 {order_id}: Trailing SL activated")
            
            # Update trailing SL (only tighten)
            if pos['trail_active']:
                new_trail = current_ema20
                if new_trail < pos['trail_sl']:
                    pos['trail_sl'] = new_trail
            
            sl_price = pos['trail_sl'] if pos['trail_active'] else pos['sl']
            
            # SL HIT
            if current_price >= sl_price:
                exit_price = sl_price
                pnl = pos['entry_price'] - exit_price
                r_multiple = pnl / pos['risk']
                result = 'TRAIL_SL' if pos['trail_active'] else 'SL'
                
                self._close_position(order_id, exit_price, pnl, r_multiple, result, current_time)
                
                if result == 'SL':
                    self.consecutive_sl += 1
                else:
                    self.consecutive_sl = 0
                
                if self.consecutive_sl >= Config.KILLSWITCH_SL:
                    self.killswitch_active = True
                    logger.warning("🛑 KILLSWITCH ACTIVATED - No more trades today")
            
            # TARGET HIT
            elif current_price <= pos['target']:
                exit_price = pos['target']
                pnl = pos['entry_price'] - exit_price
                r_multiple = pnl / pos['risk']
                
                self._close_position(order_id, exit_price, pnl, r_multiple, 'TARGET', current_time)
                self.consecutive_sl = 0
    
    def force_exit_all(self, current_price, current_time):
        """Force close all open positions at session end."""
        for order_id in list(self.positions.keys()):
            pos = self.positions[order_id]
            if pos['status'] == 'ACTIVE':
                pnl = pos['entry_price'] - current_price
                r_multiple = pnl / pos['risk']
                self._close_position(order_id, current_price, pnl, r_multiple, 'TIME_EXIT', current_time)
                logger.info(f"⏰ {order_id}: Force exit at {current_price:.2f}")
    
    def _close_position(self, order_id, exit_price, pnl, r_multiple, result, exit_time):
        """Internal: Mark position as closed and log trade."""
        pos = self.positions[order_id]
        pos['status'] = 'CLOSED'
        pos['exit_price'] = exit_price
        pos['pnl'] = pnl
        pos['r_multiple'] = r_multiple
        pos['exit_time'] = exit_time
        pos['result'] = result
        
        self.balance += pnl
        self.trades_log.append(pos.copy())
        
        emoji = "✅" if pnl > 0 else "❌" if pnl < 0 else "⏳"
        logger.info(
            f"{emoji} {order_id} CLOSED | Result: {result} | "
            f"Exit: {exit_price:.2f} | P&L: {pnl:+.2f} pts | R: {r_multiple:+.2f} | "
            f"Balance: {self.balance:+.0f}"
        )
    
    def reset_daily_counters(self):
        """Reset counters at end of each trading day."""
        self.today_trades = 0
        self.consecutive_sl = 0
        self.killswitch_active = False
        logger.info("📅 Daily counters reset")
    
    def get_summary(self):
        """Return current P&L summary."""
        if not self.trades_log:
            return None
        
        df = pd.DataFrame(self.trades_log)
        total = len(df)
        wins = len(df[df['pnl'] > 0])
        losses = len(df[df['pnl'] <= 0])
        total_pnl = df['pnl'].sum()
        win_rate = (wins / total * 100) if total > 0 else 0
        
        return {
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_r': df['r_multiple'].mean(),
            'balance': self.balance
        }


# ─────────────────────────────────────────────────────────────────────────────
#  DHAN API BROKER INTERFACE (Will be implemented)
# ─────────────────────────────────────────────────────────────────────────────

class DhanBroker:
    """
    🔌 FUTURE: Dhan API integration for live trading
    
    When you're ready to go live:
    1. Uncomment the import at the top
    2. Add your Dhan credentials to environment variables
    3. Replace paper trading with actual API calls in these methods
    """
    
    def __init__(self, client_id, access_token, api_key):
        """Initialize Dhan API client."""
        # Uncomment when ready:
        # from dhan import DhanClient
        # self.client = DhanClient(client_id, access_token)
        # self.api_key = api_key
        
        self.is_connected = False
        logger.info("🔌 DhanBroker initialized (ready for API integration)")
    
    def get_live_candle(self):
        """
        Fetch latest 5-min candle from Dhan.
        
        IMPLEMENTATION TODO:
        ```python
        try:
            # Historical data API call
            response = self.client.historical_candle(
                security_id=Config.SECURITY_ID,
                exchange_token="NIFTY",
                interval="FiveMin",
                from_date="2024-03-15",  # Today
                to_date="2024-03-15"
            )
            
            candle = response[-1]  # Latest candle
            return {
                'open': float(candle['open']),
                'high': float(candle['high']),
                'low': float(candle['low']),
                'close': float(candle['close']),
                'timestamp': candle['timestamp']
            }
        except Exception as e:
            logger.error(f"API Error: {e}")
            return None
        ```
        """
        pass
    
    def place_order(self, symbol, qty, side, price, order_type='LIMIT'):
        """
        Place order on Dhan.
        
        IMPLEMENTATION TODO:
        ```python
        try:
            response = self.client.place_order(
                security_id=symbol,
                quantity=qty,
                side=side,  # 'BUY' or 'SELL'
                price=price,
                product_type="MIS",  # Intraday
                order_type=order_type,
                dhan_client_id=Config.DHAN_CLIENT_ID
            )
            return response['order_id']
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return None
        ```
        """
        pass
    
    def cancel_order(self, order_id):
        """Cancel an order."""
        # Implementation similar to place_order
        pass
    
    def get_position(self, order_id):
        """Get position status from Dhan."""
        # Implementation
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN AUTOMATION LOOP
# ─────────────────────────────────────────────────────────────────────────────

class TradingBot:
    """
    ✅ MAIN: Orchestrates the entire automation loop
    Runs continuously during market hours
    """
    
    def __init__(self):
        Config.load_dhan_credentials()
        
        self.data_manager = DataManager()
        self.signal_gen = SignalGenerator(self.data_manager)
        self.paper_engine = PaperTradingEngine()
        self.dhan = DhanBroker(Config.DHAN_CLIENT_ID, Config.DHAN_ACCESS_TOKEN, Config.DHAN_API_KEY)
        
        self.running = True
        self.current_day = None
        
        logger.info("=" * 80)
        logger.info("🚀 NIFTY ATM BOT INITIALIZED")
        logger.info(f"   Mode: {'PAPER TRADING' if Config.PAPER_TRADING else 'LIVE TRADING'}")
        logger.info(f"   Max Trades/Day: {Config.MAX_TRADES_DAY}")
        logger.info(f"   Session: {Config.SESSION_START.strftime('%H:%M')} - {Config.SESSION_END.strftime('%H:%M')} IST")
        logger.info("=" * 80)
    
    def on_new_candle(self, candle_data):
        """
        Called every 5 minutes when new candle completes.
        This is the MAIN ENTRY POINT for new market data.
        """
        timestamp = candle_data['timestamp']
        current_time = timestamp.time()
        current_date = timestamp.date()
        
        # Reset daily counters at start of day
        if self.current_day != current_date:
            self.paper_engine.reset_daily_counters()
            self.current_day = current_date
            logger.info(f"📅 New trading day: {current_date}")
        
        # Add candle to buffer
        self.data_manager.add_candle(
            candle_data['open'],
            candle_data['high'],
            candle_data['low'],
            candle_data['close'],
            timestamp
        )
        
        # Not enough warmup data yet
        if not self.data_manager.has_enough_data():
            return
        
        df = self.data_manager.get_dataframe()
        latest = df.iloc[-1]
        
        # UPDATE: Manage existing positions (check SL, Target, Trail)
        self.paper_engine.update_position(
            latest['Close'],
            latest['EMA20'],
            timestamp
        )
        
        # CHECK: Is it time to check for new entries?
        if not (Config.SESSION_START <= current_time < Config.ENTRY_CUTOFF):
            if current_time >= Config.FORCE_EXIT_TIME and self.paper_engine.positions:
                logger.warning(f"⚠️  Force exit time reached: {current_time}")
                self.paper_engine.force_exit_all(latest['Close'], timestamp)
            return
        
        # SIGNAL: Check for entry signal
        if self.signal_gen.check_signal(latest_candle_idx=-1):
            # Try to enter
            order_id = self.paper_engine.create_order(
                entry_price=latest['Close'],
                highest_point=latest['High'],
                ema20=latest['EMA20'],
                current_time=timestamp
            )
            
            # If not paper trading, also place order on broker
            if order_id and not Config.PAPER_TRADING:
                self._place_real_order(order_id, latest['Close'])
    
    def _place_real_order(self, order_id, price):
        """
        Place real order on Dhan broker.
        Only called when PAPER_TRADING = False
        """
        logger.info(f"📡 Placing real order on Dhan: {order_id}")
        # This will call dhan.place_order() after implementation
        pass
    
    def run_live_loop(self):
        """
        ✅ MAIN LOOP: Run continuously during market hours
        Connected to live data feed (Dhan API)
        """
        logger.info("▶️  Starting live trading loop...")
        
        while self.running:
            try:
                current_time = datetime.now(Config.IST).time()
                
                # Check if market is open
                if not (Config.MARKET_OPEN <= current_time <= Config.SESSION_END):
                    time_module.sleep(60)  # Sleep during closed hours
                    continue
                
                # Fetch latest candle (from Dhan API or paper data)
                candle = self._fetch_candle()
                
                if candle:
                    self.on_new_candle(candle)
                
                # Log summary every hour
                if current_time.minute == 0:
                    self._log_summary()
                
                # Sleep until next candle (5 minutes)
                time_module.sleep(300)  # 5 minutes
            
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                time_module.sleep(10)
    
    def _fetch_candle(self):
        """
        Fetch the latest candle.
        Will use Dhan API when implemented.
        """
        # TODO: Replace with:
        # candle = self.dhan.get_live_candle()
        # For now, returns None (needs real data feed)
        return None
    
    def _log_summary(self):
        """Log current trading summary."""
        summary = self.paper_engine.get_summary()
        if summary:
            logger.info(
                f"📊 Summary | Trades: {summary['total_trades']} | "
                f"W/L: {summary['wins']}/{summary['losses']} | "
                f"Win%: {summary['win_rate']:.1f}% | "
                f"PnL: {summary['total_pnl']:+.1f} | "
                f"Balance: {summary['balance']:+.0f}"
            )


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot = TradingBot()
    
    # Option 1: Run live loop (requires Dhan API connection)
    # bot.run_live_loop()
    
    # Option 2: Test with sample data (for development)
    logger.info("💡 Tip: Connect real data feed or use test_with_sample_data()")
    logger.info("   Documentation includes Dhan API integration steps")
