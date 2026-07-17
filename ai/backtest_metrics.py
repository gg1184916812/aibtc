"""
共用回测指标计算工具
统一的回测报告指标计算，所有回测入口共用
"""
import numpy as np
from typing import Dict, List, Any


def compute_backtest_metrics(
    trades: List[Dict[str, Any]],
    equity_curve: List[Dict[str, Any]],
    initial_capital: float,
    final_capital: float,
) -> Dict[str, Any]:
    """
    从交易记录和权益曲线计算所有回测指标

    Args:
        trades: 所有交易记录 [{'action': 'OPEN'/'CLOSE', 'price': ..., 'profit': ..., ...}]
        equity_curve: 权益曲线 [{'time': ..., 'capital': ...}]
        initial_capital: 初始资金
        final_capital: 最终资金

    Returns:
        dict: 完整指标体系
    """
    close_trades = [t for t in trades if t['action'] == 'CLOSE']
    total_trades = len(close_trades)
    winning_trades = [t for t in close_trades if t.get('profit', 0) > 0]
    losing_trades = [t for t in close_trades if t.get('profit', 0) < 0]
    win_count = len(winning_trades)
    lose_count = len(losing_trades)

    total_profit = sum(t.get('profit', 0) for t in close_trades)
    total_profit_percent = (final_capital - initial_capital) / initial_capital * 100

    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

    # Avg win / avg loss
    avg_win = np.mean([t['profit'] for t in winning_trades]) if win_count > 0 else 0
    avg_loss = np.mean([abs(t['profit']) for t in losing_trades]) if lose_count > 0 else 0
    profit_factor = (sum(t['profit'] for t in winning_trades) /
                     abs(sum(t['profit'] for t in losing_trades))) if lose_count > 0 and sum(t['profit'] for t in losing_trades) != 0 else float('inf')

    # Max drawdown (from equity curve)
    max_drawdown_pct = 0
    peak = initial_capital
    for point in equity_curve:
        equity = point.get('capital', point.get('equity', 0))
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd
    max_drawdown = round(max_drawdown_pct, 2)

    # Max consecutive wins/losses
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_wins = 0
    current_losses = 0
    for t in sorted(close_trades, key=lambda x: x.get('time', '')):
        if t.get('profit', 0) > 0:
            current_wins += 1
            current_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_wins)
        elif t.get('profit', 0) < 0:
            current_losses += 1
            current_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_losses)

    # Sharpe ratio (annualized, assuming daily returns)
    returns = []
    if len(equity_curve) > 1:
        for i in range(1, len(equity_curve)):
            prev = equity_curve[i - 1].get('capital', 0)
            curr = equity_curve[i].get('capital', 0)
            if prev > 0:
                returns.append((curr - prev) / prev)
    sharpe = 0.0
    if returns and np.std(returns) > 0:
        sharpe = round(np.mean(returns) / np.std(returns) * np.sqrt(252), 2)

    # Calmar ratio
    calmar = 0.0
    if max_drawdown > 0:
        calmar = round(total_profit_percent / max_drawdown, 2)

    # Average trade duration (bars)
    avg_bars = 0
    if total_trades > 0:
        bar_counts = [t.get('bars', 0) for t in close_trades]
        avg_bars = np.mean(bar_counts) if bar_counts else 0

    return {
        'total_trades': total_trades,
        'winning_trades': win_count,
        'losing_trades': lose_count,
        'win_rate': round(win_rate, 2),
        'total_profit': round(total_profit, 2),
        'total_profit_percent': round(total_profit_percent, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else None,
        'max_drawdown': max_drawdown,
        'max_consecutive_wins': max_consecutive_wins,
        'max_consecutive_losses': max_consecutive_losses,
        'sharpe_ratio': sharpe,
        'calmar_ratio': calmar,
        'avg_trade_bars': round(avg_bars, 1),
        'initial_capital': initial_capital,
        'final_capital': round(final_capital, 2),
    }
