# core/ai/decision_fusion.py
from core.ai.state_strategy_map import STATE_STRATEGY_MAP, LLM_BIAS_TO_STATE

def fuse_decisions(ml_result: dict, llm_result: dict, current_state: int = None) -> dict:
    ml_state = ml_result.get('state', 0)
    ml_conf = ml_result.get('confidence', 0.0)
    llm_bias = llm_result.get('bias', 'neutral')
    llm_risk_adj = llm_result.get('risk_adjustment', 1.0)
    llm_preferred = llm_result.get('preferred_strategy', None)

    # 决定最终状态
    if ml_conf > 0.75:
        final_state = ml_state
    elif ml_conf > 0.5:
        llm_state = LLM_BIAS_TO_STATE.get(llm_bias, ml_state)
        if llm_state == ml_state:
            final_state = ml_state
        else:
            if llm_bias == 'bearish' and ml_state == 1:
                final_state = 0
            elif llm_bias == 'bullish' and ml_state == 2:
                final_state = 0
            else:
                final_state = ml_state
    else:
        final_state = LLM_BIAS_TO_STATE.get(llm_bias, current_state if current_state is not None else 0)

    strategy_info = STATE_STRATEGY_MAP.get(final_state, STATE_STRATEGY_MAP[0])
    
    if llm_preferred:
        from core.strategies.strategy_map import resolve_strategy_class
        if resolve_strategy_class(llm_preferred):
            strategy_info['strategy'] = llm_preferred

    return {
        'state': final_state,
        'strategy': strategy_info.get('strategy', 'MA_CROSSOVER'),
        'params': strategy_info.get('params', {}),
        'risk_adj': llm_risk_adj
    }