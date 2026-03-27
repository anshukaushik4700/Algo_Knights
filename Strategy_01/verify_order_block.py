#!/usr/bin/env python3
"""
ORDER BLOCK VERIFICATION TOOL FOR STRATEGY_01

This script tests the custom order block:
- Buy 1 Lot of ATM Put
- SL: 20 points of index above entry
- Target: 60 points of index below entry

Run this to verify order calculations are correct before deploying to live bot.
"""

import csv
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
#  CUSTOM ORDER BLOCK - Your Specification
# ─────────────────────────────────────────────────────────────────────────────

class CustomOrderBlock:
    """
    Custom order block with fixed SL and Target distances
    
    Parameters:
    - BUY: 1 Lot of ATM Put
    - SL: 20 points above entry
    - Target: 60 points below entry
    - Lot Size: 1
    - Risk: Fixed 20 points
    - Reward: Fixed 60 points
    - R:R Ratio: 1:3 (Fixed)
    """
    
    # Fixed parameters for this strategy
    LOT_SIZE = 1                    # Buy 1 Lot
    SL_DISTANCE = 20                # SL 20 points above entry
    TARGET_DISTANCE = 60            # Target 60 points below entry
    ORDER_TYPE = "BUY_PUT_ATM"      # Buy Put (Bearish signal)
    
    @staticmethod
    def create_order(entry_price, current_time):
        """
        Create order with fixed SL and Target
        
        Args:
            entry_price: NIFTY index level at entry
            current_time: Timestamp of entry
        
        Returns:
            order_dict with all order details
        """
        
        # Calculate SL and Target
        sl = entry_price + CustomOrderBlock.SL_DISTANCE
        target = entry_price - CustomOrderBlock.TARGET_DISTANCE
        risk = CustomOrderBlock.SL_DISTANCE
        reward = CustomOrderBlock.TARGET_DISTANCE
        
        # Create order structure
        order = {
            'Entry Price': entry_price,
            'SL Level': sl,
            'Target Level': target,
            'Risk (Points)': risk,
            'Reward (Points)': reward,
            'R:R Ratio': f"1:{reward/risk:.1f}",
            'Lot Size': CustomOrderBlock.LOT_SIZE,
            'Order Type': CustomOrderBlock.ORDER_TYPE,
            'Entry Time': current_time,
            'Status': 'ACTIVE',
        }
        
        return order


# ─────────────────────────────────────────────────────────────────────────────
#  TEST SCENARIOS - Verify Order Block
# ─────────────────────────────────────────────────────────────────────────────

def create_test_scenarios():
    """Create test scenarios with different entry prices"""
    
    test_entries = [
        20000.00,  # Lower index level
        20250.50,  # Mid level
        20450.75,  # Typical entry
        20500.00,  # Higher level
        20750.25,  # High level
    ]
    
    test_data = []
    
    for entry_price in test_entries:
        order = CustomOrderBlock.create_order(
            entry_price=entry_price,
            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        test_data.append([
            f"{order['Entry Price']:.2f}",
            f"{order['SL Level']:.2f}",
            f"{order['Target Level']:.2f}",
            order['Risk (Points)'],
            order['Reward (Points)'],
            order['R:R Ratio'],
            order['Lot Size'],
            order['Order Type'],
            order['Status'],
        ])
    
    return test_data


# ─────────────────────────────────────────────────────────────────────────────
#  VERIFICATION & OUTPUT
# ─────────────────────────────────────────────────────────────────────────────

def format_table(headers, rows):
    """Format a table for terminal display"""
    col_widths = [max(len(str(h)), max(len(str(row[i])) for row in rows)) for i, h in enumerate(headers)]
    
    line = "│ " + " │ ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers)) + " │"
    sep = "├─" + "─┼─".join("─" * (w + 2) for w in col_widths) + "─┤"
    
    print("┌─" + "─┬─".join("─" * (w + 2) for w in col_widths) + "─┐")
    print(line)
    print(sep)
    for row in rows:
        print("│ " + " │ ".join(f"{str(row[i]):<{col_widths[i]}}" for i in range(len(headers))) + " │")
    print("└─" + "─┴─".join("─" * (w + 2) for w in col_widths) + "─┘")


def verify_order_block():
    """Verify and display the order block"""
    
    print("\n" + "=" * 120)
    print("ORDER BLOCK VERIFICATION - STRATEGY_01 CUSTOM PARAMETERS")
    print("=" * 120)
    
    print("\n📋 ORDER BLOCK SPECIFICATION:")
    print("─" * 120)
    print(f"  • Instrument: NIFTY 50 Index (Buy Put - Bearish)")
    print(f"  • Lot Size: {CustomOrderBlock.LOT_SIZE}")
    print(f"  • SL Distance: {CustomOrderBlock.SL_DISTANCE} points ABOVE entry")
    print(f"  • Target Distance: {CustomOrderBlock.TARGET_DISTANCE} points BELOW entry")
    print(f"  • Risk per Trade: Fixed {CustomOrderBlock.SL_DISTANCE} points")
    print(f"  • Reward per Trade: Fixed {CustomOrderBlock.TARGET_DISTANCE} points")
    print(f"  • Risk:Reward Ratio: 1:{CustomOrderBlock.TARGET_DISTANCE / CustomOrderBlock.SL_DISTANCE:.1f}")
    print("─" * 120)
    
    # Create test scenarios
    test_data = create_test_scenarios()
    headers = ['Entry Price', 'SL Level', 'Target Level', 'Risk (Pts)', 'Reward (Pts)', 'R:R Ratio', 'Lot', 'Order Type', 'Status']
    
    print("\n📊 TEST SCENARIOS - Order Block Calculation:")
    print("─" * 120)
    format_table(headers, test_data)
    print("─" * 120)
    
    # Save to CSV
    csv_filename = "order_block_verification.csv"
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(test_data)
    print(f"\n✅ CSV saved: {csv_filename}")
    
    # Sample transaction verification
    print("\n" + "=" * 120)
    print("DETAILED TRANSACTION EXAMPLE - Entry at 20450.75")
    print("=" * 120)
    
    entry = 20450.75
    order = CustomOrderBlock.create_order(entry, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    print(f"\n📍 ENTRY SETUP:")
    print(f"   Entry Price (NIFTY): {order['Entry Price']:.2f}")
    print(f"   Order Type: {order['Order Type']}")
    print(f"   Lot Size: {order['Lot Size']}")
    
    print(f"\n🎯 ORDER PARAMETERS:")
    print(f"   Stop Loss (SL): {order['SL Level']:.2f}")
    print(f"      └─ SL = Entry + {CustomOrderBlock.SL_DISTANCE} points")
    print(f"      └─ SL = {entry:.2f} + {CustomOrderBlock.SL_DISTANCE} = {order['SL Level']:.2f}")
    
    print(f"\n🏁 TARGET:")
    print(f"   Target: {order['Target Level']:.2f}")
    print(f"      └─ Target = Entry - {CustomOrderBlock.TARGET_DISTANCE} points")
    print(f"      └─ Target = {entry:.2f} - {CustomOrderBlock.TARGET_DISTANCE} = {order['Target Level']:.2f}")
    
    print(f"\n💰 RISK/REWARD:")
    print(f"   Risk: {order['Risk (Points)']} points")
    print(f"   Reward: {order['Reward (Points)']} points")
    print(f"   Risk:Reward Ratio: {order['R:R Ratio']}")
    
    # Calculate hypothetical P&L
    print(f"\n" + "─" * 120)
    print("HYPOTHETICAL OUTCOMES:")
    print("─" * 120)
    
    outcomes = [
        ("Best Case (Hit Target)", order['Target Level'], order['Reward (Points)']),
        ("Worst Case (Hit SL)", order['SL Level'], -order['Risk (Points)']),
        ("Mid Exit (Midway)", (entry + order['Target Level']) / 2, 
         entry - (entry + order['Target Level']) / 2),
    ]
    
    for scenario, exit_price, pnl in outcomes:
        pnl_sign = f"+{pnl:.2f}" if pnl >= 0 else f"{pnl:.2f}"
        emoji = "✅" if pnl > 0 else "❌" if pnl < 0 else "⏳"
        print(f"  {emoji} {scenario}: Exit @ {exit_price:.2f} | P&L: {pnl_sign} points")
    
    print("─" * 120)
    
    # Create extended test cases CSV
    print("\n📄 Creating detailed verification CSV...")
    
    extended_entries = [
        ("Very Low", 19800.00),
        ("Low", 20000.00),
        ("Medium-Low", 20200.50),
        ("Medium (Typical)", 20450.75),
        ("Medium-High", 20600.25),
        ("High", 20800.00),
        ("Very High", 21000.50),
    ]
    
    extended_data = []
    for category, entry_price in extended_entries:
        order = CustomOrderBlock.create_order(entry_price, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        extended_data.append([
            category,
            f"{entry_price:.2f}",
            f"{order['SL Level']:.2f}",
            f"{order['Target Level']:.2f}",
            f"{order['SL Level'] - entry_price:.0f}",
            f"{entry_price - order['Target Level']:.0f}",
            f"{order['Risk (Points)']}",
            f"{order['Reward (Points)']}",
            order['R:R Ratio'],
            f"-{order['Risk (Points)']} pts",
            f"+{order['Reward (Points)']} pts",
        ])
    
    extended_headers = [
        'Entry Category',
        'Entry Price',
        'SL Level',
        'Target Level',
        'Distance Entry to SL',
        'Distance Entry to Target',
        'Risk Points',
        'Reward Points',
        'Risk:Reward',
        'Max Loss Scenario',
        'Max Win Scenario',
    ]
    
    extended_csv_filename = "order_block_extended_verification.csv"
    with open(extended_csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(extended_headers)
        writer.writerows(extended_data)
    
    print(f"\n✅ Detailed CSV created: {extended_csv_filename}")
    
    print("\n" + "=" * 120)
    print("✅ ORDER BLOCK VERIFICATION COMPLETE")
    print("=" * 120)
    print("\nTo integrate this into Strategy_01, update Config class with:")
    print("""
    # ── Custom Order Block Parameters ────────────────────┐
    USE_FIXED_ORDER_BLOCK = True        # Enable custom order block
    ORDER_SL_DISTANCE = 20              # SL points above entry
    ORDER_TARGET_DISTANCE = 60          # Target points below entry
    ORDER_LOT_SIZE = 1                  # Lot size
    """)
    
    print("\n📋 Summary of created files:")
    print("   1. order_block_verification.csv - Basic test scenarios")
    print("   2. order_block_extended_verification.csv - Extended range test")
    print("\n✅ Review these CSV files to verify the order block is correct!")


if __name__ == "__main__":
    verify_order_block()
