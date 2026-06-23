"""
StrategyAI - Test Suite
Tests for backtester, AI generator, and security
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import generate_strategy_code, validate_strategy
from backtester import Backtester


class TestAIGenerator(unittest.TestCase):
    """Test AI strategy generation"""
    
    def test_local_rsi_template(self):
        """Test RSI template detection"""
        result = generate_strategy_code("Buy when RSI < 30, sell when RSI > 70", provider='local')
        self.assertEqual(result['provider'], 'local')
        self.assertIn('rsi', result['code'].lower())
        self.assertTrue(result['code'].startswith('import numpy'))
    
    def test_local_macd_template(self):
        """Test MACD template detection"""
        result = generate_strategy_code("MACD crossover strategy", provider='local')
        self.assertEqual(result['provider'], 'local')
        self.assertIn('macd', result['code'].lower())
    
    def test_local_golden_cross(self):
        """Test Golden Cross template"""
        result = generate_strategy_code("Golden cross 50 EMA 200 EMA", provider='local')
        self.assertEqual(result['provider'], 'local')
        self.assertIn('ema50', result['code'].lower())
        self.assertIn('ema200', result['code'].lower())
    
    def test_validation_syntax_error(self):
        """Test that syntax errors are caught"""
        bad_code = "def strategy(data):\n    return True, False\n    print('unclosed"
        validation = validate_strategy(bad_code)
        self.assertFalse(validation['valid'])
        self.assertTrue(len(validation['errors']) > 0)
    
    def test_validation_missing_strategy(self):
        """Test that missing strategy function is caught"""
        bad_code = "import numpy as np\n# No strategy function"
        validation = validate_strategy(bad_code)
        self.assertFalse(validation['valid'])
    
    def test_validation_security(self):
        """Test that dangerous code is caught"""
        bad_code = "import os\nos.system('rm -rf /')\ndef strategy(data):\n    return True, False"
        validation = validate_strategy(bad_code)
        self.assertFalse(validation['valid'])
        self.assertTrue(any('security' in e.lower() for e in validation['errors']))
    
    def test_valid_strategy_structure(self):
        """Test valid strategy passes validation"""
        good_code = """import numpy as np
def strategy(data):
    close = data['close']
    buy = close < 50000
    sell = close > 60000
    return buy, sell"""
        validation = validate_strategy(good_code)
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['errors']), 0)


class TestBacktester(unittest.TestCase):
    """Test backtester functionality"""
    
    def setUp(self):
        """Create sample data for tests"""
        np.random.seed(42)
        n = 100
        self.df = {
            'close': 50000 + np.cumsum(np.random.randn(n) * 100),
            'open': 50000 + np.cumsum(np.random.randn(n) * 100),
            'high': 50000 + np.cumsum(np.random.randn(n) * 100) + 50,
            'low': 50000 + np.cumsum(np.random.randn(n) * 100) - 50,
            'volume': np.random.randint(1000, 10000, n)
        }
        self.simple_strategy = """import numpy as np
def strategy(data):
    close = data['close']
    buy = close < np.mean(close)
    sell = close > np.mean(close)
    return buy, sell"""
    
    def test_backtester_initialization(self):
        """Test backtester initializes correctly"""
        backtester = Backtester(initial_capital=1000, fee_rate=0.001)
        self.assertEqual(backtester.initial_capital, 1000)
        self.assertEqual(backtester.fee_rate, 0.001)
    
    def test_backtester_runs_without_error(self):
        """Test backtester runs with valid strategy"""
        backtester = Backtester(initial_capital=1000)
        import pandas as pd
        df = pd.DataFrame(self.df)
        result = backtester.run(df, self.simple_strategy)
        self.assertIn('metrics', result)
        self.assertIn('final_capital', result['metrics'])
    
    def test_backtester_detects_no_trades(self):
        """Test backtester handles no trades"""
        no_trade_strategy = """import numpy as np
def strategy(data):
    return np.zeros(len(data['close']), dtype=bool), np.zeros(len(data['close']), dtype=bool)"""
        
        backtester = Backtester(initial_capital=1000)
        import pandas as pd
        df = pd.DataFrame(self.df)
        result = backtester.run(df, no_trade_strategy)
        self.assertEqual(result['metrics']['total_trades'], 0)
    
    def test_backtester_fee_impact(self):
        """Test that fees reduce returns"""
        backtester_no_fee = Backtester(initial_capital=1000, fee_rate=0.0)
        backtester_with_fee = Backtester(initial_capital=1000, fee_rate=0.01)
        
        import pandas as pd
        df = pd.DataFrame(self.df)
        result_no_fee = backtester_no_fee.run(df, self.simple_strategy)
        result_with_fee = backtester_with_fee.run(df, self.simple_strategy)
        
        # Fees should reduce final capital
        self.assertGreater(
            result_no_fee['metrics']['final_capital'],
            result_with_fee['metrics']['final_capital']
        )


class TestSecurity(unittest.TestCase):
    """Test security measures"""
    
    def test_no_os_import(self):
        """Test that os module cannot be imported in strategy"""
        malicious = """import os
def strategy(data):
    os.system('echo hacked')
    return True, False"""
        validation = validate_strategy(malicious)
        self.assertFalse(validation['valid'])
    
    def test_no_subprocess(self):
        """Test that subprocess is blocked"""
        malicious = """import subprocess
def strategy(data):
    subprocess.run(['ls'])
    return True, False"""
        validation = validate_strategy(malicious)
        self.assertFalse(validation['valid'])
    
    def test_no_eval(self):
        """Test that eval() is blocked"""
        malicious = """def strategy(data):
    eval('print("hacked")')
    return True, False"""
        validation = validate_strategy(malicious)
        self.assertFalse(validation['valid'])
    
    def test_no_exec(self):
        """Test that exec() is blocked"""
        malicious = """def strategy(data):
    exec('print("hacked")')
    return True, False"""
        validation = validate_strategy(malicious)
        self.assertFalse(validation['valid'])
    
    def test_no_network_calls(self):
        """Test that network calls are blocked"""
        malicious = """import requests
def strategy(data):
    requests.get('http://evil.com')
    return True, False"""
        validation = validate_strategy(malicious)
        self.assertFalse(validation['valid'])
    
    def test_no_file_operations(self):
        """Test that file operations are blocked"""
        malicious = """def strategy(data):
    with open('/etc/passwd', 'r') as f:
        print(f.read())
    return True, False"""
        validation = validate_strategy(malicious)
        self.assertFalse(validation['valid'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_empty_strategy_input(self):
        """Test empty strategy input"""
        result = generate_strategy_code("", provider='local')
        self.assertEqual(result['provider'], 'local')
        # Should return default strategy
    
    def test_very_long_strategy_input(self):
        """Test very long strategy description"""
        long_input = "Buy when RSI is very very very very very very very very very very low" * 100
        result = generate_strategy_code(long_input, provider='local')
        self.assertEqual(result['provider'], 'local')
    
    def test_special_characters_in_input(self):
        """Test special characters in strategy input"""
        result = generate_strategy_code("Buy when RSI < 30 & MACD > 0!", provider='local')
        self.assertEqual(result['provider'], 'local')
    
    def test_backtester_with_nan_data(self):
        """Test backtester handles NaN values"""
        import pandas as pd
        import numpy as np
        
        df = pd.DataFrame({
            'close': [50000, 51000, np.nan, 52000, 53000],
            'open': [50000, 51000, 51500, 52000, 53000],
            'high': [50500, 51500, 52000, 52500, 53500],
            'low': [49500, 50500, 51000, 51500, 52500],
            'volume': [1000, 2000, 3000, 4000, 5000]
        })
        
        backtester = Backtester(initial_capital=1000)
        strategy = """import numpy as np
def strategy(data):
    return np.array([False, True, False, False, False]), np.array([False, False, False, True, False])"""
        
        # Should not crash
        result = backtester.run(df, strategy)
        self.assertIn('metrics', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
