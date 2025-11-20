"""Hybrid retrieval (keyword + vector) with metadata filters and regime-conditioned queries."""

from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings

from .embedder import Embedder


class HybridRetriever:
    """Hybrid retriever combining vector search and keyword matching."""
    
    def __init__(self, index_path: str = "./kb.index", model_name: str = "BAAI/bge-m3"):
        """Initialize retriever.
        
        Args:
            index_path: Path to Chroma index
            model_name: Embedding model name
        """
        self.index_path = Path(index_path)
        self.embedder = Embedder(model_name)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=str(self.index_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection("knowledge_base")
        except:
            raise ValueError(f"Index not found at {index_path}. Run indexer first.")
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        regime: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Metadata filters (e.g., {"topic": "momentum", "status": "passed"})
            regime: Regime filter (e.g., "high_vol", "bull")
        
        Returns:
            List of result dictionaries with 'text', 'metadata', 'score'
        """
        # Build where clause for metadata filtering
        where_clause = {}
        if filters:
            where_clause.update(filters)
        
        if regime:
            # Add regime to filters
            where_clause["regime"] = regime
        
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Vector search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'score': 1.0 - results['distances'][0][i] if results['distances'] else 1.0,  # Convert distance to similarity
                    'id': results['ids'][0][i] if results['ids'] else None
                })
        
        # Also do keyword search (simple: check if query terms appear in documents)
        keyword_results = self._keyword_search(query, n_results, where_clause)
        
        # Combine and deduplicate
        combined = self._combine_results(formatted_results, keyword_results, n_results)
        
        return combined
    
    def _keyword_search(
        self,
        query: str,
        n_results: int,
        where_clause: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Simple keyword search (term matching).
        
        Args:
            query: Search query
            n_results: Number of results
            where_clause: Metadata filters
        
        Returns:
            List of results
        """
        # Get all documents (or filtered subset)
        # This is simplified - in production, use proper keyword search
        query_terms = query.lower().split()
        
        # Get all documents from collection
        all_docs = self.collection.get()
        
        if not all_docs['documents']:
            return []
        
        # Score documents by keyword matches
        scored_docs = []
        for i, doc in enumerate(all_docs['documents']):
            doc_lower = doc.lower()
            score = sum(1 for term in query_terms if term in doc_lower) / len(query_terms)
            
            # Apply metadata filters
            if where_clause:
                metadata = all_docs['metadatas'][i]
                matches = all(
                    metadata.get(k) == v for k, v in where_clause.items()
                )
                if not matches:
                    continue
            
            if score > 0:
                scored_docs.append({
                    'text': doc,
                    'metadata': all_docs['metadatas'][i] if all_docs['metadatas'] else {},
                    'score': score,
                    'id': all_docs['ids'][i] if all_docs['ids'] else None
                })
        
        # Sort by score and return top N
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:n_results]
    
    def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        n_results: int
    ) -> List[Dict[str, Any]]:
        """Combine vector and keyword results, deduplicate, and rerank.
        
        Args:
            vector_results: Vector search results
            keyword_results: Keyword search results
            n_results: Final number of results
        
        Returns:
            Combined and deduplicated results
        """
        # Create a map by document ID
        result_map = {}
        
        # Add vector results (weighted higher)
        for result in vector_results:
            doc_id = result.get('id') or result['text'][:100]  # Use text as fallback ID
            if doc_id not in result_map:
                result_map[doc_id] = result.copy()
                result_map[doc_id]['score'] = result['score'] * 0.7  # Vector weight
            else:
                # Boost score if found in both
                result_map[doc_id]['score'] = max(
                    result_map[doc_id]['score'],
                    result['score'] * 0.7
                )
        
        # Add keyword results
        for result in keyword_results:
            doc_id = result.get('id') or result['text'][:100]
            if doc_id not in result_map:
                result_map[doc_id] = result.copy()
                result_map[doc_id]['score'] = result['score'] * 0.3  # Keyword weight
            else:
                # Boost score
                result_map[doc_id]['score'] += result['score'] * 0.3
        
        # Sort by combined score
        combined = sorted(result_map.values(), key=lambda x: x['score'], reverse=True)
        
        return combined[:n_results]
    
    def search_by_topic(self, topic: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search by topic tag.
        
        Args:
            topic: Topic tag (e.g., "momentum", "volatility")
            n_results: Number of results
        
        Returns:
            List of results
        """
        return self.search(
            query=topic,
            n_results=n_results,
            filters={"topic": topic}
        )
    
    def search_successful_factors(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search for successful factor patterns.
        
        Args:
            n_results: Number of results
        
        Returns:
            List of successful factor results
        """
        return self.search(
            query="successful factor design",
            n_results=n_results,
            filters={"status": "passed"}
        )
    
    def search_failed_factors(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search for failed factor patterns (error bank).
        
        Args:
            n_results: Number of results
        
        Returns:
            List of failed factor results
        """
        return self.search(
            query="factor failure issues",
            n_results=n_results,
            filters={"status": "failed"}
        )
    
    def search_regime_specific(
        self,
        query: str,
        regime: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search with regime conditioning.
        
        Args:
            query: Search query
            regime: Regime (e.g., "high_vol", "bull", "bear")
            n_results: Number of results
        
        Returns:
            List of regime-specific results
        """
        return self.search(
            query=query,
            n_results=n_results,
            regime=regime
        )

