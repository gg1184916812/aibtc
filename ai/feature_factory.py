# core/ai/feature_factory.py
"""
特征工程：从OHLCV数据中提取20+技术指标特征
用于训练市场状态分类器
"""
import pandas as pd
import numpy as np  # 添加这一行
import pandas_ta as ta

class FeatureFactory:
    @staticmethod
    def compute_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        输入OHLCV DataFrame（含 time, open, high, low, close, volume）
        返回特征DataFrame（索引与df相同，包含所有特征列）
        """
        df = df.copy()
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df.get('volume', df.get('tick_volume'))

        # 1. 收益率特征
        df['ret_1'] = close.pct_change()
        df['ret_5'] = close.pct_change(5)
        df['ret_10'] = close.pct_change(10)
        df['ret_20'] = close.pct_change(20)

        # 2. 波动率（ATR）
        df['atr_14'] = ta.atr(high, low, close, length=14)
        df['atr_ratio'] = df['atr_14'] / close.rolling(50).mean()

        # 3. 趋势强度（ADX）
        adx_df = ta.adx(high, low, close, length=14)
        df['adx'] = adx_df['ADX_14']
        df['plus_di'] = adx_df['DMP_14']
        df['minus_di'] = adx_df['DMN_14']

        # 4. 均线乖离率
        for period in [10, 20, 50, 100]:
            ma = close.rolling(period).mean()
            df[f'ma_{period}_bias'] = (close - ma) / ma

        # 5. RSI
        df['rsi_14'] = ta.rsi(close, length=14)

        # 6. 布林带宽度（波动率压缩/扩张）
        bb = ta.bbands(close, length=20, std=2)
        df['bb_width'] = (bb['BBU_20_2.0'] - bb['BBL_20_2.0']) / bb['BBM_20_2.0']

        # 7. 价格位置（在近期高低点中的位置）
        for period in [10, 20, 50]:
            high_max = high.rolling(period).max()
            low_min = low.rolling(period).min()
            df[f'price_position_{period}'] = (close - low_min) / (high_max - low_min + 1e-6)

        # 8. 成交量特征（若存在）
        if volume is not None:
            df['volume_ratio'] = volume / volume.rolling(20).mean()
            df['volume_trend'] = (volume > volume.shift(1)).astype(int)

        # 9. 动量（ROC）
        for period in [5, 10, 20]:
            df[f'roc_{period}'] = ta.roc(close, length=period)

        # 10. 蜡烛实体比例（动能）
        df['body_ratio'] = abs(close - df['open']) / (high - low + 1e-6)

        df.dropna(inplace=True)
        return df