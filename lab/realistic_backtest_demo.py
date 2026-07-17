# realistic_backtest_demo.py - Demo of enhanced backtesting with spread consideration
import os
import sys
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load project environment
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
load_dotenv(os.path.join(project_root, '.env'))

def enhance_backtest_with_spread(df, spread_pips=2.0):
    """
    Enhance historical data with realistic spread modeling
    
    Args:
        df: Historical OHLC data
        spread_pips: Average spread in pips (default 2.0 for major pairs)
    
    Returns:
        Enhanced DataFrame with bid/ask prices
    """
    df = df.copy()
    
    # Determine pip size based on price level
    if df['close'].mean() > 100:  # Likely JPY pair or gold/indices
        pip_size = 0.01
    else:  # Major forex pairs
        pip_size = 0.0001
    
    spread_in_price = spread_pips * pip_size
    
    # Add realistic bid/ask spread
    df['bid'] = df['close'] - (spread_in_price / 2)
    df['ask'] = df['close'] + (spread_in_price / 2)
    
    # Adjust OHLC for bid/ask
    df['bid_high'] = df['high'] - (spread_in_price / 2)
    df['bid_low'] = df['low'] - (spread_in_price / 2)
    df['ask_high'] = df['high'] + (spread_in_price / 2)
    df['ask_low'] = df['low'] + (spread_in_price / 2)
    
    return df

def realistic_trade_execution(signal, current_bar, spread_pips=2.0):
    """
    Simulate realistic trade execution with spread costs
    
    Args:
        signal: 'BUY' or 'SELL'
        current_bar: Current price data
        spread_pips: Spread in pips
    
    Returns:
        Realistic entry price considering spread
    """
    # Determine pip size
    close_price = current_bar['close']
    if close_price > 100:
        pip_size = 0.01
    else:
        pip_size = 0.0001
    
    spread_in_price = spread_pips * pip_size
    
    if signal == 'BUY':
        # Buy at ask price (higher)
        entry_price = close_price + (spread_in_price / 2)
    else:  # SELL
        # Sell at bid price (lower) 
        entry_price = close_price - (spread_in_price / 2)
    
    return entry_price

def calculate_spread_cost(df, trades_per_month=20):
    """
    Calculate total spread costs for a trading period
    
    Args:
        df: Historical data
        trades_per_month: Average number of trades per month
    
    Returns:
        Estimated spread costs
    """
    # Estimate based on data timeframe
    total_hours = len(df)
    months = total_hours / (24 * 30)  # Rough estimate
    total_trades = trades_per_month * months
    
    # Average spread cost per trade (round trip)
    avg_price = df['close'].mean()
    if avg_price > 100:
        pip_size = 0.01
        spread_pips = 20  # Higher spread for gold/indices
    else:
        pip_size = 0.0001
        spread_pips = 2   # Typical for major pairs
    
    spread_cost_per_trade = spread_pips * pip_size * 2  # Round trip
    total_spread_cost = total_trades * spread_cost_per_trade
    
    # Convert to dollar equivalent (rough estimate)
    if avg_price > 1000:  # Gold
        dollar_per_pip = 1.0  # $1 per pip for 0.01 lot
    else:  # Forex
        dollar_per_pip = 1.0  # $1 per pip for 0.01 lot
    
    total_cost_usd = total_trades * spread_pips * dollar_per_pip
    
    return {
        'total_trades': int(total_trades),
        'spread_pips': spread_pips,
        'cost_per_trade_usd': spread_pips * dollar_per_pip,
        'total_cost_usd': total_cost_usd
    }

def demo_spread_impact():
    """Demonstrate the impact of spread on backtesting results"""
    
    print("💰 Spread Impact Analysis for QuantumBotX Backtesting")
    print("=" * 60)
    
    # Check if we have any CSV files to analyze
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'data' in f]
    
    if not csv_files:
        print("❌ No CSV data files found. Please run download_data.py first.")
        return
    
    # Analyze a few different instruments
    instruments_to_analyze = ['EURUSD', 'XAUUSD', 'GBPUSD', 'USDJPY']
    available_files = []
    
    for instrument in instruments_to_analyze:
        matching_files = [f for f in csv_files if instrument in f.upper()]
        if matching_files:
            available_files.append((instrument, matching_files[0]))
    
    if not available_files:
        print("❌ No recognized instrument files found.")
        print(f"Available files: {csv_files[:5]}")
        return
    
    print(f"🔍 Analyzing {len(available_files)} instruments:")
    
    for instrument, filename in available_files:
        print(f"\n📊 {instrument} Analysis ({filename})")
        print("-" * 40)
        
        try:
            # Load the data
            df = pd.read_csv(filename)
            
            # Skip if wrong format
            if 'close' not in df.columns:
                print(f"   ⚠️ Skipping - wrong format (needs cleaning)")
                continue
            
            # Calculate spread impact
            spread_analysis = calculate_spread_cost(df)
            avg_price = df['close'].mean()
            
            print(f"   📈 Average Price: {avg_price:.4f}")
            print(f"   📅 Data Points: {len(df)} hours")
            print(f"   🎯 Estimated Monthly Trades: {spread_analysis['total_trades']//int(len(df)/(24*30))}")
            print(f"   💸 Spread: {spread_analysis['spread_pips']} pips")
            print(f"   💰 Cost per Trade: ${spread_analysis['cost_per_trade_usd']:.2f}")
            print(f"   📊 Total Spread Cost: ${spread_analysis['total_cost_usd']:.2f}")
            
            # Show impact on profitability
            if spread_analysis['total_cost_usd'] > 500:
                print(f"   ⚠️ HIGH IMPACT: Spread costs could significantly affect results")
            elif spread_analysis['total_cost_usd'] > 200:
                print(f"   ⚠️ MEDIUM IMPACT: Moderate spread cost consideration needed")
            else:
                print(f"   ✅ LOW IMPACT: Spread costs are manageable")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {filename}: {e}")
    
    print(f"\n💡 Recommendations:")
    print(f"   1. XAUUSD: High spreads (15-30 pips) - major impact on scalping")
    print(f"   2. Major Forex: Low spreads (1-3 pips) - minor impact")
    print(f"   3. Consider adding spread modeling to backtesting")
    print(f"   4. Test with your actual broker's spreads")
    
    print(f"\n🔧 Your Current Backtesting Engine:")
    print(f"   ✅ Uses close prices (reasonable approximation)")
    print(f"   ❌ Ignores spread costs (optimistic results)")
    print(f"   ❌ Assumes perfect execution (no slippage)")
    print(f"   ❌ No swap/commission costs")
    
    print(f"\n📈 Reality Check:")
    print(f"   • Backtesting profits may be 10-30% higher than reality")
    print(f"   • High-frequency strategies most affected")
    print(f"   • Gold trading especially impacted by spreads")

if __name__ == "__main__":
    # Change to lab directory
    lab_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(lab_dir)
    
    demo_spread_impact()