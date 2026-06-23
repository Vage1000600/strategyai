"""
StrategyAI - FastAPI Web App for Vercel
AI-Powered Trading Strategy Backtester
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
from datetime import datetime

from ai_generator import generate_strategy_code
from backtester import run_backtest
from visualization import plot_results

app = FastAPI(title="StrategyAI")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Strategy library
STRATEGY_LIBRARY = {
    "RSI Oversold/Overbought": "Buy when RSI < 30, sell when RSI > 70",
    "MACD Crossover": "Buy when MACD crosses above signal line, sell when it crosses below",
    "Golden Cross": "Buy when 50 EMA crosses above 200 EMA, sell when 50 EMA crosses below 200 EMA",
    "Bollinger Breakout": "Buy when price breaks above upper Bollinger Band, sell at middle band",
    "Mean Reversion": "Buy when price is 2 standard deviations below 20-day MA, sell at mean",
    "Dual Moving Average": "Buy when price crosses above 50 SMA, sell when it crosses below",
}


class StrategyRequest(BaseModel):
    strategy_input: str
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    initial_capital: float = 1000.0
    fee_rate: float = 0.1
    slippage: float = 0.05
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with strategy input form"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "strategies": list(STRATEGY_LIBRARY.keys()),
            "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"],
            "timeframes": ["1h", "4h", "1d"],
        }
    )


@app.post("/backtest")
async def backtest(
    strategy_input: str = Form(...),
    symbol: str = Form("BTC/USDT"),
    timeframe: str = Form("1h"),
    initial_capital: float = Form(1000.0),
    fee_rate: float = Form(0.1),
    slippage: float = Form(0.05),
    api_key: Optional[str] = Form(None),
    api_secret: Optional[str] = Form(None),
):
    """Run backtest on a strategy"""
    try:
        # Generate strategy code
        generated = generate_strategy_code(strategy_input)
        
        if "error" in generated:
            return JSONResponse({
                "success": False,
                "error": f"AI Error: {generated['error']}"
            })
        
        # Run backtest
        results = run_backtest(
            code=generated["code"],
            symbol=symbol,
            timeframe=timeframe,
            initial_capital=initial_capital,
            fee_rate=fee_rate / 100,
            slippage=slippage / 100,
            api_key=api_key if api_key else None,
            api_secret=api_secret if api_secret else None,
        )
        
        if "error" in results:
            return JSONResponse({
                "success": False,
                "error": f"Backtest Error: {results['error']}"
            })
        
        # Format results for frontend
        benchmark_return = results.get("benchmark_return", 0)
        strategy_return = results["return_pct"]
        outperformance = strategy_return - benchmark_return
        
        # Generate chart data
        equity_data = {
            "equity": results["equity_curve"],
            "drawdown": results.get("drawdown", []),
        }
        
        return JSONResponse({
            "success": True,
            "code": generated["code"],
            "strategy_type": generated.get("strategy_type", "Unknown"),
            "metrics": {
                "pnl": results["pnl"],
                "return_pct": results["return_pct"],
                "sharpe": results.get("sharpe", 0),
                "max_drawdown": results.get("max_drawdown", 0),
                "win_rate": results.get("win_rate", 0),
                "total_trades": results.get("total_trades", 0),
                "benchmark_return": benchmark_return,
                "outperformance": outperformance,
                "profit_factor": results.get("profit_factor", 0),
                "avg_win_loss": results.get("avg_win_loss", 0),
            },
            "charts": equity_data,
            "trades": results.get("trades", []).to_dict("records") if hasattr(results.get("trades"), "to_dict") else [],
            "using_public_api": results.get("using_public_api", False),
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/strategies")
async def get_strategies():
    """Get pre-built strategy library"""
    return {"strategies": STRATEGY_LIBRARY}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
