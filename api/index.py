<!DOCTYPE html>
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
        
        /* Modern dark theme */
        .dark {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            color: #e2e8f0;
        }
        
        /* Glass morphism cards */
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
        
        /* Gradient accents */
        .gradient-text {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .gradient-border {
            position: relative;
            background: rgba(30, 41, 59, 0.7);
            border-radius: 16px;
        }
        
        .gradient-border::before {
            content: '';
            position: absolute;
            inset: -1px;
            border-radius: 16px;
            padding: 1px;
            background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
        }
        
        /* Modern buttons */
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
        
        /* Input fields */
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
        
        .input-field::placeholder {
            color: #94a3b8;
        }
        
        /* Select dropdown */
        select.input-field {
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 20px;
            padding-right: 40px;
        }
        
        /* Metric cards */
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
        
        /* Loading animation */
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
        
        /* Glow effects */
        .glow {
            position: relative;
        }
        
        .glow::after {
            content: '';
            position: absolute;
            inset: -2px;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            border-radius: inherit;
            filter: blur(20px);
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: -1;
        }
        
        .glow:hover::after {
            opacity: 0.5;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.5);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(148, 163, 184, 0.3);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(148, 163, 184, 0.5);
        }
        
        /* Code block */
        pre {
            background: #0f172a;
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 20px;
            overflow-x: auto;
        }
        
        /* Info banner */
        .info-banner {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 16px;
        }
    </style>
</head>
<body class="min-h-screen">
    <!-- Header -->
    <header class="py-8 border-b border-white/5">
        <div class="container mx-auto px-4">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-5xl font-bold mb-2">
                        <span class="gradient-text">🚀 StrategyAI</span>
                    </h1>
                    <p class="text-xl text-slate-400">AI-Powered Trading Strategy Backtester</p>
                </div>
                <div class="hidden md:flex items-center space-x-4">
                    <a href="https://github.com/Vage1000600/strategyai" target="_blank" class="btn-secondary text-sm">
                        <svg class="inline w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                        </svg>
                        GitHub
                    </a>
                    <a href="https://www.bitget.com/activity-hub/hackathon" target="_blank" class="btn-secondary text-sm">
                        🏆 Bitget Hackathon
                    </a>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="container mx-auto px-4 pb-12">
        <div class="max-w-7xl mx-auto">
            <!-- Info Banner -->
            <div class="info-banner mb-8">
                <div class="flex items-center">
                    <span class="text-2xl mr-3">🎉</span>
                    <div>
                        <strong class="text-emerald-400">No Setup Required!</strong>
                        <span class="text-slate-300 ml-2">Using public Bitget API. Add your API key in settings for unlimited access.</span>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Left Column - Input Form -->
                <div class="lg:col-span-1">
                    <div class="glass-card p-6 sticky top-8">
                        <h2 class="text-2xl font-bold mb-6 flex items-center">
                            <span class="mr-2">⚙️</span>
                            Settings
                        </h2>
                        
                        <form id="backtestForm" onsubmit="runBacktest(event)">
                            <!-- Trading Pair -->
                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">📊 Trading Pair</label>
                                <select id="symbol" name="symbol" class="input-field">
                                    <option value="BTC/USDT">BTC/USDT</option>
                                    <option value="ETH/USDT">ETH/USDT</option>
                                    <option value="SOL/USDT">SOL/USDT</option>
                                    <option value="XRP/USDT">XRP/USDT</option>
                                    <option value="BNB/USDT">BNB/USDT</option>
                                </select>
                            </div>

                            <!-- Timeframe -->
                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">⏱️ Timeframe</label>
                                <select id="timeframe" name="timeframe" class="input-field">
                                    <option value="1h">1 Hour</option>
                                    <option value="4h">4 Hours</option>
                                    <option value="1d">1 Day</option>
                                </select>
                            </div>

                            <!-- Strategy Input -->
                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">📝 Your Strategy</label>
                                <textarea id="strategy_input" name="strategy_input" rows="4" 
                                    class="input-field" 
                                    placeholder="Example: Buy when RSI &lt; 30, sell when RSI &gt; 70"></textarea>
                            </div>

                            <!-- Quick Strategies -->
                            <div class="mb-6">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">🚀 Quick Strategies</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <button type="button" onclick="setStrategy('Buy when RSI &lt; 30, sell when RSI &gt; 70')" 
                                        class="btn-secondary text-sm flex items-center justify-center">
                                        📊 RSI Strategy
                                    </button>
                                    <button type="button" onclick="setStrategy('Buy when MACD crosses above signal, sell when crosses below')" 
                                        class="btn-secondary text-sm flex items-center justify-center">
                                        📈 MACD Crossover
                                    </button>
                                    <button type="button" onclick="setStrategy('Buy when 50 EMA crosses above 200 EMA, sell on reverse')" 
                                        class="btn-secondary text-sm flex items-center justify-center">
                                        🎯 Golden Cross
                                    </button>
                                    <button type="button" onclick="setStrategy('Buy when price breaks above upper Bollinger Band, sell at middle')" 
                                        class="btn-secondary text-sm flex items-center justify-center">
                                        🔥 Bollinger Breakout
                                    </button>
                                </div>
                            </div>

                            <!-- Submit Button -->
                            <button type="submit" class="btn-primary w-full glow">
                                <span class="flex items-center justify-center">
                                    <span class="mr-2">🚀</span>
                                    Generate & Backtest
                                </span>
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Right Column - Results -->
                <div class="lg:col-span-2 space-y-6">
                    <!-- Loading State -->
                    <div id="loading" class="hidden glass-card p-12 text-center">
                        <div class="loader mx-auto mb-4"></div>
                        <p class="text-xl font-semibold text-slate-300">🤖 AI is generating your strategy...</p>
                        <p class="text-slate-500 mt-2">This typically takes 5-10 seconds</p>
                    </div>

                    <!-- Results -->
                    <div id="results" class="space-y-6">
                        <!-- Metrics Cards -->
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
                                <p class="text-sm text-slate-400 mb-1">Sharpe Ratio</p>
                                <p id="metric_sharpe" class="text-2xl font-bold text-indigo-400">0.00</p>
                            </div>
                            <div class="metric-card">
                                <p class="text-sm text-slate-400 mb-1">Max Drawdown</p>
                                <p id="metric_drawdown" class="text-2xl font-bold text-red-400">0.00%</p>
                            </div>
                            <div class="metric-card">
                                <p class="text-sm text-slate-400 mb-1">Win Rate</p>
                                <p id="metric_winrate" class="text-2xl font-bold text-purple-400">0.00%</p>
                            </div>
                        </div>

                        <!-- Benchmark Comparison -->
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

                        <!-- Equity Curve Chart -->
                        <div class="glass-card p-6">
                            <h3 class="text-xl font-bold mb-4">📈 Equity Curve</h3>
                            <div id="equity_chart" class="w-full h-96"></div>
                        </div>

                        <!-- Generated Code -->
                        <div class="glass-card p-6">
                            <h3 class="text-xl font-bold mb-4">💻 Generated Code</h3>
                            <pre id="generated_code"><code class="text-sm text-emerald-400">def strategy(data):<br>&nbsp;&nbsp;# Strategy code will appear here...</code></pre>
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

    <!-- Footer -->
    <footer class="border-t border-white/5 py-8">
        <div class="container mx-auto px-4 text-center text-slate-400">
            <p>Built for <strong class="text-slate-300">Bitget AI Hackathon S1</strong> | Trading Infra Track</p>
            <p class="text-sm mt-2">
                <a href="https://github.com/Vage1000600/strategyai" class="text-indigo-400 hover:text-indigo-300 transition">GitHub</a> • 
                <a href="https://www.bitget.com/activity-hub/hackathon" class="text-indigo-400 hover:text-indigo-300 transition">Hackathon</a>
            </p>
        </div>
    </footer>

    <script>
        const strategies = {
            "RSI Oversold/Overbought": "Buy when RSI < 30, sell when RSI > 70",
            "MACD Crossover": "Buy when MACD crosses above signal line, sell when it crosses below",
            "Golden Cross": "Buy when 50 EMA crosses above 200 EMA, sell when 50 EMA crosses below 200 EMA",
            "Bollinger Breakout": "Buy when price breaks above upper Bollinger Band, sell at middle band",
            "Mean Reversion": "Buy when price is 2 standard deviations below 20-day MA, sell at mean",
            "Dual Moving Average": "Buy when price crosses above 50 SMA, sell when it crosses below"
        };
        
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
            
            try {
                const response = await fetch('/backtest', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    // Update metrics with color coding
                    const pnl = data.metrics.pnl;
                    const returnPct = data.metrics.return_pct;
                    
                    document.getElementById('metric_pnl').textContent = `$${pnl.toFixed(2)}`;
                    document.getElementById('metric_pnl').className = `text-2xl font-bold ${pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`;
                    
                    document.getElementById('metric_return').textContent = `${returnPct.toFixed(2)}%`;
                    document.getElementById('metric_return').className = `text-2xl font-bold ${returnPct >= 0 ? 'text-emerald-400' : 'text-red-400'}`;
                    
                    document.getElementById('metric_sharpe').textContent = data.metrics.sharpe.toFixed(2);
                    document.getElementById('metric_drawdown').textContent = `${data.metrics.max_drawdown.toFixed(2)}%`;
                    document.getElementById('metric_winrate').textContent = `${data.metrics.win_rate.toFixed(1)}%`;
                    document.getElementById('metric_benchmark').textContent = `${data.metrics.benchmark_return.toFixed(2)}%`;
                    
                    const outperf = data.metrics.outperformance;
                    const outperfEl = document.getElementById('metric_outperformance');
                    outperfEl.textContent = `${outperf >= 0 ? '+' : ''}${outperf.toFixed(2)}%`;
                    outperfEl.className = `text-2xl font-bold ${outperf >= 0 ? 'text-emerald-400' : 'text-red-400'}`;
                    
                    // Update code
                    document.getElementById('generated_code').innerHTML = data.code
                        .replace(/</g, '&lt;')
                        .replace(/>/g, '&gt;')
                        .replace(/def/g, '<span class="text-purple-400">def</span>')
                        .replace(/return/g, '<span class="text-purple-400">return</span>')
                        .replace(/if/g, '<span class="text-purple-400">if</span>')
                        .replace(/else/g, '<span class="text-purple-400">else</span>')
                        .replace(/elif/g, '<span class="text-purple-400">elif</span>');
                    
                    // Plot equity curve
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
                document.getElementById('error_message').textContent = 'Network error: ' + err.message;
                document.getElementById('error').classList.remove('hidden');
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }
    </script>
</body>
</html>
