# StrategyAI UI Redesign Plan

## Current Issues
- Single long page with everything crammed together
- Settings mixed with strategy input
- Poor visual hierarchy
- No clear separation of concerns

## New Structure

### Navigation Tabs
1. **🏠 Home** - Landing with quick start
2. **📊 Backtest** - Main backtesting interface
3. **⚙️ Settings** - API keys, preferences, advanced settings
4. **📈 Results** - View past backtest results
5. **❓ Help** - Documentation & guides

### Layout Changes
- Tab-based navigation at top
- Each section focused on single purpose
- Settings moved to dedicated page
- Cleaner visual hierarchy
- Keep existing theme (dark mode, amber accent, glass panels)

### File Structure
Keep HTML embedded in Python (for Vercel serverless), but:
- Split into cleaner sections
- Add tab navigation
- Better CSS organization
- Modular JavaScript functions
