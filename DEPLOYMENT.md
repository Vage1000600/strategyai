# Deployment Guide

## Deploy to Vercel (Recommended)

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Vage1000600/strategyai)

### Manual Deployment

1. **Go to Vercel:** https://vercel.com/dashboard
2. **Click "Add New Project"**
3. **Import your GitHub repo:** `Vage1000600/strategyai`
4. **Configure:**
   - Framework Preset: `Python`
   - Root Directory: `./`
   - **No environment variables required!** (uses public API by default)
5. **Click "Deploy"**

### Environment Variables (Optional)

Add these in Vercel Dashboard → Settings → Environment Variables:

| Name | Required? | Default | Purpose |
|------|-----------|---------|---------|
| `BITGET_API_KEY` | ❌ No | Empty | Your Bitget API key (uses public API if empty) |
| `BITGET_API_SECRET` | ❌ No | Empty | Your Bitget API secret |
| `DEEPSEEK_API_KEY` | ❌ No | Empty | DeepSeek API key for better AI (uses local AI if empty) |

**App works with all variables empty!** ✅

### Auto-Deploy

Vercel automatically deploys on every push to `main` branch.

---

## Run Locally

### Prerequisites

- Python 3.9+
- pip

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Vage1000600/strategyai.git
cd strategyai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
uvicorn main:app --reload

# 4. Open browser
# http://localhost:8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Get Bitget API Key (Optional)

1. Go to https://www.bitget.com/
2. Sign up / Log in
3. Profile → API Management
4. Create new API key
5. Enable **"Read-only"** permissions
6. Copy key and secret
7. Add to Vercel environment variables or local `.env` file

---

## Get DeepSeek API Key (Optional)

1. Go to https://platform.deepseek.com/
2. Sign up / Log in
3. Get API key
4. Add to environment variables

**Benefits:** Better code generation for complex strategies

**Default:** Local AI reasoning (no API key needed)

---

## Troubleshooting

### Deployment Fails

**Check Vercel build logs** for errors. Common issues:

- Missing dependencies → Update `requirements.txt`
- Python version mismatch → Vercel auto-detects Python 3.9+
- Import errors → Check file paths in `main.py`

### App Returns Errors

**Public API rate-limited?**
- Add your Bitget API key in settings

**Strategy code error?**
- Rephrase strategy in simpler terms
- Use supported indicators: RSI, MACD, EMA, SMA, BB, ATR

### Local Development

**Port already in use?**
```bash
uvicorn main:app --reload --port 8001
```

**Missing dependencies?**
```bash
pip install -r requirements.txt --upgrade
```

---

## Custom Domain

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your domain
3. Configure DNS records as instructed
4. Wait for SSL certificate (automatic)

---

## Performance Tips

- **Cold starts:** Vercel serverless functions have ~1-2s cold start
- **Optimize:** Keep backtest limit reasonable (500 candles default)
- **Cache:** Consider adding Redis for frequently-used strategies (Pro tier)

---

## Support

- **GitHub Issues:** https://github.com/Vage1000600/strategyai/issues
- **Hackathon Forum:** https://www.bitget.com/activity-hub/hackathon
- **Documentation:** https://github.com/Vage1000600/strategyai/wiki

---

*Built for Bitget AI Hackathon S1*
