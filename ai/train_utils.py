"""
共用训练工具：XGBoost 训练、概率校准、评估
统一所有训练入口的调用方式，消除重复代码
"""
import numpy as np
import pickle
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, cross_val_predict, StratifiedKFold, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
from sklearn.isotonic import IsotonicRegression
from sklearn.utils.class_weight import compute_class_weight

logger = logging.getLogger(__name__)


def train_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: Optional[np.ndarray] = None,
    y_val: Optional[np.ndarray] = None,
    params: Optional[Dict] = None,
    use_grid_search: bool = False,
    cv_folds: int = 3,
) -> Tuple[XGBClassifier, Dict[str, Any]]:
    """
    训练 XGBoost 分类器，支持自定义参数和自动调参

    Args:
        X_train: 训练特征
        y_train: 训练标签
        X_val: 验证集特征（可选）
        y_val: 验证集标签（可选）
        params: 自定义超参数字典，不提供则使用默认参数
        use_grid_search: 是否使用 GridSearchCV 自动调参
        cv_folds: 交叉验证折数

    Returns:
        (model, report) - 训练好的模型 + 训练报告 dict
    """
    default_params = dict(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        eval_metric='mlogloss',
        tree_method='hist',
        verbosity=0,
        early_stopping_rounds=30,
    )

    if params:
        merged = {**default_params, **params}
    else:
        merged = default_params

    report = {'params': merged, 'grid_search': use_grid_search}

    if use_grid_search:
        param_grid = {
            'max_depth': [4, 6, 8],
            'learning_rate': [0.03, 0.05, 0.07],
            'subsample': [0.7, 0.8, 0.9],
            'colsample_bytree': [0.7, 0.8, 0.9],
            'n_estimators': [200, 300, 500],
            'reg_alpha': [0.05, 0.1, 0.2],
            'reg_lambda': [0.8, 1.0, 1.5],
        }
        base_model = XGBClassifier(random_state=42, eval_metric='mlogloss', tree_method='hist', verbosity=0)
        # Use TimeSeriesSplit for financial data
        tscv = TimeSeriesSplit(n_splits=min(cv_folds, 3))
        grid = GridSearchCV(
            base_model, param_grid,
            cv=tscv, scoring='accuracy', n_jobs=-1, verbose=0
        )
        grid.fit(X_train, y_train)
        model = grid.best_estimator_
        report['best_params'] = grid.best_params_
        report['best_score'] = float(grid.best_score_)
        report['cv_results'] = {
            k: v.tolist() if isinstance(v, np.ndarray) else v
            for k, v in grid.cv_results_.items()
            if k in ('mean_test_score', 'std_test_score', 'rank_test_score', 'params')
        }
        logger.info(f"GridSearch best params: {grid.best_params_}, score: {grid.best_score_:.4f}")
    else:
        model = XGBClassifier(**merged)
        n_estimators = merged.get('n_estimators', 300)
        fit_kwargs = {'verbose': False}
        if X_val is not None and y_val is not None:
            fit_kwargs['eval_set'] = [(X_val, y_val)]
            fit_kwargs['early_stopping_rounds'] = merged.get('early_stopping_rounds', 30)
        model.fit(X_train, y_train, **fit_kwargs)

    return model, report


def calibrate_probabilities(
    model: XGBClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray,
    cv_folds: int = 3,
    n_classes: Optional[int] = None,
) -> Tuple[List[Optional[IsotonicRegression]], Dict[str, float]]:
    """
    使用 Isotonic Regression 对 XGBoost 输出概率进行校准

    Returns:
        (calibrators, cal_report) - 校准器列表 + 校准前后 Brier score
    """
    if n_classes is None:
        n_classes = len(np.unique(y_train))

    calibrators: List[Optional[IsotonicRegression]] = []
    cal_report = {}

    for i in range(n_classes):
        try:
            cv_proba = cross_val_predict(
                model, X_train, y_train,
                cv=min(cv_folds, 3), method='predict_proba', n_jobs=-1
            )[:, i]
            iso_reg = IsotonicRegression(out_of_bounds='clip')
            iso_reg.fit(cv_proba, (y_train == i).astype(int))
            calibrators.append(iso_reg)
            logger.info(f"Calibrator class {i} fitted successfully")
        except Exception as e:
            logger.warning(f"Calibrator class {i} failed: {e}")
            calibrators.append(None)

    return calibrators, cal_report


def evaluate_model(
    model: XGBClassifier,
    X_test: np.ndarray,
    y_test: np.ndarray,
    calibrators: Optional[List] = None,
    feature_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    全面评估模型，返回详细指标

    Returns:
        dict with keys: accuracy, precision, recall, f1, class_report, confusion_matrix,
                        feature_importance, calibrated_accuracy (if calibrators provided)
    """
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    n_classes = len(np.unique(y_test))
    acc = float(accuracy_score(y_test, y_pred))

    report = {
        'accuracy': acc,
        'precision_macro': float(precision_score(y_test, y_pred, average='macro', zero_division=0)),
        'recall_macro': float(recall_score(y_test, y_pred, average='macro', zero_division=0)),
        'f1_macro': float(f1_score(y_test, y_pred, average='macro', zero_division=0)),
        'classification_report': classification_report(y_test, y_pred, output_dict=True),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
    }

    if feature_names is not None and hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        top_n = min(20, len(feature_names))
        report['feature_importance'] = [
            {'feature': str(feature_names[i]), 'importance': float(importances[i])}
            for i in indices[:top_n]
        ]
        report['feature_importance_full'] = [
            {'feature': str(feature_names[i]), 'importance': float(importances[i])}
            for i in indices
        ]

    if calibrators:
        calibrated_proba = []
        for i in range(n_classes):
            if calibrators[i] is not None:
                calibrated_proba.append(calibrators[i].predict(y_proba[:, i]))
            else:
                calibrated_proba.append(y_proba[:, i])
        cal_proba = np.array(calibrated_proba).T
        cal_proba = cal_proba / (cal_proba.sum(axis=1, keepdims=True) + 1e-10)
        cal_pred = np.argmax(cal_proba, axis=1)
        report['calibrated_accuracy'] = float(accuracy_score(y_test, cal_pred))
        report['calibrated_f1'] = float(f1_score(y_test, cal_pred, average='macro', zero_division=0))

    return report


def safe_load_model(model_path: str):
    """
    安全加载 pickle 模型（处理 xgboost 版本不兼容导致的 dict 反序列化）

    三层回退策略:
    1. 原生 pickle.load (最常见)
    2. XGBClassifier().__setstate__(dict) + _Booster 验证
    3. 从 dict 中的 _Booster 原始字节重建 Booster → 挂载到新 XGBClassifier
    """
    with open(model_path, 'rb') as f:
        loaded = pickle.load(f)

    if not isinstance(loaded, dict):
        return loaded

    from xgboost import XGBClassifier, Booster

    # 策略1: __setstate__ (需要验证 _Booster 被正确恢复)
    try:
        new_model = XGBClassifier()
        new_model.__setstate__(loaded)
        # 关键验证：检查 _Booster 属性是否被正确初始化
        if hasattr(new_model, '_Booster') and new_model._Booster is not None:
            logger.warning(f"Model reconstructed via __setstate__: {model_path}")
            return new_model
    except Exception as e:
        logger.debug(f"__setstate__ failed: {e}")

    # 策略2: 从 _Booster 原始字节重建
    for booster_key in ['_Booster', 'Booster']:
        try:
            if booster_key in loaded and loaded[booster_key] is not None:
                booster_raw = loaded[booster_key]
                bst = Booster()
                if isinstance(booster_raw, str):
                    bst.load_model(bytearray(booster_raw, 'utf-8'))
                elif isinstance(booster_raw, (bytes, bytearray)):
                    bst.load_model(bytearray(booster_raw))
                else:
                    continue
                new_model = XGBClassifier()
                new_model._Booster = bst
                for param_key in ['n_estimators', 'max_depth', 'learning_rate', 'objective', 'n_features_in_']:
                    if param_key in loaded:
                        setattr(new_model, param_key, loaded[param_key])
                logger.warning(f"Model reconstructed via booster bytes: {model_path}")
                return new_model
        except Exception as e:
            logger.debug(f"Booster key {booster_key} failed: {e}")

    raise ValueError(
        f"Model file {model_path} contains dict, cannot reconstruct. "
        f"Keys: {list(loaded.keys())[:10]}. Try retraining the model."
    )


def save_model_artifacts(
    model_dir: str,
    base_name: str,
    model: XGBClassifier,
    scaler: StandardScaler,
    feature_cols: List[str],
    calibrators: Optional[List] = None,
    training_report: Optional[Dict] = None,
):
    """
    保存模型及所有关联文件
    """
    import os
    os.makedirs(model_dir, exist_ok=True)

    with open(os.path.join(model_dir, f"{base_name}.pkl"), 'wb') as f:
        pickle.dump(model, f)
    with open(os.path.join(model_dir, f"{base_name}_scaler.pkl"), 'wb') as f:
        pickle.dump(scaler, f)
    with open(os.path.join(model_dir, f"{base_name}_feature_cols.pkl"), 'wb') as f:
        pickle.dump(list(feature_cols), f)
    if calibrators is not None:
        with open(os.path.join(model_dir, f"{base_name}_calibrators.pkl"), 'wb') as f:
            pickle.dump(calibrators, f)
    if training_report is not None:
        with open(os.path.join(model_dir, f"{base_name}_report.pkl"), 'wb') as f:
            pickle.dump(training_report, f)
