# core/strategies/index_optimizations.py

"""
股指策略優化
為交易 US30、US100、US500、DE30 等股指提供優化參數
"""

# 針對股指市場特徵優化的策略參數
INDEX_STRATEGY_PARAMS = {
    'MA_CROSSOVER': {
        'US30': {
            'fast_period': 12,
            'slow_period': 26,
            'risk_percent': 0.5,
            'description': '道瓊 - 工業重點，適度波動'
        },
        'US100': {
            'fast_period': 10,
            'slow_period': 22,
            'risk_percent': 0.7,
            'description': '納斯達克 - 科技權重，較高波動'
        },
        'US500': {
            'fast_period': 12,
            'slow_period': 26,
            'risk_percent': 0.5,
            'description': '標普500 - 廣泛市場，均衡策略'
        },
        'DE30': {
            'fast_period': 14,
            'slow_period': 30,
            'risk_percent': 0.4,
            'description': '德國DAX - 歐洲市場，保守策略'
        }
    },
    
    'TURTLE_BREAKOUT': {
        'US30': {
            'entry_period': 15,
            'exit_period': 8,
            'risk_percent': 0.6,
            'description': '道瓊突破 - 已確立的趨勢'
        },
        'US100': {
            'entry_period': 12,
            'exit_period': 6,
            'risk_percent': 0.8,
            'description': '納斯達克突破 - 快速移動'
        },
        'US500': {
            'entry_period': 15,
            'exit_period': 8,
            'risk_percent': 0.6,
            'description': '標普突破 - 廣泛市場動量'
        },
        'DE30': {
            'entry_period': 18,
            'exit_period': 10,
            'risk_percent': 0.5,
            'description': '德國DAX突破 - 歐洲交易時段'
        }
    },
    
    'QUANTUMBOTX_HYBRID': {
        'US30': {
            'adx_period': 12,
            'adx_threshold': 22,
            'ma_fast_period': 12,
            'ma_slow_period': 26,
            'bb_length': 18,
            'risk_percent': 0.5,
            'description': '自適應道瓊交易'
        },
        'US100': {
            'adx_period': 10,
            'adx_threshold': 24,
            'ma_fast_period': 10,
            'ma_slow_period': 22,
            'bb_length': 16,
            'risk_percent': 0.7,
            'description': '自適應納斯達克 - 更高靈敏度'
        },
        'US500': {
            'adx_period': 12,
            'adx_threshold': 22,
            'ma_fast_period': 12,
            'ma_slow_period': 26,
            'bb_length': 18,
            'risk_percent': 0.5,
            'description': '自適應標普500'
        },
        'DE30': {
            'adx_period': 14,
            'adx_threshold': 20,
            'ma_fast_period': 14,
            'ma_slow_period': 30,
            'bb_length': 20,
            'risk_percent': 0.4,
            'description': '自適應德國DAX - 歐洲交易時段'
        }
    },
    
    'BOLLINGER_SQUEEZE': {
        'US30': {
            'bb_length': 16,
            'bb_std': 2.0,
            'squeeze_factor': 0.75,
            'squeeze_window': 8,
            'risk_percent': 0.6,
            'description': '道瓊波動率壓縮'
        },
        'US100': {
            'bb_length': 14,
            'bb_std': 2.2,
            'squeeze_factor': 0.8,
            'squeeze_window': 6,
            'risk_percent': 0.8,
            'description': '納斯達克壓縮 - 科技波動率'
        },
        'US500': {
            'bb_length': 16,
            'bb_std': 2.0,
            'squeeze_factor': 0.75,
            'squeeze_window': 8,
            'risk_percent': 0.6,
            'description': '標普壓縮交易'
        },
        'DE30': {
            'bb_length': 18,
            'bb_std': 1.8,
            'squeeze_factor': 0.7,
            'squeeze_window': 10,
            'risk_percent': 0.5,
            'description': '德國DAX壓縮 - 歐洲時段'
        }
    }
}

# 不同股指的交易時段限制
INDEX_TRADING_HOURS = {
    'US30': {
        'market_open': '14:30',  # UTC
        'market_close': '21:00',  # UTC
        'pre_market': '08:00',   # UTC
        'post_market': '00:00',  # UTC next day
        'timezone': 'Eastern'
    },
    'US100': {
        'market_open': '14:30',
        'market_close': '21:00',
        'pre_market': '08:00',
        'post_market': '00:00',
        'timezone': 'Eastern'
    },
    'US500': {
        'market_open': '14:30',
        'market_close': '21:00',
        'pre_market': '08:00',
        'post_market': '00:00',
        'timezone': 'Eastern'
    },
    'DE30': {
        'market_open': '07:00',  # UTC
        'market_close': '15:30',  # UTC
        'pre_market': '06:00',
        'post_market': '16:00',
        'timezone': 'CET'
    }
}

# 股指風險管理調整
INDEX_RISK_ADJUSTMENTS = {
    'gap_protection': {
        'enabled': True,
        'max_overnight_exposure': 50,  # % of normal position
        'description': '市場收盤前減小倉位'
    },
    'news_filter': {
        'enabled': True,
        'avoid_news_minutes': 30,  # Minutes before/after major news
        'description': '避免在重大經濟公告期間交易'
    },
    'volatility_filter': {
        'max_atr_multiplier': 3.0,  # Skip trades if ATR too high
        'description': '在極端波動期間跳過交易'
    }
}

def get_index_params(strategy_name, symbol):
    """
    Get optimized parameters for a specific strategy and index
    
    Args:
        strategy_name (str): Strategy identifier (e.g., 'MA_CROSSOVER')
        symbol (str): Index symbol (e.g., 'US30')
    
    Returns:
        dict: Optimized parameters for the strategy-symbol combination
    """
    return INDEX_STRATEGY_PARAMS.get(strategy_name, {}).get(symbol, {})

def get_trading_hours(symbol):
    """Get trading hours for a specific index"""
    return INDEX_TRADING_HOURS.get(symbol, {})

def get_risk_adjustments():
    """Get index-specific risk management rules"""
    return INDEX_RISK_ADJUSTMENTS

def is_index_symbol(symbol):
    """Check if symbol is a stock index"""
    return symbol.upper() in ['US30', 'US100', 'US500', 'DE30', 'UK100', 'JP225', 'AUS200']

def get_recommended_strategies_for_index(symbol):
    """Get recommended strategies for a specific index, sorted by suitability"""
    recommendations = {
        'US30': [
            ('MA_CROSSOVER', '道瓊趨勢極佳'),
            ('TURTLE_BREAKOUT', '適合已確立的走勢'),
            ('QUANTUMBOTX_HYBRID', '適應所有市場狀態')
        ],
        'US100': [
            ('TURTLE_BREAKOUT', '科技波動率策略首選'),
            ('BOLLINGER_SQUEEZE', '納斯達克缺口交易極佳'),
            ('MA_CROSSOVER', '適合趨勢階段')
        ],
        'US500': [
            ('QUANTUMBOTX_HYBRID', '廣泛市場最優選擇'),
            ('MA_CROSSOVER', '趨勢跟蹤極佳'),
            ('TURTLE_BREAKOUT', '動量捕捉良好')
        ],
        'DE30': [
            ('MA_CROSSOVER', '保守的歐洲策略'),
            ('QUANTUMBOTX_HYBRID', '適應德國DAX模式'),
            ('BOLLINGER_SQUEEZE', '歐洲交易時段波動率')
        ]
    }
    
    return recommendations.get(symbol.upper(), [])

# 股指交易的漸進學習路徑
INDEX_LEARNING_PATH = [
    {
        'week': 1,
        'strategy': 'MA_CROSSOVER',
        'symbol': 'US30',
        'description': '從道瓊的簡單趨勢跟蹤開始',
        'risk': 0.3,
        'focus': '學習股指行為 vs 外匯'
    },
    {
        'week': 2,
        'strategy': 'MA_CROSSOVER',
        'symbol': 'US500',
        'description': '擴展到更廣泛的標普500市場',
        'risk': 0.4,
        'focus': '比較不同股指的特性'
    },
    {
        'week': 3,
        'strategy': 'TURTLE_BREAKOUT',
        'symbol': 'US100',
        'description': '在高波動納斯達克上學習突破交易',
        'risk': 0.5,
        'focus': '理解科技板塊動態'
    },
    {
        'week': 4,
        'strategy': 'QUANTUMBOTX_HYBRID',
        'symbol': 'US500',
        'description': '在成熟市場部署自適應策略',
        'risk': 0.5,
        'focus': '多條件自適應'
    },
    {
        'week': 5,
        'strategy': 'BOLLINGER_SQUEEZE',
        'symbol': 'DE30',
        'description': '歐洲市場的波動率交易',
        'risk': 0.4,
        'focus': '不同的時區和波動率模式'
    }
]

def get_learning_path():
    """Get the progressive learning path for index trading"""
    return INDEX_LEARNING_PATH