
import pytest
from src.factors.dsl import DSLParser
from src.memory.factor_registry import FactorSpec

def test_dsl_lookahead_validation():
    """Test DSL parser lookahead validation."""
    parser = DSLParser()
    
    # Valid factor
    valid_yaml = """
    name: "ValidFactor"
    universe: "sp500"
    frequency: "D"
    signals:
      - id: "sig1"
        expr: "RET_LAG(1, 21)"
        normalize: "zscore_252"
    portfolio:
      scheme: "long_short_deciles"
      weight: "equal"
      notional: 1.0
    validation:
      min_history_days: 252
      purge_gap_days: 21
      max_turnover_monthly: 250.0
    targets:
      min_sharpe: 1.0
      max_maxdd: -0.2
      min_avg_ic: 0.05
    """
    spec = parser.parse(valid_yaml)
    is_valid, warnings = parser.validate_no_lookahead(spec)
    assert is_valid
    assert len(warnings) == 0
    
    # Invalid factor: RET_LAG(0, 21)
    invalid_yaml = """
    name: "InvalidFactor"
    universe: "sp500"
    frequency: "D"
    signals:
      - id: "sig1"
        expr: "RET_LAG(0, 21)"
        normalize: "zscore_252"
    portfolio:
      scheme: "long_short_deciles"
      weight: "equal"
      notional: 1.0
    validation:
      min_history_days: 252
      purge_gap_days: 21
      max_turnover_monthly: 250.0
    targets:
      min_sharpe: 1.0
      max_maxdd: -0.2
      min_avg_ic: 0.05
    """
    spec = parser.parse(invalid_yaml)
    is_valid, warnings = parser.validate_no_lookahead(spec)
    assert not is_valid
    assert any("RET_LAG has lag < 1" in w for w in warnings)
    
    # Invalid factor: Future keyword
    future_yaml = """
    name: "FutureFactor"
    universe: "sp500"
    frequency: "D"
    signals:
      - id: "sig1"
        expr: "future_return(1)"
        normalize: "zscore_252"
    portfolio:
      scheme: "long_short_deciles"
      weight: "equal"
      notional: 1.0
    validation:
      min_history_days: 252
      purge_gap_days: 21
      max_turnover_monthly: 250.0
    targets:
      min_sharpe: 1.0
      max_maxdd: -0.2
      min_avg_ic: 0.05
    """
    spec = parser.parse(future_yaml)
    is_valid, warnings = parser.validate_no_lookahead(spec)
    assert not is_valid
    assert any("potential lookahead" in w for w in warnings)

def test_dsl_supported_operations():
    """Test DSL supported operations validation."""
    parser = DSLParser()
    
    # Unsupported operation
    unsupported_yaml = """
    name: "UnsupportedFactor"
    universe: "sp500"
    frequency: "D"
    signals:
      - id: "sig1"
        expr: "MAGIC_FUNCTION(1)"
        normalize: "zscore_252"
    portfolio:
      scheme: "long_short_deciles"
      weight: "equal"
      notional: 1.0
    validation:
      min_history_days: 252
      purge_gap_days: 21
      max_turnover_monthly: 250.0
    targets:
      min_sharpe: 1.0
      max_maxdd: -0.2
      min_avg_ic: 0.05
    """
    spec = parser.parse(unsupported_yaml)
    is_valid, warnings = parser.validate_supported_operations(spec)
    assert not is_valid
    assert any("unsupported operation" in w for w in warnings)
