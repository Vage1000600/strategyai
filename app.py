"""
StrategyAI - Main Streamlit Application
Person 4: UI/UX + Integration Lead
"""

import streamlit as st
from ai_generator import generate_strategy_code
from backtester import run_backtest
from visualization import plot_results

# Page config
st.set_page_config(
    page_title="StrategyAI - AI Trading Strategy Backtester",
    page_icon="🚀",
    layout="wide"
)

# Title
st.title("🚀 StrategyAI")
st.subheader("Describe Your Trading Strategy in English. We'll Code It, Backtest It, Optimize It.")

# Sidebar - Settings
st.sidebar.header("⚙️ Settings")

symbol = st.sidebar.selectbox(
    "Trading Pair",
    ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"],
    index=0
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1h", "4h", "1d"],
    index=0
)

initial_capital = st.sidebar.number_input(
    "Initial Capital (USDT)",
    min_value=100,
    max_value=100000,
    value=1000,
    step=100
)

# Main input area
st.header("📝 Describe Your Strategy")

strategy_input = st.text_area(
    "Enter your trading strategy in natural language:",
    placeholder="Example: Buy when RSI < 30, sell when RSI > 70",
    height=150
)

# Example strategies
with st.expander("📚 See Example Strategies"):
    st.code("Buy when RSI < 30, sell when RSI > 70")
    st.code("Buy when MACD crosses above signal line, sell when it crosses below")
    st.code("Buy when 50 EMA crosses above 200 EMA, sell on reverse")
    st.code("Buy when price breaks above 20-day high, sell at 10% profit")

# Backtest button
if st.button("🚀 Generate & Backtest", type="primary", use_container_width=True):
    if not strategy_input:
        st.warning("Please enter your strategy description")
    else:
        with st.spinner("🤖 AI is generating your strategy code..."):
            # Step 1: Generate code from natural language
            generated_code = generate_strategy_code(strategy_input)
            
            if generated_code.get("error"):
                st.error(f"❌ AI Error: {generated_code['error']}")
            else:
                st.success("✅ Strategy code generated!")
                
                # Show generated code
                with st.expander("👀 View Generated Code"):
                    st.code(generated_code["code"], language="python")
                
                # Step 2: Run backtest
                with st.spinner("📊 Running backtest on historical data..."):
                    backtest_results = run_backtest(
                        code=generated_code["code"],
                        symbol=symbol,
                        timeframe=timeframe,
                        initial_capital=initial_capital
                    )
                    
                    if backtest_results.get("error"):
                        st.error(f"❌ Backtest Error: {backtest_results['error']}")
                    else:
                        # Step 3: Display results
                        st.success("✅ Backtest complete!")
                        
                        # Metrics row
                        col1, col2, col3, col4 = st.columns(4)
                        
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
                        
                        # Charts
                        st.header("📊 Performance Charts")
                        
                        # Equity curve
                        fig_equity = plot_results.plot_equity_curve(
                            backtest_results["equity_curve"]
                        )
                        st.plotly_chart(fig_equity, use_container_width=True)
                        
                        # Drawdown chart
                        fig_drawdown = plot_results.plot_drawdown(
                            backtest_results["drawdown"]
                        )
                        st.plotly_chart(fig_drawdown, use_container_width=True)
                        
                        # Trade breakdown
                        st.header("💼 Trade Breakdown")
                        st.dataframe(
                            backtest_results["trades"],
                            use_container_width=True
                        )
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Strategy Code",
                            data=generated_code["code"],
                            file_name=f"strategy_{symbol.replace('/', '_')}.py",
                            mime="text/plain"
                        )

# Footer
st.markdown("---")
st.markdown(
    "Built for **Bitget AI Hackathon S1** | "
    "Track: Trading Infra | "
    "[GitHub](https://github.com/YOUR_USERNAME/strategyai)"
)
