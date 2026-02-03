"""
Unit tests for Pain Category Classification Tool.
"""

import pytest

from src.tools.pain_category_tool import (
    PainCategoryTool,
    classify_pain_category,
    PAIN_CATEGORIES,
)


class TestClassifyPainCategory:
    """Tests for the classify_pain_category function."""
    
    def test_category_c_behavioral_observation(self):
        """Test: Behavioral observation only → Category C."""
        procedures = """
        Animals will undergo behavioral observation in their home cages.
        No invasive procedures will be performed. Researchers will record
        locomotor activity and social interactions.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "C"
        assert result.confidence in ["high", "medium"]
        assert not result.requires_justification
    
    def test_category_c_non_invasive_imaging(self):
        """Test: Non-invasive imaging → Category C."""
        procedures = """
        Mice will be imaged using non-invasive MRI to assess brain structure.
        Animals will be briefly restrained but no anesthesia is required.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "C"
    
    def test_category_c_tissue_harvest_post_euthanasia(self):
        """Test: Euthanasia followed by tissue harvest → Category C."""
        procedures = """
        Animals will be euthanized by CO2 inhalation followed by cervical
        dislocation. Tissues will be harvested post-mortem for analysis.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "C"
    
    def test_category_d_surgery_with_anesthesia(self):
        """Test: Surgery with anesthesia → Category D."""
        procedures = """
        Mice will undergo survival surgery under isoflurane anesthesia.
        Carprofen will be administered for post-operative analgesia.
        Animals will be monitored daily for 7 days post-surgery.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "D"
        assert result.confidence == "high"
        assert not result.requires_justification
    
    def test_category_d_tumor_with_pain_management(self):
        """Test: Tumor implantation with pain management → Category D."""
        procedures = """
        4T1 tumor cells will be implanted subcutaneously. Animals will
        receive buprenorphine for pain management. Tumors will be measured
        every 3 days and animals euthanized before reaching humane endpoints.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "D"
        assert not result.requires_justification
    
    def test_category_d_injection_with_anesthesia(self):
        """Test: Injection procedures with anesthesia → Category D."""
        procedures = """
        Animals will receive intraperitoneal injections of test compound.
        For catheter implantation, isoflurane anesthesia will be used
        with post-procedure analgesia.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "D"
    
    def test_category_e_unrelieved_pain(self):
        """Test: Unrelieved pain with justification → Category E."""
        procedures = """
        This pain study requires assessment of nociceptive responses
        without analgesia. Pain relief would interfere with the study
        endpoints and cannot be provided.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "E"
        assert result.requires_justification
    
    def test_category_e_toxicity_lethal_dose(self):
        """Test: Toxicity study at lethal doses → Category E."""
        procedures = """
        Animals will receive the maximum tolerated dose (MTD) of the test
        compound. LD50 determination will be performed. Moribund animals
        will be euthanized.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "E"
        assert result.requires_justification
        assert "justification" in result.reasoning.lower()
    
    def test_category_e_tumor_to_endpoint(self):
        """Test: Tumor studies to death endpoint → Category E."""
        procedures = """
        Tumor-bearing mice will be monitored until death as endpoint.
        No tumor burden limits will be applied. Animals will not receive
        analgesics as this could affect tumor growth.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "E"
        assert result.requires_justification
    
    def test_category_b_breeding_only(self):
        """Test: Breeding colony → Category B."""
        procedures = """
        Animals will be maintained in a breeding colony for production
        of offspring. No experimental procedures will be performed on
        these breeding animals.
        """
        
        result = classify_pain_category(procedures)
        
        assert result.category == "B"
        assert not result.requires_justification
    
    def test_surgery_without_explicit_relief_assumes_d(self):
        """Test: Surgery without explicit pain relief mentioned assumes D."""
        procedures = """
        Mice will undergo craniotomy for electrode implantation.
        Post-operative monitoring will be performed.
        """
        
        result = classify_pain_category(procedures)
        
        # Should assume D but with recommendation to specify relief
        assert result.category == "D"
        assert result.confidence == "medium"
        assert any("anesthesia" in rec.lower() or "analgesia" in rec.lower() 
                   for rec in result.recommendations)
    
    def test_multiple_procedures_highest_category(self):
        """Test: Multiple procedures should result in highest applicable category."""
        procedures = """
        Part 1: Behavioral observation (no manipulation).
        Part 2: Survival surgery under anesthesia with analgesics.
        Part 3: Blood collection under brief anesthesia.
        """
        
        result = classify_pain_category(procedures)
        
        # Should be D due to surgery, not C due to observation
        assert result.category == "D"


class TestPainCategoryTool:
    """Tests for PainCategoryTool."""
    
    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        tool = PainCategoryTool()
        
        assert tool.name == "pain_category_classifier"
        assert "USDA" in tool.description
    
    def test_tool_returns_formatted_output(self):
        """Test tool returns properly formatted output."""
        tool = PainCategoryTool()
        
        result = tool._run("Surgery will be performed under anesthesia with carprofen analgesia.")
        
        assert "Category:" in result
        assert "Confidence:" in result
        assert "Reasoning:" in result
        assert "Recommendations:" in result
    
    def test_tool_category_e_shows_warning(self):
        """Test Category E output includes justification warning."""
        tool = PainCategoryTool()
        
        result = tool._run("Toxicity study with lethal dose, no pain relief provided.")
        
        assert "Category: E" in result
        assert "JUSTIFICATION REQUIRED" in result


class TestPainCategoryDefinitions:
    """Tests for pain category definitions."""
    
    def test_all_categories_defined(self):
        """Test all USDA categories are defined."""
        assert "B" in PAIN_CATEGORIES
        assert "C" in PAIN_CATEGORIES
        assert "D" in PAIN_CATEGORIES
        assert "E" in PAIN_CATEGORIES
    
    def test_category_structure(self):
        """Test category definitions have required fields."""
        for cat_id, cat_data in PAIN_CATEGORIES.items():
            assert "name" in cat_data
            assert "description" in cat_data
            assert "examples" in cat_data
            assert isinstance(cat_data["examples"], list)
    
    def test_category_e_requires_justification(self):
        """Test Category E is marked as requiring justification."""
        assert PAIN_CATEGORIES["E"].get("requires_justification", False)


class TestEdgeCases:
    """Tests for edge cases and complex scenarios."""
    
    def test_empty_input(self):
        """Test handling of empty input."""
        result = classify_pain_category("")
        
        # Empty input should default to C (no procedures = no pain)
        assert result.category in ["B", "C"]
    
    def test_ambiguous_procedures(self):
        """Test handling of ambiguous procedure descriptions."""
        procedures = "Animals will be used in the study."
        
        result = classify_pain_category(procedures)
        
        # Should classify but with lower confidence
        assert result.category in ["B", "C", "D", "E"]
        assert result.confidence in ["low", "medium"]
    
    def test_mixed_case_input(self):
        """Test case-insensitive matching."""
        procedures = "SURGERY will be performed under ISOFLURANE ANESTHESIA"
        
        result = classify_pain_category(procedures)
        
        assert result.category == "D"
    
    def test_conflicting_indicators(self):
        """Test when both pain and relief indicators present."""
        procedures = """
        Animals will undergo surgery. Initially, no analgesia will be
        provided for the first hour to assess acute pain responses, then
        buprenorphine will be administered for pain relief.
        """
        
        result = classify_pain_category(procedures)
        
        # Should recognize the period without relief
        # This is a complex case - could be D or E depending on interpretation
        assert result.category in ["D", "E"]
