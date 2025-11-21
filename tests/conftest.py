"""Pytest configuration and fixtures."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from src.memory.store import ExperimentStore
# from src.rag.indexer import KnowledgeBaseIndexer
# from src.rag.retriever import HybridRetriever


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()
    
    store = ExperimentStore(db_path)
    yield store
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def temp_kb_index():
    """Create temporary knowledge base index for testing."""
    temp_dir = tempfile.mkdtemp()
    index_path = Path(temp_dir) / "test_index"
    
    kb_dir = Path("kb")
    if kb_dir.exists():
        try:
            from src.rag.indexer import KnowledgeBaseIndexer
            indexer = KnowledgeBaseIndexer(kb_dir=kb_dir, index_path=str(index_path))
            indexer.rebuild_index()
        except ImportError:
            # Skip indexing if dependencies are missing
            pass
    
    yield str(index_path)
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_prices():
    """Generate sample price data."""
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
    dates = dates[dates.weekday < 5]  # Business days only
    
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    prices = pd.DataFrame(
        index=dates,
        columns=tickers
    )
    
    # Generate random walk prices
    np.random.seed(42)
    for ticker in tickers:
        returns = np.random.normal(0.0005, 0.02, len(dates))
        prices[ticker] = 100 * (1 + pd.Series(returns)).cumprod()
    
    return prices


@pytest.fixture
def sample_returns(sample_prices):
    """Generate sample return data from prices."""
    returns = sample_prices.pct_change()
    return returns


@pytest.fixture
def sample_prices_returns(sample_prices, sample_returns):
    """Combined fixture for prices and returns."""
    return sample_prices, sample_returns


@pytest.fixture
def sample_factor_yaml():
    """Sample Factor DSL YAML."""
    return """
name: "TestFactor_Momentum"
universe: "sp500"
frequency: "D"
signals:
  - id: "momentum"
    expr: "RET_LAG(1,21)"
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
  min_sharpe: 1.8  # Updated requirement: minimum Sharpe 1.8
  max_maxdd: 0.25  # Updated requirement: maximum drawdown -25%
  min_avg_ic: 0.05
"""


@pytest.fixture
def mock_ollama_llm(monkeypatch):
    """Mock Ollama LLM for testing."""
    class MockLLM:
        def __call__(self, prompt, **kwargs):
            return "Mock LLM response"
        
        def run(self, *args, **kwargs):
            return "Mock LLM response"
    
    monkeypatch.setattr("langchain.llms.Ollama", lambda *args, **kwargs: MockLLM())
    return MockLLM()

