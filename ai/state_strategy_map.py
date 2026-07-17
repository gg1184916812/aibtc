# core/ai/state_strategy_map.py
"""
市场状态 → 策略/参数 映射表
支持基于目标价的策略选择，并叠加 PerformanceScorer 的历史表现排名覆盖。

回测 (ai_backtester) 與實盤 (ai_trading_bot) 都透過統一的 select_strategy() 選策，
確保 回測 ≈ 實盤。
"""

# 状态到策略的映射（基础版，已扩大策略池）
STATE_STRATEGY_MAP = {
    0: {'strategy': 'BOLLINGER_REVERSION', 'params': {'bb_length': 20, 'bb_std': 2.0, 'trend_filter_period': 50}},
    1: {'strategy': 'TURTLE_BREAKOUT', 'params': {'entry_period': 20, 'exit_period': 10}},
    2: {'strategy': 'MA_CROSSOVER', 'params': {'fast_period': 10, 'slow_period': 30}},
    3: {'strategy': 'QUANTUM_VELOCITY', 'params': {'bb_length': 20, 'squeeze_window': 10, 'squeeze_factor': 0.7}},
}

# 各状态对应的候选策略池（用于表现排名时从中挑选，而非只用单一映射）
STATE_STRATEGY_CANDIDATES = {
    0: [  # 震荡
        'BOLLINGER_REVERSION', 'RSI_CROSSOVER', 'BOLLINGER_SQUEEZE',
        'PULSE_SYNC', 'MERCY_EDGE', 'SUPERTREND',
    ],
    1: [  # 多头
        'TURTLE_BREAKOUT', 'MA_CROSSOVER', 'QUANTUM_VELOCITY',
        'ICHIMOKU_CLOUD', 'SUPERTREND', 'DONCHIAN_BREAKOUT',
    ],
    2: [  # 空头
        'TURTLE_BREAKOUT', 'MA_CROSSOVER', 'QUANTUM_VELOCITY',
        'ICHIMOKU_CLOUD', 'DONCHIAN_BREAKOUT', 'DYNAMIC_BREAKOUT',
    ],
    3: [  # 突破
        'QUANTUM_VELOCITY', 'DYNAMIC_BREAKOUT', 'TURTLE_BREAKOUT',
        'VOLATILITY_BREAKOUT', 'DONCHIAN_BREAKOUT', 'INDEX_BREAKOUT_PRO',
    ],
}

# LLM bias -> 状态映射
LLM_BIAS_TO_STATE = {
    'bullish': 1,
    'bearish': 2,
    'neutral': 0,
}


def _base_selection(state: int, target_info: dict = None) -> dict:
    """根据状态/目标价返回基础策略选择（不含表现排名覆盖）"""
    if target_info and target_info.get('direction') != 'UNKNOWN':
        sel = select_strategy_by_target(
            target_info['target_price'],
            target_info['current_price'],
            target_info.get('target_time', 5),
            timeframe_minutes=5,
        )
        sel['source'] = 'target_based'
        return sel

    info = STATE_STRATEGY_MAP.get(state, STATE_STRATEGY_MAP[0])
    return {
        'strategy': info.get('strategy', 'BOLLINGER_REVERSION'),
        'params': info.get('params', {}),
        'expected_rr': '1:1.5',
        'reason': f'状态 {state} 默认映射',
        'source': 'state_mapping',
    }


def select_strategy(state: int, target_info: dict = None,
                    symbol: str = 'XAUUSDm', timeframe: str = 'M5') -> dict:
    """
    统一策略选择入口（回测與實盤共用）。

    1) 先用 状态/目标价 選出基礎策略
    2) 再用 PerformanceScorer 查 DB 中該 symbol+state 近期表現，
       若候选池中有明顯更優者則覆蓋（表現排名驅動的自動換策）
    """
    print(f"[DEBUG select_strategy] State: {state}, Target Info: {target_info}, Symbol: {symbol}, Timeframe: {timeframe}")
    base = _base_selection(state, target_info)
    print(f"[DEBUG select_strategy] Base selection: {base}")

    try:
        from core.strategies.performance_scorer import performance_scorer
        candidates = STATE_STRATEGY_CANDIDATES.get(state, [base['strategy']])
        if base['strategy'] not in candidates:
            candidates = candidates + [base['strategy']]

        best = None
        best_score = -1.0
        for strat in candidates:
            res = _query_recent_backtest(symbol, state, strat)
            if not res:
                continue
            score = performance_scorer.calculate_performance_score(
                res, {'market_condition': 'both', 'instrument_type': _instrument_type(symbol)}, strat, symbol
            )
            if score['composite_score'] > best_score:
                best_score = score['composite_score']
                best = (strat, res)

        # 仅当表现明显更优（差距 > 0.1）时才覆盖基础选择，避免抖动
        if best and best[0] != base['strategy'] and best_score > 0.6:
            res = best[1]
            base = {
                'strategy': best[0],
                'params': res.get('params', {}),
                'expected_rr': 'rank-based',
                'reason': f"表现排名覆盖 (composite={best_score:.2f})",
                'source': 'performance_rank',
            }
    except Exception:
        # 表现排名失败不影響基礎選擇
        pass

    return base


def _instrument_type(symbol: str) -> str:
    s = (symbol or '').upper()
    if 'XAU' in s or 'GOLD' in s:
        return 'GOLD'
    if 'BTC' in s or 'ETH' in s or 'CRYPTO' in s:
        return 'CRYPTO'
    if any(k in s for k in ['US30', 'NAS', 'SPX', 'DJI', 'INDEX']):
        return 'INDICES'
    return 'FOREX'


def _query_recent_backtest(symbol: str, state: int, strategy: str) -> dict:
    """从 bots.db 的 backtest_results 查近期该 symbol+state+strategy 的最佳结果"""
    import os
    import sqlite3
    import json
    db_path = "bots.db"
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='backtest_results'")
        if not cur.fetchone():
            conn.close()
            return None
        pattern = f'%"{symbol}"%"{state}"%'
        cur.execute(
            """SELECT strategy_name, parameters, total_profit_usd, win_rate_percent,
                      total_trades, max_drawdown_percent
               FROM backtest_results
               WHERE strategy_name = ? AND parameters LIKE ?
               ORDER BY total_profit_usd DESC LIMIT 1""",
            (strategy, pattern),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            params = json.loads(row['parameters']) if row['parameters'] else {}
            return {
                'total_profit_usd': row['total_profit_usd'] or 0,
                'net_profit_after_costs': row['total_profit_usd'] or 0,
                'win_rate_percent': row['win_rate_percent'] or 0,
                'total_trades': row['total_trades'] or 0,
                'wins': int((row['win_rate_percent'] or 0) / 100.0 * (row['total_trades'] or 0)),
                'losses': (row['total_trades'] or 0) - int((row['win_rate_percent'] or 0) / 100.0 * (row['total_trades'] or 0)),
                'max_drawdown_percent': row['max_drawdown_percent'] or 0,
                'params': params.get('params', {}),
            }
        return None
    except Exception:
        return None


def get_strategy_for_state_and_target(state: int, target_info: dict) -> dict:
    """兼容旧调用：状态+目标价组合选择"""
    return select_strategy(state, target_info)


def select_strategy_by_target(target_price: float, current_price: float, target_time: int, timeframe_minutes: int = 5):
    """
    根据目标价和时间选择策略（核心函数，已扩大策略池）
    """
    movement_pct = (target_price - current_price) / current_price * 100
    expected_duration = target_time * timeframe_minutes  # 分钟

    # ====== 策略选择逻辑 ======

    # 大涨预期 (> 1.5%)
    if movement_pct > 1.5:
        if expected_duration < 30:  # 30 分钟内到达
            return {
                'strategy': 'TURTLE_BREAKOUT',
                'params': {'entry_period': 10, 'exit_period': 5},
                'expected_rr': '1:2',
                'reason': f'短期大涨预期 (目标 {movement_pct:.2f}%, {expected_duration}分钟)'
            }
        else:  # 较长时间到达
            return {
                'strategy': 'QUANTUM_VELOCITY',
                'params': {'bb_length': 20, 'squeeze_window': 10, 'squeeze_factor': 0.7},
                'expected_rr': '1:3',
                'reason': f'中期趋势预期 (目标 {movement_pct:.2f}%, {expected_duration}分钟)'
            }

    # 大跌预期 (< -1.5%)
    elif movement_pct < -1.5:
        if expected_duration < 30:
            return {
                'strategy': 'MA_CROSSOVER',
                'params': {'fast_period': 5, 'slow_period': 15},
                'expected_rr': '1:2',
                'reason': f'短期大跌预期 (目标 {movement_pct:.2f}%, {expected_duration}分钟)'
            }
        else:
            return {
                'strategy': 'DYNAMIC_BREAKOUT',
                'params': {'donchian_period': 15, 'ema_filter_period': 30},
                'expected_rr': '1:2.5',
                'reason': f'中期下跌预期 (目标 {movement_pct:.2f}%, {expected_duration}分钟)'
            }

    # 震荡预期 (|movement_pct| < 0.5%)
    elif abs(movement_pct) < 0.5:
        return {
            'strategy': 'BOLLINGER_REVERSION',
            'params': {'bb_length': 20, 'bb_std': 2.0, 'trend_filter_period': 50},
            'expected_rr': '1:1.5',
            'reason': f'震荡预期 (波动 {movement_pct:.2f}%)'
        }

    # 小幅波动
    else:
        return {
            'strategy': 'RSI_CROSSOVER',
            'params': {'rsi_period': 14, 'rsi_ma_period': 7, 'trend_filter_period': 30},
            'expected_rr': '1:1.5',
            'reason': f'小幅波动 (目标 {movement_pct:.2f}%)'
        }
