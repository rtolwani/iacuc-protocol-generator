"""
Unit tests for the Document Ingestion Pipeline.
"""

import tempfile
from pathlib import Path

import pytest

from src.rag.ingestion import DocumentIngestion
from src.rag.vector_store import VectorStore


@pytest.fixture
def temp_vector_store():
    """Create a temporary vector store for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = VectorStore(
            persist_directory=temp_dir,
            collection_name="test_ingestion",
        )
        yield store


@pytest.fixture
def ingestion_pipeline(temp_vector_store):
    """Create an ingestion pipeline with temp storage."""
    return DocumentIngestion(
        vector_store=temp_vector_store,
        chunk_size=500,
        chunk_overlap=100,
    )


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF for testing using reportlab or manual creation."""
    # We'll create a simple test PDF using pdfplumber's write capability
    # Since pdfplumber doesn't write PDFs, we'll use a fixture approach
    pdf_path = tmp_path / "sample.pdf"
    
    try:
        # Try to use reportlab if available
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 750, "IACUC Protocol Test Document")
        c.drawString(100, 700, "This is a sample document for testing the ingestion pipeline.")
        c.drawString(100, 650, "It contains information about laboratory animal care.")
        c.drawString(100, 600, "Pain categories include B, C, D, and E.")
        c.drawString(100, 550, "All procedures must be approved by the IACUC committee.")
        c.save()
        return pdf_path
    except ImportError:
        # Skip tests that require a real PDF if reportlab not available
        pytest.skip("reportlab not installed, skipping PDF tests")


class TestDocumentIngestion:
    """Tests for DocumentIngestion class."""

    def test_chunk_text_basic(self, ingestion_pipeline):
        """Test basic text chunking."""
        text = "This is sentence one. This is sentence two. This is sentence three. " * 10
        
        chunks = ingestion_pipeline.chunk_text(text, chunk_size=100, chunk_overlap=20)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_chunk_text_empty(self, ingestion_pipeline):
        """Test chunking empty text."""
        chunks = ingestion_pipeline.chunk_text("")
        assert chunks == []

    def test_chunk_text_whitespace_only(self, ingestion_pipeline):
        """Test chunking whitespace-only text."""
        chunks = ingestion_pipeline.chunk_text("   \n\t  ")
        assert chunks == []

    def test_chunk_text_single_sentence(self, ingestion_pipeline):
        """Test chunking a single short sentence."""
        text = "This is a single short sentence."
        chunks = ingestion_pipeline.chunk_text(text, chunk_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_extract_metadata(self, ingestion_pipeline, tmp_path):
        """Test metadata extraction from file path."""
        # Create a fake file path
        fake_path = tmp_path / "regulatory_core" / "test_doc.pdf"
        fake_path.parent.mkdir(parents=True, exist_ok=True)
        fake_path.touch()
        
        metadata = ingestion_pipeline.extract_metadata(fake_path)
        
        assert metadata["filename"] == "test_doc.pdf"
        assert metadata["file_type"] == "pdf"
        assert metadata["doc_type"] == "regulatory"

    def test_extract_metadata_clinical(self, ingestion_pipeline, tmp_path):
        """Test metadata extraction identifies clinical documents."""
        fake_path = tmp_path / "clinical_standards" / "formulary.pdf"
        fake_path.parent.mkdir(parents=True, exist_ok=True)
        fake_path.touch()
        
        metadata = ingestion_pipeline.extract_metadata(fake_path)
        assert metadata["doc_type"] == "clinical"

    def test_extract_metadata_institutional(self, ingestion_pipeline, tmp_path):
        """Test metadata extraction identifies institutional documents."""
        fake_path = tmp_path / "institutional" / "sop_001.pdf"
        fake_path.parent.mkdir(parents=True, exist_ok=True)
        fake_path.touch()
        
        metadata = ingestion_pipeline.extract_metadata(fake_path)
        assert metadata["doc_type"] == "institutional"

    def test_generate_chunk_id(self, ingestion_pipeline, tmp_path):
        """Test chunk ID generation."""
        file_path = tmp_path / "test.pdf"
        
        id1 = ingestion_pipeline.generate_chunk_id(file_path, 0)
        id2 = ingestion_pipeline.generate_chunk_id(file_path, 1)
        id3 = ingestion_pipeline.generate_chunk_id(file_path, 0)
        
        # Same file, same index should give same ID
        assert id1 == id3
        # Different index should give different ID
        assert id1 != id2
        # IDs should have file stem
        assert "test" in id1

    def test_ingest_file_not_found(self, ingestion_pipeline):
        """Test ingesting a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            ingestion_pipeline.ingest_file("/nonexistent/file.pdf")

    def test_ingest_file_wrong_type(self, ingestion_pipeline, tmp_path):
        """Test ingesting a non-PDF file raises error."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is not a PDF")
        
        with pytest.raises(ValueError, match="Expected PDF"):
            ingestion_pipeline.ingest_file(txt_file)

    def test_ingest_directory_not_found(self, ingestion_pipeline):
        """Test ingesting a non-existent directory raises error."""
        with pytest.raises(FileNotFoundError):
            ingestion_pipeline.ingest_directory("/nonexistent/directory")

    def test_ingest_directory_not_a_directory(self, ingestion_pipeline, tmp_path):
        """Test ingesting a file path raises error."""
        file_path = tmp_path / "test.txt"
        file_path.touch()
        
        with pytest.raises(ValueError, match="Not a directory"):
            ingestion_pipeline.ingest_directory(file_path)


class TestDocumentIngestionWithPDF:
    """Tests that require actual PDF files."""

    def test_extract_text_from_pdf(self, ingestion_pipeline, sample_pdf):
        """Test extracting text from a PDF file."""
        text = ingestion_pipeline.extract_text_from_pdf(sample_pdf)
        
        assert "IACUC" in text
        assert "laboratory animal" in text.lower()

    def test_ingest_file(self, ingestion_pipeline, sample_pdf):
        """Test ingesting a PDF file."""
        chunk_ids = ingestion_pipeline.ingest_file(sample_pdf)
        
        assert len(chunk_ids) > 0
        assert ingestion_pipeline.vector_store.count() > 0

    def test_ingest_file_with_additional_metadata(self, ingestion_pipeline, sample_pdf):
        """Test ingesting with additional metadata."""
        extra_metadata = {"custom_field": "custom_value", "version": "1.0"}
        
        chunk_ids = ingestion_pipeline.ingest_file(
            sample_pdf,
            additional_metadata=extra_metadata,
        )
        
        # Verify metadata was added
        doc = ingestion_pipeline.vector_store.get_document(chunk_ids[0])
        assert doc["metadata"]["custom_field"] == "custom_value"
        assert doc["metadata"]["version"] == "1.0"

    def test_ingest_directory(self, ingestion_pipeline, sample_pdf):
        """Test ingesting a directory of PDFs."""
        directory = sample_pdf.parent
        
        results = ingestion_pipeline.ingest_directory(directory)
        
        assert results["total_files"] == 1
        assert results["successful"] == 1
        assert results["failed"] == 0
        assert results["total_chunks"] > 0
