"""Plotting utilities for equity curves, IC charts, regime heatmaps, drawdown plots."""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict, Any, List


def plot_equity_curve(
    equity_curve: pd.Series,
    benchmark: Optional[pd.Series] = None,
    title: str = "Equity Curve"
) -> go.Figure:
    """Plot equity curve with optional benchmark.
    
    Args:
        equity_curve: Cumulative equity curve
        benchmark: Optional benchmark equity curve
        title: Plot title
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=equity_curve.index,
        y=equity_curve.values,
        mode='lines',
        name='Portfolio',
        line=dict(color='blue', width=2)
    ))
    
    if benchmark is not None:
        # Align dates
        common_dates = equity_curve.index.intersection(benchmark.index)
        if len(common_dates) > 0:
            fig.add_trace(go.Scatter(
                x=common_dates,
                y=benchmark.loc[common_dates].values,
                mode='lines',
                name='Benchmark',
                line=dict(color='gray', width=1, dash='dash')
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Cumulative Return",
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig


def plot_drawdown(
    equity_curve: pd.Series,
    title: str = "Drawdown"
) -> go.Figure:
    """Plot drawdown chart.
    
    Args:
        equity_curve: Cumulative equity curve
        title: Plot title
    
    Returns:
        Plotly figure
    """
    running_max = equity_curve.expanding().max()
    drawdown = (equity_curve - running_max) / running_max
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=drawdown.index,
        y=drawdown.values * 100,  # Convert to percentage
        mode='lines',
        fill='tozeroy',
        name='Drawdown',
        line=dict(color='red', width=1),
        fillcolor='rgba(255,0,0,0.3)'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode='x unified',
        template='plotly_white',
        yaxis=dict(tickformat='.1f')
    )
    
    return fig


def plot_ic_timeline(
    ic_series: pd.Series,
    title: str = "Information Coefficient Timeline"
) -> go.Figure:
    """Plot IC over time.
    
    Args:
        ic_series: Series of IC values
        title: Plot title
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=ic_series.index,
        y=ic_series.values,
        mode='lines+markers',
        name='IC',
        line=dict(color='blue', width=1),
        marker=dict(size=3)
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Add mean line
    mean_ic = ic_series.mean()
    fig.add_hline(y=mean_ic, line_dash="dot", line_color="green", 
                  annotation_text=f"Mean: {mean_ic:.4f}")
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="IC",
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig


def plot_ic_histogram(
    ic_series: pd.Series,
    title: str = "IC Distribution"
) -> go.Figure:
    """Plot IC histogram.
    
    Args:
        ic_series: Series of IC values
        title: Plot title
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=ic_series.values,
        nbinsx=30,
        name='IC',
        marker_color='blue',
        opacity=0.7
    ))
    
    # Add mean line
    mean_ic = ic_series.mean()
    fig.add_vline(x=mean_ic, line_dash="dash", line_color="red",
                  annotation_text=f"Mean: {mean_ic:.4f}")
    
    fig.update_layout(
        title=title,
        xaxis_title="IC",
        yaxis_title="Frequency",
        template='plotly_white'
    )
    
    return fig


def plot_regime_heatmap(
    performance_by_regime: Dict[str, Dict[str, float]],
    title: str = "Performance by Regime"
) -> go.Figure:
    """Plot regime performance heatmap.
    
    Args:
        performance_by_regime: Dictionary mapping regime to metrics
            e.g., {"high_vol": {"sharpe": 1.2, "return": 0.15}, ...}
        title: Plot title
    
    Returns:
        Plotly figure
    """
    regimes = list(performance_by_regime.keys())
    metrics = list(performance_by_regime[regimes[0]].keys()) if regimes else []
    
    # Build matrix
    matrix = []
    for regime in regimes:
        row = [performance_by_regime[regime].get(metric, 0) for metric in metrics]
        matrix.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=metrics,
        y=regimes,
        colorscale='RdYlGn',
        text=matrix,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Value")
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Metric",
        yaxis_title="Regime",
        template='plotly_white'
    )
    
    return fig


def plot_rolling_metrics(
    returns: pd.Series,
    window: int = 252,
    title: str = "Rolling Performance Metrics"
) -> go.Figure:
    """Plot rolling Sharpe and other metrics.
    
    Args:
        returns: Return series
        window: Rolling window size
        title: Plot title
    
    Returns:
        Plotly figure with subplots
    """
    from ..backtest.metrics import sharpe, annualized_return, annualized_volatility
    
    # Calculate rolling metrics
    rolling_sharpe = []
    rolling_ret = []
    rolling_vol = []
    dates = []
    
    for i in range(window, len(returns), window // 4):  # Overlapping windows
        window_returns = returns.iloc[i-window:i]
        if len(window_returns) > 0:
            rolling_sharpe.append(sharpe(window_returns))
            rolling_ret.append(annualized_return(window_returns))
            rolling_vol.append(annualized_volatility(window_returns))
            dates.append(returns.index[i])
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Rolling Sharpe', 'Rolling Return', 'Rolling Volatility'),
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(x=dates, y=rolling_sharpe, mode='lines', name='Sharpe'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=dates, y=rolling_ret, mode='lines', name='Return'),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=dates, y=rolling_vol, mode='lines', name='Volatility'),
        row=3, col=1
    )
    
    fig.update_layout(
        title=title,
        height=800,
        template='plotly_white',
        showlegend=False
    )
    
    return fig


def plot_factor_leaderboard(
    runs_data: List[Dict[str, Any]],
    title: str = "Factor Leaderboard"
) -> go.Figure:
    """Plot factor leaderboard as bar chart.
    
    Args:
        runs_data: List of run dictionaries with metrics
        title: Plot title
    
    Returns:
        Plotly figure
    """
    # Sort by Sharpe
    sorted_runs = sorted(runs_data, key=lambda x: x.get('sharpe', 0), reverse=True)
    
    factor_names = [r.get('factor_name', f"Factor {r.get('run_id', '?')}") for r in sorted_runs[:10]]
    sharpes = [r.get('sharpe', 0) for r in sorted_runs[:10]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=factor_names,
        y=sharpes,
        marker_color='steelblue',
        text=[f"{s:.2f}" for s in sharpes],
        textposition='outside'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Factor",
        yaxis_title="Sharpe Ratio",
        template='plotly_white',
        xaxis=dict(tickangle=-45)
    )
    
    return fig

