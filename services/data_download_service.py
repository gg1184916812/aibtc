# core/services/data_download_service.py
"""
自动数据下载服务（覆盖模式）
每次下载直接覆盖旧文件，只保留最近 N 天的数据
"""

import os
import sys
import time
import threading
import logging
import pandas as pd
from datetime import datetime, timedelta
import MetaTrader5 as mt5

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.utils.mt5 import TIMEFRAME_MAP, get_rates_mt5, find_mt5_symbol

logger = logging.getLogger(__name__)

class DataDownloadService:
    """自动数据下载服务 - 覆盖模式"""
    
    def __init__(self):
        self.is_running = False
        self.thread = None
        self._stop_event = threading.Event()
        
        # 数据目录
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backtest_data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 监控的品种和周期
        self.symbols = [
            {'symbol': 'XAUUSDm', 'timeframes': ['M5', 'M15', 'H1', 'H4']},
            {'symbol': 'BTCUSDm', 'timeframes': ['M5', 'M15', 'H1', 'H4']},
            {'symbol': 'EURUSD',  'timeframes': ['M5', 'M15', 'H1', 'H4']},
        ]
        
        # 配置
        self.check_interval = 3600  # 每小时检查一次
        self.lookback_days = 90     # 只保留最近 90 天数据
        
        # 下载状态
        self.status = {
            'last_check': None,
            'last_download': None,
            'total_downloads': 0,
            'errors': [],
            'downloaded_files': [],
            'is_downloading': False,
        }
        
        # 日志
        self.logs = []
        self._add_log("📋 数据下载服务已初始化", "info")
    
    def start(self):
        """启动服务"""
        if self.is_running:
            return False, "服务已在运行"
        
        self._stop_event.clear()
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        self._add_log("🚀 数据下载服务已启动（覆盖模式）", "info")
        self._add_log(f"📁 数据目录: {self.data_dir}", "info")
        self._add_log(f"📅 保留最近 {self.lookback_days} 天数据", "info")
        self._add_log(f"⏱️ 检查间隔: {self.check_interval}秒", "info")
        return True, "服务已启动"
    
    def stop(self):
        """停止服务"""
        if not self.is_running:
            return False, "服务未运行"
        
        self._stop_event.set()
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        self._add_log("🛑 数据下载服务已停止", "warning")
        return True, "服务已停止"
    
    def get_status(self):
        """获取服务状态"""
        return {
            'is_running': self.is_running,
            'status': self.status,
            'logs': self.logs[-50:],
        }
    
    def _add_log(self, message, level="info"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append({
            'timestamp': timestamp,
            'message': message,
            'level': level
        })
        if len(self.logs) > 500:
            self.logs = self.logs[-200:]
    
    def _run_loop(self):
        """主循环"""
        self._add_log("⏳ 数据下载服务初始化中...", "info")
        
        # 启动时立即执行一次下载
        self._download_all()
        
        while not self._stop_event.is_set():
            try:
                time.sleep(self.check_interval)
                self._download_all()
            except Exception as e:
                logger.error(f"数据下载服务错误: {e}")
                self._add_log(f"❌ 错误: {e}", "error")
                time.sleep(60)
        
        self.is_running = False
    
    def _download_all(self):
        """下载所有配置的品种和周期"""
        self.status['last_check'] = datetime.now().isoformat()
        
        # 检查 MT5 连接
        if not mt5.terminal_info():
            self._add_log("⚠️ MT5 未连接，跳过检查", "warning")
            return
        
        for config in self.symbols:
            symbol = config['symbol']
            for timeframe in config['timeframes']:
                self._download_symbol_data(symbol, timeframe)
        
        self.status['last_check'] = datetime.now().isoformat()
        self._add_log("✅ 所有数据检查完成", "info")
    
    def _download_symbol_data(self, symbol: str, timeframe: str):
        """下载单个品种的单个周期数据（覆盖模式）"""
        try:
            file_path = os.path.join(self.data_dir, f"{symbol}_{timeframe}_data.csv")
            
            # 检查文件是否需要更新
            need_download = True
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, parse_dates=['time'])
                if not df.empty:
                    last_date = df['time'].max()
                    days_since = (datetime.now() - last_date).days
                    if days_since < 1:
                        need_download = False
                        return
            
            if not need_download:
                return
            
            self._add_log(f"📊 {symbol} {timeframe}: 下载最新数据...", "info")
            self.status['is_downloading'] = True
            self.status['last_download'] = datetime.now().isoformat()
            
            # 获取 MT5 符号
            mt5_symbol = find_mt5_symbol(symbol)
            if not mt5_symbol:
                self._add_log(f"❌ {symbol}: 符号未找到", "error")
                return
            
            tf_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1,
                'W1': mt5.TIMEFRAME_W1,
            }
            
            tf_const = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)
            
            rates = mt5.copy_rates_range(mt5_symbol, tf_const, start_date, end_date)
            
            if rates is None or len(rates) == 0:
                self._add_log(f"❌ {symbol} {timeframe}: 无数据返回", "error")
                return
            
            df_new = pd.DataFrame(rates)
            df_new['time'] = pd.to_datetime(df_new['time'], unit='s')
            
            df_new = df_new.rename(columns={
                'time': 'time',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            })
            df_new = df_new[['time', 'open', 'high', 'low', 'close', 'volume']]
            
            # 直接覆盖保存
            df_new.to_csv(file_path, index=False)
            
            self._add_log(f"✅ {symbol} {timeframe}: 已覆盖更新 (共 {len(df_new)} 条, 最近 {self.lookback_days} 天)", "info")
            
            self.status['total_downloads'] += 1
            self.status['downloaded_files'].append({
                'symbol': symbol,
                'timeframe': timeframe,
                'bars': len(df_new),
                'time': datetime.now().isoformat()
            })
            
            self.status['is_downloading'] = False
            
        except Exception as e:
            logger.error(f"下载 {symbol} {timeframe} 失败: {e}")
            self._add_log(f"❌ {symbol} {timeframe}: {e}", "error")
            self.status['is_downloading'] = False
            self.status['errors'].append({
                'symbol': symbol,
                'timeframe': timeframe,
                'error': str(e),
                'time': datetime.now().isoformat()
            })
    
    def manual_download(self, symbol: str, timeframe: str):
        """手动触发下载（覆盖模式）"""
        self._add_log(f"🔄 手动下载: {symbol} {timeframe}", "info")
        self._download_symbol_data(symbol, timeframe)
        return True


# 全局服务实例
_download_service = None

def get_download_service():
    """获取下载服务单例"""
    global _download_service
    if _download_service is None:
        _download_service = DataDownloadService()
    return _download_service