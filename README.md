# StrategyAI 🚀

## AI-Powered Trading Strategy Backtester for Bitget

**Describe your trading strategy in English. We'll code it, backtest it, and show you the results.**

![Bitget AI Hackathon](https://img.shields.io/badge/Bitget%20AI%20Hackathon-S1-blue)
![Track](https://img.shields.io/badge/Track-Trading%20Infra-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black?logo=vercel)
![No Setup](https://img.shields.io/badge/No%20Setup%20Required-green)

---

## 🎯 What Is This?

StrategyAI lets you **backtest trading strategies without writing code**. Just describe your strategy in natural language, and our AI converts it to executable code, runs it on historical Bitget data, and shows you the results.

### ✨ No Setup Required!

**Works instantly** with public Bitget API (no API key needed for testing).

Want unlimited access? Add your free Bitget API key in the settings.

---

## 🚀 Quick Start

### Option 1: Try Live Demo (No Setup!)
**Deployed on Vercel:** **[https://strategyai.vercel.app](https://strategyai.vercel.app)**

> ⚡ Just open and start testing! No API keys required.

### Option 2: Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/Vage1000600/strategyai.git
cd strategyai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
uvicorn main:app --reload
```

Open: http://localhost:8000

---

## 🎨 Key Features

| Feature | Description |
|---------|-------------|
| 🆓 **No API Key Required** | Works with public Bitget API instantly |
| 🤖 **Hybrid AI** | Local reasoning (default) + DeepSeek (optional) |
| 📊 **Backtesting** | Test on historical Bitget data |
| 📈 **Visual Charts** | Interactive equity curve & drawdown charts |
| 📉 **Risk Metrics** | Sharpe, drawdown, win rate, profit factor |
| 💾 **Export** | Download CSV, JSON, or Python code |
| ⚡ **Fast** | Results in 5-10 seconds |
| 🔑 **Optional API Key** | Add your own Bitget key for unlimited access |

---

## 📖 Example Strategies

### 1. RSI Strategy
```
Input: "Buy when RSI < 30, sell when RSI > 70"
```

### 2. MACD Crossover
```
Input: "Buy when MACD crosses above signal, sell when it crosses below"
```

### 3. Golden Cross
```
Input: "Buy when 50 EMA crosses above 200 EMA, sell on death cross"
```

### 4. Bollinger Breakout
```
Input: "Buy when price breaks above upper Bollinger Band, sell at middle"
```

### 5. Custom Strategy
```
Input: Describe your own strategy in plain English!
```

---

## 🔑 API Configuration

### Public API (Default)
- ✅ No setup required
- ✅ Works instantly
- ⚠️ Rate-limited
- ✅ Perfect for testing

### Personal API Key (Optional)
- ✅ Unlimited access
- ✅ No rate limits
- ✅ Free to get
- ✅ Read-only permissions

**Get your free Bitget API key:**
1. Go to https://www.bitget.com/
2. Sign up / Log in
3. Profile → API Management
4. Create new API key
5. Enable **"Read-only"** permissions
6. Enter key in app settings

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | FastAPI + Tailwind CSS + Plotly.js |
| AI Engine | Local parser + DeepSeek (optional) |
| Backtesting | Custom Python |
| Data | Bitget API (public or personal) |
| Charts | Plotly.js |
| Deployment | Vercel (serverless) |

---

## 📊 Performance Metrics

The backtester calculates:

| Metric | Description |
|--------|-------------|
| **Total PnL** | Net profit/loss in USDT |
| **Return %** | Percentage return |
| **Sharpe Ratio** | Risk-adjusted return |
| **Max Drawdown** | Largest peak-to-trough decline |
| **Win Rate** | Percentage of winning trades |
| **Profit Factor** | Gross profit / Gross loss |
| **Avg Win/Loss** | Average win vs loss ratio |
| **Beat HODL** | Performance vs buy & hold |

---

## 🏗️ Project Structure

```
strategyai/
├── main.py               # FastAPI web application
├── templates/
│   └── index.html        # Web UI (Tailwind CSS)
├── ai_generator.py       # Hybrid AI (Local + DeepSeek)
├── backtester.py         # Backtesting engine
├── visualization.py      # Chart generation
├── requirements.txt      # Dependencies
├── vercel.json          # Vercel config
├── README.md            # This file
└── DEPLOYMENT.md        # Deployment guide
```

---

## 🎯 Bitget AI Hackathon S1

This project was built for the **Bitget AI Hackathon Season 1** (Trading Infra track).

**Team:** StrategyAI Team
**Timeline:** 7 days (June 24-30, 2026)
**Status:** ✅ Production Ready

---

## 🚀 Deploy Your Own

### Deploy to Vercel (3 minutes):

1. Fork this repo
2. Go to https://vercel.com/new
3. Import your fork
4. Deploy! (No environment variables required)

**Optional:** Add environment variables for better performance:
- `BITGET_API_KEY` - Your personal Bitget API key
- `BITGET_API_SECRET` - Your Bitget API secret
- `DEEPSEEK_API_KEY` - DeepSeek API key for better AI

**Full guide:** [DEPLOYMENT.md](DEPLOYMENT.md)

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

Built with ❤️ for the Bitget AI Hackathon S1

**Inspired by:** AgentFlow Infra local reasoning architecture

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| **Live Demo** | https://strategyai.vercel.app |
| **GitHub** | https://github.com/Vage1000600/strategyai |
| **Get Bitget API** | https://www.bitget.com/api |
| **Get DeepSeek API** | https://platform.deepseek.com/ |
| **Hackathon** | https://www.bitget.com/activity-hub/hackathon |

---

*Happy Backtesting! 📈*

**No API keys. No BS. Just backtest.** 🚀
