"""
Unit tests for Drug Formulary Tool.
"""

import pytest
from pathlib import Path

from src.tools.formulary_tool import (
    FormularyLookupTool,
    DrugFormulary,
    DrugInfo,
    FormularyLookupResult,
)


@pytest.fixture
def formulary():
    """Create a formulary instance for testing."""
    return DrugFormulary()


@pytest.fixture
def tool():
    """Create a tool instance for testing."""
    return FormularyLookupTool()


class TestDrugFormulary:
    """Tests for DrugFormulary class."""
    
    def test_loads_default_formulary(self, formulary):
        """Test that default formulary loads correctly."""
        assert formulary.data is not None
        assert "drugs" in formulary.data
        assert len(formulary.data["drugs"]) > 0
    
    def test_lookup_existing_drug(self, formulary):
        """Test looking up a drug that exists."""
        result = formulary.lookup_drug("ketamine")
        
        assert result.found is True
        assert result.drug_info is not None
        assert result.drug_info.name == "Ketamine"
    
    def test_lookup_drug_case_insensitive(self, formulary):
        """Test that drug lookup is case-insensitive."""
        result1 = formulary.lookup_drug("Ketamine")
        result2 = formulary.lookup_drug("KETAMINE")
        result3 = formulary.lookup_drug("ketamine")
        
        assert result1.found == result2.found == result3.found == True
    
    def test_lookup_nonexistent_drug(self, formulary):
        """Test looking up a drug that doesn't exist."""
        result = formulary.lookup_drug("nonexistent_drug_xyz")
        
        assert result.found is False
        assert result.drug_info is None
    
    def test_lookup_with_species(self, formulary):
        """Test looking up drug with species-specific dosing."""
        result = formulary.lookup_drug("ketamine", "mouse")
        
        assert result.found is True
        assert result.species_specific is True
        assert result.drug_info.dose_range is not None
        assert "mg/kg" in result.drug_info.dose_range
    
    def test_lookup_with_unsupported_species(self, formulary):
        """Test looking up drug with unsupported species."""
        result = formulary.lookup_drug("ketamine", "elephant")
        
        assert result.found is True
        assert result.species_specific is False
    
    def test_drug_info_contains_contraindications(self, formulary):
        """Test that drug info includes contraindications."""
        result = formulary.lookup_drug("ketamine")
        
        assert result.drug_info.contraindications is not None
        assert len(result.drug_info.contraindications) > 0
    
    def test_drug_info_contains_dea_schedule(self, formulary):
        """Test that controlled drugs have DEA schedule."""
        result = formulary.lookup_drug("ketamine")
        
        assert result.drug_info.dea_schedule == "III"
    
    def test_list_drugs_for_species(self, formulary):
        """Test listing drugs available for a species."""
        drugs = formulary.list_drugs_for_species("mouse")
        
        assert len(drugs) > 0
        assert "Ketamine" in drugs
        assert "Buprenorphine" in drugs


class TestDoseValidation:
    """Tests for dose validation."""
    
    def test_valid_dose_within_range(self, formulary):
        """Test that dose within range is validated as correct."""
        result = formulary.validate_dose("ketamine", "mouse", "90 mg/kg")
        
        assert result["valid"] is True
        assert result["status"] == "APPROVED"
    
    def test_dose_below_range(self, formulary):
        """Test that dose below range is flagged."""
        result = formulary.validate_dose("ketamine", "mouse", "10 mg/kg")
        
        assert result["valid"] is False
        assert result["status"] == "BELOW_RANGE"
    
    def test_dose_above_range(self, formulary):
        """Test that dose above range is flagged."""
        result = formulary.validate_dose("ketamine", "mouse", "200 mg/kg")
        
        assert result["valid"] is False
        assert result["status"] == "ABOVE_RANGE"
    
    def test_validation_unknown_drug(self, formulary):
        """Test validation for unknown drug."""
        result = formulary.validate_dose("fakemedicine", "mouse", "10 mg/kg")
        
        assert result["valid"] is False
        assert result["status"] == "NOT_FOUND"
    
    def test_validation_unsupported_species(self, formulary):
        """Test validation for unsupported species."""
        result = formulary.validate_dose("ketamine", "elephant", "100 mg/kg")
        
        assert result["valid"] is False
        assert result["status"] == "NO_SPECIES_DATA"


class TestCombinationProtocols:
    """Tests for combination protocol lookup."""
    
    def test_get_ketamine_xylazine_protocol(self, formulary):
        """Test looking up ketamine/xylazine protocol."""
        protocol = formulary.get_combination_protocol("ketamine/xylazine")
        
        assert protocol is not None
        assert len(protocol["components"]) >= 2
    
    def test_protocol_contains_required_fields(self, formulary):
        """Test that protocol contains required information."""
        protocol = formulary.get_combination_protocol("ketamine")
        
        assert protocol is not None
        assert "name" in protocol
        assert "components" in protocol
        assert "indication" in protocol
    
    def test_protocol_not_found(self, formulary):
        """Test looking up nonexistent protocol."""
        protocol = formulary.get_combination_protocol("nonexistent protocol")
        
        assert protocol is None


class TestEmergencyDrugs:
    """Tests for emergency drug information."""
    
    def test_get_emergency_drugs(self, formulary):
        """Test getting emergency drug list."""
        emergency = formulary.get_emergency_drugs()
        
        assert len(emergency) > 0
    
    def test_emergency_drugs_have_doses(self, formulary):
        """Test that emergency drugs have dose information."""
        emergency = formulary.get_emergency_drugs()
        
        for drug in emergency:
            assert "name" in drug
            assert "dose" in drug
            assert "indication" in drug


class TestFormularyLookupTool:
    """Tests for the FormularyLookupTool."""
    
    def test_tool_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == "formulary_lookup"
        assert "drug" in tool.description.lower()
    
    def test_tool_simple_lookup(self, tool):
        """Test simple drug lookup."""
        result = tool._run("ketamine")
        
        assert "Ketamine" in result
        assert "Drug Class" in result
    
    def test_tool_species_lookup(self, tool):
        """Test species-specific lookup."""
        result = tool._run("ketamine for mouse")
        
        assert "Ketamine" in result
        assert "MOUSE" in result
        assert "Dose Range" in result
        assert "mg/kg" in result
    
    def test_tool_includes_contraindications(self, tool):
        """Test that output includes contraindications."""
        result = tool._run("ketamine")
        
        assert "Contraindications" in result
    
    def test_tool_handles_unknown_drug(self, tool):
        """Test handling of unknown drug."""
        result = tool._run("fakedrugxyz")
        
        assert "not found" in result.lower()
    
    def test_tool_parses_species_from_query(self, tool):
        """Test that tool correctly parses species from query."""
        result1 = tool._run("buprenorphine for rat")
        result2 = tool._run("carprofen for rabbit")
        
        assert "RAT" in result1
        assert "RABBIT" in result2


class TestDrugInfo:
    """Tests for DrugInfo model."""
    
    def test_create_drug_info(self):
        """Test creating DrugInfo model."""
        info = DrugInfo(
            name="Test Drug",
            drug_class="Test Class",
            dea_schedule="Not scheduled",
            dose_range="10-20 mg/kg",
            route="SC",
        )
        
        assert info.name == "Test Drug"
        assert info.dose_range == "10-20 mg/kg"
    
    def test_drug_info_optional_fields(self):
        """Test that optional fields default correctly."""
        info = DrugInfo(
            name="Test Drug",
            drug_class="Test Class",
            dea_schedule="Not scheduled",
        )
        
        assert info.dose_range is None
        assert info.contraindications == []


class TestFormularyLookupResult:
    """Tests for FormularyLookupResult model."""
    
    def test_found_result(self):
        """Test creating a found result."""
        info = DrugInfo(
            name="Test Drug",
            drug_class="Test Class",
            dea_schedule="Not scheduled",
        )
        result = FormularyLookupResult(
            found=True,
            drug_info=info,
            species_specific=True,
            message="Found test drug",
        )
        
        assert result.found is True
        assert result.drug_info.name == "Test Drug"
    
    def test_not_found_result(self):
        """Test creating a not-found result."""
        result = FormularyLookupResult(
            found=False,
            message="Drug not found",
        )
        
        assert result.found is False
        assert result.drug_info is None
