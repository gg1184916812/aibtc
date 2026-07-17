# core/strategies/beginner_defaults.py
"""
初學者的友好策略默認值
為新交易者簡化的參數，附帶教學解釋
"""

# 各策略的初學者優化默認值
BEGINNER_DEFAULTS = {
    # 推薦給初學者（簡單有效）
    'MA_CROSSOVER': {
        'difficulty': '初級',
        'recommended': True,
        'description': '簡單趨勢跟蹤 - 當快線穿越慢線時',
        'params': {
            'fast_period': 10,  # Faster signals for beginners
            'slow_period': 30   # Shorter period for quicker feedback
        },
        'explanation': {
            'fast_period': '快速移動平均線（10 = 對價格變化快速響應）',
            'slow_period': '慢速移動平均線（30 = 顯示主要趨勢方向）'
        }
    },
    
    'RSI_CROSSOVER': {
        'difficulty': '初級',
        'recommended': True,
        'description': '動量交易 - 當動量增強時買入',
        'params': {
            'rsi_period': 14,        # Standard RSI
            'rsi_ma_period': 7,      # Faster MA for more signals
            'trend_filter_period': 30 # Shorter trend filter
        },
        'explanation': {
            'rsi_period': 'RSI 計算周期（14 = 標準）',
            'rsi_ma_period': '平滑 RSI 信號（7 = 響應快）',
            'trend_filter_period': '主要趨勢方向（30 = 近期趨勢）'
        }
    },
    
    'TURTLE_BREAKOUT': {
        'difficulty': '初級',
        'recommended': True,
        'description': '突破交易 - 當價格突破近期高點時買入',
        'params': {
            'entry_period': 15,  # Shorter for more signals
            'exit_period': 8     # Quicker exits
        },
        'explanation': {
            'entry_period': '突破周期（15 = 查看過去 15 根K線）',
            'exit_period': '退出周期（8 = 快速獲利了結）'
        }
    },
    
    # 中級（適合學習）
    'BOLLINGER_REVERSION': {
        'difficulty': '中級',
        'recommended': False,
        'description': '均值回歸 - 當價格從支撐位反彈時買入',
        'params': {
            'bb_length': 20,
            'bb_std': 2.0,
            'trend_filter_period': 50  # Shorter for beginners
        },
        'explanation': {
            'bb_length': '布林帶周期（20 = 標準）',
            'bb_std': '帶寬（2.0 = 覆蓋 95% 的價格波動）',
            'trend_filter_period': '趨勢方向（50 = 中期趨勢）'
        }
    },
    
    'PULSE_SYNC': {
        'difficulty': '中級',
        'recommended': False,
        'description': '多指標確認 - 多個信號必須一致',
        'params': {
            'trend_period': 50,      # Shorter trend
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'stoch_k': 14,
            'stoch_d': 3,
            'stoch_smooth': 3
        },
        'explanation': {
            'trend_period': '主要趨勢（50 = 中期趨勢）',
            'macd_fast': 'MACD 快線（12 = 響應快）',
            'macd_slow': 'MACD 慢線（26 = 穩定）',
            'macd_signal': 'MACD 信號線（9 = 觸發器）',
            'stoch_k': '隨機指標主線（14 = 標準）',
            'stoch_d': '隨機指標信號線（3 = 平滑）',
            'stoch_smooth': '隨機指標平滑（3 = 乾淨信號）'
        }
    },
    
    # 高級（適合有經驗的交易者）
    'QUANTUM_VELOCITY': {
        'difficulty': '高級',
        'recommended': False,
        'description': '波動率突破 - 複雜的壓縮和突破檢測',
        'params': {
            'ema_period': 100,       # Shorter EMA for beginners
            'bb_length': 20,
            'bb_std': 2.0,
            'squeeze_window': 8,     # Shorter window
            'squeeze_factor': 0.8    # Less sensitive
        },
        'explanation': {
            'ema_period': '趨勢過濾器（100 = 長期方向）',
            'bb_length': '布林帶周期（20 = 標準）',
            'bb_std': '帶敏感度（2.0 = 正常）',
            'squeeze_window': '壓縮檢測（8 = 近期壓縮）',
            'squeeze_factor': '壓縮閾值（0.8 = 較不敏感）'
        }
    },
    
    'MERCY_EDGE': {
        'difficulty': '高級',
        'recommended': False,
        'description': 'AI增強多時間框架 - 專業級策略',
        'params': {
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'stoch_k': 14,
            'stoch_d': 3,
            'stoch_smooth': 3
        },
        'explanation': {
            'macd_fast': 'MACD 快線 EMA（12 = 快速響應）',
            'macd_slow': 'MACD 慢線 EMA（26 = 趨勢穩定）',
            'macd_signal': 'MACD 信號線（9 = 入場觸發器）',
            'stoch_k': '隨機指標 K%（14 = 動量周期）',
            'stoch_d': '隨機指標 D%（3 = 信號平滑）',
            'stoch_smooth': 'K% 平滑（3 = 降噪）'
        }
    },
    
    'QUANTUMBOTX_CRYPTO': {
        'difficulty': '專家',
        'recommended': False,
        'description': '加密貨幣專家 - 多指標應對高波動市場',
        'params': {
            'adx_period': 10,
            'adx_threshold': 20,
            'ma_fast_period': 12,
            'ma_slow_period': 26,
            'bb_length': 20,
            'bb_std': 2.2,
            'trend_filter_period': 50,  # Shorter for crypto
            'rsi_period': 14,
            'rsi_overbought': 70,       # Less extreme
            'rsi_oversold': 30,         # Less extreme
            'volatility_filter': 1.5,   # Less sensitive
            'weekend_mode': True
        },
        'explanation': {
            'adx_period': '趨勢強度周期（10 = 加密貨幣響應）',
            'adx_threshold': '最小趨勢強度（20 = 適中）',
            'ma_fast_period': '快速移動平均線（12 = 快速信號）',
            'ma_slow_period': '慢速移動平均線（26 = 趨勢過濾）',
            'bb_length': '布林帶周期（20 = 標準）',
            'bb_std': '帶寬（2.2 = 加密貨幣波動率）',
            'trend_filter_period': '主要趨勢（50 = 加密貨幣優化）',
            'rsi_period': 'RSI 計算（14 = 標準）',
            'rsi_overbought': '賣出閾值（70 = 適中）',
            'rsi_oversold': '買入閾值（30 = 適中）',
            'volatility_filter': '波動率敏感度（1.5 = 平衡）',
            'weekend_mode': '周末調整（True = 更安全）'
        }
    }
}

# 基於經驗水平的策略推薦
STRATEGY_RECOMMENDATIONS = {
    'ABSOLUTE_BEGINNER': [
        'MA_CROSSOVER',      # 從這裡開始——簡單有效
        'TURTLE_BREAKOUT'    # 學習突破概念
    ],
    
    'BEGINNER': [
        'MA_CROSSOVER',
        'RSI_CROSSOVER',
        'TURTLE_BREAKOUT'
    ],
    
    'INTERMEDIATE': [
        'MA_CROSSOVER',
        'RSI_CROSSOVER', 
        'BOLLINGER_REVERSION',
        'PULSE_SYNC'
    ],
    
    'ADVANCED': [
        'QUANTUM_VELOCITY',
        'MERCY_EDGE',
        'ICHIMOKU_CLOUD'
    ],
    
    'EXPERT': [
        'QUANTUMBOTX_CRYPTO',
        'QUANTUMBOTX_HYBRID',
        'DYNAMIC_BREAKOUT'
    ]
}

# 各難度級別的教學提示
LEARNING_TIPS = {
    '初級': [
        "從 MA_CROSSOVER 開始——它是技術分析的基礎",
        "在轉向複雜策略前，先精通一個策略",
        "學習時使用小手數（0.01）",
        "實盤交易前務必進行回測",
        "設置止損——每筆交易風險不超過 2%",
        "新功能：基於 ATR 的風險管理自動保護您！",
        "黃金（XAUUSD）的特別保護可防止帳戶爆倉",
        "系統根據波動率計算手數——天才設計！"
    ],
    
    '中級': [
        "先在模擬帳戶上嘗試不同策略",
        "學會識別市場狀態（趨勢市 vs 震蕩市）",
        "理解風險收益比（目標至少 1:2）",
        "記錄交易日誌以追蹤表現",
        "針對不同市場狀態組合使用策略",
        "掌握不同市場狀態下的 ATR 倍數調整",
        "學會通過 ATR 數值判斷市場波動率"
    ],
    
    '高級': [
        "注重風險管理而非利潤最大化", 
        "使用多時間框架分析",
        "根據市場狀態優化參數",
        "考慮組合層面的風險管理",
        "探索算法交易概念",
        "創建基於 ATR 的自定義倉位規則",
        "開發特定市場的風險管理系統"
    ]
}

# 基於 ATR 的風險管理教學
ATR_EDUCATION = {
    'concept_explanation': {
        'simple': 'ATR = 價格每天通常波動的幅度',
        'detailed': [
            'ATR 衡量每日平均價格波動',
            '高 ATR = 高波動市場（大振幅）',
            '低 ATR = 平靜市場（小波動）',
            '用於設置智能止損和止盈',
            '自動根據市場狀態調整倉位大小'
        ]
    },
    'examples': {
        'EURUSD': {
            'typical_atr': '50 點（0.0050）',
            'risk_example': '1% 風險 = $10,000 帳戶最大虧損 $100',
            'sl_distance': '2倍 ATR = 100 點止損',
            'tp_distance': '4倍 ATR = 200 點止盈',
            'explanation': '穩定外匯對 - 常規參數表現良好'
        },
        'XAUUSD': {
            'typical_atr': '$15（非常高！）',
            'risk_example': '1% 風險已設上限以保安全',
            'sl_distance': '1倍 ATR = $15 止損（為安全降低）',
            'tp_distance': '2倍 ATR = $30 止盈（保守）',
            'explanation': '系統自動保護您免受黃金波動風險！'
        }
    },
    'protection_features': [
        '高波動品種自動風險封頂',
        '黃金特殊保護防止帳戶爆倉',
        '基於市場波動率的動態倉位調整',
        '緊急剎車系統跳過危險交易',
        '實時風險計算與記錄'
    ]
}

def get_beginner_defaults(strategy_name: str) -> dict:
    """Get beginner-friendly defaults for a strategy"""
    return BEGINNER_DEFAULTS.get(strategy_name, {})

def get_strategy_recommendations(level: str) -> list:
    """Get recommended strategies for experience level"""
    return STRATEGY_RECOMMENDATIONS.get(level.upper(), [])

def get_learning_tips(level: str) -> list:
    """Get learning tips for experience level"""
    return LEARNING_TIPS.get(level.upper(), [])

def is_beginner_friendly(strategy_name: str) -> bool:
    """Check if strategy is beginner-friendly"""
    strategy_info = BEGINNER_DEFAULTS.get(strategy_name, {})
    return strategy_info.get('difficulty') == 'BEGINNER'

def get_strategy_explanation(strategy_name: str, param_name: str) -> str:
    """Get explanation for a specific parameter"""
    strategy_info = BEGINNER_DEFAULTS.get(strategy_name, {})
    explanations = strategy_info.get('explanation', {})
    return explanations.get(param_name, f"Parameter: {param_name}")

def get_atr_education_info() -> dict:
    """Get ATR education information for beginners"""
    return ATR_EDUCATION

def explain_atr_for_beginners(symbol: str = 'EURUSD') -> dict:
    """Get beginner-friendly ATR explanation with examples"""
    examples = ATR_EDUCATION['examples']
    return {
        'concept': ATR_EDUCATION['concept_explanation'],
        'example': examples.get(symbol, examples['EURUSD']),
        'protection_features': ATR_EDUCATION['protection_features']
    }