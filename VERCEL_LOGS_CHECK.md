# Vercel Logs Check

## Action Required

Go to Vercel Dashboard and check the function logs:

1. **Go to:** https://vercel.com/vage1/strategyai
2. **Click:** "Logs" tab (in top navigation)
3. **Look for:** Errors from the last 5 minutes
4. **Find:** The backtest error with full traceback

The logs will show:
- Exact line where error occurs
- What variables are defined/undefined
- Full Python traceback

## What to Look For

Search for these patterns in logs:
```
"BACKTEST STARTED"
"PRE-COMPUTING SIGNALS"
"Calling strategy_func"
"data_full type"
"ERROR" or "Exception"
```

## Expected Issue

The error "name 'data' is not defined" suggests:
1. Strategy code has a reference to `data` outside the function
2. OR the exec() sandbox is blocking something
3. OR data dictionary isn't being passed correctly

**Most likely:** The strategy code generated has some top-level code that references `data` before the function is called.

## Quick Fix to Try

In the UI, after generating code:
1. Click "Edit Code"
2. Make sure there's NO code outside the functions
3. Only `def compute_*()` and `def strategy()` functions should exist
4. No top-level `data['close']` references
5. Click "Run Backtest" again
