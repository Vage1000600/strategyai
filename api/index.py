"""
StrategyAI - Vercel Serverless Function
Minimal version for stability
"""

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Add parent directory to path for backend imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import generate_strategy_code, validate_strategy, cleanup_strategy_code
from backtester import run_backtest

# Create FastAPI app - MUST be at module level for Vercel
app = FastAPI(title="StrategyAI")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HTML TEMPLATE (Simplified for stability)
# ============================================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StrategyAI - AI Trading Backtester</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 16px; }
        .btn-primary { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 12px 24px; border-radius: 12px; font-weight: 600; border: none; cursor: pointer; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 10px 40px rgba(99, 102, 241, 0.4); }
        .btn-secondary { background: rgba(148, 163, 184, 0.1); color: #e2e8f0; padding: 10px 20px; border-radius: 10px; border: 1px solid rgba(148, 163, 184, 0.2); cursor: pointer; }
        .input-field { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 10px; padding: 12px 16px; color: #e2e8f0; width: 100%; }
        .input-field:focus { outline: none; border-color: #6366f1; }
        .metric-card { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 12px; padding: 20px; }
        .loader { border: 3px solid rgba(99, 102, 241, 0.1); border-top: 3px solid #6366f1; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        pre { background: #0f172a; border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 20px; overflow-x: auto; max-height: 400px; }
    </style>
</head>
<body class="min-h-screen">
    <header class="py-8 border-b border-white/5">
        <div class="container mx-auto px-4">
            <h1 class="text-4xl font-bold mb-2">🚀 StrategyAI</h1>
            <p class="text-slate-400">AI-Powered Trading Strategy Backtester</p>
        </div>
    </header>

    <main class="container mx-auto px-4 py-8">
        <div class="max-w-7xl mx-auto">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Left Column - Form -->
                <div class="lg:col-span-1">
                    <div class="glass p-6 sticky top-8">
                        <h2 class="text-2xl font-bold mb-6">⚙️ Settings</h2>
                        
                        <form id="backtestForm" onsubmit="runBacktest(event)">
                            <div class="mb-4">
                                <label class="block text-sm font-semibold mb-2">Bitget API Key (Optional)</label>
                                <input type="password" id="api_key" class="input-field" placeholder="Leave empty for public API">
                            </div>
                            
                            <div class="mb-4">
                                <label class="block text-sm font-semibold mb-2">API Secret (Optional)</label>
                                <input type="password" id="api_secret" class="input-field" placeholder="Leave empty for public API">
                            </div>
                            
                            <div class="mb-4">
                                <label class="block text-sm font-semibold mb-2">📊 Trading Pair</label>
                                <select id="symbol" class="input-field">
                                    <option value="BTC/USDT">BTC/USDT</option>
                                    <option value="ETH/USDT">ETH/USDT</option>
                                    <option value="SOL/USDT">SOL/USDT</option>
                                </select>
                            </div>

                            <div class="mb-4">
                                <label class="block text-sm font-semibold mb-2">⏱️ Timeframe</label>
                                <select id="timeframe" class="input-field">
                                    <option value="1h">1 Hour</option>
                                    <option value="4h">4 Hours</option>
                                    <option value="1d">1 Day</option>
                                </select>
                            </div>

                            <div class="mb-4">
                                <label class="block text-sm font-semibold mb-2">📝 Strategy</label>
                                <textarea id="strategy_input" rows="4" class="input-field" placeholder="Buy when RSI < 30, sell when RSI > 70"></textarea>
                            </div>

                            <div class="mb-6">
                                <label class="block text-sm font-semibold mb-2">🚀 Quick Strategies</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <button type="button" onclick="setStrategy('Buy when RSI < 30, sell when RSI > 70')" class="btn-secondary text-sm">📊 RSI</button>
                                    <button type="button" onclick="setStrategy('Buy when MACD crosses above signal')" class="btn-secondary text-sm">📈 MACD</button>
                                    <button type="button" onclick="setStrategy('Buy when 50 EMA crosses 200 EMA')" class="btn-secondary text-sm">🎯 Golden Cross</button>
                                    <button type="button" onclick="setStrategy('Buy when price breaks Bollinger upper band')" class="btn-secondary text-sm">🔥 Bollinger</button>
                                </div>
                            </div>

                            <button type="submit" class="btn-primary w-full">🚀 Generate & Backtest</button>
                        </form>
                    </div>
                </div>

                <!-- Right Column - Results -->
                <div class="lg:col-span-2 space-y-6">
                    <!-- Loading -->
                    <div id="loading" class="hidden glass p-12 text-center">
                        <div class="loader mx-auto mb-4"></div>
                        <p class="text-xl font-semibold">🤖 AI is generating...</p>
                        <p class="text-slate-400 mt-2">This takes 5-10 seconds</p>
                    </div>

                    <!-- Code Review -->
                    <div id="code_review" class="hidden glass p-6">
                        <h3 class="text-xl font-bold mb-4">💻 Generated Code</h3>
                        <pre id="generated_code"><code></code></pre>
                        <div class="flex gap-4 mt-4">
                            <button type="button" onclick="editCode()" class="btn-secondary">✏️ Edit</button>
                            <button type="button" onclick="runBacktestFromCode()" class="btn-primary">🚀 Backtest</button>
                        </div>
                    </div>

                    <!-- Results -->
                    <div id="results" class="hidden space-y-6">
                        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div class="metric-card">
                                <p class="text-sm text-slate-400 mb-1">Total PnL</p>
                                <p id="metric_pnl" class="text-2xl font-bold text-emerald-400">$0.00</p>
                            </div>
                            <div class="metric-card">
                                <p class="text-sm text-slate-400 mb-1">Return</p>
                                <p id="metric_return" class="text-2xl font-bold text-emerald-400">0.00%</p>
                            </div>
                            <div class="metric-card">
                                <p class="text-sm text-slate-400 mb-1">Sharpe</p>
                                <p id="metric_sharpe" class="text-2xl font-bold text-indigo-400">0.00</p>
                            </div>
                            <div class="metric-card">
                                <p class="text-sm text-slate-400 mb-1">Max DD</p>
                                <p id="metric_drawdown" class="text-2xl font-bold text-red-400">0.00%</p>
                            </div>
                            <div class="metric-card">
                                <p class="text-sm text-slate-400 mb-1">Win Rate</p>
                                <p id="metric_winrate" class="text-2xl font-bold text-purple-400">0.00%</p>
                            </div>
                        </div>

                        <div class="glass p-6">
                            <h3 class="text-xl font-bold mb-4">📈 Equity Curve</h3>
                            <div id="equity_chart" class="w-full h-96"></div>
                        </div>

                        <div class="glass p-6">
                            <h3 class="text-xl font-bold mb-4">💻 Final Code</h3>
                            <pre id="final_code"><code>def strategy(data):<br>&nbsp;&nbsp;# Code will appear here...</code></pre>
                        </div>
                    </div>

                    <!-- Error -->
                    <div id="error" class="hidden glass p-6 bg-red-500/10 border-l-4 border-red-500">
                        <h3 class="text-xl font-bold text-red-400 mb-2">❌ Error</h3>
                        <p id="error_message" class="text-red-300"></p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="border-t border-white/5 py-8 mt-12">
        <div class="container mx-auto px-4 text-center text-slate-400">
            <p>Built for <strong class="text-slate-300">Bitget AI Hackathon S1</strong></p>
        </div>
    </footer>

    <script>
        let currentCode = null;
        
        function setStrategy(text) { document.getElementById('strategy_input').value = text; }
        
        async function generateCode() {
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('code_review').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
            
            const formData = new FormData();
            formData.append('strategy_input', document.getElementById('strategy_input').value);
            formData.append('timeframe', document.getElementById('timeframe').value);
            
            try {
                const response = await fetch('/backtest/generate', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    currentCode = data.code;
                    document.getElementById('generated_code').innerHTML = data.code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    document.getElementById('code_review').classList.remove('hidden');
                } else {
                    document.getElementById('error_message').textContent = data.error;
                    document.getElementById('error').classList.remove('hidden');
                }
            } catch (err) {
                document.getElementById('error_message').textContent = 'Error: ' + err.message;
                document.getElementById('error').classList.remove('hidden');
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }
        
        async function runBacktestFromCode() {
            if (!currentCode) { alert('No code generated yet.'); return; }
            
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('results').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
            
            const formData = new FormData();
            formData.append('strategy_input', document.getElementById('strategy_input').value);
            formData.append('symbol', document.getElementById('symbol').value);
            formData.append('timeframe', document.getElementById('timeframe').value);
            formData.append('generated_code', currentCode);
            
            const apiKey = document.getElementById('api_key').value.trim();
            const apiSecret = document.getElementById('api_secret').value.trim();
            if (apiKey) formData.append('api_key', apiKey);
            if (apiSecret) formData.append('api_secret', apiSecret);
            
            try {
                const response = await fetch('/backtest', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success && data.metrics) {
                    const pnl = data.metrics.pnl || 0;
                    const returnPct = data.metrics.return_pct || 0;
                    
                    document.getElementById('metric_pnl').textContent = '$' + pnl.toFixed(2);
                    document.getElementById('metric_pnl').className = 'text-2xl font-bold ' + (pnl >= 0 ? 'text-emerald-400' : 'text-red-400');
                    document.getElementById('metric_return').textContent = returnPct.toFixed(2) + '%';
                    document.getElementById('metric_return').className = 'text-2xl font-bold ' + (returnPct >= 0 ? 'text-emerald-400' : 'text-red-400');
                    document.getElementById('metric_sharpe').textContent = (data.metrics.sharpe || 0).toFixed(2);
                    document.getElementById('metric_drawdown').textContent = (data.metrics.max_drawdown || 0).toFixed(2) + '%';
                    document.getElementById('metric_winrate').textContent = (data.metrics.win_rate || 0).toFixed(1) + '%';
                    
                    document.getElementById('final_code').innerHTML = data.code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    
                    const equityTrace = { x: Array.from({length: data.charts.equity.length}, (_, i) => i), y: data.charts.equity, type: 'scatter', mode: 'lines', line: {color: '#6366f1', width: 3}, fill: 'tozeroy', fillcolor: 'rgba(99, 102, 241, 0.2)' };
                    const layout = { xaxis: {title: 'Time', gridcolor: 'rgba(148, 163, 184, 0.1)'}, yaxis: {title: 'Value (USDT)', gridcolor: 'rgba(148, 163, 184, 0.1)'}, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', margin: {t: 30, b: 40, l: 60, r: 20}, showlegend: false };
                    Plotly.newPlot('equity_chart', [equityTrace], layout, {responsive: true, displayModeBar: false});
                    
                    document.getElementById('results').classList.remove('hidden');
                } else {
                    document.getElementById('error_message').textContent = data.error;
                    document.getElementById('error').classList.remove('hidden');
                }
            } catch (err) {
                document.getElementById('error_message').textContent = 'Error: ' + err.message;
                document.getElementById('error').classList.remove('hidden');
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }
        
        function editCode() {
            const codeArea = document.getElementById('generated_code');
            const newCode = prompt('Edit code:', codeArea.textContent);
            if (newCode) { currentCode = newCode; codeArea.innerHTML = newCode.replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
        }
        
        async function runBacktest(event) {
            event.preventDefault();
            await generateCode();
            if (currentCode) await runBacktestFromCode();
        }
    </script>
</body>
</html>'''

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Main page"""
    return HTMLResponse(content=HTML_TEMPLATE)


@app.post("/backtest/generate")
async def generate_endpoint(strategy_input: str = Form(...), timeframe: str = Form("1h")):
    """Generate strategy code"""
    try:
        generated = generate_strategy_code(strategy_input, provider='local')
        
        if 'error' in generated:
            return JSONResponse({'success': False, 'error': generated['error']})
        
        code = generated['code']
        validation = validate_strategy(code)
        
        return JSONResponse({
            'success': True,
            'code': code,
            'strategy_type': generated.get('strategy_type', 'Custom'),
            'validation': validation
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'error': f'Generation failed: {str(e)}'})


@app.post("/backtest")
async def run_backtest_endpoint(
    strategy_input: str = Form(...),
    symbol: str = Form("BTC/USDT"),
    timeframe: str = Form("1h"),
    initial_capital: float = Form(1000.0),
    fee_rate: float = Form(0.1),
    slippage: float = Form(0.05),
    generated_code: str = Form(None),
    api_key: str = Form(None),
    api_secret: str = Form(None),
    position_size: float = Form(1.0),
    trailing_stop: str = Form("false"),
):
    """Run backtest"""
    try:
        # Generate code if not provided
        if not generated_code:
            generated = generate_strategy_code(strategy_input, provider='local')
            if 'error' in generated:
                return JSONResponse({'success': False, 'error': generated['error']})
            code = generated['code']
        else:
            code = generated_code
        
        # Clean and validate code
        code = cleanup_strategy_code(code)
        validation = validate_strategy(code)
        if not validation['valid']:
            return JSONResponse({
                'success': False,
                'error': 'Validation failed: ' + ', '.join(validation['errors'])
            })
        
        # Run backtest
        results = run_backtest(
            code=code,
            symbol=symbol,
            timeframe=timeframe,
            initial_capital=initial_capital,
            fee_rate=fee_rate / 100,
            slippage=slippage / 100,
            api_key=api_key if api_key else None,
            api_secret=api_secret if api_secret else None,
            validate=True,
            position_size=position_size,
            trailing_stop=trailing_stop
        )
        
        if 'error' in results:
            return JSONResponse({'success': False, 'error': results['error']})
        
        return JSONResponse({
            'success': True,
            'metrics': results.get('metrics', results),
            'charts': {
                'equity': results.get('equity_curve', []),
                'drawdown': results.get('drawdown_curve', [])
            },
            'code': code,
            'trades': results.get('trades', [])[:10]
        })
        
    except Exception as e:
        import traceback
        return JSONResponse({
            'success': False,
            'error': f'Backtest failed: {str(e)}',
            'traceback': traceback.format_exc()
        })
