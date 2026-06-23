"""
StrategyAI - Vercel Serverless Function
AI-Powered Trading Strategy Backtester
"""

import json
import os
import sys

# Import backend modules
from ai_generator import generate_strategy_code
from backtester import run_backtest


def handler(event, context):
    """
    Vercel serverless handler function.
    
    Args:
        event: Dict with 'path', 'method', 'body', 'headers'
        context: Deployment context (unused)
    
    Returns:
        Dict with 'statusCode', 'headers', 'body'
    """
    path = event.get('path', '/')
    method = event.get('method', 'GET')
    body = event.get('body', '')
    
    # Handle GET requests - serve HTML
    if method == 'GET' and path == '/':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            'body': get_html_page()
        }
    
    # Handle POST /backtest
    if method == 'POST' and path == '/backtest':
        return handle_backtest(body)
    
    # 404 for other routes
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'text/plain',
            'Access-Control-Allow-Origin': '*'
        },
        'body': 'Not Found'
    }


def handle_backtest(body):
    """Process backtest request"""
    try:
        # Parse form data
        form_data = {}
        if body:
            for pair in body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    form_data[key] = value.replace('+', ' ')
        
        # Extract parameters
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
            return json_response({
                'success': False,
                'error': f"AI Error: {generated['error']}"
            })
        
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
            return json_response({
                'success': False,
                'error': f"Backtest Error: {results['error']}"
            })
        
        # Format results
        benchmark_return = results.get('benchmark_return', 0)
        strategy_return = results['return_pct']
        outperformance = strategy_return - benchmark_return
        
        # Convert trades to list
        trades = results.get('trades', [])
        if hasattr(trades, 'to_dict'):
            trades = trades.to_dict('records')
        
        return json_response({
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
        
    except Exception as e:
        return json_response({
            'success': False,
            'error': str(e)
        }, 500)


def json_response(data, status=200):
    """Create JSON response"""
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def get_html_page():
    """Return the HTML page"""
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
                                <input type="password" id="api_key" class="w-full px-3 py-2 border border-gray-300 rounded-lg" placeholder="Leave empty for public API">
                            </div>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">🔐 API Secret (Optional)</label>
                                <input type="password" id="api_secret" class="w-full px-3 py-2 border border-gray-300 rounded-lg" placeholder="Leave empty for public API">
                            </div>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">📊 Trading Pair</label>
                                <select id="symbol" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                    <option value="BTC/USDT">BTC/USDT</option>
                                    <option value="ETH/USDT">ETH/USDT</option>
                                    <option value="SOL/USDT">SOL/USDT</option>
                                    <option value="XRP/USDT">XRP/USDT</option>
                                    <option value="BNB/USDT">BNB/USDT</option>
                                </select>
                            </div>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">⏱️ Timeframe</label>
                                <select id="timeframe" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                    <option value="1h">1 hour</option>
                                    <option value="4h">4 hours</option>
                                    <option value="1d">1 day</option>
                                </select>
                            </div>
                            <details class="mb-4">
                                <summary class="cursor-pointer text-sm font-semibold text-gray-700">⚙️ Advanced Settings</summary>
                                <div class="mt-2 space-y-3">
                                    <div><label class="block text-xs text-gray-600">Initial Capital (USDT)</label><input type="number" id="initial_capital" value="1000" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"></div>
                                    <div><label class="block text-xs text-gray-600">Fee Rate (%)</label><input type="number" id="fee_rate" value="0.1" step="0.01" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"></div>
                                    <div><label class="block text-xs text-gray-600">Slippage (%)</label><input type="number" id="slippage" value="0.05" step="0.01" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"></div>
                                </div>
                            </details>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">📚 Quick Strategies</label>
                                <select id="strategy_select" onchange="loadStrategy()" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                    <option value="">-- Select --</option>
                                    <option value="Buy when RSI < 30, sell when RSI > 70">RSI Oversold/Overbought</option>
                                    <option value="Buy when MACD crosses above signal line, sell when it crosses below">MACD Crossover</option>
                                    <option value="Buy when 50 EMA crosses above 200 EMA, sell when 50 EMA crosses below 200 EMA">Golden Cross</option>
                                    <option value="Buy when price breaks above upper Bollinger Band, sell at middle band">Bollinger Breakout</option>
                                </select>
                            </div>
                            <div class="mb-4">
                                <label class="block text-sm font-semibold text-gray-700 mb-2">📝 Your Strategy</label>
                                <textarea id="strategy_input" rows="5" class="w-full px-3 py-2 border border-gray-300 rounded-lg" placeholder="Example: Buy when RSI < 30, sell when RSI > 70"></textarea>
                            </div>
                            <div class="grid grid-cols-2 gap-2 mb-4">
                                <button type="button" onclick="setStrategy('Buy when RSI < 30, sell when RSI > 70')" class="px-3 py-2 bg-blue-500 text-white text-sm rounded-lg">📊 RSI</button>
                                <button type="button" onclick="setStrategy('Buy when MACD crosses above signal, sell when crosses below')" class="px-3 py-2 bg-green-500 text-white text-sm rounded-lg">📈 MACD</button>
                                <button type="button" onclick="setStrategy('Buy when 50 EMA crosses above 200 EMA, sell on reverse')" class="px-3 py-2 bg-purple-500 text-white text-sm rounded-lg">🎯 Golden Cross</button>
                                <button type="button" onclick="setStrategy('Buy when price breaks above upper Bollinger Band, sell at middle')" class="px-3 py-2 bg-orange-500 text-white text-sm rounded-lg">🔥 Bollinger</button>
                            </div>
                            <button type="submit" class="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold rounded-lg">🚀 Generate & Backtest</button>
                        </form>
                    </div>
                </div>
                <div class="lg:col-span-2">
                    <div id="loading" class="hidden card rounded-xl p-12 shadow-xl text-center">
                        <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
                        <p class="text-xl font-semibold text-gray-700">🤖 AI is generating your strategy...</p>
                    </div>
                    <div id="results" class="hidden space-y-6">
                        <div class="card rounded-xl p-6 shadow-xl">
                            <h3 class="text-2xl font-bold text-gray-800 mb-4">📊 Performance Summary</h3>
                            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                                <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">Total PnL</p><p id="metric_pnl" class="text-2xl font-bold">$0</p></div>
                                <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">Return</p><p id="metric_return" class="text-2xl font-bold">0%</p></div>
                                <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">Sharpe</p><p id="metric_sharpe" class="text-2xl font-bold">0</p></div>
                                <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">Max DD</p><p id="metric_drawdown" class="text-2xl font-bold text-red-600">0%</p></div>
                                <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">Win Rate</p><p id="metric_winrate" class="text-2xl font-bold">0%</p></div>
                            </div>
                            <div class="mt-4 p-4 bg-purple-50 rounded-lg">
                                <div class="grid grid-cols-2 gap-4">
                                    <div><p class="text-sm text-gray-600">📈 Buy & Hold</p><p id="metric_benchmark" class="text-xl font-bold">0%</p></div>
                                    <div><p class="text-sm text-gray-600">🎯 vs HODL</p><p id="metric_outperformance" class="text-xl font-bold">0%</p></div>
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
        <p>Built for <strong>Bitget AI Hackathon S1</strong></p>
    </footer>
    <script>
        var strategies={"RSI Oversold/Overbought":"Buy when RSI < 30, sell when RSI > 70","MACD Crossover":"Buy when MACD crosses above signal line, sell when it crosses below","Golden Cross":"Buy when 50 EMA crosses above 200 EMA, sell when 50 EMA crosses below 200 EMA","Bollinger Breakout":"Buy when price breaks above upper Bollinger Band, sell at middle band"};
        function loadStrategy(){var s=document.getElementById('strategy_select'),i=document.getElementById('strategy_input');if(s.value&&strategies[s.value])i.value=strategies[s.value]}
        function setStrategy(t){document.getElementById('strategy_input').value=t}
        async function runBacktest(e){e.preventDefault();document.getElementById('loading').classList.remove('hidden');document.getElementById('results').classList.add('hidden');document.getElementById('error').classList.add('hidden');var f=new FormData();f.append('strategy_input',document.getElementById('strategy_input').value);f.append('symbol',document.getElementById('symbol').value);f.append('timeframe',document.getElementById('timeframe').value);f.append('initial_capital',document.getElementById('initial_capital').value);f.append('fee_rate',document.getElementById('fee_rate').value);f.append('slippage',document.getElementById('slippage').value);var k=document.getElementById('api_key').value,S=document.getElementById('api_secret').value;if(k)f.append('api_key',k);if(S)f.append('api_secret',S);try{var r=await fetch('/backtest',{method:'POST',body:f}),d=await r.json();if(d.success){document.getElementById('metric_pnl').textContent='$'+d.metrics.pnl.toFixed(2);document.getElementById('metric_pnl').className='text-2xl font-bold '+(d.metrics.pnl>=0?'text-green-600':'text-red-600');document.getElementById('metric_return').textContent=d.metrics.return_pct.toFixed(2)+'%';document.getElementById('metric_return').className='text-2xl font-bold '+(d.metrics.return_pct>=0?'text-green-600':'text-red-600');document.getElementById('metric_sharpe').textContent=d.metrics.sharpe.toFixed(2);document.getElementById('metric_drawdown').textContent=d.metrics.max_drawdown.toFixed(2)+'%';document.getElementById('metric_winrate').textContent=d.metrics.win_rate.toFixed(1)+'%';document.getElementById('metric_benchmark').textContent=d.metrics.benchmark_return.toFixed(2)+'%';var o=d.metrics.outperformance,el=document.getElementById('metric_outperformance');el.textContent=(o>=0?'+':'')+o.toFixed(2)+'%';el.className='text-xl font-bold '+(o>=0?'text-green-600':'text-red-600');document.getElementById('generated_code').textContent=d.code;var t={x:Array.from({length:d.charts.equity.length},function(_,i){return i}),y:d.charts.equity,type:'scatter',mode:'lines',name:'Equity',line:{color:'#667eea',width:2}},l={title:'Portfolio Value Over Time',xaxis:{title:'Time'},yaxis:{title:'Value (USDT)'},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',margin:{t:40,b:40,l:60,r:20}};Plotly.newPlot('equity_chart',[t],l,{responsive:true});document.getElementById('results').classList.remove('hidden')}else{document.getElementById('error_message').textContent=d.error;document.getElementById('error').classList.remove('hidden')}}catch(err){document.getElementById('error_message').textContent='Network error: '+err.message;document.getElementById('error').classList.remove('hidden')}finally{document.getElementById('loading').classList.add('hidden')}}
    </script>
</body>
</html>'''
