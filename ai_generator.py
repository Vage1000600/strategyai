"""
StrategyAI - AI Strategy Generator (Compact Version)
Supports: Groq (default), Local templates, Ollama, DeepSeek, Claude
"""

import json
import os
from typing import Dict, List

# ============================================================================
# GROQ API KEY (Set in Vercel Environment Variables)
# Get yours at: https://console.groq.com/keys
# Free tier: 30 req/min, 14,400/day
# This key is used for "Local" mode - users don't need their own key
# ============================================================================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')  # Set in Vercel dashboard


# ============================================================================
# COMPACT STRATEGY TEMPLATES (Most Common 10)
# ============================================================================

TEMPLATES = {
    'rsi': '''import numpy as np
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
    return rsi < 30, rsi > 70''',
    
    'macd': '''import numpy as np

def compute_ema(data, period):
    """Calculate Exponential Moving Average"""
    ema = np.zeros(len(data))
    ema[0] = data[0]
    multiplier = 2.0 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema

def strategy(data):
    """MACD Crossover Strategy - Buy when MACD crosses above signal line"""
    close = data['close']
    
    # Calculate EMAs
    ema12 = compute_ema(close, 12)
    ema26 = compute_ema(close, 26)
    
    # Calculate MACD and Signal
    macd_line = ema12 - ema26
    signal_line = compute_ema(macd_line, 9)
    
    # Initialize signals
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    
    # Detect crossovers
    macd_above = macd_line > signal_line
    
    for i in range(1, len(close)):
        # Buy: MACD crosses FROM below TO above signal
        if macd_above[i] and not macd_above[i-1]:
            buy_signals[i] = True
        # Sell: MACD crosses FROM above TO below signal  
        elif not macd_above[i] and macd_above[i-1]:
            sell_signals[i] = True
    
    return buy_signals, sell_signals''',
    
    'golden': '''import numpy as np
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
    buy = np.zeros(len(close), dtype=bool)
    sell = np.zeros(len(close), dtype=bool)
    buy[1:] = (ema50[1:] > ema200[1:]) & (ema50[:-1] <= ema200[:-1])
    sell[1:] = (ema50[1:] < ema200[1:]) & (ema50[:-1] >= ema200[:-1])
    return buy, sell''',
    
    'bollinger': '''import numpy as np
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
    return close > upper, close < middle''',
    
    'sma': '''import numpy as np
def compute_sma(data, period):
    return np.convolve(data, np.ones(period)/period, mode='full')[:len(data)]

def strategy(data):
    close = data['close']
    sma20 = compute_sma(close, 20)
    sma50 = compute_sma(close, 50)
    buy = np.zeros(len(close), dtype=bool)
    sell = np.zeros(len(close), dtype=bool)
    buy[1:] = (sma20[1:] > sma50[1:]) & (sma20[:-1] <= sma50[:-1])
    sell[1:] = (sma20[1:] < sma50[1:]) & (sma20[:-1] >= sma50[:-1])
    return buy, sell''',
    
    'volume': '''import numpy as np
def compute_sma(data, period):
    return np.convolve(data, np.ones(period)/period, mode='full')[:len(data)]

def strategy(data):
    volume = data['volume']
    close = data['close']
    avg_vol = compute_sma(volume, 20)
    vol_spike = volume > 2 * avg_vol
    price_up = close > np.concatenate([[close[0]], close[:-1]])
    return vol_spike & price_up, vol_spike & ~price_up''',
    
    'macd_rsi': '''import numpy as np
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
    buy = np.zeros(len(close), dtype=bool)
    sell = np.zeros(len(close), dtype=bool)
    macd_buy = (macd[1:] > signal[1:]) & (macd[:-1] <= signal[:-1])
    macd_sell = (macd[1:] < signal[1:]) & (macd[:-1] >= signal[:-1])
    buy[1:] = macd_buy & (rsi[1:] < 50)
    sell[1:] = macd_sell | (rsi[1:] > 70)
    return buy, sell''',
    
    'triple_ema': '''import numpy as np
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
    buy = np.zeros(len(close), dtype=bool)
    sell = np.zeros(len(close), dtype=bool)
    bullish = (ema8[1:] > ema21[1:]) & (ema21[1:] > ema50[1:])
    bearish = (ema8[1:] < ema21[1:]) & (ema21[1:] < ema50[1:])
    prev_bull = (ema8[:-1] < ema21[:-1]) | (ema21[:-1] < ema50[:-1])
    prev_bear = (ema8[:-1] > ema21[:-1]) | (ema21[:-1] > ema50[:-1])
    buy[1:] = bullish & prev_bear
    sell[1:] = bearish & prev_bull
    return buy, sell''',
    
    'atr': '''import numpy as np
def compute_atr(high, low, close, period=14):
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
    buy = np.ones(len(close), dtype=bool)
    buy[:14] = False
    sell = np.zeros(len(close), dtype=bool)
    highest = close[0]
    for i in range(1, len(close)):
        highest = max(highest, close[i])
        if close[i] < highest - 2 * atr[i]:
            sell[i] = True
            highest = close[i]
    return buy, sell''',
    
    'default': '''import numpy as np
def compute_sma(data, period):
    return np.convolve(data, np.ones(period)/period, mode='full')[:len(data)]

def strategy(data):
    close = data['close']
    sma20 = compute_sma(close, 20)
    sma50 = compute_sma(close, 50)
    buy = np.zeros(len(close), dtype=bool)
    sell = np.zeros(len(close), dtype=bool)
    buy[1:] = (sma20[1:] > sma50[1:]) & (sma20[:-1] <= sma50[:-1])
    sell[1:] = (sma20[1:] < sma50[1:]) & (sma20[:-1] >= sma50[:-1])
    return buy, sell'''
}


# ============================================================================
# TEMPLATE DETECTION
# ============================================================================

def detect_template(user_input: str) -> str:
    """Detect which template to use based on user input"""
    text = user_input.lower()
    
    # Check for specific indicators
    if 'rsi' in text and 'macd' in text:
        return 'macd_rsi'
    elif 'rsi' in text and ('30' in text or '70' in text or 'oversold' in text):
        return 'rsi'
    elif 'macd' in text and ('cross' in text or 'crossover' in text):
        return 'macd'
    elif 'golden' in text or ('50' in text and '200' in text and 'ema' in text):
        return 'golden'
    elif 'triple' in text and 'ema' in text:
        return 'triple_ema'
    elif 'bollinger' in text or 'band' in text:
        return 'bollinger'
    elif 'volume' in text and ('spike' in text or 'average' in text):
        return 'volume'
    elif 'atr' in text or 'trailing' in text:
        return 'atr'
    elif 'sma' in text or 'moving average' in text:
        return 'sma'
    else:
        return 'default'


# ============================================================================
# GROQ INTEGRATION (DEFAULT) - OPTIMIZED FOR ACCURACY
# ============================================================================

# FEW-SHOT EXAMPLES: Proven correct implementations
FEW_SHOT_EXAMPLES = '''
Example 1 - RSI Strategy (Correct Implementation):
```python
import numpy as np

def compute_rsi(close, period=14):
    """Calculate RSI with proper edge case handling"""
    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    
    # Use exponential moving average for smoothness
    alpha = 2.0 / (period + 1)
    avg_gain = np.zeros_like(close)
    avg_loss = np.zeros_like(close)
    avg_gain[0] = gain[0]
    avg_loss[0] = loss[0]
    
    for i in range(1, len(close)):
        avg_gain[i] = alpha * gain[i] + (1 - alpha) * avg_gain[i-1]
        avg_loss[i] = alpha * loss[i] + (1 - alpha) * avg_loss[i-1]
    
    # Prevent division by zero
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def strategy(data):
    close = data['close']
    rsi = compute_rsi(close, 14)
    # Buy when oversold, sell when overbought
    return rsi < 30, rsi > 70
```

Example 2 - MACD Strategy (Correct Implementation):
```python
import numpy as np

def compute_ema(data, period):
    """Calculate EMA with correct multiplier"""
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2.0 / (period + 1)  # Correct EMA formula
    
    for i in range(1, len(data)):
        ema[i] = multiplier * data[i] + (1 - multiplier) * ema[i-1]
    return ema

def strategy(data):
    close = data['close']
    
    # Calculate MACD components
    ema12 = compute_ema(close, 12)
    ema26 = compute_ema(close, 26)
    macd_line = ema12 - ema26
    signal_line = compute_ema(macd_line, 9)
    
    # Detect crossovers (vectorized for speed)
    macd_above = macd_line > signal_line
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    
    # Buy: MACD crosses FROM below TO above signal
    buy_signals[1:] = macd_above[1:] & ~macd_above[:-1]
    # Sell: MACD crosses FROM above TO below signal
    sell_signals[1:] = ~macd_above[1:] & macd_above[:-1]
    
    return buy_signals, sell_signals
```

Example 3 - MACD + RSI Combo (Advanced):
```python
import numpy as np

def compute_ema(data, period):
    ema = np.zeros_like(data)
    ema[0] = data[0]
    multiplier = 2.0 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = multiplier * data[i] + (1 - multiplier) * ema[i-1]
    return ema

def compute_rsi(close, period=14):
    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    alpha = 2.0 / (period + 1)
    avg_gain = np.zeros_like(close)
    avg_loss = np.zeros_like(close)
    avg_gain[0] = gain[0]
    avg_loss[0] = loss[0]
    for i in range(1, len(close)):
        avg_gain[i] = alpha * gain[i] + (1 - alpha) * avg_gain[i-1]
        avg_loss[i] = alpha * loss[i] + (1 - alpha) * avg_loss[i-1]
    rs = avg_gain / (avg_loss + 1e-10)  # Prevent div by zero
    return 100 - (100 / (1 + rs))

def strategy(data):
    close = data['close']
    ema12 = compute_ema(close, 12)
    ema26 = compute_ema(close, 26)
    macd = ema12 - ema26
    signal = compute_ema(macd, 9)
    rsi = compute_rsi(close, 14)
    
    # Buy: MACD crossover + RSI filter (only buy when not overbought)
    macd_cross_up = (macd[1:] > signal[1:]) & (macd[:-1] <= signal[:-1])
    rsi_filter = rsi[1:] < 50  # Only buy if RSI < 50
    
    buy_signals = np.zeros(len(close), dtype=bool)
    buy_signals[1:] = macd_cross_up & rsi_filter
    
    # Sell: MACD cross down OR RSI overbought
    macd_cross_down = (macd[1:] < signal[1:]) & (macd[:-1] >= signal[:-1])
    sell_signals = np.zeros(len(close), dtype=bool)
    sell_signals[1:] = macd_cross_down | (rsi[1:] > 70)
    
    return buy_signals, sell_signals
```
'''

def generate_with_groq(prompt: str, api_key: str = None) -> dict:
    """Generate code using Groq API (default provider) with optimized prompt for accuracy"""
    try:
        import requests
        use_key = api_key or GROQ_API_KEY
        if not use_key or use_key == 'gsk_your_key_here':
            return {'error': 'Groq API key not configured. Set GROQ_API_KEY env var or update ai_generator.py', 'provider': 'groq', 'fallback': 'local'}
        
        # Enhanced prompt with accuracy requirements
        enhanced_prompt = f"""You are an expert quantitative trading developer. Generate HIGHLY ACCURATE Python trading strategy code.

CRITICAL REQUIREMENTS:
1. **Mathematical Accuracy**: Use correct formulas for all indicators
   - EMA: multiplier = 2.0 / (period + 1), then ema[i] = multiplier * price[i] + (1 - multiplier) * ema[i-1]
   - RSI: Use exponential smoothing, handle division by zero with +1e-10
   - MACD: EMA(12) - EMA(26), signal = EMA(9) of MACD

2. **No Look-Ahead Bias**: Only use data available at time of signal
   - Use [:-1] and [1:] slicing for crossover detection
   - Never use future data in calculations

3. **Edge Cases**: Handle these explicitly
   - Division by zero: always add 1e-10 to denominators
   - Array bounds: initialize first element before loops
   - NaN/Inf: use np.nan_to_num() if needed

4. **Vectorization**: Prefer numpy vectorized operations over loops where possible
   - Example: buy_signals[1:] = condition[1:] & ~condition[:-1]

5. **Output Format**: Return exactly two boolean arrays of same length as input
   - buy_signals: True where buy signal fires
   - sell_signals: True where sell signal fires

{FEW_SHOT_EXAMPLES}

NOW GENERATE THIS STRATEGY:
{prompt}

Respond with code only, starting with ```python and ending with ```"""
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {use_key}"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are an expert Python developer specializing in quantitative trading strategies. Always write mathematically accurate, production-ready code."},
                {"role": "user", "content": enhanced_prompt}
            ],
            "temperature": 0.2,  # Lower temperature for more deterministic, accurate code
            "max_tokens": 2500
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        if '```python' in content:
            start = content.find('```python') + 10
            end = content.find('```', start)
            content = content[start:end].strip()
        
        return {
            'code': content,
            'strategy_type': 'Custom (Groq)',
            'indicators': ['Auto-detected'],
            'reasoning': 'Generated by Groq (Llama-3.3-70B) with accuracy optimization',
            'provider': 'groq'
        }
    except Exception as e:
        return {'error': f'Groq: {str(e)}', 'provider': 'groq', 'fallback': 'local'}


# ============================================================================
# OLLAMA INTEGRATION
# ============================================================================

def generate_with_ollama(prompt: str, model: str = 'phi3:mini') -> dict:
    """Generate code using Ollama (local LLM)"""
    try:
        import requests
        url = "http://localhost:11434/api/generate"
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.3, 'num_predict': 2000}
        }
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        content = response.json()['response']
        
        # Try to extract code
        if '```python' in content:
            start = content.find('```python') + 10
            end = content.find('```', start)
            content = content[start:end].strip()
        
        return {
            'code': content,
            'strategy_type': 'Custom (Ollama)',
            'indicators': ['Auto-detected'],
            'reasoning': 'Generated by Ollama',
            'provider': 'ollama'
        }
    except Exception as e:
        return {'error': f'Ollama: {str(e)}', 'provider': 'ollama', 'fallback': 'local'}


# ============================================================================
# DEEPSEEK INTEGRATION
# ============================================================================

def generate_with_deepseek(prompt: str, api_keys: Dict = None) -> dict:
    """Generate code using DeepSeek API"""
    try:
        import requests
        api_key = api_keys.get('deepseek') if api_keys else os.environ.get('DEEPSEEK_API_KEY')
        if not api_key:
            return {'error': 'DeepSeek API key required', 'provider': 'deepseek', 'fallback': 'local'}
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        if '```python' in content:
            start = content.find('```python') + 10
            end = content.find('```', start)
            content = content[start:end].strip()
        
        return {
            'code': content,
            'strategy_type': 'Custom (DeepSeek)',
            'indicators': ['Auto-detected'],
            'reasoning': 'Generated by DeepSeek',
            'provider': 'deepseek'
        }
    except Exception as e:
        return {'error': f'DeepSeek: {str(e)}', 'provider': 'deepseek', 'fallback': 'local'}


# ============================================================================
# CLAUDE INTEGRATION
# ============================================================================

def generate_with_claude(prompt: str, api_keys: Dict = None) -> dict:
    """Generate code using Claude API"""
    try:
        import requests
        api_key = api_keys.get('claude') if api_keys else os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {'error': 'Claude API key required', 'provider': 'claude', 'fallback': 'local'}
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.json()['content'][0]['text']
        
        if '```python' in content:
            start = content.find('```python') + 10
            end = content.find('```', start)
            content = content[start:end].strip()
        
        return {
            'code': content,
            'strategy_type': 'Custom (Claude)',
            'indicators': ['Auto-detected'],
            'reasoning': 'Generated by Claude',
            'provider': 'claude'
        }
    except Exception as e:
        return {'error': f'Claude: {str(e)}', 'provider': 'claude', 'fallback': 'local'}


# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_strategy_code(user_input: str, provider: str = 'local', api_keys: Dict = None) -> dict:
    """
    Generate strategy code from natural language.
    
    Args:
        user_input: Strategy description
        provider: 'local' (uses embedded Groq), 'groq', 'ollama', 'deepseek', or 'claude'
        api_keys: Dict with API keys
    
    Returns:
        dict with code, strategy_type, indicators, reasoning, provider
    """
    try:
        # Build prompt for AI providers
        prompt = f"""Generate Python trading strategy code.

REQUIRED FORMAT:
```python
import numpy as np

def strategy(data):
    # data has: 'close', 'open', 'high', 'low', 'volume' (numpy arrays)
    # Return: buy_signals (bool array), sell_signals (bool array)
    return buy_signals, sell_signals
```

RULES:
1. Use ONLY numpy (no pandas)
2. No look-ahead bias
3. Handle edge cases

STRATEGY: {user_input}

Respond with code only."""

        # Route to provider ('local' now uses embedded Groq key)
        if provider == 'local' or provider == 'groq':
            # Use embedded Groq key (users don't need their own)
            return generate_with_groq(prompt, api_key=GROQ_API_KEY)
        elif provider == 'ollama':
            return generate_with_ollama(prompt)
        elif provider == 'deepseek':
            return generate_with_deepseek(prompt, api_keys)
        elif provider == 'claude':
            return generate_with_claude(prompt, api_keys)
        else:  # Fallback to Groq
            return generate_with_groq(prompt, api_key=GROQ_API_KEY)
            
    except Exception as e:
        return {'error': str(e), 'provider': provider}


# ============================================================================
# ENHANCED VALIDATION (Accuracy + Security)
# ============================================================================

def validate_strategy(code: str) -> dict:
    """Validate strategy code for syntax, structure, security, and common errors"""
    import ast
    import re
    
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
        errors.append("No return statement")
    
    # 3. Security check
    dangerous = ['os.system', 'subprocess', 'eval(', 'exec(']
    for d in dangerous:
        if d in code:
            errors.append(f"Security: {d} not allowed")
    
    # 4. Accuracy checks (common mistakes)
    
    # Check for division without epsilon protection
    if re.search(r'/\s*[a-zA-Z_][a-zA-Z0-9_]*\s*[\)\]\}]', code):
        # Found potential unprotected division
        if '1e-10' not in code and 'epsilon' not in code.lower():
            warnings.append("Consider adding epsilon (1e-10) to divisions to prevent div-by-zero")
    
    # Check for look-ahead bias patterns
    if re.search(r'\[i\+1\]', code):
        warnings.append("Possible look-ahead bias: using [i+1] in loop")
    
    # Check for correct EMA formula
    if 'ema' in code.lower() and '2.0 / (' not in code and '2 / (' not in code:
        warnings.append("Verify EMA multiplier: should be 2.0 / (period + 1)")
    
    # Check for numpy import
    if 'import numpy' not in code and 'import np' not in code:
        errors.append("Missing numpy import (required)")
    
    # 5. Basic execution test (lightweight - just check strategy exists)
    try:
        # Just verify the code can be parsed and strategy function exists
        # Full execution test happens in backtester with proper environment
        if 'def strategy(' not in code:
            errors.append("strategy() function not found")
        
    except Exception as e:
        errors.append(f"Parse error: {str(e)}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def validate_and_fix(code: str) -> dict:
    """Validate code and attempt automatic fixes for common issues"""
    import re
    
    fixed_code = code
    fixes_applied = []
    
    # Fix 1: Add epsilon to unprotected divisions in RSI calculations
    if 'rs = ' in code and '1e-10' not in code:
        fixed_code = re.sub(
            r'rs = ([^\n]+)/([^\n]+)',
            r'rs = \1 / (\2 + 1e-10)',
            fixed_code
        )
        fixes_applied.append("Added epsilon to RSI division")
    
    # Fix 2: Ensure boolean dtype for signals
    if 'dtype=bool' not in code and 'dtype=np.bool' not in code:
        fixed_code = re.sub(
            r'np\.zeros\(len\(([^)]+)\)\)',
            r'np.zeros(len(\1), dtype=bool)',
            fixed_code
        )
        fixes_applied.append("Added dtype=bool to signal arrays")
    
    # Validate the fixed code
    validation = validate_strategy(fixed_code)
    validation['code'] = fixed_code
    validation['fixes_applied'] = fixes_applied
    
    return validation
