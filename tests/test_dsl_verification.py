"""Test DSL verification - ensuring Factor DSL parsing works correctly."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.factors.dsl import DSLParser
from src.memory.factor_registry import FactorSpec

def test_dsl_basic_parsing():
    """Test basic DSL parsing."""
    parser = DSLParser()
    
    valid_yaml = """
name: "TestFactor"
universe: "sp500"
frequency: "D"
signals:
  - id: "sig1"
    expr: "RET_LAG(1, 21)"
    standardize: "zscore_252"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
  rebalance: "W-FRI"
"""
    spec = parser.parse(valid_yaml)
    assert spec.name == "TestFactor"
    assert spec.universe == "sp500"
    assert len(spec.signals) == 1
    print("✓ DSL parsing works")

if __name__ == '__main__':
    print("Running DSL verification tests...")
    test_dsl_basic_parsing()
    print("\n✅ All DSL tests passed!")
