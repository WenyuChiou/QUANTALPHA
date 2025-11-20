"""End-to-end test for complete PDRR cycle."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

from src.agents.orchestrator import Orchestrator
from src.factors.recipes import get_tsmom_factor


class TestPDRRCycle:
    """Test complete Plan-Do-Review-Replan cycle."""
    
    @pytest.fixture
    def sample_data(self):
        """Create comprehensive sample data."""
        dates = pd.date_range('2015-01-01', '2023-12-31', freq='D')
        dates = dates[dates.weekday < 5]  # Business days
        
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
        
        np.random.seed(42)
        prices = pd.DataFrame(
            index=dates,
            columns=tickers
        )
        
        for ticker in tickers:
            returns = np.random.normal(0.0005, 0.02, len(dates))
            prices[ticker] = 100 * (1 + pd.Series(returns)).cumprod()
        
        returns = prices.pct_change(1).dropna()
        return prices, returns
    
    @pytest.mark.integration
    def test_complete_cycle_mock(self, temp_db, temp_kb_index, sample_data):
        """Test complete PDRR cycle with mocked agents."""
        prices, returns = sample_data
        
        # Create orchestrator with mocked agents
        with patch('src.agents.orchestrator.ResearcherAgent') as mock_researcher, \
             patch('src.agents.orchestrator.FeatureAgent') as mock_feature, \
             patch('src.agents.orchestrator.BacktesterAgent') as mock_backtester, \
             patch('src.agents.orchestrator.CriticAgent') as mock_critic, \
             patch('src.agents.orchestrator.LibrarianAgent') as mock_librarian, \
             patch('src.agents.orchestrator.ReporterAgent') as mock_reporter:
            
            # Setup mocks
            mock_researcher_instance = Mock()
            mock_researcher_instance.propose_factors.return_value = [
                get_tsmom_factor().to_yaml()
            ]
            mock_researcher.return_value = mock_researcher_instance
            
            mock_feature_instance = Mock()
            mock_feature_instance.compute_features.return_value = {
                'success': True,
                'signals': pd.DataFrame(np.random.randn(100, 5)),
                'schema': {}
            }
            mock_feature.return_value = mock_feature_instance
            
            mock_backtester_instance = Mock()
            mock_backtester_instance.run_backtest.return_value = {
                'metrics': {
                    'sharpe': 1.5,
                    'maxdd': -0.2,
                    'avg_ic': 0.08
                },
                'is_valid': True,
                'issues': []
            }
            mock_backtester.return_value = mock_backtester_instance
            
            orchestrator = Orchestrator(
                universe="sp500",
                db_path=temp_db.db_path,
                index_path=temp_kb_index
            )
            
            orchestrator.prices_df = prices
            orchestrator.returns_df = returns
            
            # Run iteration
            results = orchestrator.run_iteration(n_candidates=1)
            
            # Verify results structure
            assert 'candidates' in results
            assert 'successful' in results
            assert 'failed' in results

