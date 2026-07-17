"""
在线学习：定期用新数据重新训练模型（完整 artifact 保存，配合 edge-filtered labels）
"""
import os
import pickle
import numpy as np
import pandas as pd
import logging
import threading
import time
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier
from collections import Counter
from core.ai.feature_factory import FeatureFactory
from core.ai.label_generator import LabelGenerator

logger = logging.getLogger(__name__)

class OnlineLearner:
    def __init__(self, symbol: str = 'XAUUSDm', timeframe: str = 'M5', retrain_interval_days: int = 7):
        self.symbol = symbol
        self.timeframe = timeframe
        self.retrain_interval_days = retrain_interval_days
        self.last_retrain = None
        self._scheduler_thread = None
        self._stop_scheduler = threading.Event()

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.model_dir = os.path.join(project_root, 'ai_models')
        os.makedirs(self.model_dir, exist_ok=True)

        self.model_path = os.path.join(self.model_dir, f"{symbol}_{timeframe}_online.pkl")
        self.scaler_path = os.path.join(self.model_dir, f"{symbol}_{timeframe}_online_scaler.pkl")
        self.feature_cols_path = os.path.join(self.model_dir, f"{symbol}_{timeframe}_online_feature_cols.pkl")
        self.calibrator_path = os.path.join(self.model_dir, f"{symbol}_{timeframe}_online_calibrators.pkl")
        self.data_path = os.path.join(project_root, 'backtest_data', f"{symbol}_{timeframe}_data.csv")

    def should_retrain(self) -> bool:
        if self.last_retrain is None:
            return True
        return (datetime.now() - self.last_retrain).days >= self.retrain_interval_days

    def _load_base_data(self) -> pd.DataFrame:
        """載入基礎歷史資料"""
        if os.path.exists(self.data_path):
            df = pd.read_csv(self.data_path, parse_dates=['time'])
            df.columns = [c.lower() for c in df.columns]
            return df
        return pd.DataFrame()

    def _append_live_data(self, df_base: pd.DataFrame) -> pd.DataFrame:
        """從 MT5 抓最新資料並去重合併（簡略版，實際可對接 data_download_service）"""
        try:
            from core.utils.mt5 import get_rates_mt5
            import MetaTrader5 as mt5
            tf_map = {'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5, 'M15': mt5.TIMEFRAME_M15,
                      'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4, 'D1': mt5.TIMEFRAME_D1}
            tf = tf_map.get(self.timeframe, mt5.TIMEFRAME_M5)

            live = get_rates_mt5(self.symbol, tf, 500)
            if live is not None and not live.empty:
                # get_rates_mt5() 目前把 'time' 設為 index，所以這裡要做相容處理
                live = live.copy()
                if 'time' in live.columns:
                    live['time'] = pd.to_datetime(live['time'], errors='coerce')
                elif getattr(live.index, 'name', None) == 'time':
                    live = live.reset_index()
                    live['time'] = pd.to_datetime(live['time'], errors='coerce')
                else:
                    # 額外容錯：若 index 是 datetime 但 name 不等於 time
                    if isinstance(live.index, pd.DatetimeIndex):
                        live = live.reset_index().rename(columns={live.index.name or 'index': 'time'})
                    else:
                        raise KeyError("Missing 'time' column/index in live data")

                # 欄位小寫化（用於後續統一）
                live.columns = [c.lower() for c in live.columns]
                df_base = df_base.copy()
                if 'time' in df_base.columns:
                    df_base['time'] = pd.to_datetime(df_base['time'], errors='coerce')
                elif getattr(df_base.index, 'name', None) == 'time':
                    df_base = df_base.reset_index()

                combined = pd.concat([df_base, live], ignore_index=True)
                if 'time' not in combined.columns:
                    raise KeyError("Combined data missing 'time' column")

                combined = combined.drop_duplicates(subset=['time'], keep='last')
                combined = combined.sort_values('time').reset_index(drop=True)
                return combined
        except Exception as e:
            logger.warning(f"Live data append failed, using base only: {e}")
        return df_base

    def retrain(self) -> bool:
        """用全部歷史+最新資料重新訓練，保存完整 artifact（model/scaler/feature_cols/calibrators）"""
        if not self.should_retrain():
            logger.info("Retrain interval not reached, skipping.")
            return False
        try:
            logger.info(f"[{self.symbol}_{self.timeframe}] Starting online retraining...")

            # 1. 載入並合併資料
            df_base = self._load_base_data()
            df = self._append_live_data(df_base)
            if len(df) < 200:
                logger.warning(f"Insufficient data: {len(df)} rows")
                return False

            # 2. 特徵工程
            df_feat = FeatureFactory.compute_features(df)
            if len(df_feat) < 100:
                return False

            # 3. 生成標籤（使用新的 edge-filtered LabelGenerator）
            labels = LabelGenerator.generate_labels(df_feat, forward_bars=10)
            df_feat['label'] = labels
            df_feat = df_feat.dropna(subset=['label'])
            label_counts = df_feat['label'].value_counts()
            if len(label_counts) < 2:
                logger.warning(f"Class diversity < 2: {dict(label_counts)}")
                return False

            # 4. 準備 X, y
            exclude_cols = ['label', 'time', 'open', 'high', 'low', 'close', 'volume', 'tick_volume', 'real_volume', 'spread']
            X = df_feat.drop(columns=[c for c in exclude_cols if c in df_feat.columns])
            y = df_feat['label'].astype(int)

            # 5. 標準化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # 6. 類別權重
            # 注意：y 的實際類別值可能是 [0,2] 這種「非連續」集合。
            # compute_class_weight 需要明確提供 classes，但後續映射 sample_weights 時不能用 int(l) 當成 index。
            classes = np.unique(y)
            class_weights_arr = compute_class_weight('balanced', classes=classes, y=y)
            class_weight_map = {int(c): float(w) for c, w in zip(classes, class_weights_arr)}
            sample_weights = np.array([class_weight_map[int(l)] for l in y])


            # 7. 訓練 XGBoost
            # XGBoost 在 multiclass 时要求 classes 推断一致。
            # 若 y 的类标签是非连续集合（例如 [0,2]），则需要把 y 映射到连续索引 [0..K-1]。
            class_values = np.unique(y)
            class_to_idx = {int(c): i for i, c in enumerate(class_values)}
            y_idx = y.map(class_to_idx).astype(int)

            num_class = len(class_values)

            # sample_weights 仍用原类权重映射
            sample_weights = np.array([class_weight_map[int(l)] for l in y])

            model = XGBClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.05,
                num_class=num_class if num_class > 2 else None,

                subsample=0.8, colsample_bytree=0.8, random_state=42,

                use_label_encoder=False, eval_metric='mlogloss',
                tree_method='hist', early_stopping_rounds=30
            )
            split_idx = int(len(X_scaled) * 0.8)
            X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_val = y_idx.iloc[:split_idx], y_idx.iloc[split_idx:]

            w_train, w_val = sample_weights[:split_idx], sample_weights[split_idx:]

            model.fit(X_train, y_train, sample_weight=w_train,
                      eval_set=[(X_val, y_val)], sample_weight_eval_set=[w_val], verbose=False)

            # 8. 概率校準（避免類別映射/校準過程觸發 sklearn 的類別推斷錯誤）
            # 目標：即使 y 的類別集合是非連續的（例如 [0,2]），也能穩定產生 calibrators。
            calibrators = []
            try:
                proba_all = model.predict_proba(X_train)
                model_classes = getattr(model, 'classes_', classes)
            except Exception:
                proba_all = None
                model_classes = classes

            for cls in classes:
                try:
                    y_bin = (y_train == cls).astype(int)
                    if y_bin.nunique() < 2 or proba_all is None:
                        calibrators.append(None)
                        continue

                    # 找到 model_classes 裡 cls 對應的機率列
                    cls_locs = np.where(model_classes == cls)[0]
                    if len(cls_locs) == 0:
                        calibrators.append(None)
                        continue
                    cls_index = int(cls_locs[0])

                    proba_cls = proba_all[:, cls_index]

                    iso = IsotonicRegression(out_of_bounds='clip')
                    iso.fit(proba_cls, y_bin)
                    calibrators.append(iso)
                except Exception:
                    calibrators.append(None)



            # 9. 保存完整 artifact
            with open(self.model_path, 'wb') as f:
                pickle.dump(model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            with open(self.feature_cols_path, 'wb') as f:
                pickle.dump(list(X.columns), f)
            with open(self.calibrator_path, 'wb') as f:
                pickle.dump(calibrators, f)

            self.last_retrain = datetime.now()
            logger.info(f"[{self.symbol}_{self.timeframe}] Online retraining DONE. Train={len(X_train)}, Val={len(X_val)}")
            return True

        except Exception as e:
            # 打印更多上下文，避免只看到一句 Invalid classes...
            try:
                logger.exception(
                    f"Online retraining failed: {e} | symbol={self.symbol} timeframe={self.timeframe} | data_path={self.data_path}"
                )
            except Exception:
                logger.error(f"Online retraining failed: {e}")
            return False


    # ===== Scheduler =====
    def start_scheduler(self, check_interval_hours: int = 12):
        """啟動背景排程（每 check_interval_hours 檢查一次是否需重訓）"""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return
        self._stop_scheduler.clear()

        def _run():
            while not self._stop_scheduler.is_set():
                if self.should_retrain():
                    self.retrain()
                for _ in range(check_interval_hours * 3600 // 60):
                    if self._stop_scheduler.is_set():
                        break
                    time.sleep(60)

        self._scheduler_thread = threading.Thread(target=_run, daemon=True)
        self._scheduler_thread.start()
        logger.info(f"[{self.symbol}_{self.timeframe}] OnlineLearner scheduler started (check every {check_interval_hours}h)")

    def stop_scheduler(self):
        self._stop_scheduler.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)


# 全域實例字典（依 symbol+timeframe 可多實例）
_online_learners = {}

def get_online_learner(symbol: str = 'XAUUSDm', timeframe: str = 'M5') -> OnlineLearner:
    key = f"{symbol}_{timeframe}"
    if key not in _online_learners:
        _online_learners[key] = OnlineLearner(symbol, timeframe)
    return _online_learners[key]

def start_all_schedulers():
    # 按需求只保留：BTCUSDm / XAUUSDm
    for sym, tf in [('XAUUSDm', 'M5'), ('BTCUSDm', 'M5')]:
        get_online_learner(sym, tf).start_scheduler()


def stop_all_schedulers():
    for lr in _online_learners.values():
        lr.stop_scheduler()