"""Local embeddings using sentence-transformers with bge-m3 model."""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """Embedding model wrapper using sentence-transformers."""
    
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """Initialize embedder with specified model.
        
        Args:
            model_name: HuggingFace model name (default: BAAI/bge-m3)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def embed(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for text(s).
        
        Args:
            texts: Single text string or list of texts
            batch_size: Batch size for processing
        
        Returns:
            numpy array of embeddings (shape: [n_texts, embedding_dim])
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """Embed a query (may use different encoding for queries vs documents).
        
        Args:
            query: Query text
        
        Returns:
            Query embedding vector
        """
        # For bge-m3, queries can be encoded the same way
        # Some models use encode_queries() method, but bge-m3 uses encode()
        return self.embed(query)[0]
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.embedding_dim

