#!/usr/bin/env python3
"""
Test RAG Retrieval Script.

Test that documents are searchable in the vector store.

Usage:
    python scripts/test_rag_retrieval.py --query "pain category D requirements"
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.vector_store import VectorStore


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test RAG retrieval from the vector store"
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Query text to search for",
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=5,
        help="Number of results to return (default: 5)",
    )
    parser.add_argument(
        "--doc-type",
        type=str,
        choices=["regulatory", "clinical", "institutional", "general"],
        help="Filter by document type",
    )

    args = parser.parse_args()

    # Initialize vector store
    vector_store = VectorStore()

    print("=" * 60)
    print("RAG Retrieval Test")
    print("=" * 60)
    print(f"\nQuery: {args.query}")
    print(f"Number of results: {args.n_results}")
    if args.doc_type:
        print(f"Filter by doc type: {args.doc_type}")
    print()

    # Check document count
    doc_count = vector_store.count()
    print(f"Documents in vector store: {doc_count}")

    if doc_count == 0:
        print("\n⚠️  No documents in vector store!")
        print("   Run: python scripts/ingest_documents.py --directory knowledge_base/")
        return 1

    # Build filter if specified
    where_filter = None
    if args.doc_type:
        where_filter = {"doc_type": args.doc_type}

    # Query the vector store
    results = vector_store.query(
        query_text=args.query,
        n_results=args.n_results,
        where=where_filter,
    )

    print("=" * 60)
    print("Results:")
    print("=" * 60)

    if not results["ids"][0]:
        print("\nNo results found.")
        return 0

    for i, (doc_id, document, metadata, distance) in enumerate(
        zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ):
        print(f"\n--- Result {i + 1} (distance: {distance:.4f}) ---")
        print(f"ID: {doc_id}")
        print(f"Source: {metadata.get('filename', 'Unknown')}")
        print(f"Doc Type: {metadata.get('doc_type', 'Unknown')}")
        print(f"Chunk: {metadata.get('chunk_index', '?')}/{metadata.get('total_chunks', '?')}")
        print(f"\nContent (first 500 chars):")
        print(document[:500] + "..." if len(document) > 500 else document)
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
