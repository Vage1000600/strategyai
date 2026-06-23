# StrategyAI 🚀

## AI-Powered Trading Strategy Backtester for Bitget

**Describe your trading strategy in English. We'll code it, backtest it, and show you the results.**

![Bitget AI Hackathon](https://img.shields.io/badge/Bitget%20AI%20Hackathon-S1-blue)
![Track](https://img.shields.io/badge/Track-Trading%20Infra-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black?logo=vercel)

---

## 🎯 What Is This?

StrategyAI lets you **backtest trading strategies without writing code**. Just describe your strategy in natural language, and our AI converts it to executable code, runs it on historical Bitget data, and shows you the results.

### Example:
```
You type: "Buy when RSI < 30, sell when RSI > 70"

AI generates:
if rsi < 30:
    buy()
elif rsi > 70:
    sell()

Results:
- PnL: +$347 (34.7%)
- Sharpe: 1.8
- Max Drawdown: -12%
- Win Rate: 64%
```

---

## 🏆 Bitget AI Hackathon S1

This project was built for the **Bitget AI Hackathon Season 1** (Trading Infra track).

**Team:** [Your Team Name]
**Timeline:** 7 days (June 24-30, 2026)

---

## 🚀 Quick Start

### Option 1: Try the Live Demo (Recommended)
**Deployed on Vercel:** **[https://strategyai.vercel.app](https://strategyai.vercel.app)**

> ⚡ Fast, reliable deployment on Vercel's edge network

### Option 2: Deploy Your Own on Vercel

```bash
# 1. Fork this repo
github.com/Vage1000600/strategyai → Fork

# 2. Go to vercel.com/new
# 3. Import your fork
# 4. Select "Streamlit" preset
# 5. Add environment variables:
#    - DEEPSEEK_API_KEY
#    - BITGET_API_KEY
#    - BITGET_API_SECRET
# 6. Click Deploy!

# Full guide: DEPLOYMENT.md
```

### Option 3: Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/strategyai.git
cd strategyai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 4. Run the app
streamlit run app.py
```

---

## 📦 Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Strategy Generator** | Converts natural language to Python code |
| 📊 **Backtesting Engine** | Runs strategies on historical Bitget data |
| 📈 **Performance Metrics** | PnL, Sharpe, drawdown, win rate, and more |
| 🎨 **Interactive Charts** | Equity curve, drawdown, trade breakdown |
| 💾 **Export Code** | Download your strategy as Python file |
| 📚 **Example Strategies** | Pre-built strategies to learn from |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| AI Model | DeepSeek API |
| Backtesting | Custom Python |
| Data | Bitget API |
| Charts | Plotly |
| Deployment | Streamlit Cloud |

---

## 📖 How It Works

```
┌─────────────────┐
│  User Input     │
│  (English)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Code Gen    │
│  (DeepSeek)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backtester     │
│  (Bitget Data)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Results        │
│  (Charts + UI)  │
└─────────────────┘
```

---

## 📝 Example Strategies

### 1. RSI Strategy
```
Buy when RSI < 30
Sell when RSI > 70
```

### 2. MACD Crossover
```
Buy when MACD crosses above signal line
Sell when MACD crosses below signal line
```

### 3. Moving Average Crossover
```
Buy when 50 EMA crosses above 200 EMA
Sell when 50 EMA crosses below 200 EMA
```

### 4. Breakout Strategy
```
Buy when price breaks above 20-day high
Sell at 10% profit or 5% stop loss
```

### 5. Mean Reversion
```
Buy when price is 2 standard deviations below 20-day MA
Sell when price returns to mean
```

---

## 🏗️ Project Structure

```
strategyai/
├── app.py                  # Streamlit UI
├── ai_generator.py         # AI code generation
├── backtester.py           # Backtesting engine
├── visualization.py        # Charts & metrics
├── bitget_api.py           # Bitget data connector
├── requirements.txt        # Dependencies
├── README.md              # This file
├── examples/              # Example strategies
└── tests/                 # Unit tests
```

---

## 🔑 API Keys Required

| API | Purpose | Get Key |
|-----|---------|---------|
| **DeepSeek** | AI code generation | https://platform.deepseek.com/ |
| **Bitget** | Historical market data | https://www.bitget.com/api |

Add your keys to `.env`:
```
DEEPSEEK_API_KEY=sk-your-key-here
BITGET_API_KEY=your-bitget-key
BITGET_API_SECRET=your-bitget-secret
```

---

## 📊 Performance Metrics

The backtester calculates:

| Metric | Description |
|--------|-------------|
| **Total PnL** | Net profit/loss in USD |
| **Return %** | Percentage return on initial capital |
| **Sharpe Ratio** | Risk-adjusted return |
| **Max Drawdown** | Largest peak-to-trough decline |
| **Win Rate** | Percentage of winning trades |
| **Avg Win/Loss** | Average win vs average loss ratio |
| **Total Trades** | Number of trades executed |
| **Profit Factor** | Gross profit / Gross loss |

---

## 🎥 Demo Video

[Watch the 2-minute demo](https://youtu.be/YOUR_VIDEO_ID)

---

## 🏃 Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_backtester.py
```

---

## 🤝 Contributing

This is a hackathon project, but we welcome improvements!

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - feel free to use this for your own projects!

---

## 👥 Team

| Name | Role | GitHub |
|------|------|--------|
| [Your Name] | AI Integration | @yourhandle |
| [Teammate 2] | Backtesting Engine | @handle2 |
| [Teammate 3] | Visualization | @handle3 |
| [Teammate 4] | UI/UX + Deployment | @handle4 |

---

## 📞 Contact

- **Twitter:** [@YourHandle](https://x.com/YourHandle)
- **Email:** your-email@example.com
- **Discord:** YourDiscord#1234

---

## 🙏 Acknowledgments

- Built for **Bitget AI Hackathon Season 1**
- Powered by **DeepSeek AI** and **Bitget API**
- Inspired by traders who can't code (yet!)

---

*Happy Backtesting! 📈*
