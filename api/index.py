"""
StrategyAI - Vercel Serverless Function
AI-Powered Trading Strategy Backtester
FastAPI-compatible handler for Vercel
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import generate_strategy_code
from backtester import run_backtest


def get_html_content() -> str:
    """Return the full HTML page"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StrategyAI - AI Trading Strategy Backtester</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <header class="py-8">
        <div class="container mx-auto px-4">
            <h1 class="text-5xl font-bold text-white text-center mb-2">🚀 StrategyAI</h1>
            <p class="text-xl text-white text-center opacity-90">Describe Your Strategy. We'll Code It. Backtest It. Optimize It.</p>
        </div>
    </header>

    <main class="container mx-auto px-4 pb-12">
        <div class="max-w-6xl mx-auto">
            <div class="bg-green-500 text-white p-4 rounded-lg mb-6 text-center">
                <strong>🎉 No Setup Required!</strong> Using public Bitget API. Add your API key below for unlimited access.
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-1">
                    <div class="card rounded-xl p-6 shadow-xl">
                        <h2 class="text-2xl font-bold text-gray-800 mb-4">⚙️ Settings</h2>
                        <form id="backtestForm" onsubmit="runBacktest(event)">
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">🔑 Bitget API Key (Optional)</label>
                                <input type="password" id="api_key" name="api_key" class="w-full px-3 py-2 border border-gray-300 rounded-lg" placeholder="Leave empty for public API">
                            </div>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">🔐 API Secret (Optional)</label>
                                <input type="password" id="api_secret" name="api_secret" class="w-full px-3 py-2 border border-gray-300 rounded-lg" placeholder="Leave empty for public API">
                            </div>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">📊 Trading Pair</label>
                                <select id="symbol" name="symbol" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                    <option value="BTC/USDT">BTC/USDT</option>
                                    <option value="ETH/USDT">ETH/USDT</option>
                                    <option value="SOL/USDT">SOL/USDT</option>
                                    <option value="XRP/USDT">XRP/USDT</option>
                                    <option value="BNB/USDT">BNB/USDT</option>
                                </select>
                            </div>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">⏱️ Timeframe</label>
                                <select id="timeframe" name="timeframe" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                    <option value="1h">1 hour</option>
                                    <option value="4h">4 hours</option>
                                    <option value="1d">1 day</option>
                                </select>
                            </div>
                            <details class="mb-4">
                                <summary class="cursor-pointer text-sm font-semibold text-gray-700">⚙️ Advanced Settings</summary>
                                <div class="mt-2 space-y-3">
                                    <div>
                                        <label class="block text-xs text-gray-600">Initial Capital (USDT)</label>
                                        <input type="number" id="initial_capital" value="1000" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                                    </div>
                                    <div>
                                        <label class="block text-xs text-gray-600">Fee Rate (%)</label>
                                        <input type="number" id="fee_rate" value="0.1" step="0.01" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                                    </div>
                                    <div>
                                        <label class="block text-xs text-gray-600">Slippage (%)</label>
                                        <input type="number" id="slippage" value="0.05" step="0.01" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                                    </div>
                                </div>
                            </details>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">📚 Quick Strategies</label>
                                <select id="strategy_select" onchange="loadStrategy()" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                    <option value="">-- Select a strategy --</option>
                                    <option value="Buy when RSI < 30, sell when RSI > 70">RSI Oversold/Overbought</option>
                                    <option value="Buy when MACD crosses above signal line, sell when it crosses below">MACD Crossover</option>
                                    <option value="Buy when 50 EMA crosses above 200 EMA, sell when 50 EMA crosses below 200 EMA">Golden Cross</option>
                                    <option value="Buy when price breaks above upper Bollinger Band, sell at middle band">Bollinger Breakout</option>
                                    <option value="Buy when price is 2 standard deviations below 20-day MA, sell at mean">Mean Reversion</option>
                                    <option value="Buy when price crosses above 50 SMA, sell when it crosses below">Dual Moving Average</option>
                                </select>
                            </div>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">📝 Your Strategy</label>
                                <textarea id="strategy_input" name="strategy_input" rows="5" class="w-full px-3 py-2 border border-gray-300 rounded-lg" placeholder="Example: Buy when RSI < 30, sell when RSI > 70"></textarea>
                            </div>
                            <div class="grid grid-cols-2 gap-2 mb-4">
                                <button type="button" onclick="setStrategy('Buy when RSI < 30, sell when RSI > 70')" class="px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600">📊 RSI</button>
                                <button type="button" onclick="setStrategy('Buy when MACD crosses above signal, sell when crosses below')" class="px-3 py-2 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600">📈 MACD</button>
                                <button type="button" onclick="setStrategy('Buy when 50 EMA crosses above 200 EMA, sell on reverse')" class="px-3 py-2 bg-purple-500 text-white text-sm rounded-lg hover:bg-purple-600">🎯 Golden Cross</button>
                                <button type="button" onclick="setStrategy('Buy when price breaks above upper Bollinger Band, sell at middle')" class="px-3 py-2 bg-orange-500 text-white text-sm rounded-lg hover:bg-orange-600">🔥 Bollinger</button>
                            </div>
                            <button type="submit" class="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold rounded-lg hover:from-purple-700 hover:to-blue-700 transition transform hover:scale-105">🚀 Generate & Backtest</button>
                        </form>
                    </div>
                </div>

                <div class="lg:col-span-2">
                    <div id="loading" class="hidden card rounded-xl p-12 shadow-xl text-center">
                        <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
                        <p class="text-xl font-semibold text-gray-700">🤖 AI is generating your strategy...</p>
                        <p class="text-gray-500 mt-2">This takes 5-10 seconds</p>
                    </div>
                    <div id="results" class="hidden space-y-6">
                        <div class="card rounded-xl p-6 shadow-xl">
                            <h3 class="text-2xl font-bold text-gray-800 mb-4">📊 Performance Summary</h3>
                            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                                <div class="text-center p-3 bg-gray-50 rounded-lg">
                                    <p class="text-sm text-gray-600">Total PnL</p>
                                    <p id="metric_pnl" class="text-2xl font-bold text-green-600">$0</p>
                                </div>
                                <div class="text-center p-3 bg-gray-50 rounded-lg">
                                    <p class="text-sm text-gray-600">Return</p>
                                    <p id="metric_return" class="text-2xl font-bold">0%</p>
                                </div>
                                <div class="text-center p-3 bg-gray-50 rounded-lg">
                                    <p class="text-sm text-gray-600">Sharpe</p>
                                    <p id="metric_sharpe" class="text-2xl font-bold">0</p>
                                </div>
                                <div class="text-center p-3 bg-gray-50 rounded-lg">
                                    <p class="text-sm text-gray-600">Max Drawdown</p>
                                    <p id="metric_drawdown" class="text-2xl font-bold text-red-600">0%</p>
                                </div>
                                <div class="text-center p-3 bg-gray-50 rounded-lg">
                                    <p class="text-sm text-gray-600">Win Rate</p>
                                    <p id="metric_winrate" class="text-2xl font-bold">0%</p>
                                </div>
                            </div>
                            <div class="mt-4 p-4 bg-purple-50 rounded-lg">
                                <div class="grid grid-cols-2 gap-4">
                                    <div>
                                        <p class="text-sm text-gray-600">📈 Buy & Hold Return</p>
                                        <p id="metric_benchmark" class="text-xl font-bold">0%</p>
                                    </div>
                                    <div>
                                        <p class="text-sm text-gray-600">🎯 vs HODL</p>
                                        <p id="metric_outperformance" class="text-xl font-bold">0%</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="card rounded-xl p-6 shadow-xl">
                            <h3 class="text-2xl font-bold text-gray-800 mb-4">📈 Equity Curve</h3>
                            <div id="equity_chart" class="w-full h-80"></div>
                        </div>
                        <div class="card rounded-xl p-6 shadow-xl">
                            <h3 class="text-2xl font-bold text-gray-800 mb-4">💻 Generated Code</h3>
                            <pre id="generated_code" class="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm"></pre>
                        </div>
                    </div>
                    <div id="error" class="hidden card rounded-xl p-6 shadow-xl bg-red-50 border-l-4 border-red-500">
                        <h3 class="text-xl font-bold text-red-800 mb-2">❌ Error</h3>
                        <p id="error_message" class="text-red-600"></p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="py-8 text-center text-white opacity-75">
        <p>Built for <strong>Bitget AI Hackathon S1</strong> | Track: Trading Infra</p>
        <p class="mt-2"><a href="https://github.com/Vage1000600/strategyai" class="underline hover:opacity-100">GitHub</a> | <a href="https://www.bitget.com/activity-hub/hackathon" class="underline hover:opacity-100">Hackathon</a></p>
    </footer>

    <script>
        const strategies = {"RSI Oversold/Overbought": "Buy when RSI < 30, sell when RSI > 70", "MACD Crossover": "Buy when MACD crosses above signal line, sell when it crosses below", "Golden Cross": "Buy when 50 EMA crosses above 200 EMA, sell when 50 EMA crosses below 200 EMA", "Bollinger Breakout": "Buy when price breaks above upper Bollinger Band, sell at middle band", "Mean Reversion": "Buy when price is 2 standard deviations below 20-day MA, sell at mean", "Dual Moving Average": "Buy when price crosses above 50 SMA, sell when it crosses below"};
        
        function loadStrategy() {
            const select = document.getElementById('strategy_select');
            const input = document.getElementById('strategy_input');
            if (select.value && strategies[select.value]) {
                input.value = strategies[select.value];
            }
        }
        
        function setStrategy(text) {
            document.getElementById('strategy_input').value = text;
        }
        
        async function runBacktest(event) {
            event.preventDefault();
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('results').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
            
            const formData = new FormData();
            formData.append('strategy_input', document.getElementById('strategy_input').value);
            formData.append('symbol', document.getElementById('symbol').value);
            formData.append('timeframe', document.getElementById('timeframe').value);
            formData.append('initial_capital', document.getElementById('initial_capital').value);
            formData.append('fee_rate', document.getElementById('fee_rate').value);
            formData.append('slippage', document.getElementById('slippage').value);
            
            const apiKey = document.getElementById('api_key').value;
            const apiSecret = document.getElementById('api_secret').value;
            if (apiKey) formData.append('api_key', apiKey);
            if (apiSecret) formData.append('api_secret', apiSecret);
            
            try {
                const response = await fetch('/backtest', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('metric_pnl').textContent = '$' + data.metrics.pnl.toFixed(2);
                    document.getElementById('metric_pnl').className = 'text-2xl font-bold ' + (data.metrics.pnl >= 0 ? 'text-green-600' : 'text-red-600');
                    document.getElementById('metric_return').textContent = data.metrics.return_pct.toFixed(2) + '%';
                    document.getElementById('metric_return').className = 'text-2xl font-bold ' + (data.metrics.return_pct >= 0 ? 'text-green-600' : 'text-red-600');
                    document.getElementById('metric_sharpe').textContent = data.metrics.sharpe.toFixed(2);
                    document.getElementById('metric_drawdown').textContent = data.metrics.max_drawdown.toFixed(2) + '%';
                    document.getElementById('metric_winrate').textContent = data.metrics.win_rate.toFixed(1) + '%';
                    document.getElementById('metric_benchmark').textContent = data.metrics.benchmark_return.toFixed(2) + '%';
                    
                    const outperf = data.metrics.outperformance;
                    const outperfEl = document.getElementById('metric_outperformance');
                    outperfEl.textContent = (outperf >= 0 ? '+' : '') + outperf.toFixed(2) + '%';
                    outperfEl.className = 'text-xl font-bold ' + (outperf >= 0 ? 'text-green-600' : 'text-red-600');
                    
                    document.getElementById('generated_code').textContent = data.code;
                    
                    const equityTrace = {
                        x: Array.from({length: data.charts.equity.length}, (_, i) => i),
                        y: data.charts.equity,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Equity',
                        line: {color: '#667eea', width: 2}
                    };
                    
                    const layout = {
                        title: 'Portfolio Value Over Time',
                        xaxis: {title: 'Time'},
                        yaxis: {title: 'Value (USDT)'},
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        margin: {t: 40, b: 40, l: 60, r: 20}
                    };
                    
                    Plotly.newPlot('equity_chart', [equityTrace], layout, {responsive: true});
                    document.getElementById('results').classList.remove('hidden');
                } else {
                    document.getElementById('error_message').textContent = data.error;
                    document.getElementById('error').classList.remove('hidden');
                }
            } catch (err) {
                document.getElementById('error_message').textContent = 'Network error: ' + err.message;
                document.getElementById('error').classList.remove('hidden');
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }
    </script>
</body>
</html>'''


def handler(event, context):
    """Vercel serverless handler"""
    path = event.get('path', '/')
    method = event.get('method', 'GET')
    body = event.get('body', '')
    headers = event.get('headers', {})
    
    # Parse form data
    def parse_form_data(raw_body):
        """Parse URL-encoded form data"""
        data = {}
        if raw_body:
            pairs = raw_body.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    data[key] = value.replace('+', ' ')
        return data
    
    # Serve HTML for GET requests
    if method == 'GET' and path == '/':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
                'Access-Control-Allow-Origin': '*'
            },
            'body': get_html_content()
        }
    
    # Handle backtest API
    if method == 'POST' and path == '/backtest':
        try:
            form_data = parse_form_data(body)
            
            strategy_input = form_data.get('strategy_input', '')
            symbol = form_data.get('symbol', 'BTC/USDT')
            timeframe = form_data.get('timeframe', '1h')
            initial_capital = float(form_data.get('initial_capital', 1000))
            fee_rate = float(form_data.get('fee_rate', 0.1)) / 100
            slippage = float(form_data.get('slippage', 0.05)) / 100
            api_key = form_data.get('api_key')
            api_secret = form_data.get('api_secret')
            
            # Generate strategy code
            generated = generate_strategy_code(strategy_input)
            
            if 'error' in generated:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': False, 'error': f"AI Error: {generated['error']}"})
                }
            
            # Run backtest
            results = run_backtest(
                code=generated['code'],
                symbol=symbol,
                timeframe=timeframe,
                initial_capital=initial_capital,
                fee_rate=fee_rate,
                slippage=slippage,
                api_key=api_key if api_key else None,
                api_secret=api_secret if api_secret else None,
            )
            
            if 'error' in results:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': False, 'error': f"Backtest Error: {results['error']}"})
                }
            
            # Format results
            benchmark_return = results.get('benchmark_return', 0)
            strategy_return = results['return_pct']
            outperformance = strategy_return - benchmark_return
            
            # Convert trades to list if DataFrame
            trades = results.get('trades', [])
            if hasattr(trades, 'to_dict'):
                trades = trades.to_dict('records')
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'code': generated['code'],
                    'strategy_type': generated.get('strategy_type', 'Unknown'),
                    'metrics': {
                        'pnl': results['pnl'],
                        'return_pct': results['return_pct'],
                        'sharpe': results.get('sharpe', 0),
                        'max_drawdown': results.get('max_drawdown', 0),
                        'win_rate': results.get('win_rate', 0),
                        'total_trades': results.get('total_trades', 0),
                        'benchmark_return': benchmark_return,
                        'outperformance': outperformance,
                        'profit_factor': results.get('profit_factor', 0),
                        'avg_win_loss': results.get('avg_win_loss', 0),
                    },
                    'charts': {
                        'equity': results['equity_curve'],
                        'drawdown': results.get('drawdown', []),
                    },
                    'trades': trades,
                    'using_public_api': results.get('using_public_api', False),
                })
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': str(e)})
            }
    
    # 404 for other routes
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'text/plain', 'Access-Control-Allow-Origin': '*'},
        'body': 'Not Found'
    }
