# Bitget AI Hackathon S1 - Project Specification

## 🏆 Project Name: **StrategyAI**

**Tagline:** "Describe Your Trading Strategy in English. We'll Code It, Backtest It, Optimize It."

**Track:** Trading Infra (less competition, higher chances)

**Team:** [Your Team Name - 4 people]

**Timeline:** 7 days (June 24-30, 2026)

---

## 🎯 Problem Statement

**The Pain:**
- 90% of traders have strategies in their head but can't code them
- Hiring a developer costs $500-5000+
- Learning to code takes months
- Existing backtesting tools require programming knowledge

**The Solution:**
- User describes strategy in natural language
- AI converts it to executable code
- Automatic backtesting on historical data
- Results with PnL, Sharpe, drawdown metrics
- Optimization suggestions

---

## 📦 Features (MVP - 7 Days)

### Core Features (Must Have)
| Feature | Description | Priority |
|---------|-------------|----------|
| **Natural Language Input** | User types strategy in English | 🔴 P0 |
| **AI Code Generation** | LLM converts to Python/JS code | 🔴 P0 |
| **Backtesting Engine** | Runs strategy on historical data | 🔴 P0 |
| **Results Dashboard** | Shows PnL, metrics, equity curve | 🔴 P0 |
| **Export Strategy** | Download code for personal use | 🟠 P1 |

### Nice-to-Have (If Time)
| Feature | Description | Priority |
|---------|-------------|----------|
| **Strategy Library** | Pre-built strategies to copy | 🟡 P2 |
| **Optimization Suggestions** | AI suggests parameter tweaks | 🟡 P2 |
| **Multi-Asset Testing** | Test on BTC, ETH, SOL, etc. | 🟡 P2 |
| **Share/Publish** | Share strategies with community | 🟡 P2 |

---

## 👥 Team Roles (4 People)

### Person 1: **AI Integration Lead**
**Responsibilities:**
- DeepSeek/OpenAI API integration
- Prompt engineering for strategy → code
- Code validation (ensure generated code is safe)
- Error handling for invalid strategies

**Deliverables:**
- `ai-strategy-generator.py` module
- Prompt templates for different strategy types
- Code sanitization layer

**Time Estimate:** 2-3 days

---

### Person 2: **Backtesting Engine Lead**
**Responsibilities:**
- Historical data fetching (Bitget API)
- Backtesting logic (entry/exit signals)
- Performance metrics calculation
- Position sizing, fees, slippage modeling

**Deliverables:**
- `backtester.py` module
- Bitget historical data connector
- Metrics: PnL, Sharpe, max drawdown, win rate

**Time Estimate:** 3 days

---

### Person 3: **Results & Visualization Lead**
**Responsibilities:**
- Equity curve chart
- Trade-by-trade breakdown
- Drawdown visualization
- Performance summary table

**Deliverables:**
- `visualization.py` module
- Interactive charts (Plotly/Streamlit)
- Export to PNG/PDF

**Time Estimate:** 2 days

---

### Person 4: **UI/UX + Integration Lead**
**Responsibilities:**
- Frontend (Streamlit or simple React)
- User input form
- Results dashboard layout
- Final integration + deployment

**Deliverables:**
- `app.py` (Streamlit app)
- Deployed demo URL (Streamlit Cloud / Vercel)
- README + demo video

**Time Estimate:** 2-3 days

---

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| **Frontend** | Streamlit | Fast, Python-native, easy deploy |
| **AI Model** | DeepSeek API | Cheap, fast, good for code gen |
| **Backtesting** | Custom Python | Full control, Bitget-specific |
| **Data** | Bitget API | Official, free, historical data |
| **Charts** | Plotly | Interactive, beautiful |
| **Deployment** | Streamlit Cloud | Free, 1-click deploy |
| **Version Control** | GitHub | Required for submission |

---

## 📅 7-Day Sprint Plan

### **Day 1 (June 24): Setup & Foundation**
| Task | Owner | Status |
|------|-------|--------|
| Create GitHub repo | Person 4 | ☐ |
| Set up project structure | All | ☐ |
| Bitget API key setup | Person 2 | ☐ |
| DeepSeek API key setup | Person 1 | ☐ |
| Hello World: Simple strategy hard-coded | Person 2 | ☐ |

### **Day 2 (June 25): AI Code Generation**
| Task | Owner | Status |
|------|-------|--------|
| Design prompt templates | Person 1 | ☐ |
| Test strategy → code conversion | Person 1 | ☐ |
| Code sanitization layer | Person 1 | ☐ |
| Handle edge cases (invalid input) | Person 1 | ☐ |

### **Day 3 (June 26): Backtesting Engine**
| Task | Owner | Status |
|------|-------|--------|
| Fetch historical data from Bitget | Person 2 | ☐ |
| Implement signal generation | Person 2 | ☐ |
| Calculate PnL, fees, slippage | Person 2 | ☐ |
| Test with known strategies | Person 2 | ☐ |

### **Day 4 (June 27): Metrics & Visualization**
| Task | Owner | Status |
|------|-------|--------|
| Calculate metrics (Sharpe, drawdown, etc.) | Person 2 | ☐ |
| Build equity curve chart | Person 3 | ☐ |
| Build drawdown chart | Person 3 | ☐ |
| Trade breakdown table | Person 3 | ☐ |

### **Day 5 (June 28): UI Development**
| Task | Owner | Status |
|------|-------|--------|
| Build Streamlit input form | Person 4 | ☐ |
| Connect AI module to UI | Person 1+4 | ☐ |
| Connect backtester to UI | Person 2+4 | ☐ |
| Display results in UI | Person 3+4 | ☐ |

### **Day 6 (June 29): Polish & Testing**
| Task | Owner | Status |
|------|-------|--------|
| End-to-end testing | All | ☐ |
| Fix bugs | All | ☐ |
| Improve error messages | Person 1 | ☐ |
| Add example strategies | Person 4 | ☐ |

### **Day 7 (June 30): Submission**
| Task | Owner | Status |
|------|-------|--------|
| Record demo video (2-3 min) | Person 4 | ☐ |
| Write README | Person 4 | ☐ |
| Fill submission form | Person 4 | ☐ |
| Post on X (tag @Bitget_AI) | Person 4 | ☐ |
| **DEADLINE: June 30, 11:59 PM UTC** | All | ☐ |

---

## 📊 Example User Flow

```
1. User visits: strategyai.streamlit.app
2. User types: "Buy when RSI < 30, sell when RSI > 70"
3. AI converts to Python code:
   ```python
   if rsi < 30:
       buy()
   elif rsi > 70:
       sell()
   ```
4. User selects: BTC/USDT, 1h timeframe, $1000 initial
5. Backtest runs (5 seconds)
6. Results shown:
   - PnL: +$347 (34.7%)
   - Sharpe: 1.8
   - Max Drawdown: -12%
   - Win Rate: 64%
7. User can: Download code, tweak parameters, test another strategy
```

---

## 🎯 Winning Criteria (How Judges Score)

| Criteria | Weight | How We Win |
|----------|--------|------------|
| **AI Integration** | 30% | DeepSeek-powered code generation |
| **Bitget Integration** | 25% | Official API, real historical data |
| **Technical Depth** | 20% | Full backtesting engine, not just UI |
| **Demo Quality** | 15% | Live demo, working end-to-end |
| **Innovation** | 10% | Natural language → strategy is unique |

---

## 💰 Post-Hackathon Potential

This isn't just a hackathon project — it can become a real business:

| Monetization | Potential |
|--------------|-----------|
| **Freemium SaaS** | Free: 5 backtests/month, Pro: $29/month unlimited |
| **Strategy Marketplace** | Users sell strategies, we take 20% cut |
| **API Access** | Charge developers per API call |
| **White Label** | Sell to trading platforms |

**Estimated MRR (6 months post-launch):** $5K-15K/month

---

## 📁 Project Structure

```
strategyai/
├── app.py                      # Streamlit UI (Person 4)
├── ai_generator.py             # AI code generation (Person 1)
├── backtester.py               # Backtesting engine (Person 2)
├── visualization.py            # Charts & metrics (Person 3)
├── bitget_api.py               # Bitget data connector (Person 2)
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── examples/
│   ├── rsi_strategy.txt        # Example: RSI strategy
│   ├── macd_strategy.txt       # Example: MACD strategy
│   └── breakout_strategy.txt   # Example: Breakout strategy
└── tests/
    ├── test_ai_generator.py
    ├── test_backtester.py
    └── test_integration.py
```

---

## 🚀 Getting Started (Day 1 Checklist)

```bash
# 1. Create GitHub Repo
- Go to github.com/new
- Repo name: strategyai
- Description: "AI-Powered Trading Strategy Backtester for Bitget"
- Public repo ✅

# 2. Clone & Setup
git clone https://github.com/YOUR_USERNAME/strategyai.git
cd strategyai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install Dependencies
pip install streamlit openai pandas plotly ccxt requests

# 4. Create .env file
DEEPSEEK_API_KEY=sk-your-key-here
BITGET_API_KEY=your-bitget-key
BITGET_API_SECRET=your-bitget-secret

# 5. Create basic app.py
import streamlit as st
st.title("StrategyAI - Backtest Trading Strategies with AI")
st.write("Describe your strategy in natural language...")

# 6. Test locally
streamlit run app.py

# 7. Push to GitHub
git add .
git commit -m "Initial commit"
git push origin main
```

---

## 📝 Submission Checklist (June 30)

```
☐ Working demo URL (Streamlit Cloud)
☐ GitHub repo with clean code + README
☐ 2-3 minute demo video (Loom/YouTube)
☐ Post on X tagging @Bitget_AI (for $50 guaranteed)
☐ Submission form filled (all team members)
☐ Team wallet addresses (for prize distribution)
```

---

## 💡 Example Strategies to Test

1. **RSI Strategy:** "Buy when RSI < 30, sell when RSI > 70"
2. **MACD Strategy:** "Buy when MACD crosses above signal, sell when it crosses below"
3. **Moving Average Crossover:** "Buy when 50 EMA crosses above 200 EMA, sell on reverse"
4. **Breakout Strategy:** "Buy when price breaks above 20-day high, sell at 10% profit"
5. **Mean Reversion:** "Buy when price is 2 std dev below 20-day MA, sell at mean"

---

## 🎯 Success Metrics

| Metric | Target |
|--------|--------|
| **Hackathon Result** | Top 3 in Trading Infra track |
| **Demo Quality** | Working end-to-end, no bugs |
| **AI Accuracy** | 80%+ strategies generate valid code |
| **Backtest Speed** | <10 seconds per strategy |
| **User Experience** | 3 clicks from input to results |

---

## 📞 Team Communication

| Tool | Purpose |
|------|---------|
| **Discord/Telegram** | Daily sync, quick questions |
| **GitHub Issues** | Task tracking, bugs |
| **Google Doc** | Shared notes, decisions |
| **Loom** | Async demos, walkthroughs |

**Daily Standup (15 min):**
- What did I do yesterday?
- What will I do today?
- Any blockers?

---

*Good luck, team! Let's build something amazing! 🚀*
