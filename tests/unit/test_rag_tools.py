"""
Unit tests for RAG Tools.
"""

import tempfile
import pytest

from src.rag.vector_store import VectorStore
from src.tools.rag_tools import (
    RegulatorySearchTool,
    SpeciesGuidanceTool,
    EuthanasiaMethodTool,
)


@pytest.fixture
def populated_vector_store():
    """Create a vector store with sample regulatory documents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = VectorStore(
            persist_directory=temp_dir,
            collection_name="test_rag_tools",
        )
        
        # Add sample regulatory documents
        documents = [
            "Pain Category C: Animals upon which teaching, research, experiments, or tests will be conducted involving no pain, distress, or use of pain-relieving drugs. Examples include observational studies and blood draws.",
            "Pain Category D: Animals upon which experiments will be conducted involving accompanying pain or distress for which appropriate anesthetic, analgesic, or tranquilizing drugs will be used. Examples include survival surgery with proper anesthesia.",
            "Pain Category E: Animals upon which experiments will be conducted involving accompanying pain or distress for which the use of anesthetic, analgesic, or tranquilizing drugs will adversely affect the procedures. Requires scientific justification.",
            "Mouse housing requirements: Mice should be housed in groups unless scientifically justified for single housing. Cage space should allow for normal movement and social behavior. Temperature should be maintained at 68-79°F.",
            "Rat anesthesia protocols: Isoflurane is the preferred inhalant anesthetic for rats. Induction at 3-4% and maintenance at 1.5-2.5%. Ketamine/xylazine can be used for injectable anesthesia at 80-100 mg/kg ketamine and 5-10 mg/kg xylazine IP.",
            "Rabbit euthanasia: Acceptable methods include sodium pentobarbital injection (IV preferred, IP acceptable), CO2 followed by cervical dislocation as secondary method. Decapitation is conditionally acceptable with scientific justification.",
            "Survival surgery requirements: Aseptic technique is required for all survival surgical procedures. This includes sterile instruments, surgical gloves, mask, and hair covering. The surgical site must be prepared with appropriate antiseptic.",
            "Post-operative monitoring: Animals must be monitored until fully recovered from anesthesia. Pain assessment should be performed and analgesics administered as needed. Documentation of monitoring is required.",
            "IACUC review requirements: All protocols involving vertebrate animals must be reviewed and approved by the IACUC before work begins. Annual reviews are required for ongoing protocols.",
            "The 3Rs principle: Replacement, Reduction, and Refinement. Researchers must consider alternatives to animal use, minimize animal numbers while maintaining statistical validity, and refine procedures to minimize pain and distress.",
        ]
        
        metadatas = [
            {"filename": "guide.pdf", "doc_type": "regulatory", "chunk_index": 0, "total_chunks": 10},
            {"filename": "guide.pdf", "doc_type": "regulatory", "chunk_index": 1, "total_chunks": 10},
            {"filename": "guide.pdf", "doc_type": "regulatory", "chunk_index": 2, "total_chunks": 10},
            {"filename": "guide.pdf", "doc_type": "regulatory", "chunk_index": 3, "total_chunks": 10},
            {"filename": "guide.pdf", "doc_type": "clinical", "chunk_index": 0, "total_chunks": 5},
            {"filename": "avma_euthanasia.pdf", "doc_type": "regulatory", "chunk_index": 0, "total_chunks": 5},
            {"filename": "guide.pdf", "doc_type": "regulatory", "chunk_index": 4, "total_chunks": 10},
            {"filename": "guide.pdf", "doc_type": "regulatory", "chunk_index": 5, "total_chunks": 10},
            {"filename": "phs_policy.pdf", "doc_type": "regulatory", "chunk_index": 0, "total_chunks": 3},
            {"filename": "guide.pdf", "doc_type": "regulatory", "chunk_index": 6, "total_chunks": 10},
        ]
        
        store.add_documents(documents=documents, metadatas=metadatas)
        yield store


class TestRegulatorySearchTool:
    """Tests for RegulatorySearchTool."""
    
    def test_init(self, populated_vector_store):
        """Test tool initialization."""
        tool = RegulatorySearchTool(vector_store=populated_vector_store)
        assert tool.name == "regulatory_search"
        assert tool.vector_store is not None
    
    def test_search_pain_categories(self, populated_vector_store):
        """Test searching for pain category information."""
        tool = RegulatorySearchTool(vector_store=populated_vector_store)
        
        result = tool._run("pain category D requirements")
        
        assert "Pain Category D" in result
        assert "anesthetic" in result.lower() or "analgesic" in result.lower()
    
    def test_search_anesthesia(self, populated_vector_store):
        """Test searching for anesthesia information."""
        tool = RegulatorySearchTool(vector_store=populated_vector_store)
        
        result = tool._run("anesthesia protocols")
        
        assert "Result" in result
    
    def test_search_survival_surgery(self, populated_vector_store):
        """Test searching for survival surgery requirements."""
        tool = RegulatorySearchTool(vector_store=populated_vector_store)
        
        result = tool._run("survival surgery requirements")
        
        assert "surgery" in result.lower()
        assert "aseptic" in result.lower() or "sterile" in result.lower()
    
    def test_search_returns_citations(self, populated_vector_store):
        """Test that results include source citations."""
        tool = RegulatorySearchTool(vector_store=populated_vector_store)
        
        result = tool._run("IACUC requirements")
        
        assert "Source:" in result
        assert ".pdf" in result
    
    def test_search_no_results(self):
        """Test behavior when no results found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_store = VectorStore(
                persist_directory=temp_dir,
                collection_name="empty_test",
            )
            tool = RegulatorySearchTool(vector_store=empty_store)
            
            result = tool._run("nonexistent topic")
            
            assert "No relevant documents found" in result
    
    def test_search_multiple_results(self, populated_vector_store):
        """Test that search returns multiple results."""
        tool = RegulatorySearchTool(vector_store=populated_vector_store)
        
        result = tool._run("pain")
        
        # Should have results
        assert "Result" in result


class TestSpeciesGuidanceTool:
    """Tests for SpeciesGuidanceTool."""
    
    def test_init(self, populated_vector_store):
        """Test tool initialization."""
        tool = SpeciesGuidanceTool(vector_store=populated_vector_store)
        assert tool.name == "species_guidance"
    
    def test_mouse_housing(self, populated_vector_store):
        """Test finding mouse housing guidance."""
        tool = SpeciesGuidanceTool(vector_store=populated_vector_store)
        
        result = tool._run("mouse housing")
        
        assert "MOUSE HOUSING" in result
    
    def test_rat_anesthesia(self, populated_vector_store):
        """Test finding rat anesthesia guidance."""
        tool = SpeciesGuidanceTool(vector_store=populated_vector_store)
        
        result = tool._run("rat anesthesia")
        
        assert "RAT ANESTHESIA" in result


class TestEuthanasiaMethodTool:
    """Tests for EuthanasiaMethodTool."""
    
    def test_init(self, populated_vector_store):
        """Test tool initialization."""
        tool = EuthanasiaMethodTool(vector_store=populated_vector_store)
        assert tool.name == "euthanasia_methods"
    
    def test_rabbit_euthanasia(self, populated_vector_store):
        """Test finding rabbit euthanasia methods."""
        tool = EuthanasiaMethodTool(vector_store=populated_vector_store)
        
        result = tool._run(species="rabbit")
        
        assert "RABBIT" in result
        # Should find sodium pentobarbital or other methods
    
    def test_no_results_handling(self):
        """Test behavior when no euthanasia guidance found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_store = VectorStore(
                persist_directory=temp_dir,
                collection_name="empty_euthanasia_test",
            )
            tool = EuthanasiaMethodTool(vector_store=empty_store)
            
            result = tool._run(species="unicorn")
            
            assert "No euthanasia guidance found" in result
