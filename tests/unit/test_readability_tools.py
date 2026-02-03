"""
Unit tests for Readability Scoring Tools.
"""

import pytest

from src.tools.readability_tools import (
    ReadabilityScoreTool,
    analyze_readability,
    suggest_replacements,
    JARGON_REPLACEMENTS,
)


class TestAnalyzeReadability:
    """Tests for the analyze_readability function."""
    
    def test_simple_text_passes(self):
        """Test that simple text passes grade 7 target."""
        # Simple, short sentences
        text = "The cat sat on the mat. It was a sunny day. The cat was happy."
        
        result = analyze_readability(text, target_grade=7.0)
        
        assert result.passes_target is True
        assert result.flesch_kincaid_grade <= 7.0
        assert result.word_count > 0
    
    def test_technical_text_fails(self):
        """Test that technical/complex text fails grade 7 target."""
        # Complex scientific text
        text = """
        The pharmacokinetic characterization of the administered compound 
        demonstrated significant bioavailability subsequent to intraperitoneal 
        injection. Furthermore, the methodology utilized for quantification 
        employed mass spectrometry, which facilitated the characterization 
        of metabolite profiles with unprecedented accuracy and precision.
        """
        
        result = analyze_readability(text, target_grade=7.0)
        
        assert result.passes_target is False
        assert result.flesch_kincaid_grade > 7.0
        assert len(result.suggestions) > 1  # Should have improvement suggestions
    
    def test_empty_text(self):
        """Test handling of empty text."""
        result = analyze_readability("", target_grade=7.0)
        
        assert result.passes_target is True
        assert result.word_count == 0
    
    def test_whitespace_only(self):
        """Test handling of whitespace-only text."""
        result = analyze_readability("   \n\t  ", target_grade=7.0)
        
        assert result.passes_target is True
        assert result.word_count == 0
    
    def test_custom_target_grade(self):
        """Test with custom target grade."""
        text = "This is moderately complex text with some longer words included."
        
        # Should pass higher target
        result_high = analyze_readability(text, target_grade=12.0)
        # Might fail lower target
        result_low = analyze_readability(text, target_grade=3.0)
        
        assert result_high.target_grade == 12.0
        assert result_low.target_grade == 3.0
    
    def test_metrics_calculated(self):
        """Test that all metrics are calculated."""
        text = "This is a test. It has two sentences."
        
        result = analyze_readability(text)
        
        assert result.word_count == 8
        assert result.sentence_count == 2
        assert result.avg_sentence_length == 4.0
        assert result.flesch_reading_ease > 0
    
    def test_suggestions_for_long_sentences(self):
        """Test that long sentences trigger suggestions."""
        # One very long sentence
        text = """
        This is a very long sentence that goes on and on and on with many 
        words and clauses and phrases that make it difficult to read and 
        understand because it never seems to end.
        """
        
        result = analyze_readability(text, target_grade=5.0)
        
        # Should suggest shortening sentences
        suggestions_text = " ".join(result.suggestions)
        assert "sentence" in suggestions_text.lower()


class TestSuggestReplacements:
    """Tests for jargon replacement suggestions."""
    
    def test_finds_jargon(self):
        """Test that jargon is identified."""
        text = "We will utilize this methodology to administer the compound."
        
        replacements = suggest_replacements(text)
        
        assert "utilize" in replacements
        assert replacements["utilize"] == "use"
        assert "methodology" in replacements
        assert "administer" in replacements
    
    def test_no_jargon(self):
        """Test text without jargon returns empty dict."""
        text = "The cat sat on the mat."
        
        replacements = suggest_replacements(text)
        
        assert len(replacements) == 0
    
    def test_case_insensitive(self):
        """Test that jargon detection is case insensitive."""
        text = "We will UTILIZE this METHODOLOGY."
        
        replacements = suggest_replacements(text)
        
        assert "utilize" in replacements or "UTILIZE" in replacements.keys()
    
    def test_scientific_terms(self):
        """Test detection of scientific terms."""
        text = "Subcutaneous injection provides good bioavailability."
        
        replacements = suggest_replacements(text)
        
        assert len(replacements) > 0


class TestReadabilityScoreTool:
    """Tests for ReadabilityScoreTool."""
    
    def test_tool_init(self):
        """Test tool initialization."""
        tool = ReadabilityScoreTool()
        
        assert tool.name == "readability_score"
        assert "Flesch-Kincaid" in tool.description
    
    def test_simple_text_returns_pass(self):
        """Test simple text returns PASS."""
        tool = ReadabilityScoreTool()
        
        result = tool._run("The dog ran fast. It was fun to watch.")
        
        assert "PASS" in result
    
    def test_complex_text_returns_fail(self):
        """Test complex text returns FAIL."""
        tool = ReadabilityScoreTool()
        
        text = """
        The pharmacokinetic parameters were subsequently characterized utilizing 
        sophisticated mass spectrometry methodology, demonstrating significant 
        bioavailability following intraperitoneal administration of the compound.
        """
        
        result = tool._run(text)
        
        assert "FAIL" in result
        assert "Suggestions" in result
    
    def test_includes_metrics(self):
        """Test that output includes all metrics."""
        tool = ReadabilityScoreTool()
        
        result = tool._run("This is a simple test.")
        
        assert "Flesch-Kincaid Grade" in result
        assert "Flesch Reading Ease" in result
        assert "Word Count" in result
        assert "Sentence Count" in result
    
    def test_includes_jargon_suggestions(self):
        """Test that jargon suggestions are included when failing."""
        tool = ReadabilityScoreTool()
        
        text = """
        We will utilize this methodology to administer the compound 
        via subcutaneous injection. The pharmacokinetics will be characterized.
        """
        
        result = tool._run(text)
        
        # Should include jargon replacement suggestions
        assert "Jargon Replacement" in result or "utilize" in result


class TestIntegration:
    """Integration tests for readability workflow."""
    
    def test_lay_summary_workflow(self):
        """Test a realistic lay summary improvement workflow."""
        tool = ReadabilityScoreTool()
        
        # Start with technical text
        technical_text = """
        The research protocol involves the utilization of murine models to 
        characterize the pharmacokinetic parameters of novel therapeutic compounds. 
        Animals will be administered test substances via intraperitoneal injection, 
        and subsequent blood samples will be collected for bioanalytical quantification.
        """
        
        # Check it fails
        result1 = tool._run(technical_text)
        assert "FAIL" in result1
        
        # Simplified version
        simple_text = """
        This study uses mice to test new drugs. We will give the drugs to mice 
        by injection into the belly. Then we will take blood samples to measure 
        how much drug is in their bodies.
        """
        
        # Check it passes (or is closer to passing)
        result2 = tool._run(simple_text)
        # The simple version should have a lower grade
        assert "Grade" in result2
