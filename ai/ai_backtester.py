# core/ai/ai_backtester.py
"""
AI 机器人回测器 - 完整版
模拟 AI 机器人在历史数据上的表现，包含：
- AI 市场状态预测
- 动态策略切换
- 价格目标预测
- 基于目标价的策略匹配
"""

import os
import sys
import pandas as pd
import numpy as np
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.ai.feature_factory import FeatureFactory
from core.ai.state_strategy_map import STATE_STRATEGY_MAP, select_strategy
from core.ai.price_target_predictor import PriceTargetPredictor
from core.strategies.strategy_map import resolve_strategy_class


class AIBacktester:
    """AI 机器人回测器 - 含价格目标预测"""
    
    def __init__(self, symbol: str, model_path: str, scaler_path: str, 
                 feature_cols_path: str = None, calibrator_path: str = None,
                 price_target_model_path: str = None,
                 typical_spread_pips: float = None, slippage_pips: float = None,
                 digits: int = 2, pip_size: float = 0.01,
                 max_spread_pips: float = None,
                 stop_out_ratio: float = 0.0,
                 confidence_threshold: float = 0.60):
        # --- 调试信息 ---
        # print("[AIBacktester __init__] ➡️ 开始初始化...")
        # print(f"[AIBacktester __init__]   - model_path: {model_path}")
        # print(f"[AIBacktester __init__]   - scaler_path: {scaler_path}")
        # print(f"[AIBacktester __init__]   - feature_cols_path: {feature_cols_path}")
        # print(f"[AIBacktester __init__]   - calibrator_path: {calibrator_path}")
        # print(f"[AIBacktester __init__]   - price_target_model_path: {price_target_model_path}")
        # --- 调试结束 ---
        # print("[AIBacktester __init__] ➡️ 开始初始化...")
        self.symbol = symbol
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.calibrators = None
        self.price_predictor = None

        try:
            # 加载 AI 模型
            print(f"[AIBacktester __init__] 准备从 {model_path} 加载模型...")
            load_success = self._load_model(model_path, scaler_path, feature_cols_path, calibrator_path)
            if not load_success:
                print("⚠️ [AIBacktester __init__] 模型加载失败，回测将在无 AI 模式下运行。")
            else:
                print("✅ [AIBacktester __init__] 模型加载流程完成。")

            # 加载价格目标模型
            if price_target_model_path and os.path.exists(price_target_model_path):
                self.price_predictor = PriceTargetPredictor()
                self.price_predictor.load(price_target_model_path)
                print("✅ [AIBacktester __init__] 价格目标模型已加载。")
        except Exception as e:
            print(f"❌❌❌ [AIBacktester __init__] 初始化过程中发生严重错误: {e}")
            import traceback
            traceback.print_exc()
        
        # 回测结果
        self.results = None
        self.trades = []
        self.equity_curve = []
        self.strategy_switches = []
        self.target_predictions = []
        self.strategy_usage = {}
        self.predictions_made = 0
        self.low_confidence_count = 0
        self.predict_errors = []
        
        # 初始资金
        self.initial_capital = 10000.0
        self.capital = self.initial_capital
        
        # 交易参数
        self.risk_percent = 1.0
        self.sl_atr_multiplier = 2.0
        self.tp_atr_multiplier = 4.0
        
        # 状态
        self.current_strategy = None
        self.current_params = None
        self.position = None  # 'long' or 'short'
        self.entry_price = 0
        self.sl_price = 0
        self.tp_price = 0
        self.lot_size = 0
        self.current_target = None
        
        # AI 预测置信度门槛（可配置）
        self.confidence_threshold = confidence_threshold
        
        # 合约规格
        self.contract_size = 100  # XAUUSD 默认
        self.digits = digits
        self.pip_size = pip_size

        # 點差 / 滑點（回測與實盤對齊，避免回測過度樂觀）
        # 若未傳入，按品種給預設典型點差
        self.typical_spread_pips = typical_spread_pips if typical_spread_pips is not None \
            else self._default_spread_pips(symbol)
        self.slippage_pips = slippage_pips if slippage_pips is not None else 0.5

        # 最大可交易點差（與實盤 trading_bot 的 max_spread 對齊）
        # 超過此點差則不開倉（低流動性時段），留空表示不限制
        self.max_spread_pips = max_spread_pips
        self.skipped_by_spread = 0

        # 爆倉/停機保護：資金低於初始資金的此比例即終止回測（實盤不可能負，預設 0=資金<=0 就停）
        self.stop_out_ratio = stop_out_ratio
        self.stopped_out = False

        # 目标价预测开关
        self.use_target_prediction = True

        # 可配置预测间隔
        self.prediction_interval = 10  # 增加到10，减少频繁预测

        # external hooks
        self.log_callback = None
        self.cancel_check = None
    
    def _load_model(self, model_path, scaler_path, feature_cols_path, calibrator_path):
        """加载 AI 模型（使用统一 safe_load_model，多层回退策略）"""
        # print(f"[模型加载] ➡️ 函数 _load_model 已被调用。")
        # print(f"[模型加载] model_path: {model_path}")
        # print(f"[模型加载] scaler_path: {scaler_path}")
        # print(f"[模型加载] feature_cols_path: {feature_cols_path}")
        # print(f"[模型加载] calibrator_path: {calibrator_path}")
        try:
            if model_path is None:
                # print(f"⚠️ [模型加载] model_path 为 None，跳过状态预测模型加载。")
                self.model = None
                self.scaler = None
                self.feature_cols = None
                self.calibrators = None
                return True # Indicate no state model was expected to be loaded

            # print(f"[模型加载] 开始加载模型: {model_path}")
            if not os.path.exists(model_path):
                # print(f"❌ 模型文件不存在: {model_path}")
                return False
            
            # 先尝试直接加载
            # print(f"[模型加载] 步骤 1: 尝试直接 pickle 加载模型文件 {model_path}...")
            with open(model_path, 'rb') as f:
                loaded = pickle.load(f)
            
            # print(f"[模型加载] pickle.load 返回类型: {type(loaded)}")
            
            # 检查是否是 dict（说明模型序列化有问题）
            if isinstance(loaded, dict):
                # print(f"[模型加载] ⚠️ 检测到 dict 格式，尝试使用 safe_load_model 修复...")
                # print(f"[模型加载] 字典 Keys: {list(loaded.keys())[:10]}")
                from core.ai.train_utils import safe_load_model
                self.model = safe_load_model(model_path)
            else:
                self.model = loaded
            
            # 详细验证模型
            # print(f"[模型加载] 步骤2: 验证模型对象...")
            # print(f"[模型加载]   - 模型类型: {type(self.model)}")
            # print(f"[模型加载]   - 是否为 None: {self.model is None}")
            # print(f"[模型加载]   - 是否为 dict: {isinstance(self.model, dict)}")
            
            if self.model is None:
                # print(f"❌ [模型加载] 模型加载后为None!")
                return False
            
            if isinstance(self.model, dict):
                # print(f"❌ [模型加载] 模型仍然是dict，无法使用!")
                # print(f"❌ [模型加载] 字典内容: {list(self.model.keys())}")
                return False
            
            # 检查必要的方法
            if not hasattr(self.model, 'predict_proba'):
                # print(f"❌ [模型加载] 模型缺少predict_proba方法!")
                # print(f"[模型加载] 可用方法: {[m for m in dir(self.model) if not m.startswith('_')]}")
                return False
            
            if not hasattr(self.model, 'predict'):
                # print(f"❌ [模型加载] 模型缺少predict方法!")
                return False
            
            # print(f"✅ [模型加载] 模型对象验证通过。")
            
            # 加载scaler
            # print(f"[模型加载] 步骤3: 加载scaler {scaler_path}...")
            if not os.path.exists(scaler_path):
                # print(f"❌ Scaler 文件不存在: {scaler_path}")
                return False
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            # print(f"✅ [模型加载] Scaler 加载成功: {type(self.scaler)}")
            
            # 加载特征列
            # print(f"[模型加载] 步骤4: 加载特征列 {feature_cols_path}...")
            if feature_cols_path and os.path.exists(feature_cols_path):
                with open(feature_cols_path, 'rb') as f:
                    self.feature_cols = pickle.load(f)
                    # print(f"✅ [模型加载] 加载了 {len(self.feature_cols)} 个特征列")
                    # print(f"[模型加载] 前10个特征: {self.feature_cols[:10] if len(self.feature_cols) > 10 else self.feature_cols}")
            else:
                # print(f"⚠️ [模型加载] 未找到特征列文件或未提供路径: {feature_cols_path}")
                self.feature_cols = None
            
            # 加载校准器
            # print(f"[模型加载] 步骤5: 加载校准器 {calibrator_path}...")
            if calibrator_path and os.path.exists(calibrator_path):
                with open(calibrator_path, 'rb') as f:
                    self.calibrators = pickle.load(f)
                # print(f"✅ [模型加载] 加载了 {len(self.calibrators) if self.calibrators else 0} 个校准器")
            else:
                # print(f"⚠️ [模型加载] 未找到校准器文件或未提供路径: {calibrator_path}")
                self.calibrators = None
            
            # print(f"✅✅✅ [模型加载] 所有组件加载完成！")
            # print(f"[模型加载] 最终状态: model={type(self.model).__name__}, scaler={type(self.scaler).__name__}, feature_cols={len(self.feature_cols) if self.feature_cols else 0}, calibrators={len(self.calibrators) if self.calibrators else 0}")
            return True
            
            
        except Exception as e:
            print(f"❌❌❌ [模型加载] 加载失败: {e}")
            # import traceback
            # traceback.print_exc()
            return False
    
    def _get_feature_columns(self, df: pd.DataFrame) -> list:
        """获取特征列"""
        if self.feature_cols:
            return self.feature_cols
        elif hasattr(self.model, 'feature_names_in_'):
            return list(self.model.feature_names_in_)
        else:
            exclude = ['time', 'open', 'high', 'low', 'close', 'volume', 'tick_volume', 'real_volume', 'spread']
            return [c for c in df.columns if c not in exclude and np.issubdtype(df[c].dtype, np.number)]
    
    def _predict_state(self, df_slice: pd.DataFrame) -> Dict[str, Any]:
        """预测单根 K 线的市场状态（增强版）"""
        if self.model is None:
            print("[DEBUG] _predict_state: 模型为 None，返回中性状态。")
            return {'state': 0, 'confidence': 0.0, 'error': 'Model not loaded'}
        if isinstance(self.model, dict):
            print("[DEBUG] _predict_state: 模型是 dict (加载失败)，返回中性状态。")
            return {'state': 0, 'confidence': 0.0, 'error': 'Model is dict (load failed)'}
        if not hasattr(self.model, 'predict_proba'):
            print("[DEBUG] Model has no predict_proba - returning confidence 0.0")
            return {'state': 0, 'confidence': 0.0, 'error': 'Model has no predict_proba'}
        try:
            df_feat = FeatureFactory.compute_features(df_slice)
            if len(df_feat) == 0:
                return {'state': 0, 'confidence': 0.0, 'error': 'No features computed'}
            
            # 特徵計算是最重的一步，計算後再次確認是否被取消
            if self.cancel_check and not self.cancel_check():
                return {'state': 0, 'confidence': 0.0, 'error': 'Cancelled'}
            
            latest = df_feat.iloc[-1:].copy()
            feature_cols = self._get_feature_columns(latest)
            
            # 動態特徵對齊：只使用模型訓練時的特徵列
            if feature_cols:
                # 找出當前數據中存在的特徵列
                available_features = [col for col in feature_cols if col in latest.columns]
                missing_features = [col for col in feature_cols if col not in latest.columns]
                
                if missing_features:
                    print(f"⚠️ 缺少特徵列: {missing_features}")
                
                if len(available_features) != len(feature_cols):
                    missing = [c for c in feature_cols if c not in available_features]
                    print(f"⚠️ 特徵列不匹配: 預期 {len(feature_cols)}, 實際可用 {len(available_features)}, 缺: {missing}")
                    # 仍使用模型訓練時的特徵列，缺漏欄位由 reindex 裝 0（保持與 scaler 維度一致）
                    feature_cols = self.feature_cols or feature_cols
                
                # 注意：不使用 df_feat 的全部欄位（含 time 等非數值），避免維度/型別錯誤
            
            X = latest.reindex(columns=feature_cols, fill_value=0)

            # 只保留数值型特徵列，避免 object/字串/時間欄位導致 np.isinf 報錯
            numeric_cols = [c for c in X.columns if np.issubdtype(X[c].dtype, np.number)]
            if len(numeric_cols) != len(X.columns):
                dropped = [c for c in X.columns if c not in numeric_cols]
                print(f"⚠️ 捨棄非數值特徵列: {dropped}")
            X = X[numeric_cols].astype(float)

            # 检查是否有 NaN 或 Inf（僅對數值張量做）
            X = X.fillna(0)
            X = X.replace([np.inf, -np.inf], 0)
            
            # DEBUG: Print first few feature values
            if hasattr(self, '_debug_state_count') and self._debug_state_count < 5:
                print(f"[DEBUG FUNCTION] Computing features for time {latest['time'].iloc[0]}")
                print(f"[DEBUG FUNCTION] feature_cols: {feature_cols[:5]}...")
                print(f"[DEBUG FUNCTION] X before scaling: {X.iloc[0].tolist()[:10] if len(X) > 0 else 'empty'}")
                self._debug_state_count += 1
            elif not hasattr(self, '_debug_state_count'):
                self._debug_state_count = 1
                
            X_scaled = self.scaler.transform(X) if self.scaler else X.values
            
            # DEBUG: Check scaled values
            if hasattr(self, '_debug_count') and self._debug_count < 3:
                print(f"[DEBUG] X_scaled shape: {X_scaled.shape}, values: {X_scaled.flatten()[:5]}")
                self._debug_count += 1
            elif not hasattr(self, '_debug_count'):
                self._debug_count = 1
                print(f"[DEBUG] X_scaled shape: {X_scaled.shape}, values: {X_scaled.flatten()[:5]}")

            raw_proba = self.model.predict_proba(X_scaled)[0]
            pred = int(self.model.predict(X_scaled)[0])
            
            # DEBUG: Check raw probabilities
            if hasattr(self, '_debug_prob_count') and self._debug_prob_count < 3:
                print(f"[DEBUG] raw_proba: {raw_proba}, sum: {np.sum(raw_proba)}")
                self._debug_prob_count += 1
            elif not hasattr(self, '_debug_prob_count'):
                self._debug_prob_count = 1
                print(f"[DEBUG] raw_proba: {raw_proba}, sum: {np.sum(raw_proba)}")
            
            if self.calibrators:
                calibrated_proba = []
                for i, calibrator in enumerate(self.calibrators):
                    if calibrator is not None and i < len(raw_proba):
                        calibrated_proba.append(calibrator.predict([raw_proba[i]])[0])
                    else:
                        calibrated_proba.append(raw_proba[i] if i < len(raw_proba) else 0.0)
                proba = np.array(calibrated_proba)
                proba = proba / (proba.sum() + 1e-10)
            else:
                proba = raw_proba
            
            # DEBUG: Check final probabilities
            if hasattr(self, '_debug_final_count') and self._debug_final_count < 3:
                print(f"[DEBUG] final proba: {proba}, max: {np.max(proba)}, argmax: {np.argmax(proba)}")
                self._debug_final_count += 1
            elif not hasattr(self, '_debug_final_count'):
                self._debug_final_count = 1
                print(f"[DEBUG] final proba: {proba}, max: {np.max(proba)}, argmax: {np.argmax(proba)}")
            
            # CRITICAL DEBUG: Check if probability is all zeros
            if np.allclose(proba, 0):
                print(f"[CRITICAL DEBUG] ALL ZEROS! raw_proba={raw_proba}")
                print(f"[CRITICAL DEBUG] model type: {type(self.model)}")
                print(f"[CRITICAL DEBUG] model params: {getattr(self.model, 'get_params', lambda: 'N/A')()}")
            
            confidence = float(max(proba))
            
            # 验证预测合理性
            if confidence < 0.3:
                # print(f"⚠️ 低置信度预测: {confidence:.3f}, 使用中性状态")
                return {'state': 0, 'confidence': confidence, 'probabilities': proba.tolist(), 'warning': 'Low confidence'}
            
            return {
                'state': pred,
                'confidence': confidence,
                'probabilities': proba.tolist(),
                'error': None
            }
        except Exception as e:
            # print(f"❌ 状态预测失败: {e}")
            self.predict_errors.append(str(e))
            return {'state': 0, 'confidence': 0.0, 'error': str(e)}
    
    def _predict_target(self, df_slice: pd.DataFrame) -> dict:
        """预测价格目标"""
        if self.price_predictor and self.use_target_prediction:
            try:
                return self.price_predictor.predict(df_slice)
            except Exception as e:
                print(f"价格目标预测失败: {e}")
                return self._simple_target_prediction(df_slice)
        else:
            return self._simple_target_prediction(df_slice)
    
    def _simple_target_prediction(self, df_slice: pd.DataFrame) -> dict:
        """简化版目标预测（基于 ATR）"""
        df = df_slice.tail(50)
        if len(df) < 20:
            return {
                'current_price': df_slice['close'].iloc[-1],
                'target_price': df_slice['close'].iloc[-1],
                'target_time': 5,
                'direction': 'UNKNOWN',
                'movement_percent': 0,
                'is_calibrated': False
            }
        
        close = df['close']
        high = df['high']
        low = df['low']
        
        atr = (high - low).rolling(14).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        current_price = close.iloc[-1]
        
        # 根据价格位置决定目标方向
        if current_price > ma20:
            target_price = ma20 + atr * 1.5
            direction = 'UP'
        elif current_price < ma20:
            target_price = ma20 - atr * 1.5
            direction = 'DOWN'
        else:
            target_price = ma20
            direction = 'SIDEWAYS'
        
        movement_pct = (target_price - current_price) / current_price * 100
        
        return {
            'current_price': current_price,
            'target_price': target_price,
            'target_time': 3,
            'direction': direction,
            'movement_percent': movement_pct,
            'is_calibrated': False
        }
    
    def _switch_strategy(self, state: int, confidence: float, target_info: dict = None):
        """根据状态和目标价切换策略（与实盘共用 select_strategy）"""
        # 使用配置的置信度阈值
        # print(f"[DEBUG _switch_strategy] 策略切换检查: state={state}, confidence={confidence:.4f}, threshold={self.confidence_threshold:.4f}, current_strategy={self.current_strategy}")
        
        if confidence < self.confidence_threshold:
            # print(f"[DEBUG _switch_strategy] 策略切换跳过: 置信度 {confidence:.4f} < 门槛 {self.confidence_threshold:.4f}")
            return False

        # 統一入口：狀態 + 目標價 + 表現排名覆蓋（回測=實盤）
        selection = select_strategy(state, target_info, self.symbol, "M5")
        new_strategy = selection['strategy']
        new_params = selection.get('params', {})
        reason = selection.get('reason', f"状态 {state}")
        source = selection.get('source', 'state_mapping')

        # print(f"[DEBUG _switch_strategy] 策略选择结果 from select_strategy: new_strategy={new_strategy}, reason='{reason}', source='{source}'")
        # print(f"[DEBUG _switch_strategy] Current strategy: {self.current_strategy}, New strategy: {new_strategy}")

        # 如果策略变化，记录切换
        if new_strategy != self.current_strategy:
            # print(f"[DEBUG _switch_strategy] 策略从 {self.current_strategy} 切换到 {new_strategy}. 記錄切換信息.")
            self.strategy_switches.append({
                'time': datetime.now(),
                'from_strategy': self.current_strategy,
                'to_strategy': new_strategy,
                'state': state,
                'confidence': confidence,
                'reason': reason,
                'source': source
            })
            self.current_strategy = new_strategy
            self.current_params = new_params
            # print(f"[DEBUG _switch_strategy] 策略已切换为: {new_strategy}")
            return True
        else:
            # print(f"[DEBUG _switch_strategy] 策略未改变: 仍为 {self.current_strategy}. 不记录切换.")
            return False
    
    def _analyze_strategy(self, df_slice: pd.DataFrame) -> str:
        """执行策略分析，返回信号"""
        if not self.current_strategy:
            return 'HOLD'
        
        try:
            strategy_class = resolve_strategy_class(self.current_strategy)
            if not strategy_class:
                return 'HOLD'
            
            class MockBot:
                pass
            mock_bot = MockBot()
            mock_bot.market_for_mt5 = self.symbol
            
            strategy_instance = strategy_class(bot_instance=mock_bot, params=self.current_params)
            analysis = strategy_instance.analyze(df_slice)
            signal = analysis.get('signal', 'HOLD')
            
            return signal
        except Exception as e:
            print(f"策略分析失败: {e}")
            return 'HOLD'
    
    def _default_spread_pips(self, symbol: str) -> float:
        """按品種返回典型點差（與實盤對齊）"""
        s = (symbol or '').upper()
        if 'XAU' in s:
            return 3.0
        if 'BTC' in s:
            return 8.0
        if 'EUR' in s or 'GBP' in s or 'USD' in s:
            return 1.5
        return 2.0

    def _entry_price(self, signal: str, close: float) -> float:
        """計算含點差+滑點的現實成交價（買入加、賣出減）"""
        half_spread = (self.typical_spread_pips * self.pip_size) / 2.0
        slip = self.slippage_pips * self.pip_size
        if signal == 'BUY':
            return close + half_spread + slip
        else:
            return close - half_spread - slip

    def _exit_price(self, position: str, target: float) -> float:
        """計算含點差+滑點的現實出場價（多頭出場減、空頭出場加）"""
        half_spread = (self.typical_spread_pips * self.pip_size) / 2.0
        slip = self.slippage_pips * self.pip_size
        if position == 'long':
            return target - half_spread - slip
        else:
            return target + half_spread + slip

    def _calculate_position_size(self, capital: float, atr: float) -> float:
        """计算仓位大小"""
        if atr <= 0:
            return 0.01
        
        sl_distance = atr * self.sl_atr_multiplier
        amount_to_risk = capital * (self.risk_percent / 100.0)
        
        # XAUUSD: $1 per pip per 0.01 lot
        sl_distance_pips = sl_distance / 0.01
        risk_per_lot = sl_distance_pips * 1.0
        lot_size = amount_to_risk / risk_per_lot if risk_per_lot > 0 else 0.01
        lot_size = max(0.01, min(0.1, lot_size))
        
        return lot_size
    
    def _execute_trade(self, signal: str, price: float, atr: float, timestamp, target_info: dict = None):
        """执行交易"""
        if signal == 'HOLD':
            return
        
        # 如果有持仓且信号反转，平仓（含點差滑點）
        if self.position == 'long' and signal == 'SELL':
            self._close_position(self._exit_price('long', price), timestamp, '信号转空')
            return
        elif self.position == 'short' and signal == 'BUY':
            self._close_position(self._exit_price('short', price), timestamp, '信号转多')
            return
        
        # 如果没有持仓，开仓
        if not self.position and signal in ['BUY', 'SELL']:
            self._open_position(signal, price, atr, timestamp, target_info)
    
    def _open_position(self, signal: str, price: float, atr: float, timestamp, target_info: dict = None):
        """开仓（增强版：添加详细日志）"""
        if atr <= 0:
            return

        # 低流動性過濾：點差超過上限則不開倉（與實盤 trading_bot 對齊）
        if self.max_spread_pips and self.typical_spread_pips > self.max_spread_pips:
            self.skipped_by_spread += 1
            if self.log_callback:
                self.log_callback(f'⏸️ 點差 {self.typical_spread_pips:.2f} 超過上限 {self.max_spread_pips:.2f}，跳過開倉')
            return

        # 计算手数
        lot_size = self._calculate_position_size(self.capital, atr)
        
        # 计算 SL/TP
        sl_distance = atr * self.sl_atr_multiplier
        
        # 如果有目标价，用目标价作为 TP
        if target_info and target_info.get('direction') != 'UNKNOWN':
            target_price = target_info['target_price']
            if signal == 'BUY' and target_price > price:
                tp_distance = target_price - price
            elif signal == 'SELL' and target_price < price:
                tp_distance = price - target_price
            else:
                tp_distance = atr * self.tp_atr_multiplier
        else:
            tp_distance = atr * self.tp_atr_multiplier
        
        # 現實成交價（含點差 + 滑點），SL/TP 以成交價為基準
        entry_price = self._entry_price(signal, price)
        
        if signal == 'BUY':
            sl_price = entry_price - sl_distance
            tp_price = entry_price + tp_distance
        else:
            sl_price = entry_price + sl_distance
            tp_price = entry_price - tp_distance
        
        self.position = 'long' if signal == 'BUY' else 'short'
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.lot_size = lot_size
        self.current_target = target_info
        
        trade_detail = {
            'time': timestamp,
            'action': 'OPEN',
            'signal': signal,
            'strategy': self.current_strategy,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'lot_size': lot_size,
            'atr': atr,
            'target_info': target_info,
            'capital': self.capital
        }
        
        self.trades.append(trade_detail)
        
        if self.log_callback:
            direction = '做多' if signal == 'BUY' else '做空'
            self.log_callback(
                f'📈 {direction} {entry_price:.2f} | 手数: {lot_size:.3f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | 资金: ${self.capital:.2f}',
                trade_detail
            )
    
    def _close_position(self, exit_price: float, timestamp, reason: str):
        """平仓（增强版：添加详细日志）"""
        if not self.position:
            return
        
        if self.position == 'long':
            profit = (exit_price - self.entry_price) * self.lot_size * self.contract_size
        else:
            profit = (self.entry_price - exit_price) * self.lot_size * self.contract_size
        
        self.capital += profit
        if self.capital < 0:
            self.capital = 0.0
            self.stopped_out = True
        
        trade_detail = {
            'time': timestamp,
            'action': 'CLOSE',
            'direction': self.position,
            'entry_price': self.entry_price,
            'exit_price': exit_price,
            'profit': profit,
            'reason': reason,
            'capital': self.capital,
            'lot_size': self.lot_size,
            'remaining_balance': self.capital
        }
        
        self.trades.append(trade_detail)
        
        if self.log_callback:
            emoji = '✅' if profit > 0 else '❌'
            self.log_callback(
                f'{emoji} 平仓 {exit_price:.2f} | 盈亏: ${profit:.2f} | 原因: {reason} | 资金: ${self.capital:.2f}',
                trade_detail
            )
        
        self.position = None
        self.entry_price = 0
        self.sl_price = 0
        self.tp_price = 0
        self.lot_size = 0
        self.current_target = None
    
    def _check_stop_loss_take_profit(self, current_bar, timestamp) -> bool:
        """检查是否触及止损或止盈"""
        if not self.position:
            return False
        
        high = current_bar['high']
        low = current_bar['low']
        
        if self.position == 'long':
            if low <= self.sl_price:
                self._close_position(self._exit_price('long', self.sl_price), timestamp, '止损')
                return True
            elif high >= self.tp_price:
                self._close_position(self._exit_price('long', self.tp_price), timestamp, '止盈')
                return True
        else:
            if high >= self.sl_price:
                self._close_position(self._exit_price('short', self.sl_price), timestamp, '止损')
                return True
            elif low <= self.tp_price:
                self._close_position(self._exit_price('short', self.tp_price), timestamp, '止盈')
                return True
        
        return False
    
    def run(self, df: pd.DataFrame, cancel_check=None) -> Dict[str, Any]:
        """运行回测（增强版：支持取消检查和详细日志）"""
        self.cancel_check = cancel_check
        
        if self.log_callback:
            self.log_callback(f'📊 开始回测 {len(df)} 根 K 线')
        
        print("\n" + "="*70)
        print("🚀 AI 机器人回测启动")
        print("="*70)
        print(f"📊 数据量: {len(df)} 根 K 线")
        print(f"📅 时间范围: {df['time'].iloc[0]} 到 {df['time'].iloc[-1]}")
        print(f"💰 初始资金: ${self.initial_capital:,.2f}")
        print(f"🎯 目标预测: {'启用' if self.use_target_prediction else '禁用'}")
        print("="*70)

        # 在回测开始前再次检查模型：如果状态模型和价格模型都未加载，则无法运行
        if self.model is None and self.price_predictor is None:
            error_msg = "❌ 严重错误: 状态预测模型和价格目标模型均未能加载，无法开始回测。"
            print(error_msg)
            if self.log_callback: self.log_callback(error_msg)
            return self._generate_report() # 返回一个空的报告
        
        self.capital = self.initial_capital
        self.trades = []
        self.equity_curve = [{'time': df['time'].iloc[0], 'capital': max(0.0, self.capital)}]
        self.strategy_switches = []
        self.target_predictions = []
        self.position = None
        
        # 初始化策略
        self.current_strategy = 'BOLLINGER_REVERSION'
        self.current_params = {'bb_length': 20, 'bb_std': 2.0, 'trend_filter_period': 50}
        self.strategy_usage = {self.current_strategy: 0}  # 記錄每個策略被使用的次數
        self.predictions_made = 0
        self.low_confidence_count = 0
        self.predict_errors = []
        
        # 确保数据按时间排序
        df = df.sort_values('time').reset_index(drop=True)
        
        # 计算 ATR
        import pandas_ta as ta
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df = df.dropna()
        
        # 逐根 K 线回测
        min_bars = 100
        total_bars = len(df)
        last_prediction_idx = -1
        last_progress_log = -1
        
        for i in range(min_bars, total_bars):
            # 检查取消
            if self.cancel_check and not self.cancel_check():
                if self.log_callback:
                    self.log_callback('🛑 回测已取消')
                break

            # 爆倉/停機保護：資金跌破停機線即終止（對應實盤不可能負、需停機）
            # 若 stop_out_ratio 為 0，則使用 0 作為停機線（資金<=0 時停止）
            stop_out_capital = self.initial_capital * self.stop_out_ratio if self.stop_out_ratio > 0 else 0.0
            if self.capital <= stop_out_capital:
                if self.position:
                    last_bar = df.iloc[i]
                    self._close_position(self._exit_price(self.position, last_bar['close']), last_bar['time'], '停機平倉')
                self.stopped_out = True
                if self.log_callback:
                    self.log_callback(f'⛔ 資金 ${self.capital:.2f} 跌破停機線，終止回測')
                break
            
            current_bar = df.iloc[i]
            current_time = current_bar['time']
            
            # 获取历史窗口
            window = df.iloc[:i+1].copy()
            
            # 1. AI 状态预测
            if i - last_prediction_idx >= self.prediction_interval:
                prediction = self._predict_state(window)
                state = prediction['state']
                confidence = prediction['confidence']
                last_prediction_idx = i
                self.predictions_made += 1
                
                if confidence < self.confidence_threshold:
                    self.low_confidence_count += 1
                
                # 2. 价格目标预测
                target_info = None
                if self.use_target_prediction:
                    target_info = self._predict_target(window)
                    if target_info.get('direction') != 'UNKNOWN':
                        self.target_predictions.append({
                            'time': current_time,
                            'target_info': target_info
                        })
                        if i % 50 == 0:  # 每 50 根打印一次
                            print(f"🎯 [{current_time}] 目标: ${target_info['target_price']:.2f} "
                                  f"({target_info['direction']}) {target_info['target_time']}根K线")
                
                # 3. 切换策略
                prev_strategy = self.current_strategy
                switched = self._switch_strategy(state, confidence, target_info)
                if switched:
                    print(f"[DEBUG] 策略从 {prev_strategy} 切换到 {self.current_strategy}, 置信度={confidence:.4f}")
                if switched and self.log_callback:
                    self.log_callback(f'🔄 策略切换: {self.current_strategy}')
            
            # 記錄當前策略使用情況（即使沒有切換）
            self.strategy_usage[self.current_strategy] = self.strategy_usage.get(self.current_strategy, 0) + 1
            
            # 4. 策略信号分析
            signal = self._analyze_strategy(window)
            
            # 分析完策略後再次檢查是否已取消，避免多做後續處理
            if self.cancel_check and not self.cancel_check():
                if self.log_callback:
                    self.log_callback('🛑 回测已取消')
                break
            
            # 5. 检查止损止盈
            if self.position:
                if self._check_stop_loss_take_profit(current_bar, current_time):
                    continue
            
            # 6. 执行交易
            self._execute_trade(signal, current_bar['close'], current_bar['atr'], current_time, self.current_target)
            
            # 每 500 根 K 線回報一次進度，避免 CMD 看起來像卡住
            if i - last_progress_log >= 500:
                last_progress_log = i
                pct = int((i - min_bars) / (total_bars - min_bars) * 100)
                if self.log_callback:
                    self.log_callback(f'⏳ 回测进度: {pct}% ({i - min_bars}/{total_bars - min_bars} 根 K 线)')
            # 记录权益
            equity_capital = max(0.0, self.capital)
            if not self.position:
                self.equity_curve.append({
                    'time': current_time,
                    'capital': equity_capital
                })
            else:
                if self.position == 'long':
                    unrealized = (self._exit_price('long', current_bar['close']) - self.entry_price) * self.lot_size * self.contract_size
                else:
                    unrealized = (self.entry_price - self._exit_price('short', current_bar['close'])) * self.lot_size * self.contract_size
                current_equity = equity_capital + unrealized
                self.equity_curve.append({
                    'time': current_time,
                    'capital': max(0.0, current_equity)
                })
        
        # 如果最后还有持仓，按最后价格平仓（含點差滑點）
        if self.position:
            last_bar = df.iloc[-1]
            self._close_position(self._exit_price(self.position, last_bar['close']), last_bar['time'], '回测结束平仓')
            if self.log_callback:
                self.log_callback(f'🏁 平仓最后持仓，最终资金: ${self.capital:.2f}')
        
        # 生成报告
        report = self._generate_report()
        
        # 同時印到 CMD 與前端，確保後端 console 也能看到完成狀態
        completion_msg = f'✅ 回测完成，总交易: {report["total_trades"]}，盈亏: ${report["total_profit"]:.2f}'
        print(completion_msg)
        print(f'   預測次數: {self.predictions_made} | 低信心度(<{self.confidence_threshold}): {self.low_confidence_count} 次')
        print(f'   策略切換: {len(self.strategy_switches)} 次 | 交易明細: {len([t for t in self.trades if t["action"] == "CLOSE"])} 筆')
        print(f'   策略使用分佈: {self.strategy_usage}')
        print(f'   最終資金: ${max(0.0, self.capital):.2f} | 權益曲線點數: {len(self.equity_curve)}')
        if self.predict_errors:
            print(f'   預測錯誤: {len(self.predict_errors)} 次')
            for err in self.predict_errors[:3]:
                print(f'      - {err}')
        if self.log_callback:
            self.log_callback(completion_msg)
        
        return report
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成回测报告"""
        open_trades = [t for t in self.trades if t['action'] == 'OPEN']
        close_trades = [t for t in self.trades if t['action'] == 'CLOSE']
        
        total_trades = len(close_trades)
        winning_trades = [t for t in close_trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in close_trades if t.get('profit', 0) < 0]
        
        total_profit = sum([t.get('profit', 0) for t in close_trades])
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        # 最大回撤
        max_drawdown = 0
        if self.equity_curve:
            peak = max(0.0, self.initial_capital)
            for eq in self.equity_curve:
                eq_cap = eq.get('capital', 0) or 0
                if eq_cap > peak:
                    peak = eq_cap
                drawdown = (peak - eq_cap) / peak * 100 if peak > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        # 策略切换统计
        switches_by_strategy = {}
        for s in self.strategy_switches:
            to_strategy = s.get('to_strategy', 'UNKNOWN')
            switches_by_strategy[to_strategy] = switches_by_strategy.get(to_strategy, 0) + 1
        
        # 目标预测统计
        target_stats = {
            'total': len(self.target_predictions),
            'by_direction': {}
        }
        for tp in self.target_predictions:
            direction = tp.get('target_info', {}).get('direction', 'UNKNOWN')
            target_stats['by_direction'][direction] = target_stats['by_direction'].get(direction, 0) + 1
        
        # 平均目标时间
        avg_target_time = 0
        if self.target_predictions:
            avg_target_time = sum([tp.get('target_info', {}).get('target_time', 0) for tp in self.target_predictions]) / len(self.target_predictions) if self.target_predictions else 0
        
        # 计算额外指标
        profit_factor = '-'
        avg_loss = 0
        avg_win = 0
        if losing_trades:
            avg_loss = -sum([t.get('profit', 0) for t in losing_trades]) / len(losing_trades)
            avg_win = sum([t.get('profit', 0) for t in winning_trades]) / len(winning_trades) if winning_trades else 0
            profit_factor = round(avg_win / avg_loss, 2) if avg_loss > 0 else '-'
        elif winning_trades:
            avg_win = sum([t.get('profit', 0) for t in winning_trades]) / len(winning_trades)
        
        # 最大连胜/连亏
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_win = 0
        current_loss = 0
        for t in close_trades:
            if t.get('profit', 0) > 0:
                current_win += 1
                current_loss = 0
                max_consecutive_wins = max(max_consecutive_wins, current_win)
            else:
                current_loss += 1
                current_win = 0
                max_consecutive_losses = max(max_consecutive_losses, current_loss)
        
        # 夏普比率 (简单计算)
        sharpe_ratio = 0
        if close_trades:
            returns = [t.get('profit', 0) / self.initial_capital for t in close_trades]
            if len(returns) > 1 and self.initial_capital > 0:
                import statistics
                mean_ret = statistics.mean(returns)
                std_ret = statistics.stdev(returns) if len(returns) > 1 else 0
                sharpe_ratio = (mean_ret / std_ret) * np.sqrt(252) if std_ret > 0 else 0 # 假设每日数据
        
        # Calmar比率
        calmar_ratio = 0
        if max_drawdown > 0:
            total_profit_percent = (self.capital - self.initial_capital) / self.initial_capital if self.initial_capital > 0 else 0
            calmar_ratio = total_profit_percent / (max_drawdown / 100) if max_drawdown > 0 else 0
        
        final_capital = max(0.0, self.capital)
        total_profit_clean = final_capital - self.initial_capital
        
        return {
            'symbol': self.symbol,
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_profit': total_profit_clean,
            'total_profit_percent': (total_profit_clean / self.initial_capital) * 100 if self.initial_capital > 0 else 0,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'strategy_switches': self.strategy_switches,
            'switches_count': len(self.strategy_switches),
            'switches_by_strategy': switches_by_strategy,
            'strategy_usage': self.strategy_usage,
            'target_predictions': self.target_predictions,
            'target_stats': target_stats,
            'avg_target_time': avg_target_time,
            'trade_log': self.trades,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'use_target_prediction': self.use_target_prediction,
            'typical_spread_pips': self.typical_spread_pips,
            'slippage_pips': self.slippage_pips,
            'max_spread_pips': self.max_spread_pips,
            'skipped_by_spread': self.skipped_by_spread,
            'stop_out_ratio': self.stop_out_ratio,
            'stopped_out': getattr(self, 'stopped_out', False),
            'sharpe_ratio': sharpe_ratio,
            'calmar_ratio': calmar_ratio,
            'profit_factor': profit_factor,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
        }
    
    def print_report(self, report: Dict[str, Any]):
        """打印回测报告"""
        print("\n" + "="*70)
        print("📊 AI 机器人回测报告")
        print("="*70)
        print(f"\n📈 品种: {report['symbol']}")
        print(f"💰 初始资金: ${report['initial_capital']:,.2f}")
        print(f"💰 最终资金: ${report['final_capital']:,.2f}")
        print(f"📊 总盈亏: ${report['total_profit']:+,.2f} ({report['total_profit_percent']:+.2f}%)")
        
        print(f"\n📊 交易统计:")
        print(f"   总交易次数: {report['total_trades']}")
        print(f"   盈利次数: {report['winning_trades']}")
        print(f"   亏损次数: {report['losing_trades']}")
        print(f"   胜率: {report['win_rate']:.2f}%")
        print(f"   最大回撤: {report['max_drawdown']:.2f}%")
        
        print(f"\n🔄 策略切换统计:")
        print(f"   总切换次数: {report['switches_count']}")
        for strategy, count in report['switches_by_strategy'].items():
            print(f"   → {strategy}: {count} 次")
        
        print(f"\n🎯 目标预测统计:")
        print(f"   总预测次数: {report['target_stats']['total']}")
        for direction, count in report['target_stats']['by_direction'].items():
            print(f"   → {direction}: {count} 次")
        print(f"   平均目标时间: {report['avg_target_time']:.1f} 根K线")
        print("="*70)


def run_ai_backtest(symbol: str, model_name: str, data_file: str, use_target: bool = True,
                    initial_capital: float = 10000.0, risk_percent: float = 1.0,
                    sl_atr: float = 2.0, tp_atr: float = 4.0):
    """运行 AI 回测的便捷函数"""
    import os
    from pathlib import Path
    
    # 查找模型文件
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ai_models')
    
    model_path = os.path.join(model_dir, model_name)
    base_name = model_name.replace('.pkl', '')
    scaler_path = os.path.join(model_dir, f"{base_name}_scaler.pkl")
    feature_path = os.path.join(model_dir, f"{base_name}_feature_cols.pkl")
    calibrator_path = os.path.join(model_dir, f"{base_name}_calibrators.pkl")
    price_target_path = os.path.join(model_dir, f"{base_name}_price_target.pkl")
    
    if not os.path.exists(scaler_path):
        parts = base_name.split('_')
        if len(parts) >= 2:
            simple_base = f"{parts[0]}_{parts[1]}"
            scaler_path = os.path.join(model_dir, f"{simple_base}_scaler.pkl")
            feature_path = os.path.join(model_dir, f"{simple_base}_feature_cols.pkl")
            calibrator_path = os.path.join(model_dir, f"{simple_base}_calibrators.pkl")
            price_target_path = os.path.join(model_dir, f"{simple_base}_price_target.pkl")
    
    df = pd.read_csv(data_file, parse_dates=['time'])
    
    print(f"[DEBUG run_ai_backtest] model_path: {model_path}, exists: {os.path.exists(model_path)}")
    print(f"[DEBUG run_ai_backtest] scaler_path: {scaler_path}, exists: {os.path.exists(scaler_path)}")
    print(f"[DEBUG run_ai_backtest] feature_path: {feature_path}, exists: {os.path.exists(feature_path)}")
    print(f"[DEBUG run_ai_backtest] calibrator_path: {calibrator_path}, exists: {os.path.exists(calibrator_path)}")
    print(f"[DEBUG run_ai_backtest] price_target_path: {price_target_path}, exists: {os.path.exists(price_target_path)}")
    
    backtester = AIBacktester(
        symbol=symbol,
        model_path=model_path,
        scaler_path=scaler_path,
        feature_cols_path=feature_path if os.path.exists(feature_path) else None,
        calibrator_path=calibrator_path if os.path.exists(calibrator_path) else None,
        price_target_model_path=price_target_path if os.path.exists(price_target_path) else None
    )
    
    backtester.initial_capital = initial_capital
    backtester.capital = initial_capital
    backtester.risk_percent = risk_percent
    backtester.sl_atr_multiplier = sl_atr
    backtester.tp_atr_multiplier = tp_atr
    backtester.use_target_prediction = use_target
    report = backtester.run(df)
    backtester.print_report(report)
    
    return report
