"""Unit tests for Researcher Agent."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import yaml

from src.agents.researcher import ResearcherAgent
from src.memory.store import ExperimentStore


class TestResearcherAgent:
    """Test Researcher Agent."""
    
    @pytest.fixture
    def researcher(self, temp_db, temp_kb_index):
        """Create Researcher Agent instance."""
        with patch('src.agents.researcher.Ollama'):
            agent = ResearcherAgent(
                model_name="deepseek-r1",
                db_path=temp_db.db_path,
                index_path=temp_kb_index
            )
            return agent
    
    def test_initialization(self, researcher):
        """Test agent initialization."""
        assert researcher is not None
        assert researcher.store is not None
        assert researcher.lesson_manager is not None
    
    @patch('src.agents.researcher.rag_search')
    @patch('src.agents.researcher.LLMChain')
    def test_propose_factors(self, mock_chain, mock_rag, researcher):
        """Test factor proposal generation."""
        # Mock RAG search
        mock_rag.return_value = {
            'results': [
                {'text': 'Test knowledge', 'score': 0.9}
            ]
        }
        
        # Mock LLM chain
        mock_chain_instance = Mock()
        mock_chain_instance.run.return_value = """
```yaml
name: "TestFactor"
universe: "sp500"
frequency: "D"
signals:
  - id: "signal1"
    expr: "RET_LAG(1,21)"
    normalize: "zscore_252"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
validation:
  min_history_days: 252
targets:
  min_sharpe: 1.8  # Updated requirement: minimum Sharpe 1.8
```
"""
        mock_chain.return_value = mock_chain_instance
        
        # Mock lesson manager
        researcher.lesson_manager.get_success_ledger = Mock(return_value=[])
        researcher.lesson_manager.get_error_bank = Mock(return_value=[])
        
        factors = researcher.propose_factors(n_factors=1)
        
        assert len(factors) > 0
        assert isinstance(factors[0], str)
    
    def test_extract_yaml_blocks(self, researcher):
        """Test YAML block extraction."""
        text = """
Some text before.

```yaml
name: "Test"
```

More text.

```yaml
name: "Test2"
```
"""
        blocks = researcher._extract_yaml_blocks(text)
        assert len(blocks) == 2
        assert "name: \"Test\"" in blocks[0]
    
    def test_propose_mutations(self, researcher):
        """Test mutation proposal."""
        base_yaml = """
name: "BaseFactor"
universe: "sp500"
signals:
  - id: "signal1"
    expr: "RET_LAG(1,21)"
"""
        
        with patch.object(researcher.llm, 'run') as mock_run:
            mock_run.return_value = """
```yaml
name: "MutatedFactor"
universe: "sp500"
signals:
  - id: "signal1"
    expr: "RET_LAG(1,42)"
```
"""
            mutations = researcher.propose_mutations(base_yaml, n_mutations=1)
            assert len(mutations) > 0

