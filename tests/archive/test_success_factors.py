"""Tests for success factor archive system."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from src.archive.success_factors import SuccessFactorArchive


@pytest.fixture
def temp_archive_dir():
    """Create temporary archive directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_factor_data():
    """Create sample factor data for testing."""
    return {
        'factor_name': 'test_momentum',
        'factor_yaml': """
name: test_momentum
signal: ROLL_MEAN(RET_LAG(1, 21, prices), 63)
""",
        'agent_outputs': {
            'researcher': {'proposal': 'Test momentum factor'},
            'feature': {'status': 'computed'},
            'backtest': {'status': 'completed'}
        },
        'computations': {
            'signals': pd.DataFrame(np.random.randn(100, 3)),
            'returns': pd.DataFrame(np.random.randn(100, 3) * 0.01)
        },
        'backtest_results': {
            'metrics': {
                'sharpe': 2.1,
                'max_drawdown': -0.15,
                'avg_ic': 0.08,
                'turnover': 45.0
            },
            'splits': [
                {'train': '2020-01-01', 'test': '2021-01-01', 'sharpe': 2.0},
                {'train': '2021-01-01', 'test': '2022-01-01', 'sharpe': 2.2}
            ]
        },
        'conversation_log': [
            {'agent': 'researcher', 'content': 'Proposing momentum factor'},
            {'agent': 'feature', 'content': 'Computing signals'},
            {'agent': 'backtest', 'content': 'Running backtest'}
        ]
    }


class TestSuccessFactorArchive:
    """Test success factor archive functionality."""
    
    def test_should_archive_success(self):
        """Test that factors meeting criteria should be archived."""
        archive = SuccessFactorArchive()
        
        metrics = {
            'sharpe': 2.0,
            'max_drawdown': -0.20,
            'avg_ic': 0.06
        }
        
        assert archive.should_archive(metrics)
    
    def test_should_archive_failure_sharpe(self):
        """Test that low Sharpe factors are not archived."""
        archive = SuccessFactorArchive()
        
        metrics = {
            'sharpe': 1.5,  # Below threshold
            'max_drawdown': -0.20,
            'avg_ic': 0.06
        }
        
        assert not archive.should_archive(metrics)
    
    def test_should_archive_failure_drawdown(self):
        """Test that high drawdown factors are not archived."""
        archive = SuccessFactorArchive()
        
        metrics = {
            'sharpe': 2.0,
            'max_drawdown': -0.30,  # Below threshold
            'avg_ic': 0.06
        }
        
        assert not archive.should_archive(metrics)
    
    def test_should_archive_failure_ic(self):
        """Test that low IC factors are not archived."""
        archive = SuccessFactorArchive()
        
        metrics = {
            'sharpe': 2.0,
            'max_drawdown': -0.20,
            'avg_ic': 0.03  # Below threshold
        }
        
        assert not archive.should_archive(metrics)
    
    def test_archive_factor(self, temp_archive_dir, sample_factor_data):
        """Test archiving a complete factor."""
        archive = SuccessFactorArchive(temp_archive_dir)
        
        archive_path = archive.archive_factor(**sample_factor_data)
        
        # Check that archive was created
        assert Path(archive_path).exists()
        
        # Check that all files exist
        archive_path = Path(archive_path)
        assert (archive_path / "metadata.json").exists()
        assert (archive_path / "factor_spec.yaml").exists()
        assert (archive_path / "agent_outputs").exists()
        assert (archive_path / "computations").exists()
        assert (archive_path / "backtest").exists()
        assert (archive_path / "conversation_log.json").exists()
        assert (archive_path / "README.md").exists()
    
    def test_list_archived_factors(self, temp_archive_dir, sample_factor_data):
        """Test listing archived factors."""
        archive = SuccessFactorArchive(temp_archive_dir)
        
        # Archive a factor
        archive.archive_factor(**sample_factor_data)
        
        # List factors
        factors = archive.list_archived_factors()
        
        assert len(factors) == 1
        assert factors[0]['name'] == 'test_momentum'
        assert factors[0]['metrics']['sharpe'] == 2.1
    
    def test_list_with_filters(self, temp_archive_dir, sample_factor_data):
        """Test listing with filters."""
        archive = SuccessFactorArchive(temp_archive_dir)
        
        # Archive a factor
        archive.archive_factor(**sample_factor_data)
        
        # Filter by high Sharpe
        factors = archive.list_archived_factors(min_sharpe=2.5)
        assert len(factors) == 0
        
        # Filter by low Sharpe
        factors = archive.list_archived_factors(min_sharpe=2.0)
        assert len(factors) == 1
        
        # Filter by IC
        factors = archive.list_archived_factors(min_ic=0.1)
        assert len(factors) == 0
        
        factors = archive.list_archived_factors(min_ic=0.05)
        assert len(factors) == 1
    
    def test_load_factor(self, temp_archive_dir, sample_factor_data):
        """Test loading archived factor."""
        archive = SuccessFactorArchive(temp_archive_dir)
        
        # Archive a factor
        archive_path = archive.archive_factor(**sample_factor_data)
        
        # Load it back
        data = archive.load_factor(archive_path)
        
        assert data['metadata']['factor_name'] == 'test_momentum'
        assert 'researcher' in data['agent_outputs']
        assert 'signals' in data['computations']
        assert isinstance(data['computations']['signals'], pd.DataFrame)
        assert data['backtest_results']['metrics']['sharpe'] == 2.1
        assert len(data['conversation_log']) == 3
    
    def test_load_nonexistent_factor(self, temp_archive_dir):
        """Test loading nonexistent factor raises error."""
        archive = SuccessFactorArchive(temp_archive_dir)
        
        with pytest.raises(ValueError, match="not found"):
            archive.load_factor("nonexistent_path")
