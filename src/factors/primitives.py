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


# ============================================================================
# WorldQuant-inspired primitives
# ============================================================================

def DELTA(series: pd.Series, periods: int = 1) -> pd.Series:
    """Calculate first difference (delta).
    
    Args:
        series: Input series
        periods: Number of periods to difference (default 1)
    
    Returns:
        Differenced series
    """
    return series.diff(periods)


def DECAY_LINEAR(series: pd.Series, window: int) -> pd.Series:
    """Linear decay function (weighted moving average with linear weights).
    
    More recent values get higher weights. Weights decrease linearly.
    
    Args:
        series: Input series
        window: Decay window size
    
    Returns:
        Linearly decayed series
    """
    weights = np.arange(1, window + 1)
    weights = weights / weights.sum()  # Normalize
    
    result = pd.Series(index=series.index, dtype=float)
    for i in range(window - 1, len(series)):
        window_data = series.iloc[i - window + 1:i + 1]
        if len(window_data) == window:
            result.iloc[i] = (window_data * weights[::-1]).sum()
    
    return result


def TS_RANK(series: pd.Series, window: int) -> pd.Series:
    """Time-series rank.
    
    Ranks values within a rolling window (1 = highest, 0 = lowest).
    
    Args:
        series: Input series
        window: Rolling window size
    
    Returns:
        Time-series rank (0 to 1, where 1 is highest)
    """
    def rank_func(x):
        if len(x) == 0:
            return np.nan
        return pd.Series(x).rank(pct=True).iloc[-1]
    
    return series.rolling(window=window).apply(rank_func, raw=True)


def TS_ARGMAX(series: pd.Series, window: int) -> pd.Series:
    """Time-series argument maximum.
    
    Returns the number of periods since the maximum value in the window.
    
    Args:
        series: Input series
        window: Rolling window size
    
    Returns:
        Periods since maximum (0 = current period is max)
    """
    result = pd.Series(index=series.index, dtype=float)
    for i in range(window - 1, len(series)):
        window_data = series.iloc[i - window + 1:i + 1]
        if len(window_data) > 0:
            max_idx = window_data.idxmax()
            periods_ago = i - series.index.get_loc(max_idx)
            result.iloc[i] = periods_ago
    
    return result


def TS_ARGMIN(series: pd.Series, window: int) -> pd.Series:
    """Time-series argument minimum.
    
    Returns the number of periods since the minimum value in the window.
    
    Args:
        series: Input series
        window: Rolling window size
    
    Returns:
        Periods since minimum (0 = current period is min)
    """
    result = pd.Series(index=series.index, dtype=float)
    for i in range(window - 1, len(series)):
        window_data = series.iloc[i - window + 1:i + 1]
        if len(window_data) > 0:
            min_idx = window_data.idxmin()
            periods_ago = i - series.index.get_loc(min_idx)
            result.iloc[i] = periods_ago
    
    return result


def CORRELATION(series1: pd.Series, series2: pd.Series, window: int) -> pd.Series:
    """Rolling correlation between two series.
    
    Args:
        series1: First series
        series2: Second series
        window: Rolling window size
    
    Returns:
        Rolling correlation series
    """
    return series1.rolling(window=window).corr(series2)


def COVARIANCE(series1: pd.Series, series2: pd.Series, window: int) -> pd.Series:
    """Rolling covariance between two series.
    
    Args:
        series1: First series
        series2: Second series
        window: Rolling window size
    
    Returns:
        Rolling covariance series
    """
    return series1.rolling(window=window).cov(series2)


def VWAP(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Volume-weighted average price.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
    
    Returns:
        VWAP series
    """
    typical_price = (high + low + close) / 3
    return (typical_price * volume).rolling(window=len(typical_price)).sum() / volume.rolling(window=len(volume)).sum()


def ADV(volume: pd.Series, window: int = 20) -> pd.Series:
    """Average daily volume.
    
    Args:
        volume: Volume series
        window: Rolling window size (default 20 days)
    
    Returns:
        Average daily volume series
    """
    return volume.rolling(window=window).mean()


def INDNEUTRALIZE(
    series: pd.Series,
    industry_map: Optional[pd.Series] = None,
    method: str = "demean"
) -> pd.Series:
    """Industry neutralization.
    
    Removes industry-level effects from a series.
    
    Args:
        series: Input series (can be DataFrame for cross-sectional)
        industry_map: Series mapping tickers to industries (if None, uses simple demean)
        method: Neutralization method ('demean' or 'zscore')
    
    Returns:
        Industry-neutralized series
    """
    if isinstance(series, pd.DataFrame):
        # Cross-sectional neutralization
        if industry_map is None:
            # Simple cross-sectional demean
            return series.sub(series.mean(axis=1), axis=0)
        else:
            # Group by industry and neutralize
            result = series.copy()
            for industry in industry_map.unique():
                industry_tickers = industry_map[industry_map == industry].index
                industry_data = series[industry_tickers]
                if method == "demean":
                    result[industry_tickers] = industry_data.sub(industry_data.mean(axis=1), axis=0)
                else:  # zscore
                    mean = industry_data.mean(axis=1)
                    std = industry_data.std(axis=1)
                    result[industry_tickers] = industry_data.sub(mean, axis=0).div(std.replace(0, np.nan), axis=0)
            return result
    else:
        # Time-series: simple demean (would need industry info for proper neutralization)
        if method == "demean":
            return series - series.mean()
        else:
            return (series - series.mean()) / series.std()


def SCALE(series: pd.Series, scale: float = 1.0) -> pd.Series:
    """Scale a series.
    
    Args:
        series: Input series
        scale: Scaling factor
    
    Returns:
        Scaled series
    """
    return series * scale


def INDCLASS_NEUTRALIZE(
    series: pd.DataFrame,
    indclass: pd.Series,
    method: str = "demean"
) -> pd.DataFrame:
    """Industry class neutralization (wrapper for INDNEUTRALIZE).
    
    Args:
        series: Cross-sectional data (DataFrame)
        indclass: Industry classification series
        method: Neutralization method
    
    Returns:
        Industry-neutralized DataFrame
    """
    return INDNEUTRALIZE(series, industry_map=indclass, method=method)


def SUM(series: pd.Series, window: int) -> pd.Series:
    """Rolling sum.
    
    Args:
        series: Input series
        window: Rolling window size
    
    Returns:
        Rolling sum series
    """
    return series.rolling(window=window).sum()


def PRODUCT(series: pd.Series, window: int) -> pd.Series:
    """Rolling product.
    
    Args:
        series: Input series
        window: Rolling window size
    
    Returns:
        Rolling product series
    """
    return series.rolling(window=window).apply(lambda x: np.prod(x), raw=True)


def SIGN(series: pd.Series) -> pd.Series:
    """Sign function (-1, 0, or 1).
    
    Args:
        series: Input series
    
    Returns:
        Sign series
    """
    return np.sign(series)


def POWER(series: pd.Series, exponent: float) -> pd.Series:
    """Power function.
    
    Args:
        series: Input series
        exponent: Exponent
    
    Returns:
        Series raised to power
    """
    return series ** exponent


def LOG(series: pd.Series) -> pd.Series:
    """Natural logarithm.
    
    Args:
        series: Input series
    
    Returns:
        Log series
    """
    return np.log(series.clip(lower=1e-10))  # Avoid log(0)


def ABS(series: pd.Series) -> pd.Series:
    """Absolute value.
    
    Args:
        series: Input series
    
    Returns:
        Absolute value series
    """
    return series.abs()


def MAX(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """Element-wise maximum.
    
    Args:
        series1: First series
        series2: Second series
    
    Returns:
        Element-wise maximum
    """
    return pd.concat([series1, series2], axis=1).max(axis=1)


def MIN(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """Element-wise minimum.
    
    Args:
        series1: First series
        series2: Second series
    
    Returns:
        Element-wise minimum
    """
    return pd.concat([series1, series2], axis=1).min(axis=1)


# Dictionary mapping function names to implementations
PRIMITIVES = {
    # Basic operations
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
    
    # WorldQuant-inspired primitives
    'DELTA': DELTA,
    'DECAY_LINEAR': DECAY_LINEAR,
    'TS_RANK': TS_RANK,
    'TS_ARGMAX': TS_ARGMAX,
    'TS_ARGMIN': TS_ARGMIN,
    'CORRELATION': CORRELATION,
    'COVARIANCE': COVARIANCE,
    'VWAP': VWAP,
    'ADV': ADV,
    'INDNEUTRALIZE': INDNEUTRALIZE,
    'INDCLASS_NEUTRALIZE': INDCLASS_NEUTRALIZE,
    'SCALE': SCALE,
    'SUM': SUM,
    'PRODUCT': PRODUCT,
    'SIGN': SIGN,
    'POWER': POWER,
    'LOG': LOG,
    'ABS': ABS,
    'MAX': MAX,
    'MIN': MIN,
}

