# core/strategies/base_strategy.py

from abc import ABC, abstractmethod
import numpy as np

class BaseStrategy(ABC):
    """
    Kelas dasar abstrak untuk semua strategi trading.
    Setiap strategi harus mewarisi kelas ini dan mengimplementasikan metode `analyze`.
    """
    def __init__(self, bot_instance, params: dict = None):
        self.bot = bot_instance
        self.params = params or {}

    @abstractmethod
    def analyze(self, df):
        """
        Metode inti yang harus di-override oleh setiap strategi turunan.
        Metode ini harus mengembalikan sebuah dictionary yang berisi hasil analisis.
        Menerima DataFrame sebagai input.
        """
        raise NotImplementedError("Setiap strategi harus mengimplementasikan metode `analyze(df)`.")

    def _buy(self, price):
        return {"signal": "BUY", "price": price}

    def _sell(self, price):
        return {"signal": "SELL", "price": price}

    def _hold(self, price):
        return {"signal": "HOLD", "price": price}

    def analyze_df(self, df):
        """
        Metode untuk BACKTESTING. Menganalisis seluruh DataFrame dengan
        rolling window: setiap bar dihitung signal-nya berdasarkan data historis saat itu.
        """
        df = df.copy()
        signals = ['HOLD'] * len(df)
        min_bars = max(50, self._min_bars_required())

        for i in range(min_bars, len(df)):
            window = df.iloc[:i + 1].copy()
            try:
                result = self.analyze(window)
                signals[i] = str(result.get('signal', 'HOLD')).upper()
            except Exception:
                signals[i] = 'HOLD'

        df['signal'] = signals
        return df

    def _min_bars_required(self):
        """Override di subclass jika perlu minimum bar lebih besar."""
        return 50

    def get_stop_loss(self, df, signal: str, price: float) -> float:
        """
        Opsional: mengembalikan harga stop-loss yang disarankan berdasarkan logika strategi.
        Default: 2% dari harga entry. Override di subclass untuk custom logic (berbasis ATR dll).
        """
        if signal == "BUY":
            return price * 0.98
        elif signal == "SELL":
            return price * 1.02
        return 0.0

    def get_take_profit(self, df, signal: str, price: float) -> float:
        """
        Opsional: mengembalikan harga take-profit yang disarankan.
        Default: 4% dari harga entry (risk-reward 2:1 dari default SL).
        """
        if signal == "BUY":
            return price * 1.04
        elif signal == "SELL":
            return price * 0.96
        return 0.0

    def validate(self, df) -> tuple:
        """
        Opsional: memeriksa apakah kondisi pasar cocok untuk strategi ini.
        Mengembalikan (valid: bool, reason: str).
        Default: selalu valid.
        """
        return True, ""

    @classmethod
    def get_definable_params(cls):
        """
        Metode kelas yang mengembalikan daftar parameter yang bisa diatur oleh pengguna.
        Setiap strategi turunan harus meng-override ini jika memiliki parameter.
        """
        return []
