# 🚀 Deploy Instructions - Groq Embedded Key Setup

## What Changed

**"Local AI" now = Groq with YOUR embedded API key**

- Users select "Local AI" → uses Groq (Llama-3.3-70B)
- **Your Groq key covers ALL users** - they don't need their own
- Free tier: 30 requests/min, 14,400 requests/day
- DeepSeek/Claude remain as optional upgrades (users provide their own keys)

---

## Step 1: Get Your Groq API Key

1. Go to: https://console.groq.com/keys
2. Sign up / log in
3. Create a new API key
4. Copy the key (starts with `gsk_...`)

---

## Step 2: Add Key to Your Local Repo

**Option A: Environment Variable (Recommended for Vercel)**

Create `.env` file in strategyai root:
```bash
GROQ_API_KEY=gsk_your_actual_key_here
```

**Option B: Hardcode in ai_generator.py**

Edit line 13 in `ai_generator.py`:
```python
GROQ_API_KEY = "gsk_your_actual_key_here"  # Replace with your key
```

---

## Step 3: Push to GitHub

```bash
cd /path/to/your/local/strategyai
git pull origin main
git push origin main
```

---

## Step 4: Deploy to Vercel

**Option A: Vercel Dashboard**
1. Go to https://vercel.com
2. Select your StrategyAI project
3. Click "Deploy" (it will auto-detect changes)

**Option B: CLI**
```bash
cd /path/to/your/local/strategyai
vercel --prod
```

---

## Step 5: Add Environment Variable to Vercel

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add new variable:
   - **Name:** `GROQ_API_KEY`
   - **Value:** `gsk_your_actual_key_here`
   - **Environment:** Production ✅
3. Save and redeploy

---

## Step 6: Test It

1. Go to your live site: https://strategyai-mu.vercel.app
2. Select "🚀 Local AI (Groq 70B - Free & Fast)" (default)
3. Enter a strategy: "Buy when RSI < 30, sell when RSI > 70"
4. Click "Generate Code"
5. Should return AI-generated code (not template)

---

## Monitoring Usage

Check your Groq usage at: https://console.groq.com/usage

**Free Tier Limits:**
- 30 requests per minute
- 14,400 requests per day

If you hit limits, users can still use:
- DeepSeek (they provide key)
- Claude (they provide key)

---

## Troubleshooting

**"Groq API key not configured" error:**
- Make sure `GROQ_API_KEY` is set in Vercel environment variables
- Or hardcode it in `ai_generator.py` line 13

**Backtester still returning zeros:**
- Check browser console for debug logs
- Look for "🔍 BACKTEST STARTED" and "📊 Candle X: buy=X, sell=X"
- If no buy signals, the strategy code might not be generating signals

**Rate limit errors:**
- You've hit 30 req/min or 14,400/day
- Wait for limits to reset
- Consider upgrading Groq plan

---

## What Users See Now

**Before:**
```
🤖 AI Provider
├─ Local Templates (Free, Instant)     ← Just templates, no AI
├─ DeepSeek (Advanced, ~$0.01)
└─ Claude (Best Quality, ~$0.03)
```

**After:**
```
🤖 AI Provider
├─ 🚀 Local AI (Groq 70B - Free & Fast)  ← YOUR Groq key, FREE for users
├─ DeepSeek (Advanced, ~$0.01)
└─ Claude (Best Quality, ~$0.03)
```

Users get AI-powered code generation for free, no setup needed! 🎉
