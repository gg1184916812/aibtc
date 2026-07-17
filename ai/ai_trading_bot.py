# core/ai/ai_trading_bot.py
"""
AI 交易机器人 - 独立运行
自动根据 AI 预测结果执行交易
"""

import threading
import time
import logging
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import pickle
import os

from core.utils.mt5 import TIMEFRAME_MAP, get_rates_mt5, find_mt5_symbol
from core.mt5.trade import place_trade, close_trade
from core.strategies.strategy_map import resolve_strategy_class
from core.ai.feature_factory import FeatureFactory
from core.ai.state_strategy_map import STATE_STRATEGY_MAP
from core.ai.dynamic_strategy_recommender import get_recommended_strategy

logger = logging.getLogger(__name__)

class AITradingBot:
    """AI 交易机器人 - 独立运行，不依赖普通 TradingBot"""
    
    def __init__(self, symbol: str, model_path: str, scaler_path: str, feature_cols_path: str = None, calibrator_path: str = None):
        self.symbol = symbol
        self.market_for_mt5 = None
        self.timeframe = "H1"
        self.tf_const = TIMEFRAME_MAP.get("H1", mt5.TIMEFRAME_H1)
        
        # 加载 AI 模型
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.calibrators = None
        self._load_model(model_path, scaler_path, feature_cols_path, calibrator_path)
        
        # 状态
        self.is_running = False
        self.thread = None
        self._stop_event = threading.Event()
        
        # 当前状态
        self.current_state = -1
        self.current_confidence = 0.0
        self.current_strategy = None
        self.current_params = None
        self.current_signal = "HOLD"
        self.last_prediction_time = None
        self.last_trade_time = None
        self.trade_history = []
        
        # 策略实例
        self.strategy_instance = None
        self.last_analysis = {}
        
        # 输出日志
        self.logs = []
        
        # 风险参数
        self.risk_percent = 1.0
        self.sl_atr_multiplier = 2.0
        self.tp_atr_multiplier = 4.0
        
        # 交易间隔
        self.prediction_interval = 30  # 5分钟预测一次
        self.trade_interval = 10  # 1分钟检查一次
        self.magic_number = 99999  # AI Bot 专用 Magic Number
        
        # 初始化符号
        self._init_symbol()
        
    def _load_model(self, model_path, scaler_path, feature_cols_path, calibrator_path):
        """加载 AI 模型"""
        try:
            from core.ai.train_utils import safe_load_model
            self.model = safe_load_model(model_path)

            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            if feature_cols_path and os.path.exists(feature_cols_path):
                with open(feature_cols_path, 'rb') as f:
                    self.feature_cols = pickle.load(f)
            if calibrator_path and os.path.exists(calibrator_path):
                with open(calibrator_path, 'rb') as f:
                    self.calibrators = pickle.load(f)
            logger.info(f"AI 模型加载成功: {model_path}")
            return True
        except Exception as e:
            logger.error(f"加载 AI 模型失败: {e}")
            return False
    
    def _init_symbol(self):
        """初始化 MT5 符号"""
        self.market_for_mt5 = find_mt5_symbol(self.symbol)
        if not self.market_for_mt5:
            logger.error(f"符号 {self.symbol} 未找到")
            return False
        return True
    
    def start(self):
        """启动 AI 机器人"""
        if self.is_running:
            return False, "机器人已在运行中"
        
        if not self.market_for_mt5:
            if not self._init_symbol():
                return False, "无法初始化交易符号"
        
        self._stop_event.clear()
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        self._add_log("🚀 AI 机器人已启动", "info")
        self._add_log(f"📊 交易品种: {self.market_for_mt5}", "info")
        return True, "AI 机器人已启动"
    
    def stop(self):
        """停止 AI 机器人"""
        if not self.is_running:
            return False, "机器人未在运行"
        
        self._stop_event.set()
        self.is_running = False
        
        # 如果有持仓，平仓
        position = self._get_open_position()
        if position:
            close_trade(position)
            self._add_log(f"🔒 已平仓所有持仓", "warning")
        
        self._add_log("🛑 AI 机器人已停止", "warning")
        return True, "AI 机器人已停止"
    
    def get_status(self):
        """获取当前状态"""
        return {
            'is_running': self.is_running,
            'symbol': self.market_for_mt5,
            'current_state': self.current_state,
            'current_confidence': self.current_confidence,
            'current_strategy': self.current_strategy,
            'current_params': self.current_params,
            'current_signal': self.current_signal,
            'last_prediction': self.last_prediction_time.isoformat() if self.last_prediction_time else None,
            'last_trade': self.last_trade_time.isoformat() if self.last_trade_time else None,
            'trade_count': len(self.trade_history),
            'logs': self.logs[-50:],
        }
    
    def _add_log(self, message, level="info"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append({
            'timestamp': timestamp,
            'message': message,
            'level': level
        })
        if len(self.logs) > 1000:
            self.logs = self.logs[-500:]
    
    def _run_loop(self):
        """主循环"""
        self._add_log("⏳ AI 机器人初始化中...", "info")
        
        # 获取策略实例（使用初始策略）
        if not self._init_strategy():
            self._add_log("❌ 策略初始化失败", "error")
            self.is_running = False
            return
        
        last_prediction_time = datetime.now() - timedelta(minutes=10)
        
        while not self._stop_event.is_set():
            try:
                now = datetime.now()
                
                # 1. 获取最新数据
                df = self._get_market_data()
                if df is None or df.empty:
                    time.sleep(5)
                    continue
                
                # 2. AI 预测（每5分钟）
                if (now - last_prediction_time).seconds >= self.prediction_interval:
                    self._do_prediction(df)
                    last_prediction_time = now
                
                # 3. 执行策略分析
                self._analyze_strategy(df)
                
                # 4. 执行交易信号
                self._execute_trade()
                
                time.sleep(self.trade_interval)
                
            except Exception as e:
                logger.error(f"AI 机器人循环错误: {e}")
                self._add_log(f"❌ 错误: {e}", "error")
                time.sleep(5)
        
        self.is_running = False
    
    def _init_strategy(self):
        """初始化策略实例"""
        try:
            strategy_name = "BOLLINGER_REVERSION"
            params = {'bb_length': 20, 'bb_std': 2.0, 'trend_filter_period': 50}
            strategy_class = resolve_strategy_class(strategy_name)
            if strategy_class:
                class MockBot:
                    pass
                mock_bot = MockBot()
                mock_bot.market_for_mt5 = self.market_for_mt5
                self.strategy_instance = strategy_class(bot_instance=mock_bot, params=params)
                self.current_strategy = strategy_name
                self.current_params = params
                self._add_log(f"📈 初始策略: {strategy_name}", "info")
                return True
            else:
                self._add_log(f"❌ 策略 {strategy_name} 未找到", "error")
                return False
        except Exception as e:
            self._add_log(f"❌ 策略初始化失败: {e}", "error")
            return False
    
    def _get_market_data(self):
        """获取市场数据"""
        try:
            df = get_rates_mt5(self.market_for_mt5, self.tf_const, 250)
            return df
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return None
    
    def _do_prediction(self, df):
        """执行 AI 预测"""
        try:
            df_feat = FeatureFactory.compute_features(df.tail(100))
            if len(df_feat) == 0:
                self._add_log("⚠️ 特征计算失败", "warning")
                return
            
            latest = df_feat.iloc[-1:].copy()
            
            # 确定特征列
            if hasattr(self.model, 'feature_names_in_'):
                feature_cols = list(self.model.feature_names_in_)
            elif self.feature_cols is not None:
                feature_cols = self.feature_cols
            else:
                exclude = ['time', 'open', 'high', 'low', 'close', 'volume', 'tick_volume']
                feature_cols = [c for c in latest.columns if c not in exclude and np.issubdtype(latest[c].dtype, np.number)]
            
            X = latest.reindex(columns=feature_cols, fill_value=0)
            X_scaled = self.scaler.transform(X) if self.scaler else X.values
            
            # 原始预测
            raw_proba = self.model.predict_proba(X_scaled)[0]
            pred = int(self.model.predict(X_scaled)[0])
            
            # 概率校准
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
            
            self.current_state = pred
            self.current_confidence = float(max(proba))
            self.last_prediction_time = datetime.now()
            
            state_names = {0: '震荡', 1: '多头趋势', 2: '空头趋势', 3: '高波动突破'}
            state_emoji = {0: '🔄', 1: '📈', 2: '📉', 3: '⚡'}
            
            self._add_log(
                f"🧠 AI 预测: {state_emoji.get(pred, '❓')} {state_names.get(pred, '未知')} "
                f"(置信度: {self.current_confidence*100:.1f}%)",
                "prediction"
            )
            
            # 根据预测状态切换策略（置信度 > 55% 才切换）
            if self.current_confidence > 0.55:
                self._switch_strategy(pred)
            
        except Exception as e:
            logger.error(f"AI 预测失败: {e}")
            self._add_log(f"❌ AI 预测失败: {e}", "error")
    
    def _switch_strategy(self, state):
        """根据 AI 预测切换策略（使用动态推荐）"""
        # 获取推荐策略
        recommendation = get_recommended_strategy(self.market_for_mt5, state, "H1")
        new_strategy = recommendation.get('strategy', 'BOLLINGER_REVERSION')
        new_params = recommendation.get('params', {})
        
        # 如果策略变化，重新初始化
        if new_strategy != self.current_strategy:
            strategy_class = resolve_strategy_class(new_strategy)
            if strategy_class:
                class MockBot:
                    pass
                mock_bot = MockBot()
                mock_bot.market_for_mt5 = self.market_for_mt5
                self.strategy_instance = strategy_class(bot_instance=mock_bot, params=new_params)
                self.current_strategy = new_strategy
                self.current_params = new_params
                
                source = recommendation.get('source', 'unknown')
                win_rate = recommendation.get('win_rate')
                source_text = "📊 历史回测" if source == 'backtest_history' else "📋 默认映射"
                win_text = f" (胜率: {win_rate:.1f}%)" if win_rate else ""
                
                state_names = {0: '震荡', 1: '多头趋势', 2: '空头趋势', 3: '高波动突破'}
                self._add_log(
                    f"🔄 策略切换: {state_names.get(state, '未知')} → {new_strategy} "
                    f"{source_text}{win_text}",
                    "strategy"
                )
    
    def _analyze_strategy(self, df):
        """执行策略分析"""
        try:
            if self.strategy_instance is None:
                return
            
            self.last_analysis = self.strategy_instance.analyze(df.tail(50))
            self.current_signal = self.last_analysis.get("signal", "HOLD")
            
            if self.current_signal != "HOLD":
                self._add_log(
                    f"📊 策略信号: {self.current_signal} ({self.current_strategy})",
                    "signal"
                )
        except Exception as e:
            logger.error(f"策略分析失败: {e}")
    
    def _execute_trade(self):
        """执行交易"""
        if self.current_signal == "HOLD":
            return
        
        position = self._get_open_position()
        
        # 反转信号：如果有持仓且信号相反，先平仓
        if position:
            if position.type == mt5.ORDER_TYPE_BUY and self.current_signal == "SELL":
                self._add_log("🔒 平仓 BUY 持仓 (信号转空)", "trade")
                close_trade(position)
                position = None
            elif position.type == mt5.ORDER_TYPE_SELL and self.current_signal == "BUY":
                self._add_log("🔒 平仓 SELL 持仓 (信号转多)", "trade")
                close_trade(position)
                position = None
        
        # 如果没有持仓，开仓
        if not position and self.current_signal in ["BUY", "SELL"]:
            order_type = mt5.ORDER_TYPE_BUY if self.current_signal == "BUY" else mt5.ORDER_TYPE_SELL
            self._add_log(
                f"🚀 开仓 {self.current_signal} "
                f"(策略: {self.current_strategy}, 风险: {self.risk_percent}%)",
                "trade"
            )
            
            result, msg = place_trade(
                self.market_for_mt5,
                order_type,
                self.risk_percent,
                self.sl_atr_multiplier,
                self.tp_atr_multiplier,
                self.magic_number,
                "H1"
            )
            
            if result:
                self.last_trade_time = datetime.now()
                self.trade_history.append({
                    'time': self.last_trade_time,
                    'signal': self.current_signal,
                    'strategy': self.current_strategy,
                    'result': 'success'
                })
                self._add_log(f"✅ 开仓成功: {self.current_signal}", "trade")
            else:
                self._add_log(f"❌ 开仓失败: {msg}", "error")
    
    def _get_open_position(self):
        """获取当前持仓"""
        try:
            positions = mt5.positions_get(symbol=self.market_for_mt5)
            if positions:
                for pos in positions:
                    if pos.magic == self.magic_number:
                        return pos
            return None
        except Exception:
            return None