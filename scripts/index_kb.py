#!/usr/bin/env python3
"""Script to index knowledge base."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.indexer import KnowledgeBaseIndexer


def main():
    """Main function."""
    print("="*70)
    print("Knowledge Base Indexing")
    print("="*70)
    
    kb_dir = Path("kb")
    index_path = "./kb.index"
    
    if not kb_dir.exists():
        print(f"Error: Knowledge base directory not found: {kb_dir}")
        return 1
    
    print(f"\nIndexing from: {kb_dir}")
    print(f"Output index: {index_path}")
    
    indexer = KnowledgeBaseIndexer(kb_dir=kb_dir, index_path=index_path)
    
    print("\nRebuilding index...")
    counts = indexer.rebuild_index()
    
    print("\n" + "="*70)
    print("Indexing Complete!")
    print("="*70)
    
    total = 0
    for subdir, count in counts.items():
        print(f"{subdir:20s}: {count:4d} documents")
        total += count
    
    print(f"{'Total':20s}: {total:4d} documents")
    print("="*70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

