"""
StrategyAI - Backtesting Engine
Person 2: Backtesting Engine Lead

Runs trading strategies on historical Bitget data and calculates performance metrics.
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class BitgetDataFetcher:
    """Fetch historical data from Bitget API"""
    
    def __init__(self):
        self.exchange = ccxt.bitget()
    
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
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Add indicators
            df = self.add_indicators(df)
            
            return df
            
        except Exception as e:
            raise Exception(f"Failed to fetch data: {str(e)}")
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to dataframe"""
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
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
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # Fill NaN values
        df.fillna(method='bfill', inplace=True)
        
        return df


class Backtester:
    """Run backtest on historical data"""
    
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.fee_rate = 0.001  # 0.1% per trade (Bitget maker/taker)
        self.slippage = 0.0005  # 0.05% slippage
    
    def run(self, df: pd.DataFrame, strategy_code: str) -> Dict:
        """
        Run backtest with given strategy.
        
        Args:
            df: DataFrame with OHLCV + indicators
            strategy_code: Python code string from AI generator
            
        Returns:
            Dict with backtest results
        """
        try:
            # Create local namespace for strategy execution
            local_ns = {}
            exec(strategy_code, {}, local_ns)
            strategy_func = local_ns.get('strategy')
            
            if not strategy_func:
                return {"error": "Strategy function not found in code"}
            
            # Initialize tracking variables
            capital = self.initial_capital
            position = 0  # 0 = no position, 1 = long
            trades = []
            equity_curve = [self.initial_capital]
            
            # Run through each candle
            for i in range(1, len(df)):
                row = df.iloc[i]
                prev_row = df.iloc[i-1]
                
                # Prepare data dict for strategy
                data = {
                    'close': row['close'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'rsi': row['rsi'],
                    'macd': row['macd'],
                    'signal': row['signal'],
                    'prev_macd': row['prev_macd'],
                    'prev_signal': row['prev_signal'],
                    'ema50': row['ema50'],
                    'ema200': row['ema200'],
                    'prev_ema50': row['prev_ema50'],
                    'prev_ema200': row['prev_ema200'],
                }
                
                # Get strategy signal
                try:
                    signal = strategy_func(data)
                except Exception as e:
                    return {"error": f"Strategy execution failed: {str(e)}"}
                
                # Execute trades
                if signal == 'buy' and position == 0:
                    # Enter long position
                    position = capital / (row['close'] * (1 + self.slippage))
                    capital = 0
                    entry_price = row['close'] * (1 + self.slippage)
                    entry_time = row.name
                    
                elif signal == 'sell' and position > 0:
                    # Exit long position
                    exit_value = position * row['close'] * (1 - self.slippage - self.fee_rate)
                    pnl = exit_value - (position * entry_price)
                    pnl_pct = (pnl / (position * entry_price)) * 100
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': row.name,
                        'entry_price': entry_price,
                        'exit_price': row['close'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'type': 'LONG'
                    })
                    
                    capital = exit_value
                    position = 0
                
                # Calculate equity
                if position > 0:
                    equity = position * row['close']
                else:
                    equity = capital
                
                equity_curve.append(equity)
            
            # Close any open position at the end
            if position > 0:
                exit_value = position * df.iloc[-1]['close'] * (1 - self.slippage - self.fee_rate)
                pnl = exit_value - (position * entry_price)
                pnl_pct = (pnl / (position * entry_price)) * 100
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': df.iloc[-1].name,
                    'entry_price': entry_price,
                    'exit_price': df.iloc[-1]['close'],
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'type': 'LONG (closed at end)'
                })
                
                capital = exit_value
                position = 0
            
            # Calculate metrics
            final_equity = capital if capital > 0 else position * df.iloc[-1]['close']
            total_pnl = final_equity - self.initial_capital
            return_pct = (total_pnl / self.initial_capital) * 100
            
            # Calculate Sharpe ratio (simplified)
            equity_series = pd.Series(equity_curve)
            returns = equity_series.pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 1 else 0
            
            # Calculate max drawdown
            equity_df = pd.DataFrame(equity_curve, columns=['equity'])
            equity_df['peak'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
            max_drawdown = equity_df['drawdown'].min()
            
            # Win rate
            if trades:
                winning_trades = [t for t in trades if t['pnl'] > 0]
                win_rate = (len(winning_trades) / len(trades)) * 100
            else:
                win_rate = 0
            
            # Convert trades to DataFrame
            trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
            
            return {
                "pnl": total_pnl,
                "return_pct": return_pct,
                "sharpe": sharpe,
                "max_drawdown": abs(max_drawdown),
                "win_rate": win_rate,
                "total_trades": len(trades),
                "equity_curve": equity_curve,
                "drawdown": equity_df['drawdown'].tolist(),
                "trades": trades_df,
                "final_equity": final_equity
            }
            
        except Exception as e:
            return {"error": f"Backtest failed: {str(e)}"}


def run_backtest(code: str, symbol: str, timeframe: str, initial_capital: float) -> Dict:
    """
    Main backtest function.
    
    Args:
        code: Strategy code from AI generator
        symbol: Trading pair
        timeframe: Candle timeframe
        initial_capital: Starting capital
        
    Returns:
        Dict with backtest results
    """
    try:
        # Fetch data
        fetcher = BitgetDataFetcher()
        df = fetcher.fetch_ohlcv(symbol, timeframe, limit=500)
        
        # Run backtest
        backtester = Backtester(initial_capital)
        results = backtester.run(df, code)
        
        return results
        
    except Exception as e:
        return {"error": str(e)}


# Test function
if __name__ == "__main__":
    # Test with simple strategy
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
        print(f"PnL: ${results['pnl']:.2f}")
        print(f"Return: {results['return_pct']:.2f}%")
        print(f"Sharpe: {results['sharpe']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"Total Trades: {results['total_trades']}")
