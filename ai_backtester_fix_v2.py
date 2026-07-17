# 這是一個獨立的修復腳本，用於修復 ai_backtester.py 的問題
# 主要修復:
# 1. 模型文件發現機制 (多路徑搜尋)
# 2. 詳細的偵錯日誌
# 3. safe_load_model 增強

import os
import sys
import pickle
import traceback
from pathlib import Path

# ============================================================
# 修復 1: 增強 safe_load_model
# ============================================================

def safe_load_model_enhanced(model_path: str):
    """
    增強版安全載入 pickle 模型 (處理 xgboost 版本問題)
    四層回退策略:
    1. 原生 pickle.load
    2. safe_load_model 標準重建
    3. 從 dict 中手動提取 Booster 二進制
    4. 嘗試用 joblib 載入 (不同序列化格式)
    """
    print(f"[safe_load_model] 開始載入: {model_path}", flush=True)
    
    if not os.path.exists(model_path):
        print(f"[safe_load_model] ❌ 文件不存在: {model_path}", flush=True)
        return None
    
    file_size = os.path.getsize(model_path)
    print(f"[safe_load_model] 文件大小: {file_size} bytes", flush=True)
    
    # 策略 0: 原生 pickle.load
    try:
        with open(model_path, 'rb') as f:
            loaded = pickle.load(f)
        print(f"[safe_load_model] pickle.load 成功，類型: {type(loaded).__name__}", flush=True)
        
        if not isinstance(loaded, dict):
            print(f"[safe_load_model] ✅ 非 dict，直接返回", flush=True)
            return loaded
        
        print(f"[safe_load_model] ⚠️ 是 dict，keys: {list(loaded.keys())[:15]}", flush=True)
    except Exception as e:
        print(f"[safe_load_model] ❌ pickle.load 失敗: {e}", flush=True)
        traceback.print_exc()
        return None

    # ========== 策略 1: __setstate__ ==========
    try:
        from xgboost import XGBClassifier
        new_model = XGBClassifier()
        new_model.__setstate__(loaded)
        if hasattr(new_model, '_Booster') and new_model._Booster is not None:
            print(f"[safe_load_model] ✅ 策略1 (__setstate__) 成功", flush=True)
            return new_model
        print(f"[safe_load_model] ⚠️ 策略1: _Booster 為 None", flush=True)
    except Exception as e:
        print(f"[safe_load_model] 策略1 失敗: {e}", flush=True)

    # ========== 策略 2: 從 _Booster 原始位元組重建 ==========
    try:
        from xgboost import Booster, XGBClassifier
        for booster_key in ['_Booster', 'Booster', 'booster']:
            if booster_key in loaded and loaded[booster_key] is not None:
                booster_raw = loaded[booster_key]
                print(f"[safe_load_model] 找到 booster 鍵: {booster_key}, 類型: {type(booster_raw).__name__}", flush=True)
                
                bst = Booster()
                if isinstance(booster_raw, str):
                    bst.load_model(bytearray(booster_raw, 'utf-8'))
                elif isinstance(booster_raw, (bytes, bytearray)):
                    bst.load_model(bytearray(booster_raw))
                else:
                    print(f"[safe_load_model] ⚠️ 無法處理的 booster 類型: {type(booster_raw)}", flush=True)
                    continue
                
                new_model = XGBClassifier()
                new_model._Booster = bst
                
                # 恢復關鍵參數
                param_mapping = {
                    'n_estimators': 'n_estimators',
                    'max_depth': 'max_depth', 
                    'learning_rate': 'learning_rate',
                    'objective': 'objective',
                    'n_features_in_': 'n_features_in_',
                    'n_classes_': 'n_classes_',
                    'classes_': 'classes_',
                }
                
                for dict_key, attr_name in param_mapping.items():
                    if dict_key in loaded and loaded[dict_key] is not None:
                        setattr(new_model, attr_name, loaded[dict_key])
                        print(f"[safe_load_model]   參數 {attr_name} = {loaded[dict_key]}", flush=True)
                
                print(f"[safe_load_model] ✅ 策略2 (booster bytes) 成功重建", flush=True)
                return new_model
    except Exception as e:
        print(f"[safe_load_model] 策略2 失敗: {e}", flush=True)
        traceback.print_exc()

    # ========== 策略 3: 嘗試 joblib 載入 ==========
    try:
        import joblib
        model = joblib.load(model_path)
        if model is not None and hasattr(model, 'predict_proba'):
            print(f"[safe_load_model] ✅ 策略3 (joblib) 成功", flush=True)
            return model
    except Exception as e:
        print(f"[safe_load_model] 策略3 (joblib) 失敗: {e}", flush=True)

    print(f"[safe_load_model] ❌ 所有策略都失敗，無法重建模型", flush=True)
    print(f"[safe_load_model]    可用 keys: {list(loaded.keys())}", flush=True)
    return None


# ============================================================
# 修復 2: 模型文件發現函數
# ============================================================

def find_model_files(symbol: str, timeframe: str, model_dir: str, project_root: str = None):
    """
    在多重路徑中搜尋模型文件
    返回 (model_path, scaler_path, feature_path, calibrator_path)
    """
    search_dirs = [model_dir]
    if project_root:
        search_dirs.append(project_root)
    
    # 可能的檔案命名模式
    base_patterns = [
        f"{symbol}_{timeframe}",
    ]
    
    # 如果 model_dir 中有以 symbol_timeframe 開頭的檔案，收集後綴
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for fname in os.listdir(search_dir):
            if fname.startswith(f"{symbol}_{timeframe}") and fname.endswith('.pkl'):
                parts = fname.replace('.pkl', '').split('_')
                # 提取可能的 epochs 部分
                if len(parts) >= 3:
                    epoch = parts[2]
                    base_patterns.append(f"{symbol}_{timeframe}_{epoch}")
    
    # 去重
    base_patterns = list(dict.fromkeys(base_patterns))
    
    print(f"[find_model_files] 搜尋目錄: {search_dirs}", flush=True)
    print(f"[find_model_files] 基本模式: {base_patterns}", flush=True)
    
    model_path = None
    scaler_path = None
    feature_path = None
    calibrator_path = None
    
    # 在所有目錄中搜尋
    for base in base_patterns:
        for search_dir in search_dirs:
            # 模型主文件
            model_candidate = os.path.join(search_dir, f"{base}.pkl")
            if not model_path and os.path.exists(model_candidate):
                # 確認不是輔助文件
                if not any(suffix in base for suffix in ['_scaler', '_feature_cols', '_calibrators', '_price_target']):
                    model_path = model_candidate
                    print(f"[find_model_files] ✅ 找到模型: {model_path}", flush=True)
            
            # scaler
            scaler_candidate = os.path.join(search_dir, f"{base}_scaler.pkl")
            if not scaler_path and os.path.exists(scaler_candidate):
                scaler_path = scaler_candidate
                print(f"[find_model_files] ✅ 找到 scaler: {scaler_path}", flush=True)
            
            # feature_cols
            feature_candidate = os.path.join(search_dir, f"{base}_feature_cols.pkl")
            if not feature_path and os.path.exists(feature_candidate):
                feature_path = feature_candidate
                print(f"[find_model_files] ✅ 找到 feature_cols: {feature_path}", flush=True)
            
            # calibrators
            cal_candidate = os.path.join(search_dir, f"{base}_calibrators.pkl")
            if not calibrator_path and os.path.exists(cal_candidate):
                calibrator_path = cal_candidate
                print(f"[find_model_files] ✅ 找到 calibrators: {calibrator_path}", flush=True)
    
    # 如果沒找到特定模型，嘗試使用根目錄的 market_predictor.pkl
    if not model_path:
        for search_dir in search_dirs:
            root_model = os.path.join(search_dir, 'market_predictor.pkl')
            if os.path.exists(root_model):
                model_path = root_model
                print(f"[find_model_files] ✅ 使用備用模型: {model_path}", flush=True)
                break
            # 也嘗試 llm 相關名稱
            for alt_name in ['predictor.pkl', 'model.pkl', 'state_model.pkl']:
                alt_path = os.path.join(search_dir, alt_name)
                if os.path.exists(alt_path):
                    model_path = alt_path
                    print(f"[find_model_files] ✅ 使用備用模型: {model_path}", flush=True)
                    break
            if model_path:
                break
    
    # 如果沒找到 scaler，嘗試根目錄
    if not scaler_path:
        for search_dir in search_dirs:
            root_scaler = os.path.join(search_dir, 'scaler.pkl')
            if os.path.exists(root_scaler):
                scaler_path = root_scaler
                print(f"[find_model_files] ✅ 使用備用 scaler: {scaler_path}", flush=True)
                break
    
    if not feature_path:
        for search_dir in search_dirs:
            for alt_name in ['feature_cols.pkl', 'feature_columns.pkl']:
                alt_path = os.path.join(search_dir, alt_name)
                if os.path.exists(alt_path):
                    feature_path = alt_path
                    print(f"[find_model_files] ✅ 使用備用 feature: {feature_path}", flush=True)
                    break
            if feature_path:
                break
    
    missing = []
    if not model_path:
        missing.append('model')
    if not scaler_path:
        missing.append('scaler')
    
    if missing:
        print(f"[find_model_files] ❌ 缺少文件: {missing}", flush=True)
        print(f"[find_model_files]    已搜尋目錄: {search_dirs}", flush=True)
        if search_dirs:
            for d in search_dirs:
                if os.path.exists(d):
                    all_files = [f for f in os.listdir(d) if f.endswith('.pkl')]
                    print(f"[find_model_files]    {d}/ 內容: {all_files}", flush=True)
    
    return model_path, scaler_path, feature_path, calibrator_path


# ============================================================
# 修復 3: 增強的模型載入驗證
# ============================================================

def validate_loaded_model(model, model_path: str):
    """
    驗證載入的模型是否可用，返回詳細報告
    """
    report = {
        'success': False,
        'type': type(model).__name__ if model is not None else 'None',
        'has_predict': False,
        'has_predict_proba': False,
        'is_dict': isinstance(model, dict),
        'error': None,
    }
    
    if model is None:
        report['error'] = 'Model is None'
        return report
    
    if isinstance(model, dict):
        report['error'] = f'Model is dict with keys: {list(model.keys())[:10]}'
        return report
    
    report['has_predict'] = hasattr(model, 'predict')
    report['has_predict_proba'] = hasattr(model, 'predict_proba')
    
    if not report['has_predict_proba']:
        report['error'] = f'Model 缺少 predict_proba 方法，可用方法: {[m for m in dir(model) if not m.startswith("_")][:20]}'
        return report
    
    if not report['has_predict']:
        report['error'] = 'Model 缺少 predict 方法'
        return report
    
    # 檢查是否有 fit 過的跡象
    if hasattr(model, 'n_features_in_'):
        report['n_features_in'] = model.n_features_in_
    if hasattr(model, 'n_classes_'):
        report['n_classes'] = model.n_classes_
    if hasattr(model, 'classes_'):
        report['classes'] = model.classes_.tolist() if hasattr(model.classes_, 'tolist') else list(model.classes_)
    
    report['success'] = True
    return report


if __name__ == '__main__':
    # 測試用
    project_root = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(project_root, 'ai_models')
    
    print("=" * 60)
    print("測試模型文件發現")
    print("=" * 60)
    
    for symbol, tf in [('XAUUSDm', 'M5'), ('BTCUSDm', 'M5'), ('XAUUSDm', 'H1')]:
        m, s, f, c = find_model_files(symbol, tf, model_dir, project_root)
        print(f"\n{symbol} {tf}: model={m}, scaler={s}, feature={f}, calibrator={c}")
    
    # 測試模型載入
    if m:
        print("\n" + "=" * 60)
        print("測試模型載入")
        print("=" * 60)
        model = safe_load_model_enhanced(m)
        report = validate_loaded_model(model, m)
        print(f"\n驗證結果: {report}")