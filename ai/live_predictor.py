# core/ai/live_predictor.py
"""
实时推理：加载训练好的XGBoost模型，对最新数据窗口预测市场状态
支持特征名缺失时的降级处理
"""
import pickle
import pandas as pd
import numpy as np
import logging
from core.ai.feature_factory import FeatureFactory

logger = logging.getLogger(__name__)

class LivePredictor:
    def __init__(self, model_path: str = "market_predictor.pkl", scaler_path: str = "scaler.pkl"):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self._load_models()

    def _load_models(self):
        try:
            from core.ai.train_utils import safe_load_model
            self.model = safe_load_model(self.model_path)

            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            if hasattr(self.model, 'feature_names_in_'):
                self.feature_columns = list(self.model.feature_names_in_)
                logger.info(f"Model loaded with {len(self.feature_columns)} features: {self.feature_columns[:5]}...")
            else:
                logger.warning("Model has no feature_names_in_. Will use fallback feature selection.")
                if hasattr(self.model, 'feature_importances_'):
                    n_features = len(self.model.feature_importances_)
                    self.feature_columns = None
                else:
                    self.feature_columns = None
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.model = None
            self.scaler = None

    def predict(self, df: pd.DataFrame) -> dict:
        """
        输入最近至少50根K线的OHLCV DataFrame
        返回: {'state': int, 'confidence': float, 'probabilities': list}
        """
        if self.model is None:
            return {'state': -1, 'confidence': 0.0, 'probabilities': [], 'error': 'Model not loaded'}

        try:
            # 计算特征
            df_feat = FeatureFactory.compute_features(df)
            if len(df_feat) == 0:
                return {'state': -1, 'confidence': 0.0, 'probabilities': [], 'error': 'No features computed'}

            latest = df_feat.iloc[-1:].copy()

            # 如果模型有特征名，则对齐
            if self.feature_columns is not None:
                X = latest.reindex(columns=self.feature_columns, fill_value=0)
            else:
                # 降级：直接使用所有数值列（排除非特征列）
                exclude = ['time', 'open', 'high', 'low', 'close', 'volume', 'tick_volume']
                feature_cols = [c for c in latest.columns if c not in exclude]
                X = latest[feature_cols].copy()
                # 如果模型有 feature_importances_，则检查特征数
                if hasattr(self.model, 'feature_importances_'):
                    expected = len(self.model.feature_importances_)
                    if X.shape[1] != expected:
                        # 尝试填充或截断
                        if X.shape[1] < expected:
                            # 补零
                            for i in range(expected - X.shape[1]):
                                X[f'padding_{i}'] = 0
                        else:
                            X = X.iloc[:, :expected]
                        logger.warning(f"Adjusted features from {X.shape[1]} to {expected}")

            # 标准化
            if self.scaler is not None:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X.values

            proba = self.model.predict_proba(X_scaled)[0]
            pred = int(self.model.predict(X_scaled)[0])
            confidence = float(np.max(proba))

            return {
                'state': pred,
                'confidence': confidence,
                'probabilities': proba.tolist(),
                'error': None
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {'state': -1, 'confidence': 0.0, 'probabilities': [], 'error': str(e)}