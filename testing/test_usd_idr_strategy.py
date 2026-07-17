#!/usr/bin/env python3
"""
🇮🇩 Quick USD/IDR Strategy Test
Perfect for Indonesian traders to earn USD!
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_usd_idr_data():
    """Generate realistic USD/IDR data"""
    print("💱 Generating USD/IDR Market Data...")
    
    # Base rate around 15,400 IDR per USD
    base_rate = 15400
    
    # Generate 30 days of hourly data
    dates = pd.date_range(end=datetime.now(), periods=720, freq='H')  # 30 days * 24 hours
    
    # USD/IDR volatility (around 0.5% daily)
    daily_vol = 0.005
    hourly_vol = daily_vol / (24 ** 0.5)
    
    # Generate realistic price movements
    returns = np.random.randn(720) * hourly_vol
    
    # Add some trend (USD slightly strengthening)
    trend = np.linspace(0, 0.02, 720)  # 2% appreciation over 30 days
    returns += trend / 720
    
    # Calculate prices
    prices = base_rate * (1 + returns).cumprod()
    
    # Create OHLCV data
    df = pd.DataFrame({
        'time': dates,
        'open': prices,
        'high': prices * (1 + np.random.uniform(0, 0.002, 720)),
        'low': prices * (1 - np.random.uniform(0, 0.002, 720)),
        'close': prices,
        'volume': np.random.randint(1000, 5000, 720)
    })
    
    # Ensure OHLC integrity
    df['high'] = df[['high', 'close', 'open']].max(axis=1)
    df['low'] = df[['low', 'close', 'open']].min(axis=1)
    
    return df

def calculate_ma_crossover_signals(df):
    """Simple MA crossover strategy for USD/IDR"""
    print("🤖 Calculating Moving Average Crossover Signals...")
    
    # Calculate moving averages
    df['ma_fast'] = df['close'].rolling(window=20).mean()  # 20-hour MA
    df['ma_slow'] = df['close'].rolling(window=50).mean()  # 50-hour MA
    
    # Generate signals
    df['signal'] = 0
    df['signal'][20:] = np.where(df['ma_fast'][20:] > df['ma_slow'][20:], 1, 0)
    df['position'] = df['signal'].diff()
    
    return df

def simulate_trading_results(df):
    """Simulate trading results for USD/IDR"""
    print("📊 Simulating Trading Results...")
    
    capital = 10000  # $10,000 starting capital
    position_size = 0.1  # 0.1 lot = $1,000 per trade
    
    trades = []
    current_position = 0
    entry_price = 0
    
    for i, row in df.iterrows():
        if row['position'] == 1 and current_position == 0:  # Buy signal
            current_position = 1
            entry_price = row['close']
            trades.append({
                'type': 'entry',
                'time': row['time'],
                'price': entry_price,
                'side': 'buy'
            })
        elif row['position'] == -1 and current_position == 1:  # Sell signal
            current_position = 0
            exit_price = row['close']
            
            # Calculate profit in USD
            # For USD/IDR, we're buying USD with IDR
            # Profit = (exit_rate - entry_rate) / entry_rate * position_size
            profit_pct = (exit_price - entry_price) / entry_price
            profit_usd = profit_pct * position_size * capital
            
            trades.append({
                'type': 'exit',
                'time': row['time'],
                'price': exit_price,
                'side': 'sell',
                'profit_usd': profit_usd,
                'profit_idr': profit_usd * exit_price
            })
    
    return trades

def analyze_performance(trades):
    """Analyze trading performance"""
    print("📈 Analyzing Performance...")
    
    exit_trades = [t for t in trades if t['type'] == 'exit']
    
    if not exit_trades:
        print("❌ No completed trades in the period")
        return
    
    total_profit_usd = sum(t['profit_usd'] for t in exit_trades)
    total_profit_idr = sum(t['profit_idr'] for t in exit_trades)
    
    winning_trades = [t for t in exit_trades if t['profit_usd'] > 0]
    losing_trades = [t for t in exit_trades if t['profit_usd'] < 0]
    
    win_rate = len(winning_trades) / len(exit_trades) * 100
    
    print(f"\\n📊 USD/IDR Trading Results (30 days):")
    print(f"   Total Trades: {len(exit_trades)}")
    print(f"   Winning Trades: {len(winning_trades)}")
    print(f"   Losing Trades: {len(losing_trades)}")
    print(f"   Win Rate: {win_rate:.1f}%")
    print(f"   \\n💰 Profit Summary:")
    print(f"   Total Profit: ${total_profit_usd:+.2f} USD")
    print(f"   Total Profit: {total_profit_idr:+,.0f} IDR")
    print(f"   Monthly Return: {(total_profit_usd / 10000) * 100:.1f}%")
    
    if total_profit_usd > 0:
        print(f"   \\n🎉 SUCCESS! You earned USD while living in Indonesia!")
        print(f"   This is {total_profit_idr:,.0f} IDR in your local currency!")
    else:
        print(f"   \\n⚠️ Loss in this period, but that's normal in trading!")
        print(f"   Adjust strategy parameters and try again!")

def show_indonesian_advantages():
    """Show why USD/IDR is perfect for Indonesian traders"""
    print(f"\\n🇮🇩 Why USD/IDR Trading is PERFECT for You:")
    print(f"=" * 50)
    
    advantages = [
        "💰 Earn USD while living in Indonesia",
        "🌅 Trade during Indonesian business hours",
        "📈 Benefit from IDR volatility patterns",
        "🛡️ Hedge against IDR devaluation",
        "💸 Lower capital requirements than stocks",
        "⚡ High liquidity - easy entry/exit",
        "📊 Understand local economic factors",
        "🏦 Multiple broker options available"
    ]
    
    for advantage in advantages:
        print(f"  ✅ {advantage}")
    
    print(f"\\n🚀 BOTTOM LINE:")
    print(f"USD/IDR trading lets you earn the world's reserve currency")
    print(f"while understanding the local Indonesian economy better than")
    print(f"foreign traders. That's your competitive advantage! 💪")

def main():
    """Main USD/IDR strategy test"""
    print("🇮🇩 USD/IDR Strategy Test for Indonesian Traders")
    print("=" * 60)
    print("Testing how your QuantumBotX can earn USD income!")
    print()
    
    # Generate data
    df = generate_usd_idr_data()
    print(f"✅ Generated {len(df)} data points")
    print(f"📊 Rate Range: {df['close'].min():,.0f} - {df['close'].max():,.0f} IDR")
    
    # Calculate signals
    df = calculate_ma_crossover_signals(df)
    signals = df[df['position'] != 0]
    print(f"🎯 Generated {len(signals)} trading signals")
    
    # Simulate trading
    trades = simulate_trading_results(df)
    
    # Analyze performance
    analyze_performance(trades)
    
    # Show advantages
    show_indonesian_advantages()
    
    print(f"\\n" + "=" * 60)
    print(f"🎯 NEXT: Connect to XM Indonesia and trade for REAL!")
    print(f"=" * 60)

if __name__ == "__main__":
    main()