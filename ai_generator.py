"""
StrategyAI - Multi-Provider AI Strategy Generator
Supports: Local (default), DeepSeek, Claude

Features:
- Switch between AI providers
- Fallback handling
- Provider-specific optimizations
"""

import json
import os
from typing import Optional, Dict


# Few-shot examples (same for all providers)
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
    
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    buy_signals[1:] = (macd[1:] > signal[1:]) & (macd[:-1] <= signal[:-1])
    sell_signals[1:] = (macd[1:] < signal[1:]) & (macd[:-1] >= signal[:-1])
    
    return buy_signals, sell_signals
```

EXAMPLE 3 - Bollinger Bands:
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
"""

SYSTEM_PROMPT = f"""
You are a quantitative trading expert. Generate Python strategy code for backtesting.

REQUIRED STRUCTURE:
```python
import numpy as np

def strategy(data):
    # data is a dict with numpy arrays: 'close', 'open', 'high', 'low', 'volume'
    # Also has pre-computed indicators: 'rsi', 'macd', 'signal', 'ema50', 'ema200', etc.
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
6. You can define helper functions (compute_rsi, compute_bollinger, etc.)

{FEW_SHOT_EXAMPLES}

THINK STEP-BY-STEP:
1. What indicators are needed?
2. What are the exact entry conditions?
3. What are the exact exit conditions?
4. Generate clean, efficient code
5. Review for errors before finalizing
"""


def generate_strategy_code(user_input: str, provider: str = 'local', api_keys: Dict = None) -> dict:
    """
    Generate strategy code from natural language description.
    
    Args:
        user_input: Natural language strategy description
        provider: 'local', 'deepseek', or 'claude'
        api_keys: Dict with 'deepseek' and/or 'claude' keys
        
    Returns:
        dict: {
            'code': str,
            'strategy_type': str,
            'indicators': list,
            'reasoning': str,
            'provider': str,
            'error': str (if failed)
        }
    """
    try:
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
        
        # Route to appropriate provider
        if provider == 'deepseek':
            return generate_with_deepseek(prompt, api_keys)
        elif provider == 'claude':
            return generate_with_claude(prompt, api_keys)
        else:  # 'local'
            return generate_local_strategy(user_input, prompt)
        
    except Exception as e:
        return {'error': str(e), 'provider': provider}


def generate_local_strategy(user_input: str, prompt: str = None) -> dict:
    """
    Generate strategy code using rule-based approach (no API calls).
    Falls back to template-based generation.
    """
    user_input_lower = user_input.lower()
    
    # RSI Strategy
    if 'rsi' in user_input_lower and ('30' in user_input_lower or '70' in user_input_lower or 'oversold' in user_input_lower or 'overbought' in user_input_lower):
        code = '''import numpy as np

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
    
    # Buy when oversold (<30), sell when overbought (>70)
    buy_signals = rsi < 30
    sell_signals = rsi > 70
    
    return buy_signals, sell_signals
'''
        return {
            'code': code,
            'strategy_type': 'Mean Reversion',
            'indicators': ['RSI'],
            'reasoning': 'Classic RSI mean reversion strategy - buys oversold conditions, sells overbought',
            'provider': 'local'
        }
    
    # MACD Strategy
    elif 'macd' in user_input_lower and ('cross' in user_input_lower or 'crossover' in user_input_lower):
        code = '''import numpy as np

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
        return {
            'code': code,
            'strategy_type': 'Trend Following',
            'indicators': ['MACD', 'EMA'],
            'reasoning': 'MACD crossover strategy - buys when MACD crosses above signal, sells on reverse',
            'provider': 'local'
        }
    
    # Golden Cross / EMA Crossover
    elif ('golden' in user_input_lower or ('ema' in user_input_lower and ('50' in user_input_lower or '200' in user_input_lower))):
        code = '''import numpy as np

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
        return {
            'code': code,
            'strategy_type': 'Trend Following',
            'indicators': ['EMA', 'Golden Cross'],
            'reasoning': 'Golden Cross strategy - buys when 50 EMA crosses above 200 EMA (bullish), sells on death cross',
            'provider': 'local'
        }
    
    # Bollinger Bands
    elif 'bollinger' in user_input_lower or ('band' in user_input_lower and ('break' in user_input_lower or 'touch' in user_input_lower)):
        code = '''import numpy as np

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
    
    # Buy when price breaks above upper band, sell at middle
    buy_signals = close > upper
    sell_signals = close < middle
    
    return buy_signals, sell_signals
'''
        return {
            'code': code,
            'strategy_type': 'Breakout',
            'indicators': ['Bollinger Bands', 'SMA'],
            'reasoning': 'Bollinger Band breakout strategy - buys breakouts above upper band, sells at mean reversion',
            'provider': 'local'
        }
    
    # Moving Average Crossover (default)
    else:
        code = '''import numpy as np

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
        return {
            'code': code,
            'strategy_type': 'Trend Following',
            'indicators': ['SMA', 'Moving Average Crossover'],
            'reasoning': 'Dual moving average crossover - buys when fast MA crosses above slow MA',
            'provider': 'local'
        }


def generate_with_deepseek(prompt: str, api_keys: Dict = None) -> dict:
    """Generate code using DeepSeek API"""
    try:
        import requests
        
        api_key = api_keys.get('deepseek') if api_keys else os.environ.get('DEEPSEEK_API_KEY')
        if not api_key:
            return {
                'error': 'DeepSeek API key not provided',
                'provider': 'deepseek',
                'fallback': 'local'
            }
        
        # DeepSeek API endpoint
        url = "https://api.deepseek.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a quantitative trading expert. Generate Python strategy code."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
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
                    'provider': 'deepseek'
                }
        except:
            pass
        
        # Fallback: return raw code
        return {
            'code': content,
            'strategy_type': 'Custom',
            'indicators': [],
            'reasoning': 'Generated by DeepSeek',
            'provider': 'deepseek'
        }
        
    except Exception as e:
        return {
            'error': f'DeepSeek API error: {str(e)}',
            'provider': 'deepseek',
            'fallback': 'local'
        }


def generate_with_claude(prompt: str, api_keys: Dict = None) -> dict:
    """Generate code using Claude (Anthropic) API"""
    try:
        import requests
        
        api_key = api_keys.get('claude') if api_keys else os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {
                'error': 'Claude API key not provided',
                'provider': 'claude',
                'fallback': 'local'
            }
        
        # Anthropic API endpoint
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 2000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['content'][0]['text']
        
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
                    'provider': 'claude'
                }
        except:
            pass
        
        # Fallback: return raw code
        return {
            'code': content,
            'strategy_type': 'Custom',
            'indicators': [],
            'reasoning': 'Generated by Claude',
            'provider': 'claude'
        }
        
    except Exception as e:
        return {
            'error': f'Claude API error: {str(e)}',
            'provider': 'claude',
            'fallback': 'local'
        }
