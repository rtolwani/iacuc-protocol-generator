"""
End-to-End tests for Lay Summary Writer.

These tests verify the complete workflow with real LLM calls.
Run with: pytest tests/integration/test_lay_summary_e2e.py -v
"""

import pytest

from src.agents.lay_summary_writer import (
    generate_lay_summary,
    EXAMPLE_TECHNICAL_TEXTS,
)
from src.tools.readability_tools import analyze_readability


# Sample research descriptions for testing
SAMPLE_RESEARCH_DESCRIPTIONS = {
    "behavioral_study": """
    This protocol investigates the effects of chronic stress paradigms on 
    cognitive function in C57BL/6J mice utilizing a battery of behavioral 
    assessments including the Morris water maze for spatial memory, the 
    elevated plus maze for anxiety-related behaviors, and novel object 
    recognition for working memory. Animals will be subjected to chronic 
    unpredictable mild stress (CUMS) for 28 days, following which behavioral 
    testing will be conducted. Tissue will be harvested for subsequent 
    immunohistochemical and molecular analyses.
    """,
    
    "surgical_study": """
    The proposed research involves bilateral stereotaxic injection of 
    adeno-associated viral vectors (AAV) into the hippocampal formation 
    of adult Sprague-Dawley rats for optogenetic manipulation of specific 
    neuronal populations. Animals will undergo survival surgery under 
    isoflurane anesthesia with pre-operative carprofen administration. 
    Post-operative monitoring will occur daily for 7 days, with animals 
    remaining in study for up to 8 weeks prior to terminal procedures.
    """,
    
    "tumor_model": """
    This study employs a syngeneic orthotopic tumor model utilizing 
    4T1 mammary carcinoma cells implanted into the fourth mammary fat 
    pad of BALB/c mice. Tumor progression will be monitored via caliper 
    measurements and bioluminescence imaging. Animals will receive 
    experimental therapeutics via intraperitoneal injection on a q3d 
    schedule. Humane endpoints include tumor burden exceeding 2000mm³ 
    or significant deterioration in body condition score.
    """,
    
    "pharmacology_study": """
    This protocol examines the pharmacokinetic and pharmacodynamic 
    properties of novel small molecule inhibitors targeting the 
    PI3K/AKT/mTOR signaling pathway in xenograft models of non-small 
    cell lung carcinoma. Immunocompromised nude mice will receive 
    subcutaneous implantation of H1975 tumor cells. Treatment cohorts 
    will receive test compounds via oral gavage at escalating doses 
    with plasma sampling for PK analysis at predetermined timepoints.
    """,
}


class TestLaySummaryEndToEnd:
    """End-to-end tests for lay summary generation."""
    
    @pytest.mark.integration
    def test_behavioral_study_summary(self):
        """Test summarizing a behavioral study description."""
        text = SAMPLE_RESEARCH_DESCRIPTIONS["behavioral_study"]
        
        result = generate_lay_summary(text, verbose=False)
        
        # Check structure
        assert "summary" in result
        assert "readability" in result
        assert "passes" in result
        
        # Check readability passes target
        assert result["passes"], (
            f"Summary failed readability: grade {result['readability']['grade']}"
        )
        
        # Check summary is not empty and reasonable length
        assert len(result["summary"]) > 50
        assert result["readability"]["word_count"] > 20
    
    @pytest.mark.integration
    def test_surgical_study_summary(self):
        """Test summarizing a surgical study description."""
        text = SAMPLE_RESEARCH_DESCRIPTIONS["surgical_study"]
        
        result = generate_lay_summary(text, verbose=False)
        
        assert result["passes"], (
            f"Summary failed readability: grade {result['readability']['grade']}"
        )
        assert len(result["summary"]) > 50
    
    @pytest.mark.integration
    def test_tumor_model_summary(self):
        """Test summarizing a tumor model study description."""
        text = SAMPLE_RESEARCH_DESCRIPTIONS["tumor_model"]
        
        result = generate_lay_summary(text, verbose=False)
        
        assert result["passes"], (
            f"Summary failed readability: grade {result['readability']['grade']}"
        )
        assert len(result["summary"]) > 50
    
    @pytest.mark.integration
    def test_pharmacology_study_summary(self):
        """Test summarizing a pharmacology study description."""
        text = SAMPLE_RESEARCH_DESCRIPTIONS["pharmacology_study"]
        
        result = generate_lay_summary(text, verbose=False)
        
        assert result["passes"], (
            f"Summary failed readability: grade {result['readability']['grade']}"
        )
        assert len(result["summary"]) > 50
    
    @pytest.mark.integration
    def test_summary_improves_readability(self):
        """Test that summaries are more readable than original text."""
        text = SAMPLE_RESEARCH_DESCRIPTIONS["behavioral_study"]
        
        # Analyze original
        original = analyze_readability(text, target_grade=14.0)
        
        # Generate summary
        result = generate_lay_summary(text, verbose=False)
        
        # Summary should be at or below target grade
        assert result["readability"]["grade"] <= 14.0, (
            f"Summary grade {result['readability']['grade']} exceeds target 14.0"
        )
        
        # Summary should generally be more readable than highly technical input
        # (allowing some tolerance since original might already be close)
        assert result["readability"]["grade"] <= original.flesch_kincaid_grade + 2
    
    @pytest.mark.integration
    def test_all_example_texts(self):
        """Test that all built-in example texts can be summarized."""
        for name, text in EXAMPLE_TECHNICAL_TEXTS.items():
            result = generate_lay_summary(text, verbose=False)
            
            assert result["passes"], (
                f"Example '{name}' failed: grade {result['readability']['grade']}"
            )
            assert len(result["summary"]) > 30, (
                f"Example '{name}' summary too short"
            )


class TestLaySummaryQuality:
    """Tests for summary quality attributes."""
    
    @pytest.mark.integration
    def test_summary_preserves_key_concepts(self):
        """Test that summaries preserve key research concepts."""
        text = SAMPLE_RESEARCH_DESCRIPTIONS["behavioral_study"]
        
        result = generate_lay_summary(text, verbose=False)
        summary_lower = result["summary"].lower()
        
        # Should mention key concepts (in some form)
        # At least one of these should appear
        key_concepts = ["stress", "mice", "memory", "test", "brain", "behavior"]
        found_concepts = [c for c in key_concepts if c in summary_lower]
        
        assert len(found_concepts) >= 2, (
            f"Summary missing key concepts. Found: {found_concepts}"
        )
    
    @pytest.mark.integration
    def test_summary_reasonable_length(self):
        """Test that summaries are reasonably concise."""
        text = SAMPLE_RESEARCH_DESCRIPTIONS["tumor_model"]
        
        result = generate_lay_summary(text, verbose=False)
        
        # Summary should be concise (not just a rewording of the full text)
        word_count = result["readability"]["word_count"]
        
        # Should be between 30-150 words typically
        assert 20 <= word_count <= 200, (
            f"Summary length {word_count} words is outside expected range"
        )
    
    @pytest.mark.integration
    def test_summary_has_complete_sentences(self):
        """Test that summaries contain complete sentences."""
        text = SAMPLE_RESEARCH_DESCRIPTIONS["surgical_study"]
        
        result = generate_lay_summary(text, verbose=False)
        
        # Should have at least one period (complete sentence)
        assert "." in result["summary"], "Summary should contain complete sentences"
        
        # Should have multiple sentences typically
        sentence_count = result["readability"]["sentence_count"]
        assert sentence_count >= 2, (
            f"Summary should have multiple sentences, got {sentence_count}"
        )
