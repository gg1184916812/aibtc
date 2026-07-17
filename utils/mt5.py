# core/utils/mt5.py (VERSI FINAL LENGKAP)

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import logging
import os

# Import MetaTrader5 with proper error handling
try:
    import MetaTrader5 as mt5
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"MetaTrader5 module not found: {e}")
    logger.error("Please install MetaTrader5 using: pip install MetaTrader5")
    raise

logger = logging.getLogger(__name__)

# Definisikan konstanta di satu tempat
TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15,  # type: ignore
    "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4, "D1": mt5.TIMEFRAME_D1,  # type: ignore
    "W1": mt5.TIMEFRAME_W1, "MN1": mt5.TIMEFRAME_MN1  # type: ignore
}

_mt5_disconnected_warning_logged = False


def _is_mt5_connected() -> bool:
    try:
        return mt5.terminal_info() is not None  # type: ignore
    except Exception:
        return False


def _try_reconnect_mt5() -> bool:
    try:
        account_str = os.getenv('MT5_LOGIN')
        password = os.getenv('MT5_PASSWORD')
        server = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
        if not account_str or not password:
            return False
        account = int(account_str)
        if mt5.initialize(login=account, password=password, server=server):  # type: ignore
            global _mt5_disconnected_warning_logged
            _mt5_disconnected_warning_logged = False
            logger.info(f"MT5 已重新連線 ({account}) 至伺服器 {server}")
            return True
        return False
    except Exception:
        return False


def _log_mt5_disconnected_once(message: str):
    global _mt5_disconnected_warning_logged
    if not _mt5_disconnected_warning_logged:
        logger.warning(message)
        _mt5_disconnected_warning_logged = True


def initialize_mt5(account: int, password: str, server: str) -> bool:
    """Login ke MetaTrader 5."""
    if not mt5.initialize(login=account, password=password, server=server):  # type: ignore
        logger.error(f"Inisialisasi atau Login MT5 gagal: {mt5.last_error()}")  # type: ignore
        return False
    logger.info(f"Berhasil login ke MT5 ({account}) di server {server}")
    return True

def get_account_info_mt5() -> Optional[Dict[str, Any]]:
    """Mengambil informasi akun (saldo, equity, profit) dari MT5."""
    if not _is_mt5_connected():
        if not _try_reconnect_mt5():
            _log_mt5_disconnected_once("Gagal mengambil info akun. Error: (-10004, 'No IPC connection')")
            return None
    try:
        info = mt5.account_info()  # type: ignore
        if info:
            return info._asdict()
        else:
            logger.warning(f"Gagal mengambil info akun. Error: {mt5.last_error()}")  # type: ignore
            return None
    except Exception as e:
        logger.error(f"Error saat get_account_info_mt5: {e}", exc_info=True)
        return None

def get_rates_mt5(symbol: str, timeframe: int, count: int = 100) -> pd.DataFrame:
    """Mengambil data harga historis (rates) dari MT5 dalam bentuk DataFrame."""
    if not _is_mt5_connected():
        if not _try_reconnect_mt5():
            _log_mt5_disconnected_once(f"Gagal mengambil data harga untuk {symbol} (Timeframe: {timeframe}).")
            return pd.DataFrame()
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)  # type: ignore
        if rates is None or len(rates) == 0:
            logger.warning(f"Gagal mengambil data harga untuk {symbol} (Timeframe: {timeframe}).")
            return pd.DataFrame()
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        df.set_index('time', inplace=True) # Jadikan kolom 'time' sebagai index DataFrame
        
        return df
    except Exception as e:
        logger.error(f"Error saat get_rates_mt5 untuk {symbol}: {e}", exc_info=True)
        return pd.DataFrame()

def get_open_positions_mt5() -> List[Dict[str, Any]]:
    """Mengambil semua posisi trading yang sedang terbuka dari akun MT5."""
    if not _is_mt5_connected():
        if not _try_reconnect_mt5():
            _log_mt5_disconnected_once("Gagal mengambil posisi terbuka dari MT5.")
            return []
    try:
        positions = mt5.positions_get()  # type: ignore
        if positions is None:
            return []
        # Mengubah tuple objek menjadi list dictionary
        return [pos._asdict() for pos in positions]
    except Exception as e:
        logger.error(f"Error saat get_open_positions_mt5: {e}", exc_info=True)
        return []

def get_trade_history_mt5(days: int = 30) -> List[Dict[str, Any]]:
    """Mengambil riwayat transaksi yang sudah ditutup dari MT5."""
    if not _is_mt5_connected():
        if not _try_reconnect_mt5():
            _log_mt5_disconnected_once("Gagal mengambil histori deals dari MT5.")
            return []
    try:
        from_date = datetime.now() - timedelta(days=days)
        deals = mt5.history_deals_get(from_date, datetime.now())  # type: ignore
        if deals is None:
            logger.warning("Gagal mengambil histori deals dari MT5.")
            return []
        # Filter hanya deal penutupan (entry == 1) dan konversi ke dict
        closed_deals = [d._asdict() for d in deals if d.entry == 1]
        return closed_deals
    except Exception as e:
        logger.error(f"Error saat get_trade_history_mt5: {e}", exc_info=True)
        return []

def get_todays_profit_mt5() -> float:
    """Menghitung total profit dari histori trading hari ini."""
    if not _is_mt5_connected():
        if not _try_reconnect_mt5():
            _log_mt5_disconnected_once("Gagal mengambil histori deals untuk profit hari ini.")
            return 0.0
    try:
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = datetime.now()
        
        deals = mt5.history_deals_get(from_date, to_date)  # type: ignore
        
        if deals is None:
            logger.warning("Gagal mengambil histori deals untuk profit hari ini.")
            return 0.0
            
        # Gunakan generator expression untuk efisiensi dan filter deal penutupan
        return sum(d.profit for d in deals if d.entry == 1)
    except Exception as e:
        logger.error(f"Error saat get_todays_profit_mt5: {e}", exc_info=True)
        return 0.0

def find_mt5_symbol(base_symbol: str) -> Optional[str]:
    """
    Mencari nama simbol yang benar di MT5 berdasarkan nama dasar.
    Fungsi ini menggunakan mapping broker-specific dan regex untuk mencocokkan
    variasi simbol di berbagai broker, memastikan kompatibilitas lintas broker.

    Args:
        base_symbol (str): Nama simbol dasar (misal, "XAUUSD", "EURUSD").

    Returns:
        Optional[str]: Nama simbol yang valid dan terlihat di MT5, atau None jika tidak ditemukan.
    """
    import re
    base_symbol_cleaned = re.sub(r'[^A-Z0-9]', '', base_symbol.upper())
    
    if not _is_mt5_connected():
        if not _try_reconnect_mt5():
            _log_mt5_disconnected_once(f"Gagal mencari simbol '{base_symbol}' di MT5: No IPC connection")
            return None
    
    # Mapping broker-specific symbols
    BROKER_SYMBOL_MAP = {
        'XAUUSD': [
            'XAUUSDm',     # Micro lots (priority)
            'GOLD',        # XM Global
            'XAUUSD',      # Standard
            'GOLDmicro',   # XM micro
        ],
        'BTCUSD': [
            'BTCUSDm',     # Micro lots (priority)
            'BTCUSD',      # Standard
            'Bitcoin',     # Some brokers
        ]
    }
    
    try:
        all_symbols = mt5.symbols_get()  # type: ignore
        if all_symbols is None:
            logger.error("Gagal mengambil daftar simbol dari MT5.")
            return None
    except Exception as e:
        logger.error(f"Error saat mengambil daftar simbol dari MT5: {e}")
        return None

    visible_symbols = {s.name for s in all_symbols if s.visible}
    
    # Get current broker info for smarter symbol selection
    broker_name = ""
    try:
        account_info = mt5.account_info()  # type: ignore
        if account_info:
            broker_name = account_info.server.upper()
            logger.info(f"Detected broker: {broker_name}")
    except Exception:
        pass

    # 1. Try broker-specific symbol mapping first
    if base_symbol_cleaned in BROKER_SYMBOL_MAP:
        symbol_variants = BROKER_SYMBOL_MAP[base_symbol_cleaned]
        
        # Broker-specific priority (only for XAUUSD/GOLD variants)
        # IMPORTANT: guard with base_symbol_cleaned check to avoid
        # overwriting symbol_variants for EURUSD, GBPUSD, etc.
        if 'XM' in broker_name:
            if base_symbol_cleaned == 'XAUUSD':
                symbol_variants = ['GOLD', 'GOLDmicro', 'XAUUSD'] + [s for s in symbol_variants if s not in ['GOLD', 'GOLDmicro', 'XAUUSD']]
        elif 'DEMO' in broker_name or 'METAQUOTES' in broker_name:
            if base_symbol_cleaned == 'XAUUSD':
                symbol_variants = ['XAUUSD', 'GOLD'] + [s for s in symbol_variants if s not in ['XAUUSD', 'GOLD']]
        elif 'EXNESS' in broker_name:
            if base_symbol_cleaned == 'XAUUSD':
                symbol_variants = ['XAUUSDm', 'GOLD', 'XAUUSD'] + [s for s in symbol_variants if s not in ['XAUUSDm', 'GOLD', 'XAUUSD']]
        elif 'ALPARI' in broker_name:
            if base_symbol_cleaned == 'XAUUSD':
                symbol_variants = ['XAUUSD.c', 'XAUUSD'] + [s for s in symbol_variants if s not in ['XAUUSD.c', 'XAUUSD']]
        elif 'FBS' in broker_name:
            if base_symbol_cleaned == 'XAUUSD':
                symbol_variants = ['XAUUSD', 'GOLD'] + [s for s in symbol_variants if s not in ['XAUUSD', 'GOLD']]
        
        # Test each variant in priority order
        for variant in symbol_variants:
            if variant in visible_symbols:
                logger.info(f"Broker-specific symbol '{variant}' found for '{base_symbol_cleaned}' on {broker_name}")
                if mt5.symbol_select(variant, True):  # type: ignore
                    return variant
                else:
                    logger.warning(f"Symbol '{variant}' found but failed to activate.")

    # 2. Fallback: Direct match
    if base_symbol_cleaned in visible_symbols:
        logger.info(f"Direct symbol match '{base_symbol_cleaned}' found.")
        return base_symbol_cleaned

    # 3. Fallback: Regex pattern matching
    pattern = re.compile(f"^[a-zA-Z]*{base_symbol_cleaned}[a-zA-Z0-9._-]*$", re.IGNORECASE)
    
    for symbol_name in visible_symbols:
        if pattern.match(symbol_name):
            logger.info(f"Pattern match '{symbol_name}' found for '{base_symbol_cleaned}'.")
            if mt5.symbol_select(symbol_name, True):  # type: ignore
                return symbol_name
            else:
                logger.warning(f"Symbol '{symbol_name}' found but failed to activate.")

    logger.warning(f"No valid symbol variant found for '{base_symbol}' on broker {broker_name}.")
    return None