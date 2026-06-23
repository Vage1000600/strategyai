# Quick Start Guide

## 🚀 3-Minute Setup

### Step 1: Open the App

**Live Demo:** https://strategyai.vercel.app

No installation needed! Works instantly.

---

### Step 2: Choose a Strategy

**Option A: Quick Test (Recommended for First Time)**

Click one of the preset buttons:
- 📊 **RSI Strategy** - Classic momentum strategy
- 📈 **MACD Crossover** - Trend-following strategy
- 🎯 **Golden Cross** - Moving average crossover
- 🔥 **Bollinger Breakout** - Volatility breakout

**Option B: Custom Strategy**

Type your own strategy in plain English:
```
"Buy when RSI < 30 and MACD > signal, sell when RSI > 70"
```

---

### Step 3: Configure Settings (Optional)

**Basic Settings:**
- Trading Pair: BTC/USDT, ETH/USDT, etc.
- Timeframe: 1h, 4h, 1d

**Advanced Settings:**
- Initial Capital: Default $1000
- Fee Rate: Default 0.1%
- Slippage: Default 0.05%

**API Key (Optional):**
- Leave empty → Uses public Bitget API (rate-limited)
- Add your key → Unlimited access (free to get)

---

### Step 4: Click "Generate & Backtest"

Wait 5-10 seconds. You'll see:

1. ✅ **Generated Code** - Your strategy converted to Python
2. 📊 **Performance Metrics** - PnL, Sharpe, Win Rate, etc.
3. 📈 **Equity Curve** - Visual chart of portfolio growth
4. 📉 **vs HODL** - How your strategy compares to buy & hold

---

## 📖 Example Strategies to Try

### Beginner

```
Buy when RSI < 30, sell when RSI > 70
```

```
Buy when MACD crosses above signal, sell when crosses below
```

### Intermediate

```
Buy when 50 EMA crosses above 200 EMA (golden cross), sell on death cross
```

```
Buy when price breaks above upper Bollinger Band, sell at middle band
```

### Advanced

```
Buy when RSI < 30 AND MACD > signal AND price > 200 EMA, sell when RSI > 70
```

```
Buy when price closes above 20-day high, sell at 10% profit or 5% stop loss
```

---

## 📊 Understanding Results

### Key Metrics

| Metric | What It Means | Good Value |
|--------|---------------|------------|
| **Total PnL** | Net profit/loss in USDT | Positive |
| **Return %** | Percentage return on capital | > 10% |
| **Sharpe Ratio** | Risk-adjusted return | > 1.0 |
| **Max Drawdown** | Largest peak-to-trough decline | < 20% |
| **Win Rate** | Percentage of winning trades | > 50% |
| **Profit Factor** | Gross profit / Gross loss | > 1.5 |
| **Beat HODL** | Outperformance vs buy & hold | Positive |

### Green Flags ✅

- Sharpe ratio > 1.0
- Win rate > 50%
- Profit factor > 1.5
- Max drawdown < 20%
- Consistent equity curve (smooth upward trend)

### Red Flags 🚩

- Sharpe ratio < 0.5
- Win rate < 40%
- Max drawdown > 30%
- Erratic equity curve
- Only 1-2 trades (not statistically significant)

---

## 💡 Pro Tips

### 1. Start Simple
Begin with basic strategies (RSI, MACD) before combining multiple indicators.

### 2. Test Multiple Timeframes
A strategy that works on 1h might not work on 1d. Test both!

### 3. Compare to HODL
If your strategy doesn't beat buy & hold, maybe just HODL is better.

### 4. Watch Drawdown
High returns with 50% drawdown = too risky. Aim for smooth growth.

### 5. Iterate
Use the generated code as a starting point. Refine and retest!

---

## 🔧 Troubleshooting

### "Strategy execution failed"
- Your strategy description is too vague
- Use simple, clear language
- Reference specific indicators (RSI, MACD, EMA, etc.)

### "No trades executed"
- Your conditions might be too strict
- Try a longer timeframe or different parameters
- Check if indicators are being detected

### "Public API failed"
- You hit the rate limit
- Add your free Bitget API key in settings
- Wait a few minutes and retry

### Results look wrong
- Check your strategy logic
- Verify the generated code matches your intent
- Try a different timeframe or trading pair

---

## 🎓 Learn More

- **Documentation:** https://github.com/Vage1000600/strategyai/wiki
- **Video Tutorial:** [Coming soon]
- **Community:** Bitget AI Hackathon Discord

---

## 🏆 Next Steps

1. ✅ Test your first strategy
2. 📊 Analyze the results
3. 🔧 Refine and optimize
4. 📈 Compare multiple strategies
5. 💾 Export your best strategies
6. 🚀 Deploy to production (optional)

---

*Happy Backtesting! 📈*

**Remember:** Past performance ≠ future results. Always do your own research!
