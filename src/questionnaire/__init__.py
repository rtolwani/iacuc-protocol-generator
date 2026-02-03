"""
Questionnaire system for IACUC protocol generation.

This module provides an adaptive questionnaire that collects
information needed for protocol generation.
"""

from src.questionnaire.schema import (
    QuestionType,
    Question,
    QuestionGroup,
    BASIC_INFO_QUESTIONS,
    SPECIES_QUESTIONS,
    PROCEDURE_QUESTIONS,
)
from src.questionnaire.branching import (
    Branch,
    BranchCondition,
    QuestionnaireState,
    get_active_branches,
    evaluate_branch,
    calculate_progress,
    validate_questionnaire,
)
from src.questionnaire.renderer import (
    render_question_group,
    render_full_questionnaire,
    render_single_group,
    FormSchema,
)

__all__ = [
    "QuestionType",
    "Question",
    "QuestionGroup",
    "BASIC_INFO_QUESTIONS",
    "SPECIES_QUESTIONS",
    "PROCEDURE_QUESTIONS",
    "Branch",
    "BranchCondition",
    "QuestionnaireState",
    "get_active_branches",
    "evaluate_branch",
    "calculate_progress",
    "validate_questionnaire",
    "render_question_group",
    "render_full_questionnaire",
    "render_single_group",
    "FormSchema",
]
