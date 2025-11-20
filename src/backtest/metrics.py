"""Performance metrics calculation: Sharpe, MaxDD, IC, IR, turnover, hit rate."""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any
from scipy import stats


def sharpe(returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    """Calculate Sharpe ratio.
    
    Args:
        returns: Return series
        rf: Risk-free rate (annualized)
        periods_per_year: Number of periods per year (252 for daily)
    
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    excess_returns = returns - (rf / periods_per_year)
    ann_return = excess_returns.mean() * periods_per_year
    ann_vol = returns.std() * np.sqrt(periods_per_year)
    
    if ann_vol == 0:
        return 0.0
    
    return ann_return / ann_vol


def max_drawdown(equity_curve: pd.Series) -> float:
    """Calculate maximum drawdown.
    
    Args:
        equity_curve: Cumulative equity curve (starting at 1.0)
    
    Returns:
        Maximum drawdown (negative value, e.g., -0.35 for 35% drawdown)
    """
    if len(equity_curve) == 0:
        return 0.0
    
    running_max = equity_curve.expanding().max()
    drawdown = (equity_curve - running_max) / running_max
    
    return drawdown.min()


def information_coefficient(
    scores: pd.Series,
    next_period_returns: pd.Series,
    method: str = "spearman"
) -> float:
    """Calculate Information Coefficient (IC).
    
    Args:
        scores: Factor scores/predictions
        next_period_returns: Next period returns (aligned with scores)
        method: Correlation method ('spearman' or 'pearson')
    
    Returns:
        IC value
    """
    # Align series
    aligned = pd.DataFrame({
        'scores': scores,
        'returns': next_period_returns
    }).dropna()
    
    if len(aligned) < 2:
        return 0.0
    
    if method == "spearman":
        ic, _ = stats.spearmanr(aligned['scores'], aligned['returns'])
    else:
        ic, _ = stats.pearsonr(aligned['scores'], aligned['returns'])
    
    return ic if not np.isnan(ic) else 0.0


def information_ratio(ic_series: pd.Series) -> float:
    """Calculate Information Ratio (mean IC / std IC).
    
    Args:
        ic_series: Series of IC values over time
    
    Returns:
        Information Ratio
    """
    if len(ic_series) == 0 or ic_series.std() == 0:
        return 0.0
    
    return ic_series.mean() / ic_series.std()


def turnover(positions: pd.DataFrame) -> float:
    """Calculate portfolio turnover.
    
    Args:
        positions: DataFrame with columns as tickers, rows as dates, values as position weights
    
    Returns:
        Average daily turnover (as fraction)
    """
    if len(positions) < 2:
        return 0.0
    
    # Calculate change in positions
    position_changes = positions.diff().abs()
    
    # Sum across all positions for each day
    daily_turnover = position_changes.sum(axis=1)
    
    # Average daily turnover
    avg_turnover = daily_turnover.mean()
    
    return avg_turnover


def monthly_turnover(positions: pd.DataFrame) -> float:
    """Calculate monthly turnover percentage.
    
    Args:
        positions: DataFrame with columns as tickers, rows as dates
    
    Returns:
        Monthly turnover as percentage (e.g., 250.0 for 250%)
    """
    daily_turnover = turnover(positions)
    monthly_turnover_pct = daily_turnover * 21 * 100  # ~21 trading days per month
    
    return monthly_turnover_pct


def hit_rate(returns: pd.Series) -> float:
    """Calculate hit rate (fraction of positive returns).
    
    Args:
        returns: Return series
    
    Returns:
        Hit rate (0 to 1)
    """
    if len(returns) == 0:
        return 0.0
    
    positive_returns = (returns > 0).sum()
    return positive_returns / len(returns)


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate annualized return."""
    if len(returns) == 0:
        return 0.0
    
    return returns.mean() * periods_per_year


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate annualized volatility."""
    if len(returns) < 2:
        return 0.0
    
    return returns.std() * np.sqrt(periods_per_year)


def skewness(returns: pd.Series) -> float:
    """Calculate skewness."""
    if len(returns) < 3:
        return 0.0
    
    return returns.skew()


def kurtosis(returns: pd.Series) -> float:
    """Calculate kurtosis."""
    if len(returns) < 4:
        return 0.0
    
    return returns.kurtosis()


def drawdown_profile(equity_curve: pd.Series) -> Dict[str, Any]:
    """Calculate detailed drawdown profile.
    
    Returns:
        Dictionary with:
        - max_dd: Maximum drawdown
        - avg_dd: Average drawdown
        - dd_duration: Average drawdown duration (days)
        - recovery_time: Average recovery time (days)
    """
    if len(equity_curve) == 0:
        return {
            'max_dd': 0.0,
            'avg_dd': 0.0,
            'dd_duration': 0.0,
            'recovery_time': 0.0
        }
    
    running_max = equity_curve.expanding().max()
    drawdown = (equity_curve - running_max) / running_max
    
    # Find drawdown periods
    in_drawdown = drawdown < 0
    drawdown_periods = []
    recovery_times = []
    
    start_idx = None
    peak_idx = None
    
    for i, is_dd in enumerate(in_drawdown):
        if is_dd and start_idx is None:
            start_idx = i
            peak_idx = equity_curve[:i].idxmax() if i > 0 else None
        elif not is_dd and start_idx is not None:
            # Drawdown ended
            dd_duration = i - start_idx
            drawdown_periods.append(dd_duration)
            
            if peak_idx is not None:
                recovery_idx = equity_curve[start_idx:].idxmax()
                recovery_time = (equity_curve[start_idx:] >= equity_curve[peak_idx]).idxmax() - start_idx
                recovery_times.append(recovery_time)
            
            start_idx = None
            peak_idx = None
    
    return {
        'max_dd': drawdown.min(),
        'avg_dd': drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0.0,
        'dd_duration': np.mean(drawdown_periods) if drawdown_periods else 0.0,
        'recovery_time': np.mean(recovery_times) if recovery_times else 0.0
    }


def calculate_all_metrics(
    returns: pd.Series,
    equity_curve: Optional[pd.Series] = None,
    positions: Optional[pd.DataFrame] = None,
    scores: Optional[pd.Series] = None,
    next_returns: Optional[pd.Series] = None,
    rf: float = 0.0,
    periods_per_year: int = 252
) -> Dict[str, Any]:
    """Calculate all available metrics.
    
    Args:
        returns: Portfolio return series
        equity_curve: Cumulative equity curve (if None, computed from returns)
        positions: Position weights DataFrame (for turnover)
        scores: Factor scores (for IC calculation)
        next_returns: Next period returns (for IC calculation)
        rf: Risk-free rate
        periods_per_year: Periods per year
    
    Returns:
        Dictionary of all metrics
    """
    metrics = {}
    
    # Basic return metrics
    metrics['ann_ret'] = annualized_return(returns, periods_per_year)
    metrics['ann_vol'] = annualized_volatility(returns, periods_per_year)
    metrics['sharpe'] = sharpe(returns, rf, periods_per_year)
    metrics['skew'] = skewness(returns)
    metrics['kurt'] = kurtosis(returns)
    metrics['hit_rate'] = hit_rate(returns)
    
    # Drawdown metrics
    if equity_curve is None:
        equity_curve = (1 + returns).cumprod()
    
    metrics['maxdd'] = max_drawdown(equity_curve)
    dd_profile = drawdown_profile(equity_curve)
    metrics.update(dd_profile)
    
    # Turnover
    if positions is not None:
        metrics['turnover'] = turnover(positions)
        metrics['turnover_monthly'] = monthly_turnover(positions)
    else:
        metrics['turnover'] = 0.0
        metrics['turnover_monthly'] = 0.0
    
    # IC metrics
    if scores is not None and next_returns is not None:
        ic = information_coefficient(scores, next_returns)
        metrics['avg_ic'] = ic
        
        # Calculate rolling IC if we have enough data
        if len(scores) > 21:
            rolling_ic = []
            for i in range(21, len(scores)):
                window_scores = scores.iloc[i-21:i]
                window_returns = next_returns.iloc[i-21:i]
                window_ic = information_coefficient(window_scores, window_returns)
                rolling_ic.append(window_ic)
            
            ic_series = pd.Series(rolling_ic)
            metrics['ic_std'] = ic_series.std()
            metrics['ir'] = information_ratio(ic_series) if ic_series.std() > 0 else 0.0
        else:
            metrics['ic_std'] = 0.0
            metrics['ir'] = 0.0
    else:
        metrics['avg_ic'] = 0.0
        metrics['ic_std'] = 0.0
        metrics['ir'] = 0.0
    
    return metrics

