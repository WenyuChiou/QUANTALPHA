
import pytest
import pandas as pd
import numpy as np
from src.backtest.metrics import sharpe, max_drawdown, information_coefficient, turnover

def test_sharpe():
    """Test Sharpe ratio calculation."""
    # Flat returns -> 0 sharpe
    returns = pd.Series([0.0] * 100)
    assert sharpe(returns) == 0.0
    
    # Constant positive returns -> high sharpe (technically infinite if std=0, but implementation might handle it)
    # returns.std() would be 0.
    # Implementation: if ann_vol == 0: return 0.0
    returns = pd.Series([0.01] * 100)
    assert sharpe(returns) == 0.0
    
    # Normal returns
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.01, 252))
    # Mean ~0.001 * 252 = 0.252
    # Vol ~0.01 * sqrt(252) = 0.158
    # Sharpe ~ 0.252 / 0.158 ~ 1.6
    s = sharpe(returns)
    assert 1.0 < s < 2.0

def test_max_drawdown():
    """Test Max Drawdown calculation."""
    # No drawdown
    equity = pd.Series([1.0, 1.1, 1.2, 1.3])
    assert max_drawdown(equity) == 0.0
    
    # 50% drawdown
    equity = pd.Series([1.0, 2.0, 1.0, 2.0])
    # Peak is 2.0. Drop to 1.0 is -50%.
    assert max_drawdown(equity) == pytest.approx(-0.5)
    
    # Recovery
    equity = pd.Series([1.0, 0.5, 1.0])
    assert max_drawdown(equity) == pytest.approx(-0.5)

def test_information_coefficient():
    """Test IC calculation."""
    scores = pd.Series([1, 2, 3, 4, 5])
    returns = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5])
    
    # Perfect correlation
    assert information_coefficient(scores, returns) == pytest.approx(1.0)
    
    # Perfect negative correlation
    returns_neg = pd.Series([-0.1, -0.2, -0.3, -0.4, -0.5])
    assert information_coefficient(scores, returns_neg) == pytest.approx(-1.0)
    
    # Uncorrelated
    returns_rand = pd.Series([0.5, 0.1, 0.4, 0.2, 0.3])
    ic = information_coefficient(scores, returns_rand)
    assert -1.0 <= ic <= 1.0

def test_turnover():
    """Test turnover calculation."""
    # No change
    positions = pd.DataFrame({
        'A': [0.5, 0.5, 0.5],
        'B': [0.5, 0.5, 0.5]
    })
    assert turnover(positions) == 0.0
    
    # Full turnover (flip)
    positions = pd.DataFrame({
        'A': [1.0, 0.0, 1.0],
        'B': [0.0, 1.0, 0.0]
    })
    # Day 1 to 2: A goes 1->0 (diff 1), B goes 0->1 (diff 1). Sum = 2.
    # Day 2 to 3: A goes 0->1 (diff 1), B goes 1->0 (diff 1). Sum = 2.
    # Avg = 2.0
    assert turnover(positions) == pytest.approx(2.0)
