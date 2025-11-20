"""Validation: leakage detection, sample size checks, stability tests, regime robustness."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import yaml

from .metrics import information_coefficient, sharpe, max_drawdown
from ..factors.primitives import REGIME_VOLATILITY, REGIME_TREND


def load_constraints_config(config_path: Optional[Path] = None) -> Dict:
    """Load constraints configuration."""
    if config_path is None:
        config_path = Path("configs/constraints.yml")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def check_leakage(
    signals: pd.Series,
    future_returns: pd.Series,
    threshold: float = 0.1
) -> Tuple[bool, List[str]]:
    """Check for data leakage (correlation with future returns).
    
    Args:
        signals: Factor signals
        future_returns: Future returns (aligned with signals)
        threshold: Maximum allowed correlation
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    # Align series
    aligned = pd.DataFrame({
        'signals': signals,
        'future_returns': future_returns
    }).dropna()
    
    if len(aligned) < 10:
        return False, ["Insufficient data for leakage check"]
    
    # Calculate correlation
    correlation = aligned['signals'].corr(aligned['future_returns'])
    
    if abs(correlation) > threshold:
        issues.append(
            f"Leakage detected: correlation with future returns = {correlation:.4f} "
            f"(threshold = {threshold})"
        )
        return False, issues
    
    return True, []


def check_sample_size(
    signals_df: pd.DataFrame,
    min_history_days: int = 800,
    min_tickers: int = 50
) -> Tuple[bool, List[str]]:
    """Check sample size requirements.
    
    Args:
        signals_df: Signals DataFrame
        min_history_days: Minimum number of days
        min_tickers: Minimum number of tickers
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    n_days = len(signals_df)
    n_tickers = len(signals_df.columns)
    
    if n_days < min_history_days:
        issues.append(
            f"Insufficient history: {n_days} days < {min_history_days} required"
        )
    
    if n_tickers < min_tickers:
        issues.append(
            f"Insufficient tickers: {n_tickers} < {min_tickers} required"
        )
    
    return len(issues) == 0, issues


def check_stability(
    returns: pd.Series,
    rolling_period: int = 252,
    min_periods: int = 4,
    max_sharpe_drawdown_pct: float = 50.0
) -> Tuple[bool, List[str]]:
    """Check stability of performance metrics.
    
    Args:
        returns: Return series
        rolling_period: Rolling window size (days)
        min_periods: Minimum number of rolling periods that must pass
        max_sharpe_drawdown_pct: Maximum allowed Sharpe drawdown (%)
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    if len(returns) < rolling_period * min_periods:
        issues.append(f"Insufficient data for stability check: {len(returns)} < {rolling_period * min_periods}")
        return False, issues
    
    # Calculate rolling Sharpe
    rolling_sharpes = []
    for i in range(rolling_period, len(returns), rolling_period):
        window_returns = returns.iloc[i-rolling_period:i]
        window_sharpe = sharpe(window_returns)
        rolling_sharpes.append(window_sharpe)
    
    if len(rolling_sharpes) < min_periods:
        issues.append(f"Insufficient rolling periods: {len(rolling_sharpes)} < {min_periods}")
        return False, issues
    
    sharpe_series = pd.Series(rolling_sharpes)
    max_sharpe = sharpe_series.max()
    min_sharpe = sharpe_series.min()
    
    if max_sharpe > 0:
        sharpe_drawdown_pct = ((max_sharpe - min_sharpe) / max_sharpe) * 100
        if sharpe_drawdown_pct > max_sharpe_drawdown_pct:
            issues.append(
                f"Unstable Sharpe: drawdown of {sharpe_drawdown_pct:.1f}% "
                f"(max allowed: {max_sharpe_drawdown_pct}%)"
            )
    
    # Check IC stability
    # (This would require IC series, simplified here)
    
    return len(issues) == 0, issues


def check_ic_stability(
    ic_series: pd.Series,
    threshold: float = 0.03
) -> Tuple[bool, List[str]]:
    """Check IC stability.
    
    Args:
        ic_series: Series of IC values over time
        threshold: Minimum IC threshold
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    if len(ic_series) == 0:
        issues.append("No IC data available")
        return False, issues
    
    min_ic = ic_series.min()
    if min_ic < threshold:
        issues.append(
            f"IC drops below threshold: min IC = {min_ic:.4f} < {threshold}"
        )
    
    return len(issues) == 0, issues


def check_regime_robustness(
    returns: pd.Series,
    prices: pd.Series,
    required_regimes: List[str] = None,
    min_regime_samples: int = 63,
    min_regime_sharpe: float = 0.5
) -> Tuple[bool, List[str]]:
    """Check performance across different regimes.
    
    Args:
        returns: Return series
        prices: Price series (for regime classification)
        required_regimes: List of required regimes
        min_regime_samples: Minimum samples per regime
        min_regime_sharpe: Minimum Sharpe per regime
    
    Returns:
        (is_valid, list_of_issues)
    """
    if required_regimes is None:
        required_regimes = ["high_vol", "low_vol", "bull", "bear"]
    
    issues = []
    
    # Classify volatility regimes
    vol_regimes = REGIME_VOLATILITY(returns, window=21)
    
    # Classify trend regimes
    trend_regimes = REGIME_TREND(prices, short_window=21, long_window=63)
    
    # Combine regimes
    combined_regimes = vol_regimes + "_" + trend_regimes
    
    # Check each required regime
    for regime in required_regimes:
        if regime == "high_vol":
            regime_mask = vol_regimes == "high_vol"
        elif regime == "low_vol":
            regime_mask = vol_regimes == "low_vol"
        elif regime == "bull":
            regime_mask = trend_regimes == "bull"
        elif regime == "bear":
            regime_mask = trend_regimes == "bear"
        else:
            continue
        
        regime_returns = returns[regime_mask]
        
        if len(regime_returns) < min_regime_samples:
            issues.append(
                f"Insufficient samples in {regime} regime: "
                f"{len(regime_returns)} < {min_regime_samples}"
            )
            continue
        
        regime_sharpe = sharpe(regime_returns)
        if regime_sharpe < min_regime_sharpe:
            issues.append(
                f"Low Sharpe in {regime} regime: {regime_sharpe:.2f} < {min_regime_sharpe}"
            )
    
    return len(issues) == 0, issues


def check_turnover(
    positions: pd.DataFrame,
    max_monthly_turnover_pct: float = 250.0
) -> Tuple[bool, List[str]]:
    """Check turnover constraints.
    
    Args:
        positions: Position weights DataFrame
        max_monthly_turnover_pct: Maximum monthly turnover percentage
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    if len(positions) < 2:
        return True, []
    
    # Calculate daily turnover
    position_changes = positions.diff().abs()
    daily_turnover = position_changes.sum(axis=1)
    
    # Monthly turnover (approximate: 21 trading days)
    monthly_turnover_pct = daily_turnover.mean() * 21 * 100
    
    if monthly_turnover_pct > max_monthly_turnover_pct:
        issues.append(
            f"Turnover too high: {monthly_turnover_pct:.1f}% > {max_monthly_turnover_pct}%"
        )
    
    return len(issues) == 0, issues


def validate_run(
    signals_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    positions_df: pd.DataFrame,
    metrics: Dict[str, Any],
    constraints_config: Optional[Dict] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Comprehensive validation of a backtest run.
    
    Args:
        signals_df: Factor signals DataFrame
        returns_df: Returns DataFrame
        prices_df: Prices DataFrame
        positions_df: Positions DataFrame
        metrics: Calculated metrics
        constraints_config: Constraints configuration
    
    Returns:
        (is_valid, list_of_issues)
        Each issue is a dict with 'type', 'severity', 'detail'
    """
    if constraints_config is None:
        constraints_config = load_constraints_config()
    
    issues = []
    
    # Sample size check
    sample_config = constraints_config.get('sample_size', {})
    is_valid, sample_issues = check_sample_size(
        signals_df,
        min_history_days=sample_config.get('min_history_days', 800),
        min_tickers=sample_config.get('min_tickers', 50)
    )
    for issue in sample_issues:
        issues.append({
            'type': 'sample_size',
            'severity': 'error',
            'detail': issue
        })
    
    # Leakage check
    leakage_config = constraints_config.get('leakage_detection', {})
    if leakage_config.get('enabled', True):
        # Check correlation with future returns
        if len(signals_df) > 10:
            avg_signals = signals_df.mean(axis=1)
            future_returns = returns_df.mean(axis=1).shift(-1)
            is_valid, leakage_issues = check_leakage(
                avg_signals,
                future_returns,
                threshold=leakage_config.get('max_future_correlation', 0.1)
            )
            for issue in leakage_issues:
                issues.append({
                    'type': 'leakage_detected',
                    'severity': 'critical',
                    'detail': issue
                })
    
    # Stability check
    if 'returns' in metrics or hasattr(metrics, 'returns'):
        returns = metrics.get('returns') if isinstance(metrics, dict) else None
        if returns is None and hasattr(metrics, 'returns'):
            returns = metrics.returns
        
        if returns is not None and len(returns) > 0:
            stability_config = constraints_config.get('stability', {})
            is_valid, stability_issues = check_stability(
                returns,
                rolling_period=stability_config.get('rolling_period_days', 252),
                min_periods=stability_config.get('min_rolling_sharpe_periods', 4),
                max_sharpe_drawdown_pct=stability_config.get('max_sharpe_drawdown_pct', 50)
            )
            for issue in stability_issues:
                issues.append({
                    'type': 'unstable_performance',
                    'severity': 'warning',
                    'detail': issue
                })
    
    # Turnover check
    turnover_config = constraints_config.get('turnover', {})
    is_valid, turnover_issues = check_turnover(
        positions_df,
        max_monthly_turnover_pct=turnover_config.get('max_monthly_turnover_pct', 250.0)
    )
    for issue in turnover_issues:
        issues.append({
            'type': 'high_turnover',
            'severity': 'warning',
            'detail': issue
        })
    
    # Regime robustness (if prices available)
    if prices_df is not None and len(prices_df) > 0:
        regime_config = constraints_config.get('regime_robustness', {})
        if regime_config.get('enabled', True):
            avg_prices = prices_df.mean(axis=1)
            avg_returns = returns_df.mean(axis=1)
            is_valid, regime_issues = check_regime_robustness(
                avg_returns,
                avg_prices,
                required_regimes=regime_config.get('required_regimes', ["high_vol", "low_vol", "bull", "bear"]),
                min_regime_samples=regime_config.get('min_regime_samples', 63),
                min_regime_sharpe=regime_config.get('min_regime_sharpe', 0.5)
            )
            for issue in regime_issues:
                issues.append({
                    'type': 'regime_brittleness',
                    'severity': 'warning',
                    'detail': issue
                })
    
    # Target checks
    targets_config = constraints_config.get('targets', {})
    if metrics.get('sharpe', 0) < targets_config.get('min_sharpe', 1.0):
        issues.append({
            'type': 'below_target_sharpe',
            'severity': 'warning',
            'detail': f"Sharpe {metrics.get('sharpe', 0):.2f} < {targets_config.get('min_sharpe', 1.0)}"
        })
    
    if abs(metrics.get('maxdd', 0)) > targets_config.get('max_maxdd', 0.35):
        issues.append({
            'type': 'exceeds_max_drawdown',
            'severity': 'error',
            'detail': f"MaxDD {abs(metrics.get('maxdd', 0)):.2%} > {targets_config.get('max_maxdd', 0.35):.2%}"
        })
    
    if metrics.get('avg_ic', 0) < targets_config.get('min_avg_ic', 0.05):
        issues.append({
            'type': 'below_target_ic',
            'severity': 'warning',
            'detail': f"Avg IC {metrics.get('avg_ic', 0):.4f} < {targets_config.get('min_avg_ic', 0.05)}"
        })
    
    # Determine overall validity
    critical_issues = [i for i in issues if i['severity'] in ['error', 'critical']]
    is_valid = len(critical_issues) == 0
    
    return is_valid, issues

