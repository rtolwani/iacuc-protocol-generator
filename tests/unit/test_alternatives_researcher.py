"""
Unit tests for Alternatives Researcher Agent.
"""

import pytest

from src.agents.alternatives_researcher import (
    create_alternatives_researcher_agent,
    create_alternatives_research_task,
    generate_3rs_template,
    quick_3rs_check,
    THREE_RS_DEFINITIONS,
)


class TestThreeRsDefinitions:
    """Tests for 3Rs definitions."""
    
    def test_all_rs_defined(self):
        """Test that all 3Rs are defined."""
        assert "replacement" in THREE_RS_DEFINITIONS
        assert "reduction" in THREE_RS_DEFINITIONS
        assert "refinement" in THREE_RS_DEFINITIONS
    
    def test_definitions_have_required_fields(self):
        """Test that each R has required fields."""
        for r_name, r_info in THREE_RS_DEFINITIONS.items():
            assert "definition" in r_info
            assert "examples" in r_info
            assert "questions" in r_info
            assert isinstance(r_info["examples"], list)
            assert len(r_info["examples"]) > 0
    
    def test_replacement_includes_key_concepts(self):
        """Test replacement includes key alternative concepts."""
        replacement = THREE_RS_DEFINITIONS["replacement"]
        
        # Should mention common alternatives
        examples_text = " ".join(replacement["examples"]).lower()
        assert "in vitro" in examples_text
        assert "computer" in examples_text or "simulation" in examples_text
    
    def test_reduction_includes_statistics(self):
        """Test reduction mentions statistical approaches."""
        reduction = THREE_RS_DEFINITIONS["reduction"]
        
        examples_text = " ".join(reduction["examples"]).lower()
        assert "power" in examples_text or "sample size" in examples_text
    
    def test_refinement_includes_welfare(self):
        """Test refinement includes welfare measures."""
        refinement = THREE_RS_DEFINITIONS["refinement"]
        
        examples_text = " ".join(refinement["examples"]).lower()
        assert "anesthesia" in examples_text or "analgesia" in examples_text
        assert "humane" in examples_text or "endpoint" in examples_text


class TestGenerate3RsTemplate:
    """Tests for 3Rs template generation."""
    
    def test_generates_all_sections(self):
        """Test template has all 3Rs sections."""
        template = generate_3rs_template("mouse", "behavioral testing")
        
        assert "replacement" in template
        assert "reduction" in template
        assert "refinement" in template
    
    def test_includes_animal_model(self):
        """Test template includes animal model."""
        template = generate_3rs_template("rabbit", "surgery")
        
        assert template["animal_model"] == "rabbit"
        assert template["procedures"] == "surgery"
    
    def test_replacement_section_structure(self):
        """Test replacement section has required fields."""
        template = generate_3rs_template("rat", "toxicity study")
        
        replacement = template["replacement"]
        assert "search_conducted" in replacement
        assert "databases_searched" in replacement
        assert "keywords_used" in replacement
        assert "justification" in replacement
    
    def test_reduction_section_structure(self):
        """Test reduction section has required fields."""
        template = generate_3rs_template("mouse", "tumor model")
        
        reduction = template["reduction"]
        assert "method" in reduction
        assert "sample_size_justification" in reduction
        assert "statistical_approach" in reduction
    
    def test_refinement_section_structure(self):
        """Test refinement section has required fields."""
        template = generate_3rs_template("guinea pig", "testing")
        
        refinement = template["refinement"]
        assert "anesthesia_plan" in refinement
        assert "analgesia_plan" in refinement
        assert "humane_endpoints" in refinement
        assert "monitoring_plan" in refinement
    
    def test_keywords_generated_for_each_r(self):
        """Test that keywords are generated for each R."""
        template = generate_3rs_template("mouse", "surgery")
        
        assert len(template["replacement"]["keywords_used"]) > 0
        assert len(template["reduction"]["keywords_used"]) > 0
        assert len(template["refinement"]["keywords_used"]) > 0


class TestQuick3RsCheck:
    """Tests for quick 3Rs check function."""
    
    def test_returns_all_keyword_sets(self):
        """Test that all keyword sets are returned."""
        result = quick_3rs_check("mouse", "behavioral observation")
        
        assert "replacement_keywords" in result
        assert "reduction_keywords" in result
        assert "refinement_keywords" in result
    
    def test_returns_template(self):
        """Test that template is returned."""
        result = quick_3rs_check("rat", "surgery")
        
        assert "template" in result
        assert "replacement" in result["template"]
    
    def test_returns_database_list(self):
        """Test that required databases are listed."""
        result = quick_3rs_check("rabbit", "testing")
        
        assert "databases_to_search" in result
        assert "PubMed/MEDLINE" in result["databases_to_search"]
        assert "AGRICOLA" in result["databases_to_search"]
    
    def test_surgery_generates_refinement_recommendations(self):
        """Test that surgery procedures generate appropriate refinements."""
        result = quick_3rs_check("mouse", "survival surgery")
        
        recommendations = result["refinement_recommendations"]
        recommendations_text = " ".join(recommendations).lower()
        
        assert "anesthesia" in recommendations_text
        assert "analgesia" in recommendations_text
    
    def test_tumor_generates_endpoint_recommendations(self):
        """Test that tumor studies generate endpoint recommendations."""
        result = quick_3rs_check("mouse", "tumor implantation model")
        
        recommendations = result["refinement_recommendations"]
        recommendations_text = " ".join(recommendations).lower()
        
        assert "tumor" in recommendations_text
        assert "endpoint" in recommendations_text or "euthanize" in recommendations_text


class TestAlternativesResearcherAgent:
    """Tests for agent creation."""
    
    def test_create_agent(self):
        """Test that agent is created with correct configuration."""
        agent = create_alternatives_researcher_agent()
        
        assert agent.role == "Alternatives Researcher"
        assert "3Rs" in agent.goal or "alternatives" in agent.goal.lower()
    
    def test_agent_has_required_tools(self):
        """Test that agent has literature search and RAG tools."""
        agent = create_alternatives_researcher_agent()
        
        tool_names = [t.name for t in agent.tools]
        
        assert "literature_search_documentation" in tool_names
        assert "regulatory_search" in tool_names
    
    def test_agent_backstory_includes_3rs(self):
        """Test that agent backstory mentions 3Rs expertise."""
        agent = create_alternatives_researcher_agent()
        
        backstory_lower = agent.backstory.lower()
        assert "3rs" in backstory_lower or "replacement" in backstory_lower


class TestAlternativesResearchTask:
    """Tests for task creation."""
    
    def test_create_task(self):
        """Test that task is created with correct content."""
        agent = create_alternatives_researcher_agent()
        task = create_alternatives_research_task(
            agent=agent,
            animal_model="mouse",
            procedures="behavioral testing",
            study_objectives="Study anxiety behavior",
        )
        
        assert task.agent == agent
        assert "mouse" in task.description
        assert "behavioral" in task.description
        assert "anxiety" in task.description
    
    def test_task_includes_all_3rs(self):
        """Test that task description includes all 3Rs."""
        agent = create_alternatives_researcher_agent()
        task = create_alternatives_research_task(
            agent=agent,
            animal_model="rat",
            procedures="surgery",
            study_objectives="Test device efficacy",
        )
        
        description_lower = task.description.lower()
        
        assert "replacement" in description_lower
        assert "reduction" in description_lower
        assert "refinement" in description_lower
    
    def test_task_mentions_tool_usage(self):
        """Test that task mentions using tools."""
        agent = create_alternatives_researcher_agent()
        task = create_alternatives_research_task(
            agent=agent,
            animal_model="rabbit",
            procedures="testing",
            study_objectives="Evaluate safety",
        )
        
        assert "literature_search" in task.description.lower() or "search" in task.description.lower()


class TestIntegration:
    """Integration tests (without actual LLM calls)."""
    
    def test_template_and_keywords_align(self):
        """Test that template keywords match quick check keywords."""
        animal = "mouse"
        procedures = "tumor model surgery"
        
        template = generate_3rs_template(animal, procedures)
        quick = quick_3rs_check(animal, procedures)
        
        # Keywords should be the same
        assert template["replacement"]["keywords_used"] == quick["replacement_keywords"]
        assert template["reduction"]["keywords_used"] == quick["reduction_keywords"]
        assert template["refinement"]["keywords_used"] == quick["refinement_keywords"]
    
    def test_full_workflow_setup(self):
        """Test that full workflow can be set up."""
        agent = create_alternatives_researcher_agent()
        task = create_alternatives_research_task(
            agent=agent,
            animal_model="mouse",
            procedures="behavioral testing",
            study_objectives="Study memory",
        )
        
        # Should be able to create a crew
        from crewai import Crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False,
        )
        
        assert len(crew.agents) == 1
        assert len(crew.tasks) == 1
