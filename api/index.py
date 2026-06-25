"""
StrategyAI - Modern AI Trading Strategy Backtester
Professional UI with separate pages
"""

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for backend imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import generate_strategy_code, validate_strategy, cleanup_strategy_code
from backtester import run_backtest
from memory_system import store_backtest, get_insights
from strategy_scorer import score_strategy
from position_sizing import calculate_position_size, check_portfolio_heat

# Create FastAPI app - MUST be at module level for Vercel
app = FastAPI(title="StrategyAI", docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main landing page with unified interface"""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StrategyAI - AI Trading Backtester</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .gradient-bg {
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
        }
        .glass {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        .glass-hover:hover {
            background: rgba(30, 41, 59, 0.9);
            border-color: rgba(99, 102, 241, 0.3);
        }
        .btn-gradient {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        }
        .btn-gradient:hover {
            box-shadow: 0 10px 40px rgba(99, 102, 241, 0.4);
        }
        .metric-box {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        .nav-link {
            transition: all 0.2s ease;
        }
        .nav-link.active {
            color: #818cf8;
            border-bottom: 2px solid #818cf8;
        }
        .hidden-section {
            display: none;
        }
        .show-section {
            display: block;
        }
        pre {
            background: #0f172a;
            border-radius: 12px;
            padding: 20px;
            overflow-x: auto;
            font-family: 'Fira Code', monospace;
            font-size: 13px;
            line-height: 1.5;
        }
        code {
            color: #10b981;
        }
        .code-keyword { color: #c084fc; }
        .code-function { color: #60a5fa; }
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <!-- Navigation -->
    <nav class="border-b border-white/10 glass sticky top-0 z-50">
        <div class="container mx-auto px-6">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center space-x-8">
                    <h1 class="text-2xl font-bold text-white">
                        <span class="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">🚀 StrategyAI</span>
                    </h1>
                    <div class="hidden md:flex space-x-6">
                        <button onclick="showSection('backtest')" id="nav-backtest" class="nav-link active text-slate-300 hover:text-white">
                            🎯 Backtest
                        </button>
                        <button onclick="showSection('results')" id="nav-results" class="nav-link text-slate-300 hover:text-white">
                            📊 Results
                        </button>
                        <button onclick="showSection('settings')" id="nav-settings" class="nav-link text-slate-300 hover:text-white">
                            ⚙️ Settings
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="container mx-auto px-6 py-8">
        
        <!-- Backtest Section -->
        <section id="section-backtest" class="show-section">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Left Column - Form -->
                <div class="lg:col-span-1">
                    <div class="glass glass-hover rounded-2xl p-6 sticky top-20">
                        <h2 class="text-xl font-bold text-white mb-6">⚙️ Configuration</h2>
                        
                        <form id="backtestForm" onsubmit="runBacktest(event)">
                            <!-- API Credentials -->
                            <div class="mb-5">
                                <label class="block text-sm font-medium text-slate-300 mb-2">
                                    Bitget API Key (Optional)
                                </label>
                                <input type="password" id="api_key" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500" placeholder="Leave empty for public API">
                            </div>
                            
                            <div class="mb-5">
                                <label class="block text-sm font-medium text-slate-300 mb-2">
                                    API Secret (Optional)
                                </label>
                                <input type="password" id="api_secret" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500" placeholder="Leave empty for public API">
                            </div>
                            
                            <!-- Trading Pair -->
                            <div class="mb-5">
                                <label class="block text-sm font-medium text-slate-300 mb-2">📊 Trading Pair</label>
                                <select id="symbol" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500">
                                    <option value="BTC/USDT">BTC/USDT</option>
                                    <option value="ETH/USDT">ETH/USDT</option>
                                    <option value="SOL/USDT">SOL/USDT</option>
                                    <option value="XRP/USDT">XRP/USDT</option>
                                    <option value="BNB/USDT">BNB/USDT</option>
                                </select>
                            </div>

                            <!-- Timeframe -->
                            <div class="mb-5">
                                <label class="block text-sm font-medium text-slate-300 mb-2">⏱️ Timeframe</label>
                                <select id="timeframe" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500">
                                    <option value="1h">1 Hour</option>
                                    <option value="4h">4 Hours</option>
                                    <option value="1d">1 Day</option>
                                </select>
                            </div>

                            <!-- Strategy Input -->
                            <div class="mb-5">
                                <label class="block text-sm font-medium text-slate-300 mb-2">📝 Strategy Description</label>
                                <textarea id="strategy_input" rows="4" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500" placeholder="Buy when RSI &lt; 30, sell when RSI &gt; 70"></textarea>
                            </div>

                            <!-- Quick Strategies -->
                            <div class="mb-6">
                                <label class="block text-sm font-medium text-slate-300 mb-2">🚀 Quick Strategies</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <button type="button" onclick="setStrategy('Buy when RSI &lt; 30, sell when RSI &gt; 70')" class="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white transition">RSI</button>
                                    <button type="button" onclick="setStrategy('Buy when MACD crosses above signal')" class="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white transition">MACD</button>
                                    <button type="button" onclick="setStrategy('Buy when 50 EMA crosses 200 EMA')" class="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white transition">Golden Cross</button>
                                    <button type="button" onclick="setStrategy('Buy when price breaks Bollinger upper band')" class="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white transition">Bollinger</button>
                                </div>
                            </div>

                            <button type="submit" class="w-full btn-gradient text-white font-semibold py-3 rounded-lg transition">
                                🚀 Generate & Backtest
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Right Column - Results -->
                <div class="lg:col-span-2 space-y-6">
                    <!-- Loading -->
                    <div id="loading" class="hidden glass rounded-2xl p-12 text-center">
                        <div class="animate-spin rounded-full h-16 w-16 border-4 border-indigo-500 border-t-transparent mx-auto mb-4"></div>
                        <p class="text-xl font-semibold text-white">🤖 AI is generating...</p>
                        <p class="text-slate-400 mt-2">This takes 5-10 seconds</p>
                    </div>

                    <!-- Code Review -->
                    <div id="code_review" class="hidden glass rounded-2xl p-6">
                        <h3 class="text-xl font-bold text-white mb-4">💻 Generated Code</h3>
                        <pre id="generated_code"><code></code></pre>
                        <div class="flex gap-4 mt-4">
                            <button type="button" onclick="editCode()" class="px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white transition">✏️ Edit</button>
                            <button type="button" onclick="runBacktestFromCode()" class="px-6 py-2 btn-gradient text-white font-semibold rounded-lg transition">🚀 Backtest</button>
                        </div>
                    </div>

                    <!-- Results -->
                    <div id="results" class="hidden space-y-6">
                        <!-- Metrics -->
                        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div class="metric-box rounded-xl p-4">
                                <p class="text-sm text-slate-400 mb-1">Total PnL</p>
                                <p id="metric_pnl" class="text-2xl font-bold text-emerald-400">$0.00</p>
                            </div>
                            <div class="metric-box rounded-xl p-4">
                                <p class="text-sm text-slate-400 mb-1">Return</p>
                                <p id="metric_return" class="text-2xl font-bold text-emerald-400">0.00%</p>
                            </div>
                            <div class="metric-box rounded-xl p-4">
                                <p class="text-sm text-slate-400 mb-1">Sharpe</p>
                                <p id="metric_sharpe" class="text-2xl font-bold text-indigo-400">0.00</p>
                            </div>
                            <div class="metric-box rounded-xl p-4">
                                <p class="text-sm text-slate-400 mb-1">Max DD</p>
                                <p id="metric_drawdown" class="text-2xl font-bold text-red-400">0.00%</p>
                            </div>
                            <div class="metric-box rounded-xl p-4">
                                <p class="text-sm text-slate-400 mb-1">Win Rate</p>
                                <p id="metric_winrate" class="text-2xl font-bold text-purple-400">0.00%</p>
                            </div>
                        </div>

                        <!-- Equity Chart -->
                        <div class="glass rounded-2xl p-6">
                            <h3 class="text-xl font-bold text-white mb-4">📈 Equity Curve</h3>
                            <div id="equity_chart" class="w-full h-96"></div>
                        </div>

                        <!-- Final Code -->
                        <div class="glass rounded-2xl p-6">
                            <h3 class="text-xl font-bold text-white mb-4">💻 Final Code</h3>
                            <pre id="final_code"><code class="text-sm">def strategy(data):<br>&nbsp;&nbsp;# Code will appear here...</code></pre>
                        </div>
                    </div>

                    <!-- Error -->
                    <div id="error" class="hidden glass rounded-2xl p-6 bg-red-500/10 border-l-4 border-red-500">
                        <h3 class="text-xl font-bold text-red-400 mb-2">❌ Error</h3>
                        <p id="error_message" class="text-red-300"></p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Settings Section -->
        <section id="section-settings" class="hidden-section">
            <div class="max-w-4xl mx-auto glass rounded-2xl p-8">
                <h2 class="text-2xl font-bold text-white mb-6">⚙️ Settings</h2>
                
                <div class="space-y-6">
                    <!-- Risk Management -->
                    <div class="glass rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-white mb-4">🛡️ Risk Management</h3>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm text-slate-300 mb-2">Position Size</label>
                                <select id="position_size" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white">
                                    <option value="1.0">100% (Full)</option>
                                    <option value="0.5">50%</option>
                                    <option value="0.25">25%</option>
                                    <option value="0.1">10%</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm text-slate-300 mb-2">Trailing Stop</label>
                                <select id="trailing_stop" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white">
                                    <option value="false">Disabled</option>
                                    <option value="0.02">2%</option>
                                    <option value="0.05">5%</option>
                                    <option value="0.10">10%</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- AI Provider -->
                    <div class="glass rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-white mb-4">🤖 AI Provider</h3>
                        <select id="ai_provider" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white">
                            <option value="local" selected>🚀 Local AI (Groq 70B - Free & Fast)</option>
                            <option value="deepseek">DeepSeek (Advanced)</option>
                            <option value="claude">Claude (Best Quality)</option>
                        </select>
                        <p class="text-sm text-slate-400 mt-2">Local AI uses Groq (embedded key - no setup needed).</p>
                    </div>

                    <!-- Advanced API Keys -->
                    <div class="glass rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-white mb-4">🔑 Advanced API Keys</h3>
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm text-slate-300 mb-2">DeepSeek API Key (Optional)</label>
                                <input type="password" id="deepseek_api_key" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white" placeholder="sk-...">
                            </div>
                            <div>
                                <label class="block text-sm text-slate-300 mb-2">Claude API Key (Optional)</label>
                                <input type="password" id="claude_api_key" class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white" placeholder="sk-ant-...">
                            </div>
                        </div>
                    </div>

                    <!-- Info -->
                    <div class="glass rounded-xl p-6 bg-emerald-500/10 border border-emerald-500/30">
                        <div class="flex items-start">
                            <span class="text-2xl mr-3">🔒</span>
                            <div>
                                <h4 class="text-white font-semibold mb-2">Security First</h4>
                                <p class="text-sm text-slate-300">Your API credentials are encrypted in transit (HTTPS), never stored on our servers, and only used for the current backtest request.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Results Section (Summary) -->
        <section id="section-results" class="hidden-section">
            <div class="max-w-6xl mx-auto">
                <h2 class="text-3xl font-bold text-white mb-8">📊 Backtest Results</h2>
                
                <!-- Summary Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="glass rounded-xl p-6">
                        <p class="text-sm text-slate-400 mb-2">Total PnL</p>
                        <p id="results_pnl" class="text-3xl font-bold text-emerald-400">$0.00</p>
                    </div>
                    <div class="glass rounded-xl p-6">
                        <p class="text-sm text-slate-400 mb-2">Return</p>
                        <p id="results_return" class="text-3xl font-bold text-emerald-400">0.00%</p>
                    </div>
                    <div class="glass rounded-xl p-6">
                        <p class="text-sm text-slate-400 mb-2">Sharpe Ratio</p>
                        <p id="results_sharpe" class="text-3xl font-bold text-indigo-400">0.00</p>
                    </div>
                    <div class="glass rounded-xl p-6">
                        <p class="text-sm text-slate-400 mb-2">Win Rate</p>
                        <p id="results_winrate" class="text-3xl font-bold text-purple-400">0.00%</p>
                    </div>
                </div>

                <!-- Chart -->
                <div class="glass rounded-2xl p-6 mb-8">
                    <h3 class="text-xl font-bold text-white mb-4">📈 Equity Curve</h3>
                    <div id="results_chart" class="w-full h-96"></div>
                </div>

                <!-- Code -->
                <div class="glass rounded-2xl p-6">
                    <h3 class="text-xl font-bold text-white mb-4">💻 Generated Strategy</h3>
                    <pre id="results_code"><code class="text-sm">def strategy(data):<br>&nbsp;&nbsp;# Code will appear here...</code></pre>
                </div>
            </div>
        </section>

    </main>

    <footer class="border-t border-white/10 py-6 mt-12">
        <div class="container mx-auto px-6 text-center text-slate-400">
            <p>Built for <strong class="text-slate-300">Bitget AI Hackathon S1</strong> | Trading Infra Track</p>
        </div>
    </footer>

    <script>
        let currentCode = null;

        // Navigation
        function showSection(section) {
            // Hide all sections
            document.getElementById('section-backtest').classList.remove('show-section');
            document.getElementById('section-backtest').classList.add('hidden-section');
            document.getElementById('section-settings').classList.remove('show-section');
            document.getElementById('section-settings').classList.add('hidden-section');
            document.getElementById('section-results').classList.remove('show-section');
            document.getElementById('section-results').classList.add('hidden-section');
            
            // Show selected section
            document.getElementById('section-' + section).classList.remove('hidden-section');
            document.getElementById('section-' + section).classList.add('show-section');
            
            // Update nav
            document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
            document.getElementById('nav-' + section).classList.add('active');
        }

        function setStrategy(text) {
            document.getElementById('strategy_input').value = text;
        }

        function toggleVisibility(fieldId) {
            const field = document.getElementById(fieldId);
            field.type = field.type === 'password' ? 'text' : 'password';
        }

        function obfuscateApiKey(key) {
            if (!key || key.length === 0) return '';
            const timestamp = Date.now().toString();
            const combined = key + '|' + timestamp;
            return btoa(combined);
        }

        async function generateCode() {
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('code_review').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
            
            const formData = new FormData();
            formData.append('strategy_input', document.getElementById('strategy_input').value);
            formData.append('ai_provider', document.getElementById('ai_provider').value);
            const deepseekKey = document.getElementById('deepseek_api_key').value || '';
            const claudeKey = document.getElementById('claude_api_key').value || '';
            formData.append('deepseek_api_key', deepseekKey ? obfuscateApiKey(deepseekKey) : '');
            formData.append('claude_api_key', claudeKey ? obfuscateApiKey(claudeKey) : '');
            formData.append('timeframe', document.getElementById('timeframe').value);
            
            try {
                const response = await fetch('/backtest/generate', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    currentCode = data.code;
                    document.getElementById('generated_code').innerHTML = syntaxHighlight(data.code);
                    document.getElementById('code_review').classList.remove('hidden');
                    document.getElementById('code_review').classList.add('show-section');
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

        function syntaxHighlight(code) {
            return code
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/\b(def|return|import|from|if|else|elif|for|while)\b/g, '<span class="code-keyword">$1</span>')
                .replace(/\b(print|len|range|str|int|float|bool|list|dict|set|tuple|abs|max|min|sum|round|pow|zip|enumerate|map|filter|open|eval|exec)\b/g, '<span class="code-function">$1</span>');
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
            
            const apiKey = document.getElementById('api_key').value.trim();
            const apiSecret = document.getElementById('api_secret').value.trim();
            if (apiKey) formData.append('api_key', apiKey);
            if (apiSecret) formData.append('api_secret', apiSecret);
            
            try {
                const response = await fetch('/backtest', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success && data.metrics) {
                    updateMetrics(data.metrics);
                    updateChart(data.charts.equity);
                    document.getElementById('final_code').innerHTML = syntaxHighlight(data.code);
                    document.getElementById('results').classList.remove('hidden');
                    
                    // Update results section
                    document.getElementById('results_pnl').textContent = '$' + data.metrics.pnl.toFixed(2);
                    document.getElementById('results_return').textContent = data.metrics.return_pct.toFixed(2) + '%';
                    document.getElementById('results_sharpe').textContent = data.metrics.sharpe.toFixed(2);
                    document.getElementById('results_winrate').textContent = data.metrics.win_rate.toFixed(1) + '%';
                    document.getElementById('results_chart').innerHTML = '';
                    updateChart(data.charts.equity, 'results_chart');
                    document.getElementById('results_code').innerHTML = syntaxHighlight(data.code);
                    
                    showSection('results');
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

        function updateMetrics(metrics) {
            const pnl = metrics.pnl || 0;
            const returnPct = metrics.return_pct || 0;
            
            document.getElementById('metric_pnl').textContent = '$' + pnl.toFixed(2);
            document.getElementById('metric_pnl').className = 'text-2xl font-bold ' + (pnl >= 0 ? 'text-emerald-400' : 'text-red-400');
            
            document.getElementById('metric_return').textContent = returnPct.toFixed(2) + '%';
            document.getElementById('metric_return').className = 'text-2xl font-bold ' + (returnPct >= 0 ? 'text-emerald-400' : 'text-red-400');
            
            document.getElementById('metric_sharpe').textContent = (metrics.sharpe || 0).toFixed(2);
            document.getElementById('metric_drawdown').textContent = (metrics.max_drawdown || 0).toFixed(2) + '%';
            document.getElementById('metric_winrate').textContent = (metrics.win_rate || 0).toFixed(1) + '%';
        }

        function updateChart(equity, elementId = 'equity_chart') {
            const equityTrace = {
                x: Array.from({length: equity.length}, (_, i) => i),
                y: equity,
                type: 'scatter',
                mode: 'lines',
                name: 'Equity',
                line: {color: '#6366f1', width: 3, shape: 'spline'},
                fill: 'tozeroy',
                fillcolor: 'rgba(99, 102, 241, 0.2)'
            };
            
            const layout = {
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
            
            Plotly.newPlot(elementId, [equityTrace], layout, {responsive: true, displayModeBar: false});
        }

        function editCode() {
            const codeArea = document.getElementById('generated_code');
            const newCode = prompt('Edit your strategy code:', codeArea.textContent);
            if (newCode) {
                currentCode = newCode;
                codeArea.innerHTML = syntaxHighlight(newCode);
            }
        }

        async function runBacktest(event) {
            event.preventDefault();
            await generateCode();
            if (currentCode) {
                await runBacktestFromCode();
            }
        }

        // Initialize
        showSection('backtest');
    </script>
</body>
</html>'''
    
    return HTMLResponse(content=html_content)


# ============================================================================
# BACKTEST ENDPOINTS
# ============================================================================

@app.post("/backtest/generate")
async def generate_endpoint(
    strategy_input: str = Form(...),
    ai_provider: str = Form("local"),
    deepseek_api_key: str = Form(""),
    claude_api_key: str = Form(""),
    timeframe: str = Form("1h"),
):
    """Generate strategy code from natural language"""
    try:
        api_keys = {}
        if deepseek_api_key:
            api_keys['deepseek'] = deepseek_api_key
        if claude_api_key:
            api_keys['claude'] = claude_api_key
        
        generated = generate_strategy_code(strategy_input, provider=ai_provider, api_keys=api_keys)
        
        if 'error' in generated:
            return JSONResponse({'success': False, 'error': generated['error']})
        
        code = generated['code']
        validation = validate_strategy(code)
        
        return JSONResponse({
            'success': True,
            'code': code,
            'strategy_type': generated.get('strategy_type', 'Custom'),
            'indicators': generated.get('indicators', []),
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
    """Run backtest on a strategy"""
    try:
        # Generate code if not provided
        if not generated_code:
            generated = generate_strategy_code(strategy_input, provider='local')
            if 'error' in generated:
                return JSONResponse({'success': False, 'error': generated['error']})
            code = generated['code']
        else:
            code = generated_code
        
        # Clean code before execution
        code = cleanup_strategy_code(code)
        
        # Validate code
        validation = validate_strategy(code)
        if not validation['valid']:
            return JSONResponse({
                'success': False,
                'error': 'Code validation failed: ' + ', '.join(validation['errors']),
                'validation_errors': validation['errors']
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
            return JSONResponse({'success': False, 'error': f"Backtest Error: {results['error']}"})
        
        # Extract metrics
        metrics = results.get('metrics', results)
        
        # Prepare charts
        charts = {
            'equity': results.get('equity_curve', []),
            'drawdown': results.get('drawdown_curve', [])
        }
        
        # Store in memory
        try:
            store_backtest(strategy_input, results, code)
        except:
            pass
        
        return JSONResponse({
            'success': True,
            'metrics': metrics,
            'charts': charts,
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
