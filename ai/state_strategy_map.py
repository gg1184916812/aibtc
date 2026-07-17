# core/ai/state_strategy_map.py
"""
市场状态 → 策略/参数 映射表
支持基于目标价的策略选择
"""

# 状态到策略的映射（基础版）
STATE_STRATEGY_MAP = {
    0: {'strategy': 'BOLLINGER_REVERSION', 'params': {'bb_length': 20, 'bb_std': 2.0, 'trend_filter_period': 50}},
    1: {'strategy': 'TURTLE_BREAKOUT', 'params': {'entry_period': 20, 'exit_period': 10}},
    2: {'strategy': 'MA_CROSSOVER', 'params': {'fast_period': 10, 'slow_period': 30}},
    3: {'strategy': 'QUANTUM_VELOCITY', 'params': {'bb_length': 20, 'squeeze_window': 10, 'squeeze_factor': 0.7}},
}

# LLM bias -> 状态映射
LLM_BIAS_TO_STATE = {
    'bullish': 1,
    'bearish': 2,
    'neutral': 0
}


def select_strategy_by_target(target_price: float, current_price: float, target_time: int, timeframe_minutes: int = 5):
    """
    根据目标价和时间选择策略（核心函数）
    
    Args:
        target_price: 目标价
        current_price: 当前价
        target_time: 目标时间（根数）
        timeframe_minutes: 每根 K 线的分钟数
    
    Returns:
        dict: {strategy, params, expected_rr, reason}
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


def get_strategy_for_state_and_target(state: int, target_info: dict) -> dict:
    """
    结合市场状态和目标价选择策略
    
    Args:
        state: 市场状态 (0-3)
        target_info: 目标信息 {target_price, current_price, target_time, direction}
    """
    # 如果有目标信息，优先使用目标价匹配
    if target_info and target_info.get('direction') != 'UNKNOWN':
        return select_strategy_by_target(
            target_info['target_price'],
            target_info['current_price'],
            target_info.get('target_time', 5),
            timeframe_minutes=5
        )
    
    # 否则使用状态映射
    return STATE_STRATEGY_MAP.get(state, STATE_STRATEGY_MAP[0])