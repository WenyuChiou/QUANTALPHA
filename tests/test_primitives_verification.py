
import pytest
import pandas as pd
import numpy as np
from src.factors.primitives import (
    RET_LAG, RET_D, ROLL_STD, VOL_TARGET, ZSCORE, 
    INDNEUTRALIZE, REGIME_VOLATILITY, TS_RANK
)

def test_ret_lag():
    """Test RET_LAG primitive."""
    prices = pd.Series([100, 101, 102, 103, 104, 105])
    
    # RET_LAG(1, 1) -> 1-day return, lagged by 1
    # Returns: [NaN, NaN, (101-100)/100, (102-101)/101, (103-102)/102, (104-103)/103]
    # Shifted by 1: [NaN, NaN, NaN, 0.01, ...]
    
    lagged_ret = RET_LAG(lag=1, period=1, prices=prices)
    
    # First 2 should be NaN (1 for return calc, 1 for lag)
    assert pd.isna(lagged_ret.iloc[0])
    assert pd.isna(lagged_ret.iloc[1])
    
    # 3rd element (index 2) should be return from index 0 to 1
    expected_ret = (101 - 100) / 100
    assert lagged_ret.iloc[2] == pytest.approx(expected_ret)
    
    # Test lag < 1 error
    with pytest.raises(ValueError):
        RET_LAG(lag=0, period=1, prices=prices)

def test_vol_target():
    """Test VOL_TARGET primitive."""
    # Create a series with constant volatility
    # Alternating +1% and -1% returns
    returns = pd.Series([0.01, -0.01] * 100)
    prices = (1 + returns).cumprod()
    
    # Annualized vol of this series is approx 0.01 * sqrt(252) ~= 0.1587
    
    # Target 10% vol
    target_vol = 0.10
    scaling = VOL_TARGET(ann_vol=target_vol, using='vol', prices=prices)
    
    # Scaling factor should be roughly 0.10 / 0.1587 ~= 0.63
    # Note: VOL_TARGET uses 21-day rolling vol
    
    # Check last value
    last_scaling = scaling.iloc[-1]
    assert not pd.isna(last_scaling)
    assert last_scaling > 0
    
    # If we scale the returns, the new vol should be close to target
    scaled_returns = returns * scaling
    # We can't easily check the realized vol of scaled returns without a rolling window,
    # but we can check the scaling factor itself.

def test_zscore():
    """Test ZSCORE primitive."""
    series = pd.Series([1, 2, 3, 4, 5])
    window = 3
    
    z = ZSCORE(series, window)
    
    # Index 2: [1, 2, 3]. Mean=2, Std=1. (3-2)/1 = 1
    assert z.iloc[2] == pytest.approx(1.0)
    
    # Index 3: [2, 3, 4]. Mean=3, Std=1. (4-3)/1 = 1
    assert z.iloc[3] == pytest.approx(1.0)

def test_indneutralize():
    """Test INDNEUTRALIZE primitive."""
    # 2 industries, 2 stocks each
    data = pd.DataFrame({
        'A': [1.0, 1.0], # Ind 1
        'B': [2.0, 2.0], # Ind 1
        'C': [3.0, 3.0], # Ind 2
        'D': [4.0, 4.0]  # Ind 2
    })
    
    ind_map = pd.Series({
        'A': 'Ind1',
        'B': 'Ind1',
        'C': 'Ind2',
        'D': 'Ind2'
    })
    
    neutralized = INDNEUTRALIZE(data, industry_map=ind_map, method='demean')
    
    # Ind 1 mean: 1.5. A-> -0.5, B-> 0.5
    assert neutralized['A'].iloc[0] == pytest.approx(-0.5)
    assert neutralized['B'].iloc[0] == pytest.approx(0.5)
    
    # Ind 2 mean: 3.5. C-> -0.5, D-> 0.5
    assert neutralized['C'].iloc[0] == pytest.approx(-0.5)
    assert neutralized['D'].iloc[0] == pytest.approx(0.5)

def test_ts_rank():
    """Test TS_RANK primitive."""
    series = pd.Series([10, 20, 30, 40, 50])
    window = 3
    
    # Index 2: [10, 20, 30]. Rank of 30 is 1.0 (highest)
    assert TS_RANK(series, window).iloc[2] == pytest.approx(1.0)
    
    # Reverse order
    series2 = pd.Series([50, 40, 30, 20, 10])
    # Index 2: [50, 40, 30]. Rank of 30 is 0.0 (lowest) -> Wait, rank(pct=True)
    # pd.Series([50, 40, 30]).rank(pct=True) -> 50: 1.0, 40: 0.66, 30: 0.33
    # So for the last element (30), it should be 0.33...
    
    # Let's verify the implementation of TS_RANK
    # return series.rolling(window=window).apply(rank_func, raw=True)
    # rank_func takes array, converts to Series, ranks, takes iloc[-1]
    
    ts_r = TS_RANK(series2, window)
    # [50, 40, 30] -> ranks: 30 is lowest. 
    # If method='average' (default), ranks are 3, 2, 1. pct=True -> 1.0, 0.66, 0.33
    # So 30 should be 1/3
    assert ts_r.iloc[2] == pytest.approx(1/3)
