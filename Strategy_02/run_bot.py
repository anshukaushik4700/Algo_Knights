#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              NIFTY BUY-PUT EMA PULLBACK STRATEGY #2                          ║
║                   API-BASED AUTOMATED TRADING BOT                            ║
║                   Production Entry Point                                     ║
║                                                                              ║
║  This is the main script to run Strategy_02 automated trading.               ║
║  Supports both PAPER TRADING (virtual) and LIVE TRADING (real trades).       ║
║                                                                              ║
║  Usage:                                                                      ║
║      python run_bot.py              # Run Strategy_02 with current config    ║
║      python setup_api.py            # First-time setup and validation        ║
║                                                                              ║
║  Documentation:                                                              ║
║      .env - Configuration file (shared with Strategy_01)                     ║
║      setup_api.py - API credential validator                                 ║
║      README.md - Full documentation                                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
from datetime import datetime
import logging

# Load environment variables from .env file (if it exists)
try:
    from dotenv import load_dotenv
    
    # Try to load .env from Strategy_02 folder first
    strategy_env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(strategy_env):
        load_dotenv(strategy_env)
        print("✅ Loaded .env from Strategy_02 folder")
    else:
        # Fallback: Load from root folder
        root_env = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(root_env):
            load_dotenv(root_env)
            print("✅ Loaded .env from root folder (Algo_Knights/)")
        else:
            print("⚠️  No .env file found in Strategy_02 or root folder")
            print("   Create .env file with your Dhan API credentials")
except ImportError:
    print("⚠️  python-dotenv not installed. Environment variables from .env won't be loaded")
    print("   Install with: pip install python-dotenv")

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("🚀 STRATEGY #2 - NIFTY BUY-PUT EMA PULLBACK AUTOMATION")
    print("=" * 80)
    
    from datetime import date
    import pytz
    
    ist = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(ist)
    current_date = current_time.date()
    
    print(f"\n⏰ Current Time (IST): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Day: {current_date.strftime('%A')}")
    
    # Check if it's a weekday
    if current_time.weekday() >= 5:
        print("\n⚠️  WARNING: Market is CLOSED on weekends!")
        print("   The bot will wait until Monday 9:30 AM to start trading")
    
    # Check credentials
    print(f"\n🔐 Configuration Status:")
    
    dhan_client_id = os.getenv("DHAN_CLIENT_ID", "").strip()
    dhan_access_token = os.getenv("DHAN_ACCESS_TOKEN", "").strip()
    
    if dhan_client_id and dhan_access_token:
        masked_id = dhan_client_id[:4] + "*" * (len(dhan_client_id) - 8) + dhan_client_id[-4:]
        masked_token = dhan_access_token[:4] + "*" * (len(dhan_access_token) - 8) + dhan_access_token[-4:]
        print(f"   ✅ Dhan Client ID: {masked_id}")
        print(f"   ✅ Dhan Access Token: {masked_token}")
    else:
        print("   ❌ ERROR: Dhan credentials NOT configured!")
        print("      Set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN in .env file")
        print("      Or run: python setup_api.py")
        return False
    
    print(f"\n📋 Strategy Parameters:")
    print(f"   • Strategy: Bearish EMA 20/200 Pullback")
    print(f"   • Timeframe: 5-minute candles")
    print(f"   • Instrument: NIFTY 50 Index (^NSEI)")
    print(f"   • Trade Type: Buy Put (ATM)")
    print(f"   • Mode: Paper Trading (Virtual Position Size)")
    
    print(f"\n🕐 Trading Hours:")
    print(f"   • Session: 9:30 AM - 2:45 PM IST (Monday-Friday)")
    print(f"   • Candle Check: Every 5 minutes")
    
    print("\n" + "=" * 80)
    print("✅ Configuration validated - Starting bot...")
    print("=" * 80)
    print("\n💡 Press Ctrl+C to stop the bot gracefully\n")
    
    # Import and run the main trader
    try:
        from paper_trading_dhan import main as run_trader
        run_trader()
    except ImportError as e:
        print(f"❌ Error: Could not import trading module: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
    except KeyboardInterrupt:
        print("\n\n✅ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("🏁 Bot shutdown complete")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
