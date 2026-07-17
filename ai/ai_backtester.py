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
from core.ai.state_strategy_map import STATE_STRATEGY_MAP, select_strategy_by_target
from core.ai.dynamic_strategy_recommender import get_recommended_strategy
from core.ai.price_target_predictor import PriceTargetPredictor
from core.strategies.strategy_map import resolve_strategy_class


class AIBacktester:
    """AI 机器人回测器 - 含价格目标预测"""
    
    def __init__(self, symbol: str, model_path: str, scaler_path: str, 
                 feature_cols_path: str = None, calibrator_path: str = None,
                 price_target_model_path: str = None):
        self.symbol = symbol
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.calibrators = None
        self.price_predictor = None
        
        # 加载 AI 模型
        self._load_model(model_path, scaler_path, feature_cols_path, calibrator_path)
        
        # 加载价格目标模型
        if price_target_model_path and os.path.exists(price_target_model_path):
            self.price_predictor = PriceTargetPredictor()
            self.price_predictor.load(price_target_model_path)
            print("✅ 价格目标模型已加载")
        else:
            print("⚠️ 未找到价格目标模型，将使用简化版目标预测")
        
        # 回测结果
        self.results = None
        self.trades = []
        self.equity_curve = []
        self.strategy_switches = []
        self.target_predictions = []
        
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
        
        # AI 预测置信度门槛
        self.confidence_threshold = 0.50
        
        # 合约规格
        self.contract_size = 100  # XAUUSD 默认
        
        # 目标价预测开关
        self.use_target_prediction = True

        # 可配置预测间隔
        self.prediction_interval = 5
    
    def _load_model(self, model_path, scaler_path, feature_cols_path, calibrator_path):
        """加载 AI 模型（使用统一 safe_load_model，多层回退策略）"""
        print(f"\n[DEBUG _load_model] 开始加载模型")
        print(f"[DEBUG _load_model] model_path: {model_path}")
        print(f"[DEBUG _load_model] scaler_path: {scaler_path}")
        print(f"[DEBUG _load_model] feature_cols_path: {feature_cols_path}")
        print(f"[DEBUG _load_model] calibrator_path: {calibrator_path}")
        
        # 检查文件是否存在
        print(f"[DEBUG _load_model] 检查文件存在性:")
        print(f"[DEBUG _load_model]   model exists: {os.path.exists(model_path)}")
        print(f"[DEBUG _load_model]   scaler exists: {os.path.exists(scaler_path)}")
        if feature_cols_path:
            print(f"[DEBUG _load_model]   feature_cols exists: {os.path.exists(feature_cols_path)}")
        if calibrator_path:
            print(f"[DEBUG _load_model]   calibrators exists: {os.path.exists(calibrator_path)}")
        
        try:
            from core.ai.train_utils import safe_load_model
            print(f"[DEBUG _load_model] 调用 safe_load_model...")
            self.model = safe_load_model(model_path)
            
            print(f"[DEBUG _load_model] safe_load_model 返回类型: {type(self.model)}")
            print(f"[DEBUG _load_model] self.model is None: {self.model is None}")
            
            if self.model is None:
                print(f"[DEBUG _load_model] ❌ 严重错误: safe_load_model 返回 None!")
                print(f"[DEBUG _load_model]    可能原因: 文件损坏、格式不兼容、或加载失败")
                return False

            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            if feature_cols_path and os.path.exists(feature_cols_path):
                with open(feature_cols_path, 'rb') as f:
                    self.feature_cols = pickle.load(f)
            if calibrator_path and os.path.exists(calibrator_path):
                with open(calibrator_path, 'rb') as f:
                    self.calibrators = pickle.load(f)
            print(f"✅ AI 模型加载成功: {model_path}")
            print(f"[DEBUG _load_model] 模型类型: {type(self.model).__name__}")
            print(f"[DEBUG _load_model] 模型方法: predict={hasattr(self.model, 'predict')}, predict_proba={hasattr(self.model, 'predict_proba')}")
            return True
        except Exception as e:
            print(f"❌ AI 模型加载失败: {e}")
            import traceback
            traceback.print_exc()
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
        """预测单根 K 线的市场状态"""
        print(f"[DEBUG _predict_state] 被调用")
        
        if self.model is None:
            print(f"[DEBUG _predict_state] ❌ 严重错误: Model is None - returning confidence 0.0")
            print(f"[DEBUG _predict_state]    模型未正确加载，请检查 _load_model 的输出")
            return {'state': 0, 'confidence': 0.0}
        
        try:
            df_feat = FeatureFactory.compute_features(df_slice)
            if len(df_feat) == 0:
                print(f"[DEBUG _predict_state] ⚠️ 特征计算返回空数据")
                return {'state': 0, 'confidence': 0.0}
            
            latest = df_feat.iloc[-1:].copy()
            feature_cols = self._get_feature_columns(latest)
            X = latest.reindex(columns=feature_cols, fill_value=0)
            X_scaled = self.scaler.transform(X) if self.scaler else X.values
            
            print(f"[DEBUG _predict_state] 执行预测...")
            raw_proba = self.model.predict_proba(X_scaled)[0]
            pred = int(self.model.predict(X_scaled)[0])
            
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
            
            confidence = float(max(proba))
            
            print(f"[DEBUG _predict_state] ✅ 预测完成: state={pred}, confidence={confidence:.4f}")
            
            return {
                'state': pred,
                'confidence': confidence,
                'probabilities': proba.tolist()
            }
        except Exception as e:
            print(f"[DEBUG _predict_state] ❌ 状态预测失败: {e}")
            import traceback
            traceback.print_exc()
            return {'state': 0, 'confidence': 0.0}
    
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
        """根据状态和目标价切换策略"""
        print(f"[DEBUG _switch_strategy] called: state={state} confidence={confidence:.4f} threshold={self.confidence_threshold} current_strategy={self.current_strategy}")
        
        if confidence < self.confidence_threshold:
            print(f"[DEBUG _switch_strategy] SKIPPED: confidence {confidence:.4f} < threshold {self.confidence_threshold}")
            return
        
        # 如果有目标价信息，使用目标价匹配策略
        if target_info and target_info.get('direction') != 'UNKNOWN':
            selection = select_strategy_by_target(
                target_info['target_price'],
                target_info['current_price'],
                target_info['target_time'],
                timeframe_minutes=5  # M5
            )
            new_strategy = selection['strategy']
            new_params = selection['params']
            reason = selection['reason']
            source = 'target_based'
        else:
            # 否则使用状态映射
            recommendation = get_recommended_strategy(self.symbol, state, "M5")
            new_strategy = recommendation.get('strategy', 'BOLLINGER_REVERSION')
            new_params = recommendation.get('params', {})
            reason = f"状态 {state}"
            source = recommendation.get('source', 'default_mapping')
        
        # 如果策略变化，记录切换
        if new_strategy != self.current_strategy:
            print(f"[DEBUG _switch_strategy] ✅ 策略切换: {self.current_strategy} -> {new_strategy} (原因: {reason})")
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
            return True
        else:
            print(f"[DEBUG _switch_strategy] 策略未变化: {new_strategy}")
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
        
        # 如果有持仓且信号反转，平仓
        if self.position == 'long' and signal == 'SELL':
            self._close_position(price, timestamp, '信号转空')
            return
        elif self.position == 'short' and signal == 'BUY':
            self._close_position(price, timestamp, '信号转多')
            return
        
        # 如果没有持仓，开仓
        if not self.position and signal in ['BUY', 'SELL']:
            self._open_position(signal, price, atr, timestamp, target_info)
    
    def _open_position(self, signal: str, price: float, atr: float, timestamp, target_info: dict = None):
        """开仓"""
        if atr <= 0:
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
        
        if signal == 'BUY':
            entry_price = price
            sl_price = entry_price - sl_distance
            tp_price = entry_price + tp_distance
        else:
            entry_price = price
            sl_price = entry_price + sl_distance
            tp_price = entry_price - tp_distance
        
        self.position = 'long' if signal == 'BUY' else 'short'
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.lot_size = lot_size
        self.current_target = target_info
        
        self.trades.append({
            'time': timestamp,
            'action': 'OPEN',
            'signal': signal,
            'strategy': self.current_strategy,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'lot_size': lot_size,
            'atr': atr,
            'target_info': target_info
        })
    
    def _close_position(self, exit_price: float, timestamp, reason: str):
        """平仓"""
        if not self.position:
            return
        
        if self.position == 'long':
            profit = (exit_price - self.entry_price) * self.lot_size * self.contract_size
        else:
            profit = (self.entry_price - exit_price) * self.lot_size * self.contract_size
        
        self.capital += profit
        
        self.trades.append({
            'time': timestamp,
            'action': 'CLOSE',
            'reason': reason,
            'exit_price': exit_price,
            'profit': profit,
            'capital_after': self.capital
        })
        
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
                self._close_position(self.sl_price, timestamp, '止损')
                return True
            elif high >= self.tp_price:
                self._close_position(self.tp_price, timestamp, '止盈')
                return True
        else:
            if high >= self.sl_price:
                self._close_position(self.sl_price, timestamp, '止损')
                return True
            elif low <= self.tp_price:
                self._close_position(self.tp_price, timestamp, '止盈')
                return True
        
        return False
    
    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """运行回测"""
        print("\n" + "="*70)
        print("🚀 AI 机器人回测启动")
        print("="*70)
        print(f"📊 数据量: {len(df)} 根 K 线")
        print(f"📅 时间范围: {df['time'].iloc[0]} 到 {df['time'].iloc[-1]}")
        print(f"💰 初始资金: ${self.initial_capital:,.2f}")
        print(f"🎯 目标预测: {'启用' if self.use_target_prediction else '禁用'}")
        print("="*70)
        
        self.capital = self.initial_capital
        self.trades = []
        self.equity_curve = [{'time': df['time'].iloc[0], 'capital': self.capital}]
        self.strategy_switches = []
        self.target_predictions = []
        self.position = None
        
        # 初始化策略
        self.current_strategy = 'BOLLINGER_REVERSION'
        self.current_params = {'bb_length': 20, 'bb_std': 2.0, 'trend_filter_period': 50}
        
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
        
        print(f"[DEBUG run] 开始回测循环: {min_bars} 到 {total_bars} (共 {total_bars - min_bars} 根K线)")
        print(f"[DEBUG run] 初始策略: {self.current_strategy}")
        print(f"[DEBUG run] 模型状态: {'已加载' if self.model is not None else '❌ 未加载'}")
        print(f"[DEBUG run] scaler 状态: {'已加载' if self.scaler is not None else '❌ 未加载'}")
        print(f"[DEBUG run] feature_cols: {self.feature_cols}")
        
        for i in range(min_bars, total_bars):
            current_bar = df.iloc[i]
            current_time = current_bar['time']
            
            # 获取历史窗口
            window = df.iloc[:i+1].copy()
            
            # 1. AI 状态预测
            if i - last_prediction_idx >= self.prediction_interval:
                print(f"[DEBUG run] K线 {i}: 执行预测...")
                prediction = self._predict_state(window)
                state = prediction['state']
                confidence = prediction['confidence']
                last_prediction_idx = i
                
                print(f"[DEBUG run] K线 {i}: 预测结果 state={state}, confidence={confidence:.4f}")
                
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
                switched = self._switch_strategy(state, confidence, target_info)
                if switched:
                    print(f"[DEBUG run] K线 {i}: 策略已切换!")
            
            # 4. 策略信号分析
            signal = self._analyze_strategy(window)
            
            # 5. 检查止损止盈
            if self.position:
                if self._check_stop_loss_take_profit(current_bar, current_time):
                    continue
            
            # 6. 执行交易
            self._execute_trade(signal, current_bar['close'], current_bar['atr'], current_time, self.current_target)
            
            # 记录权益
            if not self.position:
                self.equity_curve.append({
                    'time': current_time,
                    'capital': self.capital
                })
            else:
                if self.position == 'long':
                    unrealized = (current_bar['close'] - self.entry_price) * self.lot_size * self.contract_size
                else:
                    unrealized = (self.entry_price - current_bar['close']) * self.lot_size * self.contract_size
                current_equity = self.capital + unrealized
                self.equity_curve.append({
                    'time': current_time,
                    'capital': current_equity
                })
        
        # 如果最后还有持仓，按最后价格平仓
        if self.position:
            last_bar = df.iloc[-1]
            self._close_position(last_bar['close'], last_bar['time'], '回测结束平仓')
        
        print(f"\n[DEBUG run] 回测循环结束")
        print(f"[DEBUG run] 总交易数: {len(self.trades)}")
        print(f"[DEBUG run] 策略切换次数: {len(self.strategy_switches)}")
        print(f"[DEBUG run] 权益曲线点数: {len(self.equity_curve)}")
        
        # 生成报告
        return self._generate_report()
    
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
        peak = self.initial_capital
        for eq in self.equity_curve:
            if eq['capital'] > peak:
                peak = eq['capital']
            drawdown = (peak - eq['capital']) / peak * 100 if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 策略切换统计
        switches_by_strategy = {}
        for s in self.strategy_switches:
            to_strategy = s['to_strategy']
            switches_by_strategy[to_strategy] = switches_by_strategy.get(to_strategy, 0) + 1
        
        print(f"[DEBUG _generate_report] switches_count: {len(self.strategy_switches)}")
        print(f"[DEBUG _generate_report] switches_by_strategy: {switches_by_strategy}")
        
        # 目标预测统计
        target_stats = {
            'total': len(self.target_predictions),
            'by_direction': {}
        }
        for tp in self.target_predictions:
            direction = tp['target_info'].get('direction', 'UNKNOWN')
            target_stats['by_direction'][direction] = target_stats['by_direction'].get(direction, 0) + 1
        
        # 平均目标时间
        avg_target_time = 0
        if self.target_predictions:
            avg_target_time = sum([tp['target_info'].get('target_time', 0) for tp in self.target_predictions]) / len(self.target_predictions)
        
        print(f"[DEBUG _generate_report] 报告生成完成")
        print(f"[DEBUG _generate_report] trade_log count: {len(self.trades)}")
        print(f"[DEBUG _generate_report] equity_curve count: {len(self.equity_curve)}")
        
        return {
            'symbol': self.symbol,
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_profit': total_profit,
            'total_profit_percent': (total_profit / self.initial_capital) * 100 if self.initial_capital > 0 else 0,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'strategy_switches': self.strategy_switches,
            'switches_count': len(self.strategy_switches),
            'switches_by_strategy': switches_by_strategy,
            'target_predictions': self.target_predictions,
            'target_stats': target_stats,
            'avg_target_time': avg_target_time,
            'trade_log': self.trades,
            'trades': close_trades,
            'equity_curve': self.equity_curve,
            'use_target_prediction': self.use_target_prediction
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


    def run_ai_backtest(symbol: str, model_name: str, data_file: str, use_target: bool = True):
        """运行 AI 回测的便捷函数"""
        import os
        from pathlib import Path
        
        print(f"\n{'='*70}")
        print(f"🚀 AI 回测启动")
        print(f"{'='*70}")
        print(f"📊 品种: {symbol}")
        print(f"📁 模型: {model_name}")
        print(f"📈 数据: {data_file}")
        print(f"🎯 目标预测: {'启用' if use_target else '禁用'}")
        print(f"{'='*70}\n")
        
        # 查找模型文件
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ai_models')
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        print(f"[DEBUG run_ai_backtest] model_dir: {model_dir}")
        print(f"[DEBUG run_ai_backtest] model_dir exists: {os.path.exists(model_dir)}")
        
        # 使用增強的模型發現函數
        try:
            from ai_backtester_fix_v2 import find_model_files
            model_path, scaler_path, feature_path, calibrator_path = find_model_files(
                symbol, "M5", model_dir, project_root
            )
        except ImportError:
            print(f"[DEBUG run_ai_backtest] 無法導入 find_model_files，使用預設邏輯")
            model_path = os.path.join(model_dir, model_name)
            base_name = model_name.replace('.pkl', '')
            scaler_path = os.path.join(model_dir, f"{base_name}_scaler.pkl")
            feature_path = os.path.join(model_dir, f"{base_name}_feature_cols.pkl")
            calibrator_path = os.path.join(model_dir, f"{base_name}_calibrators.pkl")
        
        price_target_path = os.path.join(model_dir, f"{base_name}_price_target.pkl") if 'base_name' in locals() else None
        
        # 如果找不到，嘗試簡化名稱
        if not os.path.exists(scaler_path):
            parts = base_name.split('_')
            if len(parts) >= 2:
                simple_base = f"{parts[0]}_{parts[1]}"
                scaler_path = os.path.join(model_dir, f"{simple_base}_scaler.pkl")
                feature_path = os.path.join(model_dir, f"{simple_base}_feature_cols.pkl")
                calibrator_path = os.path.join(model_dir, f"{simple_base}_calibrators.pkl")
                price_target_path = os.path.join(model_dir, f"{simple_base}_price_target.pkl")
        
        print(f"\n[DEBUG run_ai_backtest] 最終文件路徑:")
        print(f"[DEBUG run_ai_backtest]   model: {model_path}")
        print(f"[DEBUG run_ai_backtest]   scaler: {scaler_path}")
        print(f"[DEBUG run_ai_backtest]   feature: {feature_path}")
        print(f"[DEBUG run_ai_backtest]   calibrator: {calibrator_path}")
        print(f"[DEBUG run_ai_backtest]   price_target: {price_target_path}")
        
        # 加載數據
        print(f"\n[DEBUG run_ai_backtest] 加載數據...")
        df = pd.read_csv(data_file, parse_dates=['time'])
        print(f"[DEBUG run_ai_backtest] 數據加載完成: {len(df)} 根K線")
        
        # 創建回測器
        print(f"\n[DEBUG run_ai_backtest] 創建 AIBacktester...")
        backtester = AIBacktester(
            symbol=symbol,
            model_path=model_path,
            scaler_path=scaler_path,
            feature_cols_path=feature_path if feature_path and os.path.exists(feature_path) else None,
            calibrator_path=calibrator_path if calibrator_path and os.path.exists(calibrator_path) else None,
            price_target_model_path=price_target_path if price_target_path and os.path.exists(price_target_path) else None
        )
        
        backtester.use_target_prediction = use_target
        
        print(f"\n[DEBUG run_ai_backtest] 開始回測...")
        report = backtester.run(df)
        backtester.print_report(report)
        
        print(f"\n{'='*70}")
        print(f"✅ 回測完成")
        print(f"{'='*70}")
        
        return report
