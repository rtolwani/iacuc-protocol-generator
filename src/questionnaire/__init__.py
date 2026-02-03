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
]
