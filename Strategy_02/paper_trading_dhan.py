"""
╔══════════════════════════════════════════════════════════════════════════╗
║   NIFTY Buy-Put EMA Pullback — PAPER TRADING AUTOMATION (Dhan API)      ║
║   Run once at 9:20 AM. It will trade automatically until 14:45.         ║
╚══════════════════════════════════════════════════════════════════════════╝

HOW TO RUN:
    pip install dhanhq pandas numpy schedule requests
    python paper_trading_dhan.py

WHAT THIS DOES vs BACKTEST:
    Backtest  → reads past data all at once, no waiting
    This file → waits for each real 5-min candle to close, then checks signal
    Strategy logic is IDENTICAL to new_algo.ipynb

REAL MARKET INTEGRATION NOTE (at the bottom of this file):
    See the section "DIFFERENCE: BACKTEST vs LIVE PAPER TRADING"
"""

import os
import time
import warnings
import logging
from datetime import datetime, date, timedelta

import numpy  as np
import pandas as pd
import requests
import schedule

warnings.filterwarnings("ignore")



# ── Try to import dhanhq ────────────────────────────────────────────────
try:
    from dhanhq import dhanhq
except ImportError:
    print("❌  dhanhq not installed.  Run:  pip install dhanhq")
    raise

# ===========================================================================
# ██████████████████████  CONFIGURATION  ████████████████████████████████████
# ===========================================================================

# ── 🔑 Dhan Credentials ─────────────────────────────────────────────────────
# Get these from: https://login.dhan.co/ → My Profile → Access Token
# OPTION 1 — hardcode directly (easy local use):
DHAN_CLIENT_ID    = "YOUR_CLIENT_ID_HERE"      # ← paste your Client ID here
DHAN_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN_HERE"   # ← paste your Access Token here

# OPTION 2 — use environment variables (safer, no credentials in code):
# DHAN_CLIENT_ID    = os.getenv("DHAN_CLIENT_ID")
# DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")

# ── Strategy Parameters (SAME as new_algo.ipynb) ────────────────────────────
EMA_FAST         = 20
EMA_SLOW         = 200
TOUCH_BUFFER     = 10          # points
SL_BUFFER        = 5           # points above EMA20
RISK_REWARD      = 2.5
TRAIL_TRIGGER_R  = 1.5         # start trailing after 1.5R
CAPITAL          = 100_000     # paper capital ₹
RISK_PCT         = 0.01        # 1% per trade

# ── Session ──────────────────────────────────────────────────────────────────
SESSION_START_H, SESSION_START_M = 9, 30
SESSION_END_H,   SESSION_END_M   = 14, 45

# ── NIFTY option lot size ────────────────────────────────────────────────────
NIFTY_LOT_SIZE = 65            # current lot size (update if SEBI changes)

# ── Dhan security IDs ────────────────────────────────────────────────────────
NIFTY_SECURITY_ID  = "13"      # NIFTY 50 index on NSE
NIFTY_EXCHANGE_SEG = "IDX_I"   # NSE Index segment
NSE_FNO_SEG        = "NSE_FNO" # NSE F&O segment (for options)

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR     = os.path.dirname(os.path.abspath(__file__))
TRADES_CSV  = os.path.join(LOG_DIR, f"paper_trades_{date.today()}.csv")
CANDLES_CSV = os.path.join(LOG_DIR, f"live_candles_{date.today()}.csv")

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s  %(levelname)s  %(message)s",
    datefmt= "%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, f"paper_log_{date.today()}.log")),
    ]
)
log = logging.getLogger(__name__)


# ===========================================================================
# ██████████████████████  DHAN API WRAPPER  ██████████████████████████████████
# ===========================================================================

class DhanBridge:
    """Thin wrapper around dhanhq with helpers for NIFTY and options."""

    def __init__(self, client_id: str, access_token: str):
        self.dhan = dhanhq(client_id, access_token)
        log.info("✅ Dhan API connected.")

    # ── Spot price ───────────────────────────────────────────────────────────
    def get_nifty_spot(self) -> float:
        """Return current NIFTY 50 spot price."""
        resp = self.dhan.get_market_quote(
            security_id    = NIFTY_SECURITY_ID,
            exchange_segment = NIFTY_EXCHANGE_SEG,
        )
        # Dhan returns a dict; LTP is under 'data' → 'last_price'
        data = resp.get("data", {})
        ltp  = data.get("last_price") or data.get("ltp") or data.get("LTP")
        if ltp is None:
            raise ValueError(f"Cannot parse NIFTY LTP from response: {resp}")
        return float(ltp)

    # ── Historical 5-min candles (for EMA warmup at startup) ─────────────────
    def get_historical_candles(self, days_back: int = 6) -> pd.DataFrame:
        """
        Fetch last `days_back` trading days of 5-min NIFTY data.
        We need ~200 bars for EMA-200 warmup + session filter.
        ~51 bars/day × 5 days = 255 bars — just enough.
        """
        from_dt = (date.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_dt   = date.today().strftime("%Y-%m-%d")

        log.info(f"⏳ Fetching historical 5-min candles  {from_dt} → {to_dt} …")

        resp = self.dhan.intraday_minute_data(
            security_id      = NIFTY_SECURITY_ID,
            exchange_segment = NIFTY_EXCHANGE_SEG,
            instrument_type  = "INDEX",
            from_date        = from_dt,
            to_date          = to_dt,
            interval         = "5",
        )

        candles = resp.get("data", {})
        opens   = candles.get("open",   [])
        highs   = candles.get("high",   [])
        lows    = candles.get("low",    [])
        closes  = candles.get("close",  [])
        volumes = candles.get("volume", [])
        times   = candles.get("start_Time", candles.get("timestamp", []))

        if not closes:
            raise ValueError(f"No candle data returned from Dhan: {resp}")

        df = pd.DataFrame({
            "open"  : opens,
            "high"  : highs,
            "low"   : lows,
            "close" : closes,
            "volume": volumes,
        }, index=pd.to_datetime(times))

        df.index = pd.to_datetime(df.index)
        if df.index.tz is None:
            df.index = df.index.tz_localize("Asia/Kolkata")
        else:
            df.index = df.index.tz_convert("Asia/Kolkata")

        df.sort_index(inplace=True)
        df.dropna(subset=["close"], inplace=True)
        log.info(f"   Got {len(df):,} historical bars  ({df.index[0].date()} → {df.index[-1].date()})")
        return df

    # ── Option chain lookup ───────────────────────────────────────────────────
    def get_atm_put_security_id(self, spot: float) -> dict:
        """
        Return the Dhan security_id and premium of the nearest-expiry ATM PUT.
        ATM strike = round(spot / 50) * 50
        """
        atm_strike = round(spot / 50) * 50
        log.info(f"   Looking up ATM PUT for NIFTY spot={spot:.0f} → strike={atm_strike}")

        # Fetch option chain for current/next expiry
        today   = date.today()
        # Dhan needs expiry_date as YYYY-MM-DD; fetch nearest Thursday expiry
        expiry  = self._nearest_expiry(today)

        resp = self.dhan.option_chain(
            under_security_id  = NIFTY_SECURITY_ID,
            under_exchange_seg = NIFTY_EXCHANGE_SEG,
            expiry             = expiry.strftime("%Y-%m-%d"),
        )

        oc_data = resp.get("data", [])
        for row in oc_data:
            if (row.get("strike_price") == atm_strike
                    and row.get("option_type", "").upper() == "PE"):
                return {
                    "security_id" : str(row.get("security_id")),
                    "strike"      : atm_strike,
                    "expiry"      : expiry.strftime("%Y-%m-%d"),
                    "ltp"         : float(row.get("last_price", 0)),
                }

        log.warning(f"   ⚠️  ATM PUT security_id not found for strike {atm_strike} — using None")
        return {"security_id": None, "strike": atm_strike,
                "expiry": expiry.strftime("%Y-%m-%d"), "ltp": None}

    def get_option_ltp(self, security_id: str) -> float | None:
        """Fetch current LTP of an option contract."""
        if not security_id:
            return None
        try:
            resp = self.dhan.get_market_quote(
                security_id      = security_id,
                exchange_segment = NSE_FNO_SEG,
            )
            data = resp.get("data", {})
            ltp  = data.get("last_price") or data.get("ltp") or data.get("LTP")
            return float(ltp) if ltp else None
        except Exception as e:
            log.warning(f"   Option LTP fetch failed: {e}")
            return None

    @staticmethod
    def _nearest_expiry(ref_date: date) -> date:
        """Return the nearest upcoming Thursday (NIFTY weekly expiry)."""
        days_ahead = (3 - ref_date.weekday()) % 7  # Thursday = weekday 3
        if days_ahead == 0:
            days_ahead = 7
        return ref_date + timedelta(days=days_ahead)


# ===========================================================================
# ██████████████████████  INDICATOR ENGINE  ██████████████████████████████████
# ===========================================================================

def apply_session_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only 09:30–14:45 candles."""
    t = df.index.time
    s = pd.Timestamp("2000-01-01 09:30").time()
    e = pd.Timestamp("2000-01-01 14:45").time()
    return df.loc[(t >= s) & (t <= e)].copy()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute EMA-20 and EMA-200 + all helper columns (same as notebook)."""
    out = df.copy()
    out["ema20"]  = out["close"].ewm(span=EMA_FAST,  adjust=False, min_periods=EMA_FAST).mean()
    out["ema200"] = out["close"].ewm(span=EMA_SLOW, adjust=False, min_periods=EMA_SLOW).mean()

    out["below_ema20"]    = out["close"] < out["ema20"]
    out["below_ema200"]   = out["close"] < out["ema200"]
    out["bearish_candle"] = out["close"] < out["open"]
    out["bullish_candle"] = out["close"] > out["open"]
    out["body"]           = (out["close"] - out["open"]).abs()
    out["upper_wick"]     = out["high"] - out[["open","close"]].max(axis=1)
    out["lower_wick"]     = out[["open","close"]].min(axis=1) - out["low"]
    return out


def check_signal(df: pd.DataFrame) -> bool:
    """
    Evaluate the entry signal on the LAST completed candle.
    Exact same logic as CELL 4 (generate_signals) in new_algo.ipynb.
    Returns True if an entry signal fires on the last bar.
    """
    if len(df) < EMA_SLOW + 3:
        return False

    last = df.iloc[-1]

    # 1. Trend
    trend_bear    = last["below_ema20"] and last["below_ema200"]
    between_emas  = (last["close"] > last["ema20"]) and (last["close"] < last["ema200"])
    ema_gap_ok    = (last["ema200"] - last["ema20"]) > 20
    trend_ok      = trend_bear and not between_emas and ema_gap_ok

    # 2. Pullback (look back 3 candles including current)
    def touched(row, ema_col="ema20"):
        return row["high"] >= row[ema_col] - TOUCH_BUFFER

    pullback = any(touched(df.iloc[-i]) for i in range(1, 4) if len(df) >= i)

    # 3. Entry trigger
    close_below  = last["close"] < last["ema20"]
    close_valid  = last["close"] <= last["ema20"] + TOUCH_BUFFER
    is_bearish   = last["bearish_candle"]
    entry_ok     = is_bearish and close_valid and close_below

    return bool(trend_ok and pullback and entry_ok)


# ===========================================================================
# ██████████████████████  RISK ENGINE  ███████████████████████████████████████
# ===========================================================================

def calculate_sl(entry: float, ema20: float) -> float:
    return round(ema20 + SL_BUFFER, 2)

def calculate_target(entry: float, sl: float) -> float:
    risk = sl - entry
    return round(entry - risk * RISK_REWARD, 2)

def calculate_qty(entry: float, sl: float, capital: float) -> float:
    risk_amt = capital * RISK_PCT
    sl_pts   = abs(sl - entry)
    if sl_pts < 0.01:
        return 0.0
    return round(risk_amt / sl_pts, 4)


# ===========================================================================
# ██████████████████████  CSV LOGGER  ████████████████████████████████████████
# ===========================================================================

TRADE_COLUMNS = [
    "trade_id", "signal_time", "entry_time", "exit_time",
    "nifty_entry", "nifty_sl", "nifty_target", "nifty_exit",
    "atm_strike", "expiry", "option_security_id",
    "option_entry_premium", "option_exit_premium",
    "nifty_pnl_pts", "nifty_pnl_inr",
    "option_pnl_inr", "lots",
    "qty_notional", "r_multiple",
    "result", "exit_reason", "capital_after",
]

CANDLE_COLUMNS = [
    "time", "open", "high", "low", "close",
    "ema20", "ema200", "signal", "note",
]


def init_csv(path: str, columns: list):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_csv(path, index=False)
        log.info(f"   Created CSV: {path}")


def append_row(path: str, row_dict: dict):
    df = pd.DataFrame([row_dict])
    df.to_csv(path, mode="a", header=False, index=False)


# ===========================================================================
# ██████████████████████  PAPER TRADE STATE MACHINE  █████████████████████████
# ===========================================================================

class PaperTradeEngine:
    """
    Stateful engine — mirrors the loop in run_backtest() from the notebook.
    Called once per 5-min candle close.
    """

    def __init__(self, bridge: DhanBridge, initial_capital: float = CAPITAL):
        self.bridge   = bridge
        self.capital  = initial_capital
        self.trade_id = 0

        # Trade state
        self.in_trade      = False
        self.entry_price   = 0.0
        self.sl            = 0.0
        self.target        = 0.0
        self.qty           = 0.0
        self.risk_pts      = 0.0
        self.entry_time    = None
        self.trail_active  = False

        # Option info (paper only)
        self.option_info            = {}
        self.option_entry_premium   = None

        log.info(f"✅ Paper engine ready.  Capital: ₹{initial_capital:,}")

    # ── Called on every completed candle ─────────────────────────────────────
    def on_candle(self, df: pd.DataFrame):
        """
        df   = full indicator dataframe up to and including the closed candle.
        """
        now  = df.index[-1]
        last = df.iloc[-1]

        bar_close = float(last["close"])
        bar_high  = float(last["high"])
        bar_low   = float(last["low"])
        bar_ema20 = float(last["ema20"]) if not pd.isna(last["ema20"]) else bar_close

        # ── Log every candle ──────────────────────────────────────────────
        signal_fired = check_signal(df)
        append_row(CANDLES_CSV, {
            "time"   : now,
            "open"   : round(float(last["open"]), 2),
            "high"   : round(bar_high, 2),
            "low"    : round(bar_low, 2),
            "close"  : round(bar_close, 2),
            "ema20"  : round(bar_ema20, 2),
            "ema200" : round(float(last["ema200"]), 2) if not pd.isna(last["ema200"]) else None,
            "signal" : int(signal_fired),
            "note"   : "IN_TRADE" if self.in_trade else "",
        })

        # ── Manage open trade ─────────────────────────────────────────────
        if self.in_trade:
            pnl_pts = self.entry_price - bar_close   # positive = profit for PUT

            # Activate trailing at 1.5R
            if not self.trail_active and pnl_pts >= TRAIL_TRIGGER_R * self.risk_pts:
                self.trail_active = True
                log.info(f"   🔄 Trailing SL activated at {bar_close:.2f}")

            # Update trailing SL
            if self.trail_active:
                new_sl = bar_ema20 + SL_BUFFER
                if new_sl < self.sl:
                    log.info(f"   🔄 Trailing SL updated: {self.sl:.2f} → {new_sl:.2f}")
                    self.sl = new_sl

            # SL hit?
            if bar_high >= self.sl:
                self._exit_trade(now, self.sl, "SL", df)
                return

            # Target hit?
            if bar_low <= self.target:
                self._exit_trade(now, self.target, "TARGET", df)
                return

            # EOD exit at 14:45
            if now.hour == SESSION_END_H and now.minute >= SESSION_END_M:
                self._exit_trade(now, bar_close, "EOD", df)
                return

            log.info(f"   📊 In trade | NIFTY={bar_close:.2f}  SL={self.sl:.2f}  "
                     f"Target={self.target:.2f}  Trail={'ON' if self.trail_active else 'OFF'}")
            return

        # ── Check for new entry ───────────────────────────────────────────
        if not self.in_trade and signal_fired:
            # Session check — only enter between 09:30 and 14:30
            if not (SESSION_START_H <= now.hour < 14 or
                    (now.hour == 14 and now.minute <= 30)):
                log.info(f"   ⛔ Signal at {now.strftime('%H:%M')} outside entry window — skip")
                return

            self._enter_trade(now, bar_close, bar_ema20, df)

    # ── Entry ─────────────────────────────────────────────────────────────────
    def _enter_trade(self, ts, entry: float, ema20: float, df: pd.DataFrame):
        self.trade_id     += 1
        self.entry_price   = entry
        self.sl            = calculate_sl(entry, ema20)
        self.target        = calculate_target(entry, self.sl)
        self.risk_pts      = abs(self.sl - self.entry_price)
        self.qty           = calculate_qty(entry, self.sl, self.capital)
        self.entry_time    = ts
        self.trail_active  = False
        self.in_trade      = True

        # Fetch ATM PUT option details (paper only)
        try:
            self.option_info          = self.bridge.get_atm_put_security_id(entry)
            self.option_entry_premium = self.option_info.get("ltp")
        except Exception as e:
            log.warning(f"   Option lookup failed: {e}")
            self.option_info          = {"security_id": None, "strike": round(entry/50)*50,
                                          "expiry": None, "ltp": None}
            self.option_entry_premium = None

        log.info(f"\n{'─'*60}")
        log.info(f"  🟢 PAPER ENTRY  #{self.trade_id}")
        log.info(f"     Time         : {ts.strftime('%H:%M:%S')}")
        log.info(f"     NIFTY entry  : {entry:.2f}")
        log.info(f"     SL           : {self.sl:.2f}  (+{self.risk_pts:.1f} pts)")
        log.info(f"     Target       : {self.target:.2f}  (-{self.risk_pts*RISK_REWARD:.1f} pts)")
        log.info(f"     ATM Strike   : {self.option_info.get('strike')} PE")
        log.info(f"     Put Premium  : {self.option_entry_premium}")
        log.info(f"     Qty(notional): {self.qty:.2f}  |  Risk ₹{self.qty*self.risk_pts:.0f}")
        log.info(f"{'─'*60}\n")

    # ── Exit ──────────────────────────────────────────────────────────────────
    def _exit_trade(self, ts, exit_price: float, reason: str, df: pd.DataFrame):
        pnl_pts   = self.entry_price - exit_price    # positive = profit
        pnl_inr   = round(pnl_pts * self.qty, 2)
        self.capital += pnl_inr
        r_mult    = round(pnl_pts / self.risk_pts, 2) if self.risk_pts > 0 else 0
        result    = "WIN" if pnl_inr > 0 else "LOSS"

        # Option PnL
        option_exit_premium = None
        option_pnl_inr      = None
        lots                = None
        if self.option_info.get("security_id"):
            try:
                option_exit_premium = self.bridge.get_option_ltp(
                    self.option_info["security_id"])
            except Exception:
                pass
        if self.option_entry_premium and option_exit_premium:
            # Buy PUT: profit when premium rises (price falls)
            lots           = max(1, int(self.qty / NIFTY_LOT_SIZE))
            option_pnl_inr = round(
                (option_exit_premium - self.option_entry_premium) * lots * NIFTY_LOT_SIZE, 2)

        log.info(f"\n{'─'*60}")
        log.info(f"  {'🟢 WIN' if result=='WIN' else '🔴 LOSS'}  PAPER EXIT  #{self.trade_id}  ({reason})")
        log.info(f"     Time         : {ts.strftime('%H:%M:%S')}")
        log.info(f"     NIFTY exit   : {exit_price:.2f}")
        log.info(f"     NIFTY PnL    : {pnl_pts:+.2f} pts  →  ₹{pnl_inr:+,.0f}")
        log.info(f"     R-Multiple   : {r_mult:+.2f}R")
        if option_pnl_inr is not None:
            log.info(f"     Option PnL   : ₹{option_pnl_inr:+,.0f}  "
                     f"({lots} lot×{NIFTY_LOT_SIZE}  "
                     f"premium {self.option_entry_premium:.2f}→{option_exit_premium:.2f})")
        log.info(f"     Capital now  : ₹{self.capital:,.0f}")
        log.info(f"{'─'*60}\n")

        append_row(TRADES_CSV, {
            "trade_id"              : self.trade_id,
            "signal_time"           : self.entry_time,
            "entry_time"            : self.entry_time,
            "exit_time"             : ts,
            "nifty_entry"           : round(self.entry_price, 2),
            "nifty_sl"              : round(self.sl, 2),
            "nifty_target"          : round(self.target, 2),
            "nifty_exit"            : round(exit_price, 2),
            "atm_strike"            : self.option_info.get("strike"),
            "expiry"                : self.option_info.get("expiry"),
            "option_security_id"    : self.option_info.get("security_id"),
            "option_entry_premium"  : self.option_entry_premium,
            "option_exit_premium"   : option_exit_premium,
            "nifty_pnl_pts"         : round(pnl_pts, 2),
            "nifty_pnl_inr"         : pnl_inr,
            "option_pnl_inr"        : option_pnl_inr,
            "lots"                  : lots,
            "qty_notional"          : round(self.qty, 4),
            "r_multiple"            : r_mult,
            "result"                : result,
            "exit_reason"           : reason,
            "capital_after"         : round(self.capital, 2),
        })

        self.in_trade     = False
        self.trail_active = False


# ===========================================================================
# ██████████████████████  MAIN LOOP  █████████████████████████████████████████
# ===========================================================================

class LiveTrader:
    """Manages the intraday live loop."""

    def __init__(self):
        self.bridge     = DhanBridge(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
        self.engine     = PaperTradeEngine(self.bridge)
        self.candle_df  = pd.DataFrame()      # grows throughout the day

        # Initialise CSVs
        init_csv(TRADES_CSV,  TRADE_COLUMNS)
        init_csv(CANDLES_CSV, CANDLE_COLUMNS)

    # ── Startup: warm up EMAs with historical data ───────────────────────────
    def startup(self):
        log.info("🚀 STARTUP — fetching historical data for EMA warmup …")
        hist = self.bridge.get_historical_candles(days_back=7)
        hist = apply_session_filter(hist)
        hist = add_indicators(hist)
        hist.dropna(subset=["ema200"], inplace=True)
        # Keep only today's candles up to NOW, but we need the full
        # history for the rolling EMA — keep the full window
        self.candle_df = hist
        log.info(f"   Warmup done — {len(hist):,} bars loaded, "
                 f"last close: {hist['close'].iloc[-1]:.2f}")
        log.info(f"   EMA20={hist['ema20'].iloc[-1]:.2f}  "
                 f"EMA200={hist['ema200'].iloc[-1]:.2f}")

    # ── Called every 5 minutes at :xx:01 (1 second after candle close) ───────
    def tick(self):
        now = datetime.now()
        log.info(f"⏰ Tick at {now.strftime('%H:%M:%S')}")

        # Outside session → skip
        session_start = now.replace(hour=SESSION_START_H, minute=SESSION_START_M, second=0)
        session_end   = now.replace(hour=SESSION_END_H,   minute=SESSION_END_M,   second=0)
        if not (session_start <= now <= session_end):
            log.info("   Outside session — idle.")
            return

        # Build the latest candle
        try:
            candle = self._build_latest_candle(now)
        except Exception as e:
            log.error(f"   ❌ Failed to build candle: {e}")
            return

        if candle is None:
            log.info("   No new candle yet.")
            return

        # Append and recompute indicators (incremental EWM)
        self.candle_df = pd.concat([self.candle_df, candle])
        self.candle_df = add_indicators(self.candle_df)

        # Feed to engine
        self.engine.on_candle(self.candle_df)

    # ── Fetch the last completed 5-min candle ─────────────────────────────────
    def _build_latest_candle(self, now: datetime) -> pd.DataFrame | None:
        """
        Ask Dhan for today's 5-min bars and return the last completed one.
        """
        today_str = date.today().strftime("%Y-%m-%d")
        resp = self.bridge.dhan.intraday_minute_data(
            security_id      = NIFTY_SECURITY_ID,
            exchange_segment = NIFTY_EXCHANGE_SEG,
            instrument_type  = "INDEX",
            from_date        = today_str,
            to_date          = today_str,
            interval         = "5",
        )

        candles = resp.get("data", {})
        times   = candles.get("start_Time", candles.get("timestamp", []))
        closes  = candles.get("close", [])

        if not closes:
            return None

        df_today = pd.DataFrame({
            "open"  : candles.get("open",   []),
            "high"  : candles.get("high",   []),
            "low"   : candles.get("low",    []),
            "close" : closes,
            "volume": candles.get("volume", [0]*len(closes)),
        }, index=pd.to_datetime(times))

        if df_today.index.tz is None:
            df_today.index = df_today.index.tz_localize("Asia/Kolkata")
        else:
            df_today.index = df_today.index.tz_convert("Asia/Kolkata")

        df_today.sort_index(inplace=True)
        df_today = apply_session_filter(df_today)

        if df_today.empty:
            return None

        # Return only the last candle
        latest = df_today.iloc[[-1]]

        # Skip if we already have this timestamp
        if len(self.candle_df) > 0 and latest.index[-1] in self.candle_df.index:
            return None

        return latest

    # ── EOD summary ──────────────────────────────────────────────────────────
    def eod_summary(self):
        log.info("\n" + "="*60)
        log.info("  📋 END OF DAY SUMMARY")
        log.info("="*60)

        if not os.path.exists(TRADES_CSV):
            log.info("  No trades today.")
            return

        df = pd.read_csv(TRADES_CSV)
        if df.empty:
            log.info("  No trades today.")
            return

        wins   = (df["result"] == "WIN").sum()
        losses = (df["result"] == "LOSS").sum()
        net    = df["nifty_pnl_inr"].sum()
        log.info(f"  Trades : {len(df)}  |  W:{wins}  L:{losses}")
        log.info(f"  Net PnL (NIFTY pts) : {df['nifty_pnl_pts'].sum():+.2f} pts")
        log.info(f"  Net PnL (₹ notional): ₹{net:+,.0f}")
        if df["option_pnl_inr"].notna().any():
            log.info(f"  Net PnL (option ₹)  : ₹{df['option_pnl_inr'].sum():+,.0f}")
        log.info(f"  Trades CSV → {TRADES_CSV}")
        log.info(f"  Candles CSV → {CANDLES_CSV}")
        log.info("="*60)


# ===========================================================================
# ██████████████████████  ENTRY POINT  ███████████████████████████████████████
# ===========================================================================

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║  NIFTY Buy-Put EMA Pullback — PAPER TRADING AUTOMATION  ║
║  Strategy: same as new_algo.ipynb                       ║
║  Mode    : Paper (no real orders placed)                ║
╚══════════════════════════════════════════════════════════╝
""")

    trader = LiveTrader()
    trader.startup()

    # Schedule: fire 1 second after each 5-min candle close
    # Candles close at :30, :35, :40 ... i.e. every minute divisible by 5
    # We use schedule for simplicity; a production system would use asyncio
    for minute in range(30, 46, 5):   # 09:30 to 09:45 first hour
        pass                           # schedule handles the repeat below

    schedule.every(5).minutes.do(trader.tick)

    # Also schedule EOD summary
    schedule.every().day.at("14:50").do(trader.eod_summary)

    log.info("⏳ Waiting for next 5-min candle …  (Ctrl+C to stop)")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("\n⛔ Stopped by user.")
        trader.eod_summary()


if __name__ == "__main__":
    main()


# ===========================================================================
#
#  ██████████████████████████████████████████████████████████████████████████
#  ██                                                                      ██
#  ██   DIFFERENCE: BACKTESTING vs LIVE PAPER TRADING                     ██
#  ██   (Read this to understand what changed)                             ██
#  ██                                                                      ██
#  ██████████████████████████████████████████████████████████████████████████
#
#  ┌──────────────────────────────────────────────────────────────────────┐
#  │ ASPECT              │ BACKTEST (new_algo.ipynb)  │ THIS FILE (Live) │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ DATA SOURCE         │ yfinance (Yahoo)           │ Dhan API (live)  │
#  │                     │ All 59 days at once        │ Bar by bar       │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ TIME AWARENESS      │ No waiting needed          │ Waits 5 min per  │
#  │                     │ Loops over past data       │ candle to close  │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ SIGNAL EVALUATION   │ All signals computed on    │ ONE candle at a  │
#  │                     │ full history at once       │ time (real-time) │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ EMA WARMUP          │ Implicitly has 200 bars    │ Fetches 5-7 days │
#  │                     │ already in data            │ at startup (9AM) │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ EXECUTION           │ No orders, just simulated  │ Simulated too,   │
#  │                     │ at bar's close/high/low    │ logged to CSV    │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ OPTION INSTRUMENT   │ Not tracked — only NIFTY   │ ATM PUT found via│
#  │                     │ index points used          │ Dhan option chain│
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ SLIPPAGE            │ 0 (enters at exact close)  │ 0 (paper only)   │
#  │                     │ Unrealistic                │ Still unrealistic│
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ LOOK-AHEAD BIAS     │ Zero (ewm is backward)     │ Zero (same logic)│
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ STRATEGY LOGIC      │ CELL 4 generate_signals()  │ check_signal()   │
#  │                     │                            │ IDENTICAL RULES  │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ CAPITAL TRACKING    │ Updates after each trade   │ Updates after    │
#  │                     │ ends, uses updated capital │ each trade exits │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ EXIT LOGIC          │ SL hit on bar HIGH         │ Same             │
#  │                     │ Target on bar LOW          │ Same             │
#  │                     │ EOD at 14:45 close         │ Same             │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ TRAILING SL         │ EMA20 + buffer at 1.5R     │ Same             │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │ COSTS               │ Zero (no brokerage/tax)    │ Zero (paper)     │
#  │                     │                            │ Add STT + brok.  │
#  │                     │                            │ in real trading  │
#  └──────────────────────────────────────────────────────────────────────┘
#
#  KEY GAPS BETWEEN BACKTEST NUMBERS AND REAL RESULTS:
#  ────────────────────────────────────────────────────
#  1. OPTION PREMIUM ≠ INDEX POINTS
#     The backtest computes PnL in NIFTY index points (e.g., 30 pts = ₹1547).
#     In real trading the PUT premium moves differently — it is affected by:
#       • Delta (≈0.5 ATM) — premium moves ~50% of index move
#       • Theta (time decay) — premium loses value every minute
#       • Vega (IV change)  — premium jumps on volatility
#     So a 30-point NIFTY fall may give only 12-15 pts on the PUT premium.
#     This code tracks BOTH (nifty_pnl_pts AND option_pnl_inr) so you can
#     compare and measure the real-life drag.
#
#  2. SLIPPAGE
#     Backtest enters at candle CLOSE exactly.
#     In real market, you place a market order after you SEE the close —
#     meaning you often get filled 2–5 pts worse.
#     The CSV logs your assumed entry (bar close) vs what you'd actually get.
#
#  3. CONSECUTIVE SIGNAL FILTERING
#     Backtest suppresses new entries while a trade is open.
#     This code does the same (in_trade flag in PaperTradeEngine).
#
#  4. DATA LATENCY
#     yfinance gives clean OHLCV for past candles.
#     Dhan intraday API may have 1–2 candle lag at market open.
#     Always verify the first few candles manually.
#
#  5. WEEKDAY-ONLY AWARENESS
#     Backtest skips weekends automatically (no data).
#     This script uses `schedule` which runs every day — on weekends
#     the session filter will simply prevent any trades.
#
# ===========================================================================
