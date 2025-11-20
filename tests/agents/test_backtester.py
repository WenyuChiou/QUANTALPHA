"""Unit tests for Backtester Agent."""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.agents.backtester import BacktesterAgent


class TestBacktesterAgent:
    """Test Backtester Agent."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def backtester(self, temp_output_dir):
        """Create Backtester Agent instance."""
        return BacktesterAgent(output_base_dir=temp_output_dir)
    
    def test_initialization(self, backtester):
        """Test agent initialization."""
        assert backtester is not None
        assert backtester.output_base_dir.exists()
    
    def test_output_directory_creation(self, backtester):
        """Test output directory creation."""
        run_id = "test_run_123"
        result = backtester.run_backtest(
            factor_yaml="name: Test",
            prices_df=None,
            returns_df=None,
            run_id=run_id
        )
        
        # Should create output directory
        assert 'output_dir' in result
        assert Path(result['output_dir']).exists()

