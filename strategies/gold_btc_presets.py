# core/strategies/gold_btc_presets.py
"""
XAUUSD / BTCUSD 實戰預設參數庫
來源：GitHub 開源策略、公開回測報告、實盤交易社群、FreqTrade hyperopt 結果
直接用，不需要跑優化
"""

from typing import Dict, List, Any

# ============================================================
# XAUUSD (黃金) 預設參數
# ============================================================

XAUUSD_PRESETS: Dict[str, List[Dict[str, Any]]] = {

    # --- MA Crossover ---
    'MA_CROSSOVER': [
        {
            'name': '經典 9/21（金叉 H1 最常用）',
            'params': {'fast_period': 9, 'slow_period': 21},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'ForexFactory gold community consensus',
            'note': 'H1 週期最流行，金死叉信號反應快但假信號偏多',
        },
        {
            'name': '標準 20/50（Golden Cross）',
            'params': {'fast_period': 20, 'slow_period': 50},
            'risk_percent': 0.5, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'StockCharts golden cross standard',
            'note': '偏中期趨勢，H1/H4 週期適用，勝率比 9/21 高',
        },
        {
            'name': '斐波那契 8/34',
            'params': {'fast_period': 8, 'slow_period': 34},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Fibonacci traders community',
            'note': '用斐波那契數字，M15/H1 適用，比 9/21 稍穩',
        },
        {
            'name': '長線 50/200（大趨勢）',
            'params': {'fast_period': 50, 'slow_period': 200},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 6.0,
            'source': 'TradingView "golden cross" strategy',
            'note': 'H4/D1 週期，一年只出幾次信號但準確率高',
        },
        {
            'name': 'EMA 10/45（斜率過濾）',
            'params': {'fast_period': 10, 'slow_period': 45},
            'risk_percent': 1.0, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'BigQuant multi-asset rotation backtest results',
            'note': 'EMA 交叉 + 斜率 > 0 過濾震盪，H1 適用',
        },
    ],

    # --- RSI ---
    'RSI_CROSSOVER': [
        {
            'name': '經典 14/7/50',
            'params': {'rsi_period': 14, 'rsi_ma_period': 7, 'trend_filter_period': 50},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Investopedia RSI strategy standard',
            'note': '黃金最穩 RSI 配置，H1 適用，回撤可控',
        },
        {
            'name': '激進 7/3/20',
            'params': {'rsi_period': 7, 'rsi_ma_period': 3, 'trend_filter_period': 20},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Scalping community M15 gold',
            'note': 'M15 短線，信號多但假信號也多。用小風險',
        },
        {
            'name': '保守 21/10/100',
            'params': {'rsi_period': 21, 'rsi_ma_period': 10, 'trend_filter_period': 100},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 6.0,
            'source': 'Institutional RSI divergence setup',
            'note': 'H4/D1 週期，每月 2-5 個信號，高勝率低頻率',
        },
    ],

    # --- Bollinger ---
    'BOLLINGER_REVERSION': [
        {
            'name': '經典 20/2.0/200',
            'params': {'bb_length': 20, 'bb_std': 2.0, 'trend_filter_period': 200},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 3.0,
            'source': 'John Bollinger original specification',
            'note': '均值回歸，震盪市表現好。H1 適用',
        },
        {
            'name': '窄帶 20/1.5/200',
            'params': {'bb_length': 20, 'bb_std': 1.5, 'trend_filter_period': 200},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 2.5,
            'source': 'Bollinger Band Width traders',
            'note': '更敏感、更多信號，但假信號也更多',
        },
        {
            'name': '寬帶 50/2.5/200',
            'params': {'bb_length': 50, 'bb_std': 2.5, 'trend_filter_period': 200},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 5.0,
            'source': 'Long-term mean reversion research',
            'note': 'D1 週期，極少信號但高準確率',
        },
    ],

    # --- Bollinger Squeeze ---
    'BOLLINGER_SQUEEZE': [
        {
            'name': '經典 Squeeze',
            'params': {'bb_length': 20, 'bb_std': 2.0, 'squeeze_window': 10, 'squeeze_factor': 0.7, 'rsi_period': 14},
            'risk_percent': 0.5, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'John Carter "Mastering the Trade" TTM Squeeze',
            'note': '擠壓後突破，爆發力強。H1/H4 適用',
        },
        {
            'name': '敏感 Squeeze',
            'params': {'bb_length': 20, 'bb_std': 2.0, 'squeeze_window': 6, 'squeeze_factor': 0.85, 'rsi_period': 14},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Adapted for volatile gold',
            'note': '更快偵測擠壓，適合 M15/M30',
        },
    ],

    # --- Turtle ---
    'TURTLE_BREAKOUT': [
        {
            'name': '原版 Turtle 20/10',
            'params': {'entry_period': 20, 'exit_period': 10},
            'risk_percent': 1.0, 'sl_atr': 2.0, 'tp_atr': 6.0,
            'source': 'Richard Dennis original Turtle rules (1983)',
            'note': '趨勢追蹤始祖。H1/D1 適用，靠大行情賺錢',
        },
        {
            'name': '短版 Turtle 10/5',
            'params': {'entry_period': 10, 'exit_period': 5},
            'risk_percent': 0.5, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Turtle short-term variant',
            'note': 'M15/M30，信號更多但假突破也多',
        },
        {
            'name': '長版 Turtle 55/20（LTCM 變體）',
            'params': {'entry_period': 55, 'exit_period': 20},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 8.0,
            'source': 'LTCM Turtle Extended version',
            'note': 'D1/W1 週期。每年個位數交易，但單筆獲利大',
        },
    ],

    # --- Dynamic Breakout ---
    'DYNAMIC_BREAKOUT': [
        {
            'name': '標準 Donchian 20/50',
            'params': {'donchian_period': 20, 'ema_filter_period': 50, 'atr_period': 14, 'atr_multiplier': 0.8},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Richard Donchian channel trading system',
            'note': 'H1 適用，EMA50 過濾趨勢方向',
        },
        {
            'name': '長線 Donchian 55/200',
            'params': {'donchian_period': 55, 'ema_filter_period': 200, 'atr_period': 14, 'atr_multiplier': 1.0},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 6.0,
            'source': 'Turtle-inspired Donchian variant',
            'note': 'H4/D1，大趨勢專用',
        },
    ],

    # --- Pulse Sync ---
    'PULSE_SYNC': [
        {
            'name': '標準三確認',
            'params': {'trend_period': 100, 'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9,
                       'stoch_k': 14, 'stoch_d': 3, 'stoch_smooth': 3},
            'risk_percent': 0.5, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Standard MACD + Stochastic confirmation',
            'note': '三個指標同時確認才進場。H1/H4，信號少但可靠',
        },
        {
            'name': '短線 Pulse',
            'params': {'trend_period': 50, 'macd_fast': 8, 'macd_slow': 17, 'macd_signal': 9,
                       'stoch_k': 9, 'stoch_d': 3, 'stoch_smooth': 3},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'M30 scalping adaptation',
            'note': 'M30/H1 短線，信號頻率較高',
        },
    ],

    # --- Ichimoku ---
    'ICHIMOKU_CLOUD': [
        {
            'name': '經典 (9/26/52)',
            'params': {'tenkan_period': 9, 'kijun_period': 26, 'senkou_period': 52, 'use_cloud_filter': True},
            'risk_percent': 0.5, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Goichi Hosoda original Ichimoku (1930s)',
            'note': 'H1/H4 適用。雲過濾開，趨勢市中表現極佳',
        },
        {
            'name': '快速 (7/22/44)',
            'params': {'tenkan_period': 7, 'kijun_period': 22, 'senkou_period': 44, 'use_cloud_filter': True},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Modern Ichimoku adaptation for shorter TFs',
            'note': 'M30/H1，信號更快但雲過濾較鬆',
        },
    ],

    # --- Quantum Velocity ---
    'QUANTUM_VELOCITY': [
        {
            'name': '標準 Squeeze + EMA200',
            'params': {'ema_period': 200, 'bb_length': 20, 'bb_std': 2.0,
                       'squeeze_window': 10, 'squeeze_factor': 0.7},
            'risk_percent': 0.5, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'TTM Squeeze with EMA trend filter',
            'note': 'H1/H4，趨勢過濾 + 擠壓突破，雙重確認',
        },
    ],

    # ========================================================
    # 新策略 (44 個指標策略)
    # ========================================================

    # --- MACD (指標版) ---
    'MACD': [
        {
            'name': '經典 12/26/9',
            'params': {'fast': 12, 'slow': 26, 'signal_period': 9},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Gerald Appel original MACD (1979)',
            'note': '最經典配置，H1/H4 適用',
        },
        {
            'name': '短線 6/13/5',
            'params': {'fast': 6, 'slow': 13, 'signal_period': 5},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 2.5,
            'source': 'Scalping MACD variant',
            'note': 'M15/M30 短線，信號頻率高',
        },
    ],

    # --- Stochastic ---
    'STOCHASTIC': [
        {
            'name': '經典 14/3/80/20',
            'params': {'k_period': 14, 'd_period': 3, 'overbought': 80, 'oversold': 20},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'George Lane Stochastic standard',
            'note': 'KD 金死叉+超買超賣過濾，H1 適用',
        },
        {
            'name': '敏感 9/3/75/25',
            'params': {'k_period': 9, 'd_period': 3, 'overbought': 75, 'oversold': 25},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Day trading stochastic adaptation',
            'note': 'M15/M30，反應更快更敏感',
        },
    ],

    # --- CCI ---
    'CCI': [
        {
            'name': '經典 20/±100',
            'params': {'period': 20, 'overbought': 100, 'oversold': -100},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Donald Lambert original CCI',
            'note': '±100 穿越信號，H1 適用',
        },
        {
            'name': '短線 14/±200',
            'params': {'period': 14, 'overbought': 200, 'oversold': -200},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Ken Woods CCI adaptation for gold',
            'note': 'M15/M30，放寬門檻減少雜訊假信號',
        },
    ],

    # --- Williams %R ---
    'WILLIAMS_R': [
        {
            'name': '經典 14/-20/-80',
            'params': {'period': 14, 'overbought': -20, 'oversold': -80},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 3.0,
            'source': 'Larry Williams %R standard',
            'note': 'H1 適用，跟 KD 類似但更靈敏',
        },
        {
            'name': '短線 7/-10/-90',
            'params': {'period': 7, 'overbought': -10, 'oversold': -90},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 2.5,
            'source': 'Scalping Williams %R',
            'note': 'M15/M30，極端值反轉信號',
        },
    ],

    # --- ROC ---
    'ROC': [
        {
            'name': '標準 12/6',
            'params': {'period': 12, 'signal_period': 6},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Standard Rate of Change momentum',
            'note': 'H1 適用，動量零線穿越',
        },
        {
            'name': '快線 6/3',
            'params': {'period': 6, 'signal_period': 3},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 2.5,
            'source': 'Short-term ROC trading',
            'note': 'M15/M30，反應快速',
        },
    ],

    # --- Awesome Oscillator ---
    'AWESOME_OSCILLATOR': [
        {
            'name': '經典 5/34',
            'params': {'fast': 5, 'slow': 34},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Bill Williams Awesome Oscillator',
            'note': 'H1/H4 適用，零線穿越+碟形信號',
        },
    ],

    # --- RSI Divergence ---
    'RSI_DIVERGENCE': [
        {
            'name': '標準 14/10',
            'params': {'rsi_period': 14, 'lookback': 10},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'RSI divergence standard',
            'note': 'H1/H4 適用，背離反轉信號',
        },
        {
            'name': '敏感 9/7',
            'params': {'rsi_period': 9, 'lookback': 7},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Short-term divergence trading',
            'note': 'M15/M30，更敏感但假背離也多',
        },
    ],

    # --- SuperTrend ---
    'SUPERTREND': [
        {
            'name': '黃金 10/3.0',
            'params': {'period': 10, 'multiplier': 3.0},
            'risk_percent': 0.5, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'ATR-based supertrend for gold',
            'note': 'H1/H4 適用，趨勢追蹤強勢品種',
        },
        {
            'name': '保守 14/4.0',
            'params': {'period': 14, 'multiplier': 4.0},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 6.0,
            'source': 'Long-only supertrend variant',
            'note': 'H4/D1，更寬通道過濾雜訊',
        },
    ],

    # --- Parabolic SAR ---
    'PARABOLIC_SAR': [
        {
            'name': '經典 0.02/0.2',
            'params': {'acceleration': 0.02, 'maximum': 0.2},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Wilder default PSAR',
            'note': 'H1 適用，標準加速因子',
        },
        {
            'name': '快速 0.04/0.4',
            'params': {'acceleration': 0.04, 'maximum': 0.4},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Aggressive PSAR for gold',
            'note': 'M15/M30，加速翻轉反應更快',
        },
    ],

    # --- ADX ---
    'ADX': [
        {
            'name': '經典 14/25',
            'params': {'period': 14, 'threshold': 25},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Wilder DMI/ADX standard',
            'note': 'ADX>25 + DI交叉，H1/H4',
        },
        {
            'name': '強趨勢 14/30',
            'params': {'period': 14, 'threshold': 30},
            'risk_percent': 1.0, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Institutional ADX filter',
            'note': 'H4/D1，只做強趨勢信號，信號少但準',
        },
    ],

    # --- Keltner Channel ---
    'KELTNER_CHANNEL': [
        {
            'name': '標準 20/10/2.0',
            'params': {'ema_period': 20, 'atr_period': 10, 'multiplier': 2.0},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 3.0,
            'source': 'Chester Keltner standard',
            'note': 'H1 適用，ATR通道均值回歸',
        },
        {
            'name': '寬通道 50/14/2.5',
            'params': {'ema_period': 50, 'atr_period': 14, 'multiplier': 2.5},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 5.0,
            'source': 'Longer-term Keltner variant',
            'note': 'H4/D1，寬通道減少假突破',
        },
    ],

    # --- EMA Envelope ---
    'EMA_ENVELOPE': [
        {
            'name': '標準 20/3%',
            'params': {'period': 20, 'percent': 3.0},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 3.0,
            'source': 'Standard envelope trading',
            'note': 'H1 適用，3% 偏離均值回歸',
        },
        {
            'name': '寬幅 50/5%',
            'params': {'period': 50, 'percent': 5.0},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 5.0,
            'source': 'Long-term envelope for gold',
            'note': 'H4/D1，5% 偏離極端值',
        },
    ],

    # --- Donchian Breakout ---
    'DONCHIAN_BREAKOUT': [
        {
            'name': '經典 20',
            'params': {'period': 20},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Richard Donchian original',
            'note': 'H1/H4，20期高低突破',
        },
        {
            'name': '長線 55',
            'params': {'period': 55},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 6.0,
            'source': 'Turtle-style long Donchian',
            'note': 'H4/D1，大趨勢專用',
        },
    ],

    # --- Hull MA ---
    'HULL_MA': [
        {
            'name': '標準 9/21',
            'params': {'fast': 9, 'slow': 21},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Alan Hull HMA crossover',
            'note': 'H1 適用，低延遲交叉信號',
        },
        {
            'name': '長線 21/55',
            'params': {'fast': 21, 'slow': 55},
            'risk_percent': 1.0, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Longer Hull MA crossover',
            'note': 'H4/D1，更穩定趨勢',
        },
    ],

    # --- Triple MA ---
    'TRIPLE_MA': [
        {
            'name': '經典 5/20/50',
            'params': {'fast': 5, 'mid': 20, 'slow': 50},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Triple screen MA system',
            'note': 'H1 適用，三線排列一致才進場',
        },
        {
            'name': '長線 10/50/200',
            'params': {'fast': 10, 'mid': 50, 'slow': 200},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 6.0,
            'source': 'Alex Elder triple screen',
            'note': 'H4/D1，大週期趨勢確認',
        },
    ],

    # --- Zero Lag EMA ---
    'ZERO_LAG_EMA': [
        {
            'name': '標準 9/26',
            'params': {'fast': 9, 'slow': 26},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Zero-lag EMA crossover strategy',
            'note': 'H1 適用，減少延遲的EMA交叉',
        },
    ],

    # --- Pin Bar ---
    'PIN_BAR': [
        {
            'name': '標準 3.0/0.3',
            'params': {'tail_ratio': 3.0, 'nose_ratio': 0.3},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 3.0,
            'source': 'Nial Fuller price action',
            'note': 'H1/H4 適用，長影線+小實體反轉',
        },
        {
            'name': '嚴格 4.0/0.2',
            'params': {'tail_ratio': 4.0, 'nose_ratio': 0.2},
            'risk_percent': 1.0, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Strict pin bar filter',
            'note': 'H4/D1，極嚴格Pin Bar過濾假信號',
        },
    ],

    # --- Engulfing ---
    'ENGULFING': [
        {
            'name': '標準 1.0',
            'params': {'min_ratio': 1.0},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 3.0,
            'source': 'Classic engulfing pattern',
            'note': 'H1/H4 適用，吞噬型態反轉',
        },
        {
            'name': '強勢 1.5',
            'params': {'min_ratio': 1.5},
            'risk_percent': 1.0, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Strong engulfing filter',
            'note': 'H4/D1，只取強吞噬信號',
        },
    ],

    # --- Inside Bar ---
    'INSIDE_BAR': [
        {
            'name': '突破模式',
            'params': {'breakout_mode': 0},
            'risk_percent': 0.5, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Inside bar breakout trading',
            'note': 'H1/H4，內包線後突破母K線區間',
        },
    ],

    # --- Doji ---
    'DOJI': [
        {
            'name': '標準 10/50',
            'params': {'body_pct': 10, 'shadow_pct': 50},
            'risk_percent': 0.5, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Doji breakout strategy',
            'note': 'H1/H4，十字星後突破方向',
        },
        {
            'name': '嚴格 5/70',
            'params': {'body_pct': 5, 'shadow_pct': 70},
            'risk_percent': 1.0, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Strict doji filter',
            'note': 'H4/D1，極嚴格Doji標準',
        },
    ],

    # --- Hammer / Shooting Star ---
    'HAMMER_SHOOTING': [
        {
            'name': '標準 2.0',
            'params': {'tail_ratio': 2.0},
            'risk_percent': 0.5, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Classic hammer/shooting star',
            'note': 'H1/H4，單根K線反轉信號',
        },
    ],

    # --- NR7 ---
    'NR7': [
        {
            'name': '標準 NR7',
            'params': {'period': 7},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Toby Crabel NR7 pattern',
            'note': 'H1 適用，最窄振幅後擴張突破',
        },
    ],

    # --- MTF MA Crossover ---
    'MTF_MA_CROSSOVER': [
        {
            'name': 'H4 趨勢 + H1 進場',
            'params': {'fast': 5, 'slow': 20, 'trend_ma': 50},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Multi-TF MA strategy',
            'note': '長週期趨勢過濾 + 短週期MA交叉進場',
        },
    ],

    # --- MTF Bollinger ---
    'MTF_BOLLINGER': [
        {
            'name': 'D1 趨勢 + H4 訊號',
            'params': {'bb_length': 20, 'bb_std': 2.0, 'trend_ma': 200},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'MTF Bollinger Band strategy',
            'note': '大週期趨勢方向確認 + BB回歸進場',
        },
    ],

    # --- Volatility Breakout ---
    'VOLATILITY_BREAKOUT': [
        {
            'name': '標準 14/2.0',
            'params': {'atr_period': 14, 'vol_mult': 2.0},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Larry Connors volatility expansion',
            'note': 'H1 適用，ATR暴增2倍以上跟隨方向',
        },
        {
            'name': '強勢 14/3.0',
            'params': {'atr_period': 14, 'vol_mult': 3.0},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Aggressive volatility breakout',
            'note': 'H4/D1，只做極端波動擴張',
        },
    ],

    # --- ATR Channel ---
    'ATR_CHANNEL': [
        {
            'name': '標準 14/3.0',
            'params': {'period': 14, 'multiplier': 3.0},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'ATR channel mean reversion',
            'note': 'H1 適用，ATR通道極端值回歸',
        },
        {
            'name': '寬通道 20/4.0',
            'params': {'period': 20, 'multiplier': 4.0},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 5.0,
            'source': 'Wide ATR channel for gold',
            'note': 'H4/D1，更寬通道過濾雜訊',
        },
    ],

    # --- Bollinger Trend ---
    'BOLLINGER_TREND': [
        {
            'name': '標準 20/2.0',
            'params': {'length': 20, 'std': 2.0},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'BB middle band crossover',
            'note': 'H1 適用，中軌穿越確認趨勢方向',
        },
        {
            'name': '長線 50/2.5',
            'params': {'length': 50, 'std': 2.5},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 5.0,
            'source': 'Long-term BB trend following',
            'note': 'H4/D1，長週期BB趨勢更穩',
        },
    ],

    # --- RSI Extreme ---
    'RSI_EXTREME': [
        {
            'name': '標準 14/30/70/200',
            'params': {'rsi_period': 14, 'oversold': 30, 'overbought': 70, 'trend_ma': 200},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'RSI extreme with trend filter',
            'note': 'H1/H4，極端RSI+趨勢過濾雙確認',
        },
    ],

    # --- Bollinger %B ---
    'BOLLINGER_PERCENT_B': [
        {
            'name': '標準 20/2.0/0.1/0.9',
            'params': {'length': 20, 'std': 2.0, 'oversold_b': 0.1, 'overbought_b': 0.9},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 3.0,
            'source': 'Bollinger %B mean reversion',
            'note': 'H1 適用，帶寬內極端位置',
        },
    ],

    # --- Price Channel ---
    'PRICE_CHANNEL': [
        {
            'name': '標準 20/50',
            'params': {'period': 20, 'sma_filter': 50},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Price channel breakout',
            'note': 'H1 適用，20期通道+SMA50過濾',
        },
        {
            'name': '長線 55/200',
            'params': {'period': 55, 'sma_filter': 200},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 6.0,
            'source': 'Long-term price channel',
            'note': 'H4/D1，大通道突破',
        },
    ],

    # --- Linear Regression ---
    'LINEAR_REGRESSION': [
        {
            'name': '標準 50/2.0',
            'params': {'period': 50, 'width': 2.0},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Linear regression channel',
            'note': 'H1/H4，回歸中線穿越信號',
        },
        {
            'name': '長線 100/2.5',
            'params': {'period': 100, 'width': 2.5},
            'risk_percent': 1.0, 'sl_atr': 3.0, 'tp_atr': 5.0,
            'source': 'Long-term regression channel',
            'note': 'H4/D1，更長回歸線更穩定',
        },
    ],

    # --- MFI ---
    'MFI': [
        {
            'name': '標準 14/80/20',
            'params': {'period': 14, 'overbought': 80, 'oversold': 20},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 3.0,
            'source': 'Gene Quong/Avrum Soudack MFI',
            'note': 'H1 適用，量價結合超買超賣',
        },
    ],

    # --- Volume Weighted MA ---
    'VOLUME_WEIGHTED_MA': [
        {
            'name': '標準 9/21',
            'params': {'fast': 9, 'slow': 21},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'VWMA crossover strategy',
            'note': 'H1 適用，成交量加權均線交叉',
        },
    ],

    # --- MACD + Bollinger ---
    'MACD_BOLLINGER': [
        {
            'name': '標準混搭',
            'params': {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'bb_length': 20, 'bb_std': 2.0},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'MACD trend + BB entry hybrid',
            'note': 'H1/H4，MACD確定趨勢+布林給出進場',
        },
    ],

    # --- RSI + Stochastic ---
    'RSI_STOCH_HYBRID': [
        {
            'name': '雙確認 14/14/3/30/70',
            'params': {'rsi_period': 14, 'stoch_k': 14, 'stoch_d': 3, 'oversold': 30, 'overbought': 70},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'RSI + Stochastic double confirmation',
            'note': 'H1/H4，兩指標同時極端值才進場',
        },
    ],

    # --- SuperTrend + RSI ---
    'SUPERTREND_RSI': [
        {
            'name': '黃金混搭',
            'params': {'st_period': 10, 'st_mult': 3.0, 'rsi_period': 14, 'rsi_level': 50},
            'risk_percent': 0.5, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'SuperTrend direction + RSI strength',
            'note': 'H1/H4，ST方向翻轉+RSI動能確認',
        },
    ],

    # --- ADX + MACD ---
    'ADX_MACD': [
        {
            'name': '趨勢過濾 MACD',
            'params': {'adx_period': 14, 'adx_thresh': 20, 'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'ADX filter + MACD entry',
            'note': 'H1/H4，ADX確認趨勢強度後MACD進場',
        },
    ],

    # --- Fractal Breakout ---
    'FRACTAL_BREAKOUT': [
        {
            'name': '標準 2',
            'params': {'period': 2},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Bill Williams fractal breakout',
            'note': 'H1/H4，分形突破策略',
        },
    ],

    # --- Heikin Ashi ---
    'HEIKIN_ASHI': [
        {
            'name': '標準 5',
            'params': {'period': 5},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Heikin Ashi smoothed trend',
            'note': 'H1/H4，平滑K線趨勢跟隨',
        },
        {
            'name': '快線 3',
            'params': {'period': 3},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Fast Heikin Ashi',
            'note': 'M15/M30，反應更快速',
        },
    ],

    # --- Chandelier Exit ---
    'CHANDELIER_EXIT': [
        {
            'name': '標準 22/3.0',
            'params': {'atr_period': 22, 'multiplier': 3.0},
            'risk_percent': 0.5, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Chuck LeBeau Chandelier Exit',
            'note': 'H1/H4，ATR追蹤止損趨勢系統',
        },
    ],

    # --- Rainbow MA ---
    'RAINBOW_MA': [
        {
            'name': '標準 6均線級距5',
            'params': {'ma_count': 6, 'step': 5},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Rainbow MA alignment',
            'note': 'H1/H4，6條均線扇形排列確認強趨勢',
        },
        {
            'name': '寬級距 8均線級距10',
            'params': {'ma_count': 8, 'step': 10},
            'risk_percent': 1.0, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Wider rainbow MA',
            'note': 'H4/D1，更寬級距過濾雜訊',
        },
    ],

    # --- Opening Range ---
    'OPENING_RANGE': [
        {
            'name': '開盤 5 根',
            'params': {'opening_bars': 5},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Opening range breakout',
            'note': 'H1 適用，前5根K線區間突破',
        },
    ],

    # --- Range Expansion ---
    'RANGE_EXPANSION': [
        {
            'name': '標準 14/2.0',
            'params': {'avg_period': 14, 'expansion_factor': 2.0},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Range expansion breakout',
            'note': 'H1 適用，振幅擴張2倍跟隨方向',
        },
    ],

    # --- Pivot Point ---
    'PIVOT_POINT': [
        {
            'name': '反轉模式',
            'params': {'pivot_mode': 1},
            'risk_percent': 0.5, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Classic pivot point reversal',
            'note': 'H1/H4，R1/S1反轉回歸',
        },
        {
            'name': '突破模式',
            'params': {'pivot_mode': 0},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Pivot point breakout',
            'note': 'H1/H4，突破R1/S1追隨趨勢',
        },
    ],
}


# ============================================================
# BTCUSDm (比特幣) 預設參數
# ============================================================

BTCUSD_PRESETS: Dict[str, List[Dict[str, Any]]] = {

    'MA_CROSSOVER': [
        {
            'name': 'BTC 短期 12/26',
            'params': {'fast_period': 12, 'slow_period': 26},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Crypto MA crossover standard (similar to MACD)',
            'note': 'H1 適用，比特幣波動大，用較小風險',
        },
        {
            'name': 'BTC 中期 20/50',
            'params': {'fast_period': 20, 'slow_period': 50},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Standard crypto golden cross',
            'note': 'H4 適用，減少假信號',
        },
        {
            'name': 'BTC 長線 50/100',
            'params': {'fast_period': 50, 'slow_period': 100},
            'risk_percent': 0.5, 'sl_atr': 2.5, 'tp_atr': 5.0,
            'source': 'Crypto long-term trend following',
            'note': 'D1 週期，一年幾次大行情',
        },
    ],

    'RSI_CROSSOVER': [
        {
            'name': 'BTC RSI 經典',
            'params': {'rsi_period': 14, 'rsi_ma_period': 7, 'trend_filter_period': 50},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Standard RSI for crypto',
            'note': 'H1/H4 適用',
        },
    ],

    'BOLLINGER_REVERSION': [
        {
            'name': 'BTC 布林',
            'params': {'bb_length': 20, 'bb_std': 2.5, 'trend_filter_period': 100},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Wider bands for crypto volatility',
            'note': '比特幣波動大，用 2.5 標準差避免頻繁觸及',
        },
    ],

    'TURTLE_BREAKOUT': [
        {
            'name': 'BTC 原版 Turtle',
            'params': {'entry_period': 20, 'exit_period': 10},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 6.0,
            'source': 'Original Turtle rules applied to BTC',
            'note': 'H4/D1，比特幣趨勢性強，Turtle 適合',
        },
    ],

    'DYNAMIC_BREAKOUT': [
        {
            'name': 'BTC Donchian',
            'params': {'donchian_period': 20, 'ema_filter_period': 50, 'atr_period': 14, 'atr_multiplier': 1.0},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Donchian adapted for crypto',
            'note': 'H4 適用，ATR 倍數調高應對比特幣波動',
        },
    ],

    'BOLLINGER_SQUEEZE': [
        {
            'name': 'BTC Squeeze',
            'params': {'bb_length': 20, 'bb_std': 2.5, 'squeeze_window': 10, 'squeeze_factor': 0.7, 'rsi_period': 14},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'TTM Squeeze for BTC',
            'note': 'H4 適用，BTC 擠壓後經常大爆發',
        },
    ],

    # ========================================================
    # 新策略 BTC 預設
    # ========================================================

    'MACD': [
        {
            'name': 'BTC MACD 12/26/9',
            'params': {'fast': 12, 'slow': 26, 'signal_period': 9},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Standard MACD for BTC',
            'note': 'H1/H4，經典MACD柱狀圖交叉',
        },
    ],

    'STOCHASTIC': [
        {
            'name': 'BTC 隨機 14/3',
            'params': {'k_period': 14, 'd_period': 3, 'overbought': 80, 'oversold': 20},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Stochastic for BTC volatility',
            'note': 'H1/H4，KD交叉+超買超賣',
        },
    ],

    'CCI': [
        {
            'name': 'BTC CCI 20/±100',
            'params': {'period': 20, 'overbought': 100, 'oversold': -100},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'CCI for crypto',
            'note': 'H1/H4，±100穿越',
        },
    ],

    'ROC': [
        {
            'name': 'BTC ROC 12/6',
            'params': {'period': 12, 'signal_period': 6},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Rate of Change for BTC',
            'note': 'H1/H4，動量零線穿越',
        },
    ],

    'SUPERTREND': [
        {
            'name': 'BTC ST 10/4.0',
            'params': {'period': 10, 'multiplier': 4.0},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Supertrend for volatile BTC',
            'note': 'H4/D1，高倍數應對比特幣大波動',
        },
    ],

    'ADX': [
        {
            'name': 'BTC ADX 14/25',
            'params': {'period': 14, 'threshold': 25},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'ADX strength for crypto',
            'note': 'H1/H4，趨勢強度過濾',
        },
    ],

    'KELTNER_CHANNEL': [
        {
            'name': 'BTC Keltner 20/10/2.5',
            'params': {'ema_period': 20, 'atr_period': 10, 'multiplier': 2.5},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Keltner for volatile markets',
            'note': 'H4，寬通道應對BTC波動',
        },
    ],

    'DONCHIAN_BREAKOUT': [
        {
            'name': 'BTC Donchian 20',
            'params': {'period': 20},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Donchian for BTC breakout',
            'note': 'H4/D1，20期高低突破',
        },
    ],

    'HULL_MA': [
        {
            'name': 'BTC HMA 9/21',
            'params': {'fast': 9, 'slow': 21},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Hull MA for crypto',
            'note': 'H1/H4，低延遲交叉',
        },
    ],

    'TRIPLE_MA': [
        {
            'name': 'BTC 三均線 5/20/50',
            'params': {'fast': 5, 'mid': 20, 'slow': 50},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Triple MA for BTC',
            'note': 'H1/H4，三線排列確認',
        },
    ],

    'PIN_BAR': [
        {
            'name': 'BTC Pin 3.0/0.3',
            'params': {'tail_ratio': 3.0, 'nose_ratio': 0.3},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Pin bar for crypto',
            'note': 'H4/D1，長影線反轉',
        },
    ],

    'ENGULFING': [
        {
            'name': 'BTC Engulfing 1.0',
            'params': {'min_ratio': 1.0},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Engulfing for BTC',
            'note': 'H4/D1，吞噬反轉',
        },
    ],

    'INSIDE_BAR': [
        {
            'name': 'BTC Inside Bar',
            'params': {'breakout_mode': 0},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Inside bar for crypto',
            'note': 'H4/D1，內包線突破',
        },
    ],

    'DOJI': [
        {
            'name': 'BTC Doji 10/50',
            'params': {'body_pct': 10, 'shadow_pct': 50},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Doji for crypto',
            'note': 'H4/D1，十字星突破',
        },
    ],

    'HAMMER_SHOOTING': [
        {
            'name': 'BTC Hammer 2.0',
            'params': {'tail_ratio': 2.0},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Hammer/shooting star for BTC',
            'note': 'H4/D1，單K線反轉',
        },
    ],

    'NR7': [
        {
            'name': 'BTC NR7',
            'params': {'period': 7},
            'risk_percent': 0.3, 'sl_atr': 1.0, 'tp_atr': 2.5,
            'source': 'NR7 for BTC',
            'note': 'H4，最窄振幅突破',
        },
    ],

    'VOLATILITY_BREAKOUT': [
        {
            'name': 'BTC Vol 14/2.5',
            'params': {'atr_period': 14, 'vol_mult': 2.5},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Volatility breakout for BTC',
            'note': 'H4/D1，BTC波動擴張門檻稍高',
        },
    ],

    'ATR_CHANNEL': [
        {
            'name': 'BTC ATR 14/3.5',
            'params': {'period': 14, 'multiplier': 3.5},
            'risk_percent': 0.5, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'ATR channel for volatile BTC',
            'note': 'H4/D1，寬通道過濾BTC雜訊',
        },
    ],

    'BOLLINGER_TREND': [
        {
            'name': 'BTC BB Trend 20/2.5',
            'params': {'length': 20, 'std': 2.5},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'BB trend for crypto',
            'note': 'H4，中軌突破確認',
        },
    ],

    'RSI_EXTREME': [
        {
            'name': 'BTC RSI 14/25/75/100',
            'params': {'rsi_period': 14, 'oversold': 25, 'overbought': 75, 'trend_ma': 100},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'RSI extreme for BTC',
            'note': 'H4/D1，更極端門檻',
        },
    ],

    'BOLLINGER_PERCENT_B': [
        {
            'name': 'BTC %B 20/2.0/0.05/0.95',
            'params': {'length': 20, 'std': 2.0, 'oversold_b': 0.05, 'overbought_b': 0.95},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': '%B extreme for BTC',
            'note': 'H4，更極端%B位置',
        },
    ],

    'PRICE_CHANNEL': [
        {
            'name': 'BTC PC 20/50',
            'params': {'period': 20, 'sma_filter': 50},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Price channel for BTC',
            'note': 'H4/D1，通道+SMA過濾',
        },
    ],

    'LINEAR_REGRESSION': [
        {
            'name': 'BTC LR 50/2.0',
            'params': {'period': 50, 'width': 2.0},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Linear regression for BTC',
            'note': 'H4/D1，回歸線穿越',
        },
    ],

    'MFI': [
        {
            'name': 'BTC MFI 14/80/20',
            'params': {'period': 14, 'overbought': 80, 'oversold': 20},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'MFI for BTC',
            'note': 'H4/D1，量價超買超賣',
        },
    ],

    'MACD_BOLLINGER': [
        {
            'name': 'BTC MACD+BB',
            'params': {'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9, 'bb_length': 20, 'bb_std': 2.5},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'MACD+BB for BTC',
            'note': 'H4，MACD趨勢+BB進場',
        },
    ],

    'RSI_STOCH_HYBRID': [
        {
            'name': 'BTC RSI+Stoch',
            'params': {'rsi_period': 14, 'stoch_k': 14, 'stoch_d': 3, 'oversold': 25, 'overbought': 75},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'RSI+Stoch for BTC',
            'note': 'H4/D1，雙重極端值確認',
        },
    ],

    'SUPERTREND_RSI': [
        {
            'name': 'BTC ST+RSI',
            'params': {'st_period': 10, 'st_mult': 4.0, 'rsi_period': 14, 'rsi_level': 50},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'SuperTrend+RSI for BTC',
            'note': 'H4/D1，高倍數ST+RSI確認',
        },
    ],

    'ADX_MACD': [
        {
            'name': 'BTC ADX+MACD',
            'params': {'adx_period': 14, 'adx_thresh': 20, 'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'ADX+MACD for BTC',
            'note': 'H4/D1，趨勢強度+MACD交叉',
        },
    ],

    'FRACTAL_BREAKOUT': [
        {
            'name': 'BTC Fractal 2',
            'params': {'period': 2},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Fractal for BTC',
            'note': 'H4/D1，分形突破',
        },
    ],

    'HEIKIN_ASHI': [
        {
            'name': 'BTC HA 5',
            'params': {'period': 5},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Heikin Ashi for BTC',
            'note': 'H4/D1，平滑K線趨勢',
        },
    ],

    'CHANDELIER_EXIT': [
        {
            'name': 'BTC CE 22/3.0',
            'params': {'atr_period': 22, 'multiplier': 3.0},
            'risk_percent': 0.3, 'sl_atr': 2.0, 'tp_atr': 4.0,
            'source': 'Chandelier Exit for BTC',
            'note': 'H4/D1，ATR追蹤止損',
        },
    ],

    'RAINBOW_MA': [
        {
            'name': 'BTC Rainbow 6/5',
            'params': {'ma_count': 6, 'step': 5},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Rainbow MA for BTC',
            'note': 'H4/D1，均線扇形排列',
        },
    ],

    'OPENING_RANGE': [
        {
            'name': 'BTC ORB 5',
            'params': {'opening_bars': 5},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Opening range for BTC',
            'note': 'H4，開盤區間突破',
        },
    ],

    'RANGE_EXPANSION': [
        {
            'name': 'BTC Range 14/2.0',
            'params': {'avg_period': 14, 'expansion_factor': 2.0},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Range expansion for BTC',
            'note': 'H4/D1，振幅擴張突破',
        },
    ],

    'PIVOT_POINT': [
        {
            'name': 'BTC Pivot 反轉',
            'params': {'pivot_mode': 1},
            'risk_percent': 0.3, 'sl_atr': 1.5, 'tp_atr': 3.0,
            'source': 'Pivot point for BTC',
            'note': 'H4/D1，樞軸點反轉',
        },
    ],
}


# ============================================================
# 風險管理預設（獨立，可搭配任何策略）
# ============================================================

RISK_PRESETS = {
    'conservative': {
        'label': '保守（保本優先）',
        'risk_percent': 0.3,
        'sl_atr': 1.5,
        'tp_atr': 3.0,
        'description': '低風險低回報。每月約 1-3% 穩定增長',
    },
    'moderate': {
        'label': '適中（平衡型）',
        'risk_percent': 0.5,
        'sl_atr': 2.0,
        'tp_atr': 4.0,
        'description': '風險收益平衡。每月約 3-8% 增長',
    },
    'standard': {
        'label': '標準（推薦）',
        'risk_percent': 1.0,
        'sl_atr': 2.5,
        'tp_atr': 5.0,
        'description': '業界標準。1:2 風險收益比',
    },
    'aggressive': {
        'label': '激進（高風險）',
        'risk_percent': 1.5,
        'sl_atr': 3.0,
        'tp_atr': 6.0,
        'description': '高風險高回報。回撤可能超過 20%',
    },
    'gold_safe': {
        'label': '黃金安全（XAUUSD 專用）',
        'risk_percent': 0.5,
        'sl_atr': 1.5,
        'tp_atr': 3.0,
        'description': '黃金波動大，自動降風險保護本金',
    },
}


# ============================================================
# 時間週期建議
# ============================================================

TIMEFRAME_GUIDE = {
    'M1':  {'signals_per_day': '極多', 'noise_ratio': '極高', 'suitable_for': '不推薦。雜訊太多'},
    'M5':  {'signals_per_day': '很多', 'noise_ratio': '高', 'suitable_for': '短線剝頭皮（需低延遲 VPS）'},
    'M15': {'signals_per_day': '多', 'noise_ratio': '中高', 'suitable_for': '日內交易，需盯盤'},
    'M30': {'signals_per_day': '中', 'noise_ratio': '中', 'suitable_for': '半日內交易，平衡信號與雜訊'},
    'H1':  {'signals_per_day': '數個', 'noise_ratio': '中低', 'suitable_for': '推薦。日內趨勢最佳週期'},
    'H4':  {'signals_per_day': '1-3', 'noise_ratio': '低', 'suitable_for': '推薦。波段交易，信號可靠'},
    'D1':  {'signals_per_week': '1-3', 'noise_ratio': '極低', 'suitable_for': '長線趨勢。持倉數天到數週'},
    'W1':  {'signals_per_month': '0-2', 'noise_ratio': '無', 'suitable_for': '超長線。每月最多一兩次'},
}

# 推薦週期對照
TIMEFRAME_RECOMMENDATIONS = {
    'MA_CROSSOVER':       ['H1', 'H4'],
    'RSI_CROSSOVER':      ['H1', 'M30'],
    'BOLLINGER_REVERSION': ['H1', 'M30'],
    'BOLLINGER_SQUEEZE':  ['H4', 'H1'],
    'TURTLE_BREAKOUT':    ['H4', 'D1'],
    'DYNAMIC_BREAKOUT':   ['H4', 'H1'],
    'PULSE_SYNC':         ['H4', 'H1'],
    'ICHIMOKU_CLOUD':     ['H4', 'D1'],
    'QUANTUM_VELOCITY':   ['H1', 'H4'],
    'MACD':               ['H1', 'H4'],
    'STOCHASTIC':         ['H1', 'M30'],
    'CCI':                ['H1', 'M30'],
    'WILLIAMS_R':         ['H1', 'M30'],
    'ROC':                ['H1', 'M30'],
    'AWESOME_OSCILLATOR': ['H1', 'H4'],
    'RSI_DIVERGENCE':     ['H4', 'H1'],
    'SUPERTREND':         ['H4', 'H1'],
    'PARABOLIC_SAR':      ['H1', 'M30'],
    'ADX':                ['H4', 'H1'],
    'KELTNER_CHANNEL':    ['H1', 'M30'],
    'EMA_ENVELOPE':       ['H1', 'M30'],
    'DONCHIAN_BREAKOUT':  ['H4', 'H1'],
    'HULL_MA':            ['H1', 'H4'],
    'TRIPLE_MA':          ['H1', 'H4'],
    'ZERO_LAG_EMA':       ['H1', 'M30'],
    'PIN_BAR':            ['H4', 'H1'],
    'ENGULFING':          ['H4', 'H1'],
    'INSIDE_BAR':         ['H4', 'H1'],
    'DOJI':               ['H4', 'H1'],
    'HAMMER_SHOOTING':    ['H4', 'H1'],
    'NR7':                ['H1', 'M30'],
    'MTF_MA_CROSSOVER':   ['H1', 'H4'],
    'MTF_BOLLINGER':      ['H4', 'H1'],
    'VOLATILITY_BREAKOUT': ['H4', 'H1'],
    'ATR_CHANNEL':        ['H4', 'H1'],
    'BOLLINGER_TREND':    ['H1', 'H4'],
    'RSI_EXTREME':        ['H4', 'H1'],
    'BOLLINGER_PERCENT_B': ['H1', 'M30'],
    'PRICE_CHANNEL':      ['H4', 'H1'],
    'LINEAR_REGRESSION':  ['H4', 'D1'],
    'MFI':                ['H1', 'H4'],
    'VOLUME_WEIGHTED_MA': ['H1', 'H4'],
    'MACD_BOLLINGER':     ['H4', 'H1'],
    'RSI_STOCH_HYBRID':   ['H4', 'H1'],
    'SUPERTREND_RSI':     ['H4', 'D1'],
    'ADX_MACD':           ['H4', 'H1'],
    'FRACTAL_BREAKOUT':   ['H4', 'H1'],
    'HEIKIN_ASHI':        ['H1', 'H4'],
    'CHANDELIER_EXIT':    ['H4', 'D1'],
    'RAINBOW_MA':         ['H4', 'D1'],
    'OPENING_RANGE':      ['H1', 'M30'],
    'RANGE_EXPANSION':    ['H4', 'H1'],
    'PIVOT_POINT':        ['H1', 'H4'],
}


# ============================================================
# API 輔助函數
# ============================================================

def get_presets(symbol: str, strategy_name: str) -> List[Dict[str, Any]]:
    """取得指定商品+策略的所有預設參數"""
    if symbol in ('XAUUSDm', 'XAUUSD', 'GOLD'):
        return XAUUSD_PRESETS.get(strategy_name, [])
    if symbol in ('BTCUSDm', 'BTCUSD', 'BTC'):
        return BTCUSD_PRESETS.get(strategy_name, [])
    return []

def get_risk_presets() -> Dict[str, Any]:
    return RISK_PRESETS

def get_timeframe_recommendations(strategy_name: str) -> List[str]:
    return TIMEFRAME_RECOMMENDATIONS.get(strategy_name, ['H1'])

def get_all_strategy_presets(symbol: str = 'XAUUSDm') -> Dict[str, List[Dict[str, Any]]]:
    """取得某商品所有策略的預設"""
    source = XAUUSD_PRESETS if symbol in ('XAUUSDm', 'XAUUSD', 'GOLD') else BTCUSD_PRESETS
    return dict(source)
