"""Unit tests for Reporter Agent."""

import pytest
from unittest.mock import Mock, patch

from src.agents.reporter import ReporterAgent


class TestReporterAgent:
    """Test Reporter Agent."""
    
    @pytest.fixture
    def reporter(self, temp_db):
        """Create Reporter Agent instance."""
        with patch('src.agents.reporter.Ollama'):
            agent = ReporterAgent(
                model_name="deepseek-r1",
                db_path=temp_db.db_path
            )
            return agent
    
    def test_initialization(self, reporter):
        """Test agent initialization."""
        assert reporter is not None
        assert reporter.store is not None
    
    def test_generate_dashboard_notes(self, reporter, temp_db):
        """Test dashboard notes generation."""
        notes = reporter.generate_dashboard_notes()
        assert 'top_performers' in notes
        assert 'recent_failures' in notes
        assert 'last_updated' in notes

