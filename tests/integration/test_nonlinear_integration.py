"""Integration tests for nonlinear factors with DSL and agents."""

import pytest
import pandas as pd
import numpy as np
from src.factors.dsl import DSLParser
from src.tools.compute_factor import compute_factor


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


class TestNonlinearFactorIntegration:
    """Test complete nonlinear factor pipeline."""
    
    def test_dsl_with_custom_code(self, sample_data):
        """Test DSL parsing with custom code."""
        prices, returns = sample_data
        
        yaml_spec = """
name: custom_momentum
universe: test
frequency: D
signals:
  - id: mom_signal
    custom_code: |
      # Simple momentum using custom code
      mom = returns.rolling(21).mean()
      result = mom
    code_type: custom
"""
        
        parser = DSLParser()
        spec = parser.parse(yaml_spec)
        
        # Check that spec was parsed correctly
        assert spec.name == 'custom_momentum'
        assert len(spec.signals) == 1
        assert spec.signals[0].custom_code is not None
        assert spec.signals[0].code_type == 'custom'
    
    def test_compute_factor_with_custom_code(self, sample_data):
        """Test computing factor with custom code."""
        prices, returns = sample_data
        
        yaml_spec = """
name: custom_momentum
universe: test
frequency: D
signals:
  - id: mom_signal
    custom_code: |
      # Simple momentum
      mom = returns.rolling(21).mean()
      result = mom
    code_type: custom
"""
        
        result = compute_factor(yaml_spec, prices, returns)
        
        # Check that computation succeeded
        assert result['signals'] is not None
        assert isinstance(result['signals'], pd.DataFrame)
        assert result['error'] is None
    
    def test_validation_with_custom_code(self, sample_data):
        """Test that validation works with custom code."""
        prices, returns = sample_data
        
        # Code with forbidden operation
        yaml_spec = """
name: bad_factor
universe: test
frequency: D
signals:
  - id: bad_signal
    custom_code: |
      import os
      os.system('ls')
      result = returns.mean()
    code_type: custom
"""
        
        result = compute_factor(yaml_spec, prices, returns)
        
        # Should fail validation
        assert result['signals'] is None
        assert result['error'] is not None
        assert 'validation failed' in result['error'].lower()
    
    def test_sklearn_factor(self, sample_data):
        """Test factor using sklearn."""
        prices, returns = sample_data
        
        yaml_spec = """
name: sklearn_momentum
universe: test
frequency: D
signals:
  - id: ml_signal
    custom_code: |
      from sklearn.ensemble import RandomForestRegressor
      import numpy as np
      
      # Create features
      features = pd.DataFrame({
          'mom_5': returns.rolling(5).mean().mean(axis=1),
          'mom_21': returns.rolling(21).mean().mean(axis=1),
          'vol': returns.rolling(21).std().mean(axis=1)
      }).fillna(0)
      
      # For now, just return momentum feature
      result = features['mom_21']
    code_type: sklearn
"""
        
        result = compute_factor(yaml_spec, prices, returns)
        
        # Should succeed
        assert result['signals'] is not None
        assert isinstance(result['signals'], pd.DataFrame)
    
    def test_mixed_dsl_and_custom(self, sample_data):
        """Test factor with both DSL and custom code signals."""
        prices, returns = sample_data
        
        yaml_spec = """
name: mixed_factor
universe: test
frequency: D
signals:
  - id: dsl_signal
    expr: "RET_LAG(1, 21)"
  - id: custom_signal
    custom_code: |
      # Custom momentum
      mom = returns.rolling(21).mean()
      result = mom
    code_type: custom
"""
        
        result = compute_factor(yaml_spec, prices, returns)
        
        # Should succeed with both signals
        assert result['signals'] is not None
        assert 'dsl_signal' in result['schema']['signals_computed']
        assert 'custom_signal' in result['schema']['signals_computed']
    
    def test_lookahead_warning_in_custom_code(self, sample_data):
        """Test that lookahead patterns in custom code trigger warnings."""
        prices, returns = sample_data
        
        yaml_spec = """
name: lookahead_factor
universe: test
frequency: D
signals:
  - id: lookahead_signal
    custom_code: |
      # Using shift(-1) - lookahead!
      future_returns = returns.shift(-1)
      result = future_returns
    code_type: custom
"""
        
        parser = DSLParser()
        spec = parser.parse(yaml_spec)
        is_valid, warnings = parser.validate_no_lookahead(spec)
        
        # Should have warnings about shift(-1)
        assert len(warnings) > 0
        assert any('shift(-' in w for w in warnings)
