"""
StrategyAI - AI Strategy Code Generator
Person 1: AI Integration Lead

Converts natural language trading strategies to Python code using DeepSeek API.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize DeepSeek client (OpenAI-compatible API)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# System prompt for strategy code generation
SYSTEM_PROMPT = """
You are a trading strategy code generator. Convert natural language trading 
strategies into valid Python code that can be executed by a backtesting engine.

RULES:
1. Only use these indicators: rsi, macd, ema, sma, bb (Bollinger Bands), atr
2. Only use these actions: buy(), sell(), hold()
3. Use simple if/elif/else logic
4. Reference price data as: close, high, low, open
5. Keep code simple and readable
6. Do NOT import any libraries
7. Do NOT use loops or complex logic

EXAMPLE INPUT: "Buy when RSI < 30, sell when RSI > 70"

EXAMPLE OUTPUT:
```python
def strategy(data):
    rsi = data['rsi']
    
    if rsi < 30:
        return 'buy'
    elif rsi > 70:
        return 'sell'
    else:
        return 'hold'
```

EXAMPLE INPUT: "Buy when MACD crosses above signal, sell when it crosses below"

EXAMPLE OUTPUT:
```python
def strategy(data):
    macd = data['macd']
    signal = data['signal']
    prev_macd = data['prev_macd']
    prev_signal = data['prev_signal']
    
    # MACD crosses above signal
    if prev_macd <= prev_signal and macd > signal:
        return 'buy'
    # MACD crosses below signal
    elif prev_macd >= prev_signal and macd < signal:
        return 'sell'
    else:
        return 'hold'
```

EXAMPLE INPUT: "Buy when 50 EMA crosses above 200 EMA, sell on reverse"

EXAMPLE OUTPUT:
```python
def strategy(data):
    ema50 = data['ema50']
    ema200 = data['ema200']
    prev_ema50 = data['prev_ema50']
    prev_ema200 = data['prev_ema200']
    
    # Golden cross
    if prev_ema50 <= prev_ema200 and ema50 > ema200:
        return 'buy'
    # Death cross
    elif prev_ema50 >= prev_ema200 and ema50 < ema200:
        return 'sell'
    else:
        return 'hold'
```

IMPORTANT: Return ONLY the code, no explanations.
"""

def generate_strategy_code(natural_language: str) -> dict:
    """
    Convert natural language strategy to Python code.
    
    Args:
        natural_language: User's strategy description in English
        
    Returns:
        dict with 'code' (str) or 'error' (str)
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": natural_language}
            ],
            temperature=0.3,  # Lower temperature for more deterministic code
            max_tokens=500,
        )
        
        generated_code = response.choices[0].message.content.strip()
        
        # Extract code from markdown code blocks if present
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0].strip()
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()
        
        # Validate the code (basic safety check)
        validation = validate_code(generated_code)
        if not validation["valid"]:
            return {"error": validation["message"]}
        
        return {"code": generated_code}
        
    except Exception as e:
        return {"error": f"AI generation failed: {str(e)}"}


def validate_code(code: str) -> dict:
    """
    Basic safety validation for generated code.
    
    Args:
        code: Generated Python code
        
    Returns:
        dict with 'valid' (bool) and 'message' (str)
    """
    # Check for dangerous patterns
    dangerous_patterns = [
        "import os",
        "import sys",
        "import subprocess",
        "eval(",
        "exec(",
        "open(",
        "rm ",
        "del ",
        "__class__",
        "__import__",
    ]
    
    for pattern in dangerous_patterns:
        if pattern in code:
            return {
                "valid": False,
                "message": f"Code contains unsafe pattern: {pattern}"
            }
    
    # Check for required function signature
    if "def strategy(data):" not in code:
        return {
            "valid": False,
            "message": "Code must contain 'def strategy(data):' function"
        }
    
    # Check for return statement
    if "return" not in code:
        return {
            "valid": False,
            "message": "Code must have return statement"
        }
    
    return {"valid": True, "message": "Code passed validation"}


# Test function
if __name__ == "__main__":
    # Test with example strategy
    test_strategy = "Buy when RSI < 30, sell when RSI > 70"
    result = generate_strategy_code(test_strategy)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("Generated Code:")
        print(result["code"])
