#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   NIFTY ATM AUTOMATED TRADING BOT                            ║
║                   API-BASED PRODUCTION ENTRY POINT                           ║
║                                                                              ║
║  This is the main script to run the automated trading strategy.              ║
║  Supports both PAPER TRADING (virtual) and LIVE TRADING (real trades).       ║
║                                                                              ║
║  Usage:                                                                      ║
║      python run_bot.py              # Run with current config                ║
║      python setup_api.py            # First-time setup and validation        ║
║                                                                              ║
║  Documentation:                                                              ║
║      .env.example - Configuration template                                   ║
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
# First checks Strategy_01 folder, then checks parent (root) folder
try:
    from dotenv import load_dotenv
    import os
    
    # Try to load .env from Strategy_01 folder first
    strategy_env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(strategy_env):
        load_dotenv(strategy_env)
        print("✅ Loaded .env from Strategy_01 folder")
    else:
        # Fallback: Load from root folder
        root_env = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(root_env):
            load_dotenv(root_env)
            print("✅ Loaded .env from root folder (Algo_Knights/)")
        else:
            print("⚠️  No .env file found in Strategy_01 or root folder")
            print("   Create .env file with your Dhan API credentials")
except ImportError:
    print("⚠️  python-dotenv not installed. Environment variables from .env won't be loaded")
    print("   Install with: pip install python-dotenv")

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nifty_atm_automation import TradingBot, Config, logger

# ─────────────────────────────────────────────────────────────────────────────
#  ENVIRONMENT SETUP
# ─────────────────────────────────────────────────────────────────────────────

def load_api_config():
    """Load API configuration from environment variables"""
    # Get trading mode
    paper_trading_env = os.getenv('PAPER_TRADING', 'true').lower()
    Config.PAPER_TRADING = paper_trading_env in ['true', '1', 'yes', 'on']
    
    # Load Dhan credentials
    Config.DHAN_CLIENT_ID = os.getenv('DHAN_CLIENT_ID', '')
    Config.DHAN_ACCESS_TOKEN = os.getenv('DHAN_ACCESS_TOKEN', '')
    Config.DHAN_API_KEY = os.getenv('DHAN_API_KEY', '')
    
    # Override strategy parameters if set in environment
    if os.getenv('EMA_FAST'):
        Config.EMA_FAST = int(os.getenv('EMA_FAST'))
    if os.getenv('EMA_SLOW'):
        Config.EMA_SLOW = int(os.getenv('EMA_SLOW'))
    if os.getenv('MAX_TRADES_DAY'):
        Config.MAX_TRADES_DAY = int(os.getenv('MAX_TRADES_DAY'))
    if os.getenv('RR_RATIO'):
        Config.RR_RATIO = float(os.getenv('RR_RATIO'))

def setup_environment():
    """Setup environment and check requirements"""
    print("\n" + "=" * 80)
    print("🚀 NIFTY ATM TRADING BOT - STARTUP")
    print("=" * 80)
    
    # Load config from environment
    load_api_config()
    
    # Check if running during market hours
    import pytz
    
    ist = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(ist)
    current_date = current_time.date()
    
    print(f"\n⏰ Current Time (IST): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Day: {current_date.strftime('%A')}")
    
    # Check if it's a weekday
    if current_time.weekday() >= 5:
        print("\n⚠️  WARNING: Market is CLOSED on weekends!")
        print("   The bot will wait until Monday 9:15 AM to start trading")
    
    # Check credentials and mode
    print(f"\n🔐 Configuration Status:")
    
    if Config.PAPER_TRADING:
        print("   ✅ Mode: PAPER TRADING (Virtual)")
        print(f"   📊 Starting Balance: {Config.INITIAL_BALANCE} points")
        print("   ℹ️  No real capital at risk - safe to test")
    else:
        print("   🔴 Mode: LIVE TRADING (Real Money!)")
        print("   ⚠️  REAL CAPITAL AT RISK!")
        
        if Config.DHAN_CLIENT_ID and Config.DHAN_ACCESS_TOKEN:
            print("   ✅ Dhan credentials: Configured")
        else:
            print("   ❌ ERROR: Dhan credentials NOT configured for live trading!")
            print("      Set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN in .env file")
            print("      Or run: python setup_api.py")
            return False
    
    print(f"\n📋 Strategy Parameters:")
    print(f"   • EMA Fast (Entry): {Config.EMA_FAST}")
    print(f"   • EMA Slow (Trend): {Config.EMA_SLOW}")
    print(f"   • Max Trades/Day: {Config.MAX_TRADES_DAY}")
    print(f"   • Risk:Reward: 1:{Config.RR_RATIO}")
    print(f"   • Max Consecutive SL: {Config.KILLSWITCH_SL}")
    
    print(f"\n🕐 Market Hours:")
    print(f"   • Session Opens: {Config.SESSION_START.strftime('%H:%M')} IST")
    print(f"   • New Entries Until: {Config.ENTRY_CUTOFF.strftime('%H:%M')} IST")
    print(f"   • Force Exit: {Config.FORCE_EXIT_TIME.strftime('%H:%M')} IST")
    print(f"   • Session Closes: {Config.SESSION_END.strftime('%H:%M')} IST")
    
    # ✅ Confirm before live trading
    if not Config.PAPER_TRADING:
        print("\n" + "=" * 80)
        print("⚠️  LIVE TRADING MODE - CONFIRMATION REQUIRED")
        print("=" * 80)
        response = input("\n🔴 Type 'YES, TRADE LIVE' to proceed with REAL MONEY trading: ").strip()
        
        if response.upper() != 'YES, TRADE LIVE':
            print("\n❌ Live trading not confirmed - switching to paper mode for safety")
            Config.PAPER_TRADING = True
            print("   Rerun with PAPER_TRADING=true in .env to avoid this prompt")
    
    print("\n" + "=" * 80)
    print("✅ All checks passed - Starting bot...")
    print("=" * 80)
    
    # Log to file
    logger.info("=" * 80)
    logger.info(f"🚀 BOT STARTED | {current_time.strftime('%Y-%m-%d %H:%M:%S')} IST")
    logger.info(f"   Mode: {'PAPER TRADING' if Config.PAPER_TRADING else 'LIVE TRADING'}")
    logger.info(f"   Run By: run_bot.py")
    logger.info(f"   Python: {sys.version.split()[0]}")
    logger.info("=" * 80)
    
    return True

def show_first_time_help():
    """Show help for first-time setup"""
    if not os.path.exists(".env"):
        print("\n" + "━" * 80)
        print("📋 FIRST TIME SETUP")
        print("━" * 80)
        print("""
1️⃣  Create credentials file:
    Copy .env.example to .env
    
    cp .env.example .env          # Linux/Mac
    copy .env.example .env        # Windows

2️⃣  Configure your credentials:
    Open .env and add:
    • DHAN_CLIENT_ID
    • DHAN_ACCESS_TOKEN  
    • DHAN_API_KEY
    
    Get these from: https://www.dhan.co/settings/api-keys

3️⃣  Validate setup:
    python setup_api.py

4️⃣  Run the bot:
    python run_bot.py

📚 For more info, see README.md
━ """ * 80)

def main():
    """Main entry point"""
    try:
        # First-time setup help
        show_first_time_help()
        
        # Setup and checks
        if not setup_environment():
            print("\n❌ Setup failed - bot cannot start")
            sys.exit(1)
        
        # Create and start bot
        print("\n💡 Press Ctrl+C to stop the bot gracefully\n")
        bot = TradingBot()
        bot.run_live_loop()
        
    except KeyboardInterrupt:
        print("\n\n✅ Bot stopped by user")
        logger.info("🛑 Bot stopped by user")
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        logger.error(f"❌ Fatal Error: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        print("\n" + "=" * 80)
        print("🏁 Bot shutdown complete")
        print("=" * 80)
        logger.info("=" * 80)
        logger.info("🏁 Bot shutdown complete")
        logger.info("=" * 80)

if __name__ == "__main__":
    main()
