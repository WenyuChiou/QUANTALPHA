"""Test metrics verification - ensuring performance metrics calculation is correct."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
from src.backtest.metrics import sharpe, max_drawdown, information_coefficient, turnover

def test_sharpe():
    """Test Sharpe ratio calculation."""
    # Flat returns -> 0 sharpe
    returns = pd.Series([0.0] * 100)
    assert sharpe(returns) == 0.0
    
    # Normal returns
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.01, 252))
    s = sharpe(returns)
    assert 1.0 < s < 2.0
    print("✓ Sharpe calculation works")

def test_max_drawdown():
    """Test Max Drawdown calculation."""
    # No drawdown
    equity = pd.Series([1.0, 1.1, 1.2, 1.3])
    assert max_drawdown(equity) == 0.0
    
    # 50% drawdown
    equity = pd.Series([1.0, 2.0, 1.0, 2.0])
    assert max_drawdown(equity) == pytest.approx(-0.5)
    print("✓ Max drawdown calculation works")

if __name__ == '__main__':
    print("Running metrics verification tests...")
    test_sharpe()
    test_max_drawdown()
    print("\n✅ All metrics tests passed!")
