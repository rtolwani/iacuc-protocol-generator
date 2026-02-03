"""
Document Ingestion Pipeline.

Handles loading, chunking, and storing documents in the vector store.
"""

import hashlib
import re
from pathlib import Path
from typing import Optional

import pdfplumber

from src.config import get_settings
from src.rag.vector_store import VectorStore


class DocumentIngestion:
    """
    Pipeline for ingesting documents into the vector store.
    
    Supports PDF files with text extraction, chunking, and metadata handling.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize the ingestion pipeline.

        Args:
            vector_store: VectorStore instance. Creates one if not provided.
            chunk_size: Target size for text chunks in characters.
            chunk_overlap: Number of overlapping characters between chunks.
        """
        self.vector_store = vector_store or VectorStore()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_from_pdf(self, file_path: str | Path) -> str:
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text content as a string.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a PDF.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected PDF file, got: {file_path.suffix}")

        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n\n".join(text_parts)

    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> list[str]:
        """
        Split text into overlapping chunks.

        Uses sentence-aware splitting to avoid breaking in the middle of sentences.

        Args:
            text: Text to chunk.
            chunk_size: Target chunk size. Defaults to instance setting.
            chunk_overlap: Overlap size. Defaults to instance setting.

        Returns:
            List of text chunks.
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap

        if not text or not text.strip():
            return []

        # Clean up the text
        text = re.sub(r'\s+', ' ', text).strip()

        # Split into sentences (simple approach)
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))

                # Calculate overlap - keep sentences that fit in overlap
                overlap_chunk = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= chunk_overlap:
                        overlap_chunk.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break

                current_chunk = overlap_chunk
                current_length = overlap_length

            current_chunk.append(sentence)
            current_length += sentence_length

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def extract_metadata(self, file_path: str | Path) -> dict:
        """
        Extract metadata from a document file.

        Args:
            file_path: Path to the document.

        Returns:
            Dictionary of metadata.
        """
        file_path = Path(file_path)

        metadata = {
            "filename": file_path.name,
            "file_path": str(file_path.absolute()),
            "file_type": file_path.suffix.lower().lstrip("."),
        }

        # Try to infer document type from path
        path_str = str(file_path).lower()
        if "regulatory" in path_str:
            metadata["doc_type"] = "regulatory"
        elif "clinical" in path_str or "formulary" in path_str:
            metadata["doc_type"] = "clinical"
        elif "institutional" in path_str or "sop" in path_str:
            metadata["doc_type"] = "institutional"
        else:
            metadata["doc_type"] = "general"

        # Extract PDF-specific metadata if available
        if file_path.suffix.lower() == ".pdf" and file_path.exists():
            try:
                with pdfplumber.open(file_path) as pdf:
                    metadata["page_count"] = len(pdf.pages)
                    if pdf.metadata:
                        if pdf.metadata.get("Title"):
                            metadata["title"] = pdf.metadata["Title"]
                        if pdf.metadata.get("Author"):
                            metadata["author"] = pdf.metadata["Author"]
            except Exception:
                pass

        return metadata

    def generate_chunk_id(self, file_path: str | Path, chunk_index: int) -> str:
        """
        Generate a unique ID for a document chunk.

        Args:
            file_path: Path to the source file.
            chunk_index: Index of the chunk within the document.

        Returns:
            Unique chunk ID.
        """
        file_path = Path(file_path)
        content = f"{file_path.absolute()}:{chunk_index}"
        hash_str = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"{file_path.stem}_{chunk_index}_{hash_str}"

    def ingest_file(
        self,
        file_path: str | Path,
        additional_metadata: Optional[dict] = None,
    ) -> list[str]:
        """
        Ingest a single file into the vector store.

        Args:
            file_path: Path to the file to ingest.
            additional_metadata: Optional additional metadata to add to all chunks.

        Returns:
            List of chunk IDs that were added.
        """
        file_path = Path(file_path)

        # Extract text
        text = self.extract_text_from_pdf(file_path)

        if not text.strip():
            return []

        # Chunk the text
        chunks = self.chunk_text(text)

        if not chunks:
            return []

        # Prepare metadata
        base_metadata = self.extract_metadata(file_path)
        if additional_metadata:
            base_metadata.update(additional_metadata)

        # Generate IDs and prepare chunk metadata
        ids = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_id = self.generate_chunk_id(file_path, i)
            ids.append(chunk_id)

            chunk_metadata = base_metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            metadatas.append(chunk_metadata)

        # Add to vector store
        self.vector_store.add_documents(
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
        )

        return ids

    def ingest_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        additional_metadata: Optional[dict] = None,
    ) -> dict:
        """
        Ingest all PDF files in a directory.

        Args:
            directory: Path to directory containing documents.
            recursive: Whether to search subdirectories.
            additional_metadata: Optional metadata to add to all documents.

        Returns:
            Dictionary with ingestion results.
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Find all PDF files
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = list(directory.glob(pattern))

        results = {
            "total_files": len(pdf_files),
            "successful": 0,
            "failed": 0,
            "total_chunks": 0,
            "files": [],
        }

        for pdf_file in pdf_files:
            try:
                chunk_ids = self.ingest_file(pdf_file, additional_metadata)
                results["successful"] += 1
                results["total_chunks"] += len(chunk_ids)
                results["files"].append({
                    "file": str(pdf_file),
                    "status": "success",
                    "chunks": len(chunk_ids),
                })
            except Exception as e:
                results["failed"] += 1
                results["files"].append({
                    "file": str(pdf_file),
                    "status": "failed",
                    "error": str(e),
                })

        return results
