# core/strategies/strategy_switcher.py
"""
🔄 Enhanced Strategy Switching Logic

This module implements the core logic for automatically switching between
strategy/instrument combinations based on performance scores and market conditions.

Features:
- Automatic strategy switching based on performance rankings
- Market condition-aware switching
- Performance threshold monitoring
- Switching cooldown periods
- Historical performance tracking
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import json
import os

from .market_condition_detector import get_market_condition
from .performance_scorer import calculate_strategy_score, rank_strategies
from ..backtesting.enhanced_engine import run_enhanced_backtest

logger = logging.getLogger(__name__)

class StrategySwitcher:
    """
    Automatic strategy switching system with enhanced market awareness
    """
    
    def __init__(self, config_file: str = 'strategy_switcher_config.json'):
        self.config_file = config_file
        self.config = self._load_config()
        self.performance_history = []
        self.last_switch_time = None
        self.current_strategy = None
        self.current_symbol = None
        self.current_score = 0.0
        self.switch_log = []
        
        # Enhanced configuration with market condition weighting
        self.config = {
            'switching_cooldown_hours': 0.5,  # Reduced from 24h to 30 minutes
            'performance_evaluation_period': 50,  # Reduced evaluation window
            'min_performance_score': 0.75,  # Increased threshold
            'switch_threshold': 0.2,  # Higher sensitivity
            'market_condition_weight': 0.4,  # Weight for market conditions
            'data_directory': 'lab/backtest_data',
            'monitored_instruments': ['XAUUSDm', 'BTCUSDm'],
            'test_strategies': [
                'INDEX_BREAKOUT_PRO', 'MA_CROSSOVER', 'RSI_CROSSOVER',
                'TURTLE_BREAKOUT', 'QUANTUMBOTX_HYBRID'
            ],
            'enable_dynamic_adjustment': True  # Enable dynamic parameter adjustment
        }

    def _load_config(self) -> dict:
        """Load configuration from file or use defaults"""
        default_config = {
            'switching_cooldown_hours': 0.5,
            'performance_evaluation_period': 50,
            'min_performance_score': 0.75,
            'switch_threshold': 0.2,
            'market_condition_weight': 0.4,
            'data_directory': 'lab/backtest_data',
            'monitored_instruments': ['XAUUSDm', 'BTCUSDm'],
            'test_strategies': [
                'INDEX_BREAKOUT_PRO', 'MA_CROSSOVER', 'RSI_CROSSOVER',
                'TURTLE_BREAKOUT', 'QUANTUMBOTX_HYBRID'
            ],
            'initial_capital': 100.0,
            'enable_spread_costs': True,
            'enable_slippage': True,
            'enable_realistic_execution': True,
            'enable_dynamic_adjustment': True
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                default_config.update(config)
        except Exception as e:
            logger.warning(f"Could not load config file {self.config_file}: {e}")
        
        return default_config

    def evaluate_and_switch(self, current_data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Evaluate all strategy/instrument combinations with enhanced market awareness"""
        try:
            # Check if we're in cooldown period
            if self._in_cooldown():
                logger.info("Strategy switcher in cooldown period")
                return None

            # Enhanced market condition analysis
            market_condition = get_market_condition(current_data)
            volatility = market_condition['volatility']
            trend_strength = market_condition['trend_strength']
            
            # Force re-evaluation during high volatility
            if volatility > 0.05:
                self.performance_history = []
                logger.info("Forced re-evaluation due to high volatility")

            # Enhanced scoring with market condition weighting
            performance_scores = {}
            for symbol, df in current_data.items():
                scores = calculate_strategy_score(df)
                performance_scores[symbol] = scores

            # Calculate weighted score
            best_symbol = max(performance_scores.keys(), key=lambda x: performance_scores[x]) if performance_scores else None
            weighted_score = (performance_scores[best_symbol] * 0.6 + 
                            trend_strength * 0.4) if best_symbol else 0

            # Enhanced switching condition with market awareness
            should_switch = False
            switch_reason = "Unknown"
            
            if weighted_score > self.current_score * (1 + self.config['switch_threshold']):
                should_switch = True
                switch_reason = f"Performance improvement: {weighted_score:.3f}"
            elif (volatility > 0.1 and performance_scores.get(best_symbol, 0) > self.current_score * 0.8):
                should_switch = True
                switch_reason = f"Market regime change with decent performance: {weighted_score:.3f}"
            
            if should_switch and self._can_switch():
                result = self._execute_switch(best_symbol, weighted_score, switch_reason, market_condition)
                if result:
                    logger.info(f"Strategy switched: {result}")
                    return result
            
            return None

        except Exception as e:
            logger.error(f"Error in strategy evaluation: {e}")
            return None

    def _can_switch(self) -> bool:
        """Check if we can switch strategies"""
        current_time = datetime.now()
        time_since_last_switch = (current_time - self.last_switch_time).total_seconds() / 3600
        
        # Respect cooldown period
        if time_since_last_switch < self.config['switching_cooldown_hours']:
            return False
            
        # Additional checks could be added here
        return True

    def _execute_switch(self, symbol: str, score: float, reason: str, market_condition: dict) -> bool:
        """Execute strategy switch and log it"""
        if not self.current_strategy:
            # First strategy selection
            self.current_strategy = self._select_default_strategy(symbol)
            self.current_score = score
            self.current_symbol = symbol
            return True

        # Check if switch is significant enough
        improvement = score - self.current_score
        if improvement <= self.config['switch_threshold']:
            return False
            
        # Execute switch
        old_strategy = self.current_strategy
        self.current_strategy = self._select_strategy(symbol)
        self.current_score = score
        self.current_symbol = symbol
        self.last_switch_time = datetime.now()
        
        # Log the switch
        self.switch_log.append({
            'time': datetime.now(),
            'from_strategy': old_strategy,
            'to_strategy': self.current_strategy,
            'score': score,
            'reason': reason,
            'volatility': market_condition.get('volatility', 0)
        })
        
        logger.info(f"Strategy switched from {old_strategy} to {self.current_strategy} ({reason})")
        return True

    def _select_strategy(self, symbol: str) -> str:
        """Select the best strategy for the given symbol"""
        # This is a simplified version - actual logic may be more complex
        strategies = self.config['test_strategies']
        # In a real implementation, we would evaluate each strategy
        # For now, we'll return a default based on symbol
        if 'BTC' in symbol or 'XAU' in symbol:
            return 'QUANTUMBOTX_HYBRID'
        return strategies[0] if strategies else 'MA_CROSSOVER'

    def _select_default_strategy(self, symbol: str) -> str:
        """Select default strategy for initial setup"""
        return self._select_strategy(symbol)

    def _in_cooldown(self) -> bool:
        """Check if we are in the cooldown period"""
        if not self.last_switch_time:
            return False
        current_time = datetime.now()
        time_since_last_switch = (current_time - self.last_switch_time).total_seconds() / 3600
        return time_since_last_switch < self.config['switching_cooldown_hours']

    def get_switch_history(self) -> List[Dict[str, Any]]:
        """Return the history of strategy switches"""
        return self.switch_log.copy()

    def clear_switch_history(self) -> None:
        """Clear the switch history"""
        self.switch_log.clear()