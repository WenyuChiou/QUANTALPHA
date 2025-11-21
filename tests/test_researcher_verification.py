
import pytest
from unittest.mock import MagicMock, patch
from src.agents.researcher import ResearcherAgent

@pytest.fixture
def mock_llm_chain():
    with patch("src.agents.researcher.LLMChain") as mock:
        yield mock

@pytest.fixture
def mock_store():
    with patch("src.agents.researcher.ExperimentStore") as mock:
        yield mock

@pytest.fixture
def mock_lesson_manager():
    with patch("src.agents.researcher.LessonManager") as mock:
        yield mock

@pytest.fixture
def mock_rag_search():
    with patch("src.agents.researcher.rag_search") as mock:
        mock.return_value = {'results': [{'text': 'context'}]}
        yield mock

def test_researcher_propose_factors(mock_llm_chain, mock_store, mock_lesson_manager, mock_rag_search):
    """Test factor proposal."""
    # Mock LLM response
    mock_chain_instance = mock_llm_chain.return_value
    mock_chain_instance.run.return_value = """
    Here are the factors:
    
    ```yaml
    name: "TestFactor1"
    universe: "sp500"
    frequency: "D"
    signals:
      - id: "sig1"
        expr: "RET_LAG(1, 21)"
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
      min_sharpe: 1.8
      max_maxdd: -0.25
      min_avg_ic: 0.05
    ```
    
    ```yaml
    name: "TestFactor2"
    universe: "sp500"
    frequency: "D"
    signals:
      - id: "sig2"
        expr: "RET_LAG(1, 252)"
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
      min_sharpe: 1.8
      max_maxdd: -0.25
      min_avg_ic: 0.05
    ```
    """
    
    # Mock lesson manager
    mock_lesson_manager.return_value.get_success_ledger.return_value = []
    mock_lesson_manager.return_value.get_error_bank.return_value = []
    
    agent = ResearcherAgent(db_path="dummy.db", index_path="dummy_index")
    
    factors = agent.propose_factors(n_factors=2)
    
    assert len(factors) == 2
    assert "TestFactor1" in factors[0]
    assert "TestFactor2" in factors[1]
    
    # Verify prompt contained momentum priority
    call_args = mock_chain_instance.run.call_args
    assert call_args is not None
    kwargs = call_args[1]
    assert "requirements" in kwargs
    assert "MOMENTUM FACTORS ARE CRITICAL" in kwargs["requirements"]

def test_researcher_propose_mutations(mock_llm_chain, mock_store, mock_lesson_manager):
    """Test mutation proposal."""
    mock_chain_instance = mock_llm_chain.return_value
    mock_chain_instance.run.return_value = """
    ```yaml
    name: "MutatedFactor"
    # ...
    ```
    """
    
    agent = ResearcherAgent(db_path="dummy.db", index_path="dummy_index")
    base_yaml = "name: BaseFactor..."
    
    mutations = agent.propose_mutations(base_yaml, n_mutations=1)
    
    assert len(mutations) == 1
    assert "MutatedFactor" in mutations[0]
