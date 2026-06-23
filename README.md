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

### Two Modes:

**🆓 Local Mode (Default):**
- No API keys needed
- 100% free
- Fast processing
- Good for standard strategies

**🤖 DeepSeek Mode (Optional):**
- Requires DeepSeek API key
- Better code quality
- Handles complex strategies
- Still free tier available

---

## 🔥 Key Features

| Feature | Local Mode | DeepSeek Mode |
|---------|------------|---------------|
| **API Key Required** | ❌ No | ✅ Yes (DeepSeek) |
| **Cost** | Free | Free tier available |
| **Speed** | ⚡ Fast | 🐌 Slower (API call) |
| **Code Quality** | Good | Excellent |
| **Complex Strategies** | Limited | Unlimited |
| **Offline** | ✅ Yes | ❌ No |

---

## 🚀 Quick Start

### Option 1: Try Live Demo
**Deployed on Vercel:** **[https://strategyai.vercel.app](https://strategyai.vercel.app)**

> ⚡ Fast deployment. Local mode works without API keys!

### Option 2: Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/Vage1000600/strategyai.git
cd strategyai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Open: http://localhost:8501

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

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| AI Engine | Local parser OR DeepSeek API |
| Backtesting | Custom Python |
| Data | Bitget API (via CCXT) |
| Charts | Plotly |
| Deployment | Vercel |

---

## 🔑 API Requirements

| API | Required? | Purpose |
|-----|-----------|---------|
| **Bitget API** | ✅ Yes | Historical market data |
| **DeepSeek API** | ❌ Optional | Better AI code generation |

### Get Bitget API Key (Free, Read-Only):

1. Go to https://www.bitget.com/
2. Sign up / Log in
3. Profile → API Management
4. Create new API key
5. Enable **"Read-only"** permissions
6. Copy key and secret

### Get DeepSeek API Key (Optional):

1. Go to https://platform.deepseek.com/
2. Sign up / Log in
3. Get API key
4. Add to environment variables

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
├── api/
│   └── index.py          # Vercel serverless wrapper
├── app.py                # Main Streamlit UI
├── ai_generator.py       # Hybrid AI (Local + DeepSeek)
├── backtester.py         # Backtesting engine
├── visualization.py      # Charts & metrics
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

### Deploy to Vercel (5 minutes):

1. Fork this repo
2. Go to https://vercel.com/new
3. Import your fork
4. Select "Streamlit" preset
5. Add environment variables:
   - `BITGET_API_KEY` (Required)
   - `BITGET_API_SECRET` (Required)
   - `DEEPSEEK_API_KEY` (Optional - for better AI)
6. Deploy!

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
| **Bitget API** | https://www.bitget.com/api |
| **DeepSeek API** | https://platform.deepseek.com/ |
| **Hackathon** | https://www.bitget.com/activity-hub/hackathon |

---

*Happy Backtesting! 📈*

**Local mode: No API keys. DeepSeek mode: Optional upgrade.** 🚀
