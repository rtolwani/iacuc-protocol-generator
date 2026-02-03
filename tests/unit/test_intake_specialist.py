"""
Unit tests for Intake Specialist Agent.
"""

import pytest

from src.agents.intake_specialist import (
    create_intake_specialist_agent,
    create_intake_task,
    quick_intake,
    extract_research_profile,
    generate_clarifying_questions,
    calculate_completeness,
    ResearchProfile,
    ClarifyingQuestion,
    REQUIRED_FIELDS,
    RECOMMENDED_FIELDS,
)


class TestExtractResearchProfile:
    """Tests for profile extraction."""
    
    def test_extracts_species(self):
        """Test species extraction."""
        profile = extract_research_profile(
            "This study will use C57BL/6 mice for behavioral testing."
        )
        
        assert profile.species == "mouse"
    
    def test_extracts_strain(self):
        """Test strain extraction."""
        profile = extract_research_profile(
            "C57BL/6J mice will be used in this study."
        )
        
        assert profile.strain is not None
        assert "C57BL" in profile.strain.upper()
    
    def test_extracts_total_animals(self):
        """Test total animal extraction."""
        profile = extract_research_profile(
            "A total of 60 animals will be used in this study."
        )
        
        assert profile.total_animals == 60
    
    def test_extracts_animals_per_group(self):
        """Test animals per group extraction."""
        profile = extract_research_profile(
            "There will be 10 per group in each treatment arm."
        )
        
        assert profile.animals_per_group == 10
    
    def test_extracts_number_of_groups(self):
        """Test number of groups extraction."""
        profile = extract_research_profile(
            "The study has 6 groups including controls."
        )
        
        assert profile.number_of_groups == 6
    
    def test_extracts_procedures(self):
        """Test procedure extraction."""
        profile = extract_research_profile(
            "Animals will undergo surgery, followed by behavioral testing and blood collection."
        )
        
        assert len(profile.procedures) > 0
        assert "Surgery" in profile.procedures or "Behavioral testing" in profile.procedures
    
    def test_extracts_anesthesia(self):
        """Test anesthesia extraction."""
        profile = extract_research_profile(
            "Surgery will be performed under isoflurane anesthesia."
        )
        
        assert profile.anesthesia_method is not None
        assert "isoflurane" in profile.anesthesia_method.lower()
    
    def test_extracts_analgesia(self):
        """Test analgesia extraction."""
        profile = extract_research_profile(
            "Buprenorphine will be provided for post-operative pain."
        )
        
        assert profile.analgesia_method is not None
        assert "buprenorphine" in profile.analgesia_method.lower()
    
    def test_extracts_euthanasia(self):
        """Test euthanasia extraction."""
        profile = extract_research_profile(
            "Euthanasia will be by CO2 inhalation followed by cervical dislocation."
        )
        
        assert profile.euthanasia_method is not None


class TestCalculateCompleteness:
    """Tests for completeness calculation."""
    
    def test_empty_profile_low_completeness(self):
        """Test that empty profile has low completeness."""
        profile = ResearchProfile()
        profile = calculate_completeness(profile)
        
        assert profile.completeness_score < 0.5
        assert len(profile.missing_fields) > 0
    
    def test_complete_profile_high_completeness(self):
        """Test that complete profile has high completeness."""
        profile = ResearchProfile(
            species="mouse",
            strain="C57BL/6",
            source="Jackson Labs",
            total_animals=60,
            animals_per_group=10,
            number_of_groups=6,
            procedures=["Surgery", "Behavioral testing"],
            anesthesia_method="Isoflurane",
            analgesia_method="Buprenorphine",
            euthanasia_method="CO2",
            study_duration="8 weeks",
            primary_endpoint="Tumor volume",
        )
        profile = calculate_completeness(profile)
        
        assert profile.completeness_score > 0.8
        assert len(profile.missing_fields) < 3
    
    def test_missing_required_identified(self):
        """Test that missing required fields are identified."""
        profile = ResearchProfile(
            species="mouse",
            # Missing: total_animals, procedures, euthanasia_method
        )
        profile = calculate_completeness(profile)
        
        # Check that missing required fields are in the list
        missing_required = [f for f in profile.missing_fields if f in REQUIRED_FIELDS]
        assert len(missing_required) > 0


class TestGenerateClarifyingQuestions:
    """Tests for clarifying question generation."""
    
    def test_generates_questions_for_missing(self):
        """Test that questions are generated for missing fields."""
        profile = ResearchProfile(
            species="mouse",
            # Missing many fields
        )
        profile = calculate_completeness(profile)
        
        questions = generate_clarifying_questions(profile)
        
        assert len(questions) > 0
    
    def test_required_questions_first(self):
        """Test that required questions come first."""
        profile = ResearchProfile()  # Empty - all missing
        profile = calculate_completeness(profile)
        
        questions = generate_clarifying_questions(profile)
        
        # First questions should be required priority
        if questions:
            assert questions[0].priority == "required"
    
    def test_questions_have_examples(self):
        """Test that questions include example answers."""
        profile = ResearchProfile()
        profile = calculate_completeness(profile)
        
        questions = generate_clarifying_questions(profile)
        
        # At least some questions should have examples
        questions_with_examples = [q for q in questions if q.example_answer]
        assert len(questions_with_examples) > 0
    
    def test_no_questions_for_complete_profile(self):
        """Test that complete profile generates no questions."""
        profile = ResearchProfile(
            species="mouse",
            strain="C57BL/6",
            source="Jackson Labs",
            total_animals=60,
            animals_per_group=10,
            number_of_groups=6,
            procedures=["Surgery"],
            anesthesia_method="Isoflurane",
            analgesia_method="Buprenorphine",
            euthanasia_method="CO2",
            study_duration="8 weeks",
            primary_endpoint="Tumor volume",
        )
        profile = calculate_completeness(profile)
        
        questions = generate_clarifying_questions(profile)
        
        # Should have few or no questions
        assert len(questions) < 3


class TestQuickIntake:
    """Tests for quick intake function."""
    
    def test_returns_all_fields(self):
        """Test that all expected fields are returned."""
        result = quick_intake(
            "We will use 60 C57BL/6 mice for behavioral testing."
        )
        
        assert "profile" in result
        assert "clarifying_questions" in result
        assert "completeness_score" in result
    
    def test_extracts_from_complex_description(self):
        """Test extraction from complex description."""
        description = """
        This study will investigate anxiety-related behavior.
        N=60 mice will be used for behavioral testing including the elevated plus 
        maze and open field test. At study end, animals will be euthanized by 
        CO2 inhalation followed by cervical dislocation.
        """
        
        result = quick_intake(description)
        
        assert result["profile"]["species"] == "mouse"
        assert result["profile"]["total_animals"] == 60
        assert result["profile"]["euthanasia_method"] is not None
    
    def test_identifies_missing_required(self):
        """Test identification of missing required fields."""
        result = quick_intake("Simple study with mice.")
        
        # Should identify some missing required fields
        assert "missing_required" in result
        # Species is found, but other required fields likely missing


class TestIntakeSpecialistAgent:
    """Tests for agent creation."""
    
    def test_create_agent(self):
        """Test that agent is created correctly."""
        agent = create_intake_specialist_agent()
        
        assert agent.role == "Intake Specialist"
    
    def test_agent_has_classifier_tool(self):
        """Test that agent has the classifier tool."""
        agent = create_intake_specialist_agent()
        
        tool_names = [t.name for t in agent.tools]
        assert "research_classifier" in tool_names
    
    def test_agent_goal_mentions_extraction(self):
        """Test that agent goal mentions extraction."""
        agent = create_intake_specialist_agent()
        
        assert "extract" in agent.goal.lower() or "parameter" in agent.goal.lower()


class TestIntakeTask:
    """Tests for task creation."""
    
    def test_create_task(self):
        """Test that task is created correctly."""
        agent = create_intake_specialist_agent()
        task = create_intake_task(
            agent=agent,
            research_description="Test study with mice",
        )
        
        assert task.agent == agent
        assert "Test study with mice" in task.description
    
    def test_task_includes_extraction_requirements(self):
        """Test that task includes extraction requirements."""
        agent = create_intake_specialist_agent()
        task = create_intake_task(
            agent=agent,
            research_description="Research description",
        )
        
        description_lower = task.description.lower()
        
        assert "species" in description_lower
        assert "procedures" in description_lower
        assert "gaps" in description_lower or "missing" in description_lower


class TestModels:
    """Tests for Pydantic models."""
    
    def test_research_profile_defaults(self):
        """Test ResearchProfile default values."""
        profile = ResearchProfile()
        
        assert profile.species is None
        assert profile.procedures == []
        assert profile.completeness_score == 0.0
    
    def test_research_profile_with_values(self):
        """Test ResearchProfile with values."""
        profile = ResearchProfile(
            species="mouse",
            total_animals=50,
            procedures=["Surgery", "Imaging"],
        )
        
        assert profile.species == "mouse"
        assert profile.total_animals == 50
        assert len(profile.procedures) == 2
    
    def test_clarifying_question(self):
        """Test ClarifyingQuestion model."""
        question = ClarifyingQuestion(
            field="species",
            question="What species will be used?",
            priority="required",
            example_answer="C57BL/6 mice",
        )
        
        assert question.field == "species"
        assert question.priority == "required"


class TestConstants:
    """Tests for constants."""
    
    def test_required_fields_defined(self):
        """Test that required fields are defined."""
        assert len(REQUIRED_FIELDS) >= 3
        assert "species" in REQUIRED_FIELDS
        assert "euthanasia_method" in REQUIRED_FIELDS
    
    def test_recommended_fields_defined(self):
        """Test that recommended fields are defined."""
        assert len(RECOMMENDED_FIELDS) >= 5
        assert "strain" in RECOMMENDED_FIELDS
    
    def test_no_overlap_required_recommended(self):
        """Test no overlap between required and recommended."""
        overlap = set(REQUIRED_FIELDS) & set(RECOMMENDED_FIELDS)
        assert len(overlap) == 0
