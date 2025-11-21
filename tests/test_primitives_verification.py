"""Test primitives verification - ensuring core building blocks work correctly."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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

def test_zscore():
    """Test ZSCORE primitive."""
    series = pd.Series([1, 2, 3, 4, 5])
    window = 3
    
    z = ZSCORE(series, window)
    
    # Index 2: [1, 2, 3]. Mean=2, Std=1. (3-2)/1 = 1
    assert z.iloc[2] == pytest.approx(1.0)
    
    # Index 3: [2, 3, 4]. Mean=3, Std=1. (4-3)/1 = 1
    assert z.iloc[3] == pytest.approx(1.0)

if __name__ == '__main__':
    print("Running primitives verification tests...")
    test_ret_lag()
    print("✓ test_ret_lag passed")
    test_zscore()
    print("✓ test_zscore passed")
    print("\n✅ All primitives tests passed!")
