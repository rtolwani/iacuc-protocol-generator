"""
JSON Schema Renderer for Questionnaire.

Generates JSON Schema format for dynamic form rendering in frontend.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from src.questionnaire.schema import (
    QuestionType,
    Question,
    QuestionGroup,
    Option,
    ValidationRule,
    ALL_QUESTION_GROUPS,
    get_group_by_id,
)
from src.questionnaire.branching import (
    QuestionnaireState,
    get_active_branches,
    should_show_question,
)


class JsonSchemaProperty(BaseModel):
    """A property in JSON Schema format."""
    
    type: str = Field(description="JSON Schema type")
    title: str = Field(description="Display title")
    description: Optional[str] = Field(default=None)
    default: Optional[Any] = Field(default=None)
    enum: Optional[list[Any]] = Field(default=None)
    enumNames: Optional[list[str]] = Field(default=None)
    minLength: Optional[int] = Field(default=None)
    maxLength: Optional[int] = Field(default=None)
    minimum: Optional[float] = Field(default=None)
    maximum: Optional[float] = Field(default=None)
    pattern: Optional[str] = Field(default=None)
    format: Optional[str] = Field(default=None)
    items: Optional[dict] = Field(default=None)
    uniqueItems: Optional[bool] = Field(default=None)


class UiSchemaField(BaseModel):
    """UI Schema for a field (react-jsonschema-form compatible)."""
    
    ui_widget: Optional[str] = Field(default=None, alias="ui:widget")
    ui_options: Optional[dict] = Field(default=None, alias="ui:options")
    ui_help: Optional[str] = Field(default=None, alias="ui:help")
    ui_placeholder: Optional[str] = Field(default=None, alias="ui:placeholder")
    
    class Config:
        populate_by_name = True


class FormSchema(BaseModel):
    """Complete form schema for a question group."""
    
    schema_: dict = Field(alias="schema")
    uiSchema: dict = Field(default_factory=dict)
    formData: dict = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True


def question_type_to_json_type(qtype: QuestionType) -> str:
    """
    Convert question type to JSON Schema type.
    
    Args:
        qtype: Question type
        
    Returns:
        JSON Schema type string.
    """
    type_mapping = {
        QuestionType.TEXT: "string",
        QuestionType.TEXTAREA: "string",
        QuestionType.NUMBER: "number",
        QuestionType.SINGLE_SELECT: "string",
        QuestionType.MULTI_SELECT: "array",
        QuestionType.DATE: "string",
        QuestionType.YES_NO: "boolean",
        QuestionType.FILE: "string",
    }
    return type_mapping.get(qtype, "string")


def question_type_to_ui_widget(qtype: QuestionType) -> Optional[str]:
    """
    Get UI widget for question type.
    
    Args:
        qtype: Question type
        
    Returns:
        UI widget name or None.
    """
    widget_mapping = {
        QuestionType.TEXTAREA: "textarea",
        QuestionType.SINGLE_SELECT: "select",
        QuestionType.MULTI_SELECT: "checkboxes",
        QuestionType.DATE: "date",
        QuestionType.YES_NO: "radio",
        QuestionType.FILE: "file",
    }
    return widget_mapping.get(qtype)


def validation_to_json_schema(
    validation_rules: list[ValidationRule],
) -> dict:
    """
    Convert validation rules to JSON Schema constraints.
    
    Args:
        validation_rules: List of validation rules
        
    Returns:
        Dictionary of JSON Schema constraints.
    """
    constraints = {}
    
    for rule in validation_rules:
        if rule.rule_type == "min_length":
            constraints["minLength"] = rule.value
        elif rule.rule_type == "max_length":
            constraints["maxLength"] = rule.value
        elif rule.rule_type == "min":
            constraints["minimum"] = rule.value
        elif rule.rule_type == "max":
            constraints["maximum"] = rule.value
        elif rule.rule_type == "pattern":
            constraints["pattern"] = rule.value
    
    return constraints


def render_question_property(question: Question) -> dict:
    """
    Render a question as a JSON Schema property.
    
    Args:
        question: The question to render
        
    Returns:
        JSON Schema property definition.
    """
    prop = {
        "type": question_type_to_json_type(question.question_type),
        "title": question.label,
    }
    
    # Add description/help text
    if question.help_text:
        prop["description"] = question.help_text
    
    # Add default value
    if question.default_value is not None:
        prop["default"] = question.default_value
    
    # Handle select types
    if question.question_type == QuestionType.SINGLE_SELECT:
        if question.options:
            prop["enum"] = [opt.value for opt in question.options]
            prop["enumNames"] = [opt.label for opt in question.options]
    
    elif question.question_type == QuestionType.MULTI_SELECT:
        if question.options:
            prop["items"] = {
                "type": "string",
                "enum": [opt.value for opt in question.options],
                "enumNames": [opt.label for opt in question.options],
            }
            prop["uniqueItems"] = True
    
    elif question.question_type == QuestionType.YES_NO:
        prop["type"] = "boolean"
        prop["enumNames"] = ["No", "Yes"]
    
    elif question.question_type == QuestionType.DATE:
        prop["format"] = "date"
    
    # Add validation constraints
    constraints = validation_to_json_schema(question.validation)
    prop.update(constraints)
    
    return prop


def render_question_ui_schema(question: Question) -> dict:
    """
    Render UI schema for a question.
    
    Args:
        question: The question to render
        
    Returns:
        UI schema definition.
    """
    ui = {}
    
    # Set widget
    widget = question_type_to_ui_widget(question.question_type)
    if widget:
        ui["ui:widget"] = widget
    
    # Add placeholder
    if question.placeholder:
        ui["ui:placeholder"] = question.placeholder
    
    # Add help text
    if question.help_text:
        ui["ui:help"] = question.help_text
    
    # Add options for specific widgets
    if question.question_type == QuestionType.TEXTAREA:
        ui["ui:options"] = {"rows": 5}
    
    # Add regulatory reference as additional help
    if question.regulatory_reference:
        ui["ui:description"] = f"Regulatory Reference: {question.regulatory_reference}"
    
    return ui


def render_question_group(
    group: QuestionGroup,
    answers: Optional[dict] = None,
) -> FormSchema:
    """
    Render a question group as a complete form schema.
    
    Args:
        group: The question group to render
        answers: Current answers (for conditional questions)
        
    Returns:
        FormSchema with schema, uiSchema, and formData.
    """
    answers = answers or {}
    
    # Build JSON Schema
    properties = {}
    required = []
    ui_schema = {}
    form_data = {}
    
    # Sort questions by order
    sorted_questions = sorted(group.questions, key=lambda q: q.order)
    
    for question in sorted_questions:
        # Check if question should be shown
        if not should_show_question(question, answers):
            continue
        
        # Add to properties
        properties[question.id] = render_question_property(question)
        
        # Track required fields
        if question.required:
            required.append(question.id)
        
        # Add UI schema
        ui = render_question_ui_schema(question)
        if ui:
            ui_schema[question.id] = ui
        
        # Add current answer to form data
        if question.id in answers:
            form_data[question.id] = answers[question.id]
    
    # Build complete schema
    schema = {
        "type": "object",
        "title": group.title,
        "properties": properties,
        "required": required,
    }
    
    if group.description:
        schema["description"] = group.description
    
    # Set field order
    ui_schema["ui:order"] = [q.id for q in sorted_questions if should_show_question(q, answers)]
    
    return FormSchema(
        schema=schema,
        uiSchema=ui_schema,
        formData=form_data,
    )


def render_full_questionnaire(
    state: Optional[QuestionnaireState] = None,
) -> dict:
    """
    Render the full questionnaire based on current state.
    
    Args:
        state: Current questionnaire state
        
    Returns:
        Dictionary with all form schemas.
    """
    state = state or QuestionnaireState()
    
    result = {
        "groups": [],
        "activeBranches": [],
        "progress": 0.0,
    }
    
    # Base groups
    base_group_ids = ["basic_info", "species", "procedures"]
    
    for group_id in base_group_ids:
        group = get_group_by_id(group_id)
        if group:
            form_schema = render_question_group(group, state.answers)
            result["groups"].append({
                "id": group.id,
                "title": group.title,
                "order": group.order,
                "isBranch": False,
                "formSchema": form_schema.model_dump(by_alias=True),
            })
    
    # Active branch groups
    active_branches = get_active_branches(state.answers)
    result["activeBranches"] = [b.id for b in active_branches]
    
    for branch in active_branches:
        group = get_group_by_id(branch.question_group_id)
        if group:
            form_schema = render_question_group(group, state.answers)
            result["groups"].append({
                "id": group.id,
                "title": group.title,
                "order": group.order,
                "isBranch": True,
                "branchId": branch.id,
                "branchName": branch.name,
                "formSchema": form_schema.model_dump(by_alias=True),
            })
    
    # Sort groups by order
    result["groups"].sort(key=lambda g: g["order"])
    
    return result


def render_single_group(
    group_id: str,
    answers: Optional[dict] = None,
) -> Optional[dict]:
    """
    Render a single question group by ID.
    
    Args:
        group_id: Group ID to render
        answers: Current answers
        
    Returns:
        Form schema for the group or None if not found.
    """
    group = get_group_by_id(group_id)
    if not group:
        return None
    
    form_schema = render_question_group(group, answers or {})
    
    return {
        "id": group.id,
        "title": group.title,
        "description": group.description,
        "formSchema": form_schema.model_dump(by_alias=True),
    }


def get_options_with_triggers(question_id: str) -> list[dict]:
    """
    Get options for a question with their branch triggers.
    
    Args:
        question_id: Question ID
        
    Returns:
        List of options with trigger information.
    """
    from src.questionnaire.schema import get_question_by_id
    
    question = get_question_by_id(question_id)
    if not question or not question.options:
        return []
    
    return [
        {
            "value": opt.value,
            "label": opt.label,
            "helpText": opt.help_text,
            "triggersBranch": opt.triggers_branch,
        }
        for opt in question.options
    ]


# Export
__all__ = [
    "render_question_property",
    "render_question_ui_schema",
    "render_question_group",
    "render_full_questionnaire",
    "render_single_group",
    "get_options_with_triggers",
    "FormSchema",
    "JsonSchemaProperty",
    "UiSchemaField",
]
