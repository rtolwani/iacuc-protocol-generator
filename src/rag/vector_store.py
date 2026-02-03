"""
ChromaDB Vector Store for RAG.

Provides persistent storage for document embeddings and semantic search.
"""

import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import get_settings


class VectorStore:
    """
    ChromaDB-based vector store for document embeddings.
    
    Provides methods to add, query, and manage document embeddings
    for the RAG (Retrieval Augmented Generation) system.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        """
        Initialize the vector store.

        Args:
            persist_directory: Directory to persist ChromaDB data.
                             Defaults to settings value.
            collection_name: Name of the collection to use.
                           Defaults to settings value.
        """
        settings = get_settings()
        
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name
        
        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        # Get or create the collection
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "IACUC knowledge base documents"},
        )

    @property
    def collection(self):
        """Get the ChromaDB collection."""
        return self._collection

    def add_documents(
        self,
        documents: list[str],
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Add documents to the vector store.

        Args:
            documents: List of document texts to add.
            metadatas: Optional list of metadata dicts for each document.
            ids: Optional list of unique IDs. Auto-generated if not provided.

        Returns:
            List of document IDs that were added.
        """
        if not documents:
            return []

        # Generate IDs if not provided
        if ids is None:
            existing_count = self._collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(documents))]

        # ChromaDB requires non-empty metadata dicts, so add a default key if none provided
        if metadatas is None:
            metadatas = [{"_source": "unknown"} for _ in documents]
        else:
            # Ensure no empty dicts (ChromaDB requires non-empty metadata)
            metadatas = [
                m if m else {"_source": "unknown"} for m in metadatas
            ]

        self._collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        return ids

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict] = None,
        include: Optional[list[str]] = None,
    ) -> dict:
        """
        Query the vector store for similar documents.

        Args:
            query_text: The query text to search for.
            n_results: Number of results to return (default 5).
            where: Optional metadata filter.
            include: What to include in results. Defaults to documents and metadatas.

        Returns:
            Dictionary containing ids, documents, metadatas, and distances.
        """
        if include is None:
            include = ["documents", "metadatas", "distances"]

        results = self._collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=include,
        )

        return results

    def get_document(self, doc_id: str) -> Optional[dict]:
        """
        Get a specific document by ID.

        Args:
            doc_id: The document ID to retrieve.

        Returns:
            Dictionary with document content and metadata, or None if not found.
        """
        result = self._collection.get(
            ids=[doc_id],
            include=["documents", "metadatas"],
        )

        if result["ids"]:
            return {
                "id": result["ids"][0],
                "document": result["documents"][0] if result["documents"] else None,
                "metadata": result["metadatas"][0] if result["metadatas"] else None,
            }
        return None

    def delete_documents(self, ids: list[str]) -> None:
        """
        Delete documents by their IDs.

        Args:
            ids: List of document IDs to delete.
        """
        if ids:
            self._collection.delete(ids=ids)

    def count(self) -> int:
        """
        Get the total number of documents in the collection.

        Returns:
            Number of documents in the collection.
        """
        return self._collection.count()

    def reset(self) -> None:
        """
        Reset the collection by deleting all documents.
        
        Warning: This is destructive and cannot be undone.
        """
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "IACUC knowledge base documents"},
        )

    def list_collections(self) -> list[str]:
        """
        List all collections in the database.

        Returns:
            List of collection names.
        """
        return [col.name for col in self._client.list_collections()]
