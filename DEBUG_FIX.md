# Debug: Zero Results Issue

## Problem
Strategy code is correct, but backtest returns all zeros.

## Root Cause Analysis

The backtester iterates candle-by-candle:
```python
for i in range(1, len(df)):
    data = self._prepare_data(df, i)  # Data up to candle i
    result = strategy_func(data)  # Returns arrays of length i+1
    buy_signal = result[0][-1]  # Takes LAST value only
```

**Issue:** The strategy returns full arrays, but backtester only checks `[-1]` (last element) each iteration.

For MACD crossover:
- Most candles: NO crossover (buy_signal = False)
- Rare candles: Crossover happens (buy_signal = True)

If the last candle has no crossover, `buy_signal[-1]` is always False!

## Solution Options

### Option 1: Fix Backtester (Recommended)
Make backtester check ALL signals, not just last one:

```python
# In backtester.py, run() method
# Get signals from strategy
result = strategy_func(data)
buy_signals, sell_signals = result

# Check if ANY signal fired in recent candles
if np.any(buy_signals[-5:]) and position == 0:  # Check last 5 candles
    # Enter position
```

### Option 2: Change Strategy Output
Make strategy return single boolean (not array):

```python
def strategy(data):
    # ... calculations ...
    # Return single value for CURRENT candle only
    return buy_signals[-1], sell_signals[-1]
```

### Option 3: Pre-compute All Signals (Best)
Run strategy ONCE on full dataset, then iterate through signals:

```python
# Before loop
data_full = prepare_full_data(df)
buy_signals, sell_signals = strategy_func(data_full)

# In loop
if buy_signals[i] and position == 0:
    # Enter
```

## Recommended Fix: Option 3

Most efficient - run strategy once, then use pre-computed signals.
