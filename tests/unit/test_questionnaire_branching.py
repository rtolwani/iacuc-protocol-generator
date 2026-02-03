"""
Unit tests for Questionnaire Branching Logic.
"""

import pytest

from src.questionnaire.branching import (
    BranchCondition,
    Branch,
    QuestionnaireState,
    BRANCHES,
    evaluate_condition,
    evaluate_branch,
    get_active_branches,
    get_next_questions,
    should_show_question,
    filter_visible_questions,
    calculate_progress,
    validate_questionnaire,
)
from src.questionnaire.schema import (
    Question,
    QuestionGroup,
    QuestionType,
    get_question_by_id,
    get_group_by_id,
)


class TestBranchCondition:
    """Tests for BranchCondition model."""
    
    def test_create_eq_condition(self):
        """Test creating equality condition."""
        condition = BranchCondition(
            question_id="species",
            operator="eq",
            value="mouse",
        )
        
        assert condition.operator == "eq"
    
    def test_create_in_condition(self):
        """Test creating 'in' condition."""
        condition = BranchCondition(
            question_id="species",
            operator="in",
            value=["rabbit", "dog", "cat"],
        )
        
        assert condition.operator == "in"
        assert len(condition.value) == 3


class TestEvaluateCondition:
    """Tests for evaluate_condition function."""
    
    def test_eq_true(self):
        """Test equality returns true when match."""
        condition = BranchCondition(
            question_id="species",
            operator="eq",
            value="mouse",
        )
        
        result = evaluate_condition(condition, {"species": "mouse"})
        
        assert result == True
    
    def test_eq_false(self):
        """Test equality returns false when no match."""
        condition = BranchCondition(
            question_id="species",
            operator="eq",
            value="mouse",
        )
        
        result = evaluate_condition(condition, {"species": "rat"})
        
        assert result == False
    
    def test_ne_true(self):
        """Test not-equal returns true when different."""
        condition = BranchCondition(
            question_id="species",
            operator="ne",
            value="mouse",
        )
        
        result = evaluate_condition(condition, {"species": "rat"})
        
        assert result == True
    
    def test_in_true(self):
        """Test 'in' returns true when value in list."""
        condition = BranchCondition(
            question_id="species",
            operator="in",
            value=["rabbit", "dog", "cat"],
        )
        
        result = evaluate_condition(condition, {"species": "dog"})
        
        assert result == True
    
    def test_in_false(self):
        """Test 'in' returns false when value not in list."""
        condition = BranchCondition(
            question_id="species",
            operator="in",
            value=["rabbit", "dog", "cat"],
        )
        
        result = evaluate_condition(condition, {"species": "mouse"})
        
        assert result == False
    
    def test_contains_true(self):
        """Test 'contains' for multi-select answers."""
        condition = BranchCondition(
            question_id="procedure_types",
            operator="contains",
            value="survival_surgery",
        )
        
        result = evaluate_condition(
            condition,
            {"procedure_types": ["injections", "survival_surgery", "behavioral_testing"]},
        )
        
        assert result == True
    
    def test_contains_false(self):
        """Test 'contains' returns false when not in list."""
        condition = BranchCondition(
            question_id="procedure_types",
            operator="contains",
            value="survival_surgery",
        )
        
        result = evaluate_condition(
            condition,
            {"procedure_types": ["injections", "behavioral_testing"]},
        )
        
        assert result == False
    
    def test_missing_answer(self):
        """Test returns false when answer missing."""
        condition = BranchCondition(
            question_id="species",
            operator="eq",
            value="mouse",
        )
        
        result = evaluate_condition(condition, {})
        
        assert result == False


class TestEvaluateBranch:
    """Tests for evaluate_branch function."""
    
    def test_single_condition_true(self):
        """Test branch with single true condition."""
        branch = Branch(
            id="test",
            name="Test",
            conditions=[
                BranchCondition(
                    question_id="species",
                    operator="eq",
                    value="mouse",
                ),
            ],
            question_group_id="test_group",
        )
        
        result = evaluate_branch(branch, {"species": "mouse"})
        
        assert result == True
    
    def test_multiple_conditions_all_true(self):
        """Test branch with multiple true conditions."""
        branch = Branch(
            id="test",
            name="Test",
            conditions=[
                BranchCondition(
                    question_id="species",
                    operator="eq",
                    value="mouse",
                ),
                BranchCondition(
                    question_id="pain_category",
                    operator="eq",
                    value="D",
                ),
            ],
            question_group_id="test_group",
        )
        
        result = evaluate_branch(
            branch,
            {"species": "mouse", "pain_category": "D"},
        )
        
        assert result == True
    
    def test_multiple_conditions_one_false(self):
        """Test branch fails if any condition false."""
        branch = Branch(
            id="test",
            name="Test",
            conditions=[
                BranchCondition(
                    question_id="species",
                    operator="eq",
                    value="mouse",
                ),
                BranchCondition(
                    question_id="pain_category",
                    operator="eq",
                    value="D",
                ),
            ],
            question_group_id="test_group",
        )
        
        result = evaluate_branch(
            branch,
            {"species": "mouse", "pain_category": "C"},
        )
        
        assert result == False


class TestGetActiveBranches:
    """Tests for get_active_branches function."""
    
    def test_surgery_branch_activates(self):
        """Test that selecting survival surgery activates surgery branch."""
        answers = {
            "procedure_types": ["survival_surgery", "behavioral_testing"],
        }
        
        branches = get_active_branches(answers)
        branch_ids = [b.id for b in branches]
        
        assert "surgery_branch" in branch_ids
    
    def test_category_e_branch_activates(self):
        """Test that Category E activates justification branch."""
        answers = {
            "pain_category": "E",
        }
        
        branches = get_active_branches(answers)
        branch_ids = [b.id for b in branches]
        
        assert "category_e_branch" in branch_ids
    
    def test_usda_covered_branch(self):
        """Test that rabbit triggers USDA covered branch."""
        answers = {
            "species": "rabbit",
        }
        
        branches = get_active_branches(answers)
        branch_ids = [b.id for b in branches]
        
        assert "usda_covered_branch" in branch_ids
    
    def test_mouse_no_usda_branch(self):
        """Test that mouse does NOT trigger USDA covered branch."""
        answers = {
            "species": "mouse",
        }
        
        branches = get_active_branches(answers)
        branch_ids = [b.id for b in branches]
        
        assert "usda_covered_branch" not in branch_ids
    
    def test_tumor_branch_activates(self):
        """Test that tumor implantation activates tumor branch."""
        answers = {
            "procedure_types": ["tumor_implantation"],
        }
        
        branches = get_active_branches(answers)
        branch_ids = [b.id for b in branches]
        
        assert "tumor_branch" in branch_ids
    
    def test_branches_sorted_by_priority(self):
        """Test that branches are sorted by priority."""
        answers = {
            "procedure_types": ["survival_surgery", "tumor_implantation"],
            "pain_category": "E",
        }
        
        branches = get_active_branches(answers)
        
        # Should be sorted by priority (highest first)
        priorities = [b.priority for b in branches]
        assert priorities == sorted(priorities, reverse=True)


class TestShouldShowQuestion:
    """Tests for should_show_question function."""
    
    def test_no_condition_shows(self):
        """Test question without condition always shows."""
        question = Question(
            id="test",
            question_type=QuestionType.TEXT,
            label="Test",
        )
        
        result = should_show_question(question, {})
        
        assert result == True
    
    def test_condition_met_shows(self):
        """Test question shows when condition met."""
        question = Question(
            id="details",
            question_type=QuestionType.TEXTAREA,
            label="Details",
            depends_on="has_details",
            show_when={"has_details": True},
        )
        
        result = should_show_question(question, {"has_details": True})
        
        assert result == True
    
    def test_condition_not_met_hides(self):
        """Test question hides when condition not met."""
        question = Question(
            id="details",
            question_type=QuestionType.TEXTAREA,
            label="Details",
            depends_on="has_details",
            show_when={"has_details": True},
        )
        
        result = should_show_question(question, {"has_details": False})
        
        assert result == False
    
    def test_missing_dependent_hides(self):
        """Test question hides when dependent answer missing."""
        question = Question(
            id="details",
            question_type=QuestionType.TEXTAREA,
            label="Details",
            depends_on="has_details",
            show_when={"has_details": True},
        )
        
        result = should_show_question(question, {})
        
        assert result == False


class TestQuestionnaireState:
    """Tests for QuestionnaireState model."""
    
    def test_create_empty_state(self):
        """Test creating empty state."""
        state = QuestionnaireState()
        
        assert state.answers == {}
        assert state.active_branches == []
        assert state.is_complete == False
    
    def test_state_with_answers(self):
        """Test state with answers."""
        state = QuestionnaireState(
            answers={"species": "mouse", "total_animals": 60},
        )
        
        assert state.answers["species"] == "mouse"
        assert state.answers["total_animals"] == 60


class TestCalculateProgress:
    """Tests for calculate_progress function."""
    
    def test_empty_state_zero_progress(self):
        """Test that empty state has zero progress."""
        state = QuestionnaireState()
        
        progress = calculate_progress(state)
        
        assert progress == 0.0
    
    def test_partial_progress(self):
        """Test partial progress calculation."""
        state = QuestionnaireState(
            answers={
                "protocol_title": "Test Protocol",
                "pi_name": "Dr. Test",
            },
        )
        
        progress = calculate_progress(state)
        
        assert 0 < progress < 1.0


class TestValidateQuestionnaire:
    """Tests for validate_questionnaire function."""
    
    def test_empty_state_has_errors(self):
        """Test that empty state has validation errors."""
        state = QuestionnaireState()
        
        errors = validate_questionnaire(state)
        
        assert len(errors) > 0
    
    def test_missing_required_detected(self):
        """Test that missing required fields are detected."""
        state = QuestionnaireState(
            answers={
                "protocol_title": "Test",
                # Missing pi_name and other required fields
            },
        )
        
        errors = validate_questionnaire(state)
        
        # Should have errors for missing required fields
        assert len(errors) > 0


class TestBranchDefinitions:
    """Tests for branch definitions."""
    
    def test_branches_exist(self):
        """Test that branches are defined."""
        assert len(BRANCHES) > 0
    
    def test_surgery_branch_defined(self):
        """Test surgery branch is defined."""
        branch_ids = [b.id for b in BRANCHES]
        assert "surgery_branch" in branch_ids
    
    def test_category_e_branch_defined(self):
        """Test Category E branch is defined."""
        branch_ids = [b.id for b in BRANCHES]
        assert "category_e_branch" in branch_ids
    
    def test_tumor_branch_defined(self):
        """Test tumor branch is defined."""
        branch_ids = [b.id for b in BRANCHES]
        assert "tumor_branch" in branch_ids
    
    def test_all_branches_have_ids(self):
        """Test all branches have unique IDs."""
        ids = [b.id for b in BRANCHES]
        assert len(ids) == len(set(ids))
    
    def test_all_branches_have_conditions(self):
        """Test all branches have conditions."""
        for branch in BRANCHES:
            assert len(branch.conditions) > 0


class TestBranchingScenarios:
    """Integration tests for branching scenarios."""
    
    def test_behavioral_study_path(self):
        """Test path for simple behavioral study."""
        state = QuestionnaireState(
            answers={
                "species": "mouse",
                "procedure_types": ["behavioral_testing"],
                "pain_category": "C",
            },
        )
        
        branches = get_active_branches(state.answers)
        branch_ids = [b.id for b in branches]
        
        # Should activate behavioral branch
        assert "behavior_branch" in branch_ids
        # Should NOT activate surgery or Category E
        assert "surgery_branch" not in branch_ids
        assert "category_e_branch" not in branch_ids
    
    def test_surgical_study_path(self):
        """Test path for surgical study."""
        state = QuestionnaireState(
            answers={
                "species": "rat",
                "procedure_types": ["survival_surgery", "blood_collection"],
                "pain_category": "D",
            },
        )
        
        branches = get_active_branches(state.answers)
        branch_ids = [b.id for b in branches]
        
        # Should activate surgery and pain management branches
        assert "surgery_branch" in branch_ids
        assert "blood_branch" in branch_ids
        assert "pain_management_branch" in branch_ids
    
    def test_tumor_model_path(self):
        """Test path for tumor model study."""
        state = QuestionnaireState(
            answers={
                "species": "mouse",
                "procedure_types": ["tumor_implantation", "injections"],
                "pain_category": "D",
            },
        )
        
        branches = get_active_branches(state.answers)
        branch_ids = [b.id for b in branches]
        
        # Should activate tumor and injection branches
        assert "tumor_branch" in branch_ids
        assert "injection_branch" in branch_ids
