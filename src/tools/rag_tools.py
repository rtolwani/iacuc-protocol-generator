"""
RAG Tools for Agent Use.

Provides tools that agents can use to search the regulatory knowledge base.
"""

from typing import Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.rag.vector_store import VectorStore


class RegulatorySearchInput(BaseModel):
    """Input schema for regulatory search tool."""
    
    query: str = Field(
        description="The search query to find relevant regulatory information"
    )
    doc_type: Optional[str] = Field(
        default=None,
        description="Filter by document type: 'regulatory', 'clinical', 'institutional', or 'general'"
    )
    n_results: int = Field(
        default=5,
        description="Number of results to return (1-10)"
    )


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
    description: str = """Search the regulatory knowledge base for information about 
animal care, IACUC requirements, pain categories, euthanasia methods, surgical procedures, 
and other regulatory guidance. Returns relevant excerpts with source citations."""
    
    args_schema: Type[BaseModel] = RegulatorySearchInput
    
    vector_store: Optional[VectorStore] = None
    
    def __init__(self, vector_store: Optional[VectorStore] = None, **kwargs):
        """Initialize the tool with optional vector store."""
        super().__init__(**kwargs)
        self.vector_store = vector_store or VectorStore()
    
    def _run(
        self,
        query: str,
        doc_type: Optional[str] = None,
        n_results: int = 5,
    ) -> str:
        """
        Execute the search and return formatted results.
        
        Args:
            query: Search query text
            doc_type: Optional filter by document type
            n_results: Number of results to return
            
        Returns:
            Formatted string with search results and citations
        """
        # Validate n_results
        n_results = max(1, min(10, n_results))
        
        # Build metadata filter
        where_filter = None
        if doc_type and doc_type in ["regulatory", "clinical", "institutional", "general"]:
            where_filter = {"doc_type": doc_type}
        
        # Query the vector store
        results = self.vector_store.query(
            query_text=query,
            n_results=n_results,
            where=where_filter,
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
    
    async def _arun(
        self,
        query: str,
        doc_type: Optional[str] = None,
        n_results: int = 5,
    ) -> str:
        """Async version - just calls sync version."""
        return self._run(query, doc_type, n_results)


class SpeciesGuidanceInput(BaseModel):
    """Input schema for species-specific guidance search."""
    
    species: str = Field(
        description="The species to search guidance for (e.g., 'mouse', 'rat', 'rabbit', 'dog')"
    )
    topic: str = Field(
        description="The topic to search for (e.g., 'housing', 'anesthesia', 'euthanasia', 'surgery')"
    )


class SpeciesGuidanceTool(BaseTool):
    """
    Tool for finding species-specific regulatory guidance.
    
    Searches for guidance specific to a particular species and topic.
    """
    
    name: str = "species_guidance"
    description: str = """Find species-specific guidance for animal care and procedures. 
Provide the species name and topic to get relevant regulatory requirements."""
    
    args_schema: Type[BaseModel] = SpeciesGuidanceInput
    
    vector_store: Optional[VectorStore] = None
    
    def __init__(self, vector_store: Optional[VectorStore] = None, **kwargs):
        """Initialize the tool with optional vector store."""
        super().__init__(**kwargs)
        self.vector_store = vector_store or VectorStore()
    
    def _run(self, species: str, topic: str) -> str:
        """
        Search for species-specific guidance.
        
        Args:
            species: The animal species
            topic: The topic of interest
            
        Returns:
            Formatted search results
        """
        # Construct a targeted query
        query = f"{species} {topic} requirements guidelines"
        
        results = self.vector_store.query(
            query_text=query,
            n_results=5,
        )
        
        if not results["ids"][0]:
            return f"No specific guidance found for {species} regarding {topic}."
        
        formatted_results = [
            f"Species-specific guidance for {species.upper()} - {topic.upper()}:\n"
        ]
        
        for i, (document, metadata) in enumerate(
            zip(results["documents"][0], results["metadatas"][0])
        ):
            source = metadata.get("filename", "Unknown")
            formatted_results.append(
                f"\n[{i + 1}] From {source}:\n{document[:800]}..."
                if len(document) > 800 else f"\n[{i + 1}] From {source}:\n{document}"
            )
        
        return "\n".join(formatted_results)
    
    async def _arun(self, species: str, topic: str) -> str:
        """Async version - just calls sync version."""
        return self._run(species, topic)


class EuthanasiaMethodInput(BaseModel):
    """Input schema for euthanasia method search."""
    
    species: str = Field(
        description="The species for euthanasia method lookup"
    )


class EuthanasiaMethodTool(BaseTool):
    """
    Tool for finding AVMA-approved euthanasia methods by species.
    
    Returns approved euthanasia methods and requirements for a given species.
    """
    
    name: str = "euthanasia_methods"
    description: str = """Find AVMA-approved euthanasia methods for a specific species. 
Returns acceptable methods, contraindications, and requirements."""
    
    args_schema: Type[BaseModel] = EuthanasiaMethodInput
    
    vector_store: Optional[VectorStore] = None
    
    def __init__(self, vector_store: Optional[VectorStore] = None, **kwargs):
        """Initialize the tool with optional vector store."""
        super().__init__(**kwargs)
        self.vector_store = vector_store or VectorStore()
    
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
        
        formatted_results = [
            f"AVMA Euthanasia Guidance for {species.upper()}:\n"
        ]
        
        for i, (document, metadata) in enumerate(
            zip(results["documents"][0], results["metadatas"][0])
        ):
            source = metadata.get("filename", "Unknown")
            formatted_results.append(
                f"\n[{i + 1}] From {source}:\n{document[:800]}..."
                if len(document) > 800 else f"\n[{i + 1}] From {source}:\n{document}"
            )
        
        return "\n".join(formatted_results)
    
    async def _arun(self, species: str) -> str:
        """Async version - just calls sync version."""
        return self._run(species)
