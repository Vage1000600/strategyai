"""
StrategyAI - Hybrid Strategy Code Generator
DEFAULT: Local reasoning (no API key needed)
OPTIONAL: DeepSeek API for better results (if API key provided)

Inspired by: AgentFlow Infra local reasoning
"""

import os
import re
from typing import Dict, List

# Try to import OpenAI for DeepSeek support (optional)
try:
    from openai import OpenAI
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False


class LocalStrategyGenerator:
    """
    Local strategy code generator using rule-based parsing.
    No external API calls needed!
    """
    
    # Indicator patterns
    PATTERNS = {
        'rsi': {
            'keywords': ['rsi', 'relative strength'],
            'code': "data['rsi']",
            'import': None
        },
        'macd': {
            'keywords': ['macd', 'moving average convergence'],
            'code': "data['macd']",
            'import': None
        },
        'signal': {
            'keywords': ['signal line', 'signal'],
            'code': "data['signal']",
            'import': None
        },
        'ema': {
            'keywords': ['ema', 'exponential moving average'],
            'code': "data['ema50']",
            'import': None
        },
        'sma': {
            'keywords': ['sma', 'simple moving average', 'moving average'],
            'code': "data['sma20']",
            'import': None
        },
        'bollinger': {
            'keywords': ['bollinger', 'bb'],
            'code': "data['bb_upper']",
            'import': None
        },
        'atr': {
            'keywords': ['atr', 'average true range'],
            'code': "data['atr']",
            'import': None
        },
        'price': {
            'keywords': ['price', 'close'],
            'code': "data['close']",
            'import': None
        },
        'high': {
            'keywords': ['high', 'breaks above'],
            'code': "data['high']",
            'import': None
        },
        'low': {
            'keywords': ['low', 'breaks below'],
            'code': "data['low']",
            'import': None
        }
    }
    
    # Condition templates
    CONDITION_TEMPLATES = {
        'rsi_oversold': "if data['rsi'] < 30:",
        'rsi_overbought': "if data['rsi'] > 70:",
        'macd_cross_above': "if data['macd'] > data['signal'] and data.get('prev_macd', 0) <= data.get('prev_signal', 0):",
        'macd_cross_below': "if data['macd'] < data['signal'] and data.get('prev_macd', 0) >= data.get('prev_signal', 0):",
        'ema_cross_above': "if data['ema50'] > data['ema200'] and data.get('prev_ema50', 0) <= data.get('prev_ema200', 0):",
        'ema_cross_below': "if data['ema50'] < data['ema200'] and data.get('prev_ema50', 0) >= data.get('prev_ema200', 0):",
        'price_above_sma': "if data['close'] > data['sma20']:",
        'price_below_sma': "if data['close'] < data['sma20']:",
        'price_break_high': "if data['close'] > data['high']:",
        'price_break_low': "if data['close'] < data['low']:",
        'bollinger_upper': "if data['close'] > data['bb_upper']:",
        'bollinger_lower': "if data['close'] < data['bb_lower']:",
    }
    
    def parse_strategy(self, strategy_input: str) -> Dict:
        """Parse natural language strategy into components"""
        strategy_input_lower = strategy_input.lower()
        indicators_used = set()
        conditions = []
        
        # Detect indicators
        for indicator, config in self.PATTERNS.items():
            for keyword in config['keywords']:
                if keyword in strategy_input_lower:
                    indicators_used.add(indicator)
                    break
        
        # Detect conditions
        if 'rsi' in strategy_input_lower:
            if '< 30' in strategy_input_lower or 'below 30' in strategy_input_lower or 'oversold' in strategy_input_lower:
                conditions.append(('buy', 'rsi_oversold'))
            if '> 70' in strategy_input_lower or 'above 70' in strategy_input_lower or 'overbought' in strategy_input_lower:
                conditions.append(('sell', 'rsi_overbought'))
        
        if 'macd' in strategy_input_lower:
            if 'cross' in strategy_input_lower and 'above' in strategy_input_lower:
                conditions.append(('buy', 'macd_cross_above'))
            if 'cross' in strategy_input_lower and 'below' in strategy_input_lower:
                conditions.append(('sell', 'macd_cross_below'))
        
        if 'ema' in strategy_input_lower or ('golden' in strategy_input_lower and 'cross' in strategy_input_lower):
            if 'above' in strategy_input_lower or 'cross' in strategy_input_lower:
                conditions.append(('buy', 'ema_cross_above'))
            if 'below' in strategy_input_lower or 'death' in strategy_input_lower:
                conditions.append(('sell', 'ema_cross_below'))
        
        if 'bollinger' in strategy_input_lower or 'bb' in strategy_input_lower:
            if 'above' in strategy_input_lower or 'break' in strategy_input_lower:
                conditions.append(('buy', 'bollinger_upper'))
            if 'below' in strategy_input_lower:
                conditions.append(('sell', 'bollinger_lower'))
        
        # Default if nothing detected
        if not conditions:
            conditions = [('buy', 'rsi_oversold'), ('sell', 'rsi_overbought')]
        
        # Generate code
        return self._generate_code(conditions, list(indicators_used), strategy_input)
    
    def _generate_code(self, conditions: List, indicators: List, strategy_input: str) -> Dict:
        """Generate Python code from parsed components"""
        
        code_lines = [
            "def strategy(data):",
            "    \"\"\"",
            "    Trading strategy generated by StrategyAI",
            f"    Input: {strategy_input[:50]}...",
            "    Output: 'buy', 'sell', or 'hold'",
            "    \"\"\"",
            ""
        ]
        
        # Add indicator variables
        if indicators:
            code_lines.append("    # Indicators used")
            for indicator in sorted(indicators):
                if indicator in self.PATTERNS:
                    code_lines.append(f"    {indicator} = {self.PATTERNS[indicator]['code']}")
            code_lines.append("")
        
        # Generate conditions
        buy_conditions = [c for c in conditions if c[0] == 'buy']
        sell_conditions = [c for c in conditions if c[0] == 'sell']
        
        if buy_conditions:
            code_lines.append("    # Buy conditions")
            buy_checks = []
            for _, condition_name in buy_conditions:
                if condition_name in self.CONDITION_TEMPLATES:
                    template = self.CONDITION_TEMPLATES[condition_name]
                    condition = template.replace('if ', '').rstrip(':')
                    buy_checks.append(condition)
            
            if buy_checks:
                combined_buy = ' or '.join(buy_checks)
                code_lines.append(f"    if {combined_buy}:")
                code_lines.append("        return 'buy'")
                code_lines.append("")
        
        if sell_conditions:
            code_lines.append("    # Sell conditions")
            sell_checks = []
            for _, condition_name in sell_conditions:
                if condition_name in self.CONDITION_TEMPLATES:
                    template = self.CONDITION_TEMPLATES[condition_name]
                    condition = template.replace('if ', '').rstrip(':')
                    sell_checks.append(condition)
            
            if sell_checks:
                combined_sell = ' or '.join(sell_checks)
                code_lines.append(f"    elif {combined_sell}:")
                code_lines.append("        return 'sell'")
                code_lines.append("")
        
        code_lines.append("    # Default")
        code_lines.append("    return 'hold'")
        
        final_code = '\n'.join(code_lines)
        
        # Classify strategy
        strategy_type = self._classify_strategy(indicators)
        
        return {
            'code': final_code,
            'strategy_type': strategy_type,
            'indicators': indicators,
            'conditions': conditions,
            'method': 'local'
        }
    
    def _classify_strategy(self, indicators: List) -> str:
        """Classify the strategy type"""
        if 'rsi' in indicators:
            if 'macd' in indicators:
                return 'RSI + MACD Combo (Local)'
            return 'RSI Strategy (Local)'
        elif 'macd' in indicators:
            return 'MACD Strategy (Local)'
        elif 'ema' in indicators:
            return 'Moving Average Crossover (Local)'
        elif 'bollinger' in indicators:
            return 'Bollinger Bands Strategy (Local)'
        else:
            return 'Custom Strategy (Local)'


class DeepSeekStrategyGenerator:
    """
    DeepSeek API-based strategy generator (optional, requires API key)
    Provides better code quality for complex strategies
    """
    
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
8. Return ONLY the code, no explanations

EXAMPLE INPUT: "Buy when RSI < 30, sell when RSI > 70"

EXAMPLE OUTPUT:
def strategy(data):
    rsi = data['rsi']
    
    if rsi < 30:
        return 'buy'
    elif rsi > 70:
        return 'sell'
    else:
        return 'hold'
"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
    
    def generate(self, natural_language: str) -> Dict:
        """Generate strategy code using DeepSeek API"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": natural_language}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            generated_code = response.choices[0].message.content.strip()
            
            # Extract code from markdown blocks
            if "```python" in generated_code:
                generated_code = generated_code.split("```python")[1].split("```")[0].strip()
            elif "```" in generated_code:
                generated_code = generated_code.split("```")[1].split("```")[0].strip()
            
            return {
                'code': generated_code,
                'strategy_type': 'AI-Generated (DeepSeek)',
                'method': 'deepseek',
                'indicators': self._detect_indicators(generated_code)
            }
            
        except Exception as e:
            return {
                'error': f"DeepSeek API failed: {str(e)}",
                'fallback': True
            }
    
    def _detect_indicators(self, code: str) -> List[str]:
        """Detect which indicators are used in generated code"""
        indicators = []
        if 'rsi' in code:
            indicators.append('rsi')
        if 'macd' in code:
            indicators.append('macd')
        if 'ema' in code:
            indicators.append('ema')
        if 'sma' in code:
            indicators.append('sma')
        if 'bb' in code or 'bollinger' in code:
            indicators.append('bollinger')
        if 'atr' in code:
            indicators.append('atr')
        return indicators


def generate_strategy_code(natural_language: str, use_deepseek: bool = False) -> Dict:
    """
    Main function - Generate strategy code from natural language.
    
    Args:
        natural_language: User's strategy description
        use_deepseek: If True and API key available, use DeepSeek (better quality)
                     If False or no API key, use local reasoning (free, fast)
        
    Returns:
        Dict with 'code' (str) and metadata
    """
    # Check if DeepSeek API key is available
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    has_deepseek = deepseek_api_key and DEEPSEEK_AVAILABLE
    
    # Use DeepSeek if requested and available
    if use_deepseek and has_deepseek:
        generator = DeepSeekStrategyGenerator(deepseek_api_key)
        result = generator.generate(natural_language)
        
        # If DeepSeek fails, fallback to local
        if result.get('fallback'):
            local_gen = LocalStrategyGenerator()
            result = local_gen.parse_strategy(natural_language)
        
        return result
    
    # Default: Use local reasoning (no API key needed)
    generator = LocalStrategyGenerator()
    return generator.parse_strategy(natural_language)


def get_default_strategy() -> str:
    """Return a safe default strategy"""
    return """
def strategy(data):
    # Default RSI strategy
    if data['rsi'] < 30:
        return 'buy'
    elif data['rsi'] > 70:
        return 'sell'
    else:
        return 'hold'
"""


# Test function
if __name__ == "__main__":
    # Test with example strategies
    test_strategies = [
        "Buy when RSI < 30, sell when RSI > 70",
        "Buy when MACD crosses above signal, sell when it crosses below",
        "Buy when 50 EMA crosses above 200 EMA (golden cross), sell on death cross",
        "Buy when price breaks above upper Bollinger Band, sell at middle band"
    ]
    
    print("="*60)
    print("Testing LOCAL Strategy Generator (No API Key)")
    print("="*60)
    
    for strategy in test_strategies:
        print(f"\nInput: {strategy}")
        result = generate_strategy_code(strategy, use_deepseek=False)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Type: {result['strategy_type']}")
            print(f"Method: {result.get('method', 'local')}")
            print(f"Code:\n{result['code']}")
            print("-"*60)
    
    # Test DeepSeek if available
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_key and DEEPSEEK_AVAILABLE:
        print("\n" + "="*60)
        print("Testing DeepSeek Strategy Generator (With API Key)")
        print("="*60)
        
        for strategy in test_strategies[:2]:  # Test first 2 only
            print(f"\nInput: {strategy}")
            result = generate_strategy_code(strategy, use_deepseek=True)
            
            print(f"Type: {result['strategy_type']}")
            print(f"Method: {result.get('method', 'unknown')}")
            print(f"Code:\n{result['code']}")
            print("-"*60)
