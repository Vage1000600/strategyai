"""
StrategyAI - Visualization Module
Person 3: Results & Visualization Lead

Creates interactive charts for backtest results using Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict


class PlotResults:
    """Generate visualization charts for backtest results"""
    
    @staticmethod
    def plot_equity_curve(equity_curve: List[float]) -> go.Figure:
        """
        Plot equity curve over time.
        
        Args:
            equity_curve: List of equity values over time
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        # Create x-axis (time steps)
        x_values = list(range(len(equity_curve)))
        
        # Add equity line
        fig.add_trace(go.Scatter(
            x=x_values,
            y=equity_curve,
            mode='lines',
            name='Equity',
            line=dict(color='#00CC96', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 204, 150, 0.1)'
        ))
        
        # Add initial capital line
        initial_capital = equity_curve[0] if equity_curve else 1000
        fig.add_hline(
            y=initial_capital,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Initial: ${initial_capital}",
            annotation_position="right"
        )
        
        # Layout
        fig.update_layout(
            title="📈 Equity Curve",
            xaxis_title="Time (candles)",
            yaxis_title="Equity (USDT)",
            template="plotly_dark",
            hovermode='x unified',
            height=400,
            showlegend=True
        )
        
        # Add hover template
        fig.update_traces(
            hovertemplate='<b>Equity</b>: $%{y:.2f}<extra></extra>'
        )
        
        return fig
    
    @staticmethod
    def plot_drawdown(drawdown: List[float]) -> go.Figure:
        """
        Plot drawdown over time.
        
        Args:
            drawdown: List of drawdown percentages
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        # Create x-axis (time steps)
        x_values = list(range(len(drawdown)))
        
        # Add drawdown area
        fig.add_trace(go.Scatter(
            x=x_values,
            y=drawdown,
            mode='lines',
            name='Drawdown',
            line=dict(color='#EF553B', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 85, 59, 0.2)'
        ))
        
        # Layout
        fig.update_layout(
            title="📉 Drawdown",
            xaxis_title="Time (candles)",
            yaxis_title="Drawdown (%)",
            template="plotly_dark",
            hovermode='x unified',
            height=300,
            showlegend=False
        )
        
        # Add hover template
        fig.update_traces(
            hovertemplate='<b>Drawdown</b>: %{y:.2f}%<extra></extra>'
        )
        
        return fig
    
    @staticmethod
    def plot_monthly_returns(returns: List[float]) -> go.Figure:
        """
        Plot monthly returns heatmap (placeholder for future feature).
        
        Args:
            returns: List of monthly returns
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=list(range(len(returns))),
            y=returns,
            marker_color=['#00CC96' if r > 0 else '#EF553B' for r in returns],
            name='Monthly Return'
        ))
        
        fig.update_layout(
            title="📊 Monthly Returns",
            xaxis_title="Month",
            yaxis_title="Return (%)",
            template="plotly_dark",
            height=300,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def plot_trade_distribution(trades_df: pd.DataFrame) -> go.Figure:
        """
        Plot distribution of winning vs losing trades.
        
        Args:
            trades_df: DataFrame with trade results
            
        Returns:
            Plotly Figure object
        """
        if trades_df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No trades executed", showarrow=False)
            return fig
        
        # Separate wins and losses
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        
        fig = go.Figure()
        
        # Winning trades
        fig.add_trace(go.Bar(
            x=list(range(len(wins))),
            y=wins['pnl'],
            name='Winning Trades',
            marker_color='#00CC96',
            text=wins['pnl'].apply(lambda x: f"${x:.2f}"),
            textposition='auto'
        ))
        
        # Losing trades
        fig.add_trace(go.Bar(
            x=list(range(len(losses))),
            y=losses['pnl'],
            name='Losing Trades',
            marker_color='#EF553B',
            text=losses['pnl'].apply(lambda x: f"${x:.2f}"),
            textposition='auto'
        ))
        
        fig.update_layout(
            title="💼 Trade Distribution",
            xaxis_title="Trade #",
            yaxis_title="PnL (USDT)",
            template="plotly_dark",
            barmode='relative',
            height=400,
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def plot_metrics_summary(metrics: Dict) -> go.Figure:
        """
        Create a metrics summary table as a plot.
        
        Args:
            metrics: Dict with performance metrics
            
        Returns:
            Plotly Figure object
        """
        # Create table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Metric</b>', '<b>Value</b>'],
                fill_color='#1f2937',
                font=dict(color='white', size=14),
                align='left'
            ),
            cells=dict(
                values=[
                    ['Total PnL', 'Return %', 'Sharpe Ratio', 'Max Drawdown', 
                     'Win Rate', 'Total Trades', 'Final Equity'],
                    [f"${metrics['pnl']:.2f}",
                     f"{metrics['return_pct']:.2f}%",
                     f"{metrics['sharpe']:.2f}",
                     f"{metrics['max_drawdown']:.2f}%",
                     f"{metrics['win_rate']:.2f}%",
                     metrics['total_trades'],
                     f"${metrics['final_equity']:.2f}"]
                ],
                fill_color='#374151',
                font=dict(color='white', size=12),
                align='left'
            )
        )])
        
        fig.update_layout(
            title="📊 Performance Summary",
            template="plotly_dark",
            height=300
        )
        
        return fig


# Convenience exports
plot_equity_curve = PlotResults.plot_equity_curve
plot_drawdown = PlotResults.plot_drawdown
plot_monthly_returns = PlotResults.plot_monthly_returns
plot_trade_distribution = PlotResults.plot_trade_distribution
plot_metrics_summary = PlotResults.plot_metrics_summary


# Test function
if __name__ == "__main__":
    # Test with sample data
    import numpy as np
    
    # Generate sample equity curve
    sample_equity = [1000]
    for i in range(100):
        change = np.random.randn() * 10
        sample_equity.append(sample_equity[-1] + change)
    
    # Generate sample drawdown
    sample_drawdown = []
    peak = sample_equity[0]
    for eq in sample_equity:
        if eq > peak:
            peak = eq
        drawdown = (eq - peak) / peak * 100
        sample_drawdown.append(drawdown)
    
    # Plot
    fig1 = plot_equity_curve(sample_equity)
    fig1.show()
    
    fig2 = plot_drawdown(sample_drawdown)
    fig2.show()
