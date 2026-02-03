"""
Unit tests for Regulatory Scout Agent.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.regulatory_scout import (
    create_regulatory_scout_agent,
    create_regulatory_scout_task,
    identify_species_category,
    identify_procedure_requirements,
    quick_regulatory_check,
    SPECIES_REGULATIONS,
    PROCEDURE_REGULATIONS,
)


class TestIdentifySpeciesCategory:
    """Tests for species category identification."""
    
    def test_usda_covered_rabbit(self):
        """Test: Rabbit → USDA Covered."""
        result = identify_species_category("rabbit")
        
        assert result["category"] == "USDA Covered"
        assert "USDA" in result["requirements"][0]
    
    def test_usda_covered_dog(self):
        """Test: Dog → USDA Covered."""
        result = identify_species_category("dog")
        
        assert result["category"] == "USDA Covered"
    
    def test_usda_covered_primate(self):
        """Test: Non-human primate → USDA Covered."""
        result = identify_species_category("non-human primate")
        
        assert result["category"] == "USDA Covered"
    
    def test_usda_exempt_mouse(self):
        """Test: Mouse → USDA Exempt."""
        result = identify_species_category("mouse")
        
        assert "Exempt" in result["category"]
        assert "Not covered by USDA" in result["requirements"][0]
    
    def test_usda_exempt_rat(self):
        """Test: Rat → USDA Exempt."""
        result = identify_species_category("rat")
        
        assert "Exempt" in result["category"]
    
    def test_usda_exempt_zebrafish(self):
        """Test: Zebrafish → USDA Exempt."""
        result = identify_species_category("zebrafish")
        
        assert "Exempt" in result["category"]
    
    def test_wildlife(self):
        """Test: Wild animals → Wildlife category."""
        result = identify_species_category("wild deer")
        
        assert result["category"] == "Wildlife"
        assert "wildlife permits" in result["requirements"][0].lower()
    
    def test_case_insensitive(self):
        """Test case-insensitive species matching."""
        result1 = identify_species_category("RABBIT")
        result2 = identify_species_category("Rabbit")
        result3 = identify_species_category("rabbit")
        
        assert result1["category"] == result2["category"] == result3["category"]


class TestIdentifyProcedureRequirements:
    """Tests for procedure requirement identification."""
    
    def test_survival_surgery(self):
        """Test: Survival surgery requirements identified."""
        procedures = "Animals will undergo survival surgery under anesthesia."
        
        result = identify_procedure_requirements(procedures)
        
        assert len(result) > 0
        assert any("surgery" in r["type"].lower() for r in result)
    
    def test_food_restriction(self):
        """Test: Food restriction requirements identified."""
        procedures = "Animals will be on food restriction during behavioral testing."
        
        result = identify_procedure_requirements(procedures)
        
        assert len(result) > 0
        assert any("restriction" in r["type"].lower() for r in result)
    
    def test_controlled_substances(self):
        """Test: Controlled substance requirements identified."""
        procedures = "Ketamine will be used for anesthesia."
        
        result = identify_procedure_requirements(procedures)
        
        assert len(result) > 0
        assert any("dea" in str(r).lower() or "controlled" in str(r).lower() for r in result)
    
    def test_hazardous_agents(self):
        """Test: Biohazard requirements identified."""
        procedures = "Infectious agents will be administered to study immune response."
        
        result = identify_procedure_requirements(procedures)
        
        assert len(result) > 0
        assert any("ibc" in str(r).lower() or "hazard" in r["type"].lower() for r in result)
    
    def test_euthanasia(self):
        """Test: Euthanasia requirements identified."""
        procedures = "Animals will be euthanized at the end of the study."
        
        result = identify_procedure_requirements(procedures)
        
        assert len(result) > 0
        assert any("euthanasia" in r["type"].lower() for r in result)
    
    def test_multiple_procedures(self):
        """Test: Multiple procedure types identified."""
        procedures = """
        Animals will undergo survival surgery. Ketamine will be used for 
        anesthesia. At study end, animals will be euthanized.
        """
        
        result = identify_procedure_requirements(procedures)
        
        # Should identify multiple procedure types
        assert len(result) >= 2
    
    def test_no_special_procedures(self):
        """Test: Simple procedures return empty list."""
        procedures = "Animals will be observed in their home cages."
        
        result = identify_procedure_requirements(procedures)
        
        # Basic observation shouldn't trigger special requirements
        assert len(result) == 0


class TestQuickRegulatoryCheck:
    """Tests for quick regulatory check function."""
    
    def test_returns_all_fields(self):
        """Test that quick check returns all expected fields."""
        result = quick_regulatory_check(
            species="mouse",
            procedures="Behavioral observation only",
        )
        
        assert "species" in result
        assert "species_category" in result
        assert "pain_category" in result
        assert "procedure_requirements" in result
        assert "recommendations" in result
    
    def test_mouse_behavioral_is_category_c(self):
        """Test: Mouse + behavioral observation → Category C."""
        result = quick_regulatory_check(
            species="mouse",
            procedures="Behavioral observation in home cage",
        )
        
        assert result["pain_category"] == "C"
        assert "Exempt" in result["species_category"]
    
    def test_rabbit_surgery_is_category_d(self):
        """Test: Rabbit + surgery with anesthesia → Category D."""
        result = quick_regulatory_check(
            species="rabbit",
            procedures="Survival surgery under isoflurane anesthesia with carprofen analgesia",
        )
        
        assert result["pain_category"] == "D"
        assert result["species_category"] == "USDA Covered"
    
    def test_category_e_requires_justification(self):
        """Test: Category E procedures flag justification requirement."""
        result = quick_regulatory_check(
            species="rat",
            procedures="Toxicity study with lethal dose, no pain relief",
        )
        
        assert result["pain_category"] == "E"
        assert result["requires_justification"] is True


class TestRegulatoryScoutAgent:
    """Tests for Regulatory Scout agent creation."""
    
    def test_create_agent(self):
        """Test that agent is created with correct configuration."""
        agent = create_regulatory_scout_agent()
        
        assert agent.role == "Regulatory Scout"
        assert len(agent.tools) >= 2  # Should have pain and RAG tools
    
    def test_agent_has_required_tools(self):
        """Test that agent has pain category and RAG tools."""
        agent = create_regulatory_scout_agent()
        
        tool_names = [t.name for t in agent.tools]
        assert "pain_category_classifier" in tool_names
        assert "regulatory_search" in tool_names


class TestRegulatoryScoutTask:
    """Tests for Regulatory Scout task creation."""
    
    def test_create_task(self):
        """Test that task is created with correct content."""
        agent = create_regulatory_scout_agent()
        task = create_regulatory_scout_task(
            agent=agent,
            species="mouse",
            procedures="Behavioral testing",
        )
        
        assert task.agent == agent
        assert "mouse" in task.description
        assert "Behavioral testing" in task.description
    
    def test_task_includes_key_requirements(self):
        """Test that task description includes key analysis requirements."""
        agent = create_regulatory_scout_agent()
        task = create_regulatory_scout_task(
            agent=agent,
            species="rabbit",
            procedures="Surgery",
        )
        
        description_lower = task.description.lower()
        assert "pain category" in description_lower
        assert "species" in description_lower
        assert "permit" in description_lower or "regulation" in description_lower


class TestRegulatoryConstants:
    """Tests for regulatory constant definitions."""
    
    def test_species_regulations_defined(self):
        """Test that species regulations are defined."""
        assert "usda_covered" in SPECIES_REGULATIONS
        assert "usda_exempt" in SPECIES_REGULATIONS
        assert "wildlife" in SPECIES_REGULATIONS
    
    def test_procedure_regulations_defined(self):
        """Test that key procedure regulations are defined."""
        assert "survival_surgery" in PROCEDURE_REGULATIONS
        assert "euthanasia" in PROCEDURE_REGULATIONS
        assert "controlled_substances" in PROCEDURE_REGULATIONS
    
    def test_regulation_structure(self):
        """Test that regulations have required structure."""
        for proc_type, proc_info in PROCEDURE_REGULATIONS.items():
            assert "keywords" in proc_info
            assert "regulations" in proc_info
            assert isinstance(proc_info["keywords"], list)
            assert isinstance(proc_info["regulations"], list)
