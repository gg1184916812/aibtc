#!/usr/bin/env python3
"""
測試模型載入和策略切換
"""
import os
import sys
import pickle

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_model_files():
    """測試模型文件是否存在"""
    print("=" * 70)
    print("測試 1: 檢查模型文件")
    print("=" * 70)
    
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_models')
    print(f"模型目錄: {model_dir}")
    print(f"目錄存在: {os.path.exists(model_dir)}")
    
    if os.path.exists(model_dir):
        files = os.listdir(model_dir)
        pkl_files = [f for f in files if f.endswith('.pkl')]
        print(f"\n找到 {len(pkl_files)} 個 .pkl 文件:")
        for f in sorted(pkl_files):
            file_path = os.path.join(model_dir, f)
            size = os.path.getsize(file_path)
            print(f"  {f} ({size} bytes)")
    
    # 檢查特定模型
    print("\n檢查 XAUUSDm M5 模型:")
    base_name = "XAUUSDm_M5"
    required_files = [
        f"{base_name}.pkl",
        f"{base_name}_scaler.pkl",
        f"{base_name}_feature_cols.pkl",
        f"{base_name}_calibrators.pkl"
    ]
    
    for fname in required_files:
        fpath = os.path.join(model_dir, fname)
        exists = os.path.exists(fpath)
        status = "✅" if exists else "❌"
        print(f"  {status} {fname}")
    
    return model_dir

def test_model_loading():
    """測試模型載入"""
    print("\n" + "=" * 70)
    print("測試 2: 載入模型")
    print("=" * 70)
    
    try:
        from core.ai.train_utils import safe_load_model
        
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_models')
        model_path = os.path.join(model_dir, "XAUUSDm_M5.pkl")
        
        print(f"載入模型: {model_path}")
        print(f"文件存在: {os.path.exists(model_path)}")
        
        if os.path.exists(model_path):
            model = safe_load_model(model_path)
            print(f"\n載入結果:")
            print(f"  類型: {type(model)}")
            print(f"  是否為 None: {model is None}")
            
            if model is not None:
                print(f"  有 predict 方法: {hasattr(model, 'predict')}")
                print(f"  有 predict_proba 方法: {hasattr(model, 'predict_proba')}")
                
                if hasattr(model, 'n_features_in_'):
                    print(f"  特徵數量: {model.n_features_in_}")
                if hasattr(model, 'n_classes_'):
                    print(f"  類別數量: {model.n_classes_}")
                
                print("\n✅ 模型載入成功!")
                return True
            else:
                print("\n❌ 模型載入失敗: 返回 None")
                return False
        else:
            print(f"\n❌ 模型文件不存在")
            return False
            
    except Exception as e:
        print(f"\n❌ 模型載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scaler_loading():
    """測試 scaler 載入"""
    print("\n" + "=" * 70)
    print("測試 3: 載入 Scaler")
    print("=" * 70)
    
    try:
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_models')
        scaler_path = os.path.join(model_dir, "XAUUSDm_M5_scaler.pkl")
        
        print(f"載入 scaler: {scaler_path}")
        print(f"文件存在: {os.path.exists(scaler_path)}")
        
        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
            
            print(f"\n載入結果:")
            print(f"  類型: {type(scaler)}")
            print(f"  有 transform 方法: {hasattr(scaler, 'transform')}")
            
            if hasattr(scaler, 'n_features_in_'):
                print(f"  特徵數量: {scaler.n_features_in_}")
            
            print("\n✅ Scaler 載入成功!")
            return True
        else:
            print(f"\n❌ Scaler 文件不存在")
            return False
            
    except Exception as e:
        print(f"\n❌ Scaler 載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_feature_cols_loading():
    """測試特徵列載入"""
    print("\n" + "=" * 70)
    print("測試 4: 載入特徵列")
    print("=" * 70)
    
    try:
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_models')
        feature_path = os.path.join(model_dir, "XAUUSDm_M5_feature_cols.pkl")
        
        print(f"載入特徵列: {feature_path}")
        print(f"文件存在: {os.path.exists(feature_path)}")
        
        if os.path.exists(feature_path):
            with open(feature_path, 'rb') as f:
                feature_cols = pickle.load(f)
            
            print(f"\n載入結果:")
            print(f"  類型: {type(feature_cols)}")
            print(f"  特徵數量: {len(feature_cols)}")
            print(f"  前 10 個特徵: {feature_cols[:10]}")
            
            print("\n✅ 特徵列載入成功!")
            return True
        else:
            print(f"\n❌ 特徵列文件不存在")
            return False
            
    except Exception as e:
        print(f"\n❌ 特徵列載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prediction():
    """測試預測功能"""
    print("\n" + "=" * 70)
    print("測試 5: 執行預測")
    print("=" * 70)
    
    try:
        import pandas as pd
        import numpy as np
        from core.ai.feature_factory import FeatureFactory
        
        # 載入模型
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_models')
        model_path = os.path.join(model_dir, "XAUUSDm_M5.pkl")
        scaler_path = os.path.join(model_dir, "XAUUSDm_M5_scaler.pkl")
        feature_path = os.path.join(model_dir, "XAUUSDm_M5_feature_cols.pkl")
        
        from core.ai.train_utils import safe_load_model
        model = safe_load_model(model_path)
        
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        
        with open(feature_path, 'rb') as f:
            feature_cols = pickle.load(f)
        
        print("✅ 所有組件載入成功")
        print(f"  模型: {type(model).__name__}")
        print(f"  Scaler: {type(scaler).__name__}")
        print(f"  特徵數: {len(feature_cols)}")
        
        # 載入測試數據
        data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backtest_data', 'XAUUSDm_M5_20240101_20240131.csv')
        
        if not os.path.exists(data_file):
            print(f"\n⚠️ 測試數據不存在: {data_file}")
            print("尋找其他數據文件...")
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backtest_data')
            if os.path.exists(data_dir):
                files = os.listdir(data_dir)
                csv_files = [f for f in files if f.endswith('.csv')]
                if csv_files:
                    data_file = os.path.join(data_dir, csv_files[0])
                    print(f"使用: {csv_files[0]}")
        
        if os.path.exists(data_file):
            print(f"\n載入數據: {data_file}")
            df = pd.read_csv(data_file, parse_dates=['time'])
            print(f"數據量: {len(df)} 根K線")
            
            # 計算特徵
            df_feat = FeatureFactory.compute_features(df.tail(100))
            if len(df_feat) > 0:
                latest = df_feat.iloc[-1:].copy()
                X = latest.reindex(columns=feature_cols, fill_value=0)
                X_scaled = scaler.transform(X)
                
                print(f"\n執行預測...")
                print(f"  輸入形狀: {X_scaled.shape}")
                
                # 預測
                pred = int(model.predict(X_scaled)[0])
                proba = model.predict_proba(X_scaled)[0]
                confidence = float(max(proba))
                
                state_names = {0: '震盪', 1: '多頭趨勢', 2: '空頭趨勢', 3: '高波動突破'}
                
                print(f"\n✅ 預測成功!")
                print(f"  狀態: {pred} ({state_names.get(pred, '未知')})")
                print(f"  置信度: {confidence:.4f} ({confidence*100:.1f}%)")
                print(f"  概率分布: {proba}")
                
                return True
            else:
                print("\n❌ 特徵計算返回空數據")
                return False
        else:
            print(f"\n❌ 找不到測試數據")
            return False
            
    except Exception as e:
        print(f"\n❌ 預測失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("\n" + "=" * 70)
    print("AI 模型載入和預測測試")
    print("=" * 70)
    
    results = []
    
    # 測試 1: 檢查文件
    model_dir = test_model_files()
    result1 = bool(model_dir and os.path.exists(model_dir))
    results.append(("模型文件檢查", result1))
    
    # 測試 2: 載入模型
    results.append(("模型載入", test_model_loading()))
    
    # 測試 3: 載入 scaler
    results.append(("Scaler 載入", test_scaler_loading()))
    
    # 測試 4: 載入特徵列
    results.append(("特徵列載入", test_feature_cols_loading()))
    
    # 測試 5: 執行預測
    results.append(("預測功能", test_prediction()))
    
    # 總結
    print("\n" + "=" * 70)
    print("測試總結")
    print("=" * 70)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\n總計: {passed}/{total} 通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！模型載入正常。")
    else:
        print("\n⚠️ 部分測試失敗，請檢查上述錯誤信息。")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)