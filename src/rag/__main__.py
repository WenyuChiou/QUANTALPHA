"""Command-line interface for RAG indexer."""

import argparse
from pathlib import Path
from .indexer import KnowledgeBaseIndexer


def main():
    parser = argparse.ArgumentParser(description="Index knowledge base")
    parser.add_argument("--kb", type=str, default="./kb", help="Knowledge base directory")
    parser.add_argument("--out", type=str, default="./kb.index", help="Output index path")
    
    args = parser.parse_args()
    
    kb_dir = Path(args.kb)
    index_path = args.out
    
    print(f"Indexing knowledge base from {kb_dir}...")
    indexer = KnowledgeBaseIndexer(kb_dir=kb_dir, index_path=index_path)
    counts = indexer.rebuild_index()
    
    print("Indexing complete!")
    for subdir, count in counts.items():
        print(f"  {subdir}: {count} documents")


if __name__ == "__main__":
    main()

