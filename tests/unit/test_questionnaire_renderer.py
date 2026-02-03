"""
Unit tests for Questionnaire JSON Schema Renderer.
"""

import pytest

from src.questionnaire.renderer import (
    render_question_property,
    render_question_ui_schema,
    render_question_group,
    render_full_questionnaire,
    render_single_group,
    get_options_with_triggers,
    FormSchema,
)
from src.questionnaire.schema import (
    Question,
    QuestionGroup,
    QuestionType,
    Option,
    ValidationRule,
    get_group_by_id,
)
from src.questionnaire.branching import QuestionnaireState


class TestRenderQuestionProperty:
    """Tests for render_question_property function."""
    
    def test_text_question(self):
        """Test rendering text question."""
        question = Question(
            id="test",
            question_type=QuestionType.TEXT,
            label="Test Question",
        )
        
        prop = render_question_property(question)
        
        assert prop["type"] == "string"
        assert prop["title"] == "Test Question"
    
    def test_number_question(self):
        """Test rendering number question."""
        question = Question(
            id="count",
            question_type=QuestionType.NUMBER,
            label="Animal Count",
        )
        
        prop = render_question_property(question)
        
        assert prop["type"] == "number"
    
    def test_single_select_question(self):
        """Test rendering single select question."""
        question = Question(
            id="species",
            question_type=QuestionType.SINGLE_SELECT,
            label="Species",
            options=[
                Option(value="mouse", label="Mouse"),
                Option(value="rat", label="Rat"),
            ],
        )
        
        prop = render_question_property(question)
        
        assert prop["type"] == "string"
        assert prop["enum"] == ["mouse", "rat"]
        assert prop["enumNames"] == ["Mouse", "Rat"]
    
    def test_multi_select_question(self):
        """Test rendering multi-select question."""
        question = Question(
            id="procedures",
            question_type=QuestionType.MULTI_SELECT,
            label="Procedures",
            options=[
                Option(value="surgery", label="Surgery"),
                Option(value="injection", label="Injection"),
            ],
        )
        
        prop = render_question_property(question)
        
        assert prop["type"] == "array"
        assert "items" in prop
        assert prop["items"]["enum"] == ["surgery", "injection"]
    
    def test_yes_no_question(self):
        """Test rendering yes/no question."""
        question = Question(
            id="genetic",
            question_type=QuestionType.YES_NO,
            label="Is genetically modified?",
        )
        
        prop = render_question_property(question)
        
        assert prop["type"] == "boolean"
    
    def test_date_question(self):
        """Test rendering date question."""
        question = Question(
            id="start_date",
            question_type=QuestionType.DATE,
            label="Start Date",
        )
        
        prop = render_question_property(question)
        
        assert prop["format"] == "date"
    
    def test_validation_rules(self):
        """Test validation rules are included."""
        question = Question(
            id="title",
            question_type=QuestionType.TEXT,
            label="Title",
            validation=[
                ValidationRule(rule_type="min_length", value=10, message="Too short"),
                ValidationRule(rule_type="max_length", value=200, message="Too long"),
            ],
        )
        
        prop = render_question_property(question)
        
        assert prop["minLength"] == 10
        assert prop["maxLength"] == 200
    
    def test_help_text_as_description(self):
        """Test help text becomes description."""
        question = Question(
            id="test",
            question_type=QuestionType.TEXT,
            label="Test",
            help_text="This is helpful",
        )
        
        prop = render_question_property(question)
        
        assert prop["description"] == "This is helpful"


class TestRenderQuestionUiSchema:
    """Tests for render_question_ui_schema function."""
    
    def test_textarea_widget(self):
        """Test textarea gets correct widget."""
        question = Question(
            id="desc",
            question_type=QuestionType.TEXTAREA,
            label="Description",
        )
        
        ui = render_question_ui_schema(question)
        
        assert ui["ui:widget"] == "textarea"
    
    def test_select_widget(self):
        """Test single select gets select widget."""
        question = Question(
            id="choice",
            question_type=QuestionType.SINGLE_SELECT,
            label="Choice",
            options=[Option(value="a", label="A")],
        )
        
        ui = render_question_ui_schema(question)
        
        assert ui["ui:widget"] == "select"
    
    def test_placeholder(self):
        """Test placeholder is included."""
        question = Question(
            id="name",
            question_type=QuestionType.TEXT,
            label="Name",
            placeholder="Enter name here",
        )
        
        ui = render_question_ui_schema(question)
        
        assert ui["ui:placeholder"] == "Enter name here"
    
    def test_regulatory_reference(self):
        """Test regulatory reference is included."""
        question = Question(
            id="animals",
            question_type=QuestionType.NUMBER,
            label="Animals",
            regulatory_reference="PHS Policy IV.A",
        )
        
        ui = render_question_ui_schema(question)
        
        assert "PHS Policy" in ui.get("ui:description", "")


class TestRenderQuestionGroup:
    """Tests for render_question_group function."""
    
    def test_renders_basic_group(self):
        """Test rendering a basic question group."""
        group = QuestionGroup(
            id="test",
            title="Test Group",
            questions=[
                Question(
                    id="q1",
                    question_type=QuestionType.TEXT,
                    label="Question 1",
                    order=1,
                ),
                Question(
                    id="q2",
                    question_type=QuestionType.NUMBER,
                    label="Question 2",
                    order=2,
                ),
            ],
        )
        
        result = render_question_group(group)
        
        assert isinstance(result, FormSchema)
    
    def test_schema_has_properties(self):
        """Test schema has properties for questions."""
        group = QuestionGroup(
            id="test",
            title="Test",
            questions=[
                Question(
                    id="q1",
                    question_type=QuestionType.TEXT,
                    label="Q1",
                ),
            ],
        )
        
        result = render_question_group(group)
        schema = result.model_dump(by_alias=True)["schema"]
        
        assert "q1" in schema["properties"]
    
    def test_required_fields_tracked(self):
        """Test required fields are tracked."""
        group = QuestionGroup(
            id="test",
            title="Test",
            questions=[
                Question(
                    id="q1",
                    question_type=QuestionType.TEXT,
                    label="Required",
                    required=True,
                ),
                Question(
                    id="q2",
                    question_type=QuestionType.TEXT,
                    label="Optional",
                    required=False,
                ),
            ],
        )
        
        result = render_question_group(group)
        schema = result.model_dump(by_alias=True)["schema"]
        
        assert "q1" in schema["required"]
        assert "q2" not in schema["required"]
    
    def test_conditional_questions_hidden(self):
        """Test conditional questions are hidden when condition not met."""
        group = QuestionGroup(
            id="test",
            title="Test",
            questions=[
                Question(
                    id="show_details",
                    question_type=QuestionType.YES_NO,
                    label="Show details?",
                ),
                Question(
                    id="details",
                    question_type=QuestionType.TEXT,
                    label="Details",
                    depends_on="show_details",
                    show_when={"show_details": True},
                ),
            ],
        )
        
        # Without the condition met
        result = render_question_group(group, {"show_details": False})
        schema = result.model_dump(by_alias=True)["schema"]
        
        assert "details" not in schema["properties"]
    
    def test_conditional_questions_shown(self):
        """Test conditional questions shown when condition met."""
        group = QuestionGroup(
            id="test",
            title="Test",
            questions=[
                Question(
                    id="show_details",
                    question_type=QuestionType.YES_NO,
                    label="Show details?",
                ),
                Question(
                    id="details",
                    question_type=QuestionType.TEXT,
                    label="Details",
                    depends_on="show_details",
                    show_when={"show_details": True},
                ),
            ],
        )
        
        # With condition met
        result = render_question_group(group, {"show_details": True})
        schema = result.model_dump(by_alias=True)["schema"]
        
        assert "details" in schema["properties"]


class TestRenderFullQuestionnaire:
    """Tests for render_full_questionnaire function."""
    
    def test_returns_groups(self):
        """Test returns groups array."""
        result = render_full_questionnaire()
        
        assert "groups" in result
        assert isinstance(result["groups"], list)
    
    def test_includes_base_groups(self):
        """Test includes base groups."""
        result = render_full_questionnaire()
        
        group_ids = [g["id"] for g in result["groups"]]
        
        assert "basic_info" in group_ids
        assert "species" in group_ids
        assert "procedures" in group_ids
    
    def test_includes_active_branches(self):
        """Test includes active branches when triggered."""
        state = QuestionnaireState(
            answers={
                "procedure_types": ["survival_surgery"],
            }
        )
        
        result = render_full_questionnaire(state)
        
        assert "surgery_branch" in result["activeBranches"]
    
    def test_branch_groups_marked(self):
        """Test branch groups are marked as branches."""
        state = QuestionnaireState(
            answers={
                "pain_category": "E",
            }
        )
        
        result = render_full_questionnaire(state)
        
        branch_groups = [g for g in result["groups"] if g.get("isBranch")]
        assert len(branch_groups) > 0


class TestRenderSingleGroup:
    """Tests for render_single_group function."""
    
    def test_renders_existing_group(self):
        """Test renders existing group."""
        result = render_single_group("basic_info")
        
        assert result is not None
        assert result["id"] == "basic_info"
    
    def test_returns_none_for_missing(self):
        """Test returns None for missing group."""
        result = render_single_group("nonexistent")
        
        assert result is None
    
    def test_includes_form_schema(self):
        """Test includes form schema."""
        result = render_single_group("basic_info")
        
        assert "formSchema" in result
        assert "schema" in result["formSchema"]


class TestGetOptionsWithTriggers:
    """Tests for get_options_with_triggers function."""
    
    def test_returns_options(self):
        """Test returns options list."""
        options = get_options_with_triggers("species")
        
        assert len(options) > 0
    
    def test_includes_trigger_info(self):
        """Test includes trigger information."""
        options = get_options_with_triggers("species")
        
        # At least some options should have triggers
        options_with_triggers = [o for o in options if o.get("triggersBranch")]
        assert len(options_with_triggers) > 0
    
    def test_returns_empty_for_invalid(self):
        """Test returns empty for invalid question."""
        options = get_options_with_triggers("nonexistent")
        
        assert options == []


class TestFormSchema:
    """Tests for FormSchema model."""
    
    def test_create_form_schema(self):
        """Test creating FormSchema."""
        schema = FormSchema(
            schema={"type": "object", "properties": {}},
            uiSchema={},
            formData={},
        )
        
        assert schema is not None
    
    def test_serialization(self):
        """Test FormSchema serialization."""
        schema = FormSchema(
            schema={"type": "object"},
            uiSchema={"ui:order": ["a", "b"]},
            formData={"a": "value"},
        )
        
        data = schema.model_dump(by_alias=True)
        
        assert "schema" in data
        assert "uiSchema" in data
        assert "formData" in data


class TestRealQuestionGroups:
    """Tests with real question groups."""
    
    def test_basic_info_renders(self):
        """Test basic info group renders correctly."""
        result = render_single_group("basic_info")
        
        assert result is not None
        schema = result["formSchema"]["schema"]
        
        assert "protocol_title" in schema["properties"]
        assert "pi_name" in schema["properties"]
    
    def test_species_renders(self):
        """Test species group renders correctly."""
        result = render_single_group("species")
        
        assert result is not None
        schema = result["formSchema"]["schema"]
        
        assert "species" in schema["properties"]
        assert "total_animals" in schema["properties"]
    
    def test_procedures_renders(self):
        """Test procedures group renders correctly."""
        result = render_single_group("procedures")
        
        assert result is not None
        schema = result["formSchema"]["schema"]
        
        assert "procedure_types" in schema["properties"]
        assert "pain_category" in schema["properties"]
        assert "euthanasia_method" in schema["properties"]
