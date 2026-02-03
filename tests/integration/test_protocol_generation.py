"""
Integration tests for full protocol generation.

These tests validate the complete protocol generation workflow
with realistic inputs.
"""

import pytest

from src.agents.crew import (
    ProtocolInput,
    generate_protocol,
    quick_crew_check,
)


# Test inputs for different study types
BEHAVIORAL_INPUT = ProtocolInput(
    title="Effects of Environmental Enrichment on Anxiety-Related Behavior",
    pi_name="Dr. Jane Smith",
    species="mouse",
    strain="C57BL/6J",
    total_animals=60,
    research_description=(
        "This study investigates how environmental enrichment affects "
        "anxiety-related behaviors in mice."
    ),
    procedures=(
        "Behavioral testing including elevated plus maze and open field test. "
        "Euthanasia by CO2 inhalation followed by cervical dislocation."
    ),
    study_duration="6 weeks",
    primary_endpoint="Time spent in open arms",
)

SURGICAL_INPUT = ProtocolInput(
    title="Cranial Window Implantation for In Vivo Imaging",
    pi_name="Dr. John Doe",
    species="mouse",
    strain="Thy1-GFP",
    total_animals=30,
    research_description=(
        "This study uses two-photon microscopy through a chronic cranial window."
    ),
    procedures=(
        "Survival surgery for cranial window implantation under isoflurane. "
        "Post-operative analgesia with buprenorphine. "
        "Euthanasia by pentobarbital overdose."
    ),
    study_duration="8 weeks",
    primary_endpoint="Neuronal activity patterns",
)

TUMOR_INPUT = ProtocolInput(
    title="Efficacy of Novel Anti-Cancer Agent",
    pi_name="Dr. Sarah Johnson",
    species="mouse",
    strain="BALB/c nude",
    total_animals=80,
    research_description=(
        "Testing efficacy of a novel anti-cancer compound in tumor xenograft model."
    ),
    procedures=(
        "Subcutaneous tumor implantation. Daily oral gavage treatment. "
        "Tumor measurements twice weekly. "
        "Euthanasia when tumor reaches 1500mm3 or by CO2."
    ),
    study_duration="6 weeks",
    primary_endpoint="Tumor volume",
)


class TestQuickValidation:
    """Tests for quick validation without LLM."""
    
    def test_behavioral_input_valid(self):
        """Test behavioral study input is valid."""
        result = quick_crew_check(BEHAVIORAL_INPUT)
        
        assert result["is_valid"]
        assert len(result["validation_errors"]) == 0
    
    def test_surgical_input_valid(self):
        """Test surgical study input is valid."""
        result = quick_crew_check(SURGICAL_INPUT)
        
        assert result["is_valid"]
    
    def test_tumor_input_valid(self):
        """Test tumor study input is valid."""
        result = quick_crew_check(TUMOR_INPUT)
        
        assert result["is_valid"]
    
    def test_identifies_all_agents(self):
        """Test that all 8 agents are identified."""
        result = quick_crew_check(BEHAVIORAL_INPUT)
        
        assert len(result["agents"]) == 8
    
    def test_shows_task_sequence(self):
        """Test that task sequence is shown."""
        result = quick_crew_check(SURGICAL_INPUT)
        
        assert len(result["task_sequence"]) == 8


class TestInputValidation:
    """Tests for input validation."""
    
    def test_missing_title_fails(self):
        """Test that missing title fails validation."""
        invalid_input = ProtocolInput(
            title="",
            pi_name="Test",
            species="mouse",
            total_animals=10,
            research_description="Test",
            procedures="Test",
        )
        
        result = quick_crew_check(invalid_input)
        
        assert not result["is_valid"]
        assert any("title" in e.lower() for e in result["validation_errors"])
    
    def test_missing_species_fails(self):
        """Test that missing species fails validation."""
        invalid_input = ProtocolInput(
            title="Test",
            pi_name="Test",
            species="",
            total_animals=10,
            research_description="Test",
            procedures="Test",
        )
        
        result = quick_crew_check(invalid_input)
        
        assert not result["is_valid"]
        assert any("species" in e.lower() for e in result["validation_errors"])
    
    def test_zero_animals_fails(self):
        """Test that zero animals fails validation."""
        invalid_input = ProtocolInput(
            title="Test",
            pi_name="Test",
            species="mouse",
            total_animals=0,
            research_description="Test",
            procedures="Test",
        )
        
        result = quick_crew_check(invalid_input)
        
        assert not result["is_valid"]
        assert any("animal" in e.lower() for e in result["validation_errors"])
    
    def test_negative_animals_fails(self):
        """Test that negative animals fails validation."""
        invalid_input = ProtocolInput(
            title="Test",
            pi_name="Test",
            species="mouse",
            total_animals=-5,
            research_description="Test",
            procedures="Test",
        )
        
        result = quick_crew_check(invalid_input)
        
        assert not result["is_valid"]
    
    def test_empty_description_fails(self):
        """Test that empty description fails validation."""
        invalid_input = ProtocolInput(
            title="Test",
            pi_name="Test",
            species="mouse",
            total_animals=10,
            research_description="",
            procedures="Test",
        )
        
        result = quick_crew_check(invalid_input)
        
        assert not result["is_valid"]


class TestInputSummary:
    """Tests for input summary generation."""
    
    def test_summary_includes_species(self):
        """Test that summary includes species."""
        result = quick_crew_check(BEHAVIORAL_INPUT)
        
        assert result["input_summary"]["species"] == "mouse"
    
    def test_summary_includes_animals(self):
        """Test that summary includes animal count."""
        result = quick_crew_check(BEHAVIORAL_INPUT)
        
        assert result["input_summary"]["total_animals"] == 60
    
    def test_summary_tracks_optional_fields(self):
        """Test that summary tracks optional fields."""
        result = quick_crew_check(BEHAVIORAL_INPUT)
        
        assert "has_strain" in result["input_summary"]
        assert "has_duration" in result["input_summary"]
        assert "has_endpoint" in result["input_summary"]


class TestDifferentSpecies:
    """Tests with different species."""
    
    def test_rat_input(self):
        """Test with rat species."""
        rat_input = ProtocolInput(
            title="Rat Behavioral Study",
            pi_name="Test PI",
            species="rat",
            strain="Sprague Dawley",
            total_animals=40,
            research_description="Behavioral study in rats.",
            procedures="Behavioral testing and euthanasia by CO2.",
        )
        
        result = quick_crew_check(rat_input)
        
        assert result["is_valid"]
        assert result["input_summary"]["species"] == "rat"
    
    def test_rabbit_input(self):
        """Test with rabbit species (USDA covered)."""
        rabbit_input = ProtocolInput(
            title="Rabbit Immunology Study",
            pi_name="Test PI",
            species="rabbit",
            strain="New Zealand White",
            total_animals=20,
            research_description="Antibody production study.",
            procedures="Immunization and blood collection.",
        )
        
        result = quick_crew_check(rabbit_input)
        
        assert result["is_valid"]


@pytest.mark.integration
class TestFullProtocolGeneration:
    """
    Full protocol generation tests.
    
    These require API keys and may take several minutes.
    Run with: pytest -m integration
    """
    
    @pytest.mark.timeout(300)
    def test_behavioral_protocol_generation(self):
        """Test generating a complete behavioral protocol."""
        result = generate_protocol(BEHAVIORAL_INPUT, verbose=False)
        
        assert result.success
        assert result.protocol_sections.get("lay_summary")
        assert result.protocol_sections.get("procedures")
    
    @pytest.mark.timeout(300)
    def test_surgical_protocol_generation(self):
        """Test generating a complete surgical protocol."""
        result = generate_protocol(SURGICAL_INPUT, verbose=False)
        
        assert result.success
        
        # Surgical protocol should mention anesthesia
        all_output = " ".join(str(v) for v in result.agent_outputs.values())
        assert "anesthesia" in all_output.lower() or "isoflurane" in all_output.lower()
    
    @pytest.mark.timeout(300)
    def test_tumor_protocol_generation(self):
        """Test generating a complete tumor model protocol."""
        result = generate_protocol(TUMOR_INPUT, verbose=False)
        
        assert result.success
        
        # Tumor protocol should mention endpoints
        all_output = " ".join(str(v) for v in result.agent_outputs.values())
        assert "endpoint" in all_output.lower() or "tumor" in all_output.lower()
    
    @pytest.mark.timeout(300)
    def test_protocol_has_all_sections(self):
        """Test that generated protocol has all expected sections."""
        result = generate_protocol(BEHAVIORAL_INPUT, verbose=False)
        
        assert result.success
        
        # Check for key sections
        expected_keys = [
            "title", "species", "total_animals",
            "lay_summary", "procedures"
        ]
        
        for key in expected_keys:
            assert key in result.protocol_sections
    
    @pytest.mark.timeout(300)
    def test_protocol_has_agent_outputs(self):
        """Test that protocol has outputs from all agents."""
        result = generate_protocol(BEHAVIORAL_INPUT, verbose=False)
        
        assert result.success
        
        # Should have outputs from multiple agents
        assert len(result.agent_outputs) > 0
