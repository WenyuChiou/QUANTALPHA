"""Unit tests for Librarian Agent."""

import pytest
from unittest.mock import Mock, patch

from src.agents.librarian import LibrarianAgent


class TestLibrarianAgent:
    """Test Librarian Agent."""
    
    @pytest.fixture
    def librarian(self, temp_db, temp_kb_index):
        """Create Librarian Agent instance."""
        with patch('src.agents.librarian.KnowledgeBaseIndexer'), \
             patch('src.agents.librarian.HybridRetriever'):
            agent = LibrarianAgent(
                kb_dir=Path("kb"),
                index_path=temp_kb_index,
                db_path=temp_db.db_path
            )
            return agent
    
    def test_initialization(self, librarian):
        """Test agent initialization."""
        assert librarian is not None
    
    def test_search_knowledge(self, librarian):
        """Test knowledge search."""
        with patch.object(librarian.retriever, 'search') as mock_search:
            mock_search.return_value = [
                {'text': 'Test result', 'score': 0.9, 'metadata': {}}
            ]
            
            results = librarian.search_knowledge("test query")
            assert len(results) > 0

