"""
StrategyAI - Enhanced Backtester
Supports: Long/Short, Partial Exits, Trailing Stops, Position Sizing
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime
import ccxt
import logging

# Import cleanup function from ai_generator
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_generator import cleanup_strategy_code

# Debug logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Backtester:
    """
    Enhanced backtester with advanced features:
    - Long and short positions
    - Partial position sizing (0-100%)
    - Trailing stops
    - Multiple exit conditions
    - Advanced risk metrics
    """
    
    def __init__(self, initial_capital: float = 10000, fee_rate: float = 0.001, slippage: float = 0.0005):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage = slippage
    
    def run(self, df: pd.DataFrame, strategy_code: str, use_trailing_stop: bool = False, 
            trailing_stop_pct: float = 0.02, position_size_pct: float = 1.0) -> Dict:
        """
        Run backtest with enhanced features.
        
        Args:
            df: DataFrame with OHLCV + indicators
            strategy_code: Python code string from AI generator
            use_trailing_stop: Enable trailing stop
            trailing_stop_pct: Trailing stop percentage (e.g., 0.02 = 2%)
            position_size_pct: Position size as percentage of capital (0.0-1.0)
            
        Returns:
            Dict with backtest results
        """
        try:
            logger.debug(f"🔍 BACKTEST STARTED: {len(df)} candles, initial_capital={self.initial_capital}")
            logger.debug(f"📝 Strategy code length: {len(strategy_code)} chars")
            print(f"[BACKTEST] Starting backtest with {len(df)} candles, initial_capital={self.initial_capital}")
            
            # SECURITY: Create sandboxed namespace and execute strategy code
            safe_builtins = self._create_safe_builtins()
            local_ns = {'__builtins__': safe_builtins}
            
            logger.debug("🔧 Executing strategy code in sandbox...")
            print(f"[BACKTEST] Strategy code length: {len(strategy_code)} chars")
            
            # CRITICAL: Clean up any trailing code before execution
            strategy_code = cleanup_strategy_code(strategy_code)
            print(f"[BACKTEST] Cleaned code length: {len(strategy_code)} chars")
            print(f"[BACKTEST] Strategy code (first 500 chars): {strategy_code[:500]}")
            print(f"[BACKTEST] Strategy code (last 200 chars): {strategy_code[-200:]}")
            try:
                exec(strategy_code, local_ns, local_ns)
                logger.debug("✅ Strategy code executed successfully")
            except NameError as ne:
                logger.error(f"❌ NameError during exec: {ne}")
                logger.error(f"This usually means code references undefined variables at module level")
                logger.error(f"Strategy code should ONLY contain function definitions (def), no top-level code")
                return {"error": f"Strategy code error: {str(ne)}. Make sure code only contains function definitions, no test code or example usage."}
            except Exception as ex:
                logger.error(f"❌ Error during exec: {ex}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {"error": f"Strategy code execution failed: {str(ex)}"}
            
            strategy_func = local_ns.get('strategy')
            
            if not strategy_func:
                logger.error("❌ BACKTEST ERROR: No strategy function found")
                print("[BACKTEST] ERROR: No strategy function found")
                return {"error": "Strategy function not found. Add 'def strategy(data):'"}
            
            logger.debug(f"✅ Strategy function found: {strategy_func}")
            
            # PRE-COMPUTE ALL SIGNALS (run strategy once on full dataset)
            logger.debug(f"📡 PRE-COMPUTING SIGNALS on full dataset...")
            
            try:
                # Prepare data dictionary for strategy
                data_full = self._prepare_data(df, len(df) - 1)
                logger.debug(f"📦 Data prepared: keys={list(data_full.keys())}, close_len={len(data_full['close'])}")
                
                # Verify strategy function is callable
                if not callable(strategy_func):
                    logger.error("❌ strategy_func is not callable")
                    return {"error": "Strategy function is not callable"}
                
                logger.debug(f"🔧 Calling strategy_func with data_full (type={type(data_full)})")
                logger.debug(f"   data_full keys: {list(data_full.keys())}")
                logger.debug(f"   strategy_func source (first 500 chars): {str(strategy_func)[:500]}")
                
                # Call strategy function
                buy_signals_full, sell_signals_full = strategy_func(data_full)
                logger.debug(f"✅ SIGNALS COMPUTED: {np.sum(buy_signals_full)} buy signals, {np.sum(sell_signals_full)} sell signals")
                print(f"[BACKTEST] Found {np.sum(buy_signals_full)} buy signals, {np.sum(sell_signals_full)} sell signals")
                
            except NameError as ne:
                logger.error(f"❌ NameError in strategy: {ne}")
                logger.error(f"   This means strategy code references a variable that doesn't exist")
                logger.error(f"   Common causes:")
                logger.error(f"   1. Typo in variable name (e.g., 'dat' instead of 'data')")
                logger.error(f"   2. Using 'data' outside of function definition")
                logger.error(f"   3. Missing import or helper function")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return {"error": f"Strategy code error: {str(ne)}. Check for typos or code outside function definitions."}
            except TypeError as te:
                logger.error(f"❌ TypeError calling strategy: {te}")
                logger.error(f"   strategy_func type: {type(strategy_func)}")
                logger.error(f"   data_full type: {type(data_full)}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return {"error": f"Strategy call failed: {str(te)}"}
            except Exception as e:
                import traceback
                logger.error(f"❌ SIGNAL GENERATION FAILED: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {"error": f"Strategy execution failed: {str(e)}"}
            
            print("[BACKTEST] Strategy function loaded successfully")
            
            # Initialize state
            capital = self.initial_capital
            position = 0  # -1 = short, 0 = none, 1 = long
            position_qty = 0  # Number of units
            entry_price = 0
            entry_time = None
            peak_price = 0  # For trailing stop
            unrealized_pnl = 0
            
            # Track all trades
            trades = []
            equity_curve = [self.initial_capital]
            drawdown_curve = [0]
            
            # Performance tracking
            total_trades = 0
            winning_trades = 0
            losing_trades = 0
            total_profit = 0
            total_loss = 0
            max_drawdown = 0
            peak_equity = self.initial_capital
            
            # Run through each candle (use pre-computed signals)
            print(f"[BACKTEST] Starting backtest loop with {len(df)} candles...")
            for i in range(1, len(df)):
                try:
                    row = df.iloc[i]
                    current_price = row['close']
                    
                    # Get pre-computed signals for this candle
                    buy_signal = buy_signals_full[i] if i < len(buy_signals_full) else False
                    sell_signal = sell_signals_full[i] if i < len(sell_signals_full) else False
                    
                    logger.debug(f"📊 Candle {i}: buy={buy_signal}, sell={sell_signal}, price={current_price}")
                except Exception as e:
                    print(f"[BACKTEST] ERROR at candle {i}: {e}")
                    import traceback
                    print(f"[BACKTEST] Traceback: {traceback.format_exc()}")
                    raise
                
                # Check for existing position exit
                if position != 0:
                    # Check trailing stop
                    if use_trailing_stop and position == 1:
                        peak_price = max(peak_price, current_price)
                        trail_stop = peak_price * (1 - trailing_stop_pct)
                        if current_price < trail_stop:
                            # Exit long
                            pnl = (current_price - entry_price) * position_qty
                            capital += current_price * position_qty - abs(pnl) * self.fee_rate
                            trades.append({
                                'entry_time': entry_time,
                                'exit_time': row.name,
                                'entry_price': entry_price,
                                'exit_price': current_price,
                                'side': 'LONG',
                                'quantity': position_qty,
                                'pnl': pnl,
                                'exit_reason': 'trailing_stop'
                            })
                            total_trades += 1
                            if pnl > 0:
                                winning_trades += 1
                                total_profit += pnl
                            else:
                                losing_trades += 1
                                total_loss += abs(pnl)
                            position = 0
                            position_qty = 0
                    
                    # Check regular exit
                    if sell_signal and position == 1:
                        # Exit long
                        pnl = (current_price - entry_price) * position_qty
                        capital += current_price * position_qty - abs(pnl) * self.fee_rate
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': row.name,
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'side': 'LONG',
                            'quantity': position_qty,
                            'pnl': pnl,
                            'exit_reason': 'signal'
                        })
                        total_trades += 1
                        if pnl > 0:
                            winning_trades += 1
                            total_profit += pnl
                        else:
                            losing_trades += 1
                            total_loss += abs(pnl)
                        position = 0
                        position_qty = 0
                    
                    elif sell_signal and position == -1:
                        # Exit short
                        pnl = (entry_price - current_price) * position_qty
                        capital += current_price * position_qty - abs(pnl) * self.fee_rate
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': row.name,
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'side': 'SHORT',
                            'quantity': position_qty,
                            'pnl': pnl,
                            'exit_reason': 'signal'
                        })
                        total_trades += 1
                        if pnl > 0:
                            winning_trades += 1
                            total_profit += pnl
                        else:
                            losing_trades += 1
                            total_loss += abs(pnl)
                        position = 0
                        position_qty = 0
                
                # Check for new entry (only if no position)
                if position == 0 and buy_signal:
                    logger.debug(f"💰 BUY SIGNAL at {current_price} (candle {i})")
                    # Calculate position size
                    position_value = capital * position_size_pct
                    position_qty = position_value / current_price
                    
                    # Enter long (default)
                    position = 1
                    entry_price = current_price
                    entry_time = row.name
                    peak_price = current_price
                    capital -= position_value  # Reserve capital
                    
                # Also support short selling
                if position == 0 and 'short_signal' in data:
                    short_signal = data['short_signal']
                    if hasattr(short_signal, '__len__') and len(short_signal) > 0:
                        short_signal = short_signal[-1]
                    if short_signal:
                        position = -1
                        position_qty = (capital * position_size_pct) / current_price
                        entry_price = current_price
                        entry_time = row.name
                        peak_price = current_price
                
                # Calculate unrealized PnL
                if position == 1:
                    unrealized_pnl = (current_price - entry_price) * position_qty
                elif position == -1:
                    unrealized_pnl = (entry_price - current_price) * position_qty
                else:
                    unrealized_pnl = 0
                
                # Update equity curve
                current_equity = capital + unrealized_pnl
                equity_curve.append(current_equity)
                
                # Update drawdown
                peak_equity = max(peak_equity, current_equity)
                drawdown = (peak_equity - current_equity) / peak_equity if peak_equity > 0 else 0
                drawdown_curve.append(drawdown)
                max_drawdown = max(max_drawdown, drawdown)
            
            # Close any remaining position at end
            if position != 0:
                final_price = df.iloc[-1]['close']
                if position == 1:
                    pnl = (final_price - entry_price) * position_qty
                else:
                    pnl = (entry_price - final_price) * position_qty
                capital += final_price * position_qty - abs(pnl) * self.fee_rate
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': df.iloc[-1].name,
                    'entry_price': entry_price,
                    'exit_price': final_price,
                    'side': 'LONG' if position == 1 else 'SHORT',
                    'quantity': position_qty,
                    'pnl': pnl,
                    'exit_reason': 'end_of_data'
                })
                total_trades += 1
                if pnl > 0:
                    winning_trades += 1
                    total_profit += pnl
                else:
                    losing_trades += 1
                    total_loss += abs(pnl)
            
            # Calculate metrics
            final_capital = capital
            total_pnl = final_capital - self.initial_capital
            return_pct = (total_pnl / self.initial_capital) * 100
            
            # Sharpe ratio (simplified)
            equity_array = np.array(equity_curve)
            returns = np.diff(equity_array) / equity_array[:-1]
            sharpe = np.sqrt(252) * np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0
            
            # Win rate
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Profit factor
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            # Max consecutive wins/losses
            max_consecutive_wins = self._max_consecutive(trades, True)
            max_consecutive_losses = self._max_consecutive(trades, False)
            
            # Ensure we always return valid data
            if not equity_curve:
                print("[BACKTEST] WARNING: equity_curve is empty, setting to [initial_capital]")
                equity_curve = [self.initial_capital]
            if not drawdown_curve:
                drawdown_curve = [0]
            
            logger.info(f"✅ BACKTEST COMPLETE: final_capital={final_capital}, total_trades={total_trades}, return={return_pct:.2f}%")
            logger.debug(f"📈 Equity curve length: {len(equity_curve)}, Trades: {len(trades)}")
            print(f"[BACKTEST] Results: final_capital={final_capital}, total_trades={total_trades}, equity_curve_len={len(equity_curve)}")
            
            return {
                'success': True,
                'metrics': {
                    'final_capital': round(final_capital, 2),
                    'total_pnl': round(total_pnl, 2),
                    'return_pct': round(return_pct, 2),
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': round(win_rate, 2),
                    'profit_factor': round(profit_factor, 2),
                    'sharpe_ratio': round(sharpe, 2),
                    'max_drawdown': round(max_drawdown * 100, 2),
                    'max_consecutive_wins': max_consecutive_wins,
                    'max_consecutive_losses': max_consecutive_losses,
                },
                'trades': trades[:50],
                'equity_curve': [float(x) for x in equity_curve],
                'drawdown_curve': [float(x) for x in drawdown_curve],
                'initial_capital': float(self.initial_capital)
            }
            
        except Exception as e:
            import traceback
            return {
                'error': f'Backtest failed: {str(e)}',
                'traceback': traceback.format_exc()
            }
    
    def _create_safe_builtins(self) -> Dict:
        """Create sandboxed builtins for strategy execution"""
        import builtins as builtin_module
        
        safe_builtins = {
            'len': len, 'range': range, 'abs': abs,
            'min': min, 'max': max, 'sum': sum,
            'pow': pow, 'round': round, 'zip': zip,
            'enumerate': enumerate, 'Exception': Exception,
            'bool': bool, 'int': int, 'float': float,
            'str': str, 'list': list, 'tuple': tuple,
            'dict': dict, 'set': set, 'type': type,
            'True': True, 'False': False, 'None': None,
        }
        
        # Block dangerous imports with a callable function
        dangerous_modules = ['os', 'sys', 'subprocess', 'socket', 'requests',
                           'urllib', 'http', 'ftplib', 'smtplib', 'pickle']
        
        # Get the real __import__ from builtin_module (works whether __builtins__ is dict or module)
        real_import = builtin_module.__import__
        
        def restricted_import(name, *args, **kwargs):
            if any(name.startswith(d) for d in dangerous_modules):
                raise ImportError(f"Import of '{name}' is not allowed for security")
            # Allow safe imports using the real __import__
            return real_import(name, *args, **kwargs)
        
        safe_builtins['__import__'] = restricted_import
        
        import numpy as np
        safe_builtins['np'] = np
        safe_builtins['numpy'] = np
        
        return safe_builtins
    
    def _prepare_data(self, df: pd.DataFrame, idx: int) -> Dict:
        """Prepare data arrays for strategy"""
        return {
            'close': df['close'].iloc[:idx+1].values,
            'open': df['open'].iloc[:idx+1].values,
            'high': df['high'].iloc[:idx+1].values,
            'low': df['low'].iloc[:idx+1].values,
            'volume': df['volume'].iloc[:idx+1].values,
            'rsi': df['rsi'].iloc[:idx+1].values if 'rsi' in df.columns else np.zeros(idx+1),
            'macd': df['macd'].iloc[:idx+1].values if 'macd' in df.columns else np.zeros(idx+1),
            'signal': df['signal'].iloc[:idx+1].values if 'signal' in df.columns else np.zeros(idx+1),
            'ema50': df['ema50'].iloc[:idx+1].values if 'ema50' in df.columns else np.zeros(idx+1),
            'ema200': df['ema200'].iloc[:idx+1].values if 'ema200' in df.columns else np.zeros(idx+1),
            'bb_upper': df['bb_upper'].iloc[:idx+1].values if 'bb_upper' in df.columns else np.zeros(idx+1),
            'bb_lower': df['bb_lower'].iloc[:idx+1].values if 'bb_lower' in df.columns else np.zeros(idx+1),
            'atr': df['atr'].iloc[:idx+1].values if 'atr' in df.columns else np.zeros(idx+1),
        }
    
    def _max_consecutive(self, trades: list, wins: bool) -> int:
        """Calculate max consecutive wins or losses"""
        if not trades:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in trades:
            is_win = trade['pnl'] > 0
            if is_win == wins:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive


def run_backtest(code: str, symbol: str, timeframe: str, initial_capital: float,
                 fee_rate: float = 0.001, slippage: float = 0.0005,
                 api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 validate: bool = True, position_size: float = 1.0,
                 trailing_stop: str = "false") -> Dict:
    """
    Main backtest function with all parameters.
    
    Args:
        code: Strategy code
        symbol: Trading pair (e.g., BTC/USDT)
        timeframe: Candle timeframe (e.g., 1h, 4h, 1d)
        initial_capital: Starting capital
        fee_rate: Trading fee
        slippage: Slippage rate
        api_key: Bitget API key (optional)
        api_secret: Bitget API secret (optional)
        validate: Run validation checks
        position_size: Position size as fraction (0.0-1.0)
        trailing_stop: "false" or percentage (e.g., "0.02")
    
    Returns:
        Dict with backtest results
    """
    try:
        # Step 1: Validate code
        if validate:
            from ai_generator import validate_strategy
            validation = validate_strategy(code)
            if not validation['valid']:
                return {
                    'error': 'Code validation failed',
                    'validation_errors': validation['errors']
                }
        
        # Step 2: Fetch data
        from backtester import BitgetDataFetcher
        fetcher = BitgetDataFetcher(api_key, api_secret)
        df = fetcher.fetch(symbol, timeframe)
        
        if 'error' in df:
            return df
        
        # Step 3: Run backtest
        backtester = Backtester(initial_capital=initial_capital, fee_rate=fee_rate, slippage=slippage)
        
        use_trailing = trailing_stop.lower() != "false"
        trail_pct = float(trailing_stop) if use_trailing else 0.02
        
        return backtester.run(
            df=df,
            strategy_code=code,
            use_trailing_stop=use_trailing,
            trailing_stop_pct=trail_pct,
            position_size_pct=position_size
        )
        
    except Exception as e:
        import traceback
        return {
            'error': f'Backtest failed: {str(e)}',
            'traceback': traceback.format_exc()
        }


class BitgetDataFetcher:
    """Fetch OHLCV data from Bitget"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        import ccxt
        self.exchange = ccxt.bitget({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
    
    def fetch(self, symbol: str, timeframe: str, limit: int = 1000) -> pd.DataFrame:
        """Fetch OHLCV data and calculate indicators"""
        try:
            logger.debug(f"📡 FETCHING DATA: {symbol} {timeframe} (limit={limit})")
            print(f"[FETCH] Fetching {symbol} {timeframe} data...")
            # Fetch candles
            bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            logger.debug(f"📦 RAW DATA: {len(bars)} bars received")
            print(f"[FETCH] Got {len(bars)} bars")
            
            if len(bars) == 0:
                print("[FETCH] ERROR: No data returned from exchange")
                return {'error': 'No data returned from exchange'}
            
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Calculate indicators
            df['rsi'] = self._calculate_rsi(df['close'], 14)
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema12 - ema26
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
            df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
            df['sma20'] = df['close'].rolling(window=20).mean()
            df['sma50'] = df['close'].rolling(window=50).mean()
            
            # Bollinger Bands
            sma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            df['bb_upper'] = sma20 + 2 * std20
            df['bb_lower'] = sma20 - 2 * std20
            df['bb_middle'] = sma20
            
            # ATR
            df['atr'] = self._calculate_atr(df, 14)
            
            logger.debug(f"✅ DATA READY: {len(df)} rows, columns: {list(df.columns)}")
            logger.debug(f"📊 First row: open={df['open'].iloc[0]}, close={df['close'].iloc[0]}")
            print(f"[FETCH] Success: {len(df)} rows, columns: {list(df.columns)}")
            return df
            
        except Exception as e:
            import traceback
            print(f"[FETCH] ERROR: {str(e)}")
            print(f"[FETCH] Traceback: {traceback.format_exc()}")
            return {'error': f'Failed to fetch data: {str(e)}'}
    
    def _calculate_rsi(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate ATR"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()
