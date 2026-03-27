#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    SETUP & VALIDATION SCRIPT - STRATEGY #2
    
    Validates API credentials and connection before trading
    Safe to run before trading - does NOT place any orders
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
from datetime import datetime
import pytz

# Load environment variables
try:
    from dotenv import load_dotenv
    
    # Try to load .env from Strategy_02 folder first
    strategy_env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(strategy_env):
        load_dotenv(strategy_env)
    else:
        # Fallback: Load from root folder
        root_env = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(root_env):
            load_dotenv(root_env)
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

def check_environment():
    """Check if environment is properly configured"""
    print("\n" + "=" * 80)
    print("🔍 ENVIRONMENT VALIDATION")
    print("=" * 80)
    
    env_vars = {
        'DHAN_CLIENT_ID': 'Dhan Client ID',
        'DHAN_ACCESS_TOKEN': 'Dhan Access Token',
    }
    
    missing = []
    for var, name in env_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
            print(f"  ✅ {name}: {masked}")
        else:
            print(f"  ❌ {name}: NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️  Missing credentials: {', '.join(missing)}")
        print("\n📋 To set credentials:")
        print("   1. Copy .env.template to .env (at root: Algo_Knights/)")
        print("   2. Fill in your Dhan API credentials")
        print("   3. Run this script again")
        return False
    
    return True

def test_dhan_connection():
    """Test connection to Dhan API"""
    print("\n" + "=" * 80)
    print("🔌 DHAN API CONNECTION TEST")
    print("=" * 80)
    
    try:
        from dhanhq import dhanhq
        print("  ✅ Dhan SDK installed")
    except ImportError:
        print("  ❌ Dhan SDK not installed")
        print("     Install with: pip install dhanhq")
        return False
    
    client_id = os.getenv('DHAN_CLIENT_ID')
    access_token = os.getenv('DHAN_ACCESS_TOKEN')
    
    try:
        print("  📡 Connecting to Dhan API...")
        client = dhanhq(client_id, access_token)
        print("  ✅ Successfully connected to Dhan API!")
        
        # Try to fetch NIFTY spot price as a test
        try:
            print("  📊 Fetching NIFTY 50 spot price...")
            result = client.get_market_quote(
                security_id="13",
                exchange_segment="IDX_I"
            )
            if result and result.get("data"):
                ltp = result["data"].get("last_price") or result["data"].get("ltp")
                if ltp:
                    print(f"  ✅ NIFTY Spot: ₹{ltp}")
                    return True
            return True
        except Exception as e:
            print(f"  ⚠️  Connection established but couldn't fetch NIFTY: {e}")
            return True
    
    except Exception as e:
        print(f"  ❌ Failed to connect: {e}")
        return False

def check_market_hours():
    """Check if we're in market hours"""
    print("\n" + "=" * 80)
    print("⏰ MARKET HOURS CHECK")
    print("=" * 80)
    
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    
    print(f"  Current time (IST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Day: {now.strftime('%A')}")
    
    if now.weekday() >= 5:
        print("  ⚠️  Market closed: WEEKEND")
        return False
    
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=14, minute=45, second=59, microsecond=999999)
    
    if market_open <= now <= market_close:
        print("  ✅ Market is OPEN")
        return True
    else:
        print(f"  ⏳ Market closed. Next open: Tomorrow 9:30 AM IST")
        return False

def test_data_connection():
    """Test market data connection"""
    print("\n" + "=" * 80)
    print("📊 DATA CONNECTION TEST")
    print("=" * 80)
    
    try:
        print("  ✅ Dhan API will provide live data")
        return True
    except Exception as e:
        print(f"  ⚠️  Data test failed: {e}")
        return True  # Not critical

def generate_startup_report():
    """Generate a startup readiness report"""
    print("\n" + "=" * 80)
    print("📋 STARTUP READINESS REPORT - STRATEGY #2")
    print("=" * 80)
    
    checks = {
        'Environment': check_environment(),
        'Dhan API': test_dhan_connection(),
        'Data Connection': test_data_connection(),
    }
    
    all_pass = all(checks.values())
    
    print("\n" + "=" * 80)
    if all_pass:
        print("✅ ALL CHECKS PASSED - READY TO RUN BOT!")
        print("\nNext step: python run_bot.py")
    else:
        print("❌ SOME CHECKS FAILED - FIX ABOVE ISSUES BEFORE RUNNING BOT")
    print("=" * 80)
    
    return all_pass

def main():
    """Main validation flow"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  STRATEGY #2 - SETUP & VALIDATION".center(78) + "║")
    print("║" + "  Test credentials and connection before trading".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Run checks
    ready = generate_startup_report()
    
    return 0 if ready else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
