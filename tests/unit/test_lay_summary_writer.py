"""
Unit tests for Lay Summary Writer Agent.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.lay_summary_writer import (
    create_lay_summary_writer_agent,
    create_lay_summary_task,
    generate_lay_summary,
    EXAMPLE_TECHNICAL_TEXTS,
)
from src.tools.readability_tools import analyze_readability


class TestLaySummaryWriterAgent:
    """Tests for Lay Summary Writer agent creation."""
    
    def test_create_agent(self):
        """Test that agent is created with correct configuration."""
        agent = create_lay_summary_writer_agent()
        
        assert agent.role == "Lay Summary Writer"
        assert "grade" in agent.goal.lower() or "college" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_agent_has_readability_tool(self):
        """Test that agent has readability scoring tool."""
        agent = create_lay_summary_writer_agent()
        
        tool_names = [t.name for t in agent.tools]
        assert "readability_score" in tool_names
    
    def test_agent_no_delegation(self):
        """Test that agent cannot delegate (single agent task)."""
        agent = create_lay_summary_writer_agent()
        
        assert agent.allow_delegation is False


class TestLaySummaryTask:
    """Tests for Lay Summary task creation."""
    
    def test_create_task(self):
        """Test that task is created with correct configuration."""
        agent = create_lay_summary_writer_agent()
        task = create_lay_summary_task(agent, "Test technical text")
        
        assert task.agent == agent
        assert "technical" in task.description.lower() or "Test technical text" in task.description
    
    def test_task_includes_requirements(self):
        """Test that task description includes key requirements."""
        agent = create_lay_summary_writer_agent()
        task = create_lay_summary_task(agent, "Sample text")
        
        description_lower = task.description.lower()
        assert "readability" in description_lower
        assert "grade" in description_lower or "7.0" in task.description
    
    def test_task_includes_input_text(self):
        """Test that task includes the input text."""
        agent = create_lay_summary_writer_agent()
        input_text = "This is unique input text for testing."
        task = create_lay_summary_task(agent, input_text)
        
        assert input_text in task.description


class TestExampleTexts:
    """Tests for example technical texts."""
    
    def test_examples_exist(self):
        """Test that example texts are defined."""
        assert len(EXAMPLE_TECHNICAL_TEXTS) > 0
        assert "behavioral" in EXAMPLE_TECHNICAL_TEXTS
        assert "surgical" in EXAMPLE_TECHNICAL_TEXTS
        assert "tumor_model" in EXAMPLE_TECHNICAL_TEXTS
    
    def test_examples_are_technical(self):
        """Test that examples are actually technical (high grade level)."""
        for name, text in EXAMPLE_TECHNICAL_TEXTS.items():
            result = analyze_readability(text, target_grade=7.0)
            # Technical texts should have high grade levels
            assert result.flesch_kincaid_grade > 10, (
                f"Example '{name}' should be technical (grade > 10)"
            )


class TestGenerateLaySummary:
    """Tests for the generate_lay_summary function."""
    
    @pytest.mark.integration
    def test_generate_summary_basic(self):
        """
        Test that generate_lay_summary produces output.
        
        This test makes actual API calls.
        """
        # Use a short, simple technical text
        technical_text = """
        The experimental protocol involves administration of test compounds 
        via subcutaneous injection in mice to characterize pharmacokinetic parameters.
        """
        
        result = generate_lay_summary(technical_text, verbose=False)
        
        assert "summary" in result
        assert "readability" in result
        assert "passes" in result
        assert len(result["summary"]) > 0
    
    @pytest.mark.integration
    def test_summary_improves_readability(self):
        """
        Test that the summary is more readable than input.
        
        This test makes actual API calls.
        """
        technical_text = """
        The pharmacokinetic characterization involves subcutaneous administration 
        of experimental compounds with subsequent blood collection for bioanalysis.
        """
        
        # Analyze original
        original_readability = analyze_readability(technical_text)
        
        # Generate summary
        result = generate_lay_summary(technical_text, verbose=False)
        
        # Summary should have lower grade level than original
        assert result["readability"]["grade"] < original_readability.flesch_kincaid_grade + 2
    
    def test_result_structure(self):
        """Test the structure of the result dictionary."""
        # Mock the crew to avoid API calls
        with patch('src.agents.lay_summary_writer.Crew') as mock_crew:
            mock_result = MagicMock()
            mock_result.__str__ = lambda x: "Simple test summary."
            mock_crew.return_value.kickoff.return_value = mock_result
            
            result = generate_lay_summary("Test input")
            
            assert "summary" in result
            assert "readability" in result
            assert "passes" in result
            assert "grade" in result["readability"]
            assert "ease" in result["readability"]
            assert "word_count" in result["readability"]
            assert "sentence_count" in result["readability"]
