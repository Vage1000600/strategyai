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

# Import with error handling to catch issues early
try:
    from ai_generator import generate_strategy_code, validate_strategy, validate_and_fix
    from backtester import run_backtest
    from memory_system import store_backtest, get_insights
    from strategy_scorer import score_strategy
    from position_sizing import calculate_position_size, check_portfolio_heat
    IMPORT_ERROR = None
except Exception as e:
    IMPORT_ERROR = str(e)
    import traceback
    IMPORT_TRACEBACK = traceback.format_exc()
    print(f"❌ IMPORT ERROR: {IMPORT_ERROR}")
    print(IMPORT_TRACEBACK)

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
    """Serve the main HTML page with import error check"""
    if IMPORT_ERROR:
        return HTMLResponse(
            content=f"<h1>❌ Import Error</h1><pre>{IMPORT_ERROR}\n\n{IMPORT_TRACEBACK}</pre>",
            status_code=500
        )
    return HTMLResponse(content=get_html_page())


@app.post("/backtest/generate")
async def generate_strategy(
    strategy_input: str = Form(...),
    ai_provider: str = Form('groq'),  # Changed default to groq
    groq_api_key: str = Form(None),
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
        # Deobfuscate API keys (encrypted in browser)
        def deobfuscate_key(encoded: str) -> str:
            """Deobfuscate API key encrypted in browser"""
            if not encoded:
                return ''
            try:
                import base64
                decoded = base64.b64decode(encoded).decode('utf-8')
                parts = decoded.split('|')
                return parts[0]  # Return just the key
            except:
                return encoded  # Return as-is if decoding fails
        
        # Build API keys dict (Groq uses embedded key, users only provide DeepSeek/Claude)
        api_keys = {}
        if deepseek_api_key:
            api_keys['deepseek'] = deobfuscate_key(deepseek_api_key)
        if claude_api_key:
            api_keys['claude'] = deobfuscate_key(claude_api_key)
        
        # Generate code with selected provider
        generated = generate_strategy_code(strategy_input, provider=ai_provider, api_keys=api_keys)
        if 'error' in generated:
            # If provider failed and has fallback, try local
            if generated.get('fallback') == 'local':
                generated = generate_strategy_code(strategy_input, provider='local')
            else:
                return JSONResponse({'success': False, 'error': f"AI Error: {generated['error']}"})
        
        # Enhanced validation with auto-fix
        validation = validate_and_fix(generated['code'])
        
        # If auto-fix was applied, use the fixed code
        if validation.get('fixes_applied') and len(validation['fixes_applied']) > 0:
            generated['code'] = validation['code']
            generated['reasoning'] = generated.get('reasoning', '') + f" [Auto-fixed: {', '.join(validation['fixes_applied'])}]"
        
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
    position_size: float = Form(1.0),
    trailing_stop: str = Form("false"),
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
            validate=True,
            position_size=position_size,
            trailing_stop=trailing_stop
        )
        
        if 'error' in results:
            return JSONResponse({'success': False, 'error': f"Backtest Error: {results['error']}"})
        
        # Extract metrics from new backtester structure
        metrics = results.get('metrics', results)  # Support both old and new structure
        
        # ENHANCEMENT 1: Store in memory for learning
        try:
            store_backtest(strategy_input, results, code)
        except Exception as e:
            pass
        
        # ENHANCEMENT 2: Score the strategy
        try:
            strategy_score = score_strategy(results)
        except Exception as e:
            strategy_score = {'error': str(e)}
        
        # ENHANCEMENT 3: Calculate position sizing recommendation
        try:
            current_price = results.get('current_price', 0)
            stop_price = current_price * (1 - metrics.get('max_drawdown', 0.1) / 100)
            position_rec = calculate_position_size(
                portfolio_value=initial_capital,
                entry_price=current_price,
                stop_loss_price=stop_price,
                method='fixed_risk'
            )
        except Exception as e:
            position_rec = {'error': str(e)}
        
        # Format results - handle both old and new structure
        benchmark = metrics.get('benchmark_return', 0)
        return_pct = metrics.get('return_pct', 0)
        outperf = return_pct - benchmark
        
        # Convert trades to list
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
                'pnl': float(metrics.get('total_pnl', metrics.get('pnl', 0))),
                'return_pct': float(return_pct),
                'sharpe': float(metrics.get('sharpe_ratio', metrics.get('sharpe', 0))),
                'max_drawdown': float(metrics.get('max_drawdown', 0)),
                'win_rate': float(metrics.get('win_rate', 0)),
                'total_trades': int(metrics.get('total_trades', 0)),
                'benchmark_return': float(benchmark),
                'outperformance': float(outperf),
                'profit_factor': float(metrics.get('profit_factor', 0)),
                'avg_win_loss': float(metrics.get('avg_win_loss', 0)),
            },
            'charts': {
                'equity': [float(x) for x in results.get('equity_curve', [])],
                'drawdown': [float(x) for x in results.get('drawdown_curve', results.get('drawdown', []))],
            },
            'trades': trades,
            'using_public_api': results.get('using_public_api', False),
            'validated': True,
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
    """Health check with import status"""
    if IMPORT_ERROR:
        return {'status': 'error', 'import_error': IMPORT_ERROR}
    return {'status': 'ok'}


@app.get("/debug/imports")
async def debug_imports():
    """Debug endpoint to check imports"""
    return {
        'import_error': IMPORT_ERROR,
        'traceback': IMPORT_TRACEBACK if 'IMPORT_TRACEBACK' in dir() else None,
        'ai_generator_ok': 'generate_strategy_code' in dir() or IMPORT_ERROR is not None,
        'backtester_ok': 'run_backtest' in dir() or IMPORT_ERROR is not None,
    }


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
    """Return the redesigned HTML page"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StrategyAI &mdash; AI Trading Strategy Backtester</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
  <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
  <style>
    :root {
      --bg-void:      #07080a;
      --bg-base:      #0c0e10;
      --bg-surface:   #101316;
      --bg-elevated:  #151820;
      --accent:       #f0a429;
      --accent-dim:   rgba(240,164,41,0.12);
      --accent-glow:  rgba(240,164,41,0.06);
      --text-primary: #e2e6ed;
      --text-secondary: #828997;
      --text-muted:   #424956;
      --border-sub:   rgba(255,255,255,0.052);
      --border-med:   rgba(255,255,255,0.09);
      --green:        #22c55e;
      --red:          #ef4444;
      --teal:         #2dd4bf;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body {
      font-family: 'Inter', -apple-system, sans-serif;
      background-color: var(--bg-void);
      background-image:
        radial-gradient(ellipse 100% 45% at 50% -5%, rgba(240,164,41,0.042) 0%, transparent 65%),
        radial-gradient(ellipse 55% 35% at 92% 92%, rgba(45,212,191,0.018) 0%, transparent 60%);
      color: var(--text-primary);
      min-height: 100vh;
      line-height: 1.6;
    }

    /* ─ Lucide icons ─ */
    [data-lucide] { display: inline-block; flex-shrink: 0; }

    /* ─ HEADER ─ */
    .site-header {
      border-bottom: 1px solid var(--border-sub);
      padding: 18px 0;
      position: sticky; top: 0; z-index: 100;
      background: rgba(7,8,10,0.82);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
    }
    .header-inner {
      max-width: 1300px; margin: 0 auto; padding: 0 28px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .logo { display: flex; align-items: center; gap: 12px; }
    .logo-icon {
      width: 36px; height: 36px;
      background: linear-gradient(135deg, #f0a429 0%, #d97706 100%);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 0 22px rgba(240,164,41,0.32), inset 0 1px 0 rgba(255,255,255,0.22);
    }
    .logo-icon [data-lucide] { width: 17px; height: 17px; color: #08090a; stroke-width: 2.8; }
    .logo-wordmark {
      font-family: 'Space Grotesk', sans-serif;
      font-size: 19px; font-weight: 700;
      color: var(--text-primary); letter-spacing: -0.025em;
    }
    .logo-tagline { font-size: 10.5px; color: var(--text-muted); margin-top: -1px; }
    .header-pill {
      font-size: 10px; font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      letter-spacing: 0.05em; color: var(--accent);
      background: var(--accent-dim);
      border: 1px solid rgba(240,164,41,0.2);
      border-radius: 6px; padding: 5px 11px;
    }

    /* ─ TAB NAVIGATION ─ */
    .tab-nav {
      display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap;
      border-bottom: 1px solid var(--border-sub); padding-bottom: 0;
    }
    .tab-btn {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 10px 18px; background: transparent;
      border: 1px solid var(--border-sub); border-radius: 8px;
      color: var(--text-secondary); font-size: 13px; font-weight: 600;
      cursor: pointer; transition: all .18s;
    }
    .tab-btn:hover { background: rgba(255,255,255,0.03); color: var(--text-primary); }
    .tab-btn.active {
      background: var(--accent-dim); border-color: rgba(240,164,41,0.3);
      color: var(--accent);
    }
    .tab-btn [data-lucide] { width: 14px; height: 14px; }

    /* ─ TAB CONTENT ─ */
    .tab-content { display: none; }
    .tab-content.active { display: block; }

    /* ─ LAYOUT ─ */
    .main-layout {
      max-width: 1300px; margin: 0 auto;
      padding: 28px 28px 80px;
    }

    /* ─ GLASS PANEL ─ */
    .glass-panel {
      background: rgba(12,14,16,0.72);
      backdrop-filter: blur(36px) saturate(1.4);
      -webkit-backdrop-filter: blur(36px) saturate(1.4);
      border: 1px solid var(--border-sub);
      border-radius: 16px;
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.038),
        inset 0 -1px 0 rgba(0,0,0,0.18),
        0 20px 70px rgba(0,0,0,0.52);
    }
    .glass-panel.warn-border { border-color: rgba(239,68,68,0.2); }

    /* ─ SIDEBAR ─ */
    .sidebar { position: sticky; top: 76px; }
    .sidebar-panel { overflow: hidden; }

    /* ─ SEGMENT ─ */
    .segment {
      padding: 22px 22px;
      border-bottom: 1px solid var(--border-sub);
    }
    .segment:last-child { border-bottom: none; padding-bottom: 24px; }
    .segment-hd {
      display: flex; align-items: center; gap: 10px;
      margin-bottom: 18px;
    }
    .seg-num {
      font-family: 'JetBrains Mono', monospace;
      font-size: 9.5px; font-weight: 700;
      color: var(--accent); letter-spacing: 0.08em;
    }
    .seg-label {
      font-size: 10px; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.11em;
      color: var(--text-muted);
    }
    .seg-icon {
      margin-left: auto; color: var(--text-muted);
    }
    .seg-icon [data-lucide] { width: 13px; height: 13px; }

    /* ─ STATUS BADGE ─ */
    .status-badge {
      display: flex; align-items: center; gap: 8px;
      padding: 8px 11px; border-radius: 8px;
      font-size: 11.5px; font-weight: 500; margin-bottom: 15px;
    }
    .status-badge [data-lucide] { width: 13px; height: 13px; }
    .status-badge.public {
      background: rgba(251,191,36,0.06);
      border: 1px solid rgba(251,191,36,0.16); color: #fbbf24;
    }
    .status-badge.connected {
      background: rgba(34,197,94,0.07);
      border: 1px solid rgba(34,197,94,0.18); color: var(--green);
    }

    /* ─ FIELD ─ */
    .field-group { margin-bottom: 13px; }
    .field-label {
      display: flex; align-items: center; gap: 6px;
      font-size: 10.5px; font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.08em;
      color: var(--text-secondary); margin-bottom: 7px;
    }
    .field-label [data-lucide] { width: 11px; height: 11px; }
    .field-opt {
      margin-left: auto; font-weight: 400;
      text-transform: none; letter-spacing: 0;
      font-size: 9.5px; color: var(--text-muted);
    }
    .field-hint {
      font-size: 10.5px; color: var(--text-muted);
      margin-top: 5px; line-height: 1.45;
    }
    .field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

    /* ─ INPUTS ─ */
    .input-field {
      width: 100%;
      background: rgba(255,255,255,0.025);
      border: 1px solid var(--border-sub);
      border-radius: 8px; padding: 9px 12px;
      color: var(--text-primary);
      font-family: 'Inter', sans-serif; font-size: 13px;
      outline: none; transition: border-color .18s, box-shadow .18s, background .18s;
      -webkit-appearance: none;
    }
    .input-field:focus {
      border-color: rgba(240,164,41,0.38);
      background: rgba(255,255,255,0.042);
      box-shadow: 0 0 0 3px rgba(240,164,41,0.09);
    }
    .input-field::placeholder { color: var(--text-muted); }
    select.input-field {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='11' height='11' viewBox='0 0 24 24' fill='none' stroke='%23424956' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 11px center;
      padding-right: 30px; cursor: pointer;
    }
    textarea.input-field { resize: vertical; min-height: 82px; line-height: 1.55; }
    .input-wrapper { position: relative; }
    .input-eye {
      position: absolute; right: 9px; top: 50%; transform: translateY(-50%);
      background: none; border: none; cursor: pointer;
      color: var(--text-muted); display: flex; align-items: center; padding: 4px;
      transition: color .18s;
    }
    .input-eye:hover { color: var(--text-secondary); }
    .input-eye [data-lucide] { width: 13px; height: 13px; }
    .has-eye { padding-right: 34px; }

    /* Encrypt dot */
    .enc-dot {
      width: 5px; height: 5px; border-radius: 50%;
      background: var(--green); margin-left: auto;
      display: none; box-shadow: 0 0 5px rgba(34,197,94,0.6);
    }
    .enc-dot.on { display: block; }

    /* ─ NOTICE ─ */
    .notice {
      display: flex; gap: 9px;
      padding: 10px 12px; border-radius: 8px;
      font-size: 11px; line-height: 1.5; margin-bottom: 13px;
    }
    .notice [data-lucide] { width: 13px; height: 13px; flex-shrink: 0; margin-top: 1px; }
    .notice.green {
      background: rgba(34,197,94,0.05);
      border: 1px solid rgba(34,197,94,0.14); color: #4ade80;
    }
    .notice.amber {
      background: var(--accent-glow);
      border: 1px solid rgba(240,164,41,0.13); color: #fbbf24;
    }

    /* ─ CHIP GRID ─ */
    .chip-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
    .chip {
      display: flex; align-items: center; gap: 7px;
      padding: 8px 10px;
      background: rgba(255,255,255,0.022);
      border: 1px solid var(--border-sub); border-radius: 8px;
      font-size: 11px; font-weight: 500;
      color: var(--text-secondary); cursor: pointer;
      transition: all .16s ease; text-align: left;
    }
    .chip [data-lucide] { width: 11px; height: 11px; flex-shrink: 0; }
    .chip:hover {
      background: var(--accent-dim);
      border-color: rgba(240,164,41,0.22); color: var(--accent);
    }

    /* ─ BUTTONS ─ */
    .btn-run {
      width: 100%; display: flex; align-items: center;
      justify-content: center; gap: 8px;
      padding: 13px 20px;
      background: linear-gradient(160deg, #f0a429 0%, #d97706 100%);
      color: #08090a;
      font-family: 'Space Grotesk', sans-serif;
      font-size: 14px; font-weight: 700;
      border: none; border-radius: 10px;
      cursor: pointer; transition: all .2s;
      letter-spacing: -0.01em;
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.24),
        inset 0 -1px 0 rgba(0,0,0,0.15),
        0 4px 22px rgba(240,164,41,0.28);
    }
    .btn-run:hover {
      transform: translateY(-1px);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.24),
        inset 0 -1px 0 rgba(0,0,0,0.15),
        0 8px 36px rgba(240,164,41,0.44);
    }
    .btn-run:active { transform: translateY(0); }
    .btn-run [data-lucide] { width: 16px; height: 16px; }

    .btn-ghost {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 9px 15px;
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border-med); border-radius: 8px;
      color: var(--text-secondary); font-size: 13px; font-weight: 500;
      cursor: pointer; transition: all .16s;
    }
    .btn-ghost:hover {
      background: rgba(255,255,255,0.07);
      color: var(--text-primary); border-color: rgba(255,255,255,0.14);
    }
    .btn-ghost [data-lucide] { width: 13px; height: 13px; }

    .btn-go {
      display: inline-flex; align-items: center; gap: 7px;
      padding: 9px 17px;
      background: linear-gradient(135deg, rgba(34,197,94,0.14), rgba(34,197,94,0.07));
      border: 1px solid rgba(34,197,94,0.24); border-radius: 8px;
      color: var(--green); font-size: 13px; font-weight: 600;
      cursor: pointer; transition: all .16s;
    }
    .btn-go:hover {
      background: linear-gradient(135deg, rgba(34,197,94,0.22), rgba(34,197,94,0.12));
      box-shadow: 0 4px 20px rgba(34,197,94,0.14);
    }
    .btn-go [data-lucide] { width: 13px; height: 13px; }

    /* ─ RIGHT PANEL ─ */
    .right-panel { display: flex; flex-direction: column; gap: 16px; }
    .panel-body { padding: 22px 24px; }
    .panel-title {
      display: flex; align-items: center; gap: 9px;
      font-family: 'Space Grotesk', sans-serif;
      font-size: 14.5px; font-weight: 700;
      color: var(--text-primary); margin-bottom: 16px;
      letter-spacing: -0.01em;
    }
    .panel-title [data-lucide] { width: 15px; height: 15px; color: var(--accent); }

    /* ─ LOADING ─ */
    .loading-wrap {
      display: none; text-align: center; padding: 52px 24px;
    }
    .loader-ring {
      width: 42px; height: 42px;
      border: 2px solid rgba(240,164,41,0.1);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin .75s linear infinite;
      margin: 0 auto 18px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .loading-ttl {
      font-family: 'Space Grotesk', sans-serif;
      font-size: 15px; font-weight: 600;
      color: var(--text-primary); margin-bottom: 6px;
    }
    .loading-sub { font-size: 12.5px; color: var(--text-muted); }

    /* ─ CODE BLOCK ─ */
    .code-block {
      background: #070809;
      border: 1px solid var(--border-sub); border-radius: 10px;
      padding: 17px; overflow-x: auto;
      max-height: 360px; overflow-y: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px; line-height: 1.75; color: #8899aa;
    }
    .code-block::-webkit-scrollbar { width: 4px; height: 4px; }
    .code-block::-webkit-scrollbar-track { background: transparent; }
    .code-block::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 4px; }

    /* ─ VALIDATION BAR ─ */
    .val-bar {
      display: flex; align-items: center; gap: 8px;
      padding: 8px 12px; border-radius: 8px;
      font-size: 11.5px; font-weight: 600; margin-bottom: 13px;
    }
    .val-bar [data-lucide] { width: 13px; height: 13px; }
    .val-bar.pass {
      background: rgba(34,197,94,0.07);
      border: 1px solid rgba(34,197,94,0.18); color: var(--green);
    }
    .val-bar.fail {
      background: rgba(239,68,68,0.07);
      border: 1px solid rgba(239,68,68,0.18); color: var(--red);
    }

    /* ─ METRICS GRID ─ */
    .metrics-grid {
      display: grid; grid-template-columns: repeat(5, 1fr);
      gap: 10px;
    }
    .mcard {
      background: rgba(255,255,255,0.017);
      border: 1px solid var(--border-sub); border-radius: 12px;
      padding: 16px 14px;
      position: relative; overflow: hidden;
      transition: all .2s;
    }
    .mcard::after {
      content: ''; position: absolute;
      top: 0; left: 14%; right: 14%; height: 1px;
      background: linear-gradient(90deg, transparent, rgba(240,164,41,0.28), transparent);
      opacity: 0; transition: opacity .2s;
    }
    .mcard:hover { border-color: rgba(240,164,41,0.14); background: rgba(255,255,255,0.026); }
    .mcard:hover::after { opacity: 1; }
    .mlabel {
      font-size: 9.5px; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.09em;
      color: var(--text-muted); margin-bottom: 9px;
    }
    .mval {
      font-family: 'Space Grotesk', sans-serif;
      font-size: 21px; font-weight: 700;
      letter-spacing: -0.025em; line-height: 1;
    }
    .v-green  { color: var(--green); }
    .v-red    { color: var(--red); }
    .v-amber  { color: var(--accent); }
    .v-teal   { color: var(--teal); }
    .v-muted  { color: var(--text-secondary); }

    /* ─ COMPARE PANEL ─ */
    .compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .cmp-label {
      font-size: 10px; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.09em;
      color: var(--text-muted); margin-bottom: 7px;
    }
    .cmp-val {
      font-family: 'Space Grotesk', sans-serif;
      font-size: 26px; font-weight: 700;
      letter-spacing: -0.03em;
    }

    /* ─ ERROR ─ */
    .err-hd {
      display: flex; align-items: center; gap: 8px;
      font-family: 'Space Grotesk', sans-serif;
      font-size: 14.5px; font-weight: 700;
      color: var(--red); margin-bottom: 9px;
    }
    .err-hd [data-lucide] { width: 16px; height: 16px; }
    .err-body { font-size: 12.5px; color: #f87171; line-height: 1.55; }

    /* ─ FOOTER ─ */
    .site-footer {
      border-top: 1px solid var(--border-sub);
      padding: 20px 0; text-align: center;
      font-size: 11.5px; color: var(--text-muted);
    }
    .site-footer strong { color: var(--text-secondary); }

    /* ─ UTILS ─ */
    .hidden { display: none !important; }
    .row    { display: flex; align-items: center; }
    .gap-2  { gap: 8px; }
    .mt-3   { margin-top: 12px; }

    /* ─ RESPONSIVE ─ */
    @media (max-width: 920px) {
      .main-layout { grid-template-columns: 1fr; }
      .sidebar { position: static; }
      .metrics-grid { grid-template-columns: repeat(3,1fr); }
    }
    @media (max-width: 560px) {
      .metrics-grid { grid-template-columns: 1fr 1fr; }
      .header-pill  { display: none; }
      .main-layout  { padding: 18px 16px 60px; }
    }
  </style>
</head>
<body>

<!-- ====== HEADER ====== -->
<header class="site-header">
  <div class="header-inner">
    <div class="logo">
      <div class="logo-icon">
        <i data-lucide="zap"></i>
      </div>
      <div>
        <div class="logo-wordmark">StrategyAI</div>
        <div class="logo-tagline">AI Trading Strategy Backtester</div>
      </div>
    </div>
    <div class="header-pill">Bitget AI Hackathon S1</div>
  </div>
</header>

<!-- ====== MAIN ====== -->
<main class="main-layout">

  <!-- ===== SIDEBAR ===== -->
  <aside class="sidebar">
    <div class="glass-panel sidebar-panel">

      <!-- Segment 01: Connection -->
      <div class="segment">
        <div class="segment-hd">
          <span class="seg-num">01</span>
          <span class="seg-label">Connection</span>
          <span class="seg-icon"><i data-lucide="plug"></i></span>
        </div>
                                            <option value="0.10">10%</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- AI Provider Selection -->
                            <div class="mb-5 pt-4 border-t border-white/10">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">🤖 AI Provider</label>
                                <select id="ai_provider" name="ai_provider" class="input-field">
                                    <option value="local" selected>🚀 Local AI (Groq 70B - Free & Fast)</option>
                                    <option value="deepseek">DeepSeek (Advanced, ~$0.01)</option>
                                    <option value="claude">Claude (Best Quality, ~$0.03)</option>
                                </select>
                                <p class="text-xs text-slate-500 mt-2">Local AI uses Groq (embedded key - no setup needed). Upgrade to DeepSeek/Claude for complex strategies.</p>
                            </div>
                            
                            <!-- DeepSeek API Key (Encrypted) -->
                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">
                                    🔑 DeepSeek API Key <span class="text-slate-500 text-xs">(Optional, Encrypted 🔒)</span>
                                </label>
                                <div class="relative">
                                    <input type="password" id="deepseek_api_key" name="deepseek_api_key" class="input-field pr-10" 
                                        placeholder="sk-..." autocomplete="off">
                                    <span id="deepseek-encrypt-status" class="absolute right-3 top-3 text-xs text-emerald-400 hidden">🔒</span>
                                </div>
                                <p class="text-xs text-slate-500 mt-2">Encrypted in browser before sending. Never stored.</p>
                            </div>
                            
                            <!-- Claude API Key (Encrypted) -->
                            <div class="mb-5">
                                <label class="block text-sm font-semibold text-slate-300 mb-2">
                                    🔑 Claude API Key <span class="text-slate-500 text-xs">(Optional, Encrypted 🔒)</span>
                                </label>
                                <div class="relative">
                                    <input type="password" id="claude_api_key" name="claude_api_key" class="input-field pr-10" 
                                        placeholder="sk-ant-..." autocomplete="off">
                                    <span id="claude-encrypt-status" class="absolute right-3 top-3 text-xs text-emerald-400 hidden">🔒</span>
                                </div>
                                <p class="text-xs text-slate-500 mt-2">Encrypted in browser before sending. Never stored.</p>
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
                                <select id="timeframe" name="timeframe" class="input-field" onchange="toggleCustomTimeframe()">
                                    <option value="1h">1 Hour</option>
                                    <option value="4h">4 Hours</option>
                                    <option value="1d">1 Day</option>
                                    <option value="custom">Custom...</option>
                                </select>
                                <input type="text" id="timeframe_custom" name="timeframe_custom" class="input-field mt-2 hidden" 
                                    placeholder="Enter timeframe (e.g., 5m, 15m, 2h, 3d, 1w)" 
                                    pattern="[0-9]+[mhdwM]" title="Format: number + m/h/d/w/M (e.g., 5m, 15m, 2h, 3d, 1w)">
                                <p class="text-xs text-slate-500 mt-2">Supported: m (minute), h (hour), d (day), w (week), M (month)</p>
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

        <div class="field-group">
          <label class="field-label">
            <i data-lucide="key-round"></i> Bitget API Key
            <span class="field-opt">Optional</span>
          </label>
          <div class="input-wrapper">
            <input type="password" id="api_key" class="input-field has-eye"
              placeholder="Leave empty for public API" autocomplete="off">
            <button type="button" class="input-eye" onclick="toggleEye('api_key',this)">
              <i data-lucide="eye"></i>
            </button>
          </div>
        </div>

        <div class="field-group">
          <label class="field-label">
            <i data-lucide="shield"></i> API Secret
            <span class="field-opt">Optional</span>
          </label>
          <div class="input-wrapper">
            <input type="password" id="api_secret" class="input-field has-eye"
              placeholder="Leave empty for public API" autocomplete="off">
            <button type="button" class="input-eye" onclick="toggleEye('api_secret',this)">
              <i data-lucide="eye"></i>
            </button>
          </div>
        </div>

        <div class="notice green">
          <i data-lucide="shield-check"></i>
          <span><strong>Encrypted transit.</strong> Credentials are never stored and only used for the active request.</span>
        </div>
      </div>

      <!-- Segment 02: Strategy -->
      <div class="segment">
        <div class="segment-hd">
          <span class="seg-num">02</span>
          <span class="seg-label">Strategy</span>
          <span class="seg-icon"><i data-lucide="brain-circuit"></i></span>
        </div>

        <div class="field-group">
          <label class="field-label"><i data-lucide="cpu"></i> AI Provider</label>
          <select id="ai_provider" class="input-field">
            <option value="local">Local Templates &mdash; Free, instant</option>
            <option value="deepseek">DeepSeek &mdash; Advanced, ~$0.01</option>
            <option value="claude">Claude &mdash; Best quality, ~$0.03</option>
          </select>
          <div class="field-hint">Local uses proven templates. Use DeepSeek or Claude for complex custom strategies.</div>
        </div>

        <div class="field-group">
          <label class="field-label">
            <i data-lucide="key-round"></i> DeepSeek API Key
            <div class="enc-dot" id="dot-deepseek"></div>
          </label>
          <input type="password" id="deepseek_api_key" class="input-field" placeholder="sk-..." autocomplete="off">
          <div class="field-hint">Encrypted in-browser before sending.</div>
        </div>

        <div class="field-group">
          <label class="field-label">
            <i data-lucide="key-round"></i> Claude API Key
            <div class="enc-dot" id="dot-claude"></div>
          </label>
          <input type="password" id="claude_api_key" class="input-field" placeholder="sk-ant-..." autocomplete="off">
          <div class="field-hint">Encrypted in-browser before sending.</div>
        </div>

        <div class="field-grid" style="margin-bottom:13px;">
          <div>
            <label class="field-label"><i data-lucide="bar-chart-2"></i> Pair</label>
            <select id="symbol" class="input-field">
              <option value="BTC/USDT">BTC/USDT</option>
              <option value="ETH/USDT">ETH/USDT</option>
              <option value="SOL/USDT">SOL/USDT</option>
              <option value="XRP/USDT">XRP/USDT</option>
              <option value="BNB/USDT">BNB/USDT</option>
            </select>
          </div>
          <div>
            <label class="field-label"><i data-lucide="timer"></i> Timeframe</label>
            <select id="timeframe" class="input-field" onchange="toggleCustomTF()">
              <option value="1h">1 Hour</option>
              <option value="4h">4 Hours</option>
              <option value="1d">1 Day</option>
              <option value="custom">Custom&hellip;</option>
            </select>
          </div>
        </div>
        <input type="text" id="timeframe_custom" class="input-field hidden"
          placeholder="e.g. 5m, 15m, 2h, 3d" style="margin-bottom:13px;"
          pattern="[0-9]+[mhdwM]">

        <div class="field-group">
          <label class="field-label"><i data-lucide="pencil-line"></i> Strategy Description</label>
          <textarea id="strategy_input" class="input-field"
            placeholder="e.g. Buy when RSI < 30 and volume is above average, sell when RSI > 70"></textarea>
        </div>

        <div>
          <label class="field-label" style="margin-bottom:9px;">
            <i data-lucide="layers"></i> Quick Select
          </label>
          <div class="chip-grid">
            <button class="chip" onclick="setStrategy('Buy when RSI < 30, sell when RSI > 70')">
              <i data-lucide="activity"></i> RSI Reversal
            </button>
            <button class="chip" onclick="setStrategy('Buy when MACD crosses above signal, sell when crosses below')">
              <i data-lucide="git-merge"></i> MACD Cross
            </button>
            <button class="chip" onclick="setStrategy('Buy when 50 EMA crosses above 200 EMA, sell on reverse')">
              <i data-lucide="trending-up"></i> Golden Cross
            </button>
            <button class="chip" onclick="setStrategy('Buy when price breaks above upper Bollinger Band, sell at middle')">
              <i data-lucide="align-center"></i> Bollinger
            </button>
          </div>
        </div>
      </div>

      <!-- Segment 03: Execution -->
      <div class="segment">
        <div class="segment-hd">
          <span class="seg-num">03</span>
          <span class="seg-label">Execution</span>
          <span class="seg-icon"><i data-lucide="sliders-horizontal"></i></span>
        </div>

        <div class="notice amber">
          <i data-lucide="sparkles"></i>
          <span>Long &amp; short, partial sizing, trailing stops, and multi-exit conditions supported.</span>
        </div>

        <div class="field-grid" style="margin-bottom:18px;">
          <div>
            <label class="field-label"><i data-lucide="percent"></i> Position Size</label>
            <select id="position_size" class="input-field">
              <option value="1.0">100% Full</option>
              <option value="0.5">50%</option>
              <option value="0.25">25%</option>
              <option value="0.1">10%</option>
            </select>
          </div>
          <div>
            <label class="field-label"><i data-lucide="arrow-down-to-line"></i> Trailing Stop</label>
            <select id="trailing_stop" class="input-field">
              <option value="false">Disabled</option>
              <option value="0.02">2%</option>
              <option value="0.05">5%</option>
              <option value="0.10">10%</option>
            </select>
          </div>
        </div>

        <button id="submit_btn" class="btn-run" onclick="runBacktest(event)">
          <i data-lucide="play-circle"></i>
          Generate &amp; Run Backtest
        </button>
      </div>

    </div><!-- /sidebar-panel -->
  </aside>

  <!-- ===== TAB NAVIGATION ===== -->
  <nav class="tab-nav">
    <button class="tab-btn active" onclick="switchTab('backtest')">
      <i data-lucide='cpu'></i> Backtest
    </button>
    <button class="tab-btn" onclick="switchTab('settings')">
      <i data-lucide='settings'></i> Settings
    </button>
    <button class="tab-btn" onclick="switchTab('results')">
      <i data-lucide='bar-chart-2'></i> Results
    </button>
    <button class="tab-btn" onclick="switchTab('help')">
      <i data-lucide='help-circle'></i> Help
    </button>
  </nav>

  <!-- ===== TAB CONTENT ===== -->
  <div class="tab-content" id="tab-backtest">
  <div class="right-panel">

    <!-- Loading -->
    <div id="loading" class="glass-panel loading-wrap">
      <div class="loader-ring"></div>
      <div class="loading-ttl">Generating strategy&hellip;</div>
      <div class="loading-sub">AI is thinking &mdash; usually 5&ndash;10 seconds</div>
    </div>

    <!-- Code Review -->
    <div id="code_review" class="glass-panel hidden">
      <div class="panel-body">
        <div class="panel-title">
          <i data-lucide="code-2"></i>
          Generated Strategy Code
        </div>
        <div id="code_validation" class="val-bar pass hidden">
          <!-- injected by JS -->
        </div>
        <div id="generated_code" class="code-block"></div>
        <div class="row gap-2 mt-3">
          <button class="btn-ghost" onclick="editCode()">
            <i data-lucide="pencil"></i> Edit Code
          </button>
          <button class="btn-go" onclick="runBacktestFromCode()">
            <i data-lucide="play"></i> Run Backtest
          </button>
        </div>
      </div>
    </div>

    <!-- Metrics -->
    <div class="metrics-grid" id="metrics_row">
      <div class="mcard">
        <div class="mlabel">Total PnL</div>
        <div id="metric_pnl" class="mval v-muted">&mdash;</div>
      </div>
      <div class="mcard">
        <div class="mlabel">Return</div>
        <div id="metric_return" class="mval v-muted">&mdash;</div>
      </div>
      <div class="mcard">
        <div class="mlabel">Sharpe</div>
        <div id="metric_sharpe" class="mval v-muted">&mdash;</div>
      </div>
      <div class="mcard">
        <div class="mlabel">Max Drawdown</div>
        <div id="metric_drawdown" class="mval v-muted">&mdash;</div>
      </div>
      <div class="mcard">
        <div class="mlabel">Win Rate</div>
        <div id="metric_winrate" class="mval v-muted">&mdash;</div>
      </div>
    </div>

    <!-- Compare vs B&H -->
    <div class="glass-panel">
      <div class="panel-body">
        <div class="panel-title">
          <i data-lucide="git-compare"></i>
          vs Buy &amp; Hold
        </div>
        <div class="compare-grid">
          <div>
            <div class="cmp-label">Buy &amp; Hold Return</div>
            <div id="metric_benchmark" class="cmp-val v-muted">&mdash;</div>
          </div>
          <div>
            <div class="cmp-label">Outperformance</div>
            <div id="metric_outperformance" class="cmp-val v-muted">&mdash;</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Equity Curve -->
    <div class="glass-panel">
      <div class="panel-body">
        <div class="panel-title">
          <i data-lucide="trending-up"></i>
          Equity Curve
        </div>
        <div id="equity_chart" style="width:100%;height:310px;"></div>
      </div>
    </div>

    <!-- Final Code -->
    <div class="glass-panel">
      <div class="panel-body">
        <div class="panel-title">
          <i data-lucide="file-code"></i>
          Final Generated Code
        </div>
        <div id="final_code" class="code-block">
          <span style="color:var(--text-muted);">Strategy code will appear after a successful backtest run.</span>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div id="error" class="glass-panel hidden warn-border">
      <div class="panel-body">
        <div class="err-hd">
          <i data-lucide="x-circle"></i>
          Something went wrong
        </div>
        <div id="error_message" class="err-body"></div>
      </div>
    </div>

  </div><!-- /right-panel -->
  </div><!-- /tab-backtest -->

  <!-- ===== SETTINGS TAB ===== -->
  <div class="tab-content" id="tab-settings">
    <div class="glass-panel">
      <div class="panel-body">
        <div class="panel-title">
          <i data-lucide='settings'></i>
          Settings & Configuration
        </div>
        
        <div class="segment" style="border-bottom: none; padding: 0 0 22px 0; margin-bottom: 0;">
          <div class="segment-hd">
            <span class="seg-num">01</span>
            <span class="seg-label">API Configuration</span>
          </div>

          <div class="status-badge public" id="api_status">
            <i data-lucide="globe" id="status_icon"></i>
            <span id="status_text">Using public API</span>
          </div>

          <div class="field-group">
            <label class="field-label">
              <i data-lucide="key-round"></i> Bitget API Key
              <span class="field-opt">Optional</span>
            </label>
            <div class="input-wrapper">
              <input type="password" id="api_key" class="input-field has-eye"
                placeholder="Leave empty for public API" autocomplete="off">
              <button type="button" class="input-eye" onclick="toggleEye('api_key',this)">
                <i data-lucide="eye"></i>
              </button>
            </div>
          </div>

          <div class="field-group">
            <label class="field-label">
              <i data-lucide="shield"></i> API Secret
              <span class="field-opt">Optional</span>
            </label>
            <div class="input-wrapper">
              <input type="password" id="api_secret" class="input-field has-eye"
                placeholder="Leave empty for public API" autocomplete="off">
              <button type="button" class="input-eye" onclick="toggleEye('api_secret',this)">
                <i data-lucide="eye"></i>
              </button>
            </div>
          </div>

          <div class="notice green">
            <i data-lucide="shield-check"></i>
            <span><strong>Encrypted transit.</strong> Credentials are never stored and only used for the active request.</span>
          </div>
        </div>

        <div class="segment" style="border-bottom: none; padding: 0 0 22px 0; margin-bottom: 0;">
          <div class="segment-hd">
            <span class="seg-num">02</span>
            <span class="seg-label">AI Provider Settings</span>
          </div>

          <div class="field-group">
            <label class="field-label"><i data-lucide="cpu"></i> Default AI Provider</label>
            <select id="ai_provider" class="input-field">
              <option value="groq">Groq (Free, Default)</option>
              <option value="deepseek">DeepSeek (Requires API Key)</option>
              <option value="claude">Claude (Requires API Key)</option>
              <option value="local">Local Templates (Offline)</option>
            </select>
            <div class="field-hint">Groq uses embedded free tier. DeepSeek/Claude require your API keys.</div>
          </div>

          <div class="field-group">
            <label class="field-label">
              <i data-lucide="key-round"></i> DeepSeek API Key
              <div class="enc-dot" id="dot-deepseek"></div>
            </label>
            <input type="password" id="deepseek_api_key" class="input-field" placeholder="sk-..." autocomplete="off">
            <div class="field-hint">Encrypted in-browser before sending.</div>
          </div>

          <div class="field-group">
            <label class="field-label">
              <i data-lucide="key-round"></i> Claude API Key
              <div class="enc-dot" id="dot-claude"></div>
            </label>
            <input type="password" id="claude_api_key" class="input-field" placeholder="sk-ant-..." autocomplete="off">
            <div class="field-hint">Encrypted in-browser before sending.</div>
          </div>
        </div>

        <div class="segment" style="border-bottom: none; padding: 0 0 22px 0; margin-bottom: 0;">
          <div class="segment-hd">
            <span class="seg-num">03</span>
            <span class="seg-label">Default Backtest Settings</span>
          </div>

          <div class="field-grid" style="margin-bottom:18px;">
            <div>
              <label class="field-label"><i data-lucide="bar-chart-2"></i> Default Pair</label>
              <select id="symbol" class="input-field">
                <option value="BTC/USDT">BTC/USDT</option>
                <option value="ETH/USDT">ETH/USDT</option>
                <option value="SOL/USDT">SOL/USDT</option>
                <option value="XRP/USDT">XRP/USDT</option>
                <option value="BNB/USDT">BNB/USDT</option>
              </select>
            </div>
            <div>
              <label class="field-label"><i data-lucide="timer"></i> Default Timeframe</label>
              <select id="timeframe" class="input-field" onchange="toggleCustomTF()">
                <option value="1h">1 Hour</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day</option>
                <option value="custom">Custom&hellip;</option>
              </select>
            </div>
          </div>
          <input type="text" id="timeframe_custom" class="input-field hidden"
            placeholder="e.g. 5m, 15m, 2h, 3d" style="margin-bottom:13px;"
            pattern="[0-9]+[mhdwM]">

          <div class="field-grid" style="margin-bottom:18px;">
            <div>
              <label class="field-label"><i data-lucide="percent"></i> Default Position Size</label>
              <select id="position_size" class="input-field">
                <option value="1.0">100% Full</option>
                <option value="0.5">50%</option>
                <option value="0.25">25%</option>
                <option value="0.1">10%</option>
              </select>
            </div>
            <div>
              <label class="field-label"><i data-lucide="arrow-down-to-line"></i> Trailing Stop</label>
              <select id="trailing_stop" class="input-field">
                <option value="false">Disabled</option>
                <option value="0.02">2%</option>
                <option value="0.05">5%</option>
                <option value="0.10">10%</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div><!-- /tab-settings -->

  <!-- ===== RESULTS TAB ===== -->
  <div class="tab-content" id="tab-results">
    <div class="glass-panel">
      <div class="panel-body">
        <div class="panel-title">
          <i data-lucide='bar-chart-2'></i>
          Backtest Results
        </div>
        <p style="color: var(--text-muted); margin-bottom: 24px;">Results will appear here after running a backtest.</p>
        
        <!-- Metrics -->
        <div class="metrics-grid" id="metrics_row">
          <div class="mcard">
            <div class="mlabel">Total PnL</div>
            <div id="metric_pnl" class="mval v-muted">&mdash;</div>
          </div>
          <div class="mcard">
            <div class="mlabel">Return</div>
            <div id="metric_return" class="mval v-muted">&mdash;</div>
          </div>
          <div class="mcard">
            <div class="mlabel">Sharpe</div>
            <div id="metric_sharpe" class="mval v-muted">&mdash;</div>
          </div>
          <div class="mcard">
            <div class="mlabel">Max Drawdown</div>
            <div id="metric_drawdown" class="mval v-muted">&mdash;</div>
          </div>
          <div class="mcard">
            <div class="mlabel">Win Rate</div>
            <div id="metric_winrate" class="mval v-muted">&mdash;</div>
          </div>
        </div>

        <!-- Compare vs B&H -->
        <div class="glass-panel" style="margin-top: 24px;">
          <div class="panel-body">
            <div class="panel-title">
              <i data-lucide="git-compare"></i>
              vs Buy &amp; Hold
            </div>
            <div class="compare-grid">
              <div>
                <div class="cmp-label">Buy &amp; Hold Return</div>
                <div id="metric_benchmark" class="cmp-val v-muted">&mdash;</div>
              </div>
              <div>
                <div class="cmp-label">Outperformance</div>
                <div id="metric_outperformance" class="cmp-val v-muted">&mdash;</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Equity Curve -->
        <div class="glass-panel" style="margin-top: 24px;">
          <div class="panel-body">
            <div class="panel-title">
              <i data-lucide="trending-up"></i>
              Equity Curve
            </div>
            <div id="equity_chart" style="width:100%;height:310px;"></div>
          </div>
        </div>

        <!-- Final Code -->
        <div class="glass-panel" style="margin-top: 24px;">
          <div class="panel-body">
            <div class="panel-title">
              <i data-lucide="file-code"></i>
              Final Generated Code
            </div>
            <div id="final_code" class="code-block">
              <span style="color:var(--text-muted);">Strategy code will appear after a successful backtest run.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div><!-- /tab-results -->

  <!-- ===== HELP TAB ===== -->
  <div class="tab-content" id="tab-help">
    <div class="glass-panel">
      <div class="panel-body">
        <div class="panel-title">
          <i data-lucide='help-circle'></i>
          Help & Documentation
        </div>
        
        <div style="margin-bottom: 24px;">
          <h3 style="color: var(--text-primary); margin-bottom: 12px;">📚 What is StrategyAI?</h3>
          <p style="color: var(--text-secondary); line-height: 1.7;">
            StrategyAI is an AI-powered trading strategy backtester that helps you test trading ideas before risking real money.
            Describe your strategy in plain English, and the AI will generate Python code to backtest it against historical data.
          </p>
        </div>

        <div style="margin-bottom: 24px;">
          <h3 style="color: var(--text-primary); margin-bottom: 12px;">🚀 Quick Start</h3>
          <ol style="color: var(--text-secondary); line-height: 1.8; padding-left: 20px;">
            <li>Go to the <strong>Backtest</strong> tab</li>
            <li>Enter your strategy description (or use a quick select template)</li>
            <li>Click <strong>Generate &amp; Run Backtest</strong></li>
            <li>Review the generated code and results</li>
            <li>Check the <strong>Results</strong> tab for detailed metrics</li>
          </ol>
        </div>

        <div style="margin-bottom: 24px;">
          <h3 style="color: var(--text-primary); margin-bottom: 12px;">📊 Understanding Results</h3>
          <div class="metrics-grid">
            <div>
              <div class="mlabel">Total PnL</div>
              <p class="field-hint">Total profit/loss in USDT</p>
            </div>
            <div>
              <div class="mlabel">Return</div>
              <p class="field-hint">Percentage return vs initial capital</p>
            </div>
            <div>
              <div class="mlabel">Sharpe</div>
              <p class="field-hint">Risk-adjusted return (higher is better)</p>
            </div>
            <div>
              <div class="mlabel">Max Drawdown</div>
              <p class="field-hint">Largest peak-to-trough decline (%)</p>
            </div>
            <div>
              <div class="mlabel">Win Rate</div>
              <p class="field-hint">Percentage of winning trades</p>
            </div>
          </div>
        </div>

        <div style="margin-bottom: 24px;">
          <h3 style="color: var(--text-primary); margin-bottom: 12px;">🔑 API Keys</h3>
          <p style="color: var(--text-secondary); line-height: 1.7; margin-bottom: 12px;">
            <strong>Bitget API Keys:</strong> Optional. Use your own for more accurate backtests with real market data.
          </p>
          <p style="color: var(--text-secondary); line-height: 1.7; margin-bottom: 12px;">
            <strong>AI Provider Keys:</strong> Groq is free by default. DeepSeek and Claude require your API keys for advanced strategies.
          </p>
          <p style="color: var(--accent); line-height: 1.7;">
            ⚠️ All keys are encrypted in-browser and never stored.
          </p>
        </div>

        <div>
          <h3 style="color: var(--text-primary); margin-bottom: 12px;">🎯 Hackathon Submission</h3>
          <p style="color: var(--text-secondary); line-height: 1.7;">
            Built for <strong>Bitget AI Trading Hackathon S1</strong> — Trading Infrastructure Track.
            Prize pool: <strong>$50,000 USDT</strong> ($6,600 grand prize + $50 guaranteed for valid submission).
            Deadline: <strong>June 30, 2026</strong>.
          </p>
        </div>
      </div>
    </div>
  </div><!-- /tab-help -->

</main>

<footer class="site-footer">
  Built for <strong>Bitget AI Hackathon S1</strong> &mdash; Trading Infrastructure Track
</footer>

<script>
  // ── Bootstrap Lucide ──
  lucide.createIcons();

  let currentCode = null;

  // ── Tab Navigation ──
  function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    // Deactivate all buttons
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    // Show selected tab
    document.getElementById('tab-' + tabName).classList.add('active');
    // Activate selected button
    event.target.closest('.tab-btn').classList.add('active');
    // Refresh icons
    lucide.createIcons();
  }

  // Toggle password visibility
  function toggleEye(fieldId, btn) {
    const f = document.getElementById(fieldId);
    const show = f.type === 'password';
    f.type = show ? 'text' : 'password';
    btn.innerHTML = show
      ? '<i data-lucide="eye-off"></i>'
      : '<i data-lucide="eye"></i>';
    lucide.createIcons();
  }

  // API status badge
  function refreshStatus() {
    const k = document.getElementById('api_key').value.trim();
    const s = document.getElementById('api_secret').value.trim();
    const badge = document.getElementById('api_status');
    const icon  = document.getElementById('status_icon');
    const text  = document.getElementById('status_text');
    if (k && s) {
      badge.className = 'status-badge connected';
      icon.setAttribute('data-lucide', 'check-circle-2');
      text.textContent = 'Connected — using your Bitget key';
    } else {
      badge.className = 'status-badge public';
      icon.setAttribute('data-lucide', 'globe');
      text.textContent = 'Using public API';
    }
    lucide.createIcons();
  }
  document.getElementById('api_key').addEventListener('input', refreshStatus);
  document.getElementById('api_secret').addEventListener('input', refreshStatus);

  // Encrypt dots
  [['deepseek_api_key','dot-deepseek'],['claude_api_key','dot-claude']].forEach(([id, dotId]) => {
    document.getElementById(id).addEventListener('input', function() {
      document.getElementById(dotId).classList.toggle('on', this.value.length > 0);
    });
  });

  function obfuscate(key) {
    if (!key) return '';
    return btoa(key + '|' + Date.now());
  }

  function setStrategy(text) {
    document.getElementById('strategy_input').value = text;
  }

  function toggleCustomTF() {
    const sel = document.getElementById('timeframe');
    const cust = document.getElementById('timeframe_custom');
    if (sel.value === 'custom') { cust.classList.remove('hidden'); cust.focus(); }
    else { cust.classList.add('hidden'); cust.value = ''; }
  }

  function getTF() {
    const sel = document.getElementById('timeframe');
    const cust = document.getElementById('timeframe_custom');
    return (sel.value === 'custom' && cust.value.trim()) ? cust.value.trim() : sel.value;
  }

  function hlCode(raw) {
    return raw
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/\\b(def|return|import|from|if|elif|else|for|while|in|not|and|or|True|False|None|class|try|except|pass|with|as|lambda)\\b/g,
        '<span style="color:#c792ea;">$1</span>')
      .replace(/(\\b\\d+\\.?\\d*\\b)/g, '<span style="color:#f78c6c;">$1</span>')
      .replace(/(#[^\\n]*)/g, '<span style="color:#546e7a;font-style:italic;">$1</span>')
      .replace(/(["\'])(?:(?=(\\\\?))\\2.)*?\\1/g, '<span style="color:#c3e88d;">$&</span>');
  }

  function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').classList.add('hidden');
    document.getElementById('code_review').classList.add('hidden');
  }
  function hideLoading() {
    document.getElementById('loading').style.display = 'none';
  }
  function showError(msg) {
    document.getElementById('error_message').textContent = msg;
    document.getElementById('error').classList.remove('hidden');
  }
  function setMetric(id, val, cls) {
    const el = document.getElementById(id);
    el.textContent = val;
    el.className = 'mval ' + cls;
  }

  async function generateCode() {
    showLoading();
    const fd = new FormData();
    fd.append('strategy_input', document.getElementById('strategy_input').value);
    fd.append('ai_provider', document.getElementById('ai_provider').value);
    fd.append('deepseek_api_key', obfuscate(document.getElementById('deepseek_api_key').value));
    fd.append('claude_api_key', obfuscate(document.getElementById('claude_api_key').value));
    fd.append('timeframe', getTF());
    try {
      const res  = await fetch('/backtest/generate', { method:'POST', body:fd });
      const data = await res.json();
      if (data.success) {
        currentCode = data.code;
        const vb = document.getElementById('code_validation');
        vb.classList.remove('hidden');
        if (data.validation.valid) {
          vb.className = 'val-bar pass';
          vb.innerHTML = '<i data-lucide="check-circle-2"></i> Code validated &mdash; no errors detected.';
        } else {
          vb.className = 'val-bar fail';
          vb.innerHTML = '<i data-lucide="x-circle"></i> Validation failed: ' + data.validation.errors.join(', ');
        }
        
        // Update API status based on input
        }
      } catch (err) {
        document.getElementById('error_message').textContent = 'Error: ' + err.message;
        document.getElementById('error').classList.remove('hidden');
      } finally {
        hideLoading();
      }
    }

    function editCode() {
      const codeArea = document.getElementById('generated_code');
      const newCode = prompt('Edit your strategy code:', codeArea.textContent);
      if (newCode) {
        currentCode = newCode;
        codeArea.innerHTML = hlCode(newCode);
      }
    }

    async function runBacktest(event) {
      event.preventDefault();
      await generateCode();
      if (currentCode) {
        await runBacktestFromCode();
      }
    }

    async function runBacktestFromCode() {
      if (!currentCode) return;
      showLoading();
      const fd = new FormData();
      fd.append('strategy_input', document.getElementById('strategy_input').value);
      fd.append('symbol', document.getElementById('symbol').value);
      fd.append('timeframe', getTF());
      fd.append('generated_code', currentCode);
      fd.append('position_size', document.getElementById('position_size').value);
      fd.append('trailing_stop', document.getElementById('trailing_stop').value);
      const ak = document.getElementById('api_key').value.trim();
      const as_ = document.getElementById('api_secret').value.trim();
      if (ak) fd.append('api_key', ak);
      if (as_) fd.append('api_secret', as_);
      try {
        const res = await fetch('/backtest', { method:'POST', body:fd });
        const data = await res.json();
        if (data.success && data.metrics) {
          const m = data.metrics;
          const pnl = m.pnl || 0;
          const ret = m.return_pct || 0;
          const op = m.outperformance || 0;
          setMetric('metric_pnl', '$' + pnl.toFixed(2), pnl >= 0 ? 'v-green' : 'v-red');
          setMetric('metric_return', ret.toFixed(2) + '%', ret >= 0 ? 'v-green' : 'v-red');
          setMetric('metric_sharpe', (m.sharpe||0).toFixed(2), 'v-amber');
          setMetric('metric_drawdown', (m.max_drawdown||0).toFixed(2) + '%', 'v-red');
          setMetric('metric_winrate', (m.win_rate||0).toFixed(1) + '%', 'v-teal');
          setMetric('metric_benchmark', ((m.benchmark_return||0).toFixed(2)) + '%', 'v-muted');
          setMetric('metric_outperformance', (op>=0?'+':'') + op.toFixed(2) + '%', op>=0?'v-green':'v-red');
          document.getElementById('final_code').innerHTML = hlCode(data.code || currentCode);
          Plotly.newPlot('equity_chart', [{
            x: Array.from({length: data.charts.equity.length}, (_,i) => i),
            y: data.charts.equity,
            type: 'scatter', mode: 'lines',
            line: { color:'#f0a429', width:2, shape:'spline' },
            fill: 'tozeroy', fillcolor: 'rgba(240,164,41,0.06)'
          }], {
            margin: { t:8, b:38, l:56, r:8 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor:  'rgba(0,0,0,0)',
            xaxis: { title: 'Candles', gridcolor: 'rgba(255,255,255,0.035)', tickfont: { color:'#424956', size:10, family:'JetBrains Mono' }, titlefont: { color:'#424956', size:10 } },
            yaxis: { title: 'Value (USDT)', gridcolor: 'rgba(255,255,255,0.035)', tickfont: { color:'#424956', size:10, family:'JetBrains Mono' }, titlefont: { color:'#424956', size:10 } },
            showlegend: false
          }, { responsive:true, displayModeBar:false });
        } else {
          showError(data.error);
        }
      } catch(e) { showError(e.message); }
      finally { hideLoading(); }
    }

    // Init
    refreshStatus();
  </script>
</body>
</html>"""
