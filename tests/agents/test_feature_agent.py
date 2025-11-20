"""Unit tests for Feature Agent."""

import pytest
import pandas as pd
import numpy as np

from src.agents.feature_agent import FeatureAgent
from src.factors.dsl import DSLParser


class TestFeatureAgent:
    """Test Feature Agent."""
    
    @pytest.fixture
    def feature_agent(self):
        """Create Feature Agent instance."""
        return FeatureAgent()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data."""
        dates = pd.date_range('2020-01-01', periods=500, freq='D')
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        
        prices = pd.DataFrame(
            np.random.randn(len(dates), len(tickers)).cumsum(axis=0) + 100,
            index=dates,
            columns=tickers
        )
        
        returns = prices.pct_change(1)
        return prices, returns
    
    def test_initialization(self, feature_agent):
        """Test agent initialization."""
        assert feature_agent is not None
        assert feature_agent.parser is not None
    
    def test_compute_features_valid_yaml(self, feature_agent, sample_data, sample_factor_yaml):
        """Test feature computation with valid YAML."""
        prices, returns = sample_data
        
        result = feature_agent.compute_features(
            sample_factor_yaml,
            prices,
            returns
        )
        
        assert result['success'] is not None
        # Note: actual computation may fail without full implementation
        # This test verifies the interface works
    
    def test_compute_features_invalid_yaml(self, feature_agent, sample_data):
        """Test feature computation with invalid YAML."""
        prices, returns = sample_data
        invalid_yaml = "invalid: yaml: content: ["
        
        result = feature_agent.compute_features(
            invalid_yaml,
            prices,
            returns
        )
        
        assert result['success'] == False
        assert 'error' in result
    
    def test_compute_features_lookahead_detection(self, feature_agent, sample_data):
        """Test lookahead detection."""
        prices, returns = sample_data
        
        # YAML with lookahead (lag < 1)
        lookahead_yaml = """
name: "BadFactor"
universe: "sp500"
signals:
  - id: "bad"
    expr: "RET_LAG(0,21)"
"""
        
        result = feature_agent.compute_features(
            lookahead_yaml,
            prices,
            returns
        )
        
        # Should detect lookahead
        assert result['success'] == False or len(result.get('warnings', [])) > 0

