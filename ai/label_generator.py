# core/ai/label_generator.py
"""
市场状态标签生成器（优化版 - 更敏感）
将未来N根K线的收益和波动离散化为4类：
0: 震荡（低收益低波动）
1: 多头趋势（正收益高波动）
2: 空头趋势（负收益高波动）
3: 高波动突破（高收益高波动）
"""
import pandas as pd
import numpy as np

class LabelGenerator:
    @staticmethod
    def generate_labels(df: pd.DataFrame, forward_bars: int = 10) -> pd.Series:
        """
        输入OHLCV DataFrame（必须包含close列）
        返回一个Series（索引与df对齐），标签为整数 0~3
        """
        close = df['close']
        high = df['high']
        low = df['low']
        
        # 未来收益率
        future_ret = close.shift(-forward_bars) / close - 1.0
        # 未来波动（用未来N根K线的最大最小范围）
        future_atr = (high.rolling(forward_bars).max() - low.rolling(forward_bars).min()).shift(-forward_bars) / close

        # ====== 优化：降低阈值，让模型更敏感 ======
        ret_threshold = 0.003   # 0.3%（原为 1%）
        vol_threshold = 0.01    # 1%（原为 2%）

        labels = []
        for ret, vol in zip(future_ret, future_atr):
            if pd.isna(ret) or pd.isna(vol):
                labels.append(np.nan)
            elif abs(ret) < ret_threshold and vol < vol_threshold:
                labels.append(0)   # 震荡
            elif ret > ret_threshold:
                labels.append(1)   # 多头趋势
            elif ret < -ret_threshold:
                labels.append(2)   # 空头趋势
            else:
                labels.append(3)   # 高波动突破
        return pd.Series(labels, index=df.index)