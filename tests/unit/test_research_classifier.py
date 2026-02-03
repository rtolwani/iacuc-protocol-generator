"""
Unit tests for Research Classifier Tool.
"""

import pytest

from src.tools.research_classifier import (
    ResearchClassifierTool,
    classify_research,
    classify_research_type,
    identify_procedure_types,
    identify_species_category,
    identify_special_requirements,
    estimate_pain_category,
    ResearchClassification,
    RESEARCH_TYPES,
    PROCEDURE_TYPES,
    SPECIES_CATEGORIES,
    SPECIAL_REQUIREMENTS,
)


class TestClassifyResearchType:
    """Tests for research type classification."""
    
    def test_behavioral_research(self):
        """Test classification of behavioral research."""
        result = classify_research_type(
            "Study learning and memory using Morris water maze"
        )
        assert result == "behavioral"
    
    def test_oncology_research(self):
        """Test classification of oncology research."""
        result = classify_research_type(
            "Testing new cancer therapy on tumor-bearing mice"
        )
        assert result == "oncology"
    
    def test_preclinical_research(self):
        """Test classification of preclinical research."""
        result = classify_research_type(
            "Evaluating drug efficacy for treatment of disease"
        )
        assert result == "preclinical"
    
    def test_surgical_research(self):
        """Test classification of surgical research."""
        result = classify_research_type(
            "Surgical model creation for cardiac studies"
        )
        assert result == "surgical"
    
    def test_toxicology_research(self):
        """Test classification of toxicology research."""
        result = classify_research_type(
            "Dose-response toxicity testing for safety assessment"
        )
        assert result == "toxicology"
    
    def test_defaults_to_basic(self):
        """Test that unknown research defaults to basic."""
        result = classify_research_type("Simple observation study")
        assert result == "basic"


class TestIdentifyProcedureTypes:
    """Tests for procedure type identification."""
    
    def test_identifies_surgery(self):
        """Test identification of surgical procedures."""
        procedures = identify_procedure_types(
            "Animals will undergo survival surgery with craniotomy"
        )
        assert "survival_surgery" in procedures
    
    def test_identifies_injection(self):
        """Test identification of injection procedures."""
        procedures = identify_procedure_types(
            "IP injection of test compound"
        )
        assert "injection" in procedures
    
    def test_identifies_blood_collection(self):
        """Test identification of blood collection."""
        procedures = identify_procedure_types(
            "Blood will be collected via cardiac puncture"
        )
        assert "blood_collection" in procedures
    
    def test_identifies_tumor(self):
        """Test identification of tumor implantation."""
        procedures = identify_procedure_types(
            "Tumor cells will be implanted subcutaneously"
        )
        assert "tumor_implantation" in procedures
    
    def test_identifies_multiple_procedures(self):
        """Test identification of multiple procedures."""
        procedures = identify_procedure_types(
            "Survival surgery followed by behavioral testing and blood collection"
        )
        assert "survival_surgery" in procedures
        assert "behavioral_testing" in procedures
        assert "blood_collection" in procedures
    
    def test_defaults_to_observation(self):
        """Test that no procedures defaults to observation."""
        procedures = identify_procedure_types("Animals will be observed")
        assert "observation" in procedures


class TestIdentifySpeciesCategory:
    """Tests for species category identification."""
    
    def test_usda_covered_rabbit(self):
        """Test that rabbit is USDA covered."""
        category = identify_species_category("rabbit")
        assert category == "usda_covered"
    
    def test_usda_covered_dog(self):
        """Test that dog is USDA covered."""
        category = identify_species_category("dog")
        assert category == "usda_covered"
    
    def test_usda_exempt_mouse(self):
        """Test that mouse is USDA exempt."""
        category = identify_species_category("mouse")
        assert category == "usda_exempt"
    
    def test_usda_exempt_rat(self):
        """Test that rat is USDA exempt."""
        category = identify_species_category("rat")
        assert category == "usda_exempt"
    
    def test_wildlife(self):
        """Test that wild animals are wildlife category."""
        category = identify_species_category("wild deer")
        assert category == "wildlife"
    
    def test_aquatic(self):
        """Test that frog is aquatic category."""
        category = identify_species_category("frog")
        assert category == "aquatic"


class TestIdentifySpecialRequirements:
    """Tests for special requirements identification."""
    
    def test_dea_controlled(self):
        """Test identification of DEA requirements."""
        requirements, permits = identify_special_requirements(
            "Using ketamine for anesthesia"
        )
        assert any("DEA" in r for r in requirements)
        assert any("DEA" in p for p in permits)
    
    def test_biohazard(self):
        """Test identification of biohazard requirements."""
        requirements, permits = identify_special_requirements(
            "Working with infectious pathogen BSL-2"
        )
        assert any("IBC" in r for r in requirements)
    
    def test_radiation(self):
        """Test identification of radiation requirements."""
        requirements, permits = identify_special_requirements(
            "Radioactive isotope labeling"
        )
        assert any("Radiation" in r for r in requirements)
    
    def test_field_study(self):
        """Test identification of field study requirements."""
        requirements, permits = identify_special_requirements(
            "Field study of wild populations"
        )
        assert any("Wildlife" in r for r in requirements)
    
    def test_no_special_requirements(self):
        """Test when no special requirements are needed."""
        requirements, permits = identify_special_requirements(
            "Simple behavioral observation in mice"
        )
        # May or may not have requirements depending on specifics
        assert isinstance(requirements, list)
        assert isinstance(permits, list)


class TestEstimatePainCategory:
    """Tests for pain category estimation."""
    
    def test_category_e_unrelieved_pain(self):
        """Test that unrelieved pain is Category E."""
        category = estimate_pain_category(
            ["injection"],
            "Pain study without analgesia"
        )
        assert category == "E"
    
    def test_category_d_surgery(self):
        """Test that surgery is Category D."""
        category = estimate_pain_category(
            ["survival_surgery"],
            "Survival surgery under anesthesia"
        )
        assert category == "D"
    
    def test_category_d_tumor(self):
        """Test that tumor implantation is Category D."""
        category = estimate_pain_category(
            ["tumor_implantation"],
            "Tumor model with monitoring"
        )
        assert category == "D"
    
    def test_category_c_observation(self):
        """Test that observation with testing is Category C."""
        category = estimate_pain_category(
            ["observation"],
            "Non-invasive observation test"
        )
        assert category == "C"
    
    def test_category_b_breeding(self):
        """Test that breeding is Category B."""
        category = estimate_pain_category(
            ["observation"],
            "Breeding colony maintenance"
        )
        assert category == "B"


class TestClassifyResearch:
    """Tests for complete research classification."""
    
    def test_complete_classification(self):
        """Test complete research classification."""
        result = classify_research(
            description="Survival surgery for electrode implantation followed by behavioral testing",
            species="mouse",
        )
        
        assert isinstance(result, ResearchClassification)
        assert result.research_type is not None
        assert len(result.procedure_types) > 0
        assert result.species_category is not None
        assert result.pain_category_estimate in ["B", "C", "D", "E"]
    
    def test_suggests_appropriate_agents(self):
        """Test that appropriate agents are suggested."""
        result = classify_research(
            description="Survival surgery with tumor implantation",
            species="mouse",
        )
        
        assert "Veterinary Reviewer" in result.suggested_agents
        assert "Procedure Writer" in result.suggested_agents
    
    def test_flags_category_e(self):
        """Test that Category E is flagged."""
        result = classify_research(
            description="Toxicity study without analgesia",
            species="rat",
        )
        
        assert any("Category E" in flag for flag in result.flags)
    
    def test_flags_usda_covered(self):
        """Test that USDA covered species is flagged."""
        result = classify_research(
            description="Behavioral testing",
            species="rabbit",
        )
        
        assert any("USDA" in flag for flag in result.flags)


class TestResearchClassifierTool:
    """Tests for the ResearchClassifierTool."""
    
    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        tool = ResearchClassifierTool()
        
        assert tool.name == "research_classifier"
        assert "classify" in tool.description.lower()
    
    def test_tool_basic_classification(self):
        """Test basic classification through tool."""
        tool = ResearchClassifierTool()
        
        result = tool._run(
            "species: mouse, description: behavioral testing in maze"
        )
        
        assert "Research Type:" in result
        assert "Species Category:" in result
    
    def test_tool_includes_procedures(self):
        """Test that tool output includes procedures."""
        tool = ResearchClassifierTool()
        
        result = tool._run(
            "species: rat, description: survival surgery and blood collection"
        )
        
        assert "Procedure Types:" in result
    
    def test_tool_shows_warnings(self):
        """Test that tool shows warnings for special cases."""
        tool = ResearchClassifierTool()
        
        result = tool._run(
            "species: rabbit, description: surgery using ketamine"
        )
        
        # Should have warnings for USDA covered and DEA
        assert "Flags" in result or "Special Requirements" in result


class TestConstants:
    """Tests for constant definitions."""
    
    def test_research_types_defined(self):
        """Test that research types are defined."""
        assert len(RESEARCH_TYPES) > 5
        assert "behavioral" in RESEARCH_TYPES
        assert "oncology" in RESEARCH_TYPES
    
    def test_procedure_types_defined(self):
        """Test that procedure types are defined."""
        assert len(PROCEDURE_TYPES) > 5
        assert "survival_surgery" in PROCEDURE_TYPES
        assert "injection" in PROCEDURE_TYPES
    
    def test_species_categories_defined(self):
        """Test that species categories are defined."""
        assert "usda_covered" in SPECIES_CATEGORIES
        assert "usda_exempt" in SPECIES_CATEGORIES
    
    def test_special_requirements_defined(self):
        """Test that special requirements are defined."""
        assert "dea_controlled" in SPECIAL_REQUIREMENTS
        assert "biohazard" in SPECIAL_REQUIREMENTS
    
    def test_research_types_have_keywords(self):
        """Test that research types have keywords."""
        for rtype, info in RESEARCH_TYPES.items():
            assert "keywords" in info
            assert len(info["keywords"]) > 0
    
    def test_procedure_types_have_requirements(self):
        """Test that procedure types have requirements."""
        for ptype, info in PROCEDURE_TYPES.items():
            assert "keywords" in info
            assert "requirements" in info


class TestResearchClassificationModel:
    """Tests for ResearchClassification model."""
    
    def test_create_classification(self):
        """Test creating a ResearchClassification."""
        classification = ResearchClassification(
            research_type="behavioral",
            procedure_types=["behavioral_testing"],
            species_category="usda_exempt",
            pain_category_estimate="C",
            special_requirements=[],
            required_permits=[],
            suggested_agents=["Intake Specialist"],
            flags=[],
        )
        
        assert classification.research_type == "behavioral"
        assert classification.pain_category_estimate == "C"
    
    def test_classification_with_all_fields(self):
        """Test classification with all fields populated."""
        classification = ResearchClassification(
            research_type="oncology",
            procedure_types=["tumor_implantation", "imaging"],
            species_category="usda_exempt",
            pain_category_estimate="D",
            special_requirements=["IBC Approval Required"],
            required_permits=["IBC Approval"],
            suggested_agents=["Veterinary Reviewer", "Procedure Writer"],
            flags=["Biohazard protocol"],
        )
        
        assert len(classification.procedure_types) == 2
        assert len(classification.special_requirements) == 1
        assert len(classification.flags) == 1
