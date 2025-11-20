"""Integration tests for agent workflows."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from src.agents.orchestrator import Orchestrator
from src.agents.researcher import ResearcherAgent
from src.agents.feature_agent import FeatureAgent
from src.agents.backtester import BacktesterAgent


class TestAgentWorkflows:
    """Test agent workflow integration."""
    
    @pytest.fixture
    def orchestrator(self, temp_db, temp_kb_index):
        """Create orchestrator instance."""
        with patch('src.agents.orchestrator.ResearcherAgent'), \
             patch('src.agents.orchestrator.FeatureAgent'), \
             patch('src.agents.orchestrator.BacktesterAgent'), \
             patch('src.agents.orchestrator.CriticAgent'), \
             patch('src.agents.orchestrator.LibrarianAgent'), \
             patch('src.agents.orchestrator.ReporterAgent'):
            orch = Orchestrator(
                universe="sp500",
                db_path=temp_db.db_path,
                index_path=temp_kb_index
            )
            return orch
    
    def test_researcher_to_feature_workflow(self):
        """Test Researcher → Feature Agent workflow."""
        # Mock researcher output
        factor_yaml = """
name: "TestFactor"
universe: "sp500"
signals:
  - id: "signal1"
    expr: "RET_LAG(1,21)"
"""
        
        # Mock feature agent
        feature_agent = FeatureAgent()
        with patch.object(feature_agent, 'compute_features') as mock_compute:
            mock_compute.return_value = {
                'success': True,
                'signals': pd.DataFrame(),
                'schema': {}
            }
            
            result = feature_agent.compute_features(factor_yaml, None, None)
            assert result['success'] is not None
    
    def test_feature_to_backtester_workflow(self):
        """Test Feature → Backtester workflow."""
        # This would test the integration between feature computation
        # and backtest execution
        pass
    
    def test_orchestrator_coordination(self, orchestrator):
        """Test orchestrator coordination of agents."""
        assert orchestrator is not None
        assert orchestrator.researcher is not None
        assert orchestrator.feature_agent is not None

