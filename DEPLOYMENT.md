# 🚀 Deployment Guide - Vercel

## Quick Deploy (5 minutes)

### Option 1: Vercel Dashboard (Recommended - Easiest)

1. **Go to** https://vercel.com/new
2. **Sign in** with GitHub
3. **Import Repository:** Select `Vage1000600/strategyai`
4. **Framework Preset:** Select **"Streamlit"**
5. **Configure Environment Variables:**
   - `DEEPSEEK_API_KEY` → Your DeepSeek API key
   - `BITGET_API_KEY` → Your Bitget API key
   - `BITGET_API_SECRET` → Your Bitget API secret
6. **Click "Deploy"**
7. **Wait 2-3 minutes** for build to complete
8. **Done!** You'll get a URL like: `https://strategyai.vercel.app`

---

### Option 2: Vercel CLI (For Advanced Users)

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Navigate to project
cd strategyai

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

---

## 🔧 Environment Variables Setup

### In Vercel Dashboard:

1. Go to your project: https://vercel.com/dashboard
2. Click on `strategyai`
3. Go to **Settings** → **Environment Variables**
4. Add these 3 variables:

| Name | Value | Environment |
|------|-------|-------------|
| `DEEPSEEK_API_KEY` | `sk-your-deepseek-key` | Production, Preview, Development |
| `BITGET_API_KEY` | `your-bitget-key` | Production, Preview, Development |
| `BITGET_API_SECRET` | `your-bitget-secret` | Production, Preview, Development |

5. Click **Save**

---

## 🧪 Testing After Deployment

### 1. Check Deployment Status
```
https://vercel.com/Vage1000600/strategyai/deployments
```

### 2. Test Live App
```
https://strategyai-[your-username].vercel.app
```

### 3. Test These Features:
- [ ] Load RSI Strategy (one-click button)
- [ ] Run backtest
- [ ] Check results display
- [ ] Download CSV export
- [ ] Check for errors in Vercel Functions logs

---

## 🐛 Troubleshooting

### Issue: "Module not found: streamlit"
**Fix:** Make sure `requirements.txt` is in repo root with all dependencies:
```
streamlit==1.35.0
plotly==5.22.0
openai==1.35.0
pandas==2.2.2
numpy==1.26.4
ccxt==4.3.50
requests==2.32.3
python-dotenv==1.0.1
```

### Issue: "Environment variables not set"
**Fix:** 
1. Go to Vercel Dashboard → Project → Settings → Environment Variables
2. Make sure all 3 variables are set
3. Redeploy: `vercel --prod`

### Issue: "Build failed"
**Fix:**
1. Check build logs: Vercel Dashboard → Deployments → View Build Logs
2. Look for error messages
3. Common fixes:
   - Missing dependencies in `requirements.txt`
   - Python version mismatch (use 3.9)
   - Syntax errors in code

### Issue: "App loads but shows errors"
**Fix:**
1. Check Vercel Functions logs
2. Test API keys locally first
3. Make sure keys have correct permissions

---

## 📊 Vercel Dashboard Features

### Analytics
- View deployment history
- Check build times
- Monitor errors
- View usage metrics

### Preview Deployments
- Every branch gets a preview URL
- Test before merging to main
- Share with team for feedback

### Custom Domain (Optional)
- Go to Settings → Domains
- Add your custom domain
- Free SSL included

---

## 🎯 Post-Deployment Checklist

```
☐ App loads without errors
☐ All 4 strategy buttons work
☐ Backtest completes successfully
☐ Results display correctly
☐ Export buttons work (CSV, JSON, Code)
☐ Strategy history saves
☐ Advanced settings adjustable
☐ No console errors
☐ Mobile responsive
☐ Share URL with team for testing
```

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| **Vercel Dashboard** | https://vercel.com/dashboard |
| **Vercel Docs** | https://vercel.com/docs |
| **Streamlit on Vercel** | https://vercel.com/docs/frameworks/streamlit |
| **Your Project** | https://vercel.com/Vage1000600/strategyai |

---

## 💡 Pro Tips

1. **Use Preview Deployments:** Create a branch for testing, Vercel auto-deploys
2. **Enable Analytics:** Free usage analytics in Vercel dashboard
3. **Set Up Alerts:** Get notified on deployment failures
4. **Use Custom Domain:** Makes it look more professional for hackathon
5. **Keep `.env` out of repo:** Never commit API keys!

---

**Good luck with deployment! 🚀**

Questions? Check Vercel docs or reach out to the team.
