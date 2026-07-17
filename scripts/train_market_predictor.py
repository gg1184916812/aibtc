#!/usr/bin/env python3
"""
训练市场状态预测器（XGBoost + 概率校准）
使用历史CSV数据（OHLCV格式）
用法：
    python scripts/train_market_predictor.py
    python scripts/train_market_predictor.py --symbol XAUUSDm --timeframe H1 --epochs 100
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
import pickle
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, accuracy_score
from collections import Counter

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ai.feature_factory import FeatureFactory
from core.ai.label_generator import LabelGenerator

DEFAULT_SYMBOL = "BTCUSDm"
DEFAULT_TIMEFRAME = "H1"
DEFAULT_EPOCHS = 60

def find_data_dirs():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(project_root, 'lab', 'backtest_data'),
        os.path.join(project_root, 'backtest_data'),
        os.path.join(project_root, 'lab'),
        os.path.join(project_root, 'data'),
    ]
    return [d for d in candidates if os.path.exists(d)]

def load_data_from_csv(data_dir):
    all_dfs = []
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    for file in csv_files:
        filepath = os.path.join(data_dir, file)
        try:
            df = pd.read_csv(filepath, parse_dates=['time'])
            df.columns = [c.lower() for c in df.columns]
            required = ['time', 'open', 'high', 'low', 'close']
            if not all(c in df.columns for c in required):
                print(f"Skipping {file}: missing required columns")
                continue
            if 'tick_volume' in df.columns and 'volume' not in df.columns:
                df.rename(columns={'tick_volume': 'volume'}, inplace=True)
            elif 'volume' not in df.columns:
                df['volume'] = 0
            all_dfs.append(df)
            print(f"Loaded {file} ({len(df)} rows)")
        except Exception as e:
            print(f"Error loading {file}: {e}")
    if not all_dfs:
        raise ValueError(f"No valid CSV files found in {data_dir}")
    return pd.concat(all_dfs, ignore_index=True)

def main():
    parser = argparse.ArgumentParser(description='Train market state predictor')
    parser.add_argument('--data_dir', type=str, help='Directory containing CSV files')
    parser.add_argument('--symbol', type=str, default=DEFAULT_SYMBOL)
    parser.add_argument('--timeframe', type=str, default=DEFAULT_TIMEFRAME)
    parser.add_argument('--epochs', type=int, default=DEFAULT_EPOCHS)
    args = parser.parse_args()

    data_dir = args.data_dir
    if not data_dir:
        candidates = find_data_dirs()
        if candidates:
            data_dir = candidates[0]
            print(f"Auto-detected data directory: {data_dir}")
        else:
            print("Error: No data directory found. Please run lab/download_data.py first.")
            sys.exit(1)

    if not os.path.exists(data_dir):
        print(f"Error: Directory {data_dir} does not exist.")
        sys.exit(1)

    print("Loading historical data from:", data_dir)
    df = load_data_from_csv(data_dir)
    print(f"Total rows: {len(df)}")

    print("Computing features...")
    df_feat = FeatureFactory.compute_features(df)
    print(f"Features shape: {df_feat.shape}")

    print("Generating labels...")
    labels = LabelGenerator.generate_labels(df_feat, forward_bars=10)
    df_feat['label'] = labels
    df_feat = df_feat.dropna(subset=['label'])

    exclude_cols = ['label', 'time', 'open', 'high', 'low', 'close', 'volume', 'tick_volume', 'real_volume', 'spread']
    X = df_feat.drop(columns=[c for c in exclude_cols if c in df_feat.columns])
    y = df_feat['label'].astype(int)

    print(f"Final dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Feature columns: {list(X.columns)}")

    class_counts = Counter(y)
    print(f"Class distribution: {dict(class_counts)}")

    # 计算类别权重
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=np.unique(y),
        y=y
    )
    sample_weights = np.array([class_weights[int(label)] for label in y])
    print(f"Computed class weights: {dict(zip(np.unique(y), class_weights))}")

    # 划分训练集和测试集（使用时间序列分割，避免数据泄漏）
    split_idx = int(len(y) * 0.8)
    train_idx = np.arange(split_idx)
    test_idx = np.arange(split_idx, len(y))

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]
    train_weights = sample_weights[train_idx]
    test_weights = sample_weights[test_idx]

    # 标准化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"Training XGBoost model with {args.epochs} epochs...")

    model = XGBClassifier(
        n_estimators=args.epochs,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        use_label_encoder=False,
        eval_metric='mlogloss',
        tree_method='hist',
        early_stopping_rounds=30,
    )
    model.fit(
        X_train_scaled,
        y_train,
        sample_weight=train_weights,
        eval_set=[(X_test_scaled, y_test)],
        sample_weight_eval_set=[test_weights],
        verbose=False
    )

    # 评估
    y_pred = model.predict(X_test_scaled)
    print(f"Test accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))

    # ====== 概率校准（Platt Scaling via Isotonic Regression） ======
    print("\n🔧 正在进行概率校准...")
    n_classes = len(np.unique(y_train))
    calibrators = []

    for i in range(n_classes):
        try:
            # 使用3折交叉验证获取可靠的预测概率
            cv_proba = cross_val_predict(
                model, X_train_scaled, y_train, 
                cv=3, method='predict_proba', n_jobs=-1
            )[:, i]
            iso_reg = IsotonicRegression(out_of_bounds='clip')
            iso_reg.fit(cv_proba, (y_train == i).astype(int))
            calibrators.append(iso_reg)
            print(f"✅ 类别 {i} 校准完成")
        except Exception as e:
            print(f"⚠️ 类别 {i} 校准失败: {e}")
            calibrators.append(None)

    model.calibrators = calibrators

    # 校准后验证
    test_proba = model.predict_proba(X_test_scaled)
    calibrated_test_proba = []
    for i in range(n_classes):
        if calibrators[i] is not None:
            calibrated_test_proba.append(calibrators[i].predict(test_proba[:, i]))
        else:
            calibrated_test_proba.append(test_proba[:, i])
    calibrated_proba = np.array(calibrated_test_proba).T
    # 归一化
    calibrated_proba = calibrated_proba / calibrated_proba.sum(axis=1, keepdims=True)
    
    # 用校准后的概率重新计算准确率
    cal_pred = np.argmax(calibrated_proba, axis=1)
    cal_acc = accuracy_score(y_test, cal_pred)
    print(f"📊 校准后准确率: {cal_acc:.4f} (原准确率: {accuracy_score(y_test, y_pred):.4f})")

    # ====== 保存模型 ======
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_dir = os.path.join(project_root, 'ai_models')
    os.makedirs(model_dir, exist_ok=True)

    symbol = args.symbol
    timeframe = args.timeframe
    epochs = args.epochs

    model_name = f"{symbol}_{timeframe}_{epochs}.pkl"
    scaler_name = f"{symbol}_{timeframe}_scaler.pkl"
    feature_name = f"{symbol}_{timeframe}_feature_cols.pkl"
    calibrator_name = f"{symbol}_{timeframe}_calibrators.pkl"

    with open(os.path.join(model_dir, model_name), 'wb') as f:
        pickle.dump(model, f)
    with open(os.path.join(model_dir, scaler_name), 'wb') as f:
        pickle.dump(scaler, f)
    with open(os.path.join(model_dir, feature_name), 'wb') as f:
        pickle.dump(list(X.columns), f)
    with open(os.path.join(model_dir, calibrator_name), 'wb') as f:
        pickle.dump(calibrators, f)

    print(f"\n✅ 模型保存到: {os.path.join(model_dir, model_name)}")
    print(f"✅ Scaler保存到: {os.path.join(model_dir, scaler_name)}")
    print(f"✅ 特征列保存到: {os.path.join(model_dir, feature_name)}")
    print(f"✅ 校准器保存到: {os.path.join(model_dir, calibrator_name)}")

    print("\n📊 类别权重效果:")
    for cls, weight in zip(np.unique(y), class_weights):
        original_count = class_counts[cls]
        weighted_count = original_count * weight
        print(f"  类别 {cls}: 原始样本数 {original_count} → 加权样本数 {weighted_count:.0f}")

if __name__ == "__main__":
    main()