"""
Questionnaire Branching Logic.

Implements adaptive questionnaire flow based on user responses.
"""

from typing import Optional, Any

from pydantic import BaseModel, Field

from src.questionnaire.schema import (
    Question,
    QuestionGroup,
    Option,
    ALL_QUESTION_GROUPS,
    get_question_by_id,
    get_group_by_id,
)


class BranchCondition(BaseModel):
    """Condition that triggers a branch."""
    
    question_id: str = Field(description="Question ID to check")
    operator: str = Field(description="Comparison operator: eq, ne, in, not_in, contains")
    value: Any = Field(description="Value to compare against")


class Branch(BaseModel):
    """A questionnaire branch."""
    
    id: str = Field(description="Unique branch identifier")
    name: str = Field(description="Branch name")
    conditions: list[BranchCondition] = Field(description="Conditions to activate branch")
    question_group_id: str = Field(description="Question group to show")
    priority: int = Field(default=0, description="Priority for ordering (higher = first)")


class QuestionnaireState(BaseModel):
    """Current state of the questionnaire."""
    
    answers: dict[str, Any] = Field(default_factory=dict)
    active_branches: list[str] = Field(default_factory=list)
    completed_groups: list[str] = Field(default_factory=list)
    current_group_id: Optional[str] = Field(default=None)
    is_complete: bool = Field(default=False)


# ============================================================================
# BRANCH DEFINITIONS
# ============================================================================

BRANCHES = [
    # Mouse/Rat specific (USDA exempt)
    Branch(
        id="mouse_branch",
        name="Mouse-Specific Questions",
        conditions=[
            BranchCondition(
                question_id="species",
                operator="eq",
                value="mouse",
            ),
        ],
        question_group_id="mouse_branch",
        priority=10,
    ),
    Branch(
        id="rat_branch",
        name="Rat-Specific Questions",
        conditions=[
            BranchCondition(
                question_id="species",
                operator="eq",
                value="rat",
            ),
        ],
        question_group_id="rat_branch",
        priority=10,
    ),
    
    # USDA covered species
    Branch(
        id="usda_covered_branch",
        name="USDA Covered Species",
        conditions=[
            BranchCondition(
                question_id="species",
                operator="in",
                value=["rabbit", "guinea_pig", "hamster", "dog", "cat", "pig", "sheep"],
            ),
        ],
        question_group_id="usda_covered_branch",
        priority=20,
    ),
    
    # Primate specific
    Branch(
        id="primate_branch",
        name="Non-Human Primate Requirements",
        conditions=[
            BranchCondition(
                question_id="species",
                operator="eq",
                value="primate",
            ),
        ],
        question_group_id="primate_branch",
        priority=30,
    ),
    
    # Fish specific
    Branch(
        id="fish_branch",
        name="Fish/Aquatic Species",
        conditions=[
            BranchCondition(
                question_id="species",
                operator="in",
                value=["zebrafish", "other_fish"],
            ),
        ],
        question_group_id="fish_branch",
        priority=10,
    ),
    
    # Wildlife
    Branch(
        id="wildlife_branch",
        name="Wildlife/Field Studies",
        conditions=[
            BranchCondition(
                question_id="animal_source",
                operator="eq",
                value="wild_caught",
            ),
        ],
        question_group_id="wildlife_branch",
        priority=25,
    ),
    
    # Survival surgery
    Branch(
        id="surgery_branch",
        name="Surgical Procedures",
        conditions=[
            BranchCondition(
                question_id="procedure_types",
                operator="contains",
                value="survival_surgery",
            ),
        ],
        question_group_id="surgery_branch",
        priority=50,
    ),
    
    # Terminal surgery
    Branch(
        id="terminal_surgery_branch",
        name="Terminal Surgery",
        conditions=[
            BranchCondition(
                question_id="procedure_types",
                operator="contains",
                value="non_survival_surgery",
            ),
        ],
        question_group_id="terminal_surgery_branch",
        priority=45,
    ),
    
    # Injection procedures
    Branch(
        id="injection_branch",
        name="Injection Procedures",
        conditions=[
            BranchCondition(
                question_id="procedure_types",
                operator="contains",
                value="injections",
            ),
        ],
        question_group_id="injection_branch",
        priority=40,
    ),
    
    # Blood collection
    Branch(
        id="blood_branch",
        name="Blood Collection",
        conditions=[
            BranchCondition(
                question_id="procedure_types",
                operator="contains",
                value="blood_collection",
            ),
        ],
        question_group_id="blood_branch",
        priority=40,
    ),
    
    # Behavioral testing
    Branch(
        id="behavior_branch",
        name="Behavioral Testing",
        conditions=[
            BranchCondition(
                question_id="procedure_types",
                operator="contains",
                value="behavioral_testing",
            ),
        ],
        question_group_id="behavior_branch",
        priority=35,
    ),
    
    # Imaging
    Branch(
        id="imaging_branch",
        name="In Vivo Imaging",
        conditions=[
            BranchCondition(
                question_id="procedure_types",
                operator="contains",
                value="imaging",
            ),
        ],
        question_group_id="imaging_branch",
        priority=35,
    ),
    
    # Tumor studies
    Branch(
        id="tumor_branch",
        name="Tumor/Cancer Studies",
        conditions=[
            BranchCondition(
                question_id="procedure_types",
                operator="contains",
                value="tumor_implantation",
            ),
        ],
        question_group_id="tumor_branch",
        priority=50,
    ),
    
    # Food/water restriction
    Branch(
        id="restriction_branch",
        name="Food/Water Restriction",
        conditions=[
            BranchCondition(
                question_id="procedure_types",
                operator="contains",
                value="food_water_restriction",
            ),
        ],
        question_group_id="restriction_branch",
        priority=45,
    ),
    
    # Breeding
    Branch(
        id="breeding_branch",
        name="Breeding Colony",
        conditions=[
            BranchCondition(
                question_id="procedure_types",
                operator="contains",
                value="breeding",
            ),
        ],
        question_group_id="breeding_branch",
        priority=30,
    ),
    
    # Pain Category D - need pain management details
    Branch(
        id="pain_management_branch",
        name="Pain Management Details",
        conditions=[
            BranchCondition(
                question_id="pain_category",
                operator="eq",
                value="D",
            ),
        ],
        question_group_id="pain_management_branch",
        priority=60,
    ),
    
    # Pain Category E - requires special justification
    Branch(
        id="category_e_branch",
        name="Category E Justification",
        conditions=[
            BranchCondition(
                question_id="pain_category",
                operator="eq",
                value="E",
            ),
        ],
        question_group_id="category_e_branch",
        priority=70,
    ),
]


def evaluate_condition(
    condition: BranchCondition,
    answers: dict[str, Any],
) -> bool:
    """
    Evaluate a single branch condition.
    
    Args:
        condition: The condition to evaluate
        answers: Current questionnaire answers
        
    Returns:
        True if condition is met.
    """
    if condition.question_id not in answers:
        return False
    
    answer = answers[condition.question_id]
    
    if condition.operator == "eq":
        return answer == condition.value
    
    elif condition.operator == "ne":
        return answer != condition.value
    
    elif condition.operator == "in":
        if isinstance(condition.value, list):
            return answer in condition.value
        return False
    
    elif condition.operator == "not_in":
        if isinstance(condition.value, list):
            return answer not in condition.value
        return True
    
    elif condition.operator == "contains":
        # For multi-select answers (lists)
        if isinstance(answer, list):
            return condition.value in answer
        return False
    
    elif condition.operator == "gt":
        return answer > condition.value
    
    elif condition.operator == "lt":
        return answer < condition.value
    
    elif condition.operator == "gte":
        return answer >= condition.value
    
    elif condition.operator == "lte":
        return answer <= condition.value
    
    return False


def evaluate_branch(
    branch: Branch,
    answers: dict[str, Any],
) -> bool:
    """
    Evaluate if a branch should be activated.
    
    All conditions must be met (AND logic).
    
    Args:
        branch: The branch to evaluate
        answers: Current questionnaire answers
        
    Returns:
        True if branch should be active.
    """
    if not branch.conditions:
        return False
    
    return all(
        evaluate_condition(condition, answers)
        for condition in branch.conditions
    )


def get_active_branches(answers: dict[str, Any]) -> list[Branch]:
    """
    Get all branches that should be active based on answers.
    
    Args:
        answers: Current questionnaire answers
        
    Returns:
        List of active branches, sorted by priority.
    """
    active = [
        branch for branch in BRANCHES
        if evaluate_branch(branch, answers)
    ]
    
    # Sort by priority (higher first)
    active.sort(key=lambda b: b.priority, reverse=True)
    
    return active


def get_next_questions(
    state: QuestionnaireState,
) -> list[QuestionGroup]:
    """
    Get the next set of questions based on current state.
    
    Args:
        state: Current questionnaire state
        
    Returns:
        List of question groups to show next.
    """
    # Start with base groups
    base_groups = ["basic_info", "species", "procedures"]
    
    # Get active branches
    active_branches = get_active_branches(state.answers)
    active_branch_ids = [b.id for b in active_branches]
    
    # Update state
    state.active_branches = active_branch_ids
    
    # Collect all groups to show
    groups_to_show = []
    
    # Add base groups first
    for group_id in base_groups:
        if group_id not in state.completed_groups:
            group = get_group_by_id(group_id)
            if group:
                groups_to_show.append(group)
    
    # Add branch-specific groups
    for branch in active_branches:
        if branch.question_group_id not in state.completed_groups:
            group = get_group_by_id(branch.question_group_id)
            if group:
                groups_to_show.append(group)
    
    return groups_to_show


def should_show_question(
    question: Question,
    answers: dict[str, Any],
) -> bool:
    """
    Determine if a question should be shown based on conditions.
    
    Args:
        question: The question to check
        answers: Current answers
        
    Returns:
        True if question should be shown.
    """
    # If no conditional, always show
    if not question.depends_on or not question.show_when:
        return True
    
    # Check condition
    dependent_answer = answers.get(question.depends_on)
    
    if dependent_answer is None:
        return False
    
    expected_value = question.show_when.get(question.depends_on)
    
    return dependent_answer == expected_value


def filter_visible_questions(
    group: QuestionGroup,
    answers: dict[str, Any],
) -> list[Question]:
    """
    Filter questions in a group to only those that should be visible.
    
    Args:
        group: Question group
        answers: Current answers
        
    Returns:
        List of visible questions.
    """
    return [
        q for q in group.questions
        if should_show_question(q, answers)
    ]


def get_triggered_branches_from_option(option: Option) -> Optional[str]:
    """
    Get branch ID triggered by selecting an option.
    
    Args:
        option: The selected option
        
    Returns:
        Branch ID if option triggers a branch, None otherwise.
    """
    return option.triggers_branch


def calculate_progress(state: QuestionnaireState) -> float:
    """
    Calculate questionnaire completion progress.
    
    Args:
        state: Current state
        
    Returns:
        Progress from 0 to 1.
    """
    # Count total required questions
    total_required = 0
    answered_required = 0
    
    # Base groups
    base_groups = [get_group_by_id(gid) for gid in ["basic_info", "species", "procedures"]]
    
    for group in base_groups:
        if group:
            for q in group.questions:
                if q.required and should_show_question(q, state.answers):
                    total_required += 1
                    if q.id in state.answers:
                        answered_required += 1
    
    # Active branch groups
    for branch in get_active_branches(state.answers):
        group = get_group_by_id(branch.question_group_id)
        if group:
            for q in group.questions:
                if q.required and should_show_question(q, state.answers):
                    total_required += 1
                    if q.id in state.answers:
                        answered_required += 1
    
    if total_required == 0:
        return 0.0
    
    return answered_required / total_required


def validate_questionnaire(state: QuestionnaireState) -> list[str]:
    """
    Validate the questionnaire for missing required answers.
    
    Args:
        state: Current state
        
    Returns:
        List of validation error messages.
    """
    errors = []
    
    # Check base groups
    base_groups = [get_group_by_id(gid) for gid in ["basic_info", "species", "procedures"]]
    
    for group in base_groups:
        if group:
            for q in group.questions:
                if q.required and should_show_question(q, state.answers):
                    if q.id not in state.answers or not state.answers[q.id]:
                        errors.append(f"Required: {q.label}")
    
    # Check active branch groups
    for branch in get_active_branches(state.answers):
        group = get_group_by_id(branch.question_group_id)
        if group:
            for q in group.questions:
                if q.required and should_show_question(q, state.answers):
                    if q.id not in state.answers or not state.answers[q.id]:
                        errors.append(f"Required ({branch.name}): {q.label}")
    
    return errors


# Export
__all__ = [
    "BranchCondition",
    "Branch",
    "QuestionnaireState",
    "BRANCHES",
    "evaluate_condition",
    "evaluate_branch",
    "get_active_branches",
    "get_next_questions",
    "should_show_question",
    "filter_visible_questions",
    "calculate_progress",
    "validate_questionnaire",
]
