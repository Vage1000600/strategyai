# 🚀 StrategyAI - Quick Start Guide

**For the Team:** Follow these steps to get started in 15 minutes.

---

## ⚡ Day 1 Setup (Do This First!)

### Step 1: Create GitHub Repo (5 min)

1. Go to https://github.com/new
2. Repo name: `strategyai`
3. Description: "AI-Powered Trading Strategy Backtester for Bitget AI Hackathon"
4. Public repo ✅
5. Click "Create repository"

### Step 2: Clone & Setup (5 min)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/strategyai.git
cd strategyai

# Create virtual environment
python -m venv venv

# Activate venv
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Get API Keys (5 min)

**DeepSeek API Key:**
1. Go to https://platform.deepseek.com/
2. Sign up / Log in
3. Go to API Keys section
4. Create new key
5. Copy the key

**Bitget API Key:**
1. Go to https://www.bitget.com/
2. Sign up / Log in
3. Go to Profile → API Management
4. Create new API key
5. Enable "Read-only" permissions (no trading needed)
6. Copy key and secret

### Step 4: Configure Environment

```bash
# Copy env template
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor

# Paste your API keys:
DEEPSEEK_API_KEY=sk-your-actual-key
BITGET_API_KEY=your-actual-key
BITGET_API_SECRET=your-actual-secret
```

### Step 5: Test Run

```bash
# Run the app
streamlit run app.py
```

Open http://localhost:8501 in your browser.

If you see the StrategyAI interface → ✅ Setup complete!

---

## 👥 Team Task Assignment

Share this with your team and assign roles:

| Person | Role | Files to Work On | Day 1 Task |
|--------|------|------------------|------------|
| **Person 1** | AI Integration Lead | `ai_generator.py` | Test AI code generation with 5 example strategies |
| **Person 2** | Backtesting Lead | `backtester.py`, `bitget_api.py` | Test data fetching + backtest with hard-coded strategy |
| **Person 3** | Visualization Lead | `visualization.py` | Create all 4 chart types, test with sample data |
| **Person 4** | UI/UX Lead | `app.py`, `README.md` | Integrate all modules, deploy to Streamlit Cloud |

---

## 📅 Daily Checkpoints

### Day 1 (Today)
- [ ] GitHub repo created
- [ ] All team members can run locally
- [ ] API keys configured
- [ ] Hello World: Hard-coded strategy works end-to-end

### Day 2
- [ ] AI code generation working (Person 1)
- [ ] Backtester fetching Bitget data (Person 2)
- [ ] Basic charts rendering (Person 3)
- [ ] UI skeleton ready (Person 4)

### Day 3
- [ ] AI → Backtester integration working
- [ ] All indicators implemented (RSI, MACD, EMA, etc.)
- [ ] Equity curve + drawdown charts done
- [ ] Deployed to Streamlit Cloud (test URL)

### Day 4
- [ ] All features working
- [ ] Bug fixes
- [ ] Example strategies added
- [ ] Demo video recorded

### Day 5
- [ ] Polish UI
- [ ] Write README
- [ ] Test with 10+ different strategies
- [ ] Fix edge cases

### Day 6
- [ ] Final testing
- [ ] Prepare submission
- [ ] Create demo video (2-3 min)
- [ ] Write X/Twitter post

### Day 7 (June 30 - DEADLINE)
- [ ] Submit before 11:59 PM UTC
- [ ] Post on X tagging @Bitget_AI
- [ ] Celebrate! 🎉

---

## 🐛 Common Issues & Fixes

### Issue: "Module not found: streamlit"
**Fix:** Make sure virtual environment is activated:
```bash
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows
```

### Issue: "DeepSeek API key invalid"
**Fix:** Check your key in `.env` file, make sure no extra spaces

### Issue: "Bitget API rate limit"
**Fix:** Wait 1 minute between requests, or reduce `limit` parameter

### Issue: "Strategy code execution failed"
**Fix:** Check AI-generated code has correct function signature: `def strategy(data):`

---

## 📞 Team Communication

**Daily Standup (15 min):**
- What did I do yesterday?
- What will I do today?
- Any blockers?

**Tools:**
- Discord/Telegram: Quick questions
- GitHub Issues: Bug tracking
- Google Doc: Shared notes

---

## 🎯 Success Checklist

By end of Day 3, you should have:
- [ ] Working local setup for all team members
- [ ] AI generating valid code from English
- [ ] Backtester running on Bitget data
- [ ] Charts displaying results
- [ ] Deployed test URL

By end of Day 7, you should have:
- [ ] Polished demo
- [ ] Demo video (2-3 min)
- [ ] README with screenshots
- [ ] Submission form filled
- [ ] X post with @Bitget_AI tag

---

**Let's build something amazing! 🚀**

Questions? Reach out to your team leads or post in the hackathon Discord!
