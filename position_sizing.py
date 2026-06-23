"""
StrategyAI - Position Sizing & Portfolio Heat Management
Adapted from DCA_claw's risk management system

Features:
- ATR-based position sizing
- Kelly criterion optimization
- Portfolio heat limits
- Max exposure control
"""

import numpy as np
from typing import Dict, Optional


class PositionSizer:
    """
    Calculate optimal position sizes based on risk
    Adapted from DCA_claw
    """
    
    def __init__(self, default_risk_per_trade: float = 0.02):
        """
        Args:
            default_risk_per_trade: Default risk per trade (2% = 0.02)
        """
        self.default_risk = default_risk_per_trade
        
        # Portfolio limits
        self.max_single_position = 0.05  # 5% max per position
        self.max_total_exposure = 0.20  # 20% max total exposure
        self.max_drawdown_limit = 0.15  # 15% max drawdown before stopping
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: Optional[float] = None,
        method: str = 'fixed_risk'
    ) -> Dict:
        """
        Calculate optimal position size
        
        Args:
            portfolio_value: Total portfolio value
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_per_trade: Risk per trade (optional, uses default if None)
            method: 'fixed_risk', 'kelly', or 'atr'
            
        Returns:
            Dict with position size, risk amount, and metadata
        """
        if risk_per_trade is None:
            risk_per_trade = self.default_risk
        
        if method == 'fixed_risk':
            return self._fixed_risk_sizing(
                portfolio_value, entry_price, stop_loss_price, risk_per_trade
            )
        elif method == 'kelly':
            return self._kelly_sizing(
                portfolio_value, entry_price, stop_loss_price, risk_per_trade
            )
        elif method == 'atr':
            return self._atr_sizing(
                portfolio_value, entry_price, stop_loss_price, risk_per_trade
            )
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _fixed_risk_sizing(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: float
    ) -> Dict:
        """Fixed risk per trade (e.g., always risk 2%)"""
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        
        if risk_per_share == 0:
            return {
                'error': 'Stop loss equals entry price',
                'position_size': 0,
                'position_value': 0,
                'risk_amount': 0
            }
        
        # Calculate position size
        risk_amount = portfolio_value * risk_per_trade
        position_size = risk_amount / risk_per_share
        
        # Apply position limits
        max_position_value = portfolio_value * self.max_single_position
        max_position_size = max_position_value / entry_price
        
        if position_size > max_position_size:
            position_size = max_position_size
            risk_amount = position_size * risk_per_share
        
        position_value = position_size * entry_price
        
        return {
            'position_size': round(position_size, 8),
            'position_value': round(position_value, 2),
            'risk_amount': round(risk_amount, 2),
            'risk_percentage': round(risk_amount / portfolio_value * 100, 2),
            'entry_price': entry_price,
            'stop_loss': stop_loss_price,
            'method': 'fixed_risk'
        }
    
    def _kelly_sizing(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: float,
        win_rate: float = 0.55,
        win_loss_ratio: float = 1.5
    ) -> Dict:
        """
        Kelly criterion position sizing
        
        Args:
            win_rate: Historical win rate (default 55%)
            win_loss_ratio: Average win / average loss (default 1.5)
        """
        
        # Kelly formula: K = W - (1-W)/R
        # W = win probability, R = win/loss ratio
        kelly_fraction = win_rate - (1 - win_rate) / win_loss_ratio
        
        # Half-Kelly for safety (reduces volatility)
        kelly_fraction = kelly_fraction / 2
        
        # Cap at max risk per trade
        kelly_fraction = min(kelly_fraction, risk_per_trade)
        kelly_fraction = max(kelly_fraction, 0)  # No negative sizing
        
        # Use fixed risk sizing with Kelly fraction
        return self._fixed_risk_sizing(
            portfolio_value, entry_price, stop_loss_price, kelly_fraction
        )
    
    def _atr_sizing(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: float,
        atr: Optional[float] = None
    ) -> Dict:
        """
        ATR-based position sizing (volatility-adjusted)
        
        Args:
            atr: Average True Range (volatility measure)
        """
        
        if atr is None or atr == 0:
            # Fallback to fixed risk
            return self._fixed_risk_sizing(
                portfolio_value, entry_price, stop_loss_price, risk_per_trade
            )
        
        # ATR-based stop distance (e.g., 2x ATR)
        atr_multiplier = 2.0
        stop_distance = atr * atr_multiplier
        
        # Adjust position size based on volatility
        # Higher volatility = smaller position
        volatility_factor = min(1.0, 1.0 / (atr / entry_price * 10))
        
        # Adjusted risk
        adjusted_risk = risk_per_trade * volatility_factor
        
        return self._fixed_risk_sizing(
            portfolio_value, entry_price, stop_loss_price, adjusted_risk
        )
    
    def check_portfolio_heat(
        self,
        current_exposure: float,
        current_drawdown: float,
        new_position_value: float,
        portfolio_value: float
    ) -> Dict:
        """
        Check if adding a new position is safe
        
        Args:
            current_exposure: Current total exposure (0-1)
            current_drawdown: Current drawdown (0-1)
            new_position_value: Value of new position
            portfolio_value: Total portfolio value
            
        Returns:
            Dict with approval status and reasoning
        """
        new_exposure = current_exposure + (new_position_value / portfolio_value)
        
        # Check max exposure
        if new_exposure > self.max_total_exposure:
            return {
                'approved': False,
                'reason': f'Max exposure limit ({self.max_total_exposure:.0%}) would be exceeded',
                'current_exposure': current_exposure,
                'new_exposure': new_exposure,
                'max_allowed': self.max_total_exposure
            }
        
        # Check drawdown limit
        if current_drawdown > self.max_drawdown_limit:
            return {
                'approved': False,
                'reason': f'Max drawdown limit ({self.max_drawdown_limit:.0%}) exceeded',
                'current_drawdown': current_drawdown,
                'max_allowed': self.max_drawdown_limit
            }
        
        # Check single position limit
        position_pct = new_position_value / portfolio_value
        if position_pct > self.max_single_position:
            return {
                'approved': False,
                'reason': f'Single position limit ({self.max_single_position:.0%}) exceeded',
                'position_pct': position_pct,
                'max_allowed': self.max_single_position
            }
        
        return {
            'approved': True,
            'reason': 'Within risk limits',
            'current_exposure': current_exposure,
            'new_exposure': new_exposure,
            'remaining_capacity': self.max_total_exposure - new_exposure
        }
    
    def calculate_portfolio_metrics(
        self,
        positions: list,
        portfolio_value: float
    ) -> Dict:
        """
        Calculate portfolio-level risk metrics
        
        Args:
            positions: List of position dicts with 'value', 'entry', 'current_price'
            portfolio_value: Total portfolio value
            
        Returns:
            Dict with portfolio metrics
        """
        if not positions:
            return {
                'total_exposure': 0,
                'unrealized_pnl': 0,
                'unrealized_pnl_pct': 0,
                'position_count': 0,
                'largest_position_pct': 0
            }
        
        total_value = sum(p.get('value', 0) for p in positions)
        total_exposure = total_value / portfolio_value
        
        # Calculate unrealized PnL
        unrealized_pnl = 0
        for p in positions:
            entry = p.get('entry', 0)
            current = p.get('current_price', 0)
            size = p.get('size', 0)
            if entry > 0:
                pnl = (current - entry) * size
                unrealized_pnl += pnl
        
        unrealized_pnl_pct = unrealized_pnl / portfolio_value * 100
        
        # Find largest position
        position_pcts = [p.get('value', 0) / portfolio_value for p in positions]
        largest_position_pct = max(position_pcts) if position_pcts else 0
        
        return {
            'total_exposure': round(total_exposure, 4),
            'total_value': round(total_value, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'unrealized_pnl_pct': round(unrealized_pnl_pct, 2),
            'position_count': len(positions),
            'largest_position_pct': round(largest_position_pct, 4),
            'remaining_capacity': round(self.max_total_exposure - total_exposure, 4)
        }


# Global position sizer instance
_sizer = None


def get_sizer() -> PositionSizer:
    """Get global position sizer instance"""
    global _sizer
    if _sizer is None:
        _sizer = PositionSizer()
    return _sizer


def calculate_position_size(
    portfolio_value: float,
    entry_price: float,
    stop_loss_price: float,
    **kwargs
) -> Dict:
    """Calculate position size"""
    sizer = get_sizer()
    return sizer.calculate_position_size(
        portfolio_value, entry_price, stop_loss_price, **kwargs
    )


def check_portfolio_heat(
    current_exposure: float,
    current_drawdown: float,
    new_position_value: float,
    portfolio_value: float
) -> Dict:
    """Check portfolio heat"""
    sizer = get_sizer()
    return sizer.check_portfolio_heat(
        current_exposure, current_drawdown, new_position_value, portfolio_value
    )
