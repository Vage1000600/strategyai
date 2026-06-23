"""
StrategyAI - Local Strategy Code Generator (NO API KEYS NEEDED)
Uses rule-based parsing instead of external AI API

Inspired by: AgentFlow Infra local reasoning
"""

import re
from typing import Dict, List


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
    
    # Action patterns
    ACTION_PATTERNS = {
        'buy': ['buy', 'enter long', 'go long', 'open position'],
        'sell': ['sell', 'exit', 'close position', 'take profit'],
        'hold': ['hold', 'wait', 'do nothing']
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
    
    def __init__(self):
        self.strategy_input = ""
        self.indicators_used = set()
        self.conditions = []
        self.actions = []
    
    def parse_strategy(self, strategy_input: str) -> Dict:
        """
        Parse natural language strategy into components.
        
        Args:
            strategy_input: User's strategy description
            
        Returns:
            Dict with parsed components
        """
        self.strategy_input = strategy_input.lower()
        
        # Detect indicators
        self._detect_indicators()
        
        # Detect conditions
        self._detect_conditions()
        
        # Detect actions
        self._detect_actions()
        
        # Generate code
        return self._generate_code()
    
    def _detect_indicators(self):
        """Detect which indicators are mentioned"""
        for indicator, config in self.PATTERNS.items():
            for keyword in config['keywords']:
                if keyword in self.strategy_input:
                    self.indicators_used.add(indicator)
                    break
    
    def _detect_conditions(self):
        """Detect trading conditions"""
        input_lower = self.strategy_input.lower()
        
        # RSI conditions
        if 'rsi' in input_lower:
            if '< 30' in input_lower or 'below 30' in input_lower or 'oversold' in input_lower:
                self.conditions.append(('buy', 'rsi_oversold'))
            if '> 70' in input_lower or 'above 70' in input_lower or 'overbought' in input_lower:
                self.conditions.append(('sell', 'rsi_overbought'))
        
        # MACD conditions
        if 'macd' in input_lower:
            if 'cross' in input_lower and 'above' in input_lower:
                self.conditions.append(('buy', 'macd_cross_above'))
            if 'cross' in input_lower and 'below' in input_lower:
                self.conditions.append(('sell', 'macd_cross_below'))
        
        # EMA conditions
        if 'ema' in input_lower or ('golden' in input_lower and 'cross' in input_lower):
            if 'above' in input_lower or 'cross' in input_lower:
                self.conditions.append(('buy', 'ema_cross_above'))
            if 'below' in input_lower or 'death' in input_lower:
                self.conditions.append(('sell', 'ema_cross_below'))
        
        # SMA conditions
        if 'sma' in input_lower or ('moving average' in input_lower and 'ema' not in input_lower):
            if 'above' in input_lower:
                self.conditions.append(('buy', 'price_above_sma'))
            if 'below' in input_lower:
                self.conditions.append(('sell', 'price_below_sma'))
        
        # Bollinger Bands
        if 'bollinger' in input_lower or 'bb' in input_lower:
            if 'above' in input_lower or 'break' in input_lower:
                self.conditions.append(('buy', 'bollinger_upper'))
            if 'below' in input_lower:
                self.conditions.append(('sell', 'bollinger_lower'))
        
        # Default if nothing detected
        if not self.conditions:
            # Fallback to simple RSI strategy
            self.conditions = [('buy', 'rsi_oversold'), ('sell', 'rsi_overbought')]
    
    def _detect_actions(self):
        """Detect buy/sell/hold actions"""
        input_lower = self.strategy_input.lower()
        
        for action, keywords in self.ACTION_PATTERNS.items():
            for keyword in keywords:
                if keyword in input_lower:
                    self.actions.append(action)
                    break
        
        # Default actions
        if not self.actions:
            self.actions = ['buy', 'sell', 'hold']
    
    def _generate_code(self) -> Dict:
        """Generate Python code from parsed components"""
        
        # Start with function signature
        code_lines = [
            "def strategy(data):",
            "    \"\"\"",
            "    Trading strategy generated by StrategyAI",
            "    Input: Natural language description",
            "    Output: 'buy', 'sell', or 'hold'",
            "    \"\"\"",
            ""
        ]
        
        # Add indicator variables (only the ones used)
        if self.indicators_used:
            code_lines.append("    # Indicators used in this strategy")
            for indicator in sorted(self.indicators_used):
                if indicator in self.PATTERNS:
                    code_lines.append(f"    {indicator} = {self.PATTERNS[indicator]['code']}")
            code_lines.append("")
        
        # Add conditions and actions
        code_lines.append("    # Trading logic")
        
        # Group by action
        buy_conditions = [c for c in self.conditions if c[0] == 'buy']
        sell_conditions = [c for c in self.conditions if c[0] == 'sell']
        
        # Generate buy logic
        if buy_conditions:
            code_lines.append("    # Buy conditions")
            buy_checks = []
            for _, condition_name in buy_conditions:
                if condition_name in self.CONDITION_TEMPLATES:
                    template = self.CONDITION_TEMPLATES[condition_name]
                    # Remove the trailing colon and 'if' for combining
                    condition = template.replace('if ', '').rstrip(':')
                    buy_checks.append(condition)
            
            if buy_checks:
                combined_buy = ' or '.join(buy_checks)
                code_lines.append(f"    if {combined_buy}:")
                code_lines.append("        return 'buy'")
                code_lines.append("")
        
        # Generate sell logic
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
        
        # Default hold
        code_lines.append("    # Default: hold")
        code_lines.append("    return 'hold'")
        
        # Join into final code
        final_code = '\n'.join(code_lines)
        
        return {
            'code': final_code,
            'indicators': list(self.indicators_used),
            'conditions': self.conditions,
            'actions': self.actions,
            'strategy_type': self._classify_strategy()
        }
    
    def _classify_strategy(self) -> str:
        """Classify the strategy type"""
        if 'rsi' in self.indicators_used:
            if 'macd' in self.indicators_used:
                return 'RSI + MACD Combo'
            return 'RSI Strategy'
        elif 'macd' in self.indicators_used:
            return 'MACD Strategy'
        elif 'ema' in self.indicators_used:
            return 'Moving Average Crossover'
        elif 'bollinger' in self.indicators_used:
            return 'Bollinger Bands Strategy'
        else:
            return 'Custom Strategy'


def generate_strategy_code(natural_language: str) -> Dict:
    """
    Main function - Generate strategy code from natural language.
    
    Args:
        natural_language: User's strategy description
        
    Returns:
        Dict with 'code' (str) or 'error' (str)
    """
    try:
        generator = LocalStrategyGenerator()
        result = generator.parse_strategy(natural_language)
        
        return {
            'code': result['code'],
            'strategy_type': result['strategy_type'],
            'indicators': result['indicators'],
            'conditions': result['conditions']
        }
        
    except Exception as e:
        return {
            'error': f"Strategy generation failed: {str(e)}",
            'code': get_default_strategy()
        }


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
    
    for strategy in test_strategies:
        print(f"\n{'='*60}")
        print(f"Input: {strategy}")
        print(f"{'='*60}")
        
        result = generate_strategy_code(strategy)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Strategy Type: {result['strategy_type']}")
            print(f"Indicators: {', '.join(result['indicators'])}")
            print(f"\nGenerated Code:\n{result['code']}")
