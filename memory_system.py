"""
StrategyAI - Learning Loop & Memory System
Adapted from omnilearn-agent framework

Features:
- Stores backtest results in memory
- Learns from successful/failed strategies
- Tracks performance over time
- Provides insights for improvement
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np


class StrategyMemory:
    """Manages strategy learning and memory"""
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = memory_dir
        self.memory_file = os.path.join(memory_dir, "strategy-memory.json")
        self.performance_file = os.path.join(memory_dir, "performance-state.json")
        
        # Ensure directory exists (skip on Vercel/read-only filesystem)
        try:
            os.makedirs(memory_dir, exist_ok=True)
        except (OSError, IOError, PermissionError):
            # Read-only filesystem - will work in-memory only
            pass
        
        # Load existing memory
        self.memory = self._load_memory()
        self.performance = self._load_performance()
    
    def _load_memory(self) -> Dict:
        """Load strategy memory from file"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {
            'strategies': [],
            'patterns': {},
            'lessons': []
        }
    
    def _load_performance(self) -> Dict:
        """Load performance tracking data"""
        if os.path.exists(self.performance_file):
            with open(self.performance_file, 'r') as f:
                return json.load(f)
        return {
            'total_backtests': 0,
            'profitable_strategies': 0,
            'losing_strategies': 0,
            'avg_return': 0.0,
            'avg_sharpe': 0.0,
            'best_strategy': None,
            'worst_strategy': None,
            'history': []
        }
    
    def store_backtest_result(self, strategy_input: str, results: Dict, code: str):
        """
        Store backtest result in memory for future learning
        
        Args:
            strategy_input: Original natural language description
            results: Backtest metrics and charts
            code: Generated strategy code
        """
        # Create memory entry
        entry = {
            'timestamp': datetime.now().isoformat(),
            'strategy_input': strategy_input,
            'code': code,
            'metrics': {
                'pnl': results.get('pnl', 0),
                'return_pct': results.get('return_pct', 0),
                'sharpe': results.get('sharpe', 0),
                'max_drawdown': results.get('max_drawdown', 0),
                'win_rate': results.get('win_rate', 0),
                'total_trades': results.get('total_trades', 0),
                'benchmark_return': results.get('benchmark_return', 0),
                'outperformance': results.get('outperformance', 0),
            },
            'symbol': results.get('symbol', 'Unknown'),
            'timeframe': results.get('timeframe', 'Unknown'),
            'success': results.get('return_pct', 0) > 0,
            'grade': self._grade_strategy(results)
        }
        
        # Add to strategies list
        self.memory['strategies'].append(entry)
        
        # Update performance tracking
        self._update_performance(entry)
        
        # Extract patterns
        self._extract_patterns(entry)
        
        # Generate lessons
        self._generate_lesson(entry)
        
        # Save to disk
        self._save_memory()
        self._save_performance()
    
    def _grade_strategy(self, results: Dict) -> str:
        """Grade strategy performance (A+ to F)"""
        return_pct = results.get('return_pct', 0)
        sharpe = results.get('sharpe', 0)
        max_dd = results.get('max_drawdown', 0)
        win_rate = results.get('win_rate', 0)
        
        # Simple grading rubric
        score = 0
        score += min(return_pct / 10, 4)  # Up to 4 points for return
        score += min(sharpe / 2, 3)  # Up to 3 points for Sharpe
        score += max(0, (10 - max_dd) / 10 * 2)  # Up to 2 points for low drawdown
        score += win_rate / 100 * 1  # Up to 1 point for win rate
        
        if score >= 9:
            return 'A+'
        elif score >= 8:
            return 'A'
        elif score >= 7:
            return 'B'
        elif score >= 6:
            return 'C'
        elif score >= 5:
            return 'D'
        else:
            return 'F'
    
    def _update_performance(self, entry: Dict):
        """Update overall performance metrics"""
        perf = self.performance
        metrics = entry['metrics']
        
        # Update counters
        perf['total_backtests'] += 1
        if entry['success']:
            perf['profitable_strategies'] += 1
        else:
            perf['losing_strategies'] += 1
        
        # Update averages (running average)
        n = perf['total_backtests']
        perf['avg_return'] = ((n - 1) * perf['avg_return'] + metrics['return_pct']) / n
        perf['avg_sharpe'] = ((n - 1) * perf['avg_sharpe'] + metrics['sharpe']) / n
        
        # Track best/worst
        if perf['best_strategy'] is None or metrics['return_pct'] > perf['best_strategy']['return_pct']:
            perf['best_strategy'] = {
                'return_pct': metrics['return_pct'],
                'strategy_input': entry['strategy_input'],
                'timestamp': entry['timestamp']
            }
        
        if perf['worst_strategy'] is None or metrics['return_pct'] < perf['worst_strategy']['return_pct']:
            perf['worst_strategy'] = {
                'return_pct': metrics['return_pct'],
                'strategy_input': entry['strategy_input'],
                'timestamp': entry['timestamp']
            }
        
        # Add to history
        perf['history'].append({
            'timestamp': entry['timestamp'],
            'return_pct': metrics['return_pct'],
            'grade': entry['grade']
        })
        
        # Keep only last 100 entries
        if len(perf['history']) > 100:
            perf['history'] = perf['history'][-100:]
    
    def _extract_patterns(self, entry: Dict):
        """Extract patterns from successful strategies"""
        if not entry['success']:
            return
        
        # Extract indicator patterns
        strategy_input = entry['strategy_input'].lower()
        
        # Simple pattern extraction
        indicators = []
        if 'rsi' in strategy_input:
            indicators.append('RSI')
        if 'macd' in strategy_input:
            indicators.append('MACD')
        if 'ema' in strategy_input or 'moving average' in strategy_input:
            indicators.append('Moving Average')
        if 'bollinger' in strategy_input:
            indicators.append('Bollinger Bands')
        if 'golden' in strategy_input:
            indicators.append('Golden Cross')
        
        # Track which indicators work well
        for indicator in indicators:
            if indicator not in self.memory['patterns']:
                self.memory['patterns'][indicator] = {
                    'success_count': 0,
                    'total_count': 0,
                    'avg_return': 0.0
                }
            
            pattern = self.memory['patterns'][indicator]
            pattern['total_count'] += 1
            
            if entry['success']:
                pattern['success_count'] += 1
                # Update running average
                n = pattern['total_count']
                pattern['avg_return'] = ((n - 1) * pattern['avg_return'] + entry['metrics']['return_pct']) / n
    
    def _generate_lesson(self, entry: Dict):
        """Generate learning lesson from backtest result"""
        if entry['grade'] in ['A+', 'A', 'B']:
            lesson = {
                'type': 'success',
                'timestamp': entry['timestamp'],
                'strategy': entry['strategy_input'],
                'lesson': f"Strategy worked well ({entry['grade']}): {entry['metrics']['return_pct']:.1f}% return, Sharpe {entry['metrics']['sharpe']:.2f}",
                'metrics': entry['metrics']
            }
            self.memory['lessons'].append(lesson)
        elif entry['grade'] in ['D', 'F']:
            lesson = {
                'type': 'improvement',
                'timestamp': entry['timestamp'],
                'strategy': entry['strategy_input'],
                'lesson': f"Strategy underperformed ({entry['grade']}): {entry['metrics']['return_pct']:.1f}% return, Max DD {entry['metrics']['max_drawdown']:.1f}%",
                'metrics': entry['metrics']
            }
            self.memory['lessons'].append(lesson)
        
        # Keep only last 50 lessons
        if len(self.memory['lessons']) > 50:
            self.memory['lessons'] = self.memory['lessons'][-50:]
    
    def _save_memory(self):
        """Save memory to disk (gracefully handles read-only filesystem)"""
        try:
            # Check if running on Vercel (read-only filesystem)
            if os.environ.get('VERCEL'):
                return  # Skip file writes on Vercel
            
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except (OSError, IOError, PermissionError):
            # Read-only filesystem - skip silently
            pass
    
    def _save_performance(self):
        """Save performance to disk (gracefully handles read-only filesystem)"""
        try:
            # Check if running on Vercel (read-only filesystem)
            if os.environ.get('VERCEL'):
                return  # Skip file writes on Vercel
            
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance, f, indent=2)
        except (OSError, IOError, PermissionError):
            # Read-only filesystem - skip silently
            pass
    
    def get_similar_strategies(self, strategy_input: str, limit: int = 5) -> List[Dict]:
        """Find similar strategies from memory"""
        # Simple keyword matching
        strategy_lower = strategy_input.lower()
        keywords = strategy_lower.split()
        
        matches = []
        for stored in self.memory['strategies']:
            stored_lower = stored['strategy_input'].lower()
            # Count keyword overlaps
            overlap = sum(1 for kw in keywords if kw in stored_lower)
            if overlap > 0:
                matches.append({
                    'strategy': stored['strategy_input'],
                    'return_pct': stored['metrics']['return_pct'],
                    'grade': stored['grade'],
                    'similarity': overlap / len(keywords)
                })
        
        # Sort by similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches[:limit]
    
    def get_performance_summary(self) -> Dict:
        """Get overall performance summary"""
        return self.performance
    
    def get_pattern_insights(self) -> Dict:
        """Get insights about which patterns work best"""
        insights = {}
        for indicator, pattern in self.memory['patterns'].items():
            if pattern['total_count'] >= 1:  # At least 1 data point
                success_rate = pattern['success_count'] / pattern['total_count']
                insights[indicator] = {
                    'success_rate': success_rate,
                    'avg_return': pattern['avg_return'],
                    'sample_size': pattern['total_count']
                }
        return insights
    
    def get_learning_insights(self) -> str:
        """Generate learning insights from memory"""
        insights = []
        
        # Overall performance
        perf = self.performance
        if perf['total_backtests'] > 0:
            win_rate = perf['profitable_strategies'] / perf['total_backtests']
            insights.append(f"Overall win rate: {win_rate:.1%} ({perf['profitable_strategies']}/{perf['total_backtests']})")
            insights.append(f"Average return: {perf['avg_return']:.2f}%")
        
        # Best patterns
        pattern_insights = self.get_pattern_insights()
        if pattern_insights:
            best_pattern = max(pattern_insights.items(), key=lambda x: x[1]['success_rate'])
            insights.append(f"Best pattern: {best_pattern[0]} ({best_pattern[1]['success_rate']:.1%} success rate)")
        
        # Recent lessons
        if self.memory['lessons']:
            recent = self.memory['lessons'][-3:]
            for lesson in recent:
                insights.append(f"💡 {lesson['lesson']}")
        
        return "\n".join(insights)


# Global memory instance
_memory = None


def get_memory() -> StrategyMemory:
    """Get global memory instance"""
    global _memory
    if _memory is None:
        _memory = StrategyMemory()
    return _memory


def store_backtest(strategy_input: str, results: Dict, code: str):
    """Store backtest result in memory"""
    memory = get_memory()
    memory.store_backtest_result(strategy_input, results, code)


def get_insights() -> str:
    """Get learning insights"""
    memory = get_memory()
    return memory.get_learning_insights()
