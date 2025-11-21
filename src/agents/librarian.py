"""Librarian agent: manages RAG index, curates knowledge, regime tagging."""

from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    from ..rag.indexer import KnowledgeBaseIndexer
    from ..rag.retriever import HybridRetriever
except ImportError:
    # Mock classes for missing dependencies
    class KnowledgeBaseIndexer:
        def __init__(self, **kwargs): pass
        def rebuild_index(self): return {}
        def index_file(self, *args): return 0
        
    class HybridRetriever:
        def __init__(self, **kwargs): pass
        def search(self, *args, **kwargs): return []
from ..memory.store import ExperimentStore


class LibrarianAgent:
    """Agent that manages knowledge base and RAG index."""
    
    def __init__(
        self,
        kb_dir: Path = Path("kb"),
        index_path: str = "./kb.index",
        db_path: str = "experiments.db"
    ):
        """Initialize librarian agent.
        
        Args:
            kb_dir: Knowledge base directory
            index_path: Vector index path
            db_path: Database path
        """
        self.kb_dir = kb_dir
        self.index_path = index_path
        self.indexer = KnowledgeBaseIndexer(kb_dir=kb_dir, index_path=index_path)
        self.retriever = HybridRetriever(index_path=index_path)
        self.store = ExperimentStore(db_path)
    
    def rebuild_index(self) -> Dict[str, int]:
        """Rebuild the entire RAG index.
        
        Returns:
            Dictionary with counts per subdirectory
        """
        return self.indexer.rebuild_index()
    
    def index_new_document(
        self,
        file_path: Path,
        topic: str,
        status: str = "general",
        subdir: str = "notes"
    ) -> int:
        """Index a new document.
        
        Args:
            file_path: Path to document
            topic: Topic tag
            status: Status tag
            subdir: Subdirectory name
        
        Returns:
            Number of chunks indexed
        """
        return self.indexer.index_file(file_path, topic, status, subdir)
    
    def search_knowledge(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        regime: Optional[str] = None,
        n_results: int = 5,
        prioritize_momentum: bool = True
    ) -> List[Dict[str, Any]]:
        """Search knowledge base.
        
        Args:
            query: Search query
            filters: Metadata filters
            regime: Regime filter
            n_results: Number of results
            prioritize_momentum: If True, prioritize momentum-related results
        
        Returns:
            List of search results (momentum factors prioritized if prioritize_momentum=True)
        """
        # If prioritizing momentum and query doesn't explicitly mention it, enhance query
        if prioritize_momentum and "momentum" not in query.lower():
            # Search for momentum-related content first
            momentum_query = f"{query} momentum factor time series momentum TSMOM"
            momentum_results = self.retriever.search(momentum_query, n_results=min(3, n_results), filters=filters, regime=regime)
            
            # Also search original query
            general_results = self.retriever.search(query, n_results=n_results, filters=filters, regime=regime)
            
            # Combine with momentum results first
            combined = momentum_results + general_results
            # Remove duplicates while preserving order
            seen = set()
            unique_results = []
            for r in combined:
                r_id = r.get('id') or r.get('text', '')[:100]
                if r_id not in seen:
                    seen.add(r_id)
                    unique_results.append(r)
            
            return unique_results[:n_results]
        else:
            return self.retriever.search(query, n_results, filters, regime)
    
    def tag_run_by_regime(
        self,
        run_id: int,
        regime: str
    ):
        """Tag a run with regime label.
        
        Args:
            run_id: Run ID
            regime: Regime label (e.g., "high_vol", "bull")
        """
        session = self.store.get_session()
        try:
            run = session.query(self.store.Run).filter(self.store.Run.id == run_id).first()
            if run:
                run.regime_label = regime
                session.commit()
        finally:
            session.close()
    
    def curate_successful_factors(self, min_sharpe: float = 1.8) -> List[Dict[str, Any]]:
        """Curate successful factors from database.
        
        Args:
            min_sharpe: Minimum Sharpe for curation
        
        Returns:
            List of successful factor records
        """
        top_runs = self.store.get_top_runs(limit=20, order_by="sharpe")
        
        curated = []
        for run in top_runs:
            metrics = run.metrics[0] if run.metrics else None
            if metrics and metrics.sharpe >= min_sharpe:
                factor = self.store.get_factor(run.factor_id)
                curated.append({
                    'run_id': run.id,
                    'factor_id': run.factor_id,
                    'factor_name': factor.name if factor else 'Unknown',
                    'sharpe': metrics.sharpe,
                    'avg_ic': metrics.avg_ic,
                    'regime': run.regime_label
                })
        
        return curated

