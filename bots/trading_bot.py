# core/bots/trading_bot.py - FINAL VERSION WITH AI PREDICTOR FIX

import threading
import time
import logging
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from core.strategies.strategy_map import resolve_strategy_class
from core.mt5.trade import place_trade, close_trade
from core.utils.mt5 import TIMEFRAME_MAP
from core.db.models import log_trade_for_ai_analysis
from core.seasonal.holiday_manager import holiday_manager
from core.strategies.index_optimizations import get_trading_hours, is_index_symbol

# AI imports
from core.ai.llm_analyst import LLMAnalyst
from core.ai.decision_fusion import fuse_decisions
import os
import pickle
import json

logger = logging.getLogger(__name__)

def _to_log_friendly(value):
    if isinstance(value, dict):
        return {k: _to_log_friendly(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_log_friendly(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_to_log_friendly(v) for v in value)
    if hasattr(value, "item") and value.__class__.__module__.startswith("numpy"):
        try:
            return value.item()
        except Exception:
            return value
    return value


class TradingBot(threading.Thread):
    def __init__(self, id, name, market, risk_percent, sl_pips, tp_pips, timeframe, check_interval, strategy, strategy_params={}, status='Dijeda', enable_strategy_switching=False):
        super().__init__()
        self.id = id
        self.name = name
        self.market = market
        self.risk_percent = risk_percent
        self.sl_pips = sl_pips
        self.tp_pips = tp_pips
        self.timeframe = timeframe
        self.check_interval = check_interval
        self.strategy_name = strategy
        self.strategy_params = strategy_params
        self.enable_strategy_switching = enable_strategy_switching
        self.market_for_mt5 = None
        self.status = status

        self.last_analysis = {"signal": "MEMUAT", "explanation": "Bot sedang memulai..."}
        self._stop_event = threading.Event()
        self.strategy_instance = None
        self.tf_map = TIMEFRAME_MAP

        # AI attributes
        self.ai_enabled = True
        self.ai_predictor = None
        self.ai_scaler = None
        self.feature_cols = None
        self.llm_analyst = None
        self.last_ai_decision_time = datetime.now() - timedelta(hours=1)
        self.last_llm_time = datetime.now() - timedelta(hours=4)
        self.ai_decision_interval = 1800   # 30 minutes
        self.llm_interval = 14400          # 4 hours
        self.cached_llm_result = {"bias": "neutral", "risk_adjustment": 1.0, "preferred_strategy": None}
        self.current_ai_state = 0
        self.last_ml_result = {'state': 0, 'confidence': 0.0}
        self._load_ai_models()

    def _load_ai_models(self):
        """加载AI模型、Scaler和特征列"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            model_path = os.path.join(project_root, 'market_predictor.pkl')
            scaler_path = os.path.join(project_root, 'scaler.pkl')
            feature_cols_path = os.path.join(project_root, 'feature_cols.pkl')

            if os.path.exists(model_path) and os.path.exists(scaler_path):
                from core.ai.train_utils import safe_load_model
                self.ai_predictor = safe_load_model(model_path)

                with open(scaler_path, 'rb') as f:
                    self.ai_scaler = pickle.load(f)

                if os.path.exists(feature_cols_path):
                    with open(feature_cols_path, 'rb') as f:
                        self.feature_cols = pickle.load(f)
                    logger.info(f"Loaded feature columns for bot {self.id}, count: {len(self.feature_cols)}")
                else:
                    logger.warning(f"feature_cols.pkl not found for bot {self.id}")

                if hasattr(self.ai_predictor, 'feature_names_in_'):
                    logger.info(f"AI Predictor loaded for bot {self.id}, features: {len(self.ai_predictor.feature_names_in_)}")
                else:
                    logger.warning(f"AI Predictor loaded but no feature_names_in_ for bot {self.id}.")
            else:
                logger.warning(f"AI model files not found for bot {self.id}, AI disabled")
                self.ai_enabled = False
        except Exception as e:
            logger.error(f"Failed to load AI models for bot {self.id}: {e}")
            self.ai_enabled = False

        try:
            self.llm_analyst = LLMAnalyst()
            logger.info(f"LLM Analyst initialized for bot {self.id}")
        except Exception as e:
            logger.warning(f"LLM Analyst init failed for bot {self.id}: {e}")
            self.llm_analyst = None

    def run(self):
        self.status = 'Aktif'
        self.log_activity('START', f"Bot '{self.name}' dimulai.", is_notification=True)

        from core.utils.mt5 import find_mt5_symbol
        self.market_for_mt5 = find_mt5_symbol(self.market)
        if not self.market_for_mt5:
            msg = f"Simbol '{self.market}' tidak ditemukan di MT5."
            self.log_activity('ERROR', msg, is_notification=True)
            self.status = 'Error'
            self.last_analysis = {"signal": "ERROR", "explanation": msg}
            return

        try:
            strategy_class = resolve_strategy_class(self.strategy_name)
            if not strategy_class:
                raise ValueError(f"Strategi '{self.strategy_name}' tidak ditemukan.")
            self.strategy_instance = strategy_class(bot_instance=self, params=self.strategy_params)
        except Exception as e:
            self.log_activity('ERROR', f"Inisialisasi Gagal: {e}", is_notification=True)
            self.status = 'Error'
            return

        while not self._stop_event.is_set():
            try:
                symbol_info = mt5.symbol_info(self.market_for_mt5)
                if not symbol_info:
                    self.log_activity('WARNING', f"Tidak dapat mengambil info untuk simbol {self.market_for_mt5}.")
                    time.sleep(self.check_interval)
                    continue

                from core.utils.mt5 import get_rates_mt5
                tf_const = self.tf_map.get(self.timeframe, mt5.TIMEFRAME_H1)
                df = get_rates_mt5(self.market_for_mt5, tf_const, 250)
                if df.empty:
                    self.log_activity('WARNING', f"Gagal mengambil data harga untuk {self.market_for_mt5}.")
                    time.sleep(self.check_interval)
                    continue

                # === AI Decision ===
                if self.ai_enabled and self.ai_predictor is not None:
                    self._run_ai_decision(df)

                # === Strategy Analysis ===
                self.last_analysis = self.strategy_instance.analyze(df)
                signal = self.last_analysis.get("signal", "HOLD")
                current_position = self._get_open_position()

                # Spread guard
                try:
                    symbol_info = mt5.symbol_info(self.market_for_mt5)
                    max_spread = 1500 if 'BTC' in self.market_for_mt5.upper() else 60
                    if symbol_info and symbol_info.spread > max_spread:
                        logger.info(f"Bot {self.id} - Spread {symbol_info.spread} terlalu lebar. Skip entry.")
                        if not current_position:
                            time.sleep(self.check_interval)
                            continue
                except Exception:
                    pass

                # Break-even logic
                if current_position:
                    try:
                        from core.utils.mt5 import get_rates_mt5
                        atr_df = get_rates_mt5(self.market_for_mt5, self.tf_map.get(self.timeframe, mt5.TIMEFRAME_H1), 20)
                        if atr_df is not None and len(atr_df) > 14:
                            import pandas_ta as ta
                            atr_val = ta.atr(atr_df['high'], atr_df['low'], atr_df['close'], length=14).iloc[-1]
                            if atr_val and atr_val > 0:
                                if current_position.type == mt5.ORDER_TYPE_BUY:
                                    tick = mt5.symbol_info_tick(self.market_for_mt5)
                                    if tick:
                                        profit = tick.bid - current_position.price_open
                                        if profit > atr_val and current_position.sl < current_position.price_open:
                                            req = {"action": mt5.TRADE_ACTION_SLTP, "position": current_position.ticket,
                                                   "symbol": self.market_for_mt5, "sl": current_position.price_open,
                                                   "tp": current_position.tp, "magic": self.id}
                                            mt5.order_send(req)
                                            logger.info(f"Bot {self.id} - Break-even BUY")
                                elif current_position.type == mt5.ORDER_TYPE_SELL:
                                    tick = mt5.symbol_info_tick(self.market_for_mt5)
                                    if tick:
                                        profit = current_position.price_open - tick.ask
                                        if profit > atr_val and (current_position.sl == 0 or current_position.sl > current_position.price_open):
                                            req = {"action": mt5.TRADE_ACTION_SLTP, "position": current_position.ticket,
                                                   "symbol": self.market_for_mt5, "sl": current_position.price_open,
                                                   "tp": current_position.tp, "magic": self.id}
                                            mt5.order_send(req)
                                            logger.info(f"Bot {self.id} - Break-even SELL")
                    except Exception as e:
                        logger.debug(f"Bot {self.id} - Break-even non-fatal: {e}")

                if self._is_market_open_for_symbol():
                    self._handle_trade_signal(signal, current_position)
                else:
                    logger.info(f"Bot {self.id} - Market closed for {self.market_for_mt5}. Skipping trade.")

                time.sleep(self.check_interval)

            except Exception as e:
                self.log_activity('ERROR', f"Error pada loop utama: {e}", exc_info=True, is_notification=True)
                time.sleep(self.check_interval * 2)

        self.status = 'Dijeda'
        self.log_activity('STOP', f"Bot '{self.name}' dihentikan.", is_notification=True)

    def _run_ai_decision(self, df):
        now = datetime.now()
        # ML prediction every 30 minutes
        if (now - self.last_ai_decision_time).seconds > self.ai_decision_interval:
            try:
                from core.ai.feature_factory import FeatureFactory
                df_feat = FeatureFactory.compute_features(df.tail(100))
                if len(df_feat) > 0:
                    latest = df_feat.iloc[-1:].copy()

                    # 确定特征列
                    if hasattr(self.ai_predictor, 'feature_names_in_'):
                        feature_cols = list(self.ai_predictor.feature_names_in_)
                    elif self.feature_cols is not None:
                        feature_cols = self.feature_cols
                    else:
                        # 降级：排除非特征列
                        exclude = ['time', 'open', 'high', 'low', 'close', 'volume', 'tick_volume', 'real_volume', 'spread']
                        feature_cols = [c for c in latest.columns if c not in exclude and np.issubdtype(latest[c].dtype, np.number)]

                    X = latest.reindex(columns=feature_cols, fill_value=0)

                    if self.ai_scaler is not None:
                        X_scaled = self.ai_scaler.transform(X)
                    else:
                        X_scaled = X.values

                    proba = self.ai_predictor.predict_proba(X_scaled)[0]
                    pred = int(self.ai_predictor.predict(X_scaled)[0])
                    confidence = float(max(proba))
                    self.last_ml_result = {'state': pred, 'confidence': confidence, 'probabilities': proba.tolist()}
                    logger.debug(f"Bot {self.id} AI ML: state={pred}, conf={confidence:.2f}")
                else:
                    self.last_ml_result = {'state': 0, 'confidence': 0.0}
            except Exception as e:
                logger.error(f"Bot {self.id} AI ML error: {e}")
                self.last_ml_result = {'state': 0, 'confidence': 0.0}
            self.last_ai_decision_time = now
        ml_result = self.last_ml_result

        # LLM every 4 hours (if available)
        if self.llm_analyst is not None and (now - self.last_llm_time).seconds > self.llm_interval:
            try:
                summary = self._get_market_summary(df.tail(200))
                llm_result = self.llm_analyst.analyze(summary)
                self.cached_llm_result = llm_result
                self.last_llm_time = now
                logger.info(f"Bot {self.id} LLM: {llm_result}")
            except Exception as e:
                logger.error(f"Bot {self.id} LLM error: {e}")
        llm_result = self.cached_llm_result

        # Fuse decisions
        decision = fuse_decisions(ml_result, llm_result, self.current_ai_state)
        new_state = decision['state']
        new_strategy = decision['strategy']
        new_params = decision['params']
        risk_adj = decision.get('risk_adj', 1.0)

        # Apply change if needed
        if new_state != self.current_ai_state or new_strategy != self.strategy_name:
            logger.info(f"Bot {self.id} AI change: state {self.current_ai_state}->{new_state}, strategy {self.strategy_name}->{new_strategy}")
            adjusted_risk = max(0.1, min(5.0, self.risk_percent * risk_adj))
            update_data = {
                'strategy': new_strategy,
                'params': new_params,
                'risk_percent': adjusted_risk,
            }
            try:
                from core.bots.controller import perbarui_bot
                success, msg = perbarui_bot(self.id, update_data)
                if success:
                    strategy_class = resolve_strategy_class(new_strategy)
                    if strategy_class:
                        self.strategy_instance = strategy_class(bot_instance=self, params=new_params)
                        self.strategy_name = new_strategy
                        self.strategy_params = new_params
                        self.current_ai_state = new_state
                        self.risk_percent = adjusted_risk
                        logger.info(f"Bot {self.id} AI updated to {new_strategy} (database updated)")
                    else:
                        logger.error(f"Bot {self.id} AI failed to resolve strategy {new_strategy}")
                else:
                    logger.error(f"Bot {self.id} AI update failed: {msg}")
            except Exception as e:
                logger.error(f"Bot {self.id} AI update exception: {e}")

    def _get_market_summary(self, df):
        if df.empty:
            return {}
        close = df['close']
        high = df['high']
        low = df['low']
        current_price = close.iloc[-1]
        atr_14 = (high - low).rolling(14).mean().iloc[-1]
        rsi_14 = 50
        try:
            import pandas_ta as ta
            rsi_14 = ta.rsi(close, length=14).iloc[-1]
        except:
            pass
        ma20 = close.rolling(20).mean().iloc[-1]
        trend = 'bullish' if current_price > ma20 else 'bearish' if current_price < ma20 else 'neutral'
        volatility = 'high' if atr_14 / current_price > 0.01 else 'normal'
        return {
            'symbol': self.market_for_mt5,
            'current_price': round(current_price, 4),
            'atr_14': round(atr_14, 4),
            'trend': trend,
            'volatility': volatility,
            'rsi': round(rsi_14, 1),
            'timeframe': self.timeframe,
        }

    def stop(self):
        self._stop_event.set()

    def is_stopped(self):
        return self._stop_event.is_set()

    def log_activity(self, action, details, exc_info=False, is_notification=False):
        try:
            from core.db.queries import add_history_log
            add_history_log(self.id, action, details, is_notification)
            log_message = f"Bot {self.id} [{action}]: {details}"
            if exc_info:
                logger.error(log_message, exc_info=True)
            else:
                logger.info(log_message)
        except Exception as e:
            logger.error(f"Gagal mencatat riwayat untuk bot {self.id}: {e}")

    def _get_open_position(self):
        try:
            positions = mt5.positions_get(symbol=self.market_for_mt5)
            if positions:
                for pos in positions:
                    if pos.magic == self.id:
                        return pos
            return None
        except Exception as e:
            self.log_activity('ERROR', f"Gagal mendapatkan posisi terbuka: {e}", exc_info=True)
            return None

    def _is_market_open_for_symbol(self):
        try:
            if holiday_manager.is_trading_paused():
                return False
            current_time = datetime.now()
            is_weekend = current_time.weekday() >= 5
            if "BTC" in self.market_for_mt5 or "ETH" in self.market_for_mt5:
                return True
            if is_index_symbol(self.market_for_mt5):
                if is_weekend:
                    return False
                trading_hours = get_trading_hours(self.market_for_mt5)
                if trading_hours:
                    market_open = trading_hours.get('market_open', '14:30')
                    market_close = trading_hours.get('market_close', '21:00')
                    utc_hour = current_time.hour
                    utc_minute = current_time.minute
                    open_hour, open_minute = map(int, market_open.split(':'))
                    close_hour, close_minute = map(int, market_close.split(':'))
                    current_minutes = utc_hour * 60 + utc_minute
                    open_minutes = open_hour * 60 + open_minute
                    close_minutes = close_hour * 60 + close_minute
                    if open_minutes <= close_minutes:
                        return open_minutes <= current_minutes <= close_minutes
                    else:
                        return current_minutes >= open_minutes or current_minutes <= close_minutes
            if any(pair in self.market_for_mt5 for pair in ['EUR', 'GBP', 'USD', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']):
                return not is_weekend
            return True
        except Exception as e:
            logger.error(f"Error checking market hours for {self.market_for_mt5}: {e}")
            return True

    def _handle_trade_signal(self, signal, position):
        if signal == 'BUY':
            if position and position.type == mt5.ORDER_TYPE_SELL:
                self.log_activity('CLOSE SELL', "Menutup posisi JUAL untuk membuka posisi BELI.", is_notification=True)
                profit_loss = position.profit if hasattr(position, 'profit') else 0
                self._log_trade_for_ai_mentor(position, profit_loss, 'CLOSE_SELL')
                close_trade(position)
                position = None
            if not position:
                self.log_activity('OPEN BUY', "Membuka posisi BELI berdasarkan sinyal.", is_notification=True)
                place_trade(self.market_for_mt5, mt5.ORDER_TYPE_BUY, self.risk_percent, self.sl_pips, self.tp_pips, self.id, self.timeframe)

        elif signal == 'SELL':
            if position and position.type == mt5.ORDER_TYPE_BUY:
                self.log_activity('CLOSE BUY', "Menutup posisi BELI untuk membuka posisi JUAL.", is_notification=True)
                profit_loss = position.profit if hasattr(position, 'profit') else 0
                self._log_trade_for_ai_mentor(position, profit_loss, 'CLOSE_BUY')
                close_trade(position)
                position = None
            if not position:
                self.log_activity('OPEN SELL', "Membuka posisi JUAL berdasarkan sinyal.", is_notification=True)
                place_trade(self.market_for_mt5, mt5.ORDER_TYPE_SELL, self.risk_percent, self.sl_pips, self.tp_pips, self.id, self.timeframe)

    def _log_trade_for_ai_mentor(self, position, profit_loss, action_type):
        try:
            stop_loss_used = hasattr(position, 'sl') and position.sl > 0
            take_profit_used = hasattr(position, 'tp') and position.tp > 0
            log_trade_for_ai_analysis(
                bot_id=self.id,
                symbol=self.market_for_mt5 or self.market,
                profit_loss=profit_loss,
                lot_size=position.volume if hasattr(position, 'volume') else self.risk_percent,
                stop_loss_used=stop_loss_used,
                take_profit_used=take_profit_used,
                risk_percent=self.risk_percent,
                strategy_used=self.strategy_name
            )
            logger.info(f"[AI MENTOR] Trade logged for bot {self.id}: {action_type} {self.market_for_mt5} P/L: ${profit_loss:.2f}")
        except Exception as e:
            logger.error(f"[AI MENTOR] Failed to log trade: {e}")