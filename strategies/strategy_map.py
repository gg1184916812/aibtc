# core/strategies/strategy_map.py

from .ma_crossover import MACrossoverStrategy
from .quantumbotx_hybrid import QuantumBotXHybridStrategy
from .quantumbotx_crypto import QuantumBotXCryptoStrategy
from .rsi_crossover import RSICrossoverStrategy
from .bollinger_reversion import BollingerBandsStrategy
from .bollinger_squeeze import BollingerSqueezeStrategy
from .mercy_edge import MercyEdgeStrategy
from .quantum_velocity import QuantumVelocityStrategy
from .pulse_sync import PulseSyncStrategy
from .turtle_breakout import TurtleBreakoutStrategy
from .ichimoku_cloud import IchimokuCloudStrategy
from .dynamic_breakout import DynamicBreakoutStrategy
from .index_momentum import IndexMomentumStrategy
from .index_breakout_pro import IndexBreakoutProStrategy
from .beginner_defaults import BEGINNER_DEFAULTS
from .indicator_strategies import (
    MACDStrategy, StochasticStrategy, CCIStrategy, WilliamsRStrategy,
    ROCStrategy, AwesomeOscillatorStrategy, RSIDivergenceStrategy,
    SuperTrendStrategy, ParabolicSARStrategy, ADXStrategy,
    KeltnerChannelStrategy, EMAEnvelopeStrategy, DonchianBreakoutStrategy,
    HullMAStrategy, TripleMAStrategy, ZeroLagEMAStrategy,
    PinBarStrategy, EngulfingStrategy, InsideBarStrategy, DojiStrategy,
    HammerShootingStrategy, NR7Strategy,
    MTFMACrossoverStrategy, MTFBollingerStrategy,
    VolatilityBreakoutStrategy, ATRChannelStrategy, BollingerTrendStrategy,
    RSIExtremeStrategy, BollingerPercentBStrategy,
    PriceChannelStrategy, LinearRegressionStrategy,
    MFIStrategy, VolumeWeightedMAStrategy,
    MACDBollingerStrategy, RSIStochHybridStrategy, SuperTrendRSIStrategy, ADXMACDStrategy,
    FractalBreakoutStrategy, HeikinAshiStrategy, ChandelierExitStrategy,
    RainbowMAStrategy, OpeningRangeBreakoutStrategy, RangeExpansionStrategy, PivotPointStrategy,
)

STRATEGY_MAP = {
    'MA_CROSSOVER': MACrossoverStrategy,
    'QUANTUMBOTX_HYBRID': QuantumBotXHybridStrategy,
    'QUANTUMBOTX_CRYPTO': QuantumBotXCryptoStrategy,
    'RSI_CROSSOVER': RSICrossoverStrategy,
    'BOLLINGER_REVERSION': BollingerBandsStrategy,
    'BOLLINGER_SQUEEZE': BollingerSqueezeStrategy,
    'MERCY_EDGE': MercyEdgeStrategy,
    'QUANTUM_VELOCITY': QuantumVelocityStrategy,
    'PULSE_SYNC': PulseSyncStrategy,
    'TURTLE_BREAKOUT': TurtleBreakoutStrategy,
    'ICHIMOKU_CLOUD': IchimokuCloudStrategy,
    'DYNAMIC_BREAKOUT': DynamicBreakoutStrategy,
    'INDEX_MOMENTUM': IndexMomentumStrategy,
    'INDEX_BREAKOUT_PRO': IndexBreakoutProStrategy,
    'MACD': MACDStrategy,
    'STOCHASTIC': StochasticStrategy,
    'CCI': CCIStrategy,
    'WILLIAMS_R': WilliamsRStrategy,
    'ROC': ROCStrategy,
    'AWESOME_OSCILLATOR': AwesomeOscillatorStrategy,
    'RSI_DIVERGENCE': RSIDivergenceStrategy,
    'SUPERTREND': SuperTrendStrategy,
    'PARABOLIC_SAR': ParabolicSARStrategy,
    'ADX': ADXStrategy,
    'KELTNER_CHANNEL': KeltnerChannelStrategy,
    'EMA_ENVELOPE': EMAEnvelopeStrategy,
    'DONCHIAN_BREAKOUT': DonchianBreakoutStrategy,
    'HULL_MA': HullMAStrategy,
    'TRIPLE_MA': TripleMAStrategy,
    'ZERO_LAG_EMA': ZeroLagEMAStrategy,
    'PIN_BAR': PinBarStrategy,
    'ENGULFING': EngulfingStrategy,
    'INSIDE_BAR': InsideBarStrategy,
    'DOJI': DojiStrategy,
    'HAMMER_SHOOTING': HammerShootingStrategy,
    'NR7': NR7Strategy,
    'MTF_MA_CROSSOVER': MTFMACrossoverStrategy,
    'MTF_BOLLINGER': MTFBollingerStrategy,
    'VOLATILITY_BREAKOUT': VolatilityBreakoutStrategy,
    'ATR_CHANNEL': ATRChannelStrategy,
    'BOLLINGER_TREND': BollingerTrendStrategy,
    'RSI_EXTREME': RSIExtremeStrategy,
    'BOLLINGER_PERCENT_B': BollingerPercentBStrategy,
    'PRICE_CHANNEL': PriceChannelStrategy,
    'LINEAR_REGRESSION': LinearRegressionStrategy,
    'MFI': MFIStrategy,
    'VOLUME_WEIGHTED_MA': VolumeWeightedMAStrategy,
    'MACD_BOLLINGER': MACDBollingerStrategy,
    'RSI_STOCH_HYBRID': RSIStochHybridStrategy,
    'SUPERTREND_RSI': SuperTrendRSIStrategy,
    'ADX_MACD': ADXMACDStrategy,
    'FRACTAL_BREAKOUT': FractalBreakoutStrategy,
    'HEIKIN_ASHI': HeikinAshiStrategy,
    'CHANDELIER_EXIT': ChandelierExitStrategy,
    'RAINBOW_MA': RainbowMAStrategy,
    'OPENING_RANGE': OpeningRangeBreakoutStrategy,
    'RANGE_EXPANSION': RangeExpansionStrategy,
    'PIVOT_POINT': PivotPointStrategy,
}


def normalize_strategy_id(strategy_id):
    """Return the canonical strategy ID used by STRATEGY_MAP."""
    if not strategy_id:
        return strategy_id
    aliases = {
        "quantum_velocity": "QUANTUM_VELOCITY",
    }
    raw = str(strategy_id).strip()
    return aliases.get(raw, raw.upper())


def resolve_strategy_class(strategy_id):
    """Resolve a strategy class while accepting legacy lowercase IDs."""
    return STRATEGY_MAP.get(normalize_strategy_id(strategy_id))

STRATEGY_METADATA = {
    # 初級友好
    'MA_CROSSOVER': {
        'difficulty': '初級',
        'complexity_score': 2,
        'recommended_for_beginners': True,
        'description': '簡單趨勢跟蹤 - 適合初學者的首個策略',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 1
    },
    'RSI_CROSSOVER': {
        'difficulty': '初級',
        'complexity_score': 3,
        'recommended_for_beginners': True,
        'description': '動量分析 - 優秀的第二個策略',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 2
    },
    'TURTLE_BREAKOUT': {
        'difficulty': '初級',
        'complexity_score': 2,
        'recommended_for_beginners': True,
        'description': '突破交易 - 適合趨勢市場',
        'market_types': ['黃金', '外匯'],
        'learning_priority': 3
    },
    'MACD': {
        'difficulty': '初級',
        'complexity_score': 2,
        'recommended_for_beginners': True,
        'description': 'MACD 柱狀圖交叉 - 經典動量策略',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 4
    },
    'PARABOLIC_SAR': {
        'difficulty': '初級',
        'complexity_score': 2,
        'recommended_for_beginners': True,
        'description': '拋物線 SAR 追蹤止損 - 趨勢跟隨',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 5
    },
    'HULL_MA': {
        'difficulty': '初級',
        'complexity_score': 2,
        'recommended_for_beginners': True,
        'description': 'Hull 移動平均交叉 - 低延遲趨勢信號',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 6
    },
    'TRIPLE_MA': {
        'difficulty': '初級',
        'complexity_score': 2,
        'recommended_for_beginners': True,
        'description': '三均線排列 - 多週期趨勢確認',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 7
    },
    'RAINBOW_MA': {
        'difficulty': '初級',
        'complexity_score': 2,
        'recommended_for_beginners': True,
        'description': '彩虹均線 - 多條 MA 扇形排列判斷強趨勢',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 8
    },
    'DONCHIAN_BREAKOUT': {
        'difficulty': '初級',
        'complexity_score': 2,
        'recommended_for_beginners': True,
        'description': 'Donchian 通道突破 - 經典海龜交易入門',
        'market_types': ['黃金', '加密貨幣', '外匯'],
        'learning_priority': 9
    },

    # 中級
    'BOLLINGER_REVERSION': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '均值回歸 - 適合震蕩市場',
        'market_types': ['外匯'],
        'learning_priority': 10
    },
    'PULSE_SYNC': {
        'difficulty': '中級',
        'complexity_score': 7,
        'recommended_for_beginners': False,
        'description': '多指標確認 - 紮實的中級策略',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 11
    },
    'ICHIMOKU_CLOUD': {
        'difficulty': '中級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': '日本技術分析 - 綜合系統',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 12
    },
    'BOLLINGER_SQUEEZE': {
        'difficulty': '中級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': '波動率壓縮交易',
        'market_types': ['黃金', '加密貨幣'],
        'learning_priority': 13
    },
    'STOCHASTIC': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '隨機指標 KD 交叉 - 經典超買超賣',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 14
    },
    'CCI': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '商品通道指數 - ±100 突破信號',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 15
    },
    'WILLIAMS_R': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '威廉指標 - 超買超賣動量分析',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 16
    },
    'ROC': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '價格變化率 - 動量零線穿越',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 17
    },
    'AWESOME_OSCILLATOR': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '動量震盪指標 - 零線穿越+碟形信號',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 18
    },
    'ADX': {
        'difficulty': '中級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': '平均趨向指數 - 趨勢強度+DI交叉',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 19
    },
    'SUPERTREND': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '超級趨勢 - ATR追蹤止損方向翻轉',
        'market_types': ['黃金', '加密貨幣'],
        'learning_priority': 20
    },
    'KELTNER_CHANNEL': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '凱勒通道 - ATR均值回歸',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 21
    },
    'EMA_ENVELOPE': {
        'difficulty': '中級',
        'complexity_score': 2,
        'recommended_for_beginners': False,
        'description': 'EMA 包絡線 - 百分比偏離回歸',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 22
    },
    'ZERO_LAG_EMA': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '零延遲 EMA 交叉 - 減少延遲',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 23
    },
    'PIN_BAR': {
        'difficulty': '中級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': 'Pin Bar 反轉 - 長影線+小實體反轉型態',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 24
    },
    'ENGULFING': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '吞噬型態 - 陽包陰/陰包陽反轉信號',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 25
    },
    'DOJI': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '十字星 - 猶豫不決後突破方向',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 26
    },
    'HAMMER_SHOOTING': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '錘子/流星 - 單根K線反轉型態',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 27
    },
    'NR7': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '最窄振幅 - 7日最小區間後突破',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 28
    },
    'MFI': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '資金流量指數 - 量價結合RSI',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 29
    },
    'VOLUME_WEIGHTED_MA': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '成交量加權均線交叉',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 30
    },
    'BOLLINGER_TREND': {
        'difficulty': '中級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': '布林趨勢跟隨 - 中軌突破確認方向',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 31
    },
    'ATR_CHANNEL': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': 'ATR 通道 - 波動率基準的極端區間突破',
        'market_types': ['黃金', '加密貨幣'],
        'learning_priority': 32
    },
    'PRICE_CHANNEL': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': '價格通道 - N期高低突破+SMA過濾',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 33
    },
    'BOLLINGER_PERCENT_B': {
        'difficulty': '中級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': '布林 %B - 帶寬內的相對位置均值回歸',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 34
    },
    'PIVOT_POINT': {
        'difficulty': '中級',
        'complexity_score': 2,
        'recommended_for_beginners': False,
        'description': '樞軸點 - 經典支撐阻力突破/反轉',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 35
    },
    'HEIKIN_ASHI': {
        'difficulty': '中級',
        'complexity_score': 3,
        'recommended_for_beginners': False,
        'description': 'Heikin Ashi 平滑K線 - 降噪趨勢跟隨',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 36
    },
    'CHANDELIER_EXIT': {
        'difficulty': '中級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': '吊燈出場 - ATR追蹤止損趨勢系統',
        'market_types': ['黃金', '加密貨幣'],
        'learning_priority': 37
    },
    'OPENING_RANGE': {
        'difficulty': '中級',
        'complexity_score': 2,
        'recommended_for_beginners': False,
        'description': '開盤區間突破 - 首N根K線區間突破',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 38
    },

    # 高級
    'QUANTUM_VELOCITY': {
        'difficulty': '高級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': '高級波動率突破系統',
        'market_types': ['黃金', '加密貨幣'],
        'learning_priority': 39
    },
    'MERCY_EDGE': {
        'difficulty': '高級',
        'complexity_score': 6,
        'recommended_for_beginners': False,
        'description': 'AI增強多時間框架分析',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 40
    },
    'DYNAMIC_BREAKOUT': {
        'difficulty': '高級',
        'complexity_score': 6,
        'recommended_for_beginners': False,
        'description': '動態突破檢測',
        'market_types': ['黃金', '加密貨幣'],
        'learning_priority': 41
    },
    'RSI_DIVERGENCE': {
        'difficulty': '高級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': 'RSI 背離 - 價格與指標背離反轉信號',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 42
    },
    'INSIDE_BAR': {
        'difficulty': '高級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': '內包線 - 母子K線突破策略',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 43
    },
    'MTF_MA_CROSSOVER': {
        'difficulty': '高級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': '多時間框架 MA - 大週期過濾+小週期進場',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 44
    },
    'MTF_BOLLINGER': {
        'difficulty': '高級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': '多時間框架布林 - 趨勢過濾均值回歸',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 45
    },
    'VOLATILITY_BREAKOUT': {
        'difficulty': '高級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': '波動率擴張突破 - ATR暴增後跟隨方向',
        'market_types': ['黃金', '加密貨幣'],
        'learning_priority': 46
    },
    'RSI_EXTREME': {
        'difficulty': '高級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': 'RSI 極端值 - 超買超賣+趨勢過濾',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 47
    },
    'LINEAR_REGRESSION': {
        'difficulty': '高級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': '線性回歸通道 - 回歸線穿越信號',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 48
    },
    'RANGE_EXPANSION': {
        'difficulty': '高級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': '區間擴張 - 當前K線振幅異常放大',
        'market_types': ['黃金', '加密貨幣'],
        'learning_priority': 49
    },
    'FRACTAL_BREAKOUT': {
        'difficulty': '高級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': '威廉分形突破 - 局部極值突破策略',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 50
    },

    # 混合/複合策略
    'QUANTUMBOTX_HYBRID': {
        'difficulty': '中級',
        'complexity_score': 6,
        'recommended_for_beginners': False,
        'description': '多指標混合策略，適用於外匯和加密貨幣',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 51
    },
    'QUANTUMBOTX_CRYPTO': {
        'difficulty': '中級',
        'complexity_score': 7,
        'recommended_for_beginners': False,
        'description': '加密貨幣專用策略，帶波動率管理',
        'market_types': ['加密貨幣'],
        'learning_priority': 52
    },
    'MACD_BOLLINGER': {
        'difficulty': '高級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': 'MACD 趨勢確認 + 布林區間進場',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 53
    },
    'RSI_STOCH_HYBRID': {
        'difficulty': '高級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': 'RSI + 隨機指標雙重確認',
        'market_types': ['外匯', '黃金'],
        'learning_priority': 54
    },
    'SUPERTREND_RSI': {
        'difficulty': '高級',
        'complexity_score': 5,
        'recommended_for_beginners': False,
        'description': '超級趨勢方向 + RSI 強度確認',
        'market_types': ['黃金', '加密貨幣'],
        'learning_priority': 55
    },
    'ADX_MACD': {
        'difficulty': '高級',
        'complexity_score': 6,
        'recommended_for_beginners': False,
        'description': 'ADX 趨勢強度過濾 + MACD 進場',
        'market_types': ['外匯', '黃金', '加密貨幣'],
        'learning_priority': 56
    },

    # 股指專家
    'INDEX_MOMENTUM': {
        'difficulty': '中級',
        'complexity_score': 4,
        'recommended_for_beginners': False,
        'description': '股指動量策略，帶缺口檢測',
        'market_types': ['股指'],
        'learning_priority': 57
    },
    'INDEX_BREAKOUT_PRO': {
        'difficulty': '高級',
        'complexity_score': 7,
        'recommended_for_beginners': False,
        'description': '專業股指突破，含機構分析',
        'market_types': ['股指'],
        'learning_priority': 58
    }
}

def get_beginner_strategies():
    """Get strategies recommended for beginners"""
    return [name for name, info in STRATEGY_METADATA.items()
            if info['recommended_for_beginners']]

def get_strategies_by_difficulty(difficulty):
    """Get strategies by difficulty level"""
    return [name for name, info in STRATEGY_METADATA.items()
            if info['difficulty'] == difficulty.upper()]

def get_strategies_for_market(market_type):
    """Get strategies suitable for specific market type"""
    market_upper = market_type.upper()

    # Handle index symbols by converting to INDICES market type
    if market_upper in ['US30', 'US100', 'US500', 'DE30', 'UK100', 'JP225']:
        market_upper = 'INDICES'

    return [name for name, info in STRATEGY_METADATA.items()
            if market_upper in info['market_types']]

def get_strategy_info(strategy_name):
    """Get complete strategy information"""
    strategy_id = normalize_strategy_id(strategy_name)
    metadata = STRATEGY_METADATA.get(strategy_id, {})
    beginner_info = BEGINNER_DEFAULTS.get(strategy_id, {})

    return {
        'strategy_class': resolve_strategy_class(strategy_id),
        'metadata': metadata,
        'beginner_info': beginner_info
    }
