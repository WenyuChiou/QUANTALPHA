"""MCP tool: RAG search with filters."""

from typing import Dict, Any, Optional, List
from pathlib import Path


def rag_search(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    n_results: int = 5,
    regime: Optional[str] = None,
    index_path: str = "./kb.index"
) -> Dict[str, Any]:
    """Search knowledge base using RAG.
    
    Args:
        query: Search query
        filters: Metadata filters (e.g., {"topic": "momentum", "status": "passed"})
        n_results: Number of results
        regime: Regime filter
        index_path: Path to Chroma index
    
    Returns:
        Dictionary with:
        - results: List of search results
        - citations: List of citations
    """
    try:
        from ..rag.retriever import HybridRetriever
        retriever = HybridRetriever(index_path=index_path)
    except ImportError:
        # Return empty results if dependencies missing
        return {
            'results': [],
            'citations': [],
            'n_results': 0,
            'error': "RAG dependencies missing"
        }
    
    results = retriever.search(
        query=query,
        n_results=n_results,
        filters=filters,
        regime=regime
    )
    
    # Format results with citations
    formatted_results = []
    citations = []
    
    for i, result in enumerate(results):
        formatted_results.append({
            'rank': i + 1,
            'text': result['text'][:500] + "..." if len(result['text']) > 500 else result['text'],
            'score': result['score'],
            'metadata': result['metadata']
        })
        
        citations.append({
            'source': result['metadata'].get('source', 'Unknown'),
            'topic': result['metadata'].get('topic', 'Unknown'),
            'status': result['metadata'].get('status', 'Unknown')
        })
    
    return {
        'results': formatted_results,
        'citations': citations,
        'n_results': len(results)
    }

