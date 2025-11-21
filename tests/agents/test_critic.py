"""Unit tests for Critic Agent."""

import pytest
from unittest.mock import Mock, patch

from src.agents.critic import CriticAgent
from src.memory.store import ExperimentStore


class TestCriticAgent:
    """Test Critic Agent."""
    
    @pytest.fixture
    def critic(self, temp_db):
        """Create Critic Agent instance."""
        # Mock both possible import paths
        with patch('langchain_community.llms.Ollama'), \
             patch('langchain.llms.Ollama'):
            agent = CriticAgent(
                model_name="deepseek-r1",
                db_path=temp_db.db_path
            )
            return agent
    
    def test_initialization(self, critic):
        """Test agent initialization."""
        assert critic is not None
        assert critic.store is not None
        assert critic.lesson_manager is not None
    
    def test_extract_key_params(self, critic):
        """Test parameter extraction."""
        yaml_str = """
signals:
  - id: "signal1"
    expr: "RET_LAG(1,252)"
"""
        params = critic._extract_key_params(yaml_str)
        assert 'lag' in params or 'period' in params
    
    def test_extract_strengths(self, critic):
        """Test strength extraction."""
        critique = "This factor shows strong performance in bull markets."
        strengths = critic._extract_strengths(critique)
        assert len(strengths) > 0
    
    def test_extract_root_cause(self, critic):
        """Test root cause extraction."""
        critique = "The factor failed due to data leakage."
        issues = [{'detail': 'Lookahead detected', 'severity': 'critical'}]
        root_cause = critic._extract_root_cause(critique, issues)
        assert len(root_cause) > 0

