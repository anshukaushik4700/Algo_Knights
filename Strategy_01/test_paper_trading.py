"""
═══════════════════════════════════════════════════════════════════════════════
    TEST SCRIPT: PAPER TRADING WITH HISTORICAL DATA SIMULATION
═══════════════════════════════════════════════════════════════════════════════

This script feeds historical 5-minute candles to the bot
to simulate and validate paper trading in a controlled environment.

Usage:
    python test_paper_trading.py

Result:
    • Processes historical data through bot logic
    • Detects signals on real market data
    • Tracks all trades (paper trading)
    • Prints detailed results and trade log
    • Saves logs to: nifty_atm_trading.log
"""

import warnings
warnings.filterwarnings('ignore')

# Fix Unicode emoji display on Windows
import sys, io
if sys.stdout and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import yfinance as yf
import pandas as pd
from datetime import datetime
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
    
    # Fetch recent 5-min data
    print("\n📊 Fetching historical data for simulation...")
    print("   (This may take 30-60 seconds depending on internet speed)")
    
    try:
        df_raw = yf.download(
            Config.SYMBOL,
            interval="5m",
            period="30d",  # 30 days - more candles = more signals
            auto_adjust=True,
            progress=False
        )
    except Exception as e:
        print(f"❌ Failed to download data: {e}")
        return
    
    # Handle multi-level columns
    if isinstance(df_raw.columns, pd.MultiIndex):
        df_raw.columns = df_raw.columns.get_level_values(0)
    
    # Convert timezone to IST
    if df_raw.index.tzinfo is None:
        df_raw = df_raw.tz_localize("UTC")
    df_raw = df_raw.tz_convert(Config.IST)
    
    # Filter to market session only (9:15 AM - 3:30 PM IST)
    df_raw = df_raw.between_time("09:15", "15:30")
    df_raw.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
    
    print(f"✅ Downloaded {len(df_raw)} candles")
    print(f"   Date range: {df_raw.index[0].strftime('%Y-%m-%d %H:%M')} → {df_raw.index[-1].strftime('%Y-%m-%d %H:%M')}")
    
    if len(df_raw) == 0:
        print("❌ No data available for the period. Try a different date range.")
        return
    
    # Feed candles to bot one by one
    print("\n🔄 Feeding candles to bot...\n")
    
    total_candles = len(df_raw)
    
    for idx, (ts, row) in enumerate(df_raw.iterrows()):
        candle = {
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'timestamp': ts
        }
        
        # Call bot's candle processor
        try:
            bot.on_new_candle(candle)
        except Exception as e:
            print(f"❌ Error processing candle {idx}: {e}")
            return
        
        # Print progress
        progress = (idx + 1) / total_candles * 100
        if (idx + 1) % 100 == 0 or idx == total_candles - 1:
            bar_length = 30
            filled = int(bar_length * (idx + 1) / total_candles)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"   [{bar}] {progress:.0f}% ({idx + 1}/{total_candles} candles)")
    
    print(f"\n✅ Simulation complete!\n")
    
    # Debug: Show how many signals were detected
    print("\n🔍 DEBUG INFO:")
    print(f"   Total candles processed: {total_candles}")
    print(f"   Bot trades executed: {len(bot.paper_engine.trades_log)}")
    print(f"   Check nifty_atm_trading.log for signal details")
    
    # Get summary
    summary = bot.paper_engine.get_summary()
    
    # Print final results
    print("=" * 80)
    print("📊 PAPER TRADING RESULTS")
    print("=" * 80)
    
    if summary:
        print(f"\n📈 Performance Metrics:")
        print(f"   Total Trades:        {summary['total_trades']}")
        print(f"   Wins:                {summary['wins']}")
        print(f"   Losses:              {summary['losses']}")
        print(f"   Win Rate:            {summary['win_rate']:.1f}%")
        print(f"   Total P&L:           {summary['total_pnl']:+.1f} points")
        print(f"   Avg R-Multiple:      {summary['avg_r']:+.2f}x")
        print(f"   Final Balance:       {summary['balance']:+.0f} points")
        print(f"   Initial Balance:     {Config.INITIAL_BALANCE}")
        
        # Calculate return percentage
        if Config.INITIAL_BALANCE > 0:
            return_pct = (summary['balance'] - Config.INITIAL_BALANCE) / Config.INITIAL_BALANCE * 100
            print(f"   Return:              {return_pct:+.2f}%")
    else:
        print("\n⚠️  No trades executed")
        print("   Possible reasons:")
        print("   • Not enough signals generated in this period")
        print("   • Try with longer period (30d instead of 5d)")
        print("   • Check that signals match your backtest")
    
    # Print trade log
    if bot.paper_engine.trades_log:
        print("\n" + "=" * 80)
        print("📝 DETAILED TRADE LOG")
        print("=" * 80)
        
        for i, trade in enumerate(bot.paper_engine.trades_log, 1):
            duration_minutes = (trade['exit_time'] - trade['entry_time']).total_seconds() / 60
            emoji = "✅" if trade['pnl'] > 0 else "❌" if trade['pnl'] < 0 else "⏳"
            
            print(f"\n{emoji} Trade #{i} [{trade['result']}]")
            print(f"   Entry Time:     {trade['entry_time'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Entry Price:    {trade['entry_price']:.2f}")
            print(f"   SL Level:       {trade['sl']:.2f}")
            print(f"   Target Level:   {trade['target']:.2f}")
            print(f"   Exit Price:     {trade['exit_price']:.2f}")
            print(f"   Exit Time:      {trade['exit_time'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Duration:       {duration_minutes:.0f} minutes")
            print(f"   P&L:            {trade['pnl']:+.2f} points")
            print(f"   R-Multiple:     {trade['r_multiple']:+.2f}x")
            print(f"   Risk:           {trade['risk']:.2f} points")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)
    
    # Instructions
    print("\n📋 Next Steps:")
    print("   1. Check console output above for results")
    print("   2. Open: nifty_atm_trading.log (full event log)")
    print("   3. Compare with your backtest results")
    print("   4. If satisfied, proceed to Dhan API integration")
    print("   5. See: ATM_SETUP_GUIDE.md for next steps")
    
    return summary


if __name__ == "__main__":
    test_paper_trading()
