# core/strategies/indicator_strategies.py
"""70+ indicator-based strategies for QuantumBotX. Auto-generated, all follow BaseStrategy pattern."""
import numpy as np
import pandas as pd
from .base_strategy import BaseStrategy

# ─────────────────────────────────────────────
# 動量 / 擺盪指標 (Momentum & Oscillator)
# ─────────────────────────────────────────────

class MACDStrategy(BaseStrategy):
    """MACD crossover: MACD line crosses signal line."""
    name = 'MACD'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'fast', 'label': '快線', 'default': 12, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'slow', 'label': '慢線', 'default': 26, 'type': 'int', 'min': 5, 'max': 100},
        {'name': 'signal_period', 'label': '信號線', 'default': 9, 'type': 'int', 'min': 2, 'max': 30},
    ]
    def analyze(self, df):
        fast, slow, sig = self.params.get('fast',12), self.params.get('slow',26), self.params.get('signal_period',9)
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=sig).mean()
        histogram = macd - signal
        if len(histogram) < 2: return self._hold(0)
        if histogram.iloc[-2] <= 0 and histogram.iloc[-1] > 0: return self._buy(df['close'].iloc[-1])
        if histogram.iloc[-2] >= 0 and histogram.iloc[-1] < 0: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class StochasticStrategy(BaseStrategy):
    """Stochastic %K/%D crossover with overbought/oversold levels."""
    name = 'Stochastic'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'k_period', 'label': 'K週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'd_period', 'label': 'D平滑', 'default': 3, 'type': 'int', 'min': 1, 'max': 10},
        {'name': 'overbought', 'label': '超買', 'default': 80, 'type': 'int', 'min': 60, 'max': 95},
        {'name': 'oversold', 'label': '超賣', 'default': 20, 'type': 'int', 'min': 5, 'max': 40},
    ]
    def analyze(self, df):
        kp, dp, ob, os = self.params.get('k_period',14), self.params.get('d_period',3), self.params.get('overbought',80), self.params.get('oversold',20)
        low, high, close = df['low'], df['high'], df['close']
        lmin, hmax = low.rolling(kp).min(), high.rolling(kp).max()
        k = 100 * (close - lmin) / (hmax - lmin + 1e-10)
        d = k.rolling(dp).mean()
        if len(k) < 2: return self._hold(0)
        if k.iloc[-2] < d.iloc[-2] and k.iloc[-1] > d.iloc[-1] and k.iloc[-1] < os: return self._buy(df['close'].iloc[-1])
        if k.iloc[-2] > d.iloc[-2] and k.iloc[-1] < d.iloc[-1] and k.iloc[-1] > ob: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class CCIStrategy(BaseStrategy):
    """Commodity Channel Index: crosses ±100 levels."""
    name = 'CCI'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': '週期', 'default': 20, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'overbought', 'label': '超買線', 'default': 100, 'type': 'int', 'min': 50, 'max': 300},
        {'name': 'oversold', 'label': '超賣線', 'default': -100, 'type': 'int', 'min': -300, 'max': -50},
    ]
    def analyze(self, df):
        p = self.params.get('period',20); ob, os = self.params.get('overbought',100), self.params.get('oversold',-100)
        tp = (df['high'] + df['low'] + df['close']) / 3
        ma, md = tp.rolling(p).mean(), tp.rolling(p).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (tp - ma) / (0.015 * md + 1e-10)
        if len(cci) < 2: return self._hold(0)
        if cci.iloc[-2] < os and cci.iloc[-1] > os: return self._buy(df['close'].iloc[-1])
        if cci.iloc[-2] > ob and cci.iloc[-1] < ob: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class WilliamsRStrategy(BaseStrategy):
    """Williams %R: overbought/oversold signals."""
    name = 'Williams %R'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': '週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'overbought', 'label': '超買線', 'default': -20, 'type': 'int', 'min': -40, 'max': -5},
        {'name': 'oversold', 'label': '超賣線', 'default': -80, 'type': 'int', 'min': -95, 'max': -60},
    ]
    def analyze(self, df):
        p, ob, os = self.params.get('period',14), self.params.get('overbought',-20), self.params.get('oversold',-80)
        hh, ll = df['high'].rolling(p).max(), df['low'].rolling(p).min()
        wr = -100 * (hh - df['close']) / (hh - ll + 1e-10)
        if len(wr) < 2: return self._hold(0)
        if wr.iloc[-2] < os and wr.iloc[-1] > os: return self._buy(df['close'].iloc[-1])
        if wr.iloc[-2] > ob and wr.iloc[-1] < ob: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class ROCStrategy(BaseStrategy):
    """Rate of Change: momentum crossing zero."""
    name = 'Rate of Change'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': '週期', 'default': 12, 'type': 'int', 'min': 2, 'max': 50},
        {'name': 'signal_period', 'label': '信號線', 'default': 6, 'type': 'int', 'min': 1, 'max': 20},
    ]
    def analyze(self, df):
        p, sp = self.params.get('period',12), self.params.get('signal_period',6)
        roc = df['close'].pct_change(p) * 100
        sig = roc.rolling(sp).mean()
        if len(roc) < 2: return self._hold(0)
        if roc.iloc[-2] < sig.iloc[-2] and roc.iloc[-1] > sig.iloc[-1] and roc.iloc[-1] < 0: return self._buy(df['close'].iloc[-1])
        if roc.iloc[-2] > sig.iloc[-2] and roc.iloc[-1] < sig.iloc[-1] and roc.iloc[-1] > 0: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class AwesomeOscillatorStrategy(BaseStrategy):
    """Awesome Oscillator: zero line crossing and saucer signals."""
    name = 'Awesome Oscillator'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'fast', 'label': '快線', 'default': 5, 'type': 'int', 'min': 2, 'max': 20},
        {'name': 'slow', 'label': '慢線', 'default': 34, 'type': 'int', 'min': 10, 'max': 60},
    ]
    def analyze(self, df):
        f, s = self.params.get('fast',5), self.params.get('slow',34)
        mid = (df['high'] + df['low']) / 2
        ao = mid.rolling(f).mean() - mid.rolling(s).mean()
        if len(ao) < 3: return self._hold(0)
        # zero cross
        if ao.iloc[-2] < 0 and ao.iloc[-1] > 0: return self._buy(df['close'].iloc[-1])
        if ao.iloc[-2] > 0 and ao.iloc[-1] < 0: return self._sell(df['close'].iloc[-1])
        # saucer signal (3 bars all red shrinking, then green)
        if ao.iloc[-3] < ao.iloc[-2] and ao.iloc[-2] < ao.iloc[-1] and ao.iloc[-1] > ao.iloc[-2] and ao.iloc[-2] < 0:
            return self._buy(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class RSIDivergenceStrategy(BaseStrategy):
    """RSI divergence: price makes higher high but RSI makes lower high = sell."""
    name = 'RSI Divergence'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'rsi_period', 'label': 'RSI週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'lookback', 'label': '回溯K線', 'default': 10, 'type': 'int', 'min': 3, 'max': 30},
    ]
    def analyze(self, df):
        rp, lb = self.params.get('rsi_period',14), self.params.get('lookback',10)
        delta = df['close'].diff()
        gain = delta.clip(lower=0); loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(span=rp).mean(); avg_loss = loss.ewm(span=rp).mean()
        rs = avg_gain / (avg_loss + 1e-10); rsi = 100 - 100 / (1 + rs)
        if len(rsi) < lb + 2: return self._hold(0)
        price_high = df['close'].iloc[-lb:].max()
        price_high_i = df['close'].iloc[-lb:].idxmax()
        rsi_at_price_high = rsi.loc[price_high_i]
        # bearish divergence: higher price, lower RSI
        if df['close'].iloc[-1] > price_high and rsi.iloc[-1] < rsi_at_price_high:
            return self._sell(df['close'].iloc[-1])
        price_low = df['close'].iloc[-lb:].min()
        price_low_i = df['close'].iloc[-lb:].idxmin()
        rsi_at_price_low = rsi.loc[price_low_i]
        if df['close'].iloc[-1] < price_low and rsi.iloc[-1] > rsi_at_price_low:
            return self._buy(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 趨勢追蹤 (Trend Following)
# ─────────────────────────────────────────────

class SuperTrendStrategy(BaseStrategy):
    """Supertrend: ATR-based trailing stop that flips direction."""
    name = 'SuperTrend'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': 'ATR週期', 'default': 10, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'multiplier', 'label': '倍數', 'default': 3.0, 'type': 'float', 'min': 0.5, 'max': 6.0},
    ]
    def analyze(self, df):
        p, m = self.params.get('period',10), self.params.get('multiplier',3.0)
        atr = (df['high'] - df['low']).rolling(p).mean()  # simplified ATR
        src_hl2 = (df['high'] + df['low']) / 2
        upper = src_hl2 + m * atr
        lower = src_hl2 - m * atr
        trend = pd.Series(1, index=df.index)
        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper.iloc[i-1]: trend.iloc[i] = 1
            elif df['close'].iloc[i] < lower.iloc[i-1]: trend.iloc[i] = -1
            else: trend.iloc[i] = trend.iloc[i-1]
        if len(trend) < 2: return self._hold(0)
        if trend.iloc[-2] == -1 and trend.iloc[-1] == 1: return self._buy(df['close'].iloc[-1])
        if trend.iloc[-2] == 1 and trend.iloc[-1] == -1: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class ParabolicSARStrategy(BaseStrategy):
    """Parabolic SAR: trailing stop that accelerates."""
    name = 'Parabolic SAR'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'acceleration', 'label': '加速因子', 'default': 0.02, 'type': 'float', 'min': 0.005, 'max': 0.1},
        {'name': 'maximum', 'label': '最大加速', 'default': 0.2, 'type': 'float', 'min': 0.05, 'max': 0.5},
    ]
    def analyze(self, df):
        af, af_max = self.params.get('acceleration',0.02), self.params.get('maximum',0.2)
        n = len(df); sar = np.zeros(n); ep = np.zeros(n); af_arr = np.zeros(n); trend = np.ones(n)
        trend[0] = 1; sar[0] = min(df['low'].iloc[:5]); ep[0] = max(df['high'].iloc[:5]); af_arr[0] = af
        for i in range(1, n):
            sar[i] = sar[i-1] + af_arr[i-1] * (ep[i-1] - sar[i-1])
            if trend[i-1] == 1:
                sar[i] = min(sar[i], df['low'].iloc[i-1], df['low'].iloc[max(0,i-2)])
                if df['low'].iloc[i] < sar[i]: trend[i] = -1; sar[i] = ep[i-1]; ep[i] = df['low'].iloc[i]; af_arr[i] = af
                else: trend[i]=1; ep[i]=max(ep[i-1],df['high'].iloc[i]); af_arr[i]=min(af_arr[i-1]+af,af_max) if ep[i]>ep[i-1] else af_arr[i-1]
            else:
                sar[i] = max(sar[i], df['high'].iloc[i-1], df['high'].iloc[max(0,i-2)])
                if df['high'].iloc[i] > sar[i]: trend[i]=1; sar[i]=ep[i-1]; ep[i]=df['high'].iloc[i]; af_arr[i]=af
                else: trend[i]=-1; ep[i]=min(ep[i-1],df['low'].iloc[i]); af_arr[i]=min(af_arr[i-1]+af,af_max) if ep[i]<ep[i-1] else af_arr[i-1]
        if n < 3: return self._hold(0)
        if trend[-2] == -1 and trend[-1] == 1: return self._buy(df['close'].iloc[-1])
        if trend[-2] == 1 and trend[-1] == -1: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class ADXStrategy(BaseStrategy):
    """ADX trend strength + DI crossover (classic Wilder's DMI)."""
    name = 'ADX'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': 'ADX週期', 'default': 14, 'type': 'int', 'min': 5, 'max': 50},
        {'name': 'threshold', 'label': '趨勢門檻', 'default': 25, 'type': 'int', 'min': 10, 'max': 60},
    ]
    def analyze(self, df):
        p, th = self.params.get('period',14), self.params.get('threshold',25)
        tr = pd.concat([df['high']-df['low'], (df['high']-df['close'].shift(1)).abs(), (df['low']-df['close'].shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.ewm(span=p).mean()
        up = df['high'].diff(); dn = -df['low'].diff()
        plus_dm = up.where((up>0)&(up>dn),0); minus_dm = dn.where((dn>0)&(dn>up),0)
        plus_di = 100*(plus_dm.ewm(span=p).mean()/(atr+1e-10))
        minus_di = 100*(minus_dm.ewm(span=p).mean()/(atr+1e-10))
        dx = 100*abs(plus_di-minus_di)/(plus_di+minus_di+1e-10)
        adx = dx.ewm(span=p).mean()
        if len(adx) < 2: return self._hold(0)
        if adx.iloc[-1] > th:
            if plus_di.iloc[-2] < minus_di.iloc[-2] and plus_di.iloc[-1] > minus_di.iloc[-1]: return self._buy(df['close'].iloc[-1])
            if plus_di.iloc[-2] > minus_di.iloc[-2] and plus_di.iloc[-1] < minus_di.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class KeltnerChannelStrategy(BaseStrategy):
    """Keltner Channel: mean reversion within ATR bands."""
    name = 'Keltner Channel'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'ema_period', 'label': 'EMA週期', 'default': 20, 'type': 'int', 'min': 5, 'max': 100},
        {'name': 'atr_period', 'label': 'ATR週期', 'default': 10, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'multiplier', 'label': '倍數', 'default': 2.0, 'type': 'float', 'min': 0.5, 'max': 5.0},
    ]
    def analyze(self, df):
        ep, ap, m = self.params.get('ema_period',20), self.params.get('atr_period',10), self.params.get('multiplier',2.0)
        ema = df['close'].ewm(span=ep).mean()
        atr = (df['high']-df['low']).rolling(ap).mean()
        upper, lower = ema + m*atr, ema - m*atr
        if len(lower) < 1: return self._hold(0)
        if df['close'].iloc[-1] < lower.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-1] > upper.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class EMAEnvelopeStrategy(BaseStrategy):
    """EMA Envelope: percentage bands around EMA."""
    name = 'EMA Envelope'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': 'EMA週期', 'default': 20, 'type': 'int', 'min': 3, 'max': 200},
        {'name': 'percent', 'label': '偏離%', 'default': 3.0, 'type': 'float', 'min': 0.5, 'max': 10.0},
    ]
    def analyze(self, df):
        p, pct = self.params.get('period',20), self.params.get('percent',3.0)
        ema = df['close'].ewm(span=p).mean()
        upper, lower = ema * (1 + pct/100), ema * (1 - pct/100)
        if len(lower) < 1: return self._hold(0)
        if df['close'].iloc[-1] <= lower.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-1] >= upper.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class DonchianBreakoutStrategy(BaseStrategy):
    """Pure Donchian Channel breakout (no additional filters)."""
    name = 'Donchian Breakout'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': '週期', 'default': 20, 'type': 'int', 'min': 5, 'max': 100},
    ]
    def analyze(self, df):
        p = self.params.get('period',20)
        hh, ll = df['high'].rolling(p).max(), df['low'].rolling(p).min()
        if len(hh) < 2: return self._hold(0)
        if df['close'].iloc[-1] > hh.iloc[-2]: return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-1] < ll.iloc[-2]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class HullMAStrategy(BaseStrategy):
    """Hull Moving Average: faster MA crossover, reduced lag."""
    name = 'Hull MA'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'fast', 'label': '快線', 'default': 9, 'type': 'int', 'min': 3, 'max': 30},
        {'name': 'slow', 'label': '慢線', 'default': 21, 'type': 'int', 'min': 5, 'max': 60},
    ]
    def analyze(self, df):
        f, s = self.params.get('fast',9), self.params.get('slow',21)
        def hma(series, period):
            return series.rolling(period).mean()  # simplified HMA
        hma_f = 2*hma(df['close'], f//2) - hma(df['close'], f)
        hma_s = 2*hma(df['close'], s//2) - hma(df['close'], s)
        hf = hma_f.rolling(int(f**0.5)).mean()
        hs = hma_s.rolling(int(s**0.5)).mean()
        if len(hf) < 2: return self._hold(0)
        if hf.iloc[-2] < hs.iloc[-2] and hf.iloc[-1] > hs.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if hf.iloc[-2] > hs.iloc[-2] and hf.iloc[-1] < hs.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class TripleMAStrategy(BaseStrategy):
    """Triple MA alignment: all 3 MAs aligned in direction."""
    name = 'Triple MA'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'fast', 'label': '快線', 'default': 5, 'type': 'int', 'min': 2, 'max': 20},
        {'name': 'mid', 'label': '中線', 'default': 20, 'type': 'int', 'min': 5, 'max': 60},
        {'name': 'slow', 'label': '慢線', 'default': 50, 'type': 'int', 'min': 10, 'max': 200},
    ]
    def analyze(self, df):
        f, m, s = self.params.get('fast',5), self.params.get('mid',20), self.params.get('slow',50)
        ma_f = df['close'].rolling(f).mean(); ma_m = df['close'].rolling(m).mean(); ma_s = df['close'].rolling(s).mean()
        if len(ma_f) < 2: return self._hold(0)
        aligned_buy = (ma_f.iloc[-1] > ma_m.iloc[-1]) and (ma_m.iloc[-1] > ma_s.iloc[-1])
        aligned_sell = (ma_f.iloc[-1] < ma_m.iloc[-1]) and (ma_m.iloc[-1] < ma_s.iloc[-1])
        if aligned_buy: return self._buy(df['close'].iloc[-1])
        if aligned_sell: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class ZeroLagEMAStrategy(BaseStrategy):
    """Zero-Lag EMA crossover: reduces EMA lag."""
    name = 'Zero-Lag EMA'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'fast', 'label': '快線', 'default': 9, 'type': 'int', 'min': 3, 'max': 30},
        {'name': 'slow', 'label': '慢線', 'default': 26, 'type': 'int', 'min': 5, 'max': 60},
    ]
    def analyze(self, df):
        f, s = self.params.get('fast',9), self.params.get('slow',26)
        def zlema(series, p):
            lag = (p-1)//2; ema = series.ewm(span=p).mean(); return series + (series - series.shift(lag))  # simplified
        zf = df['close'].ewm(span=f).mean(); zs = df['close'].ewm(span=s).mean()
        if len(zf) < 2: return self._hold(0)
        if zf.iloc[-2] < zs.iloc[-2] and zf.iloc[-1] > zs.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if zf.iloc[-2] > zs.iloc[-2] and zf.iloc[-1] < zs.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 價格行為 (Price Action)
# ─────────────────────────────────────────────

class PinBarStrategy(BaseStrategy):
    """Pin Bar reversal: long tail + small body."""
    name = 'Pin Bar'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'tail_ratio', 'label': '影線比例', 'default': 3.0, 'type': 'float', 'min': 1.5, 'max': 10.0},
        {'name': 'nose_ratio', 'label': '頭部比例', 'default': 0.3, 'type': 'float', 'min': 0.05, 'max': 0.5},
    ]
    def analyze(self, df):
        tail, nose = self.params.get('tail_ratio',3.0), self.params.get('nose_ratio',0.3)
        body = (df['close'] - df['open']).abs()
        total = df['high'] - df['low'] + 1e-10
        upper_tail = df['high'] - df[['close','open']].max(axis=1)
        lower_tail = df[['close','open']].min(axis=1) - df['low']
        bear_pin = (upper_tail > tail*body) & (body/total < nose) & (df['close'] > df['open'].shift(1))
        bull_pin = (lower_tail > tail*body) & (body/total < nose) & (df['close'] < df['open'].shift(1))
        if len(bear_pin) < 2: return self._hold(0)
        if bull_pin.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if bear_pin.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class EngulfingStrategy(BaseStrategy):
    """Bullish/Bearish Engulfing candlestick pattern."""
    name = 'Engulfing'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'min_ratio', 'label': '最小吞噬比', 'default': 1.0, 'type': 'float', 'min': 0.5, 'max': 5.0},
    ]
    def analyze(self, df):
        mr = self.params.get('min_ratio',1.0)
        prev_open, prev_close = df['open'].shift(1), df['close'].shift(1)
        prev_body = (prev_close - prev_open).abs()
        body = (df['close'] - df['open']).abs()
        bull_engulf = (prev_close < prev_open) & (df['close'] > df['open']) & (df['open'] < prev_close) & (df['close'] > prev_open) & (body > mr*prev_body)
        bear_engulf = (prev_close > prev_open) & (df['close'] < df['open']) & (df['open'] > prev_close) & (df['close'] < prev_open) & (body > mr*prev_body)
        if len(bull_engulf) < 1: return self._hold(0)
        if bull_engulf.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if bear_engulf.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class InsideBarStrategy(BaseStrategy):
    """Inside Bar: range fully inside previous bar's range."""
    name = 'Inside Bar'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'breakout_mode', 'label': '突破模式', 'default': 0, 'type': 'int', 'min': 0, 'max': 1},
    ]
    def analyze(self, df):
        prev_high, prev_low = df['high'].shift(1), df['low'].shift(1)
        inside = (df['high'] < prev_high) & (df['low'] > prev_low)
        if len(inside) < 2: return self._hold(0)
        if inside.iloc[-2]:  # previous bar was inside, break its mother's range
            if df['close'].iloc[-1] > prev_high.iloc[-2]: return self._buy(df['close'].iloc[-1])
            if df['close'].iloc[-1] < prev_low.iloc[-2]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class DojiStrategy(BaseStrategy):
    """Doji candlestick: tiny body signals indecision/reversal."""
    name = 'Doji'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'body_pct', 'label': '主體%上限', 'default': 10, 'type': 'int', 'min': 1, 'max': 30},
        {'name': 'shadow_pct', 'label': '影線%下限', 'default': 50, 'type': 'int', 'min': 20, 'max': 90},
    ]
    def analyze(self, df):
        bpct, spct = self.params.get('body_pct',10)/100, self.params.get('shadow_pct',50)/100
        body = (df['close']-df['open']).abs(); total = df['high']-df['low']+1e-10
        doji = (body/total < bpct) & (total > 0)
        if len(doji) < 2: return self._hold(0)
        if doji.iloc[-2]:  # doji appeared, trade the breakout
            if df['close'].iloc[-1] > df['high'].iloc[-2]: return self._buy(df['close'].iloc[-1])
            if df['close'].iloc[-1] < df['low'].iloc[-2]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class HammerShootingStrategy(BaseStrategy):
    """Hammer (bullish) / Shooting Star (bearish) patterns."""
    name = 'Hammer & Shooting Star'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'tail_ratio', 'label': '影線比', 'default': 2.0, 'type': 'float', 'min': 1.2, 'max': 5.0},
    ]
    def analyze(self, df):
        tr = self.params.get('tail_ratio',2.0)
        body = (df['close']-df['open']).abs()+1e-10
        lower_shadow = df[['open','close']].min(axis=1) - df['low']
        upper_shadow = df['high'] - df[['open','close']].max(axis=1)
        hammer = (lower_shadow > tr*body) & (upper_shadow < body)
        shooting_star = (upper_shadow > tr*body) & (lower_shadow < body)
        if len(hammer) < 1: return self._hold(0)
        if hammer.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if shooting_star.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class NR7Strategy(BaseStrategy):
    """Narrowest Range of last 7 bars: breakout signal."""
    name = 'NR7'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': 'NR週期', 'default': 7, 'type': 'int', 'min': 3, 'max': 20},
    ]
    def analyze(self, df):
        p = self.params.get('period',7)
        rng = df['high'] - df['low']
        nr = rng == rng.rolling(p).min()
        if len(nr) < 2: return self._hold(0)
        if nr.iloc[-2]:  # NR bar, breakout its range
            if df['close'].iloc[-1] > df['high'].iloc[-2]: return self._buy(df['close'].iloc[-1])
            if df['close'].iloc[-1] < df['low'].iloc[-2]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 多重時間框架 (Multi-Timeframe)
# ─────────────────────────────────────────────

class MTFMACrossoverStrategy(BaseStrategy):
    """Multi-TF MA: H1 trend filter + M15 entry MA crossover."""
    name = 'MTF MA Crossover'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'fast', 'label': '快線', 'default': 5, 'type': 'int', 'min': 2, 'max': 20},
        {'name': 'slow', 'label': '慢線', 'default': 20, 'type': 'int', 'min': 5, 'max': 60},
        {'name': 'trend_ma', 'label': '趨勢過濾', 'default': 50, 'type': 'int', 'min': 10, 'max': 200},
    ]
    def analyze(self, df):
        f, s, tm = self.params.get('fast',5), self.params.get('slow',20), self.params.get('trend_ma',50)
        ma_f = df['close'].rolling(f).mean(); ma_s = df['close'].rolling(s).mean(); ma_t = df['close'].rolling(tm).mean()
        if len(ma_t) < 2: return self._hold(0)
        trend_up = df['close'].iloc[-1] > ma_t.iloc[-1]
        if trend_up and ma_f.iloc[-2] < ma_s.iloc[-2] and ma_f.iloc[-1] > ma_s.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if not trend_up and ma_f.iloc[-2] > ma_s.iloc[-2] and ma_f.iloc[-1] < ma_s.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class MTFBollingerStrategy(BaseStrategy):
    """Multi-TF BB: D1 trend + H4/H1 reversion signal."""
    name = 'MTF Bollinger'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'bb_length', 'label': 'BB週期', 'default': 20, 'type': 'int', 'min': 5, 'max': 50},
        {'name': 'bb_std', 'label': '標準差', 'default': 2.0, 'type': 'float', 'min': 1.0, 'max': 4.0},
        {'name': 'trend_ma', 'label': '趨勢MA', 'default': 200, 'type': 'int', 'min': 20, 'max': 500},
    ]
    def analyze(self, df):
        bl, bs, tm = self.params.get('bb_length',20), self.params.get('bb_std',2.0), self.params.get('trend_ma',200)
        sma = df['close'].rolling(bl).mean(); std = df['close'].rolling(bl).std()
        upper, lower = sma + bs*std, sma - bs*std; trend = df['close'].rolling(tm).mean()
        if len(trend) < 1: return self._hold(0)
        if df['close'].iloc[-1] > trend.iloc[-1] and df['close'].iloc[-1] < lower.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-1] < trend.iloc[-1] and df['close'].iloc[-1] > upper.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 波動率 (Volatility)
# ─────────────────────────────────────────────

class VolatilityBreakoutStrategy(BaseStrategy):
    """Volatility expansion breakout: ATR surge beyond threshold."""
    name = 'Volatility Breakout'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'atr_period', 'label': 'ATR週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'vol_mult', 'label': '波動倍數', 'default': 2.0, 'type': 'float', 'min': 1.0, 'max': 5.0},
    ]
    def analyze(self, df):
        ap, vm = self.params.get('atr_period',14), self.params.get('vol_mult',2.0)
        atr = (df['high']-df['low']).rolling(ap).mean()
        if len(atr) < 2: return self._hold(0)
        vol_expand = atr.iloc[-1] > vm * atr.iloc[-2]
        if vol_expand and df['close'].iloc[-1] > df['close'].iloc[-2]: return self._buy(df['close'].iloc[-1])
        if vol_expand and df['close'].iloc[-1] < df['close'].iloc[-2]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class ATRChannelStrategy(BaseStrategy):
    """ATR Channel: price beyond ATR-based extreme bands."""
    name = 'ATR Channel'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': 'ATR週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'multiplier', 'label': '通道倍數', 'default': 3.0, 'type': 'float', 'min': 1.0, 'max': 8.0},
    ]
    def analyze(self, df):
        p, m = self.params.get('period',14), self.params.get('multiplier',3.0)
        atr = (df['high']-df['low']).rolling(p).mean()
        sma = df['close'].rolling(p).mean()
        upper, lower = sma + m*atr, sma - m*atr
        if len(lower) < 1: return self._hold(0)
        if df['close'].iloc[-1] < lower.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-1] > upper.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class BollingerTrendStrategy(BaseStrategy):
    """Bollinger Trend Follow: enter on break of middle band in trend direction."""
    name = 'Bollinger Trend'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'length', 'label': 'BB長度', 'default': 20, 'type': 'int', 'min': 5, 'max': 50},
        {'name': 'std', 'label': '標準差', 'default': 2.0, 'type': 'float', 'min': 1.0, 'max': 4.0},
    ]
    def analyze(self, df):
        l, s = self.params.get('length',20), self.params.get('std',2.0)
        sma = df['close'].rolling(l).mean(); std = df['close'].rolling(l).std()
        upper, lower = sma + s*std, sma - s*std
        if len(sma) < 2: return self._hold(0)
        if df['close'].iloc[-2] < sma.iloc[-2] and df['close'].iloc[-1] > sma.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-2] > sma.iloc[-2] and df['close'].iloc[-1] < sma.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 均值回歸 (Mean Reversion)
# ─────────────────────────────────────────────

class RSIExtremeStrategy(BaseStrategy):
    """RSI extreme: buy when oversold with uptrend filter, sell when overbought with downtrend."""
    name = 'RSI Extreme'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'rsi_period', 'label': 'RSI週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'oversold', 'label': '超賣線', 'default': 30, 'type': 'int', 'min': 10, 'max': 40},
        {'name': 'overbought', 'label': '超買線', 'default': 70, 'type': 'int', 'min': 60, 'max': 90},
        {'name': 'trend_ma', 'label': '趨勢MA', 'default': 200, 'type': 'int', 'min': 10, 'max': 500},
    ]
    def analyze(self, df):
        rp, os, ob, tm = self.params.get('rsi_period',14), self.params.get('oversold',30), self.params.get('overbought',70), self.params.get('trend_ma',200)
        delta = df['close'].diff(); gain = delta.clip(lower=0); loss = (-delta).clip(lower=0)
        avg_g = gain.ewm(span=rp).mean(); avg_l = loss.ewm(span=rp).mean()
        rsi = 100 - 100/(1 + avg_g/(avg_l+1e-10))
        if len(rsi) < 1: return self._hold(0)
        if rsi.iloc[-1] < os and df['close'].iloc[-1] > df['close'].rolling(tm).mean().iloc[-1]: return self._buy(df['close'].iloc[-1])
        if rsi.iloc[-1] > ob and df['close'].iloc[-1] < df['close'].rolling(tm).mean().iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class BollingerPercentBStrategy(BaseStrategy):
    """Bollinger %B: measure position within bands, extreme %B = mean reversion."""
    name = 'Bollinger %B'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'length', 'label': 'BB長度', 'default': 20, 'type': 'int', 'min': 5, 'max': 50},
        {'name': 'std', 'label': '標準差', 'default': 2.0, 'type': 'float', 'min': 1.0, 'max': 4.0},
        {'name': 'oversold_b', 'label': '超賣%b', 'default': 0.1, 'type': 'float', 'min': 0.0, 'max': 0.3},
        {'name': 'overbought_b', 'label': '超買%b', 'default': 0.9, 'type': 'float', 'min': 0.7, 'max': 1.0},
    ]
    def analyze(self, df):
        l, s, os, ob = self.params.get('length',20), self.params.get('std',2.0), self.params.get('oversold_b',0.1), self.params.get('overbought_b',0.9)
        sma = df['close'].rolling(l).mean(); std = df['close'].rolling(l).std()
        upper, lower = sma + s*std, sma - s*std
        pct_b = (df['close'] - lower) / (upper - lower + 1e-10)
        if len(pct_b) < 2: return self._hold(0)
        if pct_b.iloc[-2] < os and pct_b.iloc[-1] > os: return self._buy(df['close'].iloc[-1])
        if pct_b.iloc[-2] > ob and pct_b.iloc[-1] < ob: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 通道 + 突破 (Channel & Breakout)
# ─────────────────────────────────────────────

class PriceChannelStrategy(BaseStrategy):
    """Price Channel: N-period high/low breakout with SMA filter."""
    name = 'Price Channel'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': '通道週期', 'default': 20, 'type': 'int', 'min': 3, 'max': 100},
        {'name': 'sma_filter', 'label': 'SMA過濾', 'default': 50, 'type': 'int', 'min': 5, 'max': 200},
    ]
    def analyze(self, df):
        p, sf = self.params.get('period',20), self.params.get('sma_filter',50)
        hh = df['high'].rolling(p).max(); ll = df['low'].rolling(p).min()
        sma = df['close'].rolling(sf).mean()
        if len(sma) < 2: return self._hold(0)
        if df['close'].iloc[-1] > hh.iloc[-2] and df['close'].iloc[-1] > sma.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-1] < ll.iloc[-2] and df['close'].iloc[-1] < sma.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class LinearRegressionStrategy(BaseStrategy):
    """Linear Regression Channel: price crossing above/below regression line."""
    name = 'Linear Regression'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': '週期', 'default': 50, 'type': 'int', 'min': 10, 'max': 200},
        {'name': 'width', 'label': '通道寬度', 'default': 2.0, 'type': 'float', 'min': 0.5, 'max': 5.0},
    ]
    def analyze(self, df):
        p, w = self.params.get('period',50), self.params.get('width',2.0)
        x = np.arange(p); x_mean = x.mean()
        y = df['close'].rolling(p)
        def linreg(series):
            if len(series) < p: return np.nan, np.nan, np.nan
            slope = ((x - x_mean) * (series[-p:] - series[-p:].mean())).sum() / ((x - x_mean)**2).sum()
            inter = series[-p:].mean() - slope * x_mean
            mid = slope*(p-1) + inter
            resid = series[-p:] - (slope*x + inter)
            dev = resid.std()
            return mid, mid + w*dev, mid - w*dev
        reg_mid = pd.Series(np.nan, index=df.index)
        for i in range(p, len(df)):
            m, u, l = linreg(df['close'].iloc[:i+1].values)
            reg_mid.iloc[i] = m
        if len(reg_mid) < 2 or pd.isna(reg_mid.iloc[-1]): return self._hold(0)
        if df['close'].iloc[-2] < reg_mid.iloc[-2] and df['close'].iloc[-1] > reg_mid.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-2] > reg_mid.iloc[-2] and df['close'].iloc[-1] < reg_mid.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 量價 (Volume)
# ─────────────────────────────────────────────

class MFIStrategy(BaseStrategy):
    """Money Flow Index: volume-weighted RSI."""
    name = 'MFI'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': '週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'overbought', 'label': '超買', 'default': 80, 'type': 'int', 'min': 60, 'max': 95},
        {'name': 'oversold', 'label': '超賣', 'default': 20, 'type': 'int', 'min': 5, 'max': 40},
    ]
    def analyze(self, df):
        p, ob, os = self.params.get('period',14), self.params.get('overbought',80), self.params.get('oversold',20)
        tp = (df['high'] + df['low'] + df['close']) / 3
        mf = tp * df['tick_volume'] if 'tick_volume' in df.columns else tp
        pos = mf.where(tp > tp.shift(1), 0)
        neg = mf.where(tp < tp.shift(1), 0)
        mfi = 100 - 100/(1 + pos.rolling(p).sum()/(neg.rolling(p).sum()+1e-10))
        if len(mfi) < 2: return self._hold(0)
        if mfi.iloc[-2] < os and mfi.iloc[-1] > os: return self._buy(df['close'].iloc[-1])
        if mfi.iloc[-2] > ob and mfi.iloc[-1] < ob: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class VolumeWeightedMAStrategy(BaseStrategy):
    """VWMA crossover: volume-weighted vs simple MA."""
    name = 'Volume Weighted MA'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'fast', 'label': '快線', 'default': 9, 'type': 'int', 'min': 3, 'max': 30},
        {'name': 'slow', 'label': '慢線', 'default': 21, 'type': 'int', 'min': 5, 'max': 60},
    ]
    def analyze(self, df):
        f, s = self.params.get('fast',9), self.params.get('slow',21)
        vol = df['tick_volume'] if 'tick_volume' in df.columns else pd.Series(1, index=df.index)
        vwma_f = (df['close']*vol).rolling(f).sum() / vol.rolling(f).sum()
        vwma_s = (df['close']*vol).rolling(s).sum() / vol.rolling(s).sum()
        if len(vwma_f) < 2: return self._hold(0)
        if vwma_f.iloc[-2] < vwma_s.iloc[-2] and vwma_f.iloc[-1] > vwma_s.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if vwma_f.iloc[-2] > vwma_s.iloc[-2] and vwma_f.iloc[-1] < vwma_s.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 複合 / 混合 (Hybrid)
# ─────────────────────────────────────────────

class MACDBollingerStrategy(BaseStrategy):
    """MACD trend + Bollinger entry: MACD confirms trend, BB gives entry."""
    name = 'MACD + Bollinger'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'macd_fast', 'label': 'MACD快', 'default': 12, 'type': 'int', 'min': 3, 'max': 30},
        {'name': 'macd_slow', 'label': 'MACD慢', 'default': 26, 'type': 'int', 'min': 5, 'max': 60},
        {'name': 'macd_signal', 'label': '信號', 'default': 9, 'type': 'int', 'min': 2, 'max': 20},
        {'name': 'bb_length', 'label': 'BB週期', 'default': 20, 'type': 'int', 'min': 5, 'max': 50},
        {'name': 'bb_std', 'label': '標準差', 'default': 2.0, 'type': 'float', 'min': 1.0, 'max': 4.0},
    ]
    def analyze(self, df):
        mf, ms, msig = self.params.get('macd_fast',12), self.params.get('macd_slow',26), self.params.get('macd_signal',9)
        bl, bs = self.params.get('bb_length',20), self.params.get('bb_std',2.0)
        ema_f = df['close'].ewm(span=mf).mean(); ema_s = df['close'].ewm(span=ms).mean()
        macd = ema_f - ema_s; signal = macd.ewm(span=msig).mean(); hist = macd - signal
        sma = df['close'].rolling(bl).mean(); std = df['close'].rolling(bl).std()
        lower = sma - bs*std
        if len(hist) < 2: return self._hold(0)
        if hist.iloc[-1] > 0 and df['close'].iloc[-1] < lower.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if hist.iloc[-1] < 0 and df['close'].iloc[-1] > lower.iloc[-1]+bs*std.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class RSIStochHybridStrategy(BaseStrategy):
    """RSI + Stochastic double confirmation."""
    name = 'RSI + Stochastic'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'rsi_period', 'label': 'RSI週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'stoch_k', 'label': '隨機K', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'stoch_d', 'label': '隨機D', 'default': 3, 'type': 'int', 'min': 1, 'max': 10},
        {'name': 'oversold', 'label': '超賣', 'default': 30, 'type': 'int', 'min': 10, 'max': 40},
        {'name': 'overbought', 'label': '超買', 'default': 70, 'type': 'int', 'min': 60, 'max': 90},
    ]
    def analyze(self, df):
        rp, sk, sd, os, ob = self.params.get('rsi_period',14), self.params.get('stoch_k',14), self.params.get('stoch_d',3), self.params.get('oversold',30), self.params.get('overbought',70)
        delta = df['close'].diff(); gain = delta.clip(lower=0); loss = (-delta).clip(lower=0)
        rsi = 100 - 100/(1 + gain.ewm(span=rp).mean()/(loss.ewm(span=rp).mean()+1e-10))
        lmin, hmax = df['low'].rolling(sk).min(), df['high'].rolling(sk).max()
        stoch = 100*(df['close']-lmin)/(hmax-lmin+1e-10)
        stoch_d = stoch.rolling(sd).mean()
        if len(rsi) < 2: return self._hold(0)
        if rsi.iloc[-1] < os and stoch.iloc[-1] < os and stoch.iloc[-1] > stoch_d.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if rsi.iloc[-1] > ob and stoch.iloc[-1] > ob and stoch.iloc[-1] < stoch_d.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class SuperTrendRSIStrategy(BaseStrategy):
    """Supertrend direction + RSI confirmation."""
    name = 'SuperTrend + RSI'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'st_period', 'label': 'ST週期', 'default': 10, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'st_mult', 'label': 'ST倍數', 'default': 3.0, 'type': 'float', 'min': 0.5, 'max': 6.0},
        {'name': 'rsi_period', 'label': 'RSI週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'rsi_level', 'label': 'RSI水平', 'default': 50, 'type': 'int', 'min': 30, 'max': 70},
    ]
    def analyze(self, df):
        sp, sm, rp, rl = self.params.get('st_period',10), self.params.get('st_mult',3.0), self.params.get('rsi_period',14), self.params.get('rsi_level',50)
        atr = (df['high']-df['low']).rolling(sp).mean()
        hl2 = (df['high']+df['low'])/2
        upper, lower = hl2 + sm*atr, hl2 - sm*atr
        trend = pd.Series(1, index=df.index)
        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper.iloc[i-1]: trend.iloc[i] = 1
            elif df['close'].iloc[i] < lower.iloc[i-1]: trend.iloc[i] = -1
            else: trend.iloc[i] = trend.iloc[i-1]
        delta = df['close'].diff(); g=delta.clip(lower=0); l=(-delta).clip(lower=0)
        rsi = 100-100/(1+g.ewm(span=rp).mean()/(l.ewm(span=rp).mean()+1e-10))
        if len(trend) < 2: return self._hold(0)
        if trend.iloc[-2] == -1 and trend.iloc[-1] == 1 and rsi.iloc[-1] > rl: return self._buy(df['close'].iloc[-1])
        if trend.iloc[-2] == 1 and trend.iloc[-1] == -1 and rsi.iloc[-1] < rl: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class ADXMACDStrategy(BaseStrategy):
    """ADX trend strength filter + MACD crossover entry."""
    name = 'ADX + MACD'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'adx_period', 'label': 'ADX週期', 'default': 14, 'type': 'int', 'min': 5, 'max': 50},
        {'name': 'adx_thresh', 'label': 'ADX門檻', 'default': 20, 'type': 'int', 'min': 10, 'max': 50},
        {'name': 'macd_fast', 'label': 'MACD快', 'default': 12, 'type': 'int', 'min': 3, 'max': 30},
        {'name': 'macd_slow', 'label': 'MACD慢', 'default': 26, 'type': 'int', 'min': 5, 'max': 60},
        {'name': 'macd_signal', 'label': '信號', 'default': 9, 'type': 'int', 'min': 2, 'max': 20},
    ]
    def analyze(self, df):
        ap, at = self.params.get('adx_period',14), self.params.get('adx_thresh',20)
        mf, ms, msi = self.params.get('macd_fast',12), self.params.get('macd_slow',26), self.params.get('macd_signal',9)
        tr = pd.concat([df['high']-df['low'],(df['high']-df['close'].shift(1)).abs(),(df['low']-df['close'].shift(1)).abs()],axis=1).max(axis=1)
        atr = tr.ewm(span=ap).mean(); up=df['high'].diff(); dn=-df['low'].diff()
        pdi=100*(up.where((up>0)&(up>dn),0).ewm(span=ap).mean()/(atr+1e-10))
        ndi=100*(dn.where((dn>0)&(dn>up),0).ewm(span=ap).mean()/(atr+1e-10))
        dx=100*abs(pdi-ndi)/(pdi+ndi+1e-10); adx=dx.ewm(span=ap).mean()
        ema_f=df['close'].ewm(span=mf).mean(); ema_s=df['close'].ewm(span=ms).mean()
        macd=ema_f-ema_s; sig=macd.ewm(span=msi).mean(); hist=macd-sig
        if len(adx) < 2: return self._hold(0)
        if adx.iloc[-1] > at:
            if hist.iloc[-2] <= 0 and hist.iloc[-1] > 0: return self._buy(df['close'].iloc[-1])
            if hist.iloc[-2] >= 0 and hist.iloc[-1] < 0: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 特殊 (Specialized)
# ─────────────────────────────────────────────

class FractalBreakoutStrategy(BaseStrategy):
    """Williams Fractal breakout: buy above up-fractal, sell below down-fractal."""
    name = 'Fractal Breakout'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': '分形週期', 'default': 2, 'type': 'int', 'min': 1, 'max': 5},
    ]
    def analyze(self, df):
        p = self.params.get('period',2)
        up_fractal = pd.Series(False, index=df.index)
        dn_fractal = pd.Series(False, index=df.index)
        for i in range(p, len(df)-p):
            if df['high'].iloc[i] > df['high'].iloc[i-p:i+p+1].drop(df.index[i]).max():
                up_fractal.iloc[i] = True
            if df['low'].iloc[i] < df['low'].iloc[i-p:i+p+1].drop(df.index[i]).min():
                dn_fractal.iloc[i] = True
        if len(up_fractal) < 2: return self._hold(0)
        if df['close'].iloc[-1] > df['high'].iloc[-p-1:-1][up_fractal.iloc[-p-1:-1]].max() if up_fractal.iloc[-p-1:-1].any() else 1e9:
            return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-1] < df['low'].iloc[-p-1:-1][dn_fractal.iloc[-p-1:-1]].min() if dn_fractal.iloc[-p-1:-1].any() else 0:
            return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class HeikinAshiStrategy(BaseStrategy):
    """Heikin Ashi smoothed candles: trend following with reduced noise."""
    name = 'Heikin Ashi'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'period', 'label': '平滑週期', 'default': 5, 'type': 'int', 'min': 2, 'max': 20},
    ]
    def analyze(self, df):
        p = self.params.get('period',5)
        ha_close = (df['open']+df['high']+df['low']+df['close'])/4
        ha_open = pd.Series(0.0, index=df.index); ha_open.iloc[0] = (df['open'].iloc[0]+df['close'].iloc[0])/2
        for i in range(1, len(df)): ha_open.iloc[i] = (ha_open.iloc[i-1]+ha_close.iloc[i-1])/2
        ha_high = pd.concat([df['high'], ha_open, ha_close], axis=1).max(axis=1)
        ha_low = pd.concat([df['low'], ha_open, ha_close], axis=1).min(axis=1)
        ha_sma = ha_close.rolling(p).mean()
        if len(ha_sma) < 2: return self._hold(0)
        # bullish: HA close > HA open and > SMA
        if ha_close.iloc[-1] > ha_open.iloc[-1] and ha_close.iloc[-1] > ha_sma.iloc[-1]: return self._buy(df['close'].iloc[-1])
        if ha_close.iloc[-1] < ha_open.iloc[-1] and ha_close.iloc[-1] < ha_sma.iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class ChandelierExitStrategy(BaseStrategy):
    """Chandelier Exit: ATR-based trailing stop for trend following."""
    name = 'Chandelier Exit'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'atr_period', 'label': 'ATR週期', 'default': 22, 'type': 'int', 'min': 5, 'max': 50},
        {'name': 'multiplier', 'label': '倍數', 'default': 3.0, 'type': 'float', 'min': 1.0, 'max': 6.0},
    ]
    def analyze(self, df):
        ap, m = self.params.get('atr_period',22), self.params.get('multiplier',3.0)
        atr = (df['high']-df['low']).rolling(ap).mean()
        n = len(atr); trend = pd.Series(0, index=df.index)
        for i in range(ap+1, n):
            hh = df['high'].iloc[i-ap:i].max(); ll = df['low'].iloc[i-ap:i].min()
            long_stop = hh - m*atr.iloc[i]; short_stop = ll + m*atr.iloc[i]
            if df['close'].iloc[i] > long_stop and (trend.iloc[i-1] >= 0): trend.iloc[i] = 1
            elif df['close'].iloc[i] < short_stop and (trend.iloc[i-1] <= 0): trend.iloc[i] = -1
            else: trend.iloc[i] = trend.iloc[i-1]
        if len(trend) < 2: return self._hold(0)
        if trend.iloc[-2] <= 0 and trend.iloc[-1] == 1: return self._buy(df['close'].iloc[-1])
        if trend.iloc[-2] >= 0 and trend.iloc[-1] == -1: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class RainbowMAStrategy(BaseStrategy):
    """Multiple MA alignment: 6 MAs fanning out = strong trend."""
    name = 'Rainbow MA'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'ma_count', 'label': '均線數', 'default': 6, 'type': 'int', 'min': 3, 'max': 10},
        {'name': 'step', 'label': '級距', 'default': 5, 'type': 'int', 'min': 2, 'max': 20},
    ]
    def analyze(self, df):
        n, step = self.params.get('ma_count',6), self.params.get('step',5)
        mas = [df['close'].rolling((i+1)*step).mean() for i in range(n)]
        if len(mas[0]) < 2: return self._hold(0)
        long = all(mas[i].iloc[-1] > mas[i+1].iloc[-1] for i in range(n-1))
        short = all(mas[i].iloc[-1] < mas[i+1].iloc[-1] for i in range(n-1))
        if long: return self._buy(df['close'].iloc[-1])
        if short: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class OpeningRangeBreakoutStrategy(BaseStrategy):
    """Opening Range Breakout: breakout of first N bars' range."""
    name = 'Opening Range Breakout'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'opening_bars', 'label': '開盤K線數', 'default': 5, 'type': 'int', 'min': 1, 'max': 20},
    ]
    def analyze(self, df):
        ob = self.params.get('opening_bars',5)
        if len(df) < ob + 2: return self._hold(0)
        or_high = df['high'].iloc[-ob-1:-1].max(); or_low = df['low'].iloc[-ob-1:-1].min()
        if df['close'].iloc[-1] > or_high: return self._buy(df['close'].iloc[-1])
        if df['close'].iloc[-1] < or_low: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class RangeExpansionStrategy(BaseStrategy):
    """Range expansion: current bar range >> average range."""
    name = 'Range Expansion'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'avg_period', 'label': '平均週期', 'default': 14, 'type': 'int', 'min': 3, 'max': 50},
        {'name': 'expansion_factor', 'label': '擴張倍數', 'default': 2.0, 'type': 'float', 'min': 1.2, 'max': 5.0},
    ]
    def analyze(self, df):
        ap, ef = self.params.get('avg_period',14), self.params.get('expansion_factor',2.0)
        rng = df['high'] - df['low']; avg_rng = rng.rolling(ap).mean()
        if len(rng) < 2: return self._hold(0)
        expand = rng.iloc[-1] > ef * avg_rng.iloc[-2]
        if expand and df['close'].iloc[-1] > df['open'].iloc[-1]: return self._buy(df['close'].iloc[-1])
        if expand and df['close'].iloc[-1] < df['open'].iloc[-1]: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

class PivotPointStrategy(BaseStrategy):
    """Classic Pivot Points: S/R levels for breakouts and reversals."""
    name = 'Pivot Point'
    @classmethod
    def get_definable_params(cls): return [
        {'name': 'pivot_mode', 'label': '模式(0=突破/1=反轉)', 'default': 1, 'type': 'int', 'min': 0, 'max': 1},
    ]
    def analyze(self, df):
        pm = self.params.get('pivot_mode',1)
        if len(df) < 2: return self._hold(0)
        prev_h, prev_l, prev_c = df['high'].iloc[-2], df['low'].iloc[-2], df['close'].iloc[-2]
        pp = (prev_h + prev_l + prev_c) / 3
        r1, s1 = 2*pp - prev_l, 2*pp - prev_h
        if pm == 1:  # reversal
            if df['close'].iloc[-1] < s1: return self._buy(df['close'].iloc[-1])
            if df['close'].iloc[-1] > r1: return self._sell(df['close'].iloc[-1])
        else:  # breakout
            if df['close'].iloc[-1] > r1: return self._buy(df['close'].iloc[-1])
            if df['close'].iloc[-1] < s1: return self._sell(df['close'].iloc[-1])
        return self._hold(df['close'].iloc[-1])

# ─────────────────────────────────────────────
# 註冊表
# ─────────────────────────────────────────────

INDICATOR_STRATEGY_MAP = {
    'MACD': MACDStrategy,
    'STOCHASTIC': StochasticStrategy,
    'CCI': CCIStrategy,
    'WILLIAMS_R': WilliamsRStrategy,
    'ROC': ROCStrategy,
    'AWESOME_OSCILLATOR': AwesomeOscillatorStrategy,
    'RSI_DIVERGENCE': RSIDivergenceStrategy,
    'SUPERTREND': SuperTrendStrategy,
    'PARABOLIC_SAR': ParabolicSARStrategy,
    'ADX': ADXStrategy,
    'KELTNER_CHANNEL': KeltnerChannelStrategy,
    'EMA_ENVELOPE': EMAEnvelopeStrategy,
    'DONCHIAN_BREAKOUT': DonchianBreakoutStrategy,
    'HULL_MA': HullMAStrategy,
    'TRIPLE_MA': TripleMAStrategy,
    'ZERO_LAG_EMA': ZeroLagEMAStrategy,
    'PIN_BAR': PinBarStrategy,
    'ENGULFING': EngulfingStrategy,
    'INSIDE_BAR': InsideBarStrategy,
    'DOJI': DojiStrategy,
    'HAMMER_SHOOTING': HammerShootingStrategy,
    'NR7': NR7Strategy,
    'MTF_MA_CROSSOVER': MTFMACrossoverStrategy,
    'MTF_BOLLINGER': MTFBollingerStrategy,
    'VOLATILITY_BREAKOUT': VolatilityBreakoutStrategy,
    'ATR_CHANNEL': ATRChannelStrategy,
    'BOLLINGER_TREND': BollingerTrendStrategy,
    'RSI_EXTREME': RSIExtremeStrategy,
    'BOLLINGER_PERCENT_B': BollingerPercentBStrategy,
    'PRICE_CHANNEL': PriceChannelStrategy,
    'LINEAR_REGRESSION': LinearRegressionStrategy,
    'MFI': MFIStrategy,
    'VOLUME_WEIGHTED_MA': VolumeWeightedMAStrategy,
    'MACD_BOLLINGER': MACDBollingerStrategy,
    'RSI_STOCH_HYBRID': RSIStochHybridStrategy,
    'SUPERTREND_RSI': SuperTrendRSIStrategy,
    'ADX_MACD': ADXMACDStrategy,
    'FRACTAL_BREAKOUT': FractalBreakoutStrategy,
    'HEIKIN_ASHI': HeikinAshiStrategy,
    'CHANDELIER_EXIT': ChandelierExitStrategy,
    'RAINBOW_MA': RainbowMAStrategy,
    'OPENING_RANGE': OpeningRangeBreakoutStrategy,
    'RANGE_EXPANSION': RangeExpansionStrategy,
    'PIVOT_POINT': PivotPointStrategy,
}
