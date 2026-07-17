# core/ai/dynamic_strategy_recommender.py
"""
动态策略推荐器 - B方案
基于历史回测结果，为每个市场状态推荐最优策略
"""

import os
import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DynamicStrategyRecommender:
    def __init__(self, db_path: str = "bots.db"):
        self.db_path = db_path
        self.cache = {}
        self.last_cache_time = None
        self.cache_expiry = 1800  # 30分钟过期

    def get_best_strategy(self, symbol: str, state: int, timeframe: str = "H1") -> Dict[str, Any]:
        """
        根据历史回测结果，推荐该状态下表现最好的策略
        
        Args:
            symbol: 交易品种 (如 BTCUSDm)
            state: 市场状态 (0=震荡, 1=多头, 2=空头, 3=突破)
            timeframe: 时间周期
        
        Returns:
            dict: {
                strategy: 策略名,
                params: 参数,
                win_rate: 胜率,
                total_profit: 净利润,
                total_trades: 交易次数,
                max_drawdown: 最大回撤,
                source: 来源 (backtest_history / default_mapping)
            }
        """
        cache_key = f"{symbol}_{state}_{timeframe}"
        
        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # 尝试从数据库查询
        result = self._query_backtest_results(symbol, state, timeframe)
        
        if result:
            self._update_cache(cache_key, result)
            return result
        
        # 没有历史数据，使用默认映射
        default = self._get_default_strategy(state)
        default['source'] = 'default_mapping'
        self._update_cache(cache_key, default)
        return default

    def _query_backtest_results(self, symbol: str, state: int, timeframe: str) -> Optional[Dict[str, Any]]:
        """从数据库查询历史回测结果"""
        try:
            # 检查数据库文件是否存在
            if not os.path.exists(self.db_path):
                logger.warning(f"Database {self.db_path} not found")
                return None
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='backtest_results'")
            if not cursor.fetchone():
                conn.close()
                return None
            
            # 查询包含该品种和状态的记录
            # 注意：parameters 字段存储了 JSON，包含 instrument 和 state 信息
            query = """
                SELECT 
                    strategy_name,
                    parameters,
                    total_profit_usd,
                    win_rate_percent,
                    total_trades,
                    max_drawdown_percent
                FROM backtest_results 
                WHERE parameters LIKE ? 
                ORDER BY total_profit_usd DESC
                LIMIT 1
            """
            
            # 搜索包含该品种和状态的记录
            search_pattern = f'%"{symbol}"%"{state}"%'
            cursor.execute(query, (search_pattern,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                params = json.loads(row['parameters']) if row['parameters'] else {}
                return {
                    'strategy': row['strategy_name'],
                    'params': params.get('params', {}),
                    'win_rate': row['win_rate_percent'],
                    'total_profit': row['total_profit_usd'],
                    'total_trades': row['total_trades'],
                    'max_drawdown': row['max_drawdown_percent'],
                    'source': 'backtest_history'
                }
            return None
            
        except Exception as e:
            logger.error(f"查询回测结果失败: {e}")
            return None

    def _get_default_strategy(self, state: int) -> Dict[str, Any]:
        """备用：使用硬编码映射"""
        from core.ai.state_strategy_map import STATE_STRATEGY_MAP
        info = STATE_STRATEGY_MAP.get(state, {})
        return {
            'strategy': info.get('strategy', 'BOLLINGER_REVERSION'),
            'params': info.get('params', {}),
            'win_rate': None,
            'total_profit': None,
            'total_trades': None,
            'max_drawdown': None,
            'source': 'default_mapping'
        }

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        if self.last_cache_time is None:
            return False
        return (datetime.now() - self.last_cache_time).seconds < self.cache_expiry

    def _update_cache(self, key: str, value: dict):
        self.cache[key] = value
        self.last_cache_time = datetime.now()


# ====== 全局实例 ======
recommender = DynamicStrategyRecommender()


def get_recommended_strategy(symbol: str, state: int, timeframe: str = "H1") -> Dict[str, Any]:
    """便捷函数"""
    return recommender.get_best_strategy(symbol, state, timeframe)