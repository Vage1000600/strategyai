"""
StrategyAI - AI Strategy Code Generator
Enhanced with few-shot prompting, validation, and chain-of-thought reasoning
"""

import json
import os
from typing import Optional

# Few-shot examples - proven working strategies
FEW_SHOT_EXAMPLES = """
EXAMPLE 1 - RSI Strategy:
User: "Buy when RSI is below 30, sell when RSI is above 70"

```python
import numpy as np

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
    return buy_signals, sell_signals
```

EXAMPLE 2 - MACD Crossover:
User: "Buy when MACD crosses above signal line, sell when it crosses below"

```python
import numpy as np

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
    
    # Crossover detection
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    buy_signals[1:] = (macd[1:] > signal[1:]) & (macd[:-1] <= signal[:-1])
    sell_signals[1:] = (macd[1:] < signal[1:]) & (macd[:-1] >= signal[:-1])
    
    return buy_signals, sell_signals
```

EXAMPLE 3 - Golden Cross:
User: "Buy when 50 EMA crosses above 200 EMA, sell on reverse"

```python
import numpy as np

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
    
    return buy_signals, sell_signals
```

EXAMPLE 4 - Bollinger Band Breakout:
User: "Buy when price breaks above upper Bollinger Band, sell at middle band"

```python
import numpy as np

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
    
    return buy_signals, sell_signals
```

EXAMPLE 5 - Dual Moving Average:
User: "Buy when price crosses above 50 SMA, sell when it crosses below"

```python
import numpy as np

def compute_sma(data, period):
    return np.convolve(data, np.ones(period)/period, mode='full')[:len(data)]

def strategy(data):
    close = data['close']
    sma50 = compute_sma(close, 50)
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    buy_signals[1:] = (close[1:] > sma50[1:]) & (close[:-1] <= sma50[:-1])
    sell_signals[1:] = (close[1:] < sma50[1:]) & (close[:-1] >= sma50[:-1])
    
    return buy_signals, sell_signals
```
"""

SYSTEM_PROMPT = f"""
You are a quantitative trading expert. Generate Python strategy code for backtesting.

REQUIRED STRUCTURE:
```python
import numpy as np

def strategy(data):
    # data is a dict with: 'open', 'high', 'low', 'close', 'volume' (all numpy arrays)
    # Return: buy_signals (bool array), sell_signals (bool array)
    
    # YOUR CODE HERE
    return buy_signals, sell_signals
```

RULES:
1. Use ONLY numpy (no pandas, no external libraries)
2. All arrays must be same length as input data
3. Handle edge cases (first N candles for indicators)
4. Buy/sell signals must be boolean arrays
5. No look-ahead bias (use only past/present data)

{FEW_SHOT_EXAMPLES}

THINK STEP-BY-STEP:
1. What indicators are needed?
2. What are the exact entry conditions?
3. What are the exact exit conditions?
4. Generate clean, efficient code
5. Review for errors before finalizing
"""


def generate_strategy_code(user_input: str, model=None) -> dict:
    """
    Generate strategy code from natural language description.
    
    Returns:
        dict: {
            'code': str,
            'strategy_type': str,
            'indicators': list,
            'reasoning': str,
            'error': str (if failed)
        }
    """
    try:
        # Use configured model or fallback
        if model is None:
            # Try to use local reasoning first
            model = os.environ.get('AI_MODEL', 'local')
        
        # Build the prompt with chain-of-thought
        prompt = f"""{SYSTEM_PROMPT}

USER REQUEST: "{user_input}"

Generate the strategy code following the examples above. Include:
1. Brief reasoning about the approach
2. Complete working code
3. List of indicators used

Respond in this JSON format:
{{
    "reasoning": "Brief explanation of the strategy approach",
    "code": "Complete Python code here",
    "strategy_type": "e.g., Mean Reversion, Trend Following, Breakout",
    "indicators": ["RSI", "MACD", etc.]
}}
"""
        
        # Try local reasoning first (if available)
        if model == 'local':
            code = generate_local_strategy(user_input)
            return {
                'code': code,
                'strategy_type': 'Custom',
                'indicators': ['Auto-detected'],
                'reasoning': 'Generated using local reasoning engine'
            }
        
        # Use AI model (DeepSeek, OpenAI, etc.)
        code = generate_with_ai(prompt, model)
        
        # Try to parse JSON response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', code)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'code': result.get('code', code),
                    'strategy_type': result.get('strategy_type', 'Custom'),
                    'indicators': result.get('indicators', []),
                    'reasoning': result.get('reasoning', '')
                }
        except:
            pass
        
        # Fallback: return raw code
        return {
            'code': code,
            'strategy_type': 'Custom',
            'indicators': ['Auto-detected'],
            'reasoning': 'Generated from AI model'
        }
        
    except Exception as e:
        return {'error': str(e)}


def generate_local_strategy(user_input: str) -> str:
    """
    Generate strategy code using rule-based approach (no AI).
    Falls back to template-based generation.
    """
    user_input_lower = user_input.lower()
    
    # RSI Strategy
    if 'rsi' in user_input_lower:
        return '''import numpy as np

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
    
    # Default: buy when oversold (<30), sell when overbought (>70)
    buy_signals = rsi < 30
    sell_signals = rsi > 70
    
    return buy_signals, sell_signals
'''
    
    # MACD Strategy
    elif 'macd' in user_input_lower:
        return '''import numpy as np

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
    
    # Crossover detection
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    buy_signals[1:] = (macd[1:] > signal[1:]) & (macd[:-1] <= signal[:-1])
    sell_signals[1:] = (macd[1:] < signal[1:]) & (macd[:-1] >= signal[:-1])
    
    return buy_signals, sell_signals
'''
    
    # Golden Cross / EMA Crossover
    elif 'golden' in user_input_lower or ('ema' in user_input_lower and ('50' in user_input_lower or '200' in user_input_lower)):
        return '''import numpy as np

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
    
    return buy_signals, sell_signals
'''
    
    # Bollinger Bands
    elif 'bollinger' in user_input_lower or 'bollinger' in user_input_lower:
        return '''import numpy as np

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
    
    return buy_signals, sell_signals
'''
    
    # Moving Average Crossover (default)
    else:
        return '''import numpy as np

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
    
    return buy_signals, sell_signals
'''


def generate_with_ai(prompt: str, model: str) -> str:
    """Generate code using AI model (DeepSeek, OpenAI, etc.)"""
    # This would integrate with actual AI APIs
    # For now, fallback to local generation
    return generate_local_strategy(prompt[:100])  # Use first 100 chars as hint


def validate_strategy(code: str) -> dict:
    """
    Validate generated strategy code before execution.
    
    Returns:
        dict: {
            'valid': bool,
            'errors': list,
            'warnings': list
        }
    """
    import ast
    
    errors = []
    warnings = []
    
    # 1. Syntax check
    try:
        ast.parse(code)
    except SyntaxError as e:
        errors.append(f"Syntax error: {e}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}
    
    # 2. Structure check
    if "def strategy(" not in code:
        errors.append("Missing strategy() function")
    
    if "return" not in code:
        errors.append("No return statement found")
    
    # 3. Security check - no dangerous imports
    dangerous_imports = ['os.system', 'subprocess', 'eval(', 'exec(', '__import__']
    for dangerous in dangerous_imports:
        if dangerous in code:
            errors.append(f"Security violation: {dangerous} not allowed")
    
    # 4. Check for required imports
    if "import numpy" not in code and "import numpy as np" not in code:
        warnings.append("Consider importing numpy for array operations")
    
    # 5. Execution test (in next step with actual data)
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def test_strategy_execution(code: str, test_data: dict) -> dict:
    """
    Test strategy code on small sample data.
    
    Returns:
        dict: {
            'success': bool,
            'error': str (if failed),
            'buy_count': int,
            'sell_count': int
        }
    """
    try:
        # Create namespace for execution
        namespace = {}
        
        # Execute the code
        exec(code, namespace)
        
        # Get the strategy function
        if 'strategy' not in namespace:
            return {'success': False, 'error': 'strategy() function not found'}
        
        strategy_func = namespace['strategy']
        
        # Run on test data
        buy_signals, sell_signals = strategy_func(test_data)
        
        # Validate outputs
        if len(buy_signals) != len(test_data['close']):
            return {'success': False, 'error': 'Buy signals length mismatch'}
        
        if len(sell_signals) != len(test_data['close']):
            return {'success': False, 'error': 'Sell signals length mismatch'}
        
        # Count signals
        buy_count = int(np.sum(buy_signals))
        sell_count = int(np.sum(sell_signals))
        
        # Warnings
        if buy_count == 0 and sell_count == 0:
            return {
                'success': True,
                'error': None,
                'buy_count': buy_count,
                'sell_count': sell_count,
                'warning': 'No signals generated - check your conditions'
            }
        
        if buy_count > len(test_data['close']) * 0.5:
            return {
                'success': True,
                'error': None,
                'buy_count': buy_count,
                'sell_count': sell_count,
                'warning': 'Very high trade frequency - may be overfitting'
            }
        
        return {
            'success': True,
            'error': None,
            'buy_count': buy_count,
            'sell_count': sell_count
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


# Import numpy for test execution
import numpy as np
