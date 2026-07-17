# core/config.py
"""
Centralized configuration management for QuantumBotX
Provides a single source of truth for all configurable parameters
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class AIConfig:
    """AI/ML Model Configuration"""
    
    # Training parameters
    N_ESTIMATORS = int(os.getenv('AI_N_ESTIMATORS', 300))
    MAX_DEPTH = int(os.getenv('AI_MAX_DEPTH', 6))
    LEARNING_RATE = float(os.getenv('AI_LEARNING_RATE', 0.05))
    EARLY_STOPPING_ROUNDS = int(os.getenv('AI_EARLY_STOPPING_ROUNDS', 30))
    
    # Label generation
    LABEL_RET_THRESHOLD = float(os.getenv('AI_LABEL_RET_THRESHOLD', 0.005))  # 0.5%
    LABEL_VOL_THRESHOLD = float(os.getenv('AI_LABEL_VOL_THRESHOLD', 0.015))  # 1.5%
    FORWARD_BARS = int(os.getenv('AI_FORWARD_BARS', 10))
    
    # Backtesting
    CONFIDENCE_THRESHOLD = float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.60))
    PREDICTION_INTERVAL = int(os.getenv('AI_PREDICTION_INTERVAL', 10))
    MIN_CONFIDENCE_WARNING = float(os.getenv('AI_MIN_CONFIDENCE_WARNING', 0.30))
    
    # Model paths
    MODEL_DIR = os.getenv('AI_MODEL_DIR', 'ai_models')
    DEFAULT_MODEL_NAME = os.getenv('AI_DEFAULT_MODEL', 'market_predictor.pkl')
    
    # Feature engineering
    ENABLE_OUTLIER_CLIPPING = os.getenv('AI_ENABLE_OUTLIER_CLIPPING', 'true').lower() == 'true'
    OUTLIER_CLIP_PERCENTILE = float(os.getenv('AI_OUTLIER_CLIP_PERCENTILE', 0.01))


class BacktestConfig:
    """Backtesting Configuration"""
    
    # Risk management
    DEFAULT_RISK_PERCENT = float(os.getenv('BT_RISK_PERCENT', 1.0))
    DEFAULT_SL_ATR_MULTIPLIER = float(os.getenv('BT_SL_ATR_MULTIPLIER', 2.0))
    DEFAULT_TP_ATR_MULTIPLIER = float(os.getenv('BT_TP_ATR_MULTIPLIER', 4.0))
    
    # Gold-specific limits
    GOLD_MAX_RISK_PERCENT = float(os.getenv('BT_GOLD_MAX_RISK', 1.0))
    GOLD_MAX_SL_ATR = float(os.getenv('BT_GOLD_MAX_SL_ATR', 1.0))
    GOLD_MAX_TP_ATR = float(os.getenv('BT_GOLD_MAX_TP_ATR', 2.0))
    GOLD_MAX_LOT_SIZE = float(os.getenv('BT_GOLD_MAX_LOT', 0.03))
    
    # Position sizing
    INITIAL_CAPITAL = float(os.getenv('BT_INITIAL_CAPITAL', 10000.0))
    MIN_LOT_SIZE = float(os.getenv('BT_MIN_LOT', 0.01))
    MAX_LOT_SIZE = float(os.getenv('BT_MAX_LOT', 0.1))


class DatabaseConfig:
    """Database Configuration"""
    
    DB_NAME = os.getenv('DB_NAME', 'bots.db')
    BACKUP_ENABLED = os.getenv('DB_BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_INTERVAL_HOURS = int(os.getenv('DB_BACKUP_INTERVAL', 24))


class MT5Config:
    """MetaTrader 5 Configuration"""
    
    LOGIN = os.getenv('MT5_LOGIN')
    PASSWORD = os.getenv('MT5_PASSWORD')
    SERVER = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
    TIMEOUT_SECONDS = int(os.getenv('MT5_TIMEOUT', 60000))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate MT5 configuration"""
        return all([cls.LOGIN, cls.PASSWORD, cls.SERVER])


class AppConfig:
    """Application Configuration"""
    
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    PORT = int(os.getenv('FLASK_PORT', 5001))
    SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_secret_key')
    
    # Bot management
    MAX_BOTS = int(os.getenv('MAX_BOTS', 4))
    BOT_CHECK_INTERVAL = int(os.getenv('BOT_CHECK_INTERVAL', 1))  # seconds


def get_all_configs() -> Dict[str, Any]:
    """Get all configuration values as a dictionary"""
    return {
        'AI': {k: v for k, v in AIConfig.__dict__.items() if not k.startswith('_')},
        'Backtest': {k: v for k, v in BacktestConfig.__dict__.items() if not k.startswith('_')},
        'Database': {k: v for k, v in DatabaseConfig.__dict__.items() if not k.startswith('_')},
        'MT5': {k: v for k, v in MT5Config.__dict__.items() if not k.startswith('_')},
        'App': {k: v for k, v in AppConfig.__dict__.items() if not k.startswith('_')},
    }
