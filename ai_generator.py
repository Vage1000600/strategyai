"""
StrategyAI - Enhanced Local AI Strategy Generator
Features:
- 20+ strategy templates with composition support
- Ollama integration for local LLM generation
- Smart template matching with AND/OR logic
"""

import json
import os
from typing import Optional, Dict, List, Any
import re


# ============================================================================
# STRATEGY TEMPLATES (20+ templates with composition)
# ============================================================================

STRATEGY_TEMPLATES = {
    # Basic Indicators
    'rsi_oversold': {
        'name': 'RSI Oversold/Overbought',
        'description': 'Buy when RSI is oversold (<30), sell when overbought (>70)',
        'indicators': ['RSI'],
        'code': '''import numpy as np

def compute_rsi(close, period=14):
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.convolve(gain, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(loss, np.ones(period)/period, mode='valid')
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return np.concatenate([[50]*period, rsi])

def strategy(data):
    close = data['close']
    rsi = compute_rsi(close, 14)
    buy_signals = rsi < 30
    sell_signals = rsi > 70
    return buy_signals, sell_signals'''
    },
    
    'rsi_divergence': {
        'name': 'RSI Divergence',
        'description': 'Buy when price makes lower low but RSI makes higher low (bullish divergence)',
        'indicators': ['RSI'],
        'code': '''import numpy as np

def compute_rsi(close, period=14):
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.convolve(gain, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(loss, np.ones(period)/period, mode='valid')
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return np.concatenate([[50]*period, rsi])

def detect_divergence(price, rsi, lookback=5):
    """Detect bullish/bearish divergence"""
    divergence = np.zeros(len(price), dtype=int)  # -1 bearish, 0 none, 1 bullish
    
    for i in range(lookback, len(price) - lookback):
        # Check if price made lower low
        price_lower_low = (price[i] < price[i-lookback] and 
                          price[i] < price[i+lookback])
        # Check if RSI made higher low
        rsi_higher_low = (rsi[i] > rsi[i-lookback] and 
                         rsi[i] < rsi[i+lookback])
        
        if price_lower_low and rsi_higher_low:
            divergence[i] = 1  # Bullish divergence
        
        # Bearish divergence
        price_higher_high = (price[i] > price[i-lookback] and 
                            price[i] > price[i+lookback])
        rsi_lower_high = (rsi[i] < rsi[i-lookback] and 
                         rsi[i] > rsi[i+lookback])
        
        if price_higher_high and rsi_lower_high:
            divergence[i] = -1  # Bearish divergence
    
    return divergence

def strategy(data):
    close = data['close']
    rsi = compute_rsi(close, 14)
    divergence = detect_divergence(close, rsi, 5)
    
    buy_signals = divergence == 1
    sell_signals = divergence == -1
    
    return buy_signals, sell_signals'''
    },
    
    'macd_crossover': {
        'name': 'MACD Crossover',
        'description': 'Buy when MACD crosses above signal line, sell when it crosses below',
        'indicators': ['MACD', 'EMA'],
        'code': '''import numpy as np

def compute_ema(data, period):
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

def strategy(data):
    close = data['close']
    ema12 = compute_ema(close, 12)
    ema26 = compute_ema(close, 26)
    macd = ema12 - ema26
    signal = compute_ema(macd, 9)
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    buy_signals[1:] = (macd[1:] > signal[1:]) & (macd[:-1] <= signal[:-1])
    sell_signals[1:] = (macd[1:] < signal[1:]) & (macd[:-1] >= signal[:-1])
    
    return buy_signals, sell_signals'''
    },
    
    'macd_histogram': {
        'name': 'MACD Histogram',
        'description': 'Buy when MACD histogram turns positive, sell when it turns negative',
        'indicators': ['MACD'],
        'code': '''import numpy as np

def compute_ema(data, period):
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

def strategy(data):
    close = data['close']
    ema12 = compute_ema(close, 12)
    ema26 = compute_ema(close, 26)
    macd = ema12 - ema26
    signal = compute_ema(macd, 9)
    histogram = macd - signal
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    
    buy_signals[1:] = (histogram[1:] > 0) & (histogram[:-1] <= 0)
    sell_signals[1:] = (histogram[1:] < 0) & (histogram[:-1] >= 0)
    
    return buy_signals, sell_signals'''
    },
    
    'macd_rsi_combo': {
        'name': 'MACD + RSI Combo',
        'description': 'Buy when MACD crosses above signal AND RSI < 50, sell when MACD crosses below OR RSI > 70',
        'indicators': ['MACD', 'RSI'],
        'code': '''import numpy as np

def compute_ema(data, period):
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

def compute_rsi(close, period=14):
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.convolve(gain, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(loss, np.ones(period)/period, mode='valid')
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return np.concatenate([[50]*period, rsi])

def strategy(data):
    close = data['close']
    ema12 = compute_ema(close, 12)
    ema26 = compute_ema(close, 26)
    macd = ema12 - ema26
    signal = compute_ema(macd, 9)
    rsi = compute_rsi(close, 14)
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    
    # MACD crossover
    macd_buy = (macd[1:] > signal[1:]) & (macd[:-1] <= signal[:-1])
    macd_sell = (macd[1:] < signal[1:]) & (macd[:-1] >= signal[:-1])
    
    # RSI filter
    rsi_low = rsi[1:] < 50
    rsi_high = rsi[1:] > 70
    
    # Combine with AND
    buy_signals[1:] = macd_buy & rsi_low
    sell_signals[1:] = macd_sell | rsi_high
    
    return buy_signals, sell_signals'''
    },
    
    # Moving Averages
    'golden_cross': {
        'name': 'Golden Cross',
        'description': 'Buy when 50 EMA crosses above 200 EMA, sell when it crosses below',
        'indicators': ['EMA'],
        'code': '''import numpy as np

def compute_ema(data, period):
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

def strategy(data):
    close = data['close']
    ema50 = compute_ema(close, 50)
    ema200 = compute_ema(close, 200)
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    buy_signals[1:] = (ema50[1:] > ema200[1:]) & (ema50[:-1] <= ema200[:-1])
    sell_signals[1:] = (ema50[1:] < ema200[1:]) & (ema50[:-1] >= ema200[:-1])
    
    return buy_signals, sell_signals'''
    },
    
    'triple_ema': {
        'name': 'Triple EMA Crossover',
        'description': 'Buy when 8 EMA crosses above 21 EMA crosses above 50 EMA, sell when reverse',
        'indicators': ['EMA'],
        'code': '''import numpy as np

def compute_ema(data, period):
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

def strategy(data):
    close = data['close']
    ema8 = compute_ema(close, 8)
    ema21 = compute_ema(close, 21)
    ema50 = compute_ema(close, 50)
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    
    # Bullish: 8 > 21 > 50
    bullish = (ema8[1:] > ema21[1:]) & (ema21[1:] > ema50[1:])
    bearish = (ema8[1:] < ema21[1:]) & (ema21[1:] < ema50[1:])
    
    # Crossover detection
    prev_bullish = (ema8[:-1] < ema21[:-1]) | (ema21[:-1] < ema50[:-1])
    prev_bearish = (ema8[:-1] > ema21[:-1]) | (ema21[:-1] > ema50[:-1])
    
    buy_signals[1:] = bullish & prev_bearish
    sell_signals[1:] = bearish & prev_bullish
    
    return buy_signals, sell_signals'''
    },
    
    'sma_crossover': {
        'name': 'SMA Crossover',
        'description': 'Buy when 20 SMA crosses above 50 SMA, sell when it crosses below',
        'indicators': ['SMA'],
        'code': '''import numpy as np

def compute_sma(data, period):
    return np.convolve(data, np.ones(period)/period, mode='full')[:len(data)]

def strategy(data):
    close = data['close']
    sma20 = compute_sma(close, 20)
    sma50 = compute_sma(close, 50)
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    buy_signals[1:] = (sma20[1:] > sma50[1:]) & (sma20[:-1] <= sma50[:-1])
    sell_signals[1:] = (sma20[1:] < sma50[1:]) & (sma20[:-1] >= sma50[:-1])
    
    return buy_signals, sell_signals'''
    },
    
    # Volatility
    'bollinger_breakout': {
        'name': 'Bollinger Band Breakout',
        'description': 'Buy when price breaks above upper Bollinger Band, sell at middle band',
        'indicators': ['Bollinger Bands'],
        'code': '''import numpy as np

def compute_bollinger(close, period=20, std_dev=2):
    sma = np.convolve(close, np.ones(period)/period, mode='full')[:len(close)]
    std = np.zeros(len(close))
    for i in range(period-1, len(close)):
        std[i] = np.std(close[i-period+1:i+1])
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

def strategy(data):
    close = data['close']
    upper, middle, lower = compute_bollinger(close, 20, 2)
    
    buy_signals = close > upper
    sell_signals = close < middle
    
    return buy_signals, sell_signals'''
    },
    
    'bollinger_rsi': {
        'name': 'Bollinger + RSI',
        'description': 'Buy when price touches lower Bollinger Band AND RSI < 30',
        'indicators': ['Bollinger Bands', 'RSI'],
        'code': '''import numpy as np

def compute_bollinger(close, period=20, std_dev=2):
    sma = np.convolve(close, np.ones(period)/period, mode='full')[:len(close)]
    std = np.zeros(len(close))
    for i in range(period-1, len(close)):
        std[i] = np.std(close[i-period+1:i+1])
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

def compute_rsi(close, period=14):
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.convolve(gain, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(loss, np.ones(period)/period, mode='valid')
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return np.concatenate([[50]*period, rsi])

def strategy(data):
    close = data['close']
    upper, middle, lower = compute_bollinger(close, 20, 2)
    rsi = compute_rsi(close, 14)
    
    # Buy when both conditions met
    bb_touch = close <= lower
    rsi_oversold = rsi < 30
    buy_signals = bb_touch & rsi_oversold
    
    # Sell at middle band or overbought
    sell_signals = (close < middle) | (rsi > 70)
    
    return buy_signals, sell_signals'''
    },
    
    'keltner_breakout': {
        'name': 'Keltner Channel Breakout',
        'description': 'Buy when price breaks above Keltner Channel, sell at middle line',
        'indicators': ['Keltner Channel', 'ATR'],
        'code': '''import numpy as np

def compute_ema(data, period):
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

def compute_atr(high, low, close, period=14):
    """Calculate ATR"""
    high_low = high - low
    high_close = np.abs(high - np.concatenate([[close[0]], close[:-1]]))
    low_close = np.abs(low - np.concatenate([[close[0]], close[:-1]]))
    ranges = np.maximum(high_low, high_close, low_close)
    atr = np.convolve(ranges, np.ones(period)/period, mode='valid')
    return np.concatenate([np.zeros(period-1), atr])

def strategy(data):
    close = data['close']
    high = data['high']
    low = data['low']
    
    ema = compute_ema(close, 20)
    atr = compute_atr(high, low, close, 14)
    
    upper = ema + 2 * atr
    lower = ema - 2 * atr
    
    buy_signals = close > upper
    sell_signals = close < ema
    
    return buy_signals, sell_signals'''
    },
    
    # Volume
    'volume_spike': {
        'name': 'Volume Spike',
        'description': 'Buy when volume is 2x average AND price closes up',
        'indicators': ['Volume', 'SMA'],
        'code': '''import numpy as np

def compute_sma(data, period):
    return np.convolve(data, np.ones(period)/period, mode='full')[:len(data)]

def strategy(data):
    volume = data['volume']
    close = data['close']
    
    avg_volume = compute_sma(volume, 20)
    volume_spike = volume > 2 * avg_volume
    price_up = close > np.concatenate([[close[0]], close[:-1]])
    
    buy_signals = volume_spike & price_up
    sell_signals = volume_spike & ~price_up
    
    return buy_signals, sell_signals'''
    },
    
    'obv_trend': {
        'name': 'OBV Trend',
        'description': 'Buy when OBV makes new high while price is flat (accumulation)',
        'indicators': ['OBV'],
        'code': '''import numpy as np

def compute_obv(close, volume):
    obv = np.zeros(len(close))
    obv[0] = 0
    for i in range(1, len(close)):
        if close[i] > close[i-1]:
            obv[i] = obv[i-1] + volume[i]
        elif close[i] < close[i-1]:
            obv[i] = obv[i-1] - volume[i]
        else:
            obv[i] = obv[i-1]
    return obv

def strategy(data):
    close = data['close']
    volume = data['volume']
    obv = compute_obv(close, volume)
    
    # Find OBV highs
    obv_high = obv > np.maximum.accumulate(obv[:-1])
    
    # Price flat (within 1% range)
    price_flat = np.abs(close - np.concatenate([[close[0]], close[:-1]])) < 0.01 * close
    
    buy_signals = obv_high & price_flat
    sell_signals = obv < np.minimum.accumulate(obv[:-1])
    
    return buy_signals, sell_signals'''
    },
    
    # Trend Following
    'adx_trend': {
        'name': 'ADX Trend Filter',
        'description': 'Only take MACD signals when ADX > 25 (strong trend)',
        'indicators': ['MACD', 'ADX'],
        'code': '''import numpy as np

def compute_ema(data, period):
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

def compute_adx(high, low, close, period=14):
    """Calculate ADX"""
    plus_dm = np.diff(high)
    minus_dm = -np.diff(low)
    
    plus_di = 100 * np.convolve(np.where(plus_dm > minus_dm & plus_dm > 0, plus_dm, 0), 
                                np.ones(period)/period, mode='valid')
    minus_di = 100 * np.convolve(np.where(minus_dm > plus_dm & minus_dm > 0, minus_dm, 0), 
                                np.ones(period)/period, mode='valid')
    
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = np.convolve(dx, np.ones(period)/period, mode='valid')
    
    return np.concatenate([np.zeros(period*2-2), adx])

def strategy(data):
    close = data['close']
    high = data['high']
    low = data['low']
    
    ema12 = compute_ema(close, 12)
    ema26 = compute_ema(close, 26)
    macd = ema12 - ema26
    signal = compute_ema(macd, 9)
    adx = compute_adx(high, low, close, 14)
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    
    # MACD crossover
    macd_buy = (macd[1:] > signal[1:]) & (macd[:-1] <= signal[:-1])
    macd_sell = (macd[1:] < signal[1:]) & (macd[:-1] >= signal[:-1])
    
    # Only trade when ADX > 25 (strong trend)
    strong_trend = adx[1:] > 25
    
    buy_signals[1:] = macd_buy & strong_trend
    sell_signals[1:] = macd_sell & strong_trend
    
    return buy_signals, sell_signals'''
    },
    
    'ichimoku': {
        'name': 'Ichimoku Cloud',
        'description': 'Buy when price is above cloud and Tenkan crosses above Kijun',
        'indicators': ['Ichimoku'],
        'code': '''import numpy as np

def compute_ichimoku(high, low, close, period=9):
    """Calculate Ichimoku components"""
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    tenkan_high = np.maximum.accumulate(high[:period])
    tenkan_low = np.minimum.accumulate(low[:period])
    tenkan = (tenkan_high + tenkan_low) / 2
    
    # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    kijun_high = np.maximum.accumulate(high[:26])
    kijun_low = np.minimum.accumulate(low[:26])
    kijun = (kijun_high + kijun_low) / 2
    
    # Senkou Span A: (Tenkan + Kijun) / 2, shifted 26 periods
    senkou_a = (tenkan + kijun) / 2
    
    # Senkou Span B: (52-period high + 52-period low) / 2
    senkou_b_high = np.maximum.accumulate(high[:52])
    senkou_b_low = np.minimum.accumulate(low[:52])
    senkou_b = (senkou_b_high + senkou_b_low) / 2
    
    return tenkan, kijun, senkou_a, senkou_a, senkou_b

def strategy(data):
    close = data['close']
    high = data['high']
    low = data['low']
    
    tenkan, kijun, senkou_a1, senkou_a2, senkou_b = compute_ichimoku(high, low, close)
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    
    # Tenkan crosses above Kijun
    tenkan_cross = (tenkan[1:] > kijun[1:]) & (tenkan[:-1] <= kijun[:-1])
    
    # Price above cloud (Senkou A > Senkou B)
    above_cloud = close > senkou_a
    
    buy_signals[1:] = tenkan_cross & above_cloud
    sell_signals[1:] = ~above_cloud
    
    return buy_signals, sell_signals'''
    },
    
    # Mean Reversion
    'vwap_reversion': {
        'name': 'VWAP Mean Reversion',
        'description': 'Buy when price is 2% below VWAP, sell at VWAP',
        'indicators': ['VWAP'],
        'code': '''import numpy as np

def compute_vwap(high, low, close, volume):
    """Calculate VWAP"""
    typical_price = (high + low + close) / 3
    vwap = np.convolve(typical_price * volume, np.ones(len(volume))/np.sum(volume), mode='full')[:len(volume)]
    return vwap

def strategy(data):
    close = data['close']
    high = data['high']
    low = data['low']
    volume = data['volume']
    
    vwap = compute_vwap(high, low, close, volume)
    
    # Buy when 2% below VWAP
    buy_signals = close < vwap * 0.98
    
    # Sell at VWAP or above
    sell_signals = close >= vwap
    
    return buy_signals, sell_signals'''
    },
    
    'zscore_reversion': {
        'name': 'Z-Score Mean Reversion',
        'description': 'Buy when price is 2 standard deviations below 20-day mean, sell at mean',
        'indicators': ['Z-Score'],
        'code': '''import numpy as np

def compute_zscore(close, period=20):
    """Calculate Z-score of price"""
    mean = np.convolve(close, np.ones(period)/period, mode='valid')
    std = np.zeros(len(close))
    for i in range(period-1, len(close)):
        std[i] = np.std(close[i-period+1:i+1])
    zscore = (close[period-1:] - mean) / (std + 1e-10)
    return np.concatenate([np.zeros(period-1), zscore])

def strategy(data):
    close = data['close']
    zscore = compute_zscore(close, 20)
    
    # Buy when 2 std below mean
    buy_signals = zscore < -2
    
    # Sell at mean (zscore between -0.5 and 0.5)
    sell_signals = (zscore > -0.5) & (zscore < 0.5)
    
    return buy_signals, sell_signals'''
    },
    
    # Support/Resistance
    'support_resistance': {
        'name': 'Support/Resistance',
        'description': 'Buy at support (recent low), sell at resistance (recent high)',
        'indicators': ['Support', 'Resistance'],
        'code': '''import numpy as np

def find_support_resistance(low, high, lookback=20):
    """Find support and resistance levels"""
    support = np.zeros(len(low))
    resistance = np.zeros(len(high))
    
    for i in range(lookback, len(low)):
        support[i] = np.min(low[i-lookback:i])
        resistance[i] = np.max(high[i-lookback:i])
    
    return support, resistance

def strategy(data):
    close = data['close']
    low = data['low']
    high = data['high']
    
    support, resistance = find_support_resistance(low, high, 20)
    
    # Buy near support (within 1%)
    buy_signals = close <= support * 1.01
    
    # Sell near resistance (within 1%)
    sell_signals = close >= resistance * 0.99
    
    return buy_signals, sell_signals'''
    },
    
    # Candlestick
    'candlestick_patterns': {
        'name': 'Candlestick Patterns',
        'description': 'Buy on bullish engulfing, sell on bearish engulfing',
        'indicators': ['Candlestick'],
        'code': '''import numpy as np

def detect_engulfing(open, close, lookback=1):
    """Detect engulfing patterns"""
    bullish = np.zeros(len(open), dtype=bool)
    bearish = np.zeros(len(open), dtype=bool)
    
    for i in range(lookback, len(open)):
        # Bullish engulfing
        prev_bearish = open[i-1] > close[i-1]
        current_bullish = open[i] < close[i]
        engulfing = open[i] < open[i-1] and close[i] > close[i-1]
        
        if prev_bearish and current_bullish and engulfing:
            bullish[i] = True
        
        # Bearish engulfing
        prev_bullish = open[i-1] < close[i-1]
        current_bearish = open[i] > close[i]
        engulfing = open[i] > open[i-1] and close[i] < close[i-1]
        
        if prev_bullish and current_bearish and engulfing:
            bearish[i] = True
    
    return bullish, bearish

def strategy(data):
    open = data['open']
    close = data['close']
    
    bullish, bearish = detect_engulfing(open, close)
    
    return bullish, bearish'''
    },
    
    # Risk Management
    'atr_stop_loss': {
        'name': 'ATR Trailing Stop',
        'description': 'Use ATR-based trailing stop to exit positions',
        'indicators': ['ATR'],
        'code': '''import numpy as np

def compute_atr(high, low, close, period=14):
    """Calculate ATR"""
    high_low = high - low
    high_close = np.abs(high - np.concatenate([[close[0]], close[:-1]]))
    low_close = np.abs(low - np.concatenate([[close[0]], close[:-1]]))
    ranges = np.maximum(high_low, high_close, low_close)
    atr = np.convolve(ranges, np.ones(period)/period, mode='valid')
    return np.concatenate([np.zeros(period-1), atr])

def strategy(data):
    close = data['close']
    high = data['high']
    low = data['low']
    
    atr = compute_atr(high, low, close, 14)
    
    # Simple entry on any day (for demonstration)
    buy_signals = np.ones(len(close), dtype=bool)
    buy_signals[:14] = False  # Skip initial period
    
    # Trailing stop: exit if price drops 2x ATR from high since entry
    sell_signals = np.zeros(len(close), dtype=bool)
    highest_price = close[0]
    
    for i in range(1, len(close)):
        highest_price = max(highest_price, close[i])
        if close[i] < highest_price - 2 * atr[i]:
            sell_signals[i] = True
            highest_price = close[i]
    
    return buy_signals, sell_signals'''
    },
    
    'volume_price_trend': {
        'name': 'Volume Price Trend',
        'description': 'Buy when price and volume both increase',
        'indicators': ['Volume', 'Price'],
        'code': '''import numpy as np

def strategy(data):
    close = data['close']
    volume = data['volume']
    
    price_up = close > np.concatenate([[close[0]], close[:-1]])
    volume_up = volume > np.convolve(volume, np.ones(5)/5, mode='valid')[:-1]
    
    buy_signals = price_up & volume_up
    sell_signals = ~price_up
    
    return buy_signals, sell_signals'''
    },
}

# ============================================================================
# TEMPLATE COMPOSITION ENGINE
# ============================================================================

class TemplateComposer:
    """
    Composes multiple templates based on user prompt
    Supports AND, OR, and NOT logic
    """
    
    def __init__(self):
        self.templates = STRATEGY_TEMPLATES
    
    def detect_conditions(self, user_input: str) -> Dict:
        """
        Analyze user input and detect which templates/conditions to use
        """
        user_input_lower = user_input.lower()
        conditions = {
            'templates': [],
            'logic': 'AND',  # AND, OR, NOT
            'filters': []
        }
        
        # Detect indicator mentions
        indicators = []
        if 'rsi' in user_input_lower:
            indicators.append('rsi')
        if 'macd' in user_input_lower:
            indicators.append('macd')
        if 'ema' in user_input_lower or 'golden' in user_input_lower:
            indicators.append('ema')
        if 'bollinger' in user_input_lower or 'band' in user_input_lower:
            indicators.append('bollinger')
        if 'volume' in user_input_lower:
            indicators.append('volume')
        if 'atr' in user_input_lower:
            indicators.append('atr')
        if 'adx' in user_input_lower:
            indicators.append('adx')
        if 'ichimoku' in user_input_lower:
            indicators.append('ichimoku')
        if 'vwap' in user_input_lower:
            indicators.append('vwap')
        if 'support' in user_input_lower or 'resistance' in user_input_lower:
            indicators.append('support_resistance')
        if 'engulfing' in user_input_lower or 'candle' in user_input_lower:
            indicators.append('candlestick')
        if 'divergence' in user_input_lower:
            indicators.append('rsi_divergence')
        
        # Map indicators to templates
        indicator_to_template = {
            'rsi': ['rsi_oversold', 'rsi_divergence'],
            'macd': ['macd_crossover', 'macd_histogram', 'macd_rsi_combo'],
            'ema': ['golden_cross', 'triple_ema'],
            'bollinger': ['bollinger_breakout', 'bollinger_rsi'],
            'volume': ['volume_spike', 'volume_price_trend'],
            'atr': ['atr_stop_loss', 'keltner_breakout'],
            'adx': ['adx_trend'],
            'ichimoku': ['ichimoku'],
            'vwap': ['vwap_reversion'],
            'support_resistance': ['support_resistance'],
            'candlestick': ['candlestick_patterns'],
        }
        
        for indicator in indicators:
            if indicator in indicator_to_template:
                conditions['templates'].extend(indicator_to_template[indicator])
        
        # Detect logic operators
        if 'and' in user_input_lower:
            conditions['logic'] = 'AND'
        elif 'or' in user_input_lower:
            conditions['logic'] = 'OR'
        
        # Remove duplicates
        conditions['templates'] = list(set(conditions['templates']))
        
        return conditions
    
    def compose_strategy(self, conditions: Dict, user_input: str) -> str:
        """
        Compose a strategy from multiple templates
        """
        if not conditions['templates']:
            # No templates detected, return default
            return self._get_default_template()
        
        if len(conditions['templates']) == 1:
            # Single template
            template_name = conditions['templates'][0]
            return self.templates[template_name]['code']
        
        # Multiple templates - compose them
        return self._compose_multiple(conditions['templates'], conditions['logic'])
    
    def _get_default_template(self) -> str:
        """Return default SMA crossover strategy"""
        return STRATEGY_TEMPLATES['sma_crossover']['code']
    
    def _compose_multiple(self, templates: List[str], logic: str) -> str:
        """
        Compose multiple templates with AND/OR logic
        This is a simplified composition - combines indicators
        """
        # Get all unique indicators from selected templates
        indicators = set()
        for template_name in templates:
            if template_name in self.templates:
                indicators.update(self.templates[template_name]['indicators'])
        
        # Build composite code
        code_parts = []
        code_parts.append('import numpy as np\n')
        code_parts.append('import numpy as np\n\n')
        
        # Add helper functions
        if 'EMA' in indicators or 'EMA' in str(templates):
            code_parts.append('''def compute_ema(data, period):
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

''')
        
        if 'RSI' in indicators:
            code_parts.append('''def compute_rsi(close, period=14):
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.convolve(gain, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(loss, np.ones(period)/period, mode='valid')
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return np.concatenate([[50]*period, rsi])

''')
        
        if 'Bollinger' in indicators:
            code_parts.append('''def compute_bollinger(close, period=20, std_dev=2):
    sma = np.convolve(close, np.ones(period)/period, mode='full')[:len(close)]
    std = np.zeros(len(close))
    for i in range(period-1, len(close)):
        std[i] = np.std(close[i-period+1:i+1])
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

''')
        
        # Strategy function
        code_parts.append('def strategy(data):\n')
        code_parts.append('    close = data[\'close\']\n')
        
        # Add indicator calculations
        if 'EMA' in indicators:
            code_parts.append('    ema50 = compute_ema(close, 50)\n')
            code_parts.append('    ema200 = compute_ema(close, 200)\n')
        
        if 'RSI' in indicators:
            code_parts.append('    rsi = compute_rsi(close, 14)\n')
        
        if 'Bollinger' in indicators:
            code_parts.append('    upper, middle, lower = compute_bollinger(close, 20, 2)\n')
        
        # Signal generation (simplified composition)
        code_parts.append('    buy_signals = np.zeros(len(close), dtype=bool)\n')
        code_parts.append('    sell_signals = np.zeros(len(close), dtype=bool)\n')
        
        # Add signals based on templates
        if 'golden_cross' in templates or 'triple_ema' in templates:
            code_parts.append('    buy_signals[1:] = (ema50[1:] > ema200[1:]) & (ema50[:-1] <= ema200[:-1])\n')
            code_parts.append('    sell_signals[1:] = (ema50[1:] < ema200[1:]) & (ema50[:-1] >= ema200[:-1])\n')
        
        if 'macd_crossover' in templates or 'macd_histogram' in templates:
            code_parts.append('    ema12 = compute_ema(close, 12)\n')
            code_parts.append('    ema26 = compute_ema(close, 26)\n')
            code_parts.append('    macd = ema12 - ema26\n')
            code_parts.append('    signal = compute_ema(macd, 9)\n')
            code_parts.append('    macd_buy = (macd[1:] > signal[1:]) & (macd[:-1] <= signal[:-1])\n')
            code_parts.append('    macd_sell = (macd[1:] < signal[1:]) & (macd[:-1] >= signal[:-1])\n')
            if logic == 'AND':
                code_parts.append('    buy_signals = buy_signals & macd_buy\n')
                code_parts.append('    sell_signals = sell_signals | macd_sell\n')
            else:
                code_parts.append('    buy_signals = buy_signals | macd_buy\n')
                code_parts.append('    sell_signals = sell_signals | macd_sell\n')
        
        if 'rsi_oversold' in templates:
            code_parts.append('    buy_signals = buy_signals & (rsi < 30)\n')
            code_parts.append('    sell_signals = sell_signals | (rsi > 70)\n')
        
        if 'bollinger_breakout' in templates:
            code_parts.append('    buy_signals = buy_signals | (close > upper)\n')
            code_parts.append('    sell_signals = sell_signals | (close < middle)\n')
        
        code_parts.append('    \n')
        code_parts.append('    return buy_signals, sell_signals\n')
        
        return ''.join(code_parts)


# ============================================================================
# OLLAMA INTEGRATION
# ============================================================================

def generate_with_ollama(prompt: str, model: str = 'phi3:mini') -> dict:
    """
    Generate code using Ollama (local LLM)
    
    Args:
        prompt: The generation prompt
        model: Ollama model to use (default: phi3:mini)
    
    Returns:
        dict with code, strategy_type, indicators, reasoning, provider
    """
    try:
        import requests
        
        url = "http://localhost:11434/api/generate"
        
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.3,
                'num_predict': 2000
            }
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        content = result['response']
        
        # Try to extract JSON from response
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    'code': parsed.get('code', content),
                    'strategy_type': parsed.get('strategy_type', 'Custom'),
                    'indicators': parsed.get('indicators', []),
                    'reasoning': parsed.get('reasoning', ''),
                    'provider': 'ollama'
                }
        except:
            pass
        
        # Fallback: return raw code
        return {
            'code': content,
            'strategy_type': 'Custom',
            'indicators': [],
            'reasoning': 'Generated by Ollama',
            'provider': 'ollama'
        }
        
    except requests.exceptions.ConnectionError:
        return {
            'error': 'Ollama not running. Start Ollama with: ollama serve',
            'provider': 'ollama',
            'fallback': 'local'
        }
    except Exception as e:
        return {
            'error': f'Ollama error: {str(e)}',
            'provider': 'ollama',
            'fallback': 'local'
        }


# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_strategy_code(user_input: str, provider: str = 'local', api_keys: Dict = None) -> dict:
    """
    Generate strategy code from natural language description.
    
    Args:
        user_input: Natural language strategy description
        provider: 'local', 'ollama', 'deepseek', or 'claude'
        api_keys: Dict with API keys
        
    Returns:
        dict with code, strategy_type, indicators, reasoning, provider
    """
    try:
        # Build the prompt
        prompt = f"""You are a quantitative trading expert. Generate Python strategy code.

REQUIRED STRUCTURE:
```python
import numpy as np

def strategy(data):
    # data has: 'close', 'open', 'high', 'low', 'volume' (numpy arrays)
    # Return: buy_signals (bool array), sell_signals (bool array)
    return buy_signals, sell_signals
```

RULES:
1. Use ONLY numpy (no pandas)
2. All arrays must be same length as input
3. Handle edge cases
4. No look-ahead bias

USER REQUEST: "{user_input}"

Respond in JSON format:
{{
    "reasoning": "Brief explanation",
    "code": "Complete Python code",
    "strategy_type": "Strategy type",
    "indicators": ["indicator1", "indicator2"]
}}
"""
        
        # Route to appropriate provider
        if provider == 'ollama':
            return generate_with_ollama(prompt)
        elif provider == 'deepseek':
            return generate_with_deepseek(prompt, api_keys)
        elif provider == 'claude':
            return generate_with_claude(prompt, api_keys)
        else:  # 'local'
            return generate_local_strategy(user_input, prompt)
        
    except Exception as e:
        return {'error': str(e), 'provider': provider}


def generate_local_strategy(user_input: str, prompt: str = None) -> dict:
    """
    Generate strategy code using template matching with composition
    """
    composer = TemplateComposer()
    conditions = composer.detect_conditions(user_input)
    
    if conditions['templates']:
        # Compose strategy from templates
        code = composer.compose_strategy(conditions, user_input)
        
        # Extract strategy type
        template_names = conditions['templates']
        if len(template_names) == 1:
            strategy_type = STRATEGY_TEMPLATES[template_names[0]]['name']
        else:
            strategy_type = 'Composite Strategy'
        
        # Extract indicators
        indicators = set()
        for name in template_names:
            if name in STRATEGY_TEMPLATES:
                indicators.update(STRATEGY_TEMPLATES[name]['indicators'])
        
        return {
            'code': code,
            'strategy_type': strategy_type,
            'indicators': list(indicators),
            'reasoning': f"Generated using {', '.join(template_names)} templates",
            'provider': 'local'
        }
    else:
        # No templates matched, return default
        return {
            'code': STRATEGY_TEMPLATES['sma_crossover']['code'],
            'strategy_type': 'SMA Crossover',
            'indicators': ['SMA'],
            'reasoning': 'No specific indicators detected, using default SMA crossover',
            'provider': 'local'
        }


def generate_with_deepseek(prompt: str, api_keys: Dict = None) -> dict:
    """Generate code using DeepSeek API"""
    try:
        import requests
        
        api_key = api_keys.get('deepseek') if api_keys else os.environ.get('DEEPSEEK_API_KEY')
        if not api_key:
            return {'error': 'DeepSeek API key not provided', 'provider': 'deepseek', 'fallback': 'local'}
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    'code': parsed.get('code', content),
                    'strategy_type': parsed.get('strategy_type', 'Custom'),
                    'indicators': parsed.get('indicators', []),
                    'reasoning': parsed.get('reasoning', ''),
                    'provider': 'deepseek'
                }
        except:
            pass
        
        return {
            'code': content,
            'strategy_type': 'Custom',
            'indicators': [],
            'reasoning': 'Generated by DeepSeek',
            'provider': 'deepseek'
        }
        
    except Exception as e:
        return {'error': f'DeepSeek API error: {str(e)}', 'provider': 'deepseek', 'fallback': 'local'}


def generate_with_claude(prompt: str, api_keys: Dict = None) -> dict:
    """Generate code using Claude API"""
    try:
        import requests
        
        api_key = api_keys.get('claude') if api_keys else os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {'error': 'Claude API key not provided', 'provider': 'claude', 'fallback': 'local'}
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['content'][0]['text']
        
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    'code': parsed.get('code', content),
                    'strategy_type': parsed.get('strategy_type', 'Custom'),
                    'indicators': parsed.get('indicators', []),
                    'reasoning': parsed.get('reasoning', ''),
                    'provider': 'claude'
                }
        except:
            pass
        
        return {
            'code': content,
            'strategy_type': 'Custom',
            'indicators': [],
            'reasoning': 'Generated by Claude',
            'provider': 'claude'
        }
        
    except Exception as e:
        return {'error': f'Claude API error: {str(e)}', 'provider': 'claude', 'fallback': 'local'}
