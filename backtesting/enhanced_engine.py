# core/backtesting/enhanced_engine.py
# Enhanced Backtesting Engine with ATR-based Risk Management and Vectorized Spread Modeling

import math
import logging
import os
import numpy as np
from core.strategies.strategy_map import resolve_strategy_class

logger = logging.getLogger(__name__)
backtest_log_level = os.getenv('BACKTEST_LOG_LEVEL', 'INFO')
if backtest_log_level == 'DEBUG':
    logger.setLevel(logging.DEBUG)
else:
    logger.disabled = True
    logger.propagate = False


class InstrumentConfig:
    """Fallback configuration when MT5 contract info is unavailable"""

    FOREX_MAJOR = {
        'contract_size': 100000,
        'pip_size': 0.0001,
        'typical_spread_pips': 1.0,
        'max_risk_percent': 2.0,
        'max_lot_size': 10.0,
        'slippage_pips': 0.2,
        'max_sl_pips': 50.0,
        'max_tp_pips': 150.0,
    }

    FOREX_JPY = {
        'contract_size': 100000,
        'pip_size': 0.01,
        'typical_spread_pips': 1.5,
        'max_risk_percent': 2.0,
        'max_lot_size': 10.0,
        'slippage_pips': 0.3,
        'max_sl_pips': 70.0,
        'max_tp_pips': 210.0,
    }

    GOLD = {
        'contract_size': 100,
        'pip_size': 0.01,
        'typical_spread_pips': 8.0,
        'max_risk_percent': 1.0,
        'max_lot_size': 0.10,
        'slippage_pips': 1.0,
        'atr_volatility_threshold_high': 20.0,
        'atr_volatility_threshold_extreme': 30.0,
        'emergency_brake_percent': 0.05,
        'max_sl_pips': 100.0,
        'max_tp_pips': 300.0,
    }

    CRYPTO = {
        'contract_size': 1,
        'pip_size': 0.01,
        'typical_spread_pips': 2.0,
        'max_risk_percent': 1.5,
        'max_lot_size': 1.0,
        'slippage_pips': 0.5,
        'max_sl_pips': 500.0,
        'max_tp_pips': 1500.0,
    }

    INDICES = {
        'contract_size': 1,
        'pip_size': 0.01,
        'typical_spread_pips': 3.0,
        'max_risk_percent': 0.5,
        'max_lot_size': 0.1,
        'slippage_pips': 0.5,
        'atr_volatility_threshold_high': 50.0,
        'atr_volatility_threshold_extreme': 100.0,
        'emergency_brake_percent': 0.1,
        'max_sl_pips': 150.0,
        'max_tp_pips': 450.0,
    }

    @classmethod
    def get_config(cls, symbol_name):
        symbol_upper = symbol_name.upper()
        if any(index in symbol_upper for index in ['US30', 'US100', 'US500', 'DE30', 'UK100', 'JP225', 'NAS100', 'SPX500']):
            return cls.INDICES
        elif 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
            return cls.GOLD
        elif any(jpy in symbol_upper for jpy in ['JPY', 'USDJPY', 'EURJPY', 'GBPJPY']):
            return cls.FOREX_JPY
        elif any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'CRYPTO']):
            return cls.CRYPTO
        else:
            return cls.FOREX_MAJOR


def _build_runtime_config(engine_config, instrument_symbol, enable_spread, enable_slippage):
    """Build runtime configuration from MT5 contract info (preferred) or fallback."""
    mt5_contract = engine_config.get('mt5_contract_info') if engine_config else None

    if mt5_contract:
        spread_pips = mt5_contract['spread_pips']
        pip_size = mt5_contract['pip_size']
        contract_size = mt5_contract['contract_size']
        digits = mt5_contract.get('digits', 2)
        slippage_pips = spread_pips * 0.5

        if 'XAU' in instrument_symbol.upper() or 'GOLD' in instrument_symbol.upper():
            max_risk_percent = 1.0
            max_lot_size = 0.10
            emergency_brake_percent = 0.05
            atr_threshold_high = 20.0
            atr_threshold_extreme = 30.0
            max_sl_pips = 100.0 # 黄金的最大止损点数
            max_tp_pips = 200.0 # 黄金的最大止盈点数
        elif 'BTC' in instrument_symbol.upper():
            max_risk_percent = 1.5
            max_lot_size = 1.0
            emergency_brake_percent = 0.08
            atr_threshold_high = None
            atr_threshold_extreme = None
            max_sl_pips = 500.0 # BTC的最大止损点数
            max_tp_pips = 1000.0 # BTC的最大止盈点数
        else:
            max_risk_percent = 2.0
            max_lot_size = 10.0
            emergency_brake_percent = None
            atr_threshold_high = None
            atr_threshold_extreme = None
            max_sl_pips = 50.0 # 普通品种的最大止损点数
            max_tp_pips = 150.0 # 普通品种的最大止盈点数

        is_gold = 'XAU' in instrument_symbol.upper() or 'GOLD' in instrument_symbol.upper()
        is_btc = 'BTC' in instrument_symbol.upper()
    else:
        fallback_config = InstrumentConfig.get_config(instrument_symbol)
        spread_pips = fallback_config['typical_spread_pips']
        pip_size = fallback_config['pip_size']
        contract_size = fallback_config['contract_size']
        slippage_pips = fallback_config.get('slippage_pips', 0.5)
        max_risk_percent = fallback_config['max_risk_percent']
        max_lot_size = fallback_config['max_lot_size']
        emergency_brake_percent = fallback_config.get('emergency_brake_percent', None)
        atr_threshold_high = fallback_config.get('atr_volatility_threshold_high', None)
        atr_threshold_extreme = fallback_config.get('atr_volatility_threshold_extreme', None)
        is_gold = fallback_config == InstrumentConfig.GOLD
        is_btc = fallback_config == InstrumentConfig.CRYPTO
        max_sl_pips = fallback_config.get('max_sl_pips', None)
        max_tp_pips = fallback_config.get('max_tp_pips', None)

    slippage_pips = slippage_pips if enable_slippage else 0

    return {
        'spread_pips': spread_pips,
        'pip_size': pip_size,
        'contract_size': contract_size,
        'slippage_pips': slippage_pips,
        'max_risk_percent': max_risk_percent,
        'max_lot_size': max_lot_size,
        'emergency_brake_percent': emergency_brake_percent,
        'atr_threshold_high': atr_threshold_high,
        'atr_threshold_extreme': atr_threshold_extreme,
        'is_gold': is_gold,
        'is_btc': is_btc,
        'enable_spread': enable_spread,
        'enable_slippage': enable_slippage,
        'instrument_symbol': instrument_symbol, # Add instrument symbol to cfg
        'max_sl_pips': max_sl_pips,
        'max_tp_pips': max_tp_pips,
    }


def _calculate_position_size(capital, risk_percent, sl_distance, atr_value, cfg):
    """Position sizing with instrument-specific rules."""
    # 确保风险百分比不超过配置的最大值
    risk_percent = min(risk_percent, cfg['max_risk_percent'])
    amount_to_risk = capital * (risk_percent / 100.0)

    calculated_lot = 0
    if sl_distance <= 0:
        return 0 # 如果止损距离为0，则无法计算风险，不交易

    risk_per_unit = sl_distance * cfg['contract_size']

    # 处理黄金的特殊仓位计算逻辑
    if cfg['is_gold']:
        if risk_percent <= 0.5:
            base_lot = 0.01
        elif risk_percent <= 1.0:
            base_lot = 0.02
        else:
            base_lot = 0.03

        atr_high = cfg['atr_threshold_high']
        atr_extreme = cfg['atr_threshold_extreme']
        if atr_extreme and atr_value > atr_extreme:
            calculated_lot = 0.01
            logger.warning(f"GOLD EXTREME VOLATILITY ({cfg['instrument_symbol']}): ATR={atr_value:.1f}, lot=0.01")
        elif atr_high and atr_value > atr_high:
            calculated_lot = max(0.01, base_lot * 0.5)
            logger.warning(f"GOLD HIGH VOLATILITY ({cfg['instrument_symbol']}): ATR={atr_value:.1f}, lot={calculated_lot}")
        else:
            calculated_lot = base_lot

    # 处理加密货币的特殊仓位计算逻辑
    elif cfg['is_btc']:
        # BTC的base_lot现在是根据风险百分比和ATR计算的上限
        if risk_percent <= 0.5:
            base_lot_limit = 0.01
        elif risk_percent <= 1.0:
            base_lot_limit = 0.05
        elif risk_percent <= 1.5:
            base_lot_limit = 0.10
        else:
            base_lot_limit = 0.20
        
        calculated_lot = amount_to_risk / risk_per_unit
        # BTC的仓位也要受限于base_lot_limit
        calculated_lot = min(calculated_lot, base_lot_limit)

    # 普通交易品种的仓位计算
    else: 
        calculated_lot = amount_to_risk / risk_per_unit

    # 应用最大手数限制
    lot = min(calculated_lot, cfg['max_lot_size'])

    # 针对小资金账户，处理最小手数0.01的风险问题
    if lot < 0.01 and lot > 0: # 如果计算出的手数小于0.01，但不是0
        # 尝试使用最小手数0.01
        test_lot = 0.01
        # 估算使用0.01手时的实际风险金额
        actual_risk_in_currency_with_min_lot = test_lot * sl_distance * cfg['contract_size']
        # 计算使用0.01手时的实际风险百分比
        actual_risk_percent_with_min_lot = (actual_risk_in_currency_with_min_lot / capital) * 100
        
        # 如果实际风险百分比远超我们最初设定的风险百分比（例如，超过150%），则跳过交易
        if actual_risk_percent_with_min_lot > (risk_percent * 1.5):
            logger.warning(
                f"SKIP TRADE ({cfg['instrument_symbol']}): Calculated lot {lot:.4f} too small. "
                f"Min lot 0.01 would risk {actual_risk_percent_with_min_lot:.2f}% of capital, "
                f"exceeding desired {risk_percent:.2f}% by too much. Capital: ${capital:.2f}"
            )
            return 0 # 返回0表示不交易
        else:
            lot = test_lot # 否则，接受最小手数

    elif lot <= 0: # 如果计算出的手数为0或负数，直接返回0
        return 0
    
    return round(lot, 2)


def _entry_price(signal, close, spread_pips, pip_size, slippage_pips, enabled):
    """Calculate realistic entry price with spread and slippage."""
    half_spread = (spread_pips * pip_size) / 2
    slip = slippage_pips * pip_size if enabled else 0
    if signal == 'BUY':
        return close + half_spread + slip
    else:
        return close - half_spread - slip


def _exit_price(position, target, spread_pips, pip_size, slippage_pips, enabled):
    """Calculate realistic exit price with spread and slippage."""
    half_spread = (spread_pips * pip_size) / 2
    slip = slippage_pips * pip_size if enabled else 0
    if position == 'BUY':
        return target - half_spread - slip
    else:
        return target + half_spread + slip


def _find_exit_bar(signal, idx, sl_price, tp_price, lows, highs):
    """Vectorized exit bar detection. Returns (exit_idx, exit_reason) or (end_idx, 'EOD')."""
    n = len(lows)
    if idx + 1 >= n:
        return n - 1, 'EOD'

    remaining = np.arange(idx + 1, n)

    if signal == 'BUY':
        sl_hit = np.where(lows[remaining] <= sl_price)[0]
        tp_hit = np.where(highs[remaining] >= tp_price)[0]
    else:
        sl_hit = np.where(highs[remaining] >= sl_price)[0]
        tp_hit = np.where(lows[remaining] <= tp_price)[0]

    sl_first = sl_hit[0] if len(sl_hit) > 0 else None
    tp_first = tp_hit[0] if len(tp_hit) > 0 else None

    if sl_first is not None and tp_first is not None:
        if sl_first <= tp_first:
            return int(idx + 1 + sl_first), 'Stop Loss'
        else:
            return int(idx + 1 + tp_first), 'Take Profit'
    elif sl_first is not None:
        return int(idx + 1 + sl_first), 'Stop Loss'
    elif tp_first is not None:
        return int(idx + 1 + tp_first), 'Take Profit'
    else:
        return n - 1, 'EOD'


def run_enhanced_backtest(strategy_id, params, historical_data_df, symbol_name=None, engine_config=None):
    """
    Run vectorized enhanced backtesting with MT5 contract info support.

    Args:
        strategy_id: Strategy identifier
        params: Strategy parameters dict
        historical_data_df: OHLCV DataFrame with DatetimeIndex
        symbol_name: Instrument symbol (e.g. XAUUSDm)
        engine_config: {
            enable_spread_costs: bool,
            enable_slippage: bool,
            enable_realistic_execution: bool,
            mt5_contract_info: {spread, digits, contract_size, point, pip_size, spread_pips}
        }
    """
    engine_config = engine_config or {}
    enable_spread = engine_config.get('enable_spread_costs', True)
    enable_slippage = engine_config.get('enable_slippage', True)

    strategy_class = resolve_strategy_class(strategy_id)
    if not strategy_class:
        return {"error": "Strategy not found"}

    if symbol_name:
        instrument_symbol = symbol_name
    elif isinstance(historical_data_df.index, type(None)):
        instrument_symbol = "UNKNOWN"
    else:
        instrument_symbol = historical_data_df.columns[0].split('_')[0] if '_' in historical_data_df.columns[0] else "UNKNOWN"

    cfg = _build_runtime_config(engine_config, instrument_symbol, enable_spread, enable_slippage)

    class MockBot:
        def __init__(self):
            self.market_for_mt5 = instrument_symbol
            self.timeframe = "H1"
            self.tf_map = {}

    strategy_instance = strategy_class(bot_instance=MockBot(), params=params)
    df = historical_data_df.copy()
    df_with_signals = strategy_instance.analyze_df(df)
    df_with_signals.ta.atr(length=14, append=True)
    df_with_signals.dropna(inplace=True)
    df_with_signals.reset_index(inplace=True)

    if df_with_signals.empty:
        return {"error": "Insufficient data for analysis"}

    risk_percent = float(params.get('risk_percent', params.get('lot_size', 1.0)))
    sl_atr_multiplier = float(params.get('sl_atr_multiplier', params.get('sl_pips', 2.0)))
    tp_atr_multiplier = float(params.get('tp_atr_multiplier', params.get('tp_pips', 4.0)))

    # 移除黄金的硬性 ATR 乘数限制，现在通过 max_sl_pips 和 max_tp_pips 进行控制
    # if cfg['is_gold']:
    #     risk_percent = min(risk_percent, 1.0)
    #     sl_atr_multiplier = min(sl_atr_multiplier, 1.0)
    #     tp_atr_multiplier = min(tp_atr_multiplier, 2.0)

    signals = df_with_signals['signal'].values
    lows = df_with_signals['low'].values
    highs = df_with_signals['high'].values
    closes = df_with_signals['close'].values
    atrs = df_with_signals['ATRr_14'].values
    times = df_with_signals['time'].values

    entry_mask = ((signals == 'BUY') | (signals == 'SELL')) & (atrs > 0)
    entry_indices = np.where(entry_mask)[0]

    trades = []
    initial_capital = float(engine_config.get('initial_capital', 10000.0))
    capital = initial_capital
    equity_curve = [initial_capital]
    peak_equity = initial_capital
    max_drawdown = 0.0
    total_spread_costs = 0.0
    last_exit_idx = -1
    stop_out_triggered = False

    for entry_cursor in range(len(entry_indices)):
        idx = int(entry_indices[entry_cursor])

        if idx <= last_exit_idx:
            continue
        if capital <= 0:
            break

        signal = signals[idx]
        atr_value = atrs[idx]

        sl_distance = atr_value * sl_atr_multiplier
        tp_distance = atr_value * tp_atr_multiplier

        # 应用 max_sl_pips 和 max_tp_pips 限制
        if cfg['max_sl_pips'] is not None:
            max_sl_distance = cfg['max_sl_pips'] * cfg['pip_size']
            sl_distance = min(sl_distance, max_sl_distance)
        if cfg['max_tp_pips'] is not None:
            max_tp_distance = cfg['max_tp_pips'] * cfg['pip_size']
            tp_distance = min(tp_distance, max_tp_distance)

        lot_size = _calculate_position_size(capital, risk_percent, sl_distance, atr_value, cfg)
        if lot_size <= 0:
            continue

        emergency = cfg['emergency_brake_percent']
        if emergency:
            estimated_risk = sl_distance * lot_size * cfg['contract_size']
            max_risk_dollar = capital * emergency
            if estimated_risk > max_risk_dollar:
                logger.warning(f"EMERGENCY BRAKE: Risk ${estimated_risk:.0f} > ${max_risk_dollar:.0f}, trade SKIPPED")
                continue

        spread_pips = cfg['spread_pips']
        pip_size = cfg['pip_size']
        slippage_pips = cfg['slippage_pips']

        entry_price_val = _entry_price(signal, closes[idx], spread_pips, pip_size, slippage_pips, enable_slippage)

        if signal == 'BUY':
            sl_price = entry_price_val - sl_distance
            tp_price = entry_price_val + tp_distance
        else:
            sl_price = entry_price_val + sl_distance
            tp_price = entry_price_val - tp_distance

        entry_time = times[idx]

        exit_idx, exit_reason = _find_exit_bar(signal, idx, sl_price, tp_price, lows, highs)

        if exit_reason in ('Stop Loss', 'Take Profit'):
            if exit_reason == 'Stop Loss':
                target_price = sl_price
            else:
                target_price = tp_price
            exit_price_val = _exit_price(signal, target_price, spread_pips, pip_size, slippage_pips, enable_slippage)
        else:
            exit_price_val = _exit_price(signal, closes[exit_idx], spread_pips, pip_size, slippage_pips, enable_slippage)

        profit_multiplier = lot_size * cfg['contract_size']
        if signal == 'BUY':
            profit = (exit_price_val - entry_price_val) * profit_multiplier
        else:
            profit = (entry_price_val - exit_price_val) * profit_multiplier

        spread_cost = spread_pips * pip_size * cfg['contract_size'] * lot_size
        profit -= spread_cost
        total_spread_costs += spread_cost

        if not math.isfinite(profit):
            profit = 0.0

        capital += profit
        if capital <= 0:
            capital = 0.0
            stop_out_triggered = True

        trades.append({
            'entry_time': str(entry_time),
            'exit_time': str(times[exit_idx]),
            'entry': round(entry_price_val, 5),
            'exit': round(exit_price_val, 5),
            'profit': round(profit, 2),
            'spread_cost': round(spread_cost, 2),
            'reason': exit_reason,
            'position_type': signal,
            'lot_size': lot_size,
        })

        equity_curve.append(max(0.0, capital))
        peak_equity = max(peak_equity, capital)
        drawdown = (peak_equity - capital) / peak_equity if peak_equity > 0 else 0
        max_drawdown = min(1.0, max(max_drawdown, drawdown))

        last_exit_idx = exit_idx

        logger.debug(
            f"Trade: {signal} | Entry={entry_price_val:.4f} | "
            f"Exit={exit_price_val:.4f} | Profit=${profit:.2f} | "
            f"Spread=${spread_cost:.2f} | Reason={exit_reason}"
        )

        if stop_out_triggered:
            logger.warning("Backtest stop-out triggered: capital reached zero.")
            break

    total_profit = capital - initial_capital
    wins = len([t for t in trades if t['profit'] > 0])
    losses = len(trades) - wins
    win_rate = (wins / len(trades) * 100) if trades else 0

    capital_clean = max(0.0, capital)
    total_profit_clean = capital_clean - initial_capital
    final_capital = round(capital_clean, 2) if math.isfinite(capital_clean) else initial_capital
    total_profit_usd = round(total_profit_clean, 2) if math.isfinite(total_profit_clean) else 0.0
    max_dd_pct = round(max_drawdown * 100, 2) if math.isfinite(max_drawdown) else 0.0
    win_rate_pct = round(win_rate, 2) if math.isfinite(win_rate) else 0.0
    total_spread = round(total_spread_costs, 2)

    logger.info(
        f"Backtest Complete: {len(trades)} trades, "
        f"net ${total_profit_usd:+.0f}, {win_rate_pct:.0f}% win rate, "
        f"${total_spread:.0f} spread costs"
    )

    return {
        "strategy_name": strategy_class.name,
        "instrument": instrument_symbol,
        "total_trades": len(trades),
        "final_capital": final_capital,
        "gross_profit_usd": round(total_profit_usd + total_spread, 2),
        "total_profit_usd": total_profit_usd,
        "total_spread_costs": total_spread,
        "net_profit_after_costs": total_profit_usd,
        "win_rate_percent": win_rate_pct,
        "wins": wins,
        "losses": losses,
        "max_drawdown_percent": max_dd_pct,
        "equity_curve": equity_curve,
        "trades": trades[-20:],
        "initial_capital": initial_capital, # Add initial capital here
        "engine_config": {
            "spread_costs_enabled": enable_spread,
            "slippage_enabled": enable_slippage,
            "realistic_execution": engine_config.get('enable_realistic_execution', True),
            "instrument_config": {
                "max_risk_percent": cfg['max_risk_percent'],
                "typical_spread_pips": cfg['spread_pips'],
                "max_lot_size": cfg['max_lot_size'],
            },
            "mt5_contract": {
                "spread_pips": cfg['spread_pips'],
                "pip_size": cfg['pip_size'],
                "contract_size": cfg['contract_size'],
                "slippage_pips": cfg['slippage_pips'],
            },
        },
    }


def run_backtest(strategy_id, params, historical_data_df, symbol_name=None, engine_config=None):
    """Backward compatible wrapper."""
    return run_enhanced_backtest(strategy_id, params, historical_data_df, symbol_name, engine_config)