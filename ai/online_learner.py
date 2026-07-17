
"""
在线学习：定期用新数据重新训练模型
"""
import os
import pickle
import pandas as pd
import logging
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from core.ai.feature_factory import FeatureFactory
from core.ai.label_generator import LabelGenerator

logger = logging.getLogger(__name__)

class OnlineLearner:
    def __init__(self, model_path='market_predictor.pkl', scaler_path='scaler.pkl'):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.retrain_interval_days = 7  # 每周重新训练
        self.last_retrain = None

    def should_retrain(self):
        """检查是否需要重新训练"""
        if self.last_retrain is None:
            return True
        return (datetime.now() - self.last_retrain).days >= self.retrain_interval_days

    def retrain(self, new_data: pd.DataFrame):
        """用新数据重新训练模型"""
        try:
            logger.info("Starting online retraining...")
            
            # 1. 加载旧数据（如果存在）
            # 可以从数据库或文件加载历史交易记录
            
            # 2. 合并新旧数据
            # all_data = pd.concat([old_data, new_data])
            
            # 3. 特征工程
            df_feat = FeatureFactory.compute_features(new_data)
            labels = LabelGenerator.generate_labels(df_feat, forward_bars=10)
            df_feat['label'] = labels
            df_feat = df_feat.dropna(subset=['label'])
            
            # 4. 训练
            X = df_feat.drop(columns=['label', 'time', 'open', 'high', 'low', 'close', 'volume'])
            y = df_feat['label'].astype(int)
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            model = XGBClassifier(
                n_estimators=300,
                max_depth=7,
                learning_rate=0.08,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss',
                tree_method='hist'
            )
            model.fit(X_scaled, y)
            
            # 5. 保存
            with open(self.model_path, 'wb') as f:
                pickle.dump(model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            self.last_retrain = datetime.now()
            logger.info(f"Online retraining completed. Model updated at {self.last_retrain}")
            return True
            
        except Exception as e:
            logger.error(f"Online retraining failed: {e}")
            return False