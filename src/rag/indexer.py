"""Build/update Chroma index from kb/ directory with metadata tagging."""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings

from .embedder import Embedder


class KnowledgeBaseIndexer:
    """Index knowledge base documents into Chroma vector database."""
    
    def __init__(self, kb_dir: Path, index_path: str = "./kb.index", model_name: str = "BAAI/bge-m3"):
        """Initialize indexer.
        
        Args:
            kb_dir: Path to knowledge base directory
            index_path: Path for Chroma index
            model_name: Embedding model name
        """
        self.kb_dir = Path(kb_dir)
        self.index_path = Path(index_path)
        self.embedder = Embedder(model_name)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=str(self.index_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
    
    def index_directory(self, subdir: str, topic: str, status: str = "general") -> int:
        """Index all files in a subdirectory.
        
        Args:
            subdir: Subdirectory name (e.g., "papers", "notes", "run_summaries")
            topic: Topic tag (e.g., "momentum", "volatility")
            status: Status tag (e.g., "passed", "failed", "general")
        
        Returns:
            Number of documents indexed
        """
        subdir_path = self.kb_dir / subdir
        
        if not subdir_path.exists():
            return 0
        
        documents = []
        metadatas = []
        ids = []
        
        # Process all text files
        for file_path in subdir_path.glob("*.md"):
            content = file_path.read_text(encoding='utf-8')
            
            # Split into chunks (simple: by paragraphs)
            chunks = self._chunk_text(content, chunk_size=1000)
            
            for i, chunk in enumerate(chunks):
                doc_id = f"{subdir}/{file_path.stem}_{i}"
                documents.append(chunk)
                metadatas.append({
                    "source": str(file_path),
                    "subdir": subdir,
                    "topic": topic,
                    "status": status,
                    "chunk_id": i
                })
                ids.append(doc_id)
        
        if len(documents) == 0:
            return 0
        
        # Generate embeddings
        embeddings = self.embedder.embed(documents)
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(documents)
    
    def index_file(self, file_path: Path, topic: str, status: str = "general", subdir: str = "notes") -> int:
        """Index a single file.
        
        Args:
            file_path: Path to file
            topic: Topic tag
            status: Status tag
            subdir: Subdirectory name
        
        Returns:
            Number of chunks indexed
        """
        if not file_path.exists():
            return 0
        
        content = file_path.read_text(encoding='utf-8')
        chunks = self._chunk_text(content, chunk_size=1000)
        
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            doc_id = f"{subdir}/{file_path.stem}_{i}"
            documents.append(chunk)
            metadatas.append({
                "source": str(file_path),
                "subdir": subdir,
                "topic": topic,
                "status": status,
                "chunk_id": i
            })
            ids.append(doc_id)
        
        if len(documents) == 0:
            return 0
        
        embeddings = self.embedder.embed(documents)
        
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(documents)
    
    def rebuild_index(self) -> Dict[str, int]:
        """Rebuild entire index from knowledge base.
        
        Returns:
            Dictionary with counts per subdirectory
        """
        # Clear existing collection
        try:
            self.client.delete_collection("knowledge_base")
        except:
            pass
        
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
        counts = {}
        
        # Index papers (topic: momentum, volatility, etc.)
        papers_dir = self.kb_dir / "papers"
        if papers_dir.exists():
            # Try to infer topic from filename or use default
            counts["papers"] = self.index_directory("papers", topic="factor_literature", status="general")
        
        # Index notes
        notes_dir = self.kb_dir / "notes"
        if notes_dir.exists():
            counts["notes"] = self.index_directory("notes", topic="design_notes", status="general")
        
        # Index run summaries
        summaries_dir = self.kb_dir / "run_summaries"
        if summaries_dir.exists():
            counts["run_summaries"] = self.index_directory("run_summaries", topic="backtest_results", status="general")
        
        return counts
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into chunks.
        
        Args:
            text: Input text
            chunk_size: Target chunk size (characters)
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        # Simple chunking by paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If chunks are too large, split further
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= chunk_size:
                final_chunks.append(chunk)
            else:
                # Split by sentences
                sentences = chunk.split('. ')
                temp_chunk = ""
                for sent in sentences:
                    if len(temp_chunk) + len(sent) <= chunk_size:
                        temp_chunk += sent + ". "
                    else:
                        if temp_chunk:
                            final_chunks.append(temp_chunk.strip())
                        temp_chunk = sent + ". "
                if temp_chunk:
                    final_chunks.append(temp_chunk.strip())
        
        return final_chunks
    
    def get_collection(self):
        """Get Chroma collection."""
        return self.collection

