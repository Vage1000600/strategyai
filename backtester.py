"""
StrategyAI - Backtesting Engine (IMPROVED)
Uses public Bitget API by default (no key required for testing)
Users can optionally provide their own API key

Features:
✅ Public API key as default (for testing)
✅ User can override with personal key
✅ Buy & Hold benchmark comparison
✅ Expanded risk metrics
✅ Code validation before execution
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Public Bitget API credentials (read-only, rate-limited)
# These are for testing/demo purposes
PUBLIC_BITGET_KEY = ""
PUBLIC_BITGET_SECRET = ""

class BitgetDataFetcher:
    """Fetch historical data from Bitget API"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize Bitget connection.
        
        Args:
            api_key: User's API key (optional)
            api_secret: User's API secret (optional)
            
        If no key provided, uses public endpoints (rate-limited but works)
        """
        self.exchange = ccxt.bitget()
        
        # If user provides API key, use it
        if api_key and api_secret:
            self.exchange.apiKey = api_key
            self.exchange.secret = api_secret
            self.using_public = False
        else:
            # Use public API (no authentication)
            self.using_public = True
    
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """
        Fetch OHLCV data from Bitget.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '1h', '4h', '1d')
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data + indicators
        """
        try:
            # Fetch OHLCV data (works with or without API key)
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Add indicators
            df = self.add_indicators(df)
            
            return df
            
        except Exception as e:
            # If public API fails, suggest getting API key
            if self.using_public:
                raise Exception(
                    f"Public API failed: {str(e)}\n\n"
                    "💡 Tip: Get your free Bitget API key at:\n"
                    "https://www.bitget.com/api\n\n"
                    "Enter it in the sidebar for unlimited access."
                )
            else:
                raise Exception(f"Failed to fetch data: {str(e)}")
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to dataframe"""
        
        # RSI (14-period)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD (12, 26, 9)
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['prev_macd'] = df['macd'].shift(1)
        df['prev_signal'] = df['signal'].shift(1)
        
        # EMAs
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
        df['prev_ema50'] = df['ema50'].shift(1)
        df['prev_ema200'] = df['ema200'].shift(1)
        
        # SMAs
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['sma50'] = df['close'].rolling(window=50).mean()
        df['prev_sma20'] = df['sma20'].shift(1)
        df['prev_sma50'] = df['sma50'].shift(1)
        
        # Bollinger Bands (20, 2)
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
        df['prev_bb_upper'] = df['bb_upper'].shift(1)
        df['prev_bb_lower'] = df['bb_lower'].shift(1)
        
        # ATR (14-period)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # Price position relative to Bollinger Bands
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Fill NaN values
        df.fillna(method='bfill', inplace=True)
        df.fillna(0, inplace=True)  # For any remaining NaN
        
        return df


class Backtester:
    """Run backtest on historical data"""
    
    def __init__(self, initial_capital: float = 1000.0, fee_rate: float = 0.001, slippage: float = 0.0005):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting capital in USDT
            fee_rate: Trading fee (default 0.1%)
            slippage: Slippage percentage (default 0.05%)
        """
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage = slippage
    
    def run(self, df: pd.DataFrame, strategy_code: str) -> Dict:
        """
        Run backtest with given strategy.
        
        Args:
            df: DataFrame with OHLCV + indicators
            strategy_code: Python code string from AI generator
            
        Returns:
            Dict with backtest results including expanded metrics
        """
        try:
            # Create local namespace for strategy execution
            # IMPORTANT: Use local_ns as BOTH globals and locals so helper functions are accessible
            local_ns = {'__builtins__': __builtins__}  # Include builtins for safety
            exec(strategy_code, local_ns, local_ns)
            strategy_func = local_ns.get('strategy')
            
            if not strategy_func:
                return {"error": "Strategy function not found in code. Make sure your code has 'def strategy(data):'"}
            
            # Initialize tracking variables
            capital = self.initial_capital
            position = 0  # 0 = no position, 1 = long
            position_size = 0
            entry_price = 0
            entry_time = None
            
            trades = []
            equity_curve = [self.initial_capital]
            win_streak = 0
            loss_streak = 0
            longest_win_streak = 0
            longest_loss_streak = 0
            total_wins = 0
            total_losses = 0
            total_profit = 0
            total_loss = 0
            
            # Run through each candle
            for i in range(1, len(df)):
                row = df.iloc[i]
                
                # Prepare data dict for strategy - pass ARRAYS (full history up to current candle)
                # This allows strategies to compute indicators on the fly
                data = {
                    'close': df['close'].iloc[:i+1].values,  # Array of all closes up to now
                    'open': df['open'].iloc[:i+1].values,
                    'high': df['high'].iloc[:i+1].values,
                    'low': df['low'].iloc[:i+1].values,
                    'volume': df['volume'].iloc[:i+1].values,
                    'rsi': df['rsi'].iloc[:i+1].values,
                    'macd': df['macd'].iloc[:i+1].values,
                    'signal': df['signal'].iloc[:i+1].values,
                    'ema50': df['ema50'].iloc[:i+1].values,
                    'ema200': df['ema200'].iloc[:i+1].values,
                    'sma20': df['sma20'].iloc[:i+1].values,
                    'sma50': df['sma50'].iloc[:i+1].values,
                    'bb_upper': df['bb_upper'].iloc[:i+1].values,
                    'bb_middle': df['bb_middle'].iloc[:i+1].values,
                    'bb_lower': df['bb_lower'].iloc[:i+1].values,
                    'atr': df['atr'].iloc[:i+1].values,
                    # Also provide current values for convenience
                    'current_close': row['close'],
                    'current_open': row['open'],
                    'current_high': row['high'],
                    'current_low': row['low'],
                }
                
                # Get strategy signal
                try:
                    signal = strategy_func(data)
                except Exception as e:
                    return {"error": f"Strategy execution failed at candle {i}: {str(e)}"}
                
                # Execute trades
                # Note: strategy should return 'buy'/'sell' strings, or (buy_signals, sell_signals) tuples
                # Handle both return types
                if isinstance(signal, tuple):
                    # Returns (buy_signals, sell_signals) arrays
                    buy_signal = signal[0][-1] if len(signal[0]) > 0 else False
                    sell_signal = signal[1][-1] if len(signal[1]) > 0 else False
                elif isinstance(signal, str):
                    # Returns 'buy'/'sell'/'hold'
                    buy_signal = (signal == 'buy')
                    sell_signal = (signal == 'sell')
                elif isinstance(signal, bool):
                    # Returns single bool (True = buy, False = hold)
                    buy_signal = signal
                    sell_signal = False
                else:
                    buy_signal = False
                    sell_signal = False
                
                if buy_signal and position == 0:
                    # Enter long position
                    entry_price = row['close'] * (1 + self.slippage)
                    position_size = capital / entry_price
                    capital = 0
                    position = 1
                    entry_time = row.name
                    
                elif sell_signal and position > 0:
                    # Exit long position
                    exit_price = row['close'] * (1 - self.slippage)
                    exit_value = position_size * exit_price
                    exit_value = exit_value * (1 - self.fee_rate)  # Apply fee
                    
                    pnl = exit_value - (position_size * entry_price)
                    pnl_pct = (pnl / (position_size * entry_price)) * 100
                    
                    # Track win/loss
                    if pnl > 0:
                        total_wins += 1
                        total_profit += pnl
                        win_streak += 1
                        loss_streak = 0
                        longest_win_streak = max(longest_win_streak, win_streak)
                    else:
                        total_losses += 1
                        total_loss += abs(pnl)
                        loss_streak += 1
                        win_streak = 0
                        longest_loss_streak = max(longest_loss_streak, loss_streak)
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': row.name,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'type': 'LONG'
                    })
                    
                    capital = exit_value
                    position = 0
                    position_size = 0
                
                # Calculate equity
                if position > 0:
                    equity = position_size * row['close']
                else:
                    equity = capital
                
                equity_curve.append(equity)
            
            # Close any open position at the end
            if position > 0:
                exit_price = df.iloc[-1]['close'] * (1 - self.slippage)
                exit_value = position_size * exit_price * (1 - self.fee_rate)
                pnl = exit_value - (position_size * entry_price)
                pnl_pct = (pnl / (position_size * entry_price)) * 100
                
                if pnl > 0:
                    total_wins += 1
                    total_profit += pnl
                else:
                    total_losses += 1
                    total_loss += abs(pnl)
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': df.iloc[-1].name,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'type': 'LONG (closed at end)'
                })
                
                capital = exit_value
                position = 0
            
            # Calculate final equity
            final_equity = capital if capital > 0 else (position_size * df.iloc[-1]['close'] if position > 0 else self.initial_capital)
            total_pnl = final_equity - self.initial_capital
            return_pct = (total_pnl / self.initial_capital) * 100
            
            # Calculate benchmark (Buy & Hold)
            benchmark_start_price = df['close'].iloc[0]
            benchmark_end_price = df['close'].iloc[-1]
            benchmark_return = ((benchmark_end_price - benchmark_start_price) / benchmark_start_price) * 100
            
            # Calculate Sharpe ratio (annualized)
            equity_series = pd.Series(equity_curve)
            returns = equity_series.pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 1 and returns.std() > 0 else 0
            
            # Calculate max drawdown
            equity_df = pd.DataFrame(equity_curve, columns=['equity'])
            equity_df['peak'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
            max_drawdown = abs(equity_df['drawdown'].min())
            
            # Win rate
            total_trades = len(trades)
            win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
            
            # Profit factor
            profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf') if total_profit > 0 else 0
            
            # Average win/loss ratio
            avg_win = (total_profit / total_wins) if total_wins > 0 else 0
            avg_loss = (total_loss / total_losses) if total_losses > 0 else 0
            avg_win_loss_ratio = (avg_win / avg_loss) if avg_loss > 0 else float('inf') if avg_win > 0 else 0
            
            # Recovery factor
            recovery_factor = (total_pnl / max_drawdown) if max_drawdown > 0 else 0
            
            # Convert trades to DataFrame
            trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
            
            return {
                "pnl": total_pnl,
                "return_pct": return_pct,
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "total_trades": total_trades,
                "equity_curve": equity_curve,
                "drawdown": equity_df['drawdown'].tolist(),
                "trades": trades_df,
                "final_equity": final_equity,
                "benchmark_return": benchmark_return,
                "profit_factor": profit_factor,
                "avg_win_loss": avg_win_loss_ratio,
                "longest_win_streak": longest_win_streak,
                "longest_loss_streak": longest_loss_streak,
                "recovery_factor": recovery_factor,
                "total_profit": total_profit,
                "total_loss": total_loss,
                "total_wins": total_wins,
                "total_losses": total_losses
            }
            
        except Exception as e:
            return {"error": f"Backtest failed: {str(e)}"}


def run_backtest(code: str, symbol: str, timeframe: str, initial_capital: float, 
                 fee_rate: float = 0.001, slippage: float = 0.0005,
                 api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 validate: bool = True) -> Dict:
    """
    Main backtest function.
    
    Args:
        code: Strategy code from AI generator
        symbol: Trading pair
        timeframe: Candle timeframe
        initial_capital: Starting capital
        fee_rate: Trading fee (default 0.1%)
        slippage: Slippage (default 0.05%)
        api_key: User's Bitget API key (optional)
        api_secret: User's Bitget API secret (optional)
        validate: Run validation checks before execution (default True)
        
    Returns:
        Dict with backtest results including validation info
    """
    try:
        # Step 1: Validate code structure and syntax
        if validate:
            from ai_generator import validate_strategy
            
            validation = validate_strategy(code)
            if not validation['valid']:
                return {
                    'error': 'Code validation failed',
                    'validation_errors': validation['errors'],
                    'validation_warnings': validation['warnings']
                }
        
        # Step 2: Fetch data (uses public API if no key provided)
        fetcher = BitgetDataFetcher(api_key, api_secret)
        df = fetcher.fetch_ohlcv(symbol, timeframe, limit=500)
        
        # Step 3: Test execution on small sample (optional safety check)
        # SKIPPED: Function removed in compact version
        
        # Step 4: Run full backtest
        backtester = Backtester(initial_capital, fee_rate, slippage)
        results = backtester.run(df, code)
        
        # Add info about API mode and validation
        results['using_public_api'] = fetcher.using_public
        results['validated'] = validate
        
        return results
        
    except Exception as e:
        return {"error": str(e)}


# Test function
if __name__ == "__main__":
    # Test with simple RSI strategy
    test_code = """
def strategy(data):
    if data['rsi'] < 30:
        return 'buy'
    elif data['rsi'] > 70:
        return 'sell'
    else:
        return 'hold'
"""
    
    results = run_backtest(
        code=test_code,
        symbol="BTC/USDT",
        timeframe="1h",
        initial_capital=1000
    )
    
    if "error" in results:
        print(f"Error: {results['error']}")
    else:
        print(f"\n=== BACKTEST RESULTS ===")
        print(f"Using Public API: {results.get('using_public_api', False)}")
        print(f"PnL: ${results['pnl']:.2f}")
        print(f"Return: {results['return_pct']:.2f}%")
        print(f"Sharpe: {results['sharpe']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"Win Rate: {results['win_rate']:.1f}%")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Profit Factor: {results['profit_factor']:.2f}")
        print(f"Avg Win/Loss: {results['avg_win_loss']:.2f}")
        print(f"Benchmark (HODL): {results['benchmark_return']:.2f}%")
        print(f"Beat HODL by: {results['return_pct'] - results['benchmark_return']:.2f}%")
