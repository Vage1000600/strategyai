"""
StrategyAI - Vercel Serverless Function
Clean FastAPI app - no conditional imports
"""

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
import json
import os
import sys

# Add parent directory to path for backend imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import generate_strategy_code
from backtester import run_backtest

# Create FastAPI app - MUST be at module level for Vercel
app = FastAPI(title="StrategyAI")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    return HTMLResponse(content=get_html_page())


@app.post("/backtest")
async def backtest(
    strategy_input: str = Form(...),
    symbol: str = Form("BTC/USDT"),
    timeframe: str = Form("1h"),
    initial_capital: float = Form(1000.0),
    fee_rate: float = Form(0.1),
    slippage: float = Form(0.05),
    api_key: str = Form(None),
    api_secret: str = Form(None),
):
    """Run backtest on a strategy"""
    try:
        # Generate code
        generated = generate_strategy_code(strategy_input)
        if 'error' in generated:
            return JSONResponse({'success': False, 'error': f"AI Error: {generated['error']}"})
        
        # Run backtest
        results = run_backtest(
            code=generated['code'],
            symbol=symbol,
            timeframe=timeframe,
            initial_capital=initial_capital,
            fee_rate=fee_rate / 100,
            slippage=slippage / 100,
            api_key=api_key if api_key else None,
            api_secret=api_secret if api_secret else None,
        )
        
        if 'error' in results:
            return JSONResponse({'success': False, 'error': f"Backtest Error: {results['error']}"})
        
        # Format results
        benchmark = results.get('benchmark_return', 0)
        outperf = results['return_pct'] - benchmark
        
        trades = results.get('trades', [])
        if hasattr(trades, 'to_dict'):
            trades = trades.to_dict('records')
        
        return JSONResponse({
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
                'benchmark_return': benchmark,
                'outperformance': outperf,
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
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@app.get("/health")
async def health():
    """Health check"""
    return {'status': 'ok'}


def get_html_page():
    """Return HTML page"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StrategyAI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>.gradient-bg{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%)}.card{background:rgba(255,255,255,0.95);backdrop-filter:blur(10px)}</style>
</head>
<body class="gradient-bg min-h-screen">
    <header class="py-8"><div class="container mx-auto px-4"><h1 class="text-5xl font-bold text-white text-center mb-2">🚀 StrategyAI</h1><p class="text-xl text-white text-center opacity-90">Describe Your Strategy. We'll Code It. Backtest It.</p></div></header>
    <main class="container mx-auto px-4 pb-12">
        <div class="max-w-6xl mx-auto">
            <div class="bg-green-500 text-white p-4 rounded-lg mb-6 text-center"><strong>🎉 No Setup Required!</strong> Using public Bitget API</div>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-1"><div class="card rounded-xl p-6 shadow-xl">
                    <h2 class="text-2xl font-bold text-gray-800 mb-4">⚙️ Settings</h2>
                    <form id="backtestForm" onsubmit="runBacktest(event)">
                        <div class="mb-4"><label class="block text-sm font-semibold text-gray-700 mb-2">📊 Trading Pair</label><select id="symbol" class="w-full px-3 py-2 border border-gray-300 rounded-lg"><option value="BTC/USDT">BTC/USDT</option><option value="ETH/USDT">ETH/USDT</option><option value="SOL/USDT">SOL/USDT</option></select></div>
                        <div class="mb-4"><label class="block text-sm font-semibold text-gray-700 mb-2">⏱️ Timeframe</label><select id="timeframe" class="w-full px-3 py-2 border border-gray-300 rounded-lg"><option value="1h">1 hour</option><option value="4h">4 hours</option><option value="1d">1 day</option></select></div>
                        <div class="mb-4"><label class="block text-sm font-semibold text-gray-700 mb-2">📝 Your Strategy</label><textarea id="strategy_input" rows="5" class="w-full px-3 py-2 border border-gray-300 rounded-lg" placeholder="Buy when RSI < 30, sell when RSI > 70"></textarea></div>
                        <div class="grid grid-cols-2 gap-2 mb-4">
                            <button type="button" onclick="setStrategy('Buy when RSI < 30, sell when RSI > 70')" class="px-3 py-2 bg-blue-500 text-white text-sm rounded-lg">📊 RSI</button>
                            <button type="button" onclick="setStrategy('Buy when MACD crosses above signal, sell when crosses below')" class="px-3 py-2 bg-green-500 text-white text-sm rounded-lg">📈 MACD</button>
                            <button type="button" onclick="setStrategy('Buy when 50 EMA crosses above 200 EMA, sell on reverse')" class="px-3 py-2 bg-purple-500 text-white text-sm rounded-lg">🎯 Golden Cross</button>
                            <button type="button" onclick="setStrategy('Buy when price breaks above upper Bollinger Band, sell at middle')" class="px-3 py-2 bg-orange-500 text-white text-sm rounded-lg">🔥 Bollinger</button>
                        </div>
                        <button type="submit" class="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold rounded-lg">🚀 Generate & Backtest</button>
                    </form>
                </div></div>
                <div class="lg:col-span-2">
                    <div id="loading" class="hidden card rounded-xl p-12 shadow-xl text-center"><div class="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div><p class="text-xl font-semibold text-gray-700">🤖 AI is generating...</p></div>
                    <div id="results" class="hidden space-y-6">
                        <div class="card rounded-xl p-6 shadow-xl"><h3 class="text-2xl font-bold text-gray-800 mb-4">📊 Performance</h3><div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">PnL</p><p id="metric_pnl" class="text-2xl font-bold">$0</p></div>
                            <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">Return</p><p id="metric_return" class="text-2xl font-bold">0%</p></div>
                            <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">Sharpe</p><p id="metric_sharpe" class="text-2xl font-bold">0</p></div>
                            <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">Max DD</p><p id="metric_drawdown" class="text-2xl font-bold text-red-600">0%</p></div>
                            <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600">Win Rate</p><p id="metric_winrate" class="text-2xl font-bold">0%</p></div>
                        </div></div>
                        <div class="card rounded-xl p-6 shadow-xl"><h3 class="text-2xl font-bold text-gray-800 mb-4">📈 Equity Curve</h3><div id="equity_chart" class="w-full h-80"></div></div>
                        <div class="card rounded-xl p-6 shadow-xl"><h3 class="text-2xl font-bold text-gray-800 mb-4">💻 Code</h3><pre id="generated_code" class="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm"></pre></div>
                    </div>
                    <div id="error" class="hidden card rounded-xl p-6 shadow-xl bg-red-50 border-l-4 border-red-500"><h3 class="text-xl font-bold text-red-800 mb-2">❌ Error</h3><p id="error_message" class="text-red-600"></p></div>
                </div>
            </div>
        </div>
    </main>
    <footer class="py-8 text-center text-white opacity-75"><p>Built for <strong>Bitget AI Hackathon S1</strong></p></footer>
    <script>
        function setStrategy(t){document.getElementById('strategy_input').value=t}
        async function runBacktest(e){e.preventDefault();document.getElementById('loading').classList.remove('hidden');document.getElementById('results').classList.add('hidden');document.getElementById('error').classList.add('hidden');
        var f=new FormData();f.append('strategy_input',document.getElementById('strategy_input').value);f.append('symbol',document.getElementById('symbol').value);f.append('timeframe',document.getElementById('timeframe').value);
        try{var r=await fetch('/backtest',{method:'POST',body:f}),d=await r.json();
        if(d.success){document.getElementById('metric_pnl').textContent='$'+d.metrics.pnl.toFixed(2);document.getElementById('metric_return').textContent=d.metrics.return_pct.toFixed(2)+'%';document.getElementById('metric_sharpe').textContent=d.metrics.sharpe.toFixed(2);document.getElementById('metric_drawdown').textContent=d.metrics.max_drawdown.toFixed(2)+'%';document.getElementById('metric_winrate').textContent=d.metrics.win_rate.toFixed(1)+'%';document.getElementById('generated_code').textContent=d.code;
        var t={x:Array.from({length:d.charts.equity.length},(_,i)=>i),y:d.charts.equity,type:'scatter',mode:'lines',line:{color:'#667eea',width:2}},l={title:'Portfolio Value',xaxis:{title:'Time'},yaxis:{title:'USDT'},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',margin:{t:40,b:40,l:60,r:20}};Plotly.newPlot('equity_chart',[t],l,{responsive:true});document.getElementById('results').classList.remove('hidden')}
        else{document.getElementById('error_message').textContent=d.error;document.getElementById('error').classList.remove('hidden')}}
        catch(err){document.getElementById('error_message').textContent='Error: '+err.message;document.getElementById('error').classList.remove('hidden')}
        finally{document.getElementById('loading').classList.add('hidden')}}
    </script>
</body>
</html>'''
