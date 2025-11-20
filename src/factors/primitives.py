"""Factor computation primitives (RET_LAG, ROLL_STD, VOL_TARGET, etc.)."""

import numpy as np
import pandas as pd
from typing import Union, Optional, Tuple


def RET_LAG(lag: int, period: int, prices: pd.Series) -> pd.Series:
    """Calculate lagged return over a period.
    
    Args:
        lag: Number of periods to lag (must be >= 1)
        period: Number of periods to calculate return over
        prices: Price series (typically close prices)
    
    Returns:
        Lagged return series
    """
    if lag < 1:
        raise ValueError("lag must be >= 1 to avoid lookahead")
    
    # Calculate return over period, then lag
    returns = prices.pct_change(period)
    return returns.shift(lag)


def RET_D(prices: pd.Series) -> pd.Series:
    """Daily return."""
    return prices.pct_change(1)


def ROLL_STD(series: pd.Series, window: int) -> pd.Series:
    """Rolling standard deviation.
    
    Args:
        series: Input series (typically returns)
        window: Rolling window size
    
    Returns:
        Rolling standard deviation series
    """
    return series.rolling(window=window).std()


def ROLL_MEAN(series: pd.Series, window: int) -> pd.Series:
    """Rolling mean."""
    return series.rolling(window=window).mean()


def ROLL_MAX(series: pd.Series, window: int) -> pd.Series:
    """Rolling maximum."""
    return series.rolling(window=window).max()


def ROLL_MIN(series: pd.Series, window: int) -> pd.Series:
    """Rolling minimum."""
    return series.rolling(window=window).min()


def VOL_TARGET(ann_vol: float, using: Union[str, pd.Series], prices: Optional[pd.Series] = None) -> pd.Series:
    """Volatility targeting normalization.
    
    Args:
        ann_vol: Target annualized volatility (e.g., 0.15 for 15%)
        using: Either 'vol' (to use a volatility series) or a volatility series
        prices: Optional price series if using='prices'
    
    Returns:
        Volatility-targeted series (typically returns scaled to target vol)
    """
    if isinstance(using, str):
        if using == 'vol':
            if prices is None:
                raise ValueError("prices required when using='vol'")
            # Calculate realized volatility
            vol = ROLL_STD(RET_D(prices), 21) * np.sqrt(252)  # Annualized
        else:
            raise ValueError(f"Unknown 'using' value: {using}")
    else:
        vol = using
    
    # Avoid division by zero
    vol = vol.replace(0, np.nan)
    
    # Scale to target volatility
    scaling = ann_vol / vol
    return scaling


def ZSCORE(series: pd.Series, window: int) -> pd.Series:
    """Z-score normalization (rolling).
    
    Args:
        series: Input series
        window: Rolling window for mean/std calculation
    
    Returns:
        Z-scored series: (x - mean) / std
    """
    rolling_mean = ROLL_MEAN(series, window)
    rolling_std = ROLL_STD(series, window)
    
    # Avoid division by zero
    rolling_std = rolling_std.replace(0, np.nan)
    
    return (series - rolling_mean) / rolling_std


def CORRELATION_DECAY(series1: pd.Series, series2: pd.Series, window: int, decay: float = 0.5) -> pd.Series:
    """Correlation decay metric.
    
    Measures how correlation decays over time, useful for regime detection.
    
    Args:
        series1: First series
        series2: Second series
        window: Rolling window for correlation
        decay: Decay factor (default 0.5)
    
    Returns:
        Correlation decay metric
    """
    rolling_corr = series1.rolling(window=window).corr(series2)
    
    # Apply exponential decay
    decayed = rolling_corr * (decay ** np.arange(len(rolling_corr)))
    
    return decayed


def DRAWDOWN_RECOVERY(prices: pd.Series, window: int = 252) -> pd.Series:
    """Drawdown recovery metric.
    
    Measures how quickly prices recover from drawdowns.
    
    Args:
        prices: Price series
        window: Lookback window for peak calculation
    
    Returns:
        Recovery metric (positive = recovering, negative = still in drawdown)
    """
    # Calculate running maximum
    running_max = prices.rolling(window=window).max()
    
    # Current drawdown
    drawdown = (prices - running_max) / running_max
    
    # Recovery: positive change in drawdown
    recovery = drawdown.diff()
    
    return recovery


def SKEW(series: pd.Series, window: int) -> pd.Series:
    """Rolling skewness."""
    return series.rolling(window=window).skew()


def KURTOSIS(series: pd.Series, window: int) -> pd.Series:
    """Rolling kurtosis."""
    return series.rolling(window=window).kurt()


def RANK(series: pd.Series) -> pd.Series:
    """Cross-sectional rank (0 to 1)."""
    return series.rank(pct=True)


def QUANTILE(series: pd.Series, q: float) -> float:
    """Quantile value."""
    return series.quantile(q)


def REGIME_VOLATILITY(returns: pd.Series, window: int = 21, threshold: float = 0.2) -> pd.Series:
    """Classify volatility regime.
    
    Args:
        returns: Return series
        window: Rolling window for volatility calculation
        threshold: Threshold for high/low volatility (as fraction of median)
    
    Returns:
        Series with values: 'high_vol', 'low_vol', 'normal'
    """
    vol = ROLL_STD(returns, window) * np.sqrt(252)  # Annualized
    median_vol = vol.median()
    
    high_threshold = median_vol * (1 + threshold)
    low_threshold = median_vol * (1 - threshold)
    
    regime = pd.Series('normal', index=returns.index)
    regime[vol > high_threshold] = 'high_vol'
    regime[vol < low_threshold] = 'low_vol'
    
    return regime


def REGIME_TREND(prices: pd.Series, short_window: int = 21, long_window: int = 63) -> pd.Series:
    """Classify trend regime.
    
    Args:
        prices: Price series
        short_window: Short-term moving average window
        long_window: Long-term moving average window
    
    Returns:
        Series with values: 'bull', 'bear', 'neutral'
    """
    short_ma = ROLL_MEAN(prices, short_window)
    long_ma = ROLL_MEAN(prices, long_window)
    
    regime = pd.Series('neutral', index=prices.index)
    regime[short_ma > long_ma] = 'bull'
    regime[short_ma < long_ma] = 'bear'
    
    return regime


# Dictionary mapping function names to implementations
PRIMITIVES = {
    'RET_LAG': RET_LAG,
    'RET_D': RET_D,
    'ROLL_STD': ROLL_STD,
    'ROLL_MEAN': ROLL_MEAN,
    'ROLL_MAX': ROLL_MAX,
    'ROLL_MIN': ROLL_MIN,
    'VOL_TARGET': VOL_TARGET,
    'ZSCORE': ZSCORE,
    'zscore_252': lambda s: ZSCORE(s, 252),
    'zscore_63': lambda s: ZSCORE(s, 63),
    'zscore_21': lambda s: ZSCORE(s, 21),
    'CORRELATION_DECAY': CORRELATION_DECAY,
    'DRAWDOWN_RECOVERY': DRAWDOWN_RECOVERY,
    'SKEW': SKEW,
    'KURTOSIS': KURTOSIS,
    'RANK': RANK,
    'QUANTILE': QUANTILE,
    'REGIME_VOLATILITY': REGIME_VOLATILITY,
    'REGIME_TREND': REGIME_TREND,
}

