"""Plotting utilities for equity curves, IC charts, regime heatmaps, drawdown plots."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from typing import Optional, Dict, Any, List
from pathlib import Path

# Optional plotly imports
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


def _pct(x, _=None):
    """Format value as percentage."""
    return f"{100*x:.2f}%"


def compute_drawdown(equity: pd.Series) -> pd.Series:
    """Compute drawdown from equity curve.
    
    Args:
        equity: Equity curve series
    
    Returns:
        Drawdown series (negative values)
    """
    peak = equity.cummax()
    return (equity / peak - 1.0).fillna(0.0)


def plot_equity_curve_3panel(
    equity: pd.Series,
    benchmark: Optional[pd.Series] = None,
    turnover: Optional[pd.Series] = None,
    meta: Optional[Dict[str, str]] = None,
    out_path: Optional[Path] = None,
    oos_start: Optional[pd.Timestamp] = None
) -> Optional[Path]:
    """Render 3-panel equity curve chart matching blueprint specification.
    
    Creates a publication-quality chart with:
    - Panel 1: Equity curve vs benchmark with info box
    - Panel 2: Drawdown
    - Panel 3: Turnover
    
    Args:
        equity: Equity curve series (indexed by date)
        benchmark: Optional benchmark equity curve
        turnover: Optional turnover series
        meta: Metadata dictionary for info box (strategy_name, period, metrics, etc.)
        out_path: Output path for PNG file
        oos_start: Out-of-sample start date (marked with dashed vertical line)
    
    Returns:
        Path to saved chart, or None if out_path not provided
    """
    if meta is None:
        meta = {}
    
    # Sort and prepare data
    equity = equity.sort_index()
    dd = compute_drawdown(equity)
    
    if benchmark is not None:
        benchmark = benchmark.reindex_like(equity).ffill().bfill()
    
    if turnover is None:
        # Create dummy turnover if not provided
        turnover = pd.Series(0.0, index=equity.index)
    else:
        turnover = turnover.reindex_like(equity).fillna(0.0)
    
    # Create figure with 3 panels
    fig, axes = plt.subplots(
        3, 1,
        figsize=(11.5, 6.5),
        sharex=True,
        gridspec_kw={'height_ratios': [2.2, 1, 1]}
    )
    ax1, ax2, ax3 = axes
    
    # Panel 1: Equity curve
    ax1.plot(equity.index, equity.values, lw=2.0, alpha=0.95, label='Strategy')
    ax1.fill_between(equity.index, 1.0, equity.values, alpha=0.2)
    
    if benchmark is not None:
        ax1.plot(benchmark.index, benchmark.values, ls='--', lw=1.5, alpha=0.7, label='Benchmark')
    
    if oos_start is not None:
        ax1.axvline(oos_start, ls='--', lw=1.0, color='red', alpha=0.5, label='OOS Start')
    
    ax1.set_title(f"Equity Curve ({meta.get('strategy_name', 'Strategy')})")
    ax1.set_ylabel("Equity Value")
    ax1.grid(alpha=0.25)
    ax1.legend(loc='upper left', fontsize=8)
    
    # Info box
    text = (
        f"Strategy: {meta.get('strategy_name', 'N/A')}\n"
        f"Period: {meta.get('period', 'N/A')}\n"
        f"Total Return: {meta.get('total_return', 'N/A')}\n"
        f"Annual Return: {meta.get('annual_return', 'N/A')}\n"
        f"Sharpe Ratio: {meta.get('sharpe', 'N/A')}\n"
        f"PSR: {meta.get('psr', 'N/A')}\n"
        f"Sortino Ratio: {meta.get('sortino', 'N/A')}\n"
        f"Calmar Ratio: {meta.get('calmar', 'N/A')}\n"
        f"Linearity: {meta.get('linearity', 'N/A')}\n"
        f"Max Drawdown: {meta.get('maxdd', 'N/A')}\n"
        f"VaR 95%: {meta.get('var95', 'N/A')}\n"
        f"CVaR: {meta.get('cvar', 'N/A')}\n"
        f"Avg. Annual Turnover: {meta.get('avg_turnover', 'N/A')}"
    )
    
    ax1.text(
        0.01, 0.99, text,
        transform=ax1.transAxes,
        va='top', ha='left',
        fontsize=9,
        bbox=dict(boxstyle='round', alpha=0.08, pad=0.45, facecolor='white')
    )
    
    # Panel 2: Drawdown
    ax2.fill_between(dd.index, dd.values, 0, where=dd.values<0, alpha=0.45, color='red')
    ax2.plot(dd.index, dd.values, lw=1.0, color='darkred', alpha=0.7)
    ax2.set_ylabel('Drawdown')
    ax2.yaxis.set_major_formatter(FuncFormatter(_pct))
    ax2.grid(alpha=0.25)
    ax2.axhline(0, color='black', lw=0.5, alpha=0.3)
    
    # Panel 3: Turnover
    ax3.plot(turnover.index, turnover.values, lw=1.2, color='steelblue')
    ax3.set_ylabel('Turnover')
    ax3.yaxis.set_major_formatter(FuncFormatter(_pct))
    ax3.set_xlabel('Date')
    ax3.grid(alpha=0.25)
    
    # Tight layout and save
    fig.tight_layout()
    
    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=180, bbox_inches='tight')
        plt.close(fig)
        return out_path
    else:
        return None


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

