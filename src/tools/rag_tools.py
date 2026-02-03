"""
RAG Tools for Agent Use.

Provides tools that agents can use to search the regulatory knowledge base.
"""

from typing import Optional

from crewai.tools import BaseTool

from src.rag.vector_store import VectorStore


class RegulatorySearchTool(BaseTool):
    """
    Tool for searching regulatory documents in the knowledge base.
    
    Agents can use this tool to find relevant information from:
    - The Guide for the Care and Use of Laboratory Animals
    - PHS Policy on Humane Care
    - AVMA Euthanasia Guidelines
    - Institutional SOPs and policies
    """
    
    name: str = "regulatory_search"
    description: str = (
        "Search the regulatory knowledge base for information about animal care, "
        "IACUC requirements, pain categories, euthanasia methods, surgical procedures, "
        "and other regulatory guidance. Input should be a search query string."
    )
    
    vector_store: Optional[VectorStore] = None
    
    def __init__(self, vector_store: Optional[VectorStore] = None, **kwargs):
        """Initialize the tool with optional vector store."""
        super().__init__(**kwargs)
        if vector_store is None:
            self.vector_store = VectorStore()
        else:
            self.vector_store = vector_store
    
    def _run(self, query: str) -> str:
        """
        Execute the search and return formatted results.
        
        Args:
            query: Search query text
            
        Returns:
            Formatted string with search results and citations
        """
        # Query the vector store
        results = self.vector_store.query(
            query_text=query,
            n_results=5,
        )
        
        # Format results
        if not results["ids"][0]:
            return "No relevant documents found for this query."
        
        formatted_results = []
        for i, (doc_id, document, metadata, distance) in enumerate(
            zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ):
            source = metadata.get("filename", "Unknown source")
            doc_type_label = metadata.get("doc_type", "Unknown type")
            chunk_info = f"Chunk {metadata.get('chunk_index', '?')}/{metadata.get('total_chunks', '?')}"
            
            formatted_results.append(
                f"--- Result {i + 1} ---\n"
                f"Source: {source} ({doc_type_label})\n"
                f"Location: {chunk_info}\n"
                f"Relevance: {1 - distance:.2%}\n"
                f"Content:\n{document}\n"
            )
        
        return "\n".join(formatted_results)


class SpeciesGuidanceTool(BaseTool):
    """
    Tool for finding species-specific regulatory guidance.
    
    Searches for guidance specific to a particular species and topic.
    """
    
    name: str = "species_guidance"
    description: str = (
        "Find species-specific guidance for animal care and procedures. "
        "Input should be 'species topic' format, e.g., 'mouse housing' or 'rat anesthesia'."
    )
    
    vector_store: Optional[VectorStore] = None
    
    def __init__(self, vector_store: Optional[VectorStore] = None, **kwargs):
        """Initialize the tool with optional vector store."""
        super().__init__(**kwargs)
        if vector_store is None:
            self.vector_store = VectorStore()
        else:
            self.vector_store = vector_store
    
    def _run(self, query: str) -> str:
        """
        Search for species-specific guidance.
        
        Args:
            query: Species and topic, e.g., "mouse housing"
            
        Returns:
            Formatted search results
        """
        # Enhance query for better results
        enhanced_query = f"{query} requirements guidelines"
        
        results = self.vector_store.query(
            query_text=enhanced_query,
            n_results=5,
        )
        
        if not results["ids"][0]:
            return f"No specific guidance found for: {query}"
        
        formatted_results = [f"Species-specific guidance for: {query.upper()}\n"]
        
        for i, (document, metadata) in enumerate(
            zip(results["documents"][0], results["metadatas"][0])
        ):
            source = metadata.get("filename", "Unknown")
            content = document[:800] + "..." if len(document) > 800 else document
            formatted_results.append(f"\n[{i + 1}] From {source}:\n{content}")
        
        return "\n".join(formatted_results)


class EuthanasiaMethodTool(BaseTool):
    """
    Tool for finding AVMA-approved euthanasia methods by species.
    
    Returns approved euthanasia methods and requirements for a given species.
    """
    
    name: str = "euthanasia_methods"
    description: str = (
        "Find AVMA-approved euthanasia methods for a specific species. "
        "Input should be the species name, e.g., 'mouse' or 'rabbit'."
    )
    
    vector_store: Optional[VectorStore] = None
    
    def __init__(self, vector_store: Optional[VectorStore] = None, **kwargs):
        """Initialize the tool with optional vector store."""
        super().__init__(**kwargs)
        if vector_store is None:
            self.vector_store = VectorStore()
        else:
            self.vector_store = vector_store
    
    def _run(self, species: str) -> str:
        """
        Search for euthanasia methods for a species.
        
        Args:
            species: The animal species
            
        Returns:
            Formatted euthanasia guidance
        """
        query = f"euthanasia methods {species} AVMA approved acceptable"
        
        results = self.vector_store.query(
            query_text=query,
            n_results=5,
        )
        
        if not results["ids"][0]:
            return f"No euthanasia guidance found for {species}."
        
        formatted_results = [f"AVMA Euthanasia Guidance for {species.upper()}:\n"]
        
        for i, (document, metadata) in enumerate(
            zip(results["documents"][0], results["metadatas"][0])
        ):
            source = metadata.get("filename", "Unknown")
            content = document[:800] + "..." if len(document) > 800 else document
            formatted_results.append(f"\n[{i + 1}] From {source}:\n{content}")
        
        return "\n".join(formatted_results)
