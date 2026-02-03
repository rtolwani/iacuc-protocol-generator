"""
Unit tests for the ChromaDB Vector Store.
"""

import tempfile
import pytest

from src.rag.vector_store import VectorStore


@pytest.fixture
def temp_vector_store():
    """Create a temporary vector store for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = VectorStore(
            persist_directory=temp_dir,
            collection_name="test_collection",
        )
        yield store


class TestVectorStore:
    """Tests for VectorStore class."""

    def test_init_creates_collection(self, temp_vector_store):
        """Test that initialization creates a collection."""
        assert temp_vector_store.collection is not None
        assert temp_vector_store.collection.name == "test_collection"

    def test_add_documents(self, temp_vector_store):
        """Test adding documents to the store."""
        documents = [
            "The Guide for the Care and Use of Laboratory Animals.",
            "USDA pain categories range from B to E.",
            "Euthanasia methods must be AVMA approved.",
        ]
        metadatas = [
            {"source": "guide", "chapter": "1"},
            {"source": "usda", "topic": "pain"},
            {"source": "avma", "topic": "euthanasia"},
        ]

        ids = temp_vector_store.add_documents(
            documents=documents,
            metadatas=metadatas,
        )

        assert len(ids) == 3
        assert temp_vector_store.count() == 3

    def test_add_documents_with_custom_ids(self, temp_vector_store):
        """Test adding documents with custom IDs."""
        documents = ["Document one", "Document two"]
        custom_ids = ["custom_1", "custom_2"]

        ids = temp_vector_store.add_documents(
            documents=documents,
            ids=custom_ids,
        )

        assert ids == custom_ids
        assert temp_vector_store.count() == 2

    def test_add_empty_documents(self, temp_vector_store):
        """Test that adding empty documents returns empty list."""
        ids = temp_vector_store.add_documents(documents=[])
        assert ids == []
        assert temp_vector_store.count() == 0

    def test_query_returns_results(self, temp_vector_store):
        """Test querying documents returns relevant results."""
        # Add test documents
        documents = [
            "Mice require specialized housing conditions.",
            "Surgical procedures must use anesthesia.",
            "Post-operative monitoring is essential.",
        ]
        temp_vector_store.add_documents(documents=documents)

        # Query for surgery-related content
        results = temp_vector_store.query(
            query_text="What anesthesia is needed for surgery?",
            n_results=2,
        )

        assert "ids" in results
        assert len(results["ids"][0]) == 2
        assert "documents" in results
        assert "metadatas" in results

    def test_query_with_metadata_filter(self, temp_vector_store):
        """Test querying with metadata filter."""
        documents = [
            "Mouse housing requirements.",
            "Rat housing requirements.",
            "Mouse surgical procedures.",
        ]
        metadatas = [
            {"species": "mouse", "topic": "housing"},
            {"species": "rat", "topic": "housing"},
            {"species": "mouse", "topic": "surgery"},
        ]
        temp_vector_store.add_documents(documents=documents, metadatas=metadatas)

        # Query with species filter
        results = temp_vector_store.query(
            query_text="housing",
            n_results=3,
            where={"species": "mouse"},
        )

        # Should only return mouse documents
        assert len(results["ids"][0]) == 2
        for metadata in results["metadatas"][0]:
            assert metadata["species"] == "mouse"

    def test_get_document(self, temp_vector_store):
        """Test retrieving a specific document by ID."""
        documents = ["Test document content"]
        metadatas = [{"key": "value"}]
        ids = ["test_doc_1"]

        temp_vector_store.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        result = temp_vector_store.get_document("test_doc_1")

        assert result is not None
        assert result["id"] == "test_doc_1"
        assert result["document"] == "Test document content"
        assert result["metadata"] == {"key": "value"}

    def test_get_nonexistent_document(self, temp_vector_store):
        """Test retrieving a document that doesn't exist."""
        result = temp_vector_store.get_document("nonexistent_id")
        assert result is None

    def test_delete_documents(self, temp_vector_store):
        """Test deleting documents by ID."""
        documents = ["Doc 1", "Doc 2", "Doc 3"]
        ids = ["id_1", "id_2", "id_3"]

        temp_vector_store.add_documents(documents=documents, ids=ids)
        assert temp_vector_store.count() == 3

        temp_vector_store.delete_documents(["id_1", "id_2"])
        assert temp_vector_store.count() == 1

        # Verify remaining document
        result = temp_vector_store.get_document("id_3")
        assert result is not None
        assert result["document"] == "Doc 3"

    def test_count(self, temp_vector_store):
        """Test counting documents."""
        assert temp_vector_store.count() == 0

        temp_vector_store.add_documents(documents=["Doc 1", "Doc 2"])
        assert temp_vector_store.count() == 2

    def test_reset(self, temp_vector_store):
        """Test resetting the collection."""
        temp_vector_store.add_documents(documents=["Doc 1", "Doc 2", "Doc 3"])
        assert temp_vector_store.count() == 3

        temp_vector_store.reset()
        assert temp_vector_store.count() == 0

    def test_list_collections(self, temp_vector_store):
        """Test listing collections."""
        collections = temp_vector_store.list_collections()
        assert "test_collection" in collections
