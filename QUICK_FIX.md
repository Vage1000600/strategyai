# Quick Fix for Validation Retry

## Problem
The `/backtest/generate` endpoint returns validation errors directly without retrying. The retry loop I added is in the wrong endpoint (`/backtest`).

## Solution
Replace lines 112-124 in api/index.py with this retry loop:

```python
# RETRY LOOP: Generate → Validate → Retry on error
max_retries = 3
validation = None

for attempt in range(max_retries):
    validation = validate_and_fix(generated['code'])
    
    if validation['valid']:
        print(f"[SUCCESS] Code validated on attempt {attempt + 1}")
        break
    
    print(f"[RETRY {attempt + 1}/{max_retries}] Validation failed: {validation['errors']}")
    
    # Prepare fix prompt for next iteration
    if attempt < max_retries - 1:
        fix_prompt = f"Fix these errors: {', '.join(validation['errors'])}. Use ONLY numpy (np.diff, np.convolve), NOT pandas (.diff, .rolling). Must have 'def strategy(data):' and 'return buy_signals, sell_signals'."
        generated = generate_strategy_code(fix_prompt, provider=ai_provider, api_keys=api_keys)
        if 'error' in generated:
            break

# If all retries failed
if not validation['valid']:
    return JSONResponse({
        'success': False,
        'error': f"Validation failed after {max_retries} attempts: {', '.join(validation['errors'])}",
        'validation_errors': validation['errors']
    })
```

## Manual Fix (if needed)
1. Open api/index.py
2. Find line 112 (the validation section)
3. Replace with the retry loop above
4. Commit and push

## Alternative: Use Local Templates
Until the retry loop is fixed, users can select "Local Templates" from the AI Provider dropdown. This uses pre-built, validated strategy templates that always work!
