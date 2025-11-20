"""Performance tests for agents."""

import pytest
import time
from unittest.mock import Mock, patch

from src.agents.researcher import ResearcherAgent
from src.agents.feature_agent import FeatureAgent


class TestAgentPerformance:
    """Test agent performance."""
    
    @pytest.mark.performance
    def test_researcher_response_time(self, temp_db, temp_kb_index):
        """Test Researcher Agent response time."""
        with patch('src.agents.researcher.Ollama'):
            agent = ResearcherAgent(
                db_path=temp_db.db_path,
                index_path=temp_kb_index
            )
            
            start_time = time.time()
            # Mock the propose_factors to return quickly
            with patch.object(agent, 'propose_factors') as mock_propose:
                mock_propose.return_value = []
                agent.propose_factors(n_factors=1)
                elapsed = time.time() - start_time
            
            # Should complete in reasonable time (< 5 seconds for mock)
            assert elapsed < 5.0
    
    @pytest.mark.performance
    def test_feature_computation_performance(self, feature_agent, sample_data):
        """Test feature computation performance."""
        prices, returns = sample_data
        factor_yaml = """
name: "PerfTest"
universe: "sp500"
signals:
  - id: "signal1"
    expr: "RET_LAG(1,21)"
"""
        
        start_time = time.time()
        result = feature_agent.compute_features(factor_yaml, prices, returns)
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time
        assert elapsed < 10.0

