"""
StrategyAI - Strategy Scoring Engine
Adapted from DCA_claw's 16-signal scoring system

Features:
- Multi-dimensional strategy scoring
- Confidence calculation
- Risk assessment
- Pattern recognition
"""

import numpy as np
from typing import Dict, List, Tuple


class StrategyScorer:
    """
    Scores trading strategies on multiple dimensions
    Adapted from DCA_claw's 16-signal engine
    """
    
    def __init__(self):
        # Scoring weights (can be tuned)
        self.weights = {
            'trend_quality': 0.15,
            'signal_clarity': 0.12,
            'risk_reward': 0.15,
            'win_rate_potential': 0.12,
            'drawdown_risk': 0.12,
            'trade_frequency': 0.08,
            'market_regime_fit': 0.10,
            'indicator_confluence': 0.10,
            'volatility_adjustment': 0.06,
        }
    
    def score_strategy(self, results: Dict, market_data: Dict = None) -> Dict:
        """
        Score a strategy on multiple dimensions
        
        Args:
            results: Backtest results (metrics, charts, etc.)
            market_data: Optional market context data
            
        Returns:
            Dict with scores, confidence, and insights
        """
        scores = {}
        
        # 1. Trend Quality (how well does it capture trends?)
        scores['trend_quality'] = self._score_trend_quality(results)
        
        # 2. Signal Clarity (how clear are entry/exit signals?)
        scores['signal_clarity'] = self._score_signal_clarity(results)
        
        # 3. Risk/Reward Ratio
        scores['risk_reward'] = self._score_risk_reward(results)
        
        # 4. Win Rate Potential
        scores['win_rate_potential'] = self._score_win_rate(results)
        
        # 5. Drawdown Risk (inverse - lower DD is better)
        scores['drawdown_risk'] = self._score_drawdown_risk(results)
        
        # 6. Trade Frequency (optimal, not too high/low)
        scores['trade_frequency'] = self._score_trade_frequency(results)
        
        # 7. Market Regime Fit (how well does it fit current market?)
        scores['market_regime_fit'] = self._score_market_regime(results, market_data)
        
        # 8. Indicator Confluence (multiple confirming indicators)
        scores['indicator_confluence'] = self._score_indicator_confluence(results)
        
        # 9. Volatility Adjustment (risk-adjusted for volatility)
        scores['volatility_adjustment'] = self._score_volatility(results)
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[metric] * weight 
            for metric, weight in self.weights.items()
        )
        
        # Calculate confidence level
        confidence = self._calculate_confidence(scores, results)
        
        # Generate insights
        insights = self._generate_insights(scores, results)
        
        # Risk level classification
        risk_level = self._classify_risk(results)
        
        return {
            'overall_score': overall_score,  # 0-100
            'confidence': confidence,  # 0-100
            'risk_level': risk_level,  # LOW, MEDIUM, HIGH, EXTREME
            'dimension_scores': scores,
            'insights': insights,
            'recommendation': self._generate_recommendation(overall_score, confidence, risk_level)
        }
    
    def _score_trend_quality(self, results: Dict) -> float:
        """Score how well strategy captures trends (0-100)"""
        return_pct = results.get('return_pct', 0)
        benchmark_return = results.get('benchmark_return', 0)
        
        # Outperformance is key
        outperf = return_pct - benchmark_return
        
        # Score based on outperformance
        if outperf > 20:
            return 100
        elif outperf > 10:
            return 85
        elif outperf > 5:
            return 70
        elif outperf > 0:
            return 55
        elif outperf > -5:
            return 40
        elif outperf > -10:
            return 25
        else:
            return 10
    
    def _score_signal_clarity(self, results: Dict) -> float:
        """Score clarity of entry/exit signals (0-100)"""
        total_trades = results.get('total_trades', 0)
        win_rate = results.get('win_rate', 0)
        
        # More trades with good win rate = clear signals
        if total_trades < 5:
            return 30  # Too few signals
        elif total_trades < 10:
            return 50
        elif total_trades < 20:
            return 70
        elif total_trades < 50:
            return 85
        else:
            # Too many trades might be overfitting
            return 60 if win_rate > 50 else 40
    
    def _score_risk_reward(self, results: Dict) -> float:
        """Score risk/reward ratio (0-100)"""
        return_pct = abs(results.get('return_pct', 0))
        max_dd = abs(results.get('max_drawdown', 0))
        
        if max_dd == 0:
            return 50
        
        # Return per unit of drawdown
        rr_ratio = return_pct / max_dd
        
        if rr_ratio > 3:
            return 100
        elif rr_ratio > 2:
            return 85
        elif rr_ratio > 1.5:
            return 70
        elif rr_ratio > 1:
            return 55
        elif rr_ratio > 0.5:
            return 40
        else:
            return 20
    
    def _score_win_rate(self, results: Dict) -> float:
        """Score win rate potential (0-100)"""
        win_rate = results.get('win_rate', 0)
        
        # Direct mapping
        return min(win_rate * 2, 100)  # 50% win rate = 100 score
    
    def _score_drawdown_risk(self, results: Dict) -> float:
        """Score drawdown risk (inverse - lower is better) (0-100)"""
        max_dd = abs(results.get('max_drawdown', 0))
        
        if max_dd < 5:
            return 100
        elif max_dd < 10:
            return 85
        elif max_dd < 15:
            return 70
        elif max_dd < 20:
            return 55
        elif max_dd < 30:
            return 40
        else:
            return 20
    
    def _score_trade_frequency(self, results: Dict) -> float:
        """Score trade frequency (optimal range) (0-100)"""
        total_trades = results.get('total_trades', 0)
        
        # Optimal: 10-30 trades (not too few, not too many)
        if 10 <= total_trades <= 30:
            return 100
        elif 5 <= total_trades < 10:
            return 75
        elif 30 < total_trades <= 50:
            return 75
        elif total_trades < 5:
            return 50
        else:
            return 40  # Too many trades
    
    def _score_market_regime(self, results: Dict, market_data: Dict = None) -> float:
        """Score how well strategy fits current market regime (0-100)"""
        # Simplified - would need actual market data for full implementation
        # For now, use Sharpe ratio as proxy
        sharpe = results.get('sharpe', 0)
        
        if sharpe > 2:
            return 100
        elif sharpe > 1.5:
            return 85
        elif sharpe > 1:
            return 70
        elif sharpe > 0.5:
            return 55
        else:
            return 40
    
    def _score_indicator_confluence(self, results: Dict) -> float:
        """Score based on indicator confluence (0-100)"""
        # Check if strategy uses multiple indicators
        # This would require parsing the code - simplified for now
        
        # Use Sharpe as proxy for indicator quality
        sharpe = results.get('sharpe', 0)
        
        if sharpe > 2:
            return 95  # Likely good indicator combination
        elif sharpe > 1.5:
            return 80
        elif sharpe > 1:
            return 65
        else:
            return 50
    
    def _score_volatility(self, results: Dict) -> float:
        """Score volatility-adjusted returns (0-100)"""
        sharpe = results.get('sharpe', 0)
        
        # Sharpe already accounts for volatility
        if sharpe > 2:
            return 100
        elif sharpe > 1.5:
            return 85
        elif sharpe > 1:
            return 70
        elif sharpe > 0.5:
            return 55
        else:
            return 40
    
    def _calculate_confidence(self, scores: Dict[str, float], results: Dict) -> float:
        """Calculate overall confidence level (0-100)"""
        # Base confidence from weighted scores
        base_confidence = sum(scores.values()) / len(scores)
        
        # Adjust for sample size
        total_trades = results.get('total_trades', 0)
        if total_trades < 10:
            base_confidence *= 0.7  # Low confidence with few trades
        elif total_trades < 20:
            base_confidence *= 0.85
        elif total_trades > 100:
            base_confidence *= 0.9  # Slight penalty for potential overfitting
        
        # Adjust for consistency
        win_rate = results.get('win_rate', 0)
        if win_rate > 60:
            base_confidence *= 1.05
        elif win_rate < 40:
            base_confidence *= 0.9
        
        return min(max(base_confidence, 0), 100)
    
    def _generate_insights(self, scores: Dict[str, float], results: Dict) -> List[str]:
        """Generate actionable insights"""
        insights = []
        
        # Find strengths (top 2 scores)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        strengths = sorted_scores[:2]
        
        # Find weaknesses (bottom 2 scores)
        weaknesses = sorted_scores[-2:]
        
        # Strength insights
        for metric, score in strengths:
            if score > 80:
                insights.append(f"✅ Strong {metric.replace('_', ' ')} ({score:.0f}/100)")
        
        # Weakness insights
        for metric, score in weaknesses:
            if score < 50:
                insights.append(f"⚠️ Weak {metric.replace('_', ' ')} ({score:.0f}/100) - consider improving")
        
        # Specific recommendations
        if scores['drawdown_risk'] < 50:
            insights.append("💡 Consider adding stop-loss to reduce drawdown")
        
        if scores['trade_frequency'] < 50:
            insights.append("💡 Adjust signal thresholds for optimal trade frequency")
        
        if scores['risk_reward'] < 50:
            insights.append("💡 Improve entry timing or take-profit levels")
        
        return insights
    
    def _classify_risk(self, results: Dict) -> str:
        """Classify overall risk level"""
        max_dd = abs(results.get('max_drawdown', 0))
        sharpe = results.get('sharpe', 0)
        return_pct = results.get('return_pct', 0)
        
        # Risk classification
        if max_dd > 30 or sharpe < 0 or return_pct < -20:
            return 'EXTREME'
        elif max_dd > 20 or sharpe < 0.5 or return_pct < -10:
            return 'HIGH'
        elif max_dd > 10 or sharpe < 1:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_recommendation(self, score: float, confidence: float, risk_level: str) -> str:
        """Generate overall recommendation"""
        if risk_level == 'EXTREME':
            return "❌ DO NOT USE - Extreme risk, likely to lose money"
        elif risk_level == 'HIGH':
            return "⚠️ HIGH RISK - Use with caution, small position size only"
        elif score >= 80 and confidence >= 70:
            return "✅ RECOMMENDED - Strong strategy with good confidence"
        elif score >= 60 and confidence >= 50:
            return "👍 ACCEPTABLE - Decent strategy, monitor performance"
        elif score >= 40:
            return "🤔 NEEDS IMPROVEMENT - Consider refining strategy"
        else:
            return "❌ NOT RECOMMENDED - Poor performance metrics"


# Global scorer instance
_scorer = None


def get_scorer() -> StrategyScorer:
    """Get global scorer instance"""
    global _scorer
    if _scorer is None:
        _scorer = StrategyScorer()
    return _scorer


def score_strategy(results: Dict, market_data: Dict = None) -> Dict:
    """Score a strategy"""
    scorer = get_scorer()
    return scorer.score_strategy(results, market_data)
