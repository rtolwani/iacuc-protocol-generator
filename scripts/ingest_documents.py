#!/usr/bin/env python3
"""
Document Ingestion Script.

Ingest documents into the vector store for RAG.

Usage:
    python scripts/ingest_documents.py --file path/to/document.pdf
    python scripts/ingest_documents.py --directory path/to/documents/
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.ingestion import DocumentIngestion


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest documents into the vector store"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to a single file to ingest",
    )
    parser.add_argument(
        "--directory",
        type=str,
        help="Path to directory of files to ingest",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Search directories recursively (default: True)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size in characters (default: 1000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Chunk overlap in characters (default: 200)",
    )

    args = parser.parse_args()

    if not args.file and not args.directory:
        parser.error("Must specify either --file or --directory")

    # Initialize ingestion pipeline
    ingestion = DocumentIngestion(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    print("=" * 60)
    print("Document Ingestion")
    print("=" * 60)

    if args.file:
        file_path = Path(args.file)
        print(f"\nIngesting file: {file_path}")

        try:
            chunk_ids = ingestion.ingest_file(file_path)
            print(f"  ✅ Success! Added {len(chunk_ids)} chunks")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return 1

    if args.directory:
        dir_path = Path(args.directory)
        print(f"\nIngesting directory: {dir_path}")
        print(f"  Recursive: {args.recursive}")

        try:
            results = ingestion.ingest_directory(
                dir_path,
                recursive=args.recursive,
            )

            print(f"\nResults:")
            print(f"  Total files found: {results['total_files']}")
            print(f"  Successful: {results['successful']}")
            print(f"  Failed: {results['failed']}")
            print(f"  Total chunks added: {results['total_chunks']}")

            if results['failed'] > 0:
                print("\nFailed files:")
                for f in results['files']:
                    if f['status'] == 'failed':
                        print(f"  - {f['file']}: {f['error']}")

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return 1

    print("\n" + "=" * 60)
    print(f"Vector store now contains {ingestion.vector_store.count()} documents")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
