"""
StrategyAI - Main Streamlit Application (FULLY IMPROVED)
Uses public Bitget API by default (no key required for testing)
Users can optionally provide their own API key

Features Added:
✅ Error handling & loading states
✅ Pre-built example strategies (one-click buttons)
✅ Progress indicators
✅ Input validation
✅ Strategy history
✅ Export results (CSV/JSON)
✅ Advanced settings
✅ Better error messages
✅ Strategy library (pre-saved)
✅ Buy & Hold benchmark comparison
✅ Expanded risk metrics
✅ Public API key (default) + User API key (optional)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import io
from ai_generator import generate_strategy_code
from backtester import run_backtest
from visualization import plot_results

# Page config
st.set_page_config(
    page_title="StrategyAI - AI Trading Strategy Backtester",
    page_icon="🚀",
    layout="wide"
)

# Initialize session state
if 'strategy_history' not in st.session_state:
    st.session_state.strategy_history = []
if 'last_results' not in st.session_state:
    st.session_state.last_results = None

# Pre-built strategy library
STRATEGY_LIBRARY = {
    "RSI Oversold/Overbought": "Buy when RSI < 30, sell when RSI > 70",
    "MACD Crossover": "Buy when MACD crosses above signal line, sell when it crosses below",
    "Golden Cross": "Buy when 50 EMA crosses above 200 EMA, sell when 50 EMA crosses below 200 EMA",
    "Bollinger Breakout": "Buy when price breaks above upper Bollinger Band, sell at middle band",
    "Mean Reversion": "Buy when price is 2 standard deviations below 20-day MA, sell at mean",
    "Dual Moving Average": "Buy when price crosses above 50 SMA, sell when it crosses below",
    "RSI + MACD Combo": "Buy when RSI < 30 and MACD > signal, sell when RSI > 70",
    "Breakout Strategy": "Buy when price breaks above 20-day high, sell at 10% profit or 5% stop loss"
}

# Custom CSS for better UI
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #1f2937;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .info-banner {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #00CC96;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🚀 StrategyAI")
st.subheader("Describe Your Trading Strategy in English. We'll Code It, Backtest It, Optimize It.")

# Info banner about public API
st.markdown("""
<div class="info-banner">
<strong>🎉 No Setup Required!</strong> Using public Bitget API for testing. 
Want unlimited access? <a href="#api-settings">Add your API key below</a>.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Sidebar - Settings
st.sidebar.header("⚙️ Settings")

# API Key Configuration (Optional)
st.sidebar.header("🔑 API Settings")
st.sidebar.markdown("### Bitget API (Optional)")
st.sidebar.info("""
**Using public API** for testing (rate-limited).

Get your **free** API key for unlimited access:
1. Go to bitget.com
2. Profile → API Management
3. Create read-only key
""")

user_api_key = st.sidebar.text_input(
    "API Key (Optional)",
    type="password",
    placeholder="Leave empty for public API",
    help="Your personal Bitget API key (optional)"
)

user_api_secret = st.sidebar.text_input(
    "API Secret (Optional)",
    type="password",
    placeholder="Leave empty for public API",
    help="Your personal Bitget API secret (optional)"
)

# Show API status
if user_api_key and user_api_secret:
    st.sidebar.success("✅ Using your API key")
else:
    st.sidebar.warning("⚠️ Using public API (rate-limited)")

# Trading pair and timeframe
symbol = st.sidebar.selectbox(
    "Trading Pair",
    ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"],
    index=0
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1h", "4h", "1d"],
    index=0
)

# Advanced Settings (Collapsible)
with st.sidebar.expander("⚙️ Advanced Settings"):
    initial_capital = st.number_input(
        "Initial Capital (USDT)",
        min_value=100,
        max_value=100000,
        value=1000,
        step=100
    )
    
    fee_rate = st.slider(
        "Trading Fee (%)",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.01
    )
    
    slippage = st.slider(
        "Slippage (%)",
        min_value=0.0,
        max_value=1.0,
        value=0.05,
        step=0.01
    )
    
    st.info("💡 Lower fees/slippage = more optimistic results")

# Strategy Library (Pre-saved)
st.sidebar.header("📚 Strategy Library")
selected_strategy = st.sidebar.selectbox(
    "Load a pre-built strategy:",
    ["Custom"] + list(STRATEGY_LIBRARY.keys())
)

# Main input area
st.header("📝 Describe Your Strategy")

# Pre-filled input if strategy selected from library
default_value = STRATEGY_LIBRARY.get(selected_strategy, "")

strategy_input = st.text_area(
    "Enter your trading strategy in natural language:",
    value=default_value,
    placeholder="Example: Buy when RSI < 30, sell when RSI > 70",
    height=150
)

# One-click example buttons
st.markdown("**⚡ Quick Test Strategies:**")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 RSI Strategy", use_container_width=True):
        strategy_input = "Buy when RSI < 30, sell when RSI > 70"
        st.rerun()

with col2:
    if st.button("📈 MACD Crossover", use_container_width=True):
        strategy_input = "Buy when MACD crosses above signal, sell when it crosses below"
        st.rerun()

with col3:
    if st.button("🎯 Golden Cross", use_container_width=True):
        strategy_input = "Buy when 50 EMA crosses above 200 EMA, sell on reverse"
        st.rerun()

with col4:
    if st.button("🔥 Bollinger Breakout", use_container_width=True):
        strategy_input = "Buy when price breaks above upper Bollinger Band, sell at middle"
        st.rerun()

# Input validation
def validate_input(text):
    if not text or len(text.strip()) == 0:
        return False, "Please enter a strategy description"
    if len(text) < 10:
        return False, "Strategy too short. Please provide more detail (min 10 characters)"
    if len(text) > 500:
        return False, "Strategy too long. Please simplify (max 500 characters)"
    return True, ""

# Backtest button
if st.button("🚀 Generate & Backtest", type="primary", use_container_width=True):
    # Validate input
    is_valid, error_msg = validate_input(strategy_input)
    if not is_valid:
        st.warning(f"⚠️ {error_msg}")
        st.stop()
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Generate code from natural language
    status_text.text("🤖 Step 1/3: AI is generating your strategy code...")
    progress_bar.progress(33)
    
    generated_code = generate_strategy_code(strategy_input)
    
    if generated_code.get("error"):
        st.error(f"❌ AI Error: {generated_code['error']}")
        st.info("💡 Tip: Try rephrasing your strategy. Use simple language like 'Buy when RSI < 30, sell when RSI > 70'")
        progress_bar.empty()
        status_text.empty()
        st.stop()
    
    st.success("✅ Strategy code generated!")
    
    # Show generated code
    with st.expander("👀 View Generated Code"):
        st.code(generated_code["code"], language="python")
    
    # Step 2: Run backtest
    status_text.text("📊 Step 2/3: Running backtest on historical data...")
    progress_bar.progress(66)
    
    backtest_results = run_backtest(
        code=generated_code["code"],
        symbol=symbol,
        timeframe=timeframe,
        initial_capital=initial_capital,
        fee_rate=fee_rate/100,
        slippage=slippage/100,
        api_key=user_api_key if user_api_key else None,
        api_secret=user_api_secret if user_api_secret else None
    )
    
    if backtest_results.get("error"):
        st.error(f"❌ Backtest Error: {backtest_results['error']}")
        st.info("💡 Tip: Make sure your strategy uses supported indicators: RSI, MACD, EMA, SMA, BB, ATR")
        if "public API" in backtest_results['error'].lower():
            st.warning("""
            ### 🔑 Need Unlimited Access?
            
            Get your **free** Bitget API key:
            1. Go to https://www.bitget.com/
            2. Profile → API Management
            3. Create new API key (read-only)
            4. Enter it in the sidebar above
            
            This will remove rate limits!
            """)
        progress_bar.empty()
        status_text.empty()
        st.stop()
    
    # Step 3: Display results
    status_text.text("📈 Step 3/3: Analyzing results...")
    progress_bar.progress(100)
    
    st.success("✅ Backtest complete!")
    
    # Show API mode used
    if backtest_results.get('using_public_api'):
        st.info("ℹ️ Used public Bitget API (rate-limited). Add your API key in sidebar for unlimited access.")
    
    # Store in session state
    st.session_state.last_results = backtest_results
    st.session_state.strategy_history.append({
        'id': datetime.now().strftime("%Y%m%d%H%M%S"),
        'name': strategy_input[:50] + "..." if len(strategy_input) > 50 else strategy_input,
        'symbol': symbol,
        'timeframe': timeframe,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    # Metrics row with benchmark comparison
    st.header("📊 Performance Summary")
    
    # Calculate buy & hold benchmark
    benchmark_return = backtest_results.get('benchmark_return', 0)
    strategy_return = backtest_results['return_pct']
    outperformance = strategy_return - benchmark_return
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        pnl = backtest_results["pnl"]
        color = "🟢" if pnl > 0 else "🔴"
        st.metric(f"{color} Total PnL", f"${pnl:.2f}")
    
    with col2:
        return_pct = backtest_results["return_pct"]
        color = "🟢" if return_pct > 0 else "🔴"
        st.metric(f"{color} Return", f"{return_pct:.2f}%")
    
    with col3:
        st.metric("📈 Sharpe Ratio", f"{backtest_results['sharpe']:.2f}")
    
    with col4:
        st.metric("📉 Max Drawdown", f"{backtest_results['max_drawdown']:.2f}%")
    
    with col5:
        st.metric("🎯 Win Rate", f"{backtest_results['win_rate']:.1f}%")
    
    # Benchmark comparison
    st.markdown("---")
    col_bench1, col_bench2 = st.columns(2)
    
    with col_bench1:
        st.metric("📊 Buy & Hold Return", f"{benchmark_return:.2f}%")
    
    with col_bench2:
        if outperformance > 0:
            st.success(f"✅ Beat HODL by {outperformance:.2f}%!")
        elif outperformance < 0:
            st.warning(f"❌ Underperformed HODL by {abs(outperformance):.2f}%")
        else:
            st.info("➡️ Matched HODL performance")
    
    # Additional risk metrics
    if 'profit_factor' in backtest_results:
        st.subheader("📈 Advanced Risk Metrics")
        col_adv1, col_adv2, col_adv3, col_adv4 = st.columns(4)
        
        with col_adv1:
            st.metric("Profit Factor", f"{backtest_results.get('profit_factor', 0):.2f}")
        with col_adv2:
            st.metric("Avg Win/Loss Ratio", f"{backtest_results.get('avg_win_loss', 0):.2f}")
        with col_adv3:
            st.metric("Longest Win Streak", backtest_results.get('longest_win_streak', 0))
        with col_adv4:
            st.metric("Recovery Factor", f"{backtest_results.get('recovery_factor', 0):.2f}")
    
    # Charts
    st.header("📊 Performance Charts")
    
    # Equity curve
    fig_equity = plot_results.plot_equity_curve(
        backtest_results["equity_curve"],
        backtest_results.get('initial_capital', initial_capital)
    )
    st.plotly_chart(fig_equity, use_container_width=True)
    
    # Drawdown chart
    fig_drawdown = plot_results.plot_drawdown(
        backtest_results["drawdown"]
    )
    st.plotly_chart(fig_drawdown, use_container_width=True)
    
    # Trade breakdown
    st.header("💼 Trade Breakdown")
    if not backtest_results["trades"].empty:
        st.dataframe(
            backtest_results["trades"],
            use_container_width=True
        )
        
        # Export buttons
        st.subheader("📥 Export Results")
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            # Download CSV
            csv_data = backtest_results["trades"].to_csv(index=False)
            st.download_button(
                label="📥 Download Trades (CSV)",
                data=csv_data,
                file_name=f"trades_{symbol.replace('/', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_exp2:
            # Download full results
            import json
            results_json = json.dumps({
                'strategy': strategy_input,
                'symbol': symbol,
                'timeframe': timeframe,
                'metrics': {
                    'pnl': backtest_results['pnl'],
                    'return_pct': backtest_results['return_pct'],
                    'sharpe': backtest_results['sharpe'],
                    'max_drawdown': backtest_results['max_drawdown'],
                    'win_rate': backtest_results['win_rate'],
                    'total_trades': backtest_results['total_trades'],
                    'benchmark_return': benchmark_return,
                    'outperformance': outperformance
                }
            }, indent=2)
            
            st.download_button(
                label="📥 Download Results (JSON)",
                data=results_json,
                file_name=f"results_{symbol.replace('/', '_')}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col_exp3:
            # Download code
            st.download_button(
                label="📥 Download Strategy Code",
                data=generated_code["code"],
                file_name=f"strategy_{symbol.replace('/', '_')}.py",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("ℹ️ No trades were executed with this strategy. Try adjusting your parameters.")
    
    # Clear progress
    progress_bar.empty()
    status_text.empty()

# Recent strategies (sidebar)
if len(st.session_state.strategy_history) > 0:
    st.sidebar.header("📚 Recent Strategies")
    for strat in reversed(st.session_state.strategy_history[-5:]):
        with st.sidebar.expander(f"⏱️ {strat['timestamp']}"):
            st.write(f"**Strategy:** {strat['name']}")
            st.write(f"**Pair:** {strat['symbol']}")
            st.write(f"**Timeframe:** {strat['timeframe']}")

# Footer
st.markdown("---")
st.markdown(
    "Built for **Bitget AI Hackathon S1** | "
    "Track: Trading Infra | "
    "[GitHub](https://github.com/Vage1000600/strategyai) | "
    "[Documentation](https://github.com/Vage1000600/strategyai/blob/main/README.md)"
)

# Hide Streamlit branding
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)
