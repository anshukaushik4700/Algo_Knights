"""
ORDER BLOCK IMPLEMENTATION FOR STRATEGY_01

This file contains the custom order block logic that can be integrated into nifty_atm_automation.py

Copy-paste the relevant classes/methods into your main bot file as needed.

ORDER BLOCK SPECIFICATION:
- Buy: 1 Lot of ATM Put
- Stop Loss: 20 points ABOVE entry
- Target: 60 points BELOW entry
- Risk: 20 points (Fixed)
- Reward: 60 points (Fixed)
- R:R Ratio: 1:3 (Fixed)
"""

# ═══════════════════════════════════════════════════════════════════════════════
# OPTION 1: Update Config Class - Add these parameters
# ═══════════════════════════════════════════════════════════════════════════════

class Config_CustomOrderBlock:
    """
    Add these parameters to your existing Config class in nifty_atm_automation.py
    """
    
    # ──── EXISTING PARAMETERS (Keep these) ────────────────────────────────────
    EMA_FAST = 20
    EMA_SLOW = 200
    SL_BUFFER = 1.0
    RR_RATIO = 2.5
    TRAIL_TRIGGER_R = 1.5
    MAX_EMA_DISTANCE = 10.0
    
    # ──── NEW CUSTOM ORDER BLOCK PARAMETERS (Add these) ──────────────────────
    USE_CUSTOM_ORDER_BLOCK = True        # Set to True to enable custom order block
    CUSTOM_SL_DISTANCE = 20              # SL: 20 points above entry
    CUSTOM_TARGET_DISTANCE = 60          # Target: 60 points below entry
    CUSTOM_LOT_SIZE = 1                  # Lot size


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION 2: Create Custom Order Block Class
# ═══════════════════════════════════════════════════════════════════════════════

class CustomOrderBlock:
    """
    Custom order block with fixed SL and Target distances
    
    This replaces the dynamic SL/Target calculation with fixed distances:
    - SL is always 20 points above entry
    - Target is always 60 points below entry
    - 1:3 Risk:Reward ratio maintained for all trades
    """
    
    @staticmethod
    def create_order(entry_price, highest_point=None, ema20=None, current_time=None):
        """
        Create order with FIXED SL and Target distances
        
        Args:
            entry_price (float): Entry price level
            highest_point (float): Not used in custom block (for compatibility)
            ema20 (float): Not used in custom block (for compatibility)
            current_time (str): Timestamp of order creation
        
        Returns:
            dict: Order details with SL and Target
            
        Example:
            >> order = CustomOrderBlock.create_order(entry_price=20450.75)
            >> print(order['SL Level'])  # 20470.75
            >> print(order['Target Level'])  # 20390.75
        """
        
        # Fixed distances
        SL_DISTANCE = 20
        TARGET_DISTANCE = 60
        
        # Calculate SL and Target
        sl = entry_price + SL_DISTANCE
        target = entry_price - TARGET_DISTANCE
        risk = SL_DISTANCE
        reward = TARGET_DISTANCE
        
        # Create order structure
        order = {
            'entry_price': entry_price,
            'sl': sl,
            'target': target,
            'risk': risk,
            'reward': reward,
            'rr_ratio': f"{reward/risk:.1f}",
            'lot_size': 1,
            'order_type': 'BUY_PUT_ATM',
            'created_at': current_time,
        }
        
        return order


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION 3: Modify Existing create_order() Method
# ═══════════════════════════════════════════════════════════════════════════════

def create_order_custom_block(self, entry_price, highest_point, ema20, current_time):
    """
    MODIFIED VERSION of create_order() in PaperTradingEngine class
    
    This version uses FIXED SL and Target distances instead of dynamic calculation
    
    Replace the create_order() method in PaperTradingEngine with this code:
    """
    
    # ──── Use custom fixed SL/Target if enabled ────────────────────────────
    if Config.USE_CUSTOM_ORDER_BLOCK:
        # Custom order block logic
        sl = entry_price + Config.CUSTOM_SL_DISTANCE          # SL: 20 points above
        target = entry_price - Config.CUSTOM_TARGET_DISTANCE  # Target: 60 points below
        risk = Config.CUSTOM_SL_DISTANCE
        reward = Config.CUSTOM_TARGET_DISTANCE
    else:
        # Original dynamic logic (keep as fallback)
        sl = max(highest_point, ema20) + Config.SL_BUFFER
        risk = sl - entry_price
        target = entry_price - (Config.RR_RATIO * risk)
        reward = entry_price - target
    
    # Create order
    order = {
        'entry_price': entry_price,
        'highest_point': highest_point,
        'ema20': ema20,
        'sl': sl,
        'target': target,
        'risk': risk,
        'reward': reward,
        'rr_ratio': reward / risk if risk != 0 else 0,
        'lot_size': Config.CUSTOM_LOT_SIZE if Config.USE_CUSTOM_ORDER_BLOCK else 1,
        'order_type': 'BUY_PUT_ATM' if Config.USE_CUSTOM_ORDER_BLOCK else 'BUY_PUT',
        'created_at': current_time,
        'status': 'ACTIVE',
    }
    
    return order


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION 4: Integration Instructions
# ═══════════════════════════════════════════════════════════════════════════════

INTEGRATION_STEPS = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     INTEGRATION STEPS FOR CUSTOM ORDER BLOCK                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

STEP 1: Update Config Class
────────────────────────────
In nifty_atm_automation.py, find the Config class and add:

    class Config:
        # ... existing parameters ...
        
        # Add these NEW lines:
        USE_CUSTOM_ORDER_BLOCK = True
        CUSTOM_SL_DISTANCE = 20
        CUSTOM_TARGET_DISTANCE = 60
        CUSTOM_LOT_SIZE = 1


STEP 2: Modify create_order() Method
─────────────────────────────────────
In PaperTradingEngine class, replace the create_order() method with:

    def create_order(self, entry_price, highest_point, ema20, current_time):
        # Use custom fixed SL/Target if enabled
        if Config.USE_CUSTOM_ORDER_BLOCK:
            sl = entry_price + Config.CUSTOM_SL_DISTANCE
            target = entry_price - Config.CUSTOM_TARGET_DISTANCE
            risk = Config.CUSTOM_SL_DISTANCE
            reward = Config.CUSTOM_TARGET_DISTANCE
        else:
            # Original logic
            sl = max(highest_point, ema20) + Config.SL_BUFFER
            risk = sl - entry_price
            target = entry_price - (Config.RR_RATIO * risk)
            reward = entry_price - target
        
        order = {
            'entry_price': entry_price,
            'highest_point': highest_point,
            'ema20': ema20,
            'sl': sl,
            'target': target,
            'risk': risk,
            'reward': reward,
            'rr_ratio': reward / risk if risk != 0 else 0,
            'lot_size': Config.CUSTOM_LOT_SIZE if Config.USE_CUSTOM_ORDER_BLOCK else 1,
            'order_type': 'BUY_PUT_ATM' if Config.USE_CUSTOM_ORDER_BLOCK else 'BUY_PUT',
            'created_at': current_time,
            'status': 'ACTIVE',
        }
        
        return order


STEP 3: Test the Changes
────────────────────────
1. Run the bot in PAPER TRADING mode first
2. Check the logs for order creation:
   - Entry price should match signal
   - SL should be Entry + 20
   - Target should be Entry - 60
   - Risk should be 20 pts
   - Reward should be 60 pts
   - R:R ratio should be 1:3.0

3. Verify calculations match the CSV files:
   - order_block_verification.csv
   - order_block_extended_verification.csv


STEP 4: Switch to Live Trading (When Ready)
─────────────────────────────────────────
In run_bot.py or setup, change:
    PAPER_TRADING = True  →  PAPER_TRADING = False

Then start with:
    python run_bot.py


STEP 5: Monitor Orders (First Few Trades)
──────────────────────────────────────────
1. Check the log file: nifty_atm_trading.log
2. Verify each order has:
   - Entry: Correct level
   - SL: Entry + 20
   - Target: Entry - 60
   - Lot Size: 1
   - Status: ACTIVE → PARTIAL FILLED → CLOSED (as trade progresses)

3. If order blocks don't match expected values, review Config parameters


STEP 6: Rollback (If Needed)
────────────────────────────
To disable custom order block and revert to original logic:
    USE_CUSTOM_ORDER_BLOCK = False

This will revert to dynamic SL/Target calculation based on price action.
"""

print(INTEGRATION_STEPS)


# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE: How Order Block Calculations Work
# ═══════════════════════════════════════════════════════════════════════════════

CALCULATION_REFERENCE = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          ORDER BLOCK CALCULATIONS                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝

EXAMPLE: Entry at 20450.75

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Entry Signal Detected                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ NIFTY Level: 20450.75                                                       │
│ Signal: BUY_PUT (Bearish confluence detected)                               │
│ Order Type: Buy 1 Lot ATM Put                                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Calculate SL (Fixed Distance)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Formula: SL = Entry + 20 points                                             │
│ SL = 20450.75 + 20                                                          │
│ SL = 20470.75                                                               │
│                                                                              │
│ Meaning: If index goes 20 points ABOVE entry, exit with loss                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Calculate Target (Fixed Distance)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Formula: Target = Entry - 60 points                                         │
│ Target = 20450.75 - 60                                                      │
│ Target = 20390.75                                                           │
│                                                                              │
│ Meaning: If index goes 60 points BELOW entry, exit with profit              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Calculate Risk & Reward                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Risk = Entry - SL = 20450.75 - 20470.75 = 20 points (Loss if SL hits)      │
│ Reward = Entry - Target = 20450.75 - 20390.75 = 60 points (Gain if target)│
│ R:R Ratio = Reward / Risk = 60 / 20 = 3:1                                  │
│                                                                              │
│ Meaning: We risk 20 points to make 60 points (3x return)                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ POSSIBLE OUTCOMES                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Scenario 1: Target Hit ✅                                                   │
│   Index falls to 20390.75 → Position closed → Profit: +60 points            │
│                                                                              │
│ Scenario 2: SL Hit ❌                                                       │
│   Index rises to 20470.75 → Position closed → Loss: -20 points              │
│                                                                              │
│ Scenario 3: Mid-way Exit ⏳                                                 │
│   Index falls to 20420.75 (midway) → Manual exit → Profit: +30 points       │
│                                                                              │
│ Scenario 4: Time-based Exit                                                 │
│   End of day → Position closed → Profit/Loss depends on exit price          │
└─────────────────────────────────────────────────────────────────────────────┘

WIN PROBABILITY ANALYSIS (For 1:3 R:R trades):
─────────────────────────────────────────────
If you win 40% of trades and lose 60% of trades:
    Expected Value = (0.40 × 60) - (0.60 × 20)
    Expected Value = 24 - 12 = +12 points per trade

This is PROFITABLE because the 1:3 R:R ratio allows us to make money
even when we win less than 50% of the time!

"""

print(CALCULATION_REFERENCE)


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFICATION CHECKLIST
# ═══════════════════════════════════════════════════════════════════════════════

VERIFICATION_CHECKLIST = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        VERIFICATION CHECKLIST                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Before deploying to live trading, verify:

☐ 1. CSV Files Match Expected Calculations
   File: order_block_verification.csv
   Expected: All orders have SL = Entry + 20, Target = Entry - 60

☐ 2. Config Class Updated
   Find: USE_CUSTOM_ORDER_BLOCK = True
   Check: CUSTOM_SL_DISTANCE = 20
   Check: CUSTOM_TARGET_DISTANCE = 60
   Check: CUSTOM_LOT_SIZE = 1

☐ 3. create_order() Method Modified
   Find: PaperTradingEngine.create_order() method
   Check: Contains logic to check USE_CUSTOM_ORDER_BLOCK
   Check: Calculates SL = entry + 20
   Check: Calculates Target = entry - 60

☐ 4. Paper Trading Test
   Action: Set PAPER_TRADING = True
   Run: python run_bot.py
   Wait: 1-2 signals to generate
   Check: Log file shows correct SL/Target values
   Verify: Match calculations in CSV files

☐ 5. Signal Generation Unchanged
   Check: Original signal logic not modified
   Check: Only SL/Target calculation changed
   Check: Entry price still based on EMA 20/200 pullback

☐ 6. Logs Show Correct K-Line
   Look: nifty_atm_trading.log
   Verify: Entry price matches NIFTY level at order time
   Verify: SL = Entry + 20 (within 0.5 point tolerance)
   Verify: Target = Entry - 60 (within 0.5 point tolerance)

☐ 7. Ready for Live Trading
   After 2-3 successful paper trades:
   Set: PAPER_TRADING = False
   Update: .env file with PAPER_TRADING=False
   Start: python run_bot.py
   Monitor: First 3-5 live trades before leaving unattended

"""

print(VERIFICATION_CHECKLIST)
