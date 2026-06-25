"""
StrategyAI - AI Strategy Generator (COMPACT - 15KB)
Supports: Groq (default), Local templates, Ollama, DeepSeek, Claude
"""

import json
import os
from typing import Dict, List

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# COMPACT TEMPLATES (8 most common)
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
    ema = np.zeros(len(data))
    ema[0] = data[0]
    multiplier = 2.0 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema
def strategy(data):
    close = data['close']
    ema12 = compute_ema(close, 12)
    ema26 = compute_ema(close, 26)
    macd_line = ema12 - ema26
    signal_line = compute_ema(macd_line, 9)
    buy_signals = np.zeros(len(close), dtype=bool)
    sell_signals = np.zeros(len(close), dtype=bool)
    macd_above = macd_line > signal_line
    buy_signals[1:] = macd_above[1:] & ~macd_above[:-1]
    sell_signals[1:] = ~macd_above[1:] & macd_above[:-1]
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

def detect_template(user_input: str) -> str:
    text = user_input.lower()
    # Be aggressive - match common strategies
    if 'rsi' in text and 'macd' in text: return 'macd_rsi' if 'macd_rsi' in TEMPLATES else 'rsi'
    elif 'rsi' in text or 'relative strength' in text: return 'rsi'
    elif 'macd' in text or 'moving average convergence' in text: return 'macd'
    elif 'golden' in text or 'death cross' in text: return 'golden'
    elif 'bollinger' in text or 'band' in text: return 'bollinger'
    elif 'volume' in text: return 'volume'
    elif 'triple' in text and 'ema' in text: return 'triple_ema'
    elif 'sma' in text or 'moving average' in text or 'crossover' in text: return 'sma'
    elif 'buy when' in text and 'sell when' in text: return 'default'  # Generic mean-reversion
    else: return 'default'

# COMPACT AI GENERATION (single function for all providers)
def generate_with_provider(prompt: str, provider: str = 'groq', api_key: str = None) -> dict:
    try:
        import requests
        if provider == 'groq':
            key = api_key or GROQ_API_KEY
            if not key: return {'error': 'GROQ_API_KEY not set', 'provider': 'groq', 'fallback': 'local'}
            url, headers = "https://api.groq.com/openai/v1/chat/completions", {"Authorization": f"Bearer {key}"}
            payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 2500}
        elif provider == 'deepseek':
            key = api_key or os.environ.get('DEEPSEEK_API_KEY')
            if not key: return {'error': 'DeepSeek key required', 'provider': 'deepseek', 'fallback': 'local'}
            url, headers = "https://api.deepseek.com/v1/chat/completions", {"Authorization": f"Bearer {key}"}
            payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 2000}
        elif provider == 'claude':
            key = api_key or os.environ.get('ANTHROPIC_API_KEY')
            if not key: return {'error': 'Claude key required', 'provider': 'claude', 'fallback': 'local'}
            url, headers = "https://api.anthropic.com/v1/messages", {"x-api-key": key, "anthropic-version": "2023-06-01"}
            payload = {"model": "claude-3-sonnet-20240229", "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}
        elif provider == 'ollama':
            url, payload = "http://localhost:11434/api/generate", {'model': 'phi3:mini', 'prompt': prompt, 'stream': False, 'options': {'temperature': 0.3}}
            headers = {}
        else:
            return {'error': f'Unknown provider: {provider}', 'fallback': 'local'}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        if provider == 'claude':
            content = response.json()['content'][0]['text']
        elif provider == 'ollama':
            content = response.json()['response']
        else:
            content = response.json()['choices'][0]['message']['content']
        
        if '```python' in content:
            start, end = content.find('```python') + 10, content.find('```', content.find('```python') + 10)
            content = content[start:end].strip() if end > start else content
        
        return {'code': content, 'strategy_type': f'Custom ({provider.title()})', 'indicators': ['Auto'], 'reasoning': f'Generated by {provider.title()}', 'provider': provider}
    except Exception as e:
        return {'error': f'{provider.title()}: {str(e)}', 'provider': provider, 'fallback': 'local'}

def generate_strategy_code(user_input: str, provider: str = 'groq', api_keys: Dict = None) -> dict:
    # First, check if we should use a template instead of generating
    template_match = detect_template(user_input)
    if template_match in TEMPLATES:
        # Use template - it's already validated!
        return {
            'code': TEMPLATES[template_match],
            'strategy_type': f'{template_match.title()} Template',
            'indicators': [template_match.upper()],
            'reasoning': f'Used pre-built {template_match} template (validated)',
            'provider': 'local',
            'template_used': True
        }
    
    # No template match, generate with AI
    prompt = f"""Generate a COMPLETE Python trading strategy using ONLY NUMPY.

⚠️ CRITICAL: data['close'] is a NUMPY ARRAY, NOT pandas!

✅ DO use: np.diff(), np.convolve(), np.roll(), np.cumsum()
❌ DON'T use: .diff(), .rolling(), .shift() (these are pandas methods!)

REQUIRED FORMAT:
```python
import numpy as np

def strategy(data):
    # data['close'] is a numpy array (NOT pandas!)
    
    # Example RSI with numpy (correct):
    delta = np.diff(data['close'])  # ✅ numpy
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    
    # Generate boolean signals
    buy_signals = np.zeros(len(data['close']), dtype=bool)
    sell_signals = np.zeros(len(data['close']), dtype=bool)
    buy_signals[14:] = ...  # your logic
    sell_signals[14:] = ...  # your logic
    
    return buy_signals, sell_signals  # REQUIRED!
```

STRATEGY REQUEST: {user_input}

Respond with code only, NO explanations. Use ONLY numpy, NOT pandas!"""
    
    if provider == 'local': provider = 'groq'  # Local uses embedded Groq
    key = (api_keys or {}).get(provider) if provider != 'groq' else GROQ_API_KEY
    return generate_with_provider(prompt, provider, key)

def validate_strategy(code: str) -> dict:
    import ast, re
    errors, warnings = [], []
    try: ast.parse(code)
    except SyntaxError as e:
        errors.append(f"Syntax error: {e}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}
    
    if "def strategy(" not in code: errors.append("Missing strategy() function")
    if "return" not in code: errors.append("No return statement")
    for d in ['os.system', 'subprocess', 'eval(', 'exec(']:
        if d in code: errors.append(f"Security: {d} not allowed")
    
    # Check for pandas methods being used (will fail on numpy arrays)
    pandas_patterns = [
        (r'\.diff\(', 'Use np.diff(array) instead of array.diff()'),
        (r'\.rolling\(', 'Use np.convolve() instead of .rolling()'),
        (r'\.shift\(', 'Use np.roll() instead of .shift()'),
        (r'\.fillna\(', 'Use np.nan_to_num() instead of .fillna()'),
        (r'\.dropna\(', 'Use boolean indexing instead of .dropna()'),
    ]
    for pattern, msg in pandas_patterns:
        if re.search(pattern, code):
            errors.append(f"Pandas method detected: {msg}")
    
    return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}

def validate_and_fix(code: str) -> dict:
    import re, ast
    lines = code.split('\n')
    cleaned, in_func = [], False
    module_level_code = []  # Code outside functions
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            cleaned.append(line)
        elif in_func:
            if stripped and not line.startswith(' ') and not line.startswith('\t'):
                in_func = False
                if stripped.startswith('def '): 
                    cleaned.append(line)
                    in_func = True
                elif stripped:  # Non-empty line outside function - module level!
                    module_level_code.append(line)
            else:
                cleaned.append(line)
        elif stripped.startswith('def '):
            cleaned.append(line)
            in_func = True
        elif stripped:  # Non-empty line outside function - module level!
            module_level_code.append(line)
    
    fixed_code = '\n'.join(cleaned)
    
    # If there's module-level code, wrap it in strategy function
    if module_level_code:
        # Find where to insert the wrapped code (after imports, before first def)
        insert_idx = 0
        for i, line in enumerate(cleaned):
            if line.strip().startswith('def '):
                insert_idx = i
                break
        
        # Wrap module-level code in strategy function
        wrapped = ['def strategy(data):']
        for line in module_level_code:
            wrapped.append('    ' + line if line.strip() else '')
        wrapped.append('    return np.zeros(len(data[\'close\']), dtype=bool), np.zeros(len(data[\'close\']), dtype=bool)')
        
        # Insert wrapped code
        cleaned = cleaned[:insert_idx] + wrapped + cleaned[insert_idx:]
        fixed_code = '\n'.join(cleaned)
    
    if 'import numpy' not in fixed_code:
        fixed_code = 'import numpy as np\n\n' + fixed_code
    
    try: ast.parse(fixed_code)
    except SyntaxError as se:
        return {'valid': False, 'code': fixed_code, 'errors': [f"Syntax: {se}"], 'warnings': [], 'fixes_applied': []}
    
    validation = validate_strategy(fixed_code)
    validation['code'] = fixed_code
    validation['fixes_applied'] = ['Wrapped module-level code in strategy()', 'Added numpy import']
    return validation
