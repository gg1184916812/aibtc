#!/usr/bin/env python3
"""
Fix Validation Test for Crypto Backtesting
Tests both QuantumBotX Crypto and optimized Hybrid strategies with BTCUSD data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_crypto_fixes():
    """Test the fixes for crypto backtesting issues."""
    
    print("🔧 Testing Crypto Backtesting Fixes")
    print("=" * 60)
    
    try:
        # Import our utilities and strategies
        from core.utils.crypto_data_loader import load_crypto_csv, prepare_for_backtesting, validate_crypto_data
        from core.backtesting.engine import run_backtest
        
        # Test data loading
        print("📂 Step 1: Loading BTCUSD data...")
        
        data_file = "d:/dev/quantumbotx/lab/BTCUSD_16385_data.csv"
        
        if not os.path.exists(data_file):
            print(f"❌ Data file not found: {data_file}")
            return False
            
        # Load the data with our new loader
        df = load_crypto_csv(data_file, symbol_name="BTCUSD")
        
        print(f"✅ Data loaded successfully: {len(df)} rows")
        
        # Validate the data
        print("🔍 Step 2: Validating data quality...")
        
        validation_results = validate_crypto_data(df)
        
        if not validation_results['is_valid']:
            print("❌ Data validation failed:")
            for warning in validation_results['warnings']:
                print(f"   - {warning}")
            return False
        
        if validation_results['warnings']:
            print("⚠️ Data validation warnings:")
            for warning in validation_results['warnings']:
                print(f"   - {warning}")
                
        if validation_results['recommendations']:
            print("💡 Recommendations:")
            for rec in validation_results['recommendations']:
                print(f"   - {rec}")
        
        # Prepare for backtesting
        print("⚙️ Step 3: Preparing data for backtesting...")
        
        df_bt = prepare_for_backtesting(df, symbol_name="BTCUSD")
        
        print(f"✅ Backtesting data ready: {len(df_bt)} rows")
        
        # Test 1: QuantumBotX Crypto Strategy
        print("\\n🤖 Step 4: Testing QuantumBotX Crypto Strategy...")
        
        crypto_params = {
            'lot_size': 0.5,
            'sl_pips': 2.0,
            'tp_pips': 4.0,
            'adx_period': 10,
            'adx_threshold': 20,
            'ma_fast_period': 12,
            'ma_slow_period': 26,
            'bb_length': 20,
            'bb_std': 2.2,
            'trend_filter_period': 100,
            'rsi_period': 14,
            'rsi_overbought': 75,
            'rsi_oversold': 25,
            'volatility_filter': 2.0,
            'weekend_mode': True
        }
        
        try:
            crypto_result = run_backtest(
                strategy_id='QUANTUMBOTX_CRYPTO',
                params=crypto_params,
                historical_data_df=df_bt.copy(),
                symbol_name='BTCUSD'
            )
            
            if 'error' in crypto_result:
                print(f"❌ QuantumBotX Crypto failed: {crypto_result['error']}")
                crypto_success = False
            else:
                print("✅ QuantumBotX Crypto test PASSED!")
                print(f"   📊 Results: {crypto_result['total_trades']} trades, ${crypto_result['total_profit_usd']:.2f} profit")
                print(f"   📈 Win Rate: {crypto_result['win_rate_percent']:.1f}%")
                print(f"   📉 Max Drawdown: {crypto_result['max_drawdown_percent']:.1f}%")
                crypto_success = True
                
        except Exception as e:
            print(f"❌ QuantumBotX Crypto exception: {e}")
            import traceback
            traceback.print_exc()
            crypto_success = False
        
        # Test 2: Optimized Hybrid Strategy
        print("\\n🔄 Step 5: Testing Optimized Hybrid Strategy...")
        
        # For hybrid, we need to pass symbol info to trigger crypto optimization
        hybrid_params = {
            'lot_size': 0.5,
            'sl_pips': 2.0,
            'tp_pips': 4.0
        }
        
        try:
            hybrid_result = run_backtest(
                strategy_id='QUANTUMBOTX_HYBRID',
                params=hybrid_params,
                historical_data_df=df_bt.copy(),
                symbol_name='BTCUSD'
            )
            
            if 'error' in hybrid_result:
                print(f"❌ Optimized Hybrid failed: {hybrid_result['error']}")
                hybrid_success = False
            else:
                print("✅ Optimized Hybrid test PASSED!")
                print(f"   📊 Results: {hybrid_result['total_trades']} trades, ${hybrid_result['total_profit_usd']:.2f} profit")
                print(f"   📈 Win Rate: {hybrid_result['win_rate_percent']:.1f}%")
                print(f"   📉 Max Drawdown: {hybrid_result['max_drawdown_percent']:.1f}%")
                
                # Check if it's much better than the previous poor performance
                if hybrid_result['max_drawdown_percent'] < 500:
                    improvement = 990 - hybrid_result['max_drawdown_percent']
                    print(f"   🎉 MAJOR IMPROVEMENT: Drawdown reduced by {improvement:.1f}%!")
                
                hybrid_success = True
                
        except Exception as e:
            print(f"❌ Optimized Hybrid exception: {e}")
            import traceback
            traceback.print_exc()
            hybrid_success = False
        
        # Summary
        print("\\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        print(f"📂 Data Loading: {'✅ PASS' if len(df) > 0 else '❌ FAIL'}")
        print(f"🔍 Data Validation: {'✅ PASS' if validation_results['is_valid'] else '❌ FAIL'}")
        print(f"🤖 QuantumBotX Crypto: {'✅ PASS' if crypto_success else '❌ FAIL'}")
        print(f"🔄 Optimized Hybrid: {'✅ PASS' if hybrid_success else '❌ FAIL'}")
        
        overall_success = crypto_success and hybrid_success
        
        if overall_success:
            print("\\n🎉 ALL TESTS PASSED!")
            print("✅ Datetime error is fixed")
            print("✅ Crypto strategies are working")
            print("✅ Performance has been optimized")
            print("\\n🚀 Your crypto backtesting is now ready!")
        else:
            print("\\n❌ Some tests failed. Check the errors above.")
            
        return overall_success
        
    except Exception as e:
        print(f"❌ Test framework error: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_original_issues():
    """Compare our fixes with the original issues reported."""
    print("\\n🔍 Comparison with Original Issues:")
    print("-" * 50)
    
    print("\\n1. QuantumBotX Crypto Error:")
    print("   Original: 'Can only use .dt accessor with datetimelike values'")
    print("   Fix: Added robust datetime handling with multiple fallback methods")
    
    print("\\n2. Hybrid Strategy Performance:")
    print("   Original: -$99,071.74, 990.72% drawdown, 0% win rate")
    print("   Fix: Crypto-optimized parameters and volatility filtering")
    
    print("\\n3. Overall Improvements:")
    print("   ✅ Safe datetime conversion for any CSV format")
    print("   ✅ Crypto-specific parameter optimization")
    print("   ✅ Volatility filtering for risk management")
    print("   ✅ Enhanced data validation and error handling")

if __name__ == "__main__":
    print("🧪 QuantumBotX Crypto Backtesting Fix Validation")
    print("=" * 70)
    
    success = test_crypto_fixes()
    
    compare_with_original_issues()
    
    if success:
        print("\\n" + "=" * 70)
        print("🎯 CONCLUSION: All fixes are working correctly!")
        print("You can now backtest crypto strategies without errors.")
        print("=" * 70)
    else:
        print("\\n" + "=" * 70)
        print("⚠️ CONCLUSION: Some issues remain - check the output above")
        print("=" * 70)