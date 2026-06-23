"""
StrategyAI - Visualization Module (IMPROVED)
Person 3: Results & Visualization Lead

New Features:
✅ Initial capital reference line
✅ Better hover templates
✅ Improved color schemes
✅ Additional chart types
✅ Export-ready formatting
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict


class PlotResults:
    """Generate visualization charts for backtest results"""
    
    @staticmethod
    def plot_equity_curve(equity_curve: List[float], initial_capital: float = 1000) -> go.Figure:
        """
        Plot equity curve over time with initial capital reference.
        
        Args:
            equity_curve: List of equity values over time
            initial_capital: Starting capital for reference line
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        # Create x-axis (time steps)
        x_values = list(range(len(equity_curve)))
        
        # Calculate return percentage for y-axis
        equity_array = np.array(equity_curve)
        return_pct = ((equity_array - initial_capital) / initial_capital) * 100
        
        # Add equity line
        fig.add_trace(go.Scatter(
            x=x_values,
            y=return_pct,
            mode='lines',
            name='Strategy Return',
            line=dict(color='#00CC96', width=3),
            fill='tozeroy',
            fillcolor='rgba(0, 204, 150, 0.1)',
            hovertemplate='<b>Candle</b>: %{x}<br><b>Return</b>: %{y:.2f}%<br><b>Equity</b>: ${' + str(initial_capital) + ':.2f}<extra></extra>'
        ))
        
        # Add initial capital line (0% return)
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
            line_width=2,
            annotation_text="Break-even",
            annotation_position="right"
        )
        
        # Add best and worst points
        max_return_idx = np.argmax(return_pct)
        min_return_idx = np.argmin(return_pct)
        
        fig.add_trace(go.Scatter(
            x=[max_return_idx],
            y=[return_pct[max_return_idx]],
            mode='markers',
            name='Peak',
            marker=dict(color='#00FF00', size=10, symbol='star'),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=[min_return_idx],
            y=[return_pct[min_return_idx]],
            mode='markers',
            name='Trough',
            marker=dict(color='#FF0000', size=10, symbol='x'),
            showlegend=False
        ))
        
        # Layout
        fig.update_layout(
            title="📈 Equity Curve (Return %)",
            xaxis_title="Time (candles)",
            yaxis_title="Return (%)",
            template="plotly_dark",
            hovermode='x unified',
            height=450,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Add grid
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        
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
        
        # Convert to numpy for easier manipulation
        drawdown_array = np.array(drawdown)
        
        # Color based on drawdown severity
        colors = ['#FFA500' if dd < -5 else '#FF6347' if dd < -10 else '#FF4500' for dd in drawdown_array]
        
        # Add drawdown area
        fig.add_trace(go.Scatter(
            x=x_values,
            y=drawdown_array,
            mode='lines',
            name='Drawdown',
            line=dict(color='#EF553B', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 85, 59, 0.3)',
            hovertemplate='<b>Candle</b>: %{x}<br><b>Drawdown</b>: %{y:.2f}%<extra></extra>'
        ))
        
        # Add worst drawdown line
        max_dd = min(drawdown_array)
        max_dd_idx = np.argmin(drawdown_array)
        
        fig.add_hline(
            y=max_dd,
            line_dash="dot",
            line_color="red",
            annotation_text=f"Max DD: {max_dd:.2f}%",
            annotation_position="right"
        )
        
        # Layout
        fig.update_layout(
            title="📉 Drawdown (Peak-to-Trough Decline)",
            xaxis_title="Time (candles)",
            yaxis_title="Drawdown (%)",
            template="plotly_dark",
            hovermode='x unified',
            height=350,
            showlegend=False
        )
        
        # Add grid
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        
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
            fig.add_annotation(
                text="No trades executed",
                showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(
                title="💼 Trade Distribution",
                template="plotly_dark",
                height=400
            )
            return fig
        
        # Separate wins and losses
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        
        fig = go.Figure()
        
        # Winning trades
        if not wins.empty:
            fig.add_trace(go.Bar(
                x=list(range(len(wins))),
                y=wins['pnl'],
                name='Winning Trades',
                marker_color='#00CC96',
                text=wins['pnl'].apply(lambda x: f"${x:.2f}"),
                textposition='auto',
                hovertemplate='<b>Trade</b>: %{x}<br><b>PnL</b>: ${y:.2f}<extra></extra>'
            ))
        
        # Losing trades
        if not losses.empty:
            fig.add_trace(go.Bar(
                x=list(range(len(losses))),
                y=losses['pnl'],
                name='Losing Trades',
                marker_color='#EF553B',
                text=losses['pnl'].apply(lambda x: f"${x:.2f}"),
                textposition='auto',
                hovertemplate='<b>Trade</b>: %{x}<br><b>PnL</b>: ${y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            title="💼 Trade Distribution (Winning vs Losing)",
            xaxis_title="Trade #",
            yaxis_title="PnL (USDT)",
            template="plotly_dark",
            barmode='relative',
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        
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
        # Prepare data
        metric_names = [
            'Total PnL',
            'Return %',
            'Sharpe Ratio',
            'Max Drawdown',
            'Win Rate',
            'Total Trades',
            'Profit Factor',
            'Avg Win/Loss',
            'Beat HODL'
        ]
        
        metric_values = [
            f"${metrics['pnl']:.2f}",
            f"{metrics['return_pct']:.2f}%",
            f"{metrics['sharpe']:.2f}",
            f"{metrics['max_drawdown']:.2f}%",
            f"{metrics['win_rate']:.1f}%",
            str(metrics['total_trades']),
            f"{metrics.get('profit_factor', 0):.2f}",
            f"{metrics.get('avg_win_loss', 0):.2f}",
            f"{metrics.get('return_pct', 0) - metrics.get('benchmark_return', 0):+.2f}%"
        ]
        
        # Color coding
        colors = []
        for i, name in enumerate(metric_names):
            if 'PnL' in name or 'Return' in name or 'Beat' in name:
                colors.append('#00CC96' if float(metric_values[i].replace('$', '').replace('%', '').replace('+', '')) > 0 else '#EF553B')
            elif 'Drawdown' in name:
                colors.append('#EF553B' if float(metric_values[i].replace('%', '')) > 15 else '#FFA500')
            else:
                colors.append('#1f2937')
        
        # Create table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['<b>Metric</b>', '<b>Value</b>'],
                fill_color='#374151',
                font=dict(color='white', size=14),
                align='left',
                height=40
            ),
            cells=dict(
                values=[metric_names, metric_values],
                fill_color=['#1f2937'] * len(metric_names),
                font=dict(color='white', size=12),
                align='left',
                height=35
            )
        )])
        
        fig.update_layout(
            title="📊 Performance Summary",
            template="plotly_dark",
            height=350
        )
        
        return fig
    
    @staticmethod
    def plot_monthly_returns(equity_curve: List[float], initial_capital: float) -> go.Figure:
        """
        Plot monthly returns (aggregated from equity curve).
        
        Args:
            equity_curve: List of equity values
            initial_capital: Starting capital
            
        Returns:
            Plotly Figure object
        """
        # Convert to monthly (approximate - every 720 candles for 1h timeframe)
        equity_array = np.array(equity_curve)
        monthly_returns = []
        
        for i in range(0, len(equity_array), 720):
            if i + 720 < len(equity_array):
                month_start = equity_array[i]
                month_end = equity_array[i + 720]
                monthly_ret = ((month_end - month_start) / month_start) * 100
                monthly_returns.append(monthly_ret)
        
        if not monthly_returns:
            fig = go.Figure()
            fig.add_annotation(text="Insufficient data for monthly breakdown", showarrow=False)
            return fig
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=list(range(1, len(monthly_returns) + 1)),
            y=monthly_returns,
            marker_color=['#00CC96' if r > 0 else '#EF553B' for r in monthly_returns],
            name='Monthly Return',
            hovertemplate='<b>Month</b>: %{x}<br><b>Return</b>: %{y:.2f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title="📅 Monthly Returns",
            xaxis_title="Month",
            yaxis_title="Return (%)",
            template="plotly_dark",
            height=350,
            showlegend=False
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        
        return fig


# Convenience exports
plot_equity_curve = PlotResults.plot_equity_curve
plot_drawdown = PlotResults.plot_drawdown
plot_trade_distribution = PlotResults.plot_trade_distribution
plot_metrics_summary = PlotResults.plot_metrics_summary
plot_monthly_returns = PlotResults.plot_monthly_returns


# Test function
if __name__ == "__main__":
    # Test with sample data
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
    fig1 = plot_equity_curve(sample_equity, 1000)
    fig1.show()
    
    fig2 = plot_drawdown(sample_drawdown)
    fig2.show()
