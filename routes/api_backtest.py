# core/routes/api_backtest.py

import numpy as np
import pandas as pd
import json
import logging
import os
import itertools
import time
import uuid
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
import MetaTrader5 as mt5
from core.backtesting.enhanced_engine import run_enhanced_backtest as run_backtest
from core.db.queries import get_all_backtest_history
import optuna
from optuna.trial import TrialState
from scipy.optimize import differential_evolution
from sklearn.model_selection import TimeSeriesSplit
from core.db.connection import get_db_connection
from core.strategies.gold_btc_presets import get_presets, get_risk_presets, get_all_strategy_presets

api_backtest = Blueprint('api_backtest', __name__)
logger = logging.getLogger(__name__)

_optimization_state = {}
_opt_state_lock = threading.Lock()

TIMEFRAME_MAP = {
    'M1': mt5.TIMEFRAME_M1,
    'M5': mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'M30': mt5.TIMEFRAME_M30,
    'H1': mt5.TIMEFRAME_H1,
    'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1,
    'W1': mt5.TIMEFRAME_W1,
}

def download_mt5_data(symbol, timeframe_str, date_from, date_to):
    """從MT5下載歷史K線數據"""
    tf = TIMEFRAME_MAP.get(timeframe_str.upper(), mt5.TIMEFRAME_H1)
    
    # 檢查symbol是否存在
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        # 嘗試查找
        from core.utils.mt5 import find_mt5_symbol
        resolved = find_mt5_symbol(symbol)
        if resolved:
            symbol = resolved
            symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise ValueError(f"找不到交易品種: {symbol}")
    
    # 啟用symbol
    if not symbol_info.visible:
        mt5.symbol_select(symbol, True)
        symbol_info = mt5.symbol_info(symbol)
    
    # 獲取點差和合約規格
    spread = symbol_info.spread
    digits = symbol_info.digits
    contract_size = symbol_info.trade_contract_size
    point = symbol_info.point
    pip_size = point * (10 if digits == 5 or digits == 3 else 1)
    
    logger.info(f"Symbol: {symbol}, Spread: {spread}, Digits: {digits}, Contract: {contract_size}, Point: {point}, PipSize: {pip_size}")
    
    # 轉換日期
    dt_from = datetime.strptime(date_from, '%Y-%m-%d')
    dt_to = datetime.strptime(date_to, '%Y-%m-%d')
    
    # 從MT5下載數據
    rates = mt5.copy_rates_range(symbol, tf, dt_from, dt_to)
    if rates is None or len(rates) == 0:
        raise ValueError(f"MT5下載數據失敗: {symbol} {timeframe_str} {date_from}~{date_to}")
    
    # 轉換為DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    logger.info(f"Downloaded {len(df)} bars for {symbol} {timeframe_str}")
    
    # 返回數據和合約信息
    contract_info = {
        'symbol': symbol,
        'spread': spread,
        'digits': digits,
        'contract_size': contract_size,
        'point': point,
        'pip_size': pip_size,
        'spread_pips': spread * point / pip_size,  # 點差轉換為點數
    }
    
    return df, contract_info

def save_backtest_result(strategy_name, filename, params, results):
    for key, value in results.items():
        if isinstance(value, (np.floating, float)) and (np.isinf(value) or np.isnan(value)):
            results[key] = None

    profit_to_save = results.get('total_profit_usd', 0)
    spread_costs = results.get('total_spread_costs', 0)
    instrument = results.get('instrument', 'UNKNOWN')
    
    enhanced_params = params.copy()
    enhanced_params['engine_type'] = 'enhanced'
    enhanced_params['spread_costs'] = spread_costs
    enhanced_params['instrument'] = instrument
    
    if 'engine_config' in results:
        engine_config = results['engine_config']
        enhanced_params['realistic_execution'] = engine_config.get('realistic_execution', True)
        enhanced_params['spread_costs_enabled'] = engine_config.get('spread_costs_enabled', True)
        if 'instrument_config' in engine_config:
            inst_config = engine_config['instrument_config']
            enhanced_params['max_risk_percent'] = inst_config.get('max_risk_percent', 2.0)
            enhanced_params['typical_spread_pips'] = inst_config.get('typical_spread_pips', 2.0)
            enhanced_params['max_lot_size'] = inst_config.get('max_lot_size', 10.0)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backtest_results (
                    strategy_name, data_filename, total_profit_usd, total_trades, 
                    win_rate_percent, max_drawdown_percent, wins, losses, equity_curve, trade_log, parameters
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                strategy_name,
                filename,
                profit_to_save,
                results.get('total_trades', 0),
                results.get('win_rate_percent', 0),
                results.get('max_drawdown_percent', 0),
                results.get('wins', 0),
                results.get('losses', 0),
                json.dumps(results.get('equity_curve', [])),
                json.dumps(results.get('trades', [])),
                json.dumps(enhanced_params)
            ))
            conn.commit()
    except Exception as e:
        logger.error(f"[DB ERROR] Failed to save backtest result: {e}", exc_info=True)

@api_backtest.route('/api/backtest/run', methods=['POST'])
def run_backtest_route():
    """執行回測：從MT5下載數據 + 向量化回測"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "請提供JSON參數"}), 400
        
        symbol = data.get('symbol', 'XAUUSDm')
        timeframe_str = data.get('timeframe', 'H1')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        strategy_id = data.get('strategy')
        params = data.get('params', {})
        
        if not strategy_id:
            return jsonify({"error": "請選擇策略"}), 400
        if not date_from or not date_to:
            return jsonify({"error": "請選擇日期範圍"}), 400
        
        # 從MT5下載數據
        logger.info(f"Downloading MT5 data: {symbol} {timeframe_str} {date_from}~{date_to}")
        df, contract_info = download_mt5_data(symbol, timeframe_str, date_from, date_to)
        
        # 映射參數名稱
        enhanced_params = params.copy()
        if 'lot_size' in params and 'risk_percent' not in params:
            enhanced_params['risk_percent'] = float(params['lot_size'])
        if 'sl_pips' in params and 'sl_atr_multiplier' not in params:
            enhanced_params['sl_atr_multiplier'] = float(params['sl_pips'])
        if 'tp_pips' in params and 'tp_atr_multiplier' not in params:
            enhanced_params['tp_atr_multiplier'] = float(params['tp_pips'])
        
        # 傳入MT5合約信息用於實時點差和滑點
        engine_config = {
            'enable_spread_costs': True,
            'enable_slippage': True,
            'enable_realistic_execution': True,
            'mt5_contract_info': contract_info,  # 從MT5讀取的真實規格
            'initial_capital': float(data.get('initial_capital', 100)),
        }
        
        results = run_backtest(strategy_id, enhanced_params, df, symbol_name=symbol, engine_config=engine_config)
        
        # 附加合約信息到結果
        results['actual_spread_pips'] = contract_info.get('spread_pips', 0)
        results['pip_size'] = contract_info.get('pip_size', 0.01)
        results['symbol'] = symbol
        results['timeframe'] = timeframe_str
        
        if results and not results.get('error'):
            strategy_name = results.get('strategy_name', strategy_id)
            filename = f"{symbol}_{timeframe_str}_{date_from}_{date_to}"
            save_backtest_result(strategy_name, filename, params, results)
        
        return jsonify(results)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}", exc_info=True)
        return jsonify({"error": f"回測失敗: {str(e)}"}), 500

@api_backtest.route('/api/backtest/history', methods=['GET'])
def get_history_route():
    try:
        history = get_all_backtest_history()
        processed_history = []
        for record in history:
            new_record = dict(record)
            
            if 'trade_log' in new_record and new_record['trade_log']:
                try:
                    trades = json.loads(new_record['trade_log'])
                    if isinstance(trades, list):
                        new_record['trade_log'] = trades
                except (json.JSONDecodeError, TypeError):
                    new_record['trade_log'] = []
            else:
                new_record['trade_log'] = []
            
            if 'equity_curve' in new_record and new_record['equity_curve']:
                try:
                    equity = json.loads(new_record['equity_curve'])
                    if isinstance(equity, list):
                        new_record['equity_curve'] = equity
                except (json.JSONDecodeError, TypeError):
                    new_record['equity_curve'] = []
            else:
                new_record['equity_curve'] = []
                
            if 'parameters' in new_record and new_record['parameters']:
                try:
                    params = json.loads(new_record['parameters'])
                    if isinstance(params, dict):
                        new_record['parameters'] = params
                except (json.JSONDecodeError, TypeError):
                    new_record['parameters'] = {}
            else:
                new_record['parameters'] = {}
            
            processed_history.append(new_record)
            
        return jsonify(processed_history)
    except Exception as e:
        logger.error(f"Error processing history: {str(e)}", exc_info=True)
        return jsonify({"error": f"讀取歷史失敗: {str(e)}"}), 500

def _generate_param_grid(optimization_params):
    """Generate all parameter combinations from min/max/step ranges."""
    keys = []
    values = []
    for key, rng in optimization_params.items():
        keys.append(key)
        mn = rng['min']
        mx = rng['max']
        st = rng['step']
        if st <= 0:
            vals = [mn]
        else:
            vals = []
            v = mn
            while v <= mx + 1e-10:
                vals.append(round(v, 10))
                v += st
        values.append(vals)
    grid = [dict(zip(keys, combo)) for combo in itertools.product(*values)]
    return grid


def _build_enhanced_params(params_combo):
    """Map optimization param keys to engine param keys."""
    enhanced = {}
    if 'risk_percent' in params_combo:
        enhanced['risk_percent'] = params_combo['risk_percent']
    if 'sl_atr' in params_combo:
        enhanced['sl_pips'] = params_combo['sl_atr']
        enhanced['sl_atr_multiplier'] = params_combo['sl_atr']
    if 'tp_atr' in params_combo:
        enhanced['tp_pips'] = params_combo['tp_atr']
        enhanced['tp_atr_multiplier'] = params_combo['tp_atr']
    for key, val in params_combo.items():
        if key not in ('risk_percent', 'sl_atr', 'tp_atr'):
            enhanced[key] = val
    return enhanced


# ============================================================
# Shared optimization helpers
# ============================================================

def _create_state():
    return {
        'status': 'running', 'progress': 0, 'total': 0,
        'phase': 1, 'total_phases': 1,
        'logs': [], 'best_score': -float('inf'), 'best_params': None,
        'best_result': None, 'all_results': [], 'cancel_flag': False,
        'new_logs': [], 'done': False,
        'optimizer': '', 'wfo_enabled': False,
    }

def _push_log(state, msg, is_best=False):
    entry = {'msg': msg, 'is_best': is_best, 'phase': state['phase'],
             'time': time.strftime('%H:%M:%S')}
    state['logs'].append(entry)
    state['new_logs'].append(entry)
    if is_best:
        time.sleep(0.01)

def _push_progress(state, i, total_phase):
    state['progress'] = i + 1
    if (i + 1) % 5 == 0 or i == 0 or i == total_phase - 1:
        pct = round((i + 1) / max(total_phase, 1) * 100)
        _push_log(state, f'已完成 {i+1}/{total_phase} 組（{pct}%）')
    state['new_logs'] = state.get('new_logs', [])

def _try_update_best(state, params_combo, result):
    net = result.get('total_profit_usd', 0)
    dd = result.get('max_drawdown_percent', 1)
    score = net / max(dd, 0.01) if dd > 0 else net
    state['all_results'].append({
        'params': params_combo,
        'total_profit_usd': net,
        'win_rate_percent': result.get('win_rate_percent', 0),
        'max_drawdown_percent': result.get('max_drawdown_percent', 0),
        'total_trades': result.get('total_trades', 0),
    })
    if score > state['best_score']:
        state['best_score'] = score
        state['best_params'] = params_combo
        state['best_result'] = result
        return True
    return False

def _download_and_config(data, state):
    symbol = data.get('symbol', 'XAUUSDm')
    timeframe_str = data.get('timeframe', 'H1')
    _push_log(state, f'正在從 MT5 下載 {symbol} {timeframe_str} 歷史數據...')
    df, contract_info = download_mt5_data(symbol, timeframe_str,
                                          data.get('date_from'), data.get('date_to'))
    _push_log(state, f'下載完成 {len(df)} 根 K 線')
    engine_config = {
        'enable_spread_costs': True,
        'enable_slippage': True,
        'enable_realistic_execution': True,
        'mt5_contract_info': contract_info,
        'initial_capital': float(data.get('initial_capital', 100)),
    }
    return df, engine_config


# ============================================================
# Grid Search (existing, retained)
# ============================================================

def _run_grid_search_thread(task_id, data):
    state = _create_state()
    state['optimizer'] = 'grid'
    with _opt_state_lock:
        _optimization_state[task_id] = state

    try:
        strategy_id = data.get('strategy')
        optimization_params = data.get('optimization_params', {})
        df, engine_config = _download_and_config(data, state)

        fine_grid = _generate_param_grid(optimization_params)
        total_fine = len(fine_grid)

        if total_fine <= 200:
            state['total_phases'] = 1
            state['phase'] = 1
            state['total'] = total_fine
            _push_log(state, f'組合數不多（{total_fine} 組），直接精搜')
            for i, pc in enumerate(fine_grid):
                if state['cancel_flag']: break
                enhanced = _build_enhanced_params(pc)
                result = run_backtest(strategy_id, enhanced, df,
                                      symbol_name=data.get('symbol'), engine_config=engine_config)
                if result.get('error'): continue
                is_new = _try_update_best(state, pc, result)
                if is_new:
                    _push_log(state, f'新高分！淨利 ${result["total_profit_usd"]:+.2f}　'
                              f'勝率 {result.get("win_rate_percent",0):.0f}%　'
                              f'回撤 {result.get("max_drawdown_percent",0):.2f}%　{pc}', is_best=True)
                _push_progress(state, i, total_fine)
        else:
            state['total_phases'] = 2
            target_coarse = max(20, min(200, int(total_fine ** 0.5)))
            param_count = len(optimization_params)
            if param_count > 0:
                coarse_mult = round(total_fine ** (1 / param_count) / target_coarse ** (1 / param_count), 1)
                coarse_mult = max(2.0, min(10.0, coarse_mult))
            else:
                coarse_mult = 3.0
            coarse_mult = round(coarse_mult * 2) / 2

            state['phase'] = 1
            coarse_params = {}
            for key, rng in optimization_params.items():
                cs = rng['step'] * coarse_mult
                if cs > (rng['max'] - rng['min']): cs = rng['max'] - rng['min']
                if cs <= 0: cs = rng['step']
                coarse_params[key] = {'min': rng['min'], 'max': rng['max'], 'step': cs}

            cgrid = _generate_param_grid(coarse_params)
            state['total'] = len(cgrid)
            _push_log(state, f'階段一 粗篩（步長放大 {coarse_mult}× → {len(cgrid)} 組）')
            for i, pc in enumerate(cgrid):
                if state['cancel_flag']: break
                enhanced = _build_enhanced_params(pc)
                result = run_backtest(strategy_id, enhanced, df,
                                      symbol_name=data.get('symbol'), engine_config=engine_config)
                if result.get('error'): continue
                is_new = _try_update_best(state, pc, result)
                if is_new:
                    _push_log(state, f'粗篩新高分！淨利 ${result["total_profit_usd"]:+.2f}　{pc}', is_best=True)
                _push_progress(state, i, len(cgrid))
            if state['cancel_flag']: state['status'] = 'cancelled'; state['done'] = True; return
            if state['best_params'] is None: state['status'] = 'error'; state['done'] = True; return

            _push_log(state, f'粗篩完成，最佳 → {state["best_params"]}')
            state['phase'] = 2; state['progress'] = 0
            fine_params = {}
            for key, rng in optimization_params.items():
                bv = state['best_params'].get(key, rng['min'])
                cs = coarse_params.get(key, {}).get('step', rng['step'])
                fine_params[key] = {'min': max(rng['min'], bv - cs),
                                    'max': min(rng['max'], bv + cs),
                                    'step': rng['step']}
            fgrid = _generate_param_grid(fine_params)
            state['total'] = len(fgrid)
            if len(fgrid) == 0:
                _push_log(state, '精校範圍過窄，沿用粗篩結果')
                state['done'] = True; state['status'] = 'done'; return
            _push_log(state, f'精校 {len(fgrid)} 組')
            for i, pc in enumerate(fgrid):
                if state['cancel_flag']: break
                enhanced = _build_enhanced_params(pc)
                result = run_backtest(strategy_id, enhanced, df,
                                      symbol_name=data.get('symbol'), engine_config=engine_config)
                if result.get('error'): continue
                is_new = _try_update_best(state, pc, result)
                if is_new:
                    _push_log(state, f'精校新高分！淨利 ${result["total_profit_usd"]:+.2f}　{pc}', is_best=True)
                _push_progress(state, i, len(fgrid))

        state['status'] = 'cancelled' if state['cancel_flag'] else 'done'
        if state['best_params']:
            _push_log(state, f'完成！最佳淨利 ${state["best_result"].get("total_profit_usd",0):+.2f}　'
                      f'{state["best_params"]}')
        else:
            _push_log(state, '完成（未找到有效結果）')
    except Exception as e:
        logger.error(f"Grid opt error: {e}", exc_info=True)
        _push_log(state, f'錯誤：{str(e)}')
        state['status'] = 'error'
    finally:
        state['done'] = True


# ============================================================
# Optuna TPE (single-objective)
# ============================================================

def _run_optuna_tpe_thread(task_id, data):
    state = _create_state()
    state['optimizer'] = 'optuna_tpe'
    state['total_phases'] = 1
    with _opt_state_lock:
        _optimization_state[task_id] = state

    try:
        strategy_id = data.get('strategy')
        params_def = data.get('optimization_params', {})
        df, engine_config = _download_and_config(data, state)

        bounds = {}
        for k, rng in params_def.items():
            lo, hi = float(rng['min']), float(rng['max'])
            if lo > hi: lo, hi = hi, lo
            bounds[k] = (lo, hi)

        n_params = len(params_def)
        n_trials = max(50, min(500, n_params * 100))

        _push_log(state, f'Optuna TPE 啟動（最多 {n_trials} 次嘗試），開始搜尋最優參數')

        def objective(trial):
            if state['cancel_flag']:
                raise optuna.exceptions.TrialPruned()
            pc = {}
            for k, (lo, hi) in bounds.items():
                step = params_def.get(k, {}).get('step', 0.01)
                pc[k] = trial.suggest_float(k, lo, hi, step=step)
            enhanced = _build_enhanced_params(pc)
            result = run_backtest(strategy_id, enhanced, df,
                                  symbol_name=data.get('symbol'), engine_config=engine_config)
            if result.get('error'):
                return -1e9
            is_new = _try_update_best(state, pc, result)
            trial_number = trial.number if hasattr(trial, 'number') else 0
            if is_new:
                _push_log(state, f'第 {trial_number+1} 次 新高分！淨利 ${result["total_profit_usd"]:+.2f}　'
                          f'勝率 {result.get("win_rate_percent",0):.0f}%　{pc}', is_best=True)
            if trial_number % 5 == 0:
                _push_log(state, f'第 {trial_number+1}/{n_trials} 次嘗試中，目前最佳淨利 ${state.get("best_score", -1e9):+.2f}')
            state['progress'] = trial_number + 1
            state['total'] = n_trials
            state['new_logs'] = state.get('new_logs', [])
            net = result.get('total_profit_usd', 0)
            dd = result.get('max_drawdown_percent', 1)
            return net / max(dd, 0.01) if dd > 0 else net

        sampler = optuna.samplers.TPESampler(seed=42)
        study = optuna.create_study(direction='maximize', sampler=sampler)
        study.optimize(objective, n_trials=n_trials, catch=(Exception,))

        state['status'] = 'cancelled' if state['cancel_flag'] else 'done'
        if state['best_params']:
            _push_log(state, f'Optuna 完成！最佳淨利 ${state["best_result"].get("total_profit_usd",0):+.2f}　'
                      f'{state["best_params"]}')
        else:
            _push_log(state, 'Optuna 完成（未找到有效結果）')
    except Exception as e:
        logger.error(f"Optuna TPE error: {e}", exc_info=True)
        _push_log(state, f'錯誤：{str(e)}')
        state['status'] = 'error'
    finally:
        state['done'] = True


# ============================================================
# Optuna Multi-Objective (Pareto: maximize profit, minimize drawdown)
# ============================================================

def _run_optuna_multiobj_thread(task_id, data):
    state = _create_state()
    state['optimizer'] = 'optuna_multiobj'
    state['total_phases'] = 1
    with _opt_state_lock:
        _optimization_state[task_id] = state

    try:
        strategy_id = data.get('strategy')
        params_def = data.get('optimization_params', {})
        df, engine_config = _download_and_config(data, state)

        bounds = {}
        for k, rng in params_def.items():
            lo, hi = float(rng['min']), float(rng['max'])
            if lo > hi: lo, hi = hi, lo
            bounds[k] = (lo, hi)

        n_params = len(params_def)
        n_trials = max(50, min(500, n_params * 100))

        _push_log(state, f'Optuna 多目標啟動（最多 {n_trials} 次），搜尋 Pareto 前沿')
        _push_log(state, '目標：最大化淨利 ＋ 最小化回撤')

        def multi_objective(trial):
            if state['cancel_flag']:
                raise optuna.exceptions.TrialPruned()
            pc = {}
            for k, (lo, hi) in bounds.items():
                step = params_def.get(k, {}).get('step', 0.01)
                pc[k] = trial.suggest_float(k, lo, hi, step=step)
            enhanced = _build_enhanced_params(pc)
            result = run_backtest(strategy_id, enhanced, df,
                                  symbol_name=data.get('symbol'), engine_config=engine_config)
            if result.get('error'):
                return -1e9, 1e9
            net = result.get('total_profit_usd', 0)
            dd = result.get('max_drawdown_percent', 100)
            trial_number = trial.number if hasattr(trial, 'number') else 0
            is_new = _try_update_best(state, pc, result)
            if is_new:
                _push_log(state, f'第 {trial_number+1} 次 Pareto 點！淨利 ${net:+.2f}　回撤 {dd:.2f}%　{pc}', is_best=True)
            if trial_number % 5 == 0:
                _push_log(state, f'第 {trial_number+1}/{n_trials} 次搜尋中')
            state['progress'] = trial_number + 1
            state['total'] = n_trials
            state['new_logs'] = state.get('new_logs', [])
            return net, dd

        study = optuna.create_study(
            directions=['maximize', 'minimize'],
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        study.optimize(multi_objective, n_trials=n_trials, catch=(Exception,))

        state['status'] = 'cancelled' if state['cancel_flag'] else 'done'
        pareto_trials = study.best_trials
        state['pareto_front'] = [
            {'params': t.params, 'profit': t.values[0], 'drawdown': t.values[1]}
            for t in pareto_trials
        ]
        _push_log(state, f'多目標完成！Pareto 前沿共 {len(pareto_trials)} 個最優解')
        if state['best_params']:
            _push_log(state, f'綜合最佳：淨利 ${state["best_result"].get("total_profit_usd",0):+.2f}　'
                      f'{state["best_params"]}')
    except Exception as e:
        logger.error(f"Optuna multi-obj error: {e}", exc_info=True)
        _push_log(state, f'錯誤：{str(e)}')
        state['status'] = 'error'
    finally:
        state['done'] = True


# ============================================================
# Differential Evolution (scipy)
# ============================================================

def _run_de_thread(task_id, data):
    state = _create_state()
    state['optimizer'] = 'de'
    state['total_phases'] = 1
    with _opt_state_lock:
        _optimization_state[task_id] = state

    try:
        strategy_id = data.get('strategy')
        params_def = data.get('optimization_params', {})
        df, engine_config = _download_and_config(data, state)

        param_keys = list(params_def.keys())
        bounds_list = [(float(params_def[k]['min']), float(params_def[k]['max'])) for k in param_keys]
        bounds_list = [(min(lo, hi), max(lo, hi)) for lo, hi in bounds_list]

        maxiter = max(20, min(100, len(param_keys) * 30))
        popsize = max(5, min(15, len(param_keys) * 5))

        _push_log(state, f'差分進化啟動（迭代 {maxiter} 輪 × 族群 {popsize}），全域搜尋中')
        state['total'] = maxiter
        iteration_count = [0]

        def de_objective(x):
            if state['cancel_flag']:
                raise RuntimeError('cancelled')
            pc = {param_keys[i]: float(x[i]) for i in range(len(param_keys))}
            enhanced = _build_enhanced_params(pc)
            result = run_backtest(strategy_id, enhanced, df,
                                  symbol_name=data.get('symbol'), engine_config=engine_config)
            if result.get('error'):
                return 1e9
            net = result.get('total_profit_usd', 0)
            dd = result.get('max_drawdown_percent', 1)
            score = net / max(dd, 0.01) if dd > 0 else net
            is_new = _try_update_best(state, pc, result)
            if is_new:
                _push_log(state, f'DE 新高分！淨利 ${net:+.2f}　回撤 {dd:.2f}%　{pc}', is_best=True)
            return -score

        def de_callback(xk, convergence):
            iteration_count[0] += 1
            state['progress'] = iteration_count[0]
            state['new_logs'] = state.get('new_logs', [])
            if iteration_count[0] % 3 == 0:
                _push_log(state, f'DE 第 {iteration_count[0]}/{maxiter} 輪，收斂度 {convergence:.4f}')
            return state['cancel_flag']

        result = differential_evolution(
            de_objective, bounds_list,
            maxiter=maxiter, popsize=popsize,
            seed=42, callback=de_callback,
            disp=False,
        )

        state['status'] = 'cancelled' if state['cancel_flag'] else 'done'
        if state['best_params']:
            _push_log(state, f'DE 完成！最佳淨利 ${state["best_result"].get("total_profit_usd",0):+.2f}　'
                      f'{state["best_params"]}')
        else:
            _push_log(state, 'DE 完成（未找到有效結果）')
    except RuntimeError:
        state['status'] = 'cancelled'; state['done'] = True
    except Exception as e:
        logger.error(f"DE error: {e}", exc_info=True)
        _push_log(state, f'錯誤：{str(e)}')
        state['status'] = 'error'
    finally:
        state['done'] = True


# ============================================================
# Walk-Forward Optimization wrapper
# ============================================================

OPTIMIZER_REGISTRY = {
    'grid': _run_grid_search_thread,
    'optuna_tpe': _run_optuna_tpe_thread,
    'optuna_multiobj': _run_optuna_multiobj_thread,
    'de': _run_de_thread,
}

def _run_wfo_thread(task_id, data):
    """WFO: split data into rolling windows, optimize each, validate across windows."""
    state = _create_state()
    state['optimizer'] = data.get('wfo_inner', 'optuna_tpe')
    state['wfo_enabled'] = True
    with _opt_state_lock:
        _optimization_state[task_id] = state

    try:
        strategy_id = data.get('strategy')
        optimization_params = data.get('optimization_params', {})
        df, engine_config = _download_and_config(data, state)

        n_splits = min(5, max(2, len(df) // 500))
        if n_splits < 2:
            _push_log(state, '資料量不足以進行 WFO（需至少 1000 根 K 線），改用一般優化')
            inner = OPTIMIZER_REGISTRY.get(data.get('wfo_inner', 'optuna_tpe'), _run_grid_search_thread)
            inner(task_id, data)
            return

        tscv = TimeSeriesSplit(n_splits=n_splits)
        state['total_phases'] = n_splits + 1
        state['total'] = n_splits

        window_scores = {}
        _push_log(state, f'WFO 啟動：{n_splits} 個時間窗口，內部優化器 {state["optimizer"]}')

        for window_idx, (train_idx, test_idx) in enumerate(tscv.split(df)):
            if state['cancel_flag']: break
            state['phase'] = window_idx + 1
            state['progress'] = 0
            _push_log(state, f'WFO 窗口 {window_idx+1}/{n_splits}：訓練 {len(train_idx)} 根 + 測試 {len(test_idx)} 根')

            train_df = df.iloc[train_idx]
            test_df = df.iloc[test_idx]

            # Run inner optimizer on train data
            inner_optimizer = data.get('wfo_inner', 'optuna_tpe')

            if inner_optimizer == 'grid':
                _run_grid_on_slice(state, task_id, data, train_df, engine_config, window_idx, n_splits)
            elif inner_optimizer in ('optuna_tpe', 'optuna_multiobj'):
                _run_optuna_on_slice(state, task_id, data, train_df, engine_config, window_idx, n_splits, inner_optimizer)
            elif inner_optimizer == 'de':
                _run_de_on_slice(state, task_id, data, train_df, engine_config, window_idx, n_splits)
            else:
                _run_optuna_on_slice(state, task_id, data, train_df, engine_config, window_idx, n_splits, 'optuna_tpe')

            if state['cancel_flag']: break

            # Validate best params on test data
            if state['best_params']:
                enhanced = _build_enhanced_params(state['best_params'])
                test_result = run_backtest(strategy_id, enhanced, test_df,
                                           symbol_name=data.get('symbol'), engine_config=engine_config)
                test_net = test_result.get('total_profit_usd', 0)
                test_dd = test_result.get('max_drawdown_percent', 1)
                _push_log(state, f'窗口 {window_idx+1} 驗證：測試淨利 ${test_net:+.2f}　回撤 {test_dd:.2f}%')
                window_scores[window_idx] = {
                    'params': state['best_params'],
                    'train_profit': state['best_result'].get('total_profit_usd', 0),
                    'test_profit': test_net,
                    'test_drawdown': test_dd,
                }
            else:
                _push_log(state, f'窗口 {window_idx+1}：未找到有效參數')
            state['progress'] = window_idx + 1

        if state['cancel_flag']:
            state['status'] = 'cancelled'; state['done'] = True; return

        # Summary across all windows
        state['phase'] = n_splits + 1
        state['total_phases'] = n_splits + 1

        if window_scores:
            avg_test_profit = np.mean([s['test_profit'] for s in window_scores.values()])
            _push_log(state, f'WFO 總結：{len(window_scores)}/{n_splits} 個窗口有效')
            _push_log(state, f'平均測試淨利 ${avg_test_profit:+.2f}')
            best_window = max(window_scores.items(), key=lambda x: x[1]['test_profit'])
            state['wfo_windows'] = [{'window': k, **v} for k, v in window_scores.items()]
            _push_log(state, f'最佳窗口 #{best_window[0]+1}：淨利 ${best_window[1]["test_profit"]:+.2f}　'
                      f'{best_window[1]["params"]}')
        else:
            _push_log(state, 'WFO：所有窗口無效')

        state['status'] = 'done'
    except Exception as e:
        logger.error(f"WFO error: {e}", exc_info=True)
        _push_log(state, f'WFO 錯誤：{str(e)}')
        state['status'] = 'error'
    finally:
        state['done'] = True


def _run_grid_on_slice(state, original_task_id, data, df, engine_config, window_idx, n_splits):
    strategy_id = data.get('strategy')
    optimization_params = data.get('optimization_params', {})
    fgrid = _generate_param_grid(optimization_params)
    state['total'] = len(fgrid)
    for i, pc in enumerate(fgrid):
        if state['cancel_flag']: break
        enhanced = _build_enhanced_params(pc)
        result = run_backtest(strategy_id, enhanced, df,
                              symbol_name=data.get('symbol'), engine_config=engine_config)
        if result.get('error'): continue
        is_new = _try_update_best(state, pc, result)
        if is_new:
            _push_log(state, f'W{window_idx+1} 新高分！淨利 ${result["total_profit_usd"]:+.2f}　{pc}', is_best=True)
        _push_progress(state, i, len(fgrid))

def _run_optuna_on_slice(state, original_task_id, data, df, engine_config, window_idx, n_splits, optimizer):
    strategy_id = data.get('strategy')
    params_def = data.get('optimization_params', {})
    bounds = {}
    for k, rng in params_def.items():
        lo, hi = float(rng['min']), float(rng['max'])
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo > hi:
            lo, hi = hi, lo
        bounds[k] = (lo, hi)
    n_trials = max(30, min(200, len(params_def) * 50))
    state['total'] = n_trials
    trial_count = [0]

    is_multi = (optimizer == 'optuna_multiobj')
    directions = ['maximize', 'minimize'] if is_multi else ['maximize']

    def objective(trial):
        if state['cancel_flag']:
            raise optuna.exceptions.TrialPruned()
        pc = {}
        for k, (lo, hi) in bounds.items():
            step = params_def.get(k, {}).get('step', 0.01)
            pc[k] = trial.suggest_float(k, lo, hi, step=step)
        enhanced = _build_enhanced_params(pc)
        result = run_backtest(strategy_id, enhanced, df,
                              symbol_name=data.get('symbol'), engine_config=engine_config)
        if result.get('error'):
            return (-1e9, 1e9) if is_multi else -1e9
        net = result.get('total_profit_usd', 0)
        dd = result.get('max_drawdown_percent', 100)
        trial_count[0] += 1
        is_new = _try_update_best(state, pc, result)
        if is_new:
            _push_log(state, f'W{window_idx+1} 新高分！淨利 ${net:+.2f}　{pc}', is_best=True)
        if trial_count[0] % 10 == 0:
            _push_log(state, f'W{window_idx+1} 第 {trial_count[0]}/{n_trials} 次')
        state['progress'] = trial_count[0]
        state['new_logs'] = state.get('new_logs', [])
        return (net, -dd) if is_multi else (net / max(dd, 0.01) if dd > 0 else net)

    study = optuna.create_study(directions=directions, sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, catch=(Exception,))

def _run_de_on_slice(state, original_task_id, data, df, engine_config, window_idx, n_splits):
    strategy_id = data.get('strategy')
    params_def = data.get('optimization_params', {})
    param_keys = list(params_def.keys())
    bounds_list = [(float(params_def[k]['min']), float(params_def[k]['max'])) for k in param_keys]
    maxiter = max(10, min(50, len(param_keys) * 15))
    state['total'] = maxiter
    it_count = [0]

    def de_obj(x):
        if state['cancel_flag']: raise RuntimeError('cancelled')
        pc = {param_keys[i]: float(x[i]) for i in range(len(param_keys))}
        enhanced = _build_enhanced_params(pc)
        result = run_backtest(strategy_id, enhanced, df,
                              symbol_name=data.get('symbol'), engine_config=engine_config)
        if result.get('error'): return 1e9
        net = result.get('total_profit_usd', 0); dd = result.get('max_drawdown_percent', 1)
        score = net / max(dd, 0.01) if dd > 0 else net
        is_new = _try_update_best(state, pc, result)
        if is_new:
            _push_log(state, f'W{window_idx+1} DE新高分！淨利 ${net:+.2f}　{pc}', is_best=True)
        return -score

    def de_cb(xk, convergence):
        it_count[0] += 1
        state['progress'] = it_count[0]
        state['new_logs'] = state.get('new_logs', [])
        if it_count[0] % 5 == 0:
            _push_log(state, f'W{window_idx+1} DE {it_count[0]}/{maxiter} 輪，收斂 {convergence:.4f}')
        return state['cancel_flag']

    differential_evolution(de_obj, bounds_list, maxiter=maxiter, popsize=8, seed=42,
                           callback=de_cb, disp=False)


# ============================================================
# Dispatch
# ============================================================

def _dispatch_optimization(task_id, data):
    optimizer = data.get('optimizer', 'grid')
    if data.get('wfo_enabled', False):
        data['wfo_inner'] = optimizer
        threading.Thread(target=_run_wfo_thread, args=(task_id, data), daemon=True).start()
    else:
        func = OPTIMIZER_REGISTRY.get(optimizer, _run_grid_search_thread)
        threading.Thread(target=func, args=(task_id, data), daemon=True).start()


@api_backtest.route('/api/backtest/optimize/start', methods=['POST'])
def optimize_start():
    """啟動背景優化線程"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "請提供JSON參數"}), 400

        if not data.get('strategy'):
            return jsonify({"error": "請選擇策略"}), 400
        if not data.get('date_from') or not data.get('date_to'):
            return jsonify({"error": "請選擇日期範圍"}), 400
        if not data.get('optimization_params'):
            return jsonify({"error": "請設定優化參數範圍"}), 400

        task_id = str(uuid.uuid4())[:8]
        _dispatch_optimization(task_id, data)

        return jsonify({'task_id': task_id, 'status': 'started'})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Optimization start error: {str(e)}", exc_info=True)
        return jsonify({"error": f"啟動失敗: {str(e)}"}), 500


@api_backtest.route('/api/backtest/optimize/stream/<task_id>')
def optimize_stream(task_id):
    """SSE 即時推送優化進度"""
    def generate():
        last_log_idx = 0
        while True:
            state = _optimization_state.get(task_id)
            if state is None:
                yield f"data: {json.dumps({'error': 'task not found'})}\n\n"
                break

            new_logs = state.get('new_logs', [])
            payload = {
                'status': state.get('status', 'running'),
                'phase': state.get('phase', 1),
                'total_phases': state.get('total_phases', 1),
                'progress': state.get('progress', 0),
                'total': state.get('total', 0),
                'best_score': state.get('best_score'),
                'best_params': state.get('best_params'),
                'best_result_summary': None,
                'logs': new_logs[last_log_idx:],
                'done': state.get('done', False),
                'optimizer': state.get('optimizer', ''),
                'wfo_enabled': state.get('wfo_enabled', False),
            }

            if state.get('best_result'):
                br = state['best_result']
                payload['best_result_summary'] = {
                    'total_profit_usd': br.get('total_profit_usd', 0),
                    'win_rate_percent': br.get('win_rate_percent', 0),
                    'max_drawdown_percent': br.get('max_drawdown_percent', 0),
                    'total_trades': br.get('total_trades', 0),
                }

            last_log_idx = len(new_logs)
            yield f"data: {json.dumps(payload, default=str)}\n\n"

            if state.get('done'):
                break

            time.sleep(0.1)

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@api_backtest.route('/api/backtest/optimize/cancel/<task_id>', methods=['POST'])
def optimize_cancel(task_id):
    """取消優化並清理狀態"""
    state = _optimization_state.get(task_id)
    if state:
        state['cancel_flag'] = True
        state['status'] = 'cancelling'

    def _cleanup():
        time.sleep(2)
        with _opt_state_lock:
            s = _optimization_state.get(task_id)
            if s:
                s['status'] = 'cancelled'
                s['done'] = True
            # Keep state for 60s so frontend can fetch result
            time.sleep(60)
            _optimization_state.pop(task_id, None)

    threading.Thread(target=_cleanup, daemon=True).start()
    return jsonify({'message': 'cancelling', 'task_id': task_id})


@api_backtest.route('/api/backtest/optimize/result/<task_id>')
def optimize_get_result(task_id):
    """取得優化最終（或當前最佳）結果"""
    state = _optimization_state.get(task_id)
    if not state:
        return jsonify({"error": "task not found"}), 404

    best = state.get('best_result')
    if not best:
        return jsonify({"error": "no results yet"}), 404

    return jsonify({
        'best_params': state.get('best_params'),
        'best_result': best,
        'all_results': state.get('all_results', []),
        'total_combinations': len(state.get('all_results', [])),
        'status': state.get('status'),
        'logs': state.get('logs', []),
        'optimizer': state.get('optimizer', ''),
        'wfo_enabled': state.get('wfo_enabled', False),
        'wfo_windows': state.get('wfo_windows', []),
        'pareto_front': state.get('pareto_front', []),
    })


# ============================================================
# Presets API
# ============================================================

@api_backtest.route('/api/presets', methods=['GET'])
def get_preset_params():
    """回傳所有策略的預設參數清單"""
    symbol = request.args.get('symbol', 'XAUUSDm')
    strategy = request.args.get('strategy')
    if strategy:
        presets = get_presets(symbol, strategy)
    else:
        presets = get_all_strategy_presets(symbol)

    return jsonify({
        'symbol': symbol,
        'strategy': strategy,
        'presets': presets,
        'risk_presets': get_risk_presets(),
    })
