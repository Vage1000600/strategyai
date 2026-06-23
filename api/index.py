"""
StrategyAI - Vercel Serverless Function
Two-step flow: Generate code → Review → Execute backtest
"""

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for backend imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import generate_strategy_code, validate_strategy
from backtester import run_backtest
from memory_system import store_backtest, get_insights
from strategy_scorer import score_strategy
from position_sizing import calculate_position_size, check_portfolio_heat

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


def convert_timestamps(obj):
    """Convert pandas Timestamps and other non-serializable objects to JSON-friendly format"""
    import math
    
    if isinstance(obj, dict):
        return {k: convert_timestamps(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_timestamps(item) for item in obj]
    elif hasattr(obj, 'isoformat'):  # pandas Timestamp, datetime
        return obj.isoformat()
    elif hasattr(obj, 'tolist'):  # numpy types
        return obj.tolist()
    elif isinstance(obj, float):
        # Handle inf, -inf, and nan
        if math.isinf(obj):
            return None
        elif math.isnan(obj):
            return None
        else:
            return obj
    elif isinstance(obj, (int, str, bool, type(None))):
        return obj
    else:
        return str(obj)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    return HTMLResponse(content=get_html_page())


@app.post("/backtest/generate")
async def generate_strategy(
    strategy_input: str = Form(...),
    ai_provider: str = Form('local'),
    deepseek_api_key: str = Form(None),
    claude_api_key: str = Form(None),
):
    """Generate strategy code from natural language - show to user for review
    
    TWO-STEP FLOW:
    1. Generate code (this endpoint)
    2. Review & optionally edit code
    3. Run backtest with generated code
    """
    try:
        # Build API keys dict
        api_keys = {}
        if deepseek_api_key:
            api_keys['deepseek'] = deepseek_api_key
        if claude_api_key:
            api_keys['claude'] = claude_api_key
        
        # Generate code with selected provider
        generated = generate_strategy_code(strategy_input, provider=ai_provider, api_keys=api_keys)
        if 'error' in generated:
            # If provider failed and has fallback, try local
            if generated.get('fallback') == 'local':
                generated = generate_strategy_code(strategy_input, provider='local')
            else:
                return JSONResponse({'success': False, 'error': f"AI Error: {generated['error']}"})
        
        # Validate the generated code
        validation = validate_strategy(generated['code'])
        
        return JSONResponse({
            'success': True,
            'code': generated['code'],
            'strategy_type': generated.get('strategy_type', 'Custom'),
            'indicators': generated.get('indicators', []),
            'reasoning': generated.get('reasoning', ''),
            'provider': generated.get('provider', ai_provider),
            'validation': {
                'valid': validation['valid'],
                'errors': validation['errors'],
                'warnings': validation['warnings']
            }
        })
        
    except Exception as e:
        import traceback
        return JSONResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status_code=500)


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
):
    """Run backtest on a strategy (uses generated_code if provided, otherwise generates new)
    
    If generated_code is provided, uses that code directly.
    If not provided, generates code from strategy_input first.
    """
    try:
        # SECURITY: Do not log API credentials
        has_api_key = bool(api_key and api_key.strip())
        
        # Generate code if not provided
        if not generated_code:
            generated = generate_strategy_code(strategy_input)
            if 'error' in generated:
                return JSONResponse({'success': False, 'error': f"AI Error: {generated['error']}"})
            code = generated['code']
        else:
            code = generated_code
        
        # Validate the code
        validation = validate_strategy(code)
        if not validation['valid']:
            return JSONResponse({
                'success': False,
                'error': 'Code validation failed',
                'validation_errors': validation['errors']
            })
        
        # Run backtest - use provided API key or public API
        # NOTE: api_key and api_secret are NEVER logged
        results = run_backtest(
            code=code,
            symbol=symbol,
            timeframe=timeframe,
            initial_capital=initial_capital,
            fee_rate=fee_rate / 100,
            slippage=slippage / 100,
            api_key=api_key if has_api_key else None,
            api_secret=api_secret if has_api_key and api_secret else None,
            validate=True
        )
        
        if 'error' in results:
            return JSONResponse({'success': False, 'error': f"Backtest Error: {results['error']}"})
        
        # ENHANCEMENT 1: Store in memory for learning
        try:
            store_backtest(strategy_input, results, code)
        except Exception as e:
            # Don't fail if memory storage fails
            pass
        
        # ENHANCEMENT 2: Score the strategy
        try:
            strategy_score = score_strategy(results)
        except Exception as e:
            strategy_score = {'error': str(e)}
        
        # ENHANCEMENT 3: Calculate position sizing recommendation
        try:
            current_price = results.get('current_price', 0)
            # Use max drawdown as stop loss reference
            stop_price = current_price * (1 - results.get('max_drawdown', 0.1) / 100)
            position_rec = calculate_position_size(
                portfolio_value=initial_capital,
                entry_price=current_price,
                stop_loss_price=stop_price,
                method='fixed_risk'
            )
        except Exception as e:
            position_rec = {'error': str(e)}
        
        # Format results - convert timestamps and non-serializable objects
        benchmark = results.get('benchmark_return', 0)
        outperf = results['return_pct'] - benchmark
        
        # Convert trades DataFrame to list and handle timestamps
        trades = results.get('trades', [])
        if hasattr(trades, 'to_dict'):
            trades = trades.to_dict('records')
        
        # Convert all non-serializable objects
        results_clean = convert_timestamps({
            'success': True,
            'code': code,
            'strategy_type': generated.get('strategy_type', 'Custom') if not generated_code else 'Custom',
            'indicators': generated.get('indicators', []) if not generated_code else [],
            'metrics': {
                'pnl': float(results['pnl']),
                'return_pct': float(results['return_pct']),
                'sharpe': float(results.get('sharpe', 0)),
                'max_drawdown': float(results.get('max_drawdown', 0)),
                'win_rate': float(results.get('win_rate', 0)),
                'total_trades': int(results.get('total_trades', 0)),
                'benchmark_return': float(benchmark),
                'outperformance': float(outperf),
                'profit_factor': float(results.get('profit_factor', 0)),
                'avg_win_loss': float(results.get('avg_win_loss', 0)),
            },
            'charts': {
                'equity': [float(x) for x in results['equity_curve']],
                'drawdown': [float(x) for x in results.get('drawdown', [])],
            },
            'trades': trades,
            'using_public_api': results.get('using_public_api', False),
            'validated': True,
            # ENHANCEMENTS
            'strategy_score': strategy_score,
            'position_sizing': position_rec,
            'learning_insights': get_insights()
        })
        
        return JSONResponse(content=results_clean)
        
    except Exception as e:
        import traceback
        return JSONResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status_code=500)


@app.get("/health")
async def health():
    """Health check"""
    return {'status': 'ok'}


@app.get("/insights")
async def get_learning_insights():
    """Get learning insights from memory"""
    try:
        insights = get_insights()
        return {'success': True, 'insights': insights}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@app.get("/performance")
async def get_performance():
    """Get overall performance metrics"""
    try:
        from memory_system import get_memory
        memory = get_memory()
        perf = memory.get_performance_summary()
        patterns = memory.get_pattern_insights()
        return {
            'success': True,
            'performance': perf,
            'patterns': patterns
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_html_page():
    """Return HTML page"""
    return '''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StrategyAI - AI Trading Strategy Backtester</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', -apple-system, sans-serif; }
        .dark {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            color: #e2e8f0;
        }
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .glass-card:hover {
            border-color: rgba(99, 102, 241, 0.3);
            box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
        }
        .gradient-text {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .btn-primary {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 40px rgba(99, 102, 241, 0.4);
        }
        .btn-secondary {
            background: rgba(148, 163, 184, 0.1);
            color: #e2e8f0;
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: 500;
            transition: all 0.3s ease;
            border: 1px solid rgba(148, 163, 184, 0.2);
            cursor: pointer;
        }
        .btn-secondary:hover {
            background: rgba(148, 163, 184, 0.2);
            border-color: rgba(148, 163, 184, 0.4);
        }
        .btn-success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }
        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 40px rgba(16, 185, 129, 0.4);
        }
        .input-field {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 10px;
            padding: 12px 16px;
            color: #e2e8f0;
            transition: all 0.3s ease;
            width: 100%;
        }
        .input-field:focus {
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        .metric-card {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            border-color: rgba(99, 102, 241, 0.3);
        }
        .loader {
            border: 3px solid rgba(99, 102, 241, 0.1);
            border-top: 3px solid #6366f1;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        pre {
            background: #0f172a;
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 20px;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }
        .api-status {
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 16px;
            font-size: 0.875rem;
        }
        .api-status.connected {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #10b981;
        }
        .api-status.public {
            background: rgba(251, 191, 36, 0.1);
            border: 1px solid rgba(251, 191, 36, 0.3);
            color: #fbbf24;
        }
        .validation-pass {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #10b981;
        }
        .validation-fail {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #ef4444;
        }
    </style>
</head>
<body class="min-h-screen">
    <header class="py-8 border-b border-white/5">
        <div class="container mx-auto px-4">
            <h1 class="text-5xl font-bold mb-2">
                <span class="gradient-text">🚀 StrategyAI</span>
            </h1>
            <p class="text-xl text-slate-400">AI-Powered Trading Strategy Backtester</p>
        </div>
    </header>

    <main class="container mx-auto px-4 pb-12">
        <div class="max-w-7xl mx-auto">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="lg:col-span-1">
                    <div class="glass-card p-6 sticky top-8">
                        <h2 class="text-2xl font-bold mb-6 flex items-center">
                            <span class="mr-2">⚙️</span>
                            Settings
                        </h2>
                        
                        <!-- API Status -->
                        <div id="api_status" class="api-status public">
                            <span id="api_status_icon">🌐</span>
                            <span id="api_status_text">Using public API</span>
                        </div>
                        
                        <form id="backtestForm" onsubmit="runBacktest(event)">
                            <!-- API Credentials -->
                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">
                                    🔑 Bitget API Key <span class="text-slate-500 text-xs">(Optional)</span>
                                </label>
                                <div class="relative">
                                    <input type="password" id="api_key" name="api_key" class="input-field pr-12" 
                                        placeholder="Leave empty for public API" autocomplete="off">
                                    <button type="button" onclick="toggleVisibility('api_key')" 
                                        class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition">
                                        👁️
                                    </button>
                                </div>
                            </div>
                            
                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">
                                    🔐 API Secret <span class="text-slate-500 text-xs">(Optional)</span>
                                </label>
                                <div class="relative">
                                    <input type="password" id="api_secret" name="api_secret" class="input-field pr-12" 
                                        placeholder="Leave empty for public API" autocomplete="off">
                                    <button type="button" onclick="toggleVisibility('api_secret')" 
                                        class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition">
                                        👁️
                                    </button>
                                </div>
                            </div>
                            
                            <div class="mb-5 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                                <div class="flex items-start">
                                    <span class="text-lg mr-2">🔒</span>
                                    <p class="text-xs text-emerald-300">
                                        <strong>Encrypted & Secure:</strong> Your API credentials are encrypted in transit (HTTPS), never stored on our servers, and only used for the current backtest request.
                                    </p>
                                </div>
                            </div>
                            
                            <!-- AI Provider Selection -->
                            <div class="mb-5 pt-4 border-t border-white/10">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">🤖 AI Provider</label>
                                <select id="ai_provider" name="ai_provider" class="input-field">
                                    <option value="local">Local (Free, Fast)</option>
                                    <option value="ollama">Ollama (Local LLM)</option>
                                    <option value="deepseek">DeepSeek (Advanced)</option>
                                    <option value="claude">Claude (Best Quality)</option>
                                </select>
                                <p class="text-xs text-slate-500 mt-2">Local uses templates. Ollama/DeepSeek/Claude for complex strategies.</p>
                            </div>
                            
                            <!-- DeepSeek API Key -->
                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">
                                    🔑 DeepSeek API Key <span class="text-slate-500 text-xs">(Optional)</span>
                                </label>
                                <input type="password" id="deepseek_api_key" name="deepseek_api_key" class="input-field" 
                                    placeholder="sk-..." autocomplete="off">
                            </div>
                            
                            <!-- Claude API Key -->
                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">
                                    🔑 Claude API Key <span class="text-slate-500 text-xs">(Optional)</span>
                                </label>
                                <input type="password" id="claude_api_key" name="claude_api_key" class="input-field" 
                                    placeholder="sk-ant-..." autocomplete="off">
                            </div>
                            
                            <div class="mb-5 pt-4 border-t border-white/10">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">📊 Trading Pair</label>
                                <select id="symbol" name="symbol" class="input-field">
                                    <option value="BTC/USDT">BTC/USDT</option>
                                    <option value="ETH/USDT">ETH/USDT</option>
                                    <option value="SOL/USDT">SOL/USDT</option>
                                    <option value="XRP/USDT">XRP/USDT</option>
                                    <option value="BNB/USDT">BNB/USDT</option>
                                </select>
                            </div>

                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">⏱️ Timeframe</label>
                                <select id="timeframe" name="timeframe" class="input-field">
                                    <option value="1h">1 Hour</option>
                                    <option value="4h">4 Hours</option>
                                    <option value="1d">1 Day</option>
                                </select>
                            </div>

                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">📝 Your Strategy</label>
                                <textarea id="strategy_input" name="strategy_input" rows="4" 
                                    class="input-field" 
                                    placeholder="Example: Buy when RSI < 30, sell when RSI > 70"></textarea>
                            </div>

                            <div class="mb-6">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">🚀 Quick Strategies</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <button type="button" onclick="setStrategy('Buy when RSI < 30, sell when RSI > 70')" class="btn-secondary text-sm">📊 RSI</button>
                                    <button type="button" onclick="setStrategy('Buy when MACD crosses above signal, sell when crosses below')" class="btn-secondary text-sm">📈 MACD</button>
                                    <button type="button" onclick="setStrategy('Buy when 50 EMA crosses above 200 EMA, sell on reverse')" class="btn-secondary text-sm">🎯 Golden Cross</button>
                                    <button type="button" onclick="setStrategy('Buy when price breaks above upper Bollinger Band, sell at middle')" class="btn-secondary text-sm">🔥 Bollinger</button>
                                </div>
                            </div>

                            <button type="submit" id="submit_btn" class="btn-primary w-full">
                                <span class="flex items-center justify-center">
                                    <span class="mr-2">🚀</span>
                                    Generate & Backtest
                                </span>
                            </button>
                        </form>
                    </div>
                </div>

                <div class="lg:col-span-2 space-y-6">
                    <!-- Loading State -->
                    <div id="loading" class="hidden glass-card p-12 text-center">
                        <div class="loader mx-auto mb-4"></div>
                        <p class="text-xl font-semibold text-slate-300">🤖 AI is generating...</p>
                        <p class="text-slate-500 mt-2">This takes 5-10 seconds</p>
                    </div>

                    <!-- Code Review Section (shown after generation) -->
                    <div id="code_review" class="hidden glass-card p-6">
                        <h3 class="text-xl font-bold mb-4">💻 Generated Strategy Code</h3>
                        
                        <div id="code_validation" class="mb-4 p-3 rounded-lg text-sm font-semibold">
                            <!-- Validation status will be shown here -->
                        </div>
                        
                        <pre id="generated_code"><code></code></pre>
                        
                        <div class="flex gap-4 mt-4">
                            <button type="button" onclick="editCode()" class="btn-secondary">
                                ✏️ Edit Code
                            </button>
                            <button type="button" onclick="runBacktestFromCode()" class="btn-success">
                                🚀 Run Backtest
                            </button>
                        </div>
                    </div>

                    <!-- Results -->
                    <div id="results" class="space-y-6">
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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

                        <div class="glass-card p-6">
                            <h3 class="text-xl font-bold mb-4">📊 vs Buy & Hold</h3>
                            <div class="grid grid-cols-2 gap-6">
                                <div>
                                    <p class="text-sm text-slate-400 mb-1">Buy & Hold Return</p>
                                    <p id="metric_benchmark" class="text-2xl font-bold text-slate-300">0.00%</p>
                                </div>
                                <div>
                                    <p class="text-sm text-slate-400 mb-1">Outperformance</p>
                                    <p id="metric_outperformance" class="text-2xl font-bold text-emerald-400">0.00%</p>
                                </div>
                            </div>
                        </div>

                        <div class="glass-card p-6">
                            <h3 class="text-xl font-bold mb-4">📈 Equity Curve</h3>
                            <div id="equity_chart" class="w-full h-96"></div>
                        </div>

                        <div class="glass-card p-6">
                            <h3 class="text-xl font-bold mb-4">💻 Final Generated Code</h3>
                            <pre id="final_code"><code class="text-sm text-emerald-400">def strategy(data):<br>&nbsp;&nbsp;# Strategy code will appear here...</code></pre>
                        </div>
                    </div>

                    <!-- Error Message -->
                    <div id="error" class="hidden glass-card p-6 bg-red-500/10 border-l-4 border-red-500">
                        <h3 class="text-xl font-bold text-red-400 mb-2">❌ Error</h3>
                        <p id="error_message" class="text-red-300"></p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="border-t border-white/5 py-8">
        <div class="container mx-auto px-4 text-center text-slate-400">
            <p>Built for <strong class="text-slate-300">Bitget AI Hackathon S1</strong> | Trading Infra Track</p>
        </div>
    </footer>

    <script>
        let currentCode = null;
        
        // Toggle password visibility
        function toggleVisibility(fieldId) {
            const field = document.getElementById(fieldId);
            field.type = field.type === 'password' ? 'text' : 'password';
        }
        
        // Update API status based on input
        function updateApiStatus() {
            const apiKey = document.getElementById('api_key').value.trim();
            const apiSecret = document.getElementById('api_secret').value.trim();
            const statusDiv = document.getElementById('api_status');
            const statusIcon = document.getElementById('api_status_icon');
            const statusText = document.getElementById('api_status_text');
            
            if (apiKey && apiSecret) {
                statusDiv.className = 'api-status connected';
                statusIcon.textContent = '✅';
                statusText.textContent = 'Using your Bitget API key';
            } else {
                statusDiv.className = 'api-status public';
                statusIcon.textContent = '🌐';
                statusText.textContent = 'Using public API';
            }
        }
        
        // Listen for input changes
        document.getElementById('api_key').addEventListener('input', updateApiStatus);
        document.getElementById('api_secret').addEventListener('input', updateApiStatus);
        
        function setStrategy(text) {
            document.getElementById('strategy_input').value = text;
        }
        
        async function generateCode() {
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('results').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
            document.getElementById('code_review').classList.add('hidden');
            
            const formData = new FormData();
            formData.append('strategy_input', document.getElementById('strategy_input').value);
            
            try {
                const response = await fetch('/backtest/generate', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    currentCode = data.code;
                    
                    // Show validation status
                    const validationDiv = document.getElementById('code_validation');
                    if (data.validation.valid) {
                        validationDiv.className = 'validation-pass p-3 rounded-lg text-sm font-semibold';
                        validationDiv.innerHTML = '✅ <strong>Code Validated!</strong> No syntax or security errors detected.';
                    } else {
                        validationDiv.className = 'validation-fail p-3 rounded-lg text-sm font-semibold';
                        validationDiv.innerHTML = '❌ <strong>Validation Failed:</strong> ' + data.validation.errors.join(', ');
                    }
                    
                    // Show code
                    document.getElementById('generated_code').innerHTML = data.code
                        .replace(/</g, '&lt;')
                        .replace(/>/g, '&gt;')
                        .replace(/def/g, '<span class="text-purple-400">def</span>')
                        .replace(/return/g, '<span class="text-purple-400">return</span>')
                        .replace(/import/g, '<span class="text-purple-400">import</span>');
                    
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
            if (!currentCode) {
                alert('No code generated yet. Click "Generate & Backtest" first.');
                return;
            }
            
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('results').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
            
            const formData = new FormData();
            formData.append('strategy_input', document.getElementById('strategy_input').value);
            formData.append('symbol', document.getElementById('symbol').value);
            formData.append('timeframe', document.getElementById('timeframe').value);
            formData.append('generated_code', currentCode);
            
            // Add API credentials if provided
            const apiKey = document.getElementById('api_key').value.trim();
            const apiSecret = document.getElementById('api_secret').value.trim();
            if (apiKey) formData.append('api_key', apiKey);
            if (apiSecret) formData.append('api_secret', apiSecret);
            
            try {
                const response = await fetch('/backtest', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    const pnl = data.metrics.pnl;
                    const returnPct = data.metrics.return_pct;
                    
                    document.getElementById('metric_pnl').textContent = '$' + pnl.toFixed(2);
                    document.getElementById('metric_pnl').className = 'text-2xl font-bold ' + (pnl >= 0 ? 'text-emerald-400' : 'text-red-400');
                    
                    document.getElementById('metric_return').textContent = returnPct.toFixed(2) + '%';
                    document.getElementById('metric_return').className = 'text-2xl font-bold ' + (returnPct >= 0 ? 'text-emerald-400' : 'text-red-400');
                    
                    document.getElementById('metric_sharpe').textContent = data.metrics.sharpe.toFixed(2);
                    document.getElementById('metric_drawdown').textContent = data.metrics.max_drawdown.toFixed(2) + '%';
                    document.getElementById('metric_winrate').textContent = data.metrics.win_rate.toFixed(1) + '%';
                    document.getElementById('metric_benchmark').textContent = data.metrics.benchmark_return.toFixed(2) + '%';
                    
                    const outperf = data.metrics.outperformance;
                    const outperfEl = document.getElementById('metric_outperformance');
                    outperfEl.textContent = (outperf >= 0 ? '+' : '') + outperf.toFixed(2) + '%';
                    outperfEl.className = 'text-2xl font-bold ' + (outperf >= 0 ? 'text-emerald-400' : 'text-red-400');
                    
                    document.getElementById('final_code').innerHTML = data.code
                        .replace(/</g, '&lt;')
                        .replace(/>/g, '&gt;')
                        .replace(/def/g, '<span class="text-purple-400">def</span>')
                        .replace(/return/g, '<span class="text-purple-400">return</span>')
                        .replace(/import/g, '<span class="text-purple-400">import</span>');
                    
                    const equityTrace = {
                        x: Array.from({length: data.charts.equity.length}, (_, i) => i),
                        y: data.charts.equity,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Equity',
                        line: {color: '#6366f1', width: 3, shape: 'spline'},
                        fill: 'tozeroy',
                        fillcolor: 'rgba(99, 102, 241, 0.2)'
                    };
                    
                    const layout = {
                        title: 'Portfolio Value Over Time',
                        xaxis: {
                            title: 'Time (Candles)',
                            gridcolor: 'rgba(148, 163, 184, 0.1)',
                            tickfont: {color: '#94a3b8'}
                        },
                        yaxis: {
                            title: 'Value (USDT)',
                            gridcolor: 'rgba(148, 163, 184, 0.1)',
                            tickfont: {color: '#94a3b8'}
                        },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        margin: {t: 50, b: 50, l: 70, r: 20},
                        showlegend: false
                    };
                    
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
            const newCode = prompt('Edit your strategy code:', codeArea.textContent);
            if (newCode) {
                currentCode = newCode;
                codeArea.innerHTML = newCode
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/def/g, '<span class="text-purple-400">def</span>')
                    .replace(/return/g, '<span class="text-purple-400">return</span>')
                    .replace(/import/g, '<span class="text-purple-400">import</span>');
            }
        }
        
        async function runBacktest(event) {
            event.preventDefault();
            
            // First generate code
            await generateCode();
            
            // If code was generated successfully, run backtest
            if (currentCode) {
                await runBacktestFromCode();
            }
        }
        
        // Initialize status on load
        updateApiStatus();
    </script>
</body>
</html>'''
