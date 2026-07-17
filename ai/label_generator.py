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

        # ====== 优化：平衡阈值 + 风险调整 edge 过滤 ======
        # ret_threshold: 方向性最小收益率；vol_threshold: 高波动门槛
        # edge_ratio: 期望收益需 > edge_ratio * 波动，才視為可交易方向（否則歸為震盪 0）
        # 這能過濾掉「有微小漲跌但風險報酬差」的假信號，減少回測中頻繁觸及止損。
        ret_threshold = 0.005   # 0.5%
        vol_threshold = 0.015   # 1.5%
        edge_ratio = 0.5        # 期望收益至少為波動的 0.5 倍才視為有 edge

        labels = []

        for ret, vol in zip(future_ret, future_atr):
            if pd.isna(ret) or pd.isna(vol):
                labels.append(np.nan)
                continue

            # 默认都先准备 vol_safe，避免逻辑分支里未定义
            vol_safe = vol if (not pd.isna(vol) and vol > 0) else 1e-9

            if abs(ret) < ret_threshold and vol < vol_threshold:
                labels.append(0)   # 震荡
            elif ret > ret_threshold and abs(ret) > edge_ratio * vol_safe:
                labels.append(1)   # 多头趋势（有正期望 edge）
            elif ret < -ret_threshold and abs(ret) > edge_ratio * vol_safe:
                labels.append(2)   # 空头趋势（有正期望 edge）
            else:
                labels.append(0)   # 弱信號歸為震盪，避免假突破

        return pd.Series(labels, index=df.index)