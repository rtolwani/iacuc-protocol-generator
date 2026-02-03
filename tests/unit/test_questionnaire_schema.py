"""
Unit tests for Questionnaire Schema.
"""

import pytest

from src.questionnaire.schema import (
    QuestionType,
    Option,
    ValidationRule,
    Question,
    QuestionGroup,
    BASIC_INFO_QUESTIONS,
    SPECIES_QUESTIONS,
    PROCEDURE_QUESTIONS,
    SURGERY_QUESTIONS,
    TUMOR_QUESTIONS,
    CATEGORY_E_QUESTIONS,
    ALL_QUESTION_GROUPS,
    get_question_by_id,
    get_group_by_id,
)


class TestQuestionType:
    """Tests for QuestionType enum."""
    
    def test_text_type_exists(self):
        """Test TEXT type exists."""
        assert QuestionType.TEXT == "text"
    
    def test_single_select_exists(self):
        """Test SINGLE_SELECT type exists."""
        assert QuestionType.SINGLE_SELECT == "single_select"
    
    def test_multi_select_exists(self):
        """Test MULTI_SELECT type exists."""
        assert QuestionType.MULTI_SELECT == "multi_select"
    
    def test_all_types_defined(self):
        """Test all expected types are defined."""
        expected_types = [
            "text", "textarea", "number", "single_select",
            "multi_select", "date", "yes_no", "file"
        ]
        actual_types = [qt.value for qt in QuestionType]
        
        for expected in expected_types:
            assert expected in actual_types


class TestOption:
    """Tests for Option model."""
    
    def test_create_basic_option(self):
        """Test creating basic option."""
        option = Option(value="mouse", label="Mouse")
        
        assert option.value == "mouse"
        assert option.label == "Mouse"
    
    def test_option_with_help_text(self):
        """Test option with help text."""
        option = Option(
            value="mouse",
            label="Mouse",
            help_text="Common laboratory mouse",
        )
        
        assert option.help_text == "Common laboratory mouse"
    
    def test_option_with_trigger(self):
        """Test option that triggers branch."""
        option = Option(
            value="surgery",
            label="Surgery",
            triggers_branch="surgery_branch",
        )
        
        assert option.triggers_branch == "surgery_branch"


class TestValidationRule:
    """Tests for ValidationRule model."""
    
    def test_create_required_rule(self):
        """Test creating required rule."""
        rule = ValidationRule(
            rule_type="required",
            value=True,
            message="This field is required",
        )
        
        assert rule.rule_type == "required"
    
    def test_create_min_length_rule(self):
        """Test creating min length rule."""
        rule = ValidationRule(
            rule_type="min_length",
            value=10,
            message="Must be at least 10 characters",
        )
        
        assert rule.rule_type == "min_length"
        assert rule.value == 10
    
    def test_create_pattern_rule(self):
        """Test creating pattern rule."""
        rule = ValidationRule(
            rule_type="pattern",
            value=r"^\d+$",
            message="Must be numeric",
        )
        
        assert rule.rule_type == "pattern"


class TestQuestion:
    """Tests for Question model."""
    
    def test_create_text_question(self):
        """Test creating text question."""
        question = Question(
            id="test_q",
            question_type=QuestionType.TEXT,
            label="Test Question",
        )
        
        assert question.id == "test_q"
        assert question.question_type == QuestionType.TEXT
    
    def test_question_defaults(self):
        """Test question default values."""
        question = Question(
            id="test",
            question_type=QuestionType.TEXT,
            label="Test",
        )
        
        assert question.required == True
        assert question.options == []
        assert question.validation == []
    
    def test_question_with_options(self):
        """Test question with options."""
        question = Question(
            id="species",
            question_type=QuestionType.SINGLE_SELECT,
            label="Select species",
            options=[
                Option(value="mouse", label="Mouse"),
                Option(value="rat", label="Rat"),
            ],
        )
        
        assert len(question.options) == 2
    
    def test_question_with_validation(self):
        """Test question with validation rules."""
        question = Question(
            id="title",
            question_type=QuestionType.TEXT,
            label="Title",
            validation=[
                ValidationRule(
                    rule_type="min_length",
                    value=10,
                    message="Too short",
                ),
            ],
        )
        
        assert len(question.validation) == 1
    
    def test_question_with_conditional(self):
        """Test question with conditional display."""
        question = Question(
            id="details",
            question_type=QuestionType.TEXTAREA,
            label="Details",
            depends_on="has_details",
            show_when={"has_details": True},
        )
        
        assert question.depends_on == "has_details"
        assert question.show_when == {"has_details": True}


class TestQuestionGroup:
    """Tests for QuestionGroup model."""
    
    def test_create_group(self):
        """Test creating question group."""
        group = QuestionGroup(
            id="test_group",
            title="Test Group",
            questions=[],
        )
        
        assert group.id == "test_group"
        assert group.title == "Test Group"
    
    def test_group_with_questions(self):
        """Test group with questions."""
        group = QuestionGroup(
            id="test",
            title="Test",
            questions=[
                Question(
                    id="q1",
                    question_type=QuestionType.TEXT,
                    label="Question 1",
                ),
                Question(
                    id="q2",
                    question_type=QuestionType.TEXT,
                    label="Question 2",
                ),
            ],
        )
        
        assert len(group.questions) == 2
    
    def test_group_with_branch(self):
        """Test group with branch ID."""
        group = QuestionGroup(
            id="surgery",
            title="Surgery Questions",
            branch_id="surgery_branch",
            questions=[],
        )
        
        assert group.branch_id == "surgery_branch"


class TestBasicInfoQuestions:
    """Tests for basic info question group."""
    
    def test_group_exists(self):
        """Test group exists."""
        assert BASIC_INFO_QUESTIONS is not None
        assert BASIC_INFO_QUESTIONS.id == "basic_info"
    
    def test_has_title_question(self):
        """Test has protocol title question."""
        question_ids = [q.id for q in BASIC_INFO_QUESTIONS.questions]
        assert "protocol_title" in question_ids
    
    def test_has_pi_question(self):
        """Test has PI question."""
        question_ids = [q.id for q in BASIC_INFO_QUESTIONS.questions]
        assert "pi_name" in question_ids
    
    def test_has_research_description(self):
        """Test has research description question."""
        question_ids = [q.id for q in BASIC_INFO_QUESTIONS.questions]
        assert "research_description" in question_ids


class TestSpeciesQuestions:
    """Tests for species question group."""
    
    def test_group_exists(self):
        """Test group exists."""
        assert SPECIES_QUESTIONS is not None
        assert SPECIES_QUESTIONS.id == "species"
    
    def test_has_species_question(self):
        """Test has species question."""
        question_ids = [q.id for q in SPECIES_QUESTIONS.questions]
        assert "species" in question_ids
    
    def test_species_has_options(self):
        """Test species question has options."""
        species_q = get_question_by_id("species")
        assert len(species_q.options) > 5
    
    def test_species_options_trigger_branches(self):
        """Test some species options trigger branches."""
        species_q = get_question_by_id("species")
        
        options_with_branches = [
            o for o in species_q.options if o.triggers_branch
        ]
        assert len(options_with_branches) > 0
    
    def test_has_total_animals_question(self):
        """Test has total animals question."""
        question_ids = [q.id for q in SPECIES_QUESTIONS.questions]
        assert "total_animals" in question_ids


class TestProcedureQuestions:
    """Tests for procedure question group."""
    
    def test_group_exists(self):
        """Test group exists."""
        assert PROCEDURE_QUESTIONS is not None
        assert PROCEDURE_QUESTIONS.id == "procedures"
    
    def test_has_procedure_types(self):
        """Test has procedure types question."""
        question_ids = [q.id for q in PROCEDURE_QUESTIONS.questions]
        assert "procedure_types" in question_ids
    
    def test_procedure_types_is_multi_select(self):
        """Test procedure types is multi-select."""
        proc_q = get_question_by_id("procedure_types")
        assert proc_q.question_type == QuestionType.MULTI_SELECT
    
    def test_has_pain_category(self):
        """Test has pain category question."""
        question_ids = [q.id for q in PROCEDURE_QUESTIONS.questions]
        assert "pain_category" in question_ids
    
    def test_has_euthanasia_method(self):
        """Test has euthanasia method question."""
        question_ids = [q.id for q in PROCEDURE_QUESTIONS.questions]
        assert "euthanasia_method" in question_ids


class TestBranchQuestions:
    """Tests for branch-specific question groups."""
    
    def test_surgery_branch_exists(self):
        """Test surgery branch exists."""
        assert SURGERY_QUESTIONS is not None
        assert SURGERY_QUESTIONS.branch_id == "surgery_branch"
    
    def test_tumor_branch_exists(self):
        """Test tumor branch exists."""
        assert TUMOR_QUESTIONS is not None
        assert TUMOR_QUESTIONS.branch_id == "tumor_branch"
    
    def test_category_e_branch_exists(self):
        """Test category E branch exists."""
        assert CATEGORY_E_QUESTIONS is not None
        assert CATEGORY_E_QUESTIONS.branch_id == "category_e_branch"


class TestAllQuestionGroups:
    """Tests for all question groups collection."""
    
    def test_has_multiple_groups(self):
        """Test has multiple groups."""
        assert len(ALL_QUESTION_GROUPS) >= 3
    
    def test_groups_have_unique_ids(self):
        """Test all groups have unique IDs."""
        ids = [g.id for g in ALL_QUESTION_GROUPS]
        assert len(ids) == len(set(ids))


class TestGetQuestionById:
    """Tests for get_question_by_id function."""
    
    def test_find_existing_question(self):
        """Test finding existing question."""
        question = get_question_by_id("protocol_title")
        
        assert question is not None
        assert question.id == "protocol_title"
    
    def test_returns_none_for_missing(self):
        """Test returns None for missing question."""
        question = get_question_by_id("nonexistent_question")
        
        assert question is None
    
    def test_finds_nested_question(self):
        """Test finds question in different groups."""
        # From basic info
        q1 = get_question_by_id("pi_name")
        assert q1 is not None
        
        # From procedures
        q2 = get_question_by_id("pain_category")
        assert q2 is not None


class TestGetGroupById:
    """Tests for get_group_by_id function."""
    
    def test_find_existing_group(self):
        """Test finding existing group."""
        group = get_group_by_id("basic_info")
        
        assert group is not None
        assert group.id == "basic_info"
    
    def test_returns_none_for_missing(self):
        """Test returns None for missing group."""
        group = get_group_by_id("nonexistent_group")
        
        assert group is None


class TestRegulatoryReferences:
    """Tests for regulatory references."""
    
    def test_some_questions_have_references(self):
        """Test some questions have regulatory references."""
        questions_with_refs = []
        for group in ALL_QUESTION_GROUPS:
            for q in group.questions:
                if q.regulatory_reference:
                    questions_with_refs.append(q)
        
        assert len(questions_with_refs) > 0
    
    def test_total_animals_has_reference(self):
        """Test total animals question has reference."""
        q = get_question_by_id("total_animals")
        assert q.regulatory_reference is not None
    
    def test_pain_category_has_reference(self):
        """Test pain category has reference."""
        q = get_question_by_id("pain_category")
        assert q.regulatory_reference is not None
