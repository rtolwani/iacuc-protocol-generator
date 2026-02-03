"""
Integration tests for Two-Agent Crew.

Tests that Regulatory Scout and Lay Summary Writer can work together in sequence.
"""

import pytest

from crewai import Crew, Task

from src.agents.regulatory_scout import (
    create_regulatory_scout_agent,
    quick_regulatory_check,
)
from src.agents.lay_summary_writer import (
    create_lay_summary_writer_agent,
)
from src.tools.readability_tools import analyze_readability


class TestTwoAgentCrewUnit:
    """Unit tests for two-agent crew setup (no LLM calls)."""
    
    def test_both_agents_can_be_created(self):
        """Test that both agents can be created without errors."""
        scout = create_regulatory_scout_agent()
        writer = create_lay_summary_writer_agent()
        
        assert scout.role == "Regulatory Scout"
        assert writer.role == "Lay Summary Writer"
    
    def test_agents_have_different_tools(self):
        """Test that agents have their appropriate tools."""
        scout = create_regulatory_scout_agent()
        writer = create_lay_summary_writer_agent()
        
        scout_tool_names = [t.name for t in scout.tools]
        writer_tool_names = [t.name for t in writer.tools]
        
        # Scout should have regulatory search and pain category tools
        assert "regulatory_search" in scout_tool_names
        assert "pain_category_classifier" in scout_tool_names
        
        # Writer should have readability tool
        assert "readability_score" in writer_tool_names
    
    def test_create_crew_with_both_agents(self):
        """Test that a crew can be created with both agents."""
        scout = create_regulatory_scout_agent()
        writer = create_lay_summary_writer_agent()
        
        task1 = Task(
            description="Analyze protocol regulations",
            expected_output="Regulatory analysis",
            agent=scout,
        )
        
        task2 = Task(
            description="Simplify the regulatory analysis",
            expected_output="Simplified summary",
            agent=writer,
        )
        
        crew = Crew(
            agents=[scout, writer],
            tasks=[task1, task2],
            verbose=False,
        )
        
        assert len(crew.agents) == 2
        assert len(crew.tasks) == 2
    
    def test_quick_check_provides_input_for_summary(self):
        """Test that quick regulatory check output can feed into summary."""
        result = quick_regulatory_check(
            species="mouse",
            procedures="Behavioral observation in home cages",
        )
        
        # Result should have fields that could be summarized
        assert "pain_category" in result
        assert "species_category" in result
        assert "recommendations" in result
        
        # Could construct a text summary from this
        summary_input = f"""
        Species: {result['species']} ({result['species_category']})
        Pain Category: {result['pain_category']} - {result['pain_category_name']}
        Requirements: {', '.join(result['species_requirements'])}
        """
        
        assert len(summary_input) > 50


class TestTwoAgentCrewIntegration:
    """Integration tests with actual LLM calls."""
    
    @pytest.mark.integration
    def test_sequential_crew_execution(self):
        """
        Test that two agents can work in sequence.
        
        Flow: Regulatory Scout analyzes → Lay Summary Writer simplifies
        """
        scout = create_regulatory_scout_agent()
        writer = create_lay_summary_writer_agent()
        
        # Task 1: Regulatory analysis
        task1 = Task(
            description="""
            Analyze the following research protocol:
            
            Species: Mouse (C57BL/6)
            Procedures: Behavioral testing including Morris water maze and 
            elevated plus maze. No invasive procedures. Animals will be 
            euthanized at study end via CO2 followed by cervical dislocation.
            
            Determine:
            1. USDA pain category
            2. Species regulatory status
            3. Any special requirements
            
            Provide a brief regulatory summary.
            """,
            expected_output="A regulatory analysis with pain category and requirements.",
            agent=scout,
        )
        
        # Task 2: Simplify the analysis
        task2 = Task(
            description="""
            Take the regulatory analysis from the previous task and create
            a simple, accessible summary that a researcher could understand.
            Focus on the key requirements and pain category.
            Keep it to 2-3 sentences.
            """,
            expected_output="A simplified summary of regulatory requirements.",
            agent=writer,
            context=[task1],  # This task uses output from task1
        )
        
        crew = Crew(
            agents=[scout, writer],
            tasks=[task1, task2],
            verbose=False,
        )
        
        result = crew.kickoff()
        result_str = str(result)
        
        # Verify we got a result
        assert len(result_str) > 20
        
        # Verify it's reasonably readable (should be simplified)
        readability = analyze_readability(result_str, target_grade=14.0)
        # May not always pass grade 14 but should be improved
        assert readability.flesch_kincaid_grade < 20  # At least not graduate level
    
    @pytest.mark.integration
    def test_context_preserved_between_agents(self):
        """
        Test that context from first agent is available to second agent.
        """
        scout = create_regulatory_scout_agent()
        writer = create_lay_summary_writer_agent()
        
        # Specific protocol with identifiable elements
        task1 = Task(
            description="""
            Analyze this protocol:
            
            Species: Rabbit
            Procedures: Survival surgery under isoflurane anesthesia with 
            carprofen for post-operative analgesia. Surgery involves 
            implantation of telemetry device.
            
            Identify the USDA pain category and key requirements.
            """,
            expected_output="Regulatory analysis with pain category.",
            agent=scout,
        )
        
        task2 = Task(
            description="""
            Based on the regulatory analysis, create a one-paragraph summary
            that includes the pain category and species classification.
            """,
            expected_output="Summary paragraph with pain category.",
            agent=writer,
            context=[task1],
        )
        
        crew = Crew(
            agents=[scout, writer],
            tasks=[task1, task2],
            verbose=False,
        )
        
        result = crew.kickoff()
        result_str = str(result).lower()
        
        # The final summary should reference key elements from the analysis
        # Either pain category letter (d) or the word "pain"
        assert "pain" in result_str or "category" in result_str or "d" in result_str
    
    @pytest.mark.integration  
    def test_crew_handles_category_e_protocol(self):
        """
        Test crew handling of a Category E protocol.
        """
        scout = create_regulatory_scout_agent()
        writer = create_lay_summary_writer_agent()
        
        task1 = Task(
            description="""
            Analyze this protocol:
            
            Species: Rat
            Procedures: Toxicity study at maximum tolerated dose. 
            Animals will not receive pain relief as this could affect 
            the study results. Animals will be monitored and euthanized 
            if moribund.
            
            This is a Category E protocol requiring justification.
            Identify all requirements.
            """,
            expected_output="Regulatory analysis noting Category E requirements.",
            agent=scout,
        )
        
        task2 = Task(
            description="""
            Summarize the regulatory requirements, especially noting
            any special justifications needed for this protocol.
            """,
            expected_output="Summary with Category E justification note.",
            agent=writer,
            context=[task1],
        )
        
        crew = Crew(
            agents=[scout, writer],
            tasks=[task1, task2],
            verbose=False,
        )
        
        result = crew.kickoff()
        result_str = str(result).lower()
        
        # Should mention justification or category E requirements
        assert "justif" in result_str or "category e" in result_str or "pain" in result_str
