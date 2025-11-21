"""Tests for nonlinear factor executor."""

import pytest
import pandas as pd
import numpy as np
from src.factors.nonlinear import NonlinearFactorExecutor, execute_nonlinear_factor


@pytest.fixture
def sample_data():
    """Create sample price and return data."""
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    np.random.seed(42)
    prices = pd.DataFrame(
        np.cumsum(np.random.randn(100, 3) * 0.02, axis=0) + 100,
        index=dates,
        columns=tickers
    )
    returns = prices.pct_change()
    
    return prices, returns


class TestNonlinearFactorExecutor:
    """Test nonlinear factor execution."""
    
    def test_simple_momentum_factor(self, sample_data):
        """Test simple momentum factor."""
        prices, returns = sample_data
        
        code = """
# Simple 21-day momentum
mom = returns.rolling(21).mean()
result = mom
"""
        executor = NonlinearFactorExecutor(timeout=10)
        result = executor.execute_custom_code(code, prices, returns)
        
        assert result['success']
        assert isinstance(result['signals'], pd.DataFrame)
        assert result['signals'].shape == returns.shape
    
    def test_sklearn_factor(self, sample_data):
        """Test factor using sklearn."""
        prices, returns = sample_data
        
        code = """
from sklearn.ensemble import RandomForestRegressor
import numpy as np

# Features
features = pd.DataFrame({
    'mom_5': returns.rolling(5).mean(),
    'mom_21': returns.rolling(21).mean(),
    'vol': returns.rolling(21).std()
}).fillna(0)

# Simple prediction (just return features for now)
result = features['mom_21']
"""
        executor = NonlinearFactorExecutor(timeout=10)
        result = executor.execute_custom_code(code, prices, returns)
        
        assert result['success']
        assert isinstance(result['signals'], pd.DataFrame)
    
    def test_code_validation(self, sample_data):
        """Test that code validation catches errors."""
        prices, returns = sample_data
        
        # Code with forbidden operation
        code = """
import os
os.system('ls')
"""
        executor = NonlinearFactorExecutor(timeout=10, validate_code=True)
        result = executor.execute_custom_code(code, prices, returns)
        
        assert not result['success']
        assert "validation failed" in result['error'].lower()
    
    def test_execution_error(self, sample_data):
        """Test that execution errors are caught."""
        prices, returns = sample_data
        
        code = """
x = 1 / 0  # ZeroDivisionError
"""
        executor = NonlinearFactorExecutor(timeout=10)
        result = executor.execute_custom_code(code, prices, returns)
        
        assert not result['success']
        assert "ZeroDivisionError" in result['error']
    
    def test_no_return_value(self, sample_data):
        """Test handling when code doesn't return signals."""
        prices, returns = sample_data
        
        code = """
x = 1 + 1  # No DataFrame/Series returned
"""
        executor = NonlinearFactorExecutor(timeout=10)
        result = executor.execute_custom_code(code, prices, returns)
        
        assert not result['success']
        assert "did not return valid signals" in result['error'].lower()
    
    def test_series_to_dataframe_conversion(self, sample_data):
        """Test that Series is converted to DataFrame."""
        prices, returns = sample_data
        
        code = """
# Return a Series (single column)
mom = returns['AAPL'].rolling(21).mean()
result = mom
"""
        executor = NonlinearFactorExecutor(timeout=10)
        result = executor.execute_custom_code(code, prices, returns)
        
        assert result['success']
        assert isinstance(result['signals'], pd.DataFrame)
    
    def test_lookahead_warning(self, sample_data):
        """Test that lookahead patterns trigger warnings."""
        prices, returns = sample_data
        
        code = """
# Using shift(-1) - should trigger warning
y = returns.shift(-1)
result = y
"""
        executor = NonlinearFactorExecutor(timeout=10)
        result = executor.execute_custom_code(code, prices, returns)
        
        assert result['success']  # Still executes
        assert len(result['warnings']) > 0
        assert any("shift(-" in w for w in result['warnings'])
    
    def test_convenience_function(self, sample_data):
        """Test execute_nonlinear_factor convenience function."""
        prices, returns = sample_data
        
        code = """
mom = returns.rolling(21).mean()
result = mom
"""
        result = execute_nonlinear_factor(code, prices, returns, timeout=10)
        
        assert result['success']
        assert isinstance(result['signals'], pd.DataFrame)
    
    def test_additional_kwargs(self, sample_data):
        """Test passing additional variables."""
        prices, returns = sample_data
        
        code = """
# Use custom parameter
signal = returns.rolling(window).mean()
result = signal
"""
        executor = NonlinearFactorExecutor(timeout=10)
        result = executor.execute_custom_code(
            code, prices, returns, window=10
        )
        
        assert result['success']
        assert isinstance(result['signals'], pd.DataFrame)
