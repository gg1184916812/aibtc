# core/ai/price_target_predictor.py
"""
价格目标预测器 - 预测未来价格目标和到达时间
使用 LightGBM 回归模型
预测目标：
1. target_price: 未来 N 根 K 线内可能到达的价格（最高/最低）
2. target_time: 到达目标价需要的 K 线数量
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

from core.ai.feature_factory import FeatureFactory

class PriceTargetPredictor:
    """价格目标预测器"""
    
    def __init__(self):
        self.price_model = None
        self.time_model = None
        self.scaler = None
        self.feature_cols = None
        self.forward_bars = 20   # 预测未来 20 根 K 线
        self.price_target_type = 'high'  # 'high' or 'low'
    
    def prepare_labels(self, df: pd.DataFrame) -> tuple:
        """
        准备标签：
        - price_target: 未来 N 根 K 线内的最高价或最低价
        - time_to_target: 到达目标价需要的根数
        """
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        open_price = df['open'].values
        
        price_targets = []
        time_targets = []
        
        for i in range(len(df) - self.forward_bars - 1):
            # 未来窗口
            future_high = np.max(high[i+1:i+self.forward_bars+1])
            future_low = np.min(low[i+1:i+self.forward_bars+1])
            future_close = close[i+self.forward_bars]
            
            current_close = close[i]
            current_open = open_price[i]
            
            # 判断趋势方向
            # 如果收盘价 > 开盘价，且未来高点距离更远，预测高点
            # 如果收盘价 < 开盘价，且未来低点距离更远，预测低点
            up_distance = future_high - current_close
            down_distance = current_close - future_low
            
            # 如果向上空间大于向下空间，预测高点，否则预测低点
            # 用 forward 窗口末端的净方向决定主方向（比单根 open/close 稳健）
            net_move = future_close - current_close
            if net_move > 0:
                direction = 'UP'
            elif net_move < 0:
                direction = 'DOWN'
            else:
                direction = 'SIDEWAYS'

            # 目标根数 = 第一次触及方向极值的高/低价所用的根数
            if direction == 'UP':
                time_to_target = self.forward_bars
                for j in range(1, self.forward_bars + 1):
                    if high[i+j] >= future_high:
                        time_to_target = j
                        break
                target = close[i + time_to_target]
            elif direction == 'DOWN':
                time_to_target = self.forward_bars
                for j in range(1, self.forward_bars + 1):
                    if low[i+j] <= future_low:
                        time_to_target = j
                        break
                target = close[i + time_to_target]
            else:
                time_to_target = max(1, self.forward_bars // 2)
                target = future_close

            price_targets.append(target)
            time_targets.append(max(1, min(self.forward_bars, int(time_to_target))))
        
        return np.array(price_targets), np.array(time_targets)
    
    def train(self, df: pd.DataFrame, forward_bars: int = 20) -> 'PriceTargetPredictor':
        """训练模型"""
        self.forward_bars = forward_bars
        print(f"📊 训练价格目标预测器 (forward_bars={forward_bars})...")
        
        # 计算特征
        df_feat = FeatureFactory.compute_features(df)
        
        # 准备标签
        price_targets, time_targets = self.prepare_labels(df_feat)
        
        # 对齐特征和标签
        X = df_feat.iloc[:len(price_targets)].copy()
        
        # 移除不需要的列
        exclude = ['time', 'open', 'high', 'low', 'close', 'volume', 'tick_volume', 'real_volume', 'spread']
        X = X.drop(columns=[c for c in exclude if c in X.columns])
        
        self.feature_cols = list(X.columns)
        
        # 标准化
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # 划分训练集和测试集
        split_idx = int(len(X_scaled) * 0.8)
        X_train = X_scaled[:split_idx]
        X_test = X_scaled[split_idx:]
        
        y_price_train = price_targets[:split_idx]
        y_price_test = price_targets[split_idx:]
        y_time_train = time_targets[:split_idx]
        y_time_test = time_targets[split_idx:]
        
        # 训练价格预测模型
        print("🎯 训练价格预测模型 (LightGBM)...")
        self.price_model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            num_leaves=31,
            random_state=42,
            verbose=-1
        )
        self.price_model.fit(X_train, y_price_train)
        
        # 训练时间预测模型
        print("⏱️ 训练时间预测模型 (LightGBM)...")
        self.time_model = lgb.LGBMRegressor(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.05,
            num_leaves=31,
            random_state=42,
            verbose=-1
        )
        self.time_model.fit(X_train, y_time_train)
        
        # 评估
        price_pred = self.price_model.predict(X_test)
        time_pred = self.time_model.predict(X_test)
        
        price_r2 = r2_score(y_price_test, price_pred)
        price_mae = mean_absolute_error(y_price_test, price_pred)
        time_r2 = r2_score(y_time_test, time_pred)
        time_mae = mean_absolute_error(y_time_test, time_pred)
        
        print(f"📊 价格预测 R²: {price_r2:.4f}, MAE: ${price_mae:.2f}")
        print(f"📊 时间预测 R²: {time_r2:.4f}, MAE: {time_mae:.1f} 根K线")
        
        return self
    
    def predict(self, df_slice: pd.DataFrame) -> dict:
        """预测当前价格目标和时间"""
        try:
            df_feat = FeatureFactory.compute_features(df_slice.tail(100))
            if len(df_feat) == 0:
                return self._empty_prediction()
            
            latest = df_feat.iloc[-1:].copy()
            exclude = ['time', 'open', 'high', 'low', 'close', 'volume', 'tick_volume', 'real_volume', 'spread']
            X = latest.drop(columns=[c for c in exclude if c in latest.columns])
            X = X.reindex(columns=self.feature_cols, fill_value=0)
            X_scaled = self.scaler.transform(X)
            
            target_price = float(self.price_model.predict(X_scaled)[0])
            target_time = int(round(self.time_model.predict(X_scaled)[0]))
            target_time = max(1, min(self.forward_bars, target_time))

            current_price = df_slice['close'].iloc[-1]

            # 判断方向
            if target_price > current_price * 1.002:  # 0.2% 以上算涨
                direction = 'UP'
                movement_pct = (target_price - current_price) / current_price * 100
            elif target_price < current_price * 0.998:  # 0.2% 以上算跌
                direction = 'DOWN'
                movement_pct = (target_price - current_price) / current_price * 100
            else:
                direction = 'SIDEWAYS'
                movement_pct = 0

            # 合理性保护：单根 M5 历史极少超过约 2%，target_time 根内的累计涨幅不应离谱
            if direction != 'SIDEWAYS' and target_time > 0:
                per_bar_pct = abs(movement_pct) / target_time
                cap = 2.0
                if per_bar_pct > cap:
                    sign = 1 if direction == 'UP' else -1
                    movement_pct = sign * min(abs(movement_pct), cap * target_time)
                    target_price = current_price * (1 + movement_pct / 100.0)

            return {
                'current_price': current_price,
                'target_price': round(target_price, 2),
                'target_time': target_time,
                'direction': direction,
                'movement_percent': round(movement_pct, 2),
                'is_calibrated': True
            }
        except Exception as e:
            print(f"价格目标预测失败: {e}")
            return self._empty_prediction()
    
    def _empty_prediction(self) -> dict:
        """空预测"""
        return {
            'current_price': 0,
            'target_price': 0,
            'target_time': 5,
            'direction': 'UNKNOWN',
            'movement_percent': 0,
            'is_calibrated': False
        }
    
    def save(self, path: str):
        """保存模型"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'price_model': self.price_model,
                'time_model': self.time_model,
                'scaler': self.scaler,
                'feature_cols': self.feature_cols,
                'forward_bars': self.forward_bars
            }, f)
        print(f"✅ 价格目标模型已保存: {path}")
    
    def load(self, path: str) -> 'PriceTargetPredictor':
        """加载模型"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.price_model = data['price_model']
            self.time_model = data['time_model']
            self.scaler = data['scaler']
            self.feature_cols = data['feature_cols']
            self.forward_bars = data.get('forward_bars', 20)
        print(f"✅ 价格目标模型已加载: {path}")
        return self