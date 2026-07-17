#!/usr/bin/env python3
"""
🔧 Index Strategy Testing Suite
Tests the new INDEX_MOMENTUM and INDEX_BREAKOUT_PRO strategies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def generate_index_test_data(symbol='US500', periods=500):
    """Generate realistic index test data"""
    print(f"📊 Generating {periods} periods of {symbol} test data...")
    
    # Base prices for different indices
    base_prices = {
        'US30': 34500,
        'US100': 15800,
        'US500': 4350,
        'DE30': 16200
    }
    
    base_price = base_prices.get(symbol, 4350)
    
    # Generate realistic index movement
    dates = pd.date_range(start='2024-01-01', periods=periods, freq='h')
    
    # More volatile than forex but less than crypto
    returns = np.random.randn(periods) * 0.008  # 0.8% hourly volatility
    
    # Add trend component
    trend = np.sin(np.linspace(0, 4*np.pi, periods)) * 0.002
    returns += trend
    
    # Calculate prices
    price_multipliers = (1 + returns).cumprod()
    close_prices = pd.Series(base_price * price_multipliers, index=dates)
    
    # Generate OHLC data
    df = pd.DataFrame({
        'time': dates,
        'open': close_prices.shift(1).fillna(base_price),
        'close': close_prices
    })
    
    # Generate high/low with realistic spreads
    df['high'] = np.maximum(df['open'], df['close']) * (1 + np.random.uniform(0.0005, 0.002, periods))
    df['low'] = np.minimum(df['open'], df['close']) * (1 - np.random.uniform(0.0005, 0.002, periods))
    
    # Generate volume (higher during market hours)
    base_volume = np.random.randint(800, 1500, periods)
    # Simulate higher volume during NY session (14:30-21:00 UTC)
    hour_factor = [1.5 if 14 <= h <= 21 else 0.8 for h in dates.hour]  # pyright: ignore
    df['tick_volume'] = base_volume * hour_factor
    
    # Ensure OHLC integrity
    df['high'] = df[['high', 'close', 'open']].max(axis=1)
    df['low'] = df[['low', 'close', 'open']].min(axis=1)
    
    return df

def test_index_momentum_strategy():
    """Test the INDEX_MOMENTUM strategy"""
    print("\n🎯 Testing INDEX_MOMENTUM Strategy")
    print("=" * 50)
    
    try:
        from core.strategies.index_momentum import IndexMomentumStrategy
        
        # Create mock bot for testing
        class MockBot:
            def __init__(self, symbol):
                self.market_for_mt5 = symbol
                self.name = f"Test Bot ({symbol})"
        
        # Test with different indices
        test_symbols = ['US30', 'US100', 'US500', 'DE30']
        
        for symbol in test_symbols:
            print(f"\n📈 Testing {symbol}...")
            
            # Generate test data
            df = generate_index_test_data(symbol, 200)
            
            # Create strategy instance
            mock_bot = MockBot(symbol)
            strategy = IndexMomentumStrategy(mock_bot)
            
            # Test real-time analysis
            signal_info = strategy.analyze(df)
            
            print(f"   Signal: {signal_info['signal']}")
            print(f"   Price: ${signal_info['price']:.2f}")
            print(f"   Explanation: {signal_info['explanation']}")
            
            # Test backtesting
            print("   🔄 Running backtest analysis...")
            df_with_signals = strategy.analyze_df(df)
            
            # Count signals
            buy_signals = (df_with_signals['signal'] == 'BUY').sum()
            sell_signals = (df_with_signals['signal'] == 'SELL').sum()
            
            print(f"   📊 Backtest Results: {buy_signals} BUY, {sell_signals} SELL signals")
            
            # Test parameters
            print(f"   ⚙️ Definable Parameters: {len(strategy.get_definable_params())} available")
        
        print("✅ INDEX_MOMENTUM strategy test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ INDEX_MOMENTUM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_index_breakout_pro_strategy():
    """Test the INDEX_BREAKOUT_PRO strategy"""
    print("\n🚀 Testing INDEX_BREAKOUT_PRO Strategy")
    print("=" * 50)
    
    try:
        from core.strategies.index_breakout_pro import IndexBreakoutProStrategy
        
        # Create mock bot for testing
        class MockBot:
            def __init__(self, symbol):
                self.market_for_mt5 = symbol
                self.name = f"Pro Test Bot ({symbol})"
        
        # Test with different indices
        test_symbols = ['US30', 'US100', 'US500', 'DE30']
        
        for symbol in test_symbols:
            print(f"\n📈 Testing {symbol} (Professional Analysis)...")
            
            # Generate test data with more periods for advanced analysis
            df = generate_index_test_data(symbol, 300)
            
            # Create strategy instance
            mock_bot = MockBot(symbol)
            strategy = IndexBreakoutProStrategy(mock_bot)
            
            # Test real-time analysis
            signal_info = strategy.analyze(df)
            
            print(f"   Signal: {signal_info['signal']}")
            print(f"   Price: ${signal_info['price']:.2f}")
            print(f"   Analysis: {signal_info['explanation']}")
            
            # Test backtesting
            print("   🔄 Running professional backtest...")
            df_with_signals = strategy.analyze_df(df)
            
            # Count signals
            buy_signals = (df_with_signals['signal'] == 'BUY').sum()
            sell_signals = (df_with_signals['signal'] == 'SELL').sum()
            
            print(f"   📊 Professional Results: {buy_signals} BUY, {sell_signals} SELL signals")
            
            # Show parameter complexity
            params = strategy.get_definable_params()
            print(f"   ⚙️ Professional Parameters: {len(params)} advanced settings")
            
            # Show a few key parameters
            key_params = [p for p in params if p['name'] in ['volume_surge_multiplier', 'institutional_levels']]
            for param in key_params:
                print(f"      • {param['display_name']}: {param['description']}")
        
        print("✅ INDEX_BREAKOUT_PRO strategy test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ INDEX_BREAKOUT_PRO test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_integration():
    """Test integration with strategy map"""
    print("\n🔗 Testing Strategy Map Integration")
    print("=" * 50)
    
    try:
        from core.strategies.strategy_map import (
            STRATEGY_MAP, STRATEGY_METADATA, 
            get_strategies_for_market, get_strategy_info
        )
        
        # Test that new strategies are registered
        print("📋 Checking strategy registration...")
        
        if 'INDEX_MOMENTUM' in STRATEGY_MAP:
            print("   ✅ INDEX_MOMENTUM registered in STRATEGY_MAP")
        else:
            print("   ❌ INDEX_MOMENTUM missing from STRATEGY_MAP")
            return False
        
        if 'INDEX_BREAKOUT_PRO' in STRATEGY_MAP:
            print("   ✅ INDEX_BREAKOUT_PRO registered in STRATEGY_MAP")
        else:
            print("   ❌ INDEX_BREAKOUT_PRO missing from STRATEGY_MAP")
            return False
        
        # Test metadata
        print("\n📊 Checking strategy metadata...")
        
        for strategy_name in ['INDEX_MOMENTUM', 'INDEX_BREAKOUT_PRO']:
            if strategy_name in STRATEGY_METADATA:
                metadata = STRATEGY_METADATA[strategy_name]
                print(f"   ✅ {strategy_name}:")
                print(f"      Difficulty: {metadata['difficulty']}")
                print(f"      Complexity: {metadata['complexity_score']}/12")
                print(f"      Market Types: {metadata['market_types']}")
                print(f"      Description: {metadata['description']}")
            else:
                print(f"   ❌ {strategy_name} missing metadata")
                return False
        
        # Test market type filtering
        print("\n🎯 Testing market type filtering...")
        
        index_strategies = get_strategies_for_market('INDICES')
        print(f"   Strategies for INDICES: {index_strategies}")
        
        # Test with specific index symbols
        us30_strategies = get_strategies_for_market('US30')
        print(f"   Strategies for US30: {us30_strategies}")
        
        if 'INDEX_MOMENTUM' in index_strategies and 'INDEX_BREAKOUT_PRO' in index_strategies:
            print("   ✅ Index strategies correctly filtered")
        else:
            print("   ❌ Index strategy filtering failed")
            return False
        
        # Test strategy info retrieval
        print("\n📖 Testing strategy info retrieval...")
        
        for strategy_name in ['INDEX_MOMENTUM', 'INDEX_BREAKOUT_PRO']:
            info = get_strategy_info(strategy_name)
            if info['strategy_class'] and info['metadata']:
                print(f"   ✅ {strategy_name} info complete")
            else:
                print(f"   ❌ {strategy_name} info incomplete")
                return False
        
        print("✅ Strategy integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Strategy integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_index_specialization():
    """Demonstrate index-specific features"""
    print("\n🎨 Demonstrating Index Specialization")
    print("=" * 50)
    
    print("🔍 INDEX_MOMENTUM Features:")
    print("   • Session-aware trading (market hours detection)")
    print("   • Gap detection and gap fade/follow strategies")
    print("   • Volume-weighted momentum signals")
    print("   • Index-specific volatility adjustments")
    print("   • RSI momentum with volume confirmation")
    
    print("\n🚀 INDEX_BREAKOUT_PRO Features:")
    print("   • Multi-timeframe breakout confirmation")
    print("   • Institutional support/resistance detection")
    print("   • Volume-Price Analysis (VPA)")
    print("   • VWAP trend filtering")
    print("   • Dynamic ATR-based stops and targets")
    print("   • Market structure analysis")
    
    print("\n🎯 Index-Specific Optimizations:")
    print("   • US30: Industrial sector, moderate volatility")
    print("   • US100: Tech-heavy, high volatility, breakout-friendly")
    print("   • US500: Broad market, balanced approach")
    print("   • DE30: European session, conservative parameters")
    
    print("\n📚 Learning Path for Index Trading:")
    print("   Week 1-2: Start with INDEX_MOMENTUM (4/12 complexity)")
    print("   Week 3-4: Master gap trading and session awareness")
    print("   Month 2: Graduate to INDEX_BREAKOUT_PRO (7/12 complexity)")
    print("   Month 3: Professional institutional pattern recognition")

def main():
    """Main test function"""
    print("🔧 Index Strategy Testing Suite")
    print("Testing INDEX_MOMENTUM and INDEX_BREAKOUT_PRO strategies")
    print("=" * 60)
    
    tests = [
        ("Index Momentum Strategy", test_index_momentum_strategy),
        ("Index Breakout Pro Strategy", test_index_breakout_pro_strategy),
        ("Strategy Integration", test_strategy_integration)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL INDEX STRATEGY TESTS PASSED!")
        demonstrate_index_specialization()
        print("\n🚀 Index strategies are ready for FBS testing!")
        print("\n📋 Next Steps:")
        print("1. Switch to FBS broker")
        print("2. Create INDEX_MOMENTUM bot on US30")
        print("3. Test with small position sizes")
        print("4. Graduate to INDEX_BREAKOUT_PRO after gaining experience")
    else:
        print("\n⚠️ Some tests failed - please review errors above")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)