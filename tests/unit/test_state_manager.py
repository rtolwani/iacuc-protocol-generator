"""
Unit tests for Checkpoint State Manager.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.review.state_manager import (
    WorkflowStatus,
    CheckpointStatus,
    ReviewerFeedback,
    CheckpointData,
    WorkflowState,
    StateManager,
)


@pytest.fixture
def temp_storage():
    """Create temporary storage for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def state_manager(temp_storage):
    """Create state manager with temp storage."""
    return StateManager(storage_path=temp_storage)


class TestWorkflowStatus:
    """Tests for WorkflowStatus enum."""
    
    def test_all_statuses_exist(self):
        """Test all expected statuses exist."""
        expected = [
            "not_started", "in_progress", "awaiting_review",
            "revision_requested", "completed", "failed", "cancelled"
        ]
        
        actual = [s.value for s in WorkflowStatus]
        
        for status in expected:
            assert status in actual


class TestCheckpointStatus:
    """Tests for CheckpointStatus enum."""
    
    def test_all_statuses_exist(self):
        """Test all expected statuses exist."""
        expected = [
            "pending", "ready_for_review", "under_review",
            "approved", "rejected", "revision_requested", "skipped"
        ]
        
        actual = [s.value for s in CheckpointStatus]
        
        for status in expected:
            assert status in actual


class TestReviewerFeedback:
    """Tests for ReviewerFeedback model."""
    
    def test_create_feedback(self):
        """Test creating reviewer feedback."""
        feedback = ReviewerFeedback(
            reviewer_id="reviewer_1",
            decision="approved",
        )
        
        assert feedback.reviewer_id == "reviewer_1"
        assert feedback.decision == "approved"
    
    def test_feedback_with_comments(self):
        """Test feedback with comments."""
        feedback = ReviewerFeedback(
            reviewer_id="reviewer_1",
            decision="revision_requested",
            comments="Please clarify the dosing schedule",
            specific_issues=["Dosing unclear", "Missing endpoints"],
        )
        
        assert feedback.comments is not None
        assert len(feedback.specific_issues) == 2
    
    def test_feedback_has_timestamp(self):
        """Test feedback has automatic timestamp."""
        feedback = ReviewerFeedback(
            reviewer_id="reviewer_1",
            decision="approved",
        )
        
        assert feedback.timestamp is not None


class TestCheckpointData:
    """Tests for CheckpointData model."""
    
    def test_create_checkpoint(self):
        """Test creating checkpoint."""
        checkpoint = CheckpointData(
            id="cp_1",
            name="Intake Review",
        )
        
        assert checkpoint.id == "cp_1"
        assert checkpoint.status == CheckpointStatus.PENDING
    
    def test_checkpoint_with_output(self):
        """Test checkpoint with agent output."""
        checkpoint = CheckpointData(
            id="cp_1",
            name="Review",
            agent_output={"summary": "Test output"},
        )
        
        assert checkpoint.agent_output["summary"] == "Test output"
    
    def test_checkpoint_timestamps(self):
        """Test checkpoint has timestamps."""
        checkpoint = CheckpointData(
            id="cp_1",
            name="Review",
        )
        
        assert checkpoint.created_at is not None
        assert checkpoint.updated_at is not None


class TestWorkflowState:
    """Tests for WorkflowState model."""
    
    def test_create_workflow(self):
        """Test creating workflow state."""
        state = WorkflowState()
        
        assert state.id is not None
        assert state.status == WorkflowStatus.NOT_STARTED
    
    def test_workflow_with_input(self):
        """Test workflow with input data."""
        state = WorkflowState(
            input_data={"species": "mouse"},
            questionnaire_answers={"total_animals": 60},
        )
        
        assert state.input_data["species"] == "mouse"
        assert state.questionnaire_answers["total_animals"] == 60
    
    def test_workflow_has_unique_id(self):
        """Test each workflow has unique ID."""
        state1 = WorkflowState()
        state2 = WorkflowState()
        
        assert state1.id != state2.id


class TestStateManagerBasics:
    """Basic tests for StateManager."""
    
    def test_create_manager(self, temp_storage):
        """Test creating state manager."""
        manager = StateManager(storage_path=temp_storage)
        
        assert manager.storage_path == temp_storage
    
    def test_create_workflow(self, state_manager):
        """Test creating workflow through manager."""
        state = state_manager.create_workflow(
            input_data={"species": "mouse"},
        )
        
        assert state.id is not None
        assert state.input_data["species"] == "mouse"
    
    def test_save_and_load(self, state_manager):
        """Test saving and loading workflow."""
        # Create and save
        state = state_manager.create_workflow(
            input_data={"test": "data"},
        )
        workflow_id = state.id
        
        # Load
        loaded = state_manager.load_state(workflow_id)
        
        assert loaded is not None
        assert loaded.id == workflow_id
        assert loaded.input_data["test"] == "data"
    
    def test_load_nonexistent(self, state_manager):
        """Test loading nonexistent workflow."""
        loaded = state_manager.load_state("nonexistent-id")
        
        assert loaded is None
    
    def test_delete_workflow(self, state_manager):
        """Test deleting workflow."""
        state = state_manager.create_workflow()
        workflow_id = state.id
        
        # Verify exists
        assert state_manager.load_state(workflow_id) is not None
        
        # Delete
        result = state_manager.delete_state(workflow_id)
        
        assert result == True
        assert state_manager.load_state(workflow_id) is None
    
    def test_delete_nonexistent(self, state_manager):
        """Test deleting nonexistent workflow."""
        result = state_manager.delete_state("nonexistent-id")
        
        assert result == False


class TestStateManagerWorkflowOperations:
    """Tests for workflow operations."""
    
    def test_update_status(self, state_manager):
        """Test updating workflow status."""
        state = state_manager.create_workflow()
        
        updated = state_manager.update_workflow_status(
            state.id,
            WorkflowStatus.IN_PROGRESS,
        )
        
        assert updated.status == WorkflowStatus.IN_PROGRESS
    
    def test_list_workflows(self, state_manager):
        """Test listing workflows."""
        # Create multiple
        state_manager.create_workflow()
        state_manager.create_workflow()
        
        workflows = state_manager.list_workflows()
        
        assert len(workflows) == 2
    
    def test_list_workflows_by_status(self, state_manager):
        """Test filtering workflows by status."""
        state1 = state_manager.create_workflow()
        state2 = state_manager.create_workflow()
        
        state_manager.update_workflow_status(
            state1.id,
            WorkflowStatus.COMPLETED,
        )
        
        completed = state_manager.list_workflows(
            status=WorkflowStatus.COMPLETED,
        )
        
        assert len(completed) == 1
        assert completed[0].id == state1.id


class TestStateManagerCheckpoints:
    """Tests for checkpoint operations."""
    
    def test_add_checkpoint(self, state_manager):
        """Test adding checkpoint."""
        state = state_manager.create_workflow()
        
        checkpoint = state_manager.add_checkpoint(
            state.id,
            checkpoint_id="intake_review",
            checkpoint_name="Intake Review",
            agent_output={"summary": "Test"},
        )
        
        assert checkpoint is not None
        assert checkpoint.id == "intake_review"
    
    def test_checkpoint_stored_in_workflow(self, state_manager):
        """Test checkpoint is stored in workflow."""
        state = state_manager.create_workflow()
        
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        
        loaded = state_manager.load_state(state.id)
        
        assert "cp_1" in loaded.checkpoints
    
    def test_update_checkpoint_status(self, state_manager):
        """Test updating checkpoint status."""
        state = state_manager.create_workflow()
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        
        updated = state_manager.update_checkpoint_status(
            state.id,
            "cp_1",
            CheckpointStatus.READY_FOR_REVIEW,
        )
        
        assert updated.status == CheckpointStatus.READY_FOR_REVIEW
    
    def test_review_started_timestamp(self, state_manager):
        """Test review started timestamp is set."""
        state = state_manager.create_workflow()
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        
        updated = state_manager.update_checkpoint_status(
            state.id,
            "cp_1",
            CheckpointStatus.UNDER_REVIEW,
        )
        
        assert updated.review_started_at is not None


class TestStateManagerFeedback:
    """Tests for reviewer feedback."""
    
    def test_add_feedback(self, state_manager):
        """Test adding reviewer feedback."""
        state = state_manager.create_workflow()
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        
        feedback = ReviewerFeedback(
            reviewer_id="reviewer_1",
            decision="approved",
            comments="Looks good",
        )
        
        updated = state_manager.add_reviewer_feedback(
            state.id,
            "cp_1",
            feedback,
        )
        
        assert len(updated.feedback) == 1
        assert updated.feedback[0].decision == "approved"
    
    def test_feedback_updates_status_approved(self, state_manager):
        """Test feedback updates status to approved."""
        state = state_manager.create_workflow()
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        
        feedback = ReviewerFeedback(
            reviewer_id="reviewer_1",
            decision="approved",
        )
        
        updated = state_manager.add_reviewer_feedback(
            state.id,
            "cp_1",
            feedback,
        )
        
        assert updated.status == CheckpointStatus.APPROVED
    
    def test_feedback_updates_status_rejected(self, state_manager):
        """Test feedback updates status to rejected."""
        state = state_manager.create_workflow()
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        
        feedback = ReviewerFeedback(
            reviewer_id="reviewer_1",
            decision="rejected",
            comments="Does not meet requirements",
        )
        
        updated = state_manager.add_reviewer_feedback(
            state.id,
            "cp_1",
            feedback,
        )
        
        assert updated.status == CheckpointStatus.REJECTED
    
    def test_revision_increments_count(self, state_manager):
        """Test revision request increments count."""
        state = state_manager.create_workflow()
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        
        feedback = ReviewerFeedback(
            reviewer_id="reviewer_1",
            decision="revision_requested",
            comments="Please revise",
        )
        
        updated = state_manager.add_reviewer_feedback(
            state.id,
            "cp_1",
            feedback,
        )
        
        assert updated.revision_count == 1
        assert updated.status == CheckpointStatus.REVISION_REQUESTED


class TestStateManagerAgentOutputs:
    """Tests for agent output storage."""
    
    def test_store_agent_output(self, state_manager):
        """Test storing agent output."""
        state = state_manager.create_workflow()
        
        result = state_manager.store_agent_output(
            state.id,
            "regulatory_scout",
            {"regulations": ["AWA", "PHS"]},
        )
        
        assert result == True
    
    def test_get_agent_output(self, state_manager):
        """Test retrieving agent output."""
        state = state_manager.create_workflow()
        state_manager.store_agent_output(
            state.id,
            "lay_summary",
            {"text": "Summary text"},
        )
        
        output = state_manager.get_agent_output(state.id, "lay_summary")
        
        assert output["text"] == "Summary text"
    
    def test_get_missing_output(self, state_manager):
        """Test getting missing agent output."""
        state = state_manager.create_workflow()
        
        output = state_manager.get_agent_output(state.id, "nonexistent")
        
        assert output is None


class TestStateManagerErrors:
    """Tests for error tracking."""
    
    def test_add_error(self, state_manager):
        """Test adding error."""
        state = state_manager.create_workflow()
        
        result = state_manager.add_error(
            state.id,
            "agent_error",
            "Agent failed to execute",
            {"agent": "regulatory_scout"},
        )
        
        assert result == True
        
        loaded = state_manager.load_state(state.id)
        assert len(loaded.errors) == 1
    
    def test_error_has_timestamp(self, state_manager):
        """Test error has timestamp."""
        state = state_manager.create_workflow()
        
        state_manager.add_error(
            state.id,
            "test_error",
            "Test message",
        )
        
        loaded = state_manager.load_state(state.id)
        assert "timestamp" in loaded.errors[0]


class TestStateManagerPendingReviews:
    """Tests for pending review queries."""
    
    def test_get_pending_reviews(self, state_manager):
        """Test getting pending reviews."""
        state = state_manager.create_workflow()
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        state_manager.update_checkpoint_status(
            state.id,
            "cp_1",
            CheckpointStatus.READY_FOR_REVIEW,
        )
        
        pending = state_manager.get_pending_reviews()
        
        assert len(pending) == 1
        workflow, checkpoint = pending[0]
        assert checkpoint.id == "cp_1"
    
    def test_excludes_approved(self, state_manager):
        """Test excludes approved checkpoints."""
        state = state_manager.create_workflow()
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        state_manager.update_checkpoint_status(
            state.id,
            "cp_1",
            CheckpointStatus.APPROVED,
        )
        
        pending = state_manager.get_pending_reviews()
        
        assert len(pending) == 0


class TestStateManagerProceedCheck:
    """Tests for can_proceed_to_next."""
    
    def test_can_proceed_new_workflow(self, state_manager):
        """Test new workflow can proceed."""
        state = state_manager.create_workflow()
        
        can_proceed, reason = state_manager.can_proceed_to_next(state.id)
        
        assert can_proceed == True
    
    def test_cannot_proceed_awaiting_review(self, state_manager):
        """Test cannot proceed when awaiting review."""
        state = state_manager.create_workflow()
        state_manager.add_checkpoint(
            state.id,
            checkpoint_id="cp_1",
            checkpoint_name="Test",
        )
        state_manager.update_checkpoint_status(
            state.id,
            "cp_1",
            CheckpointStatus.READY_FOR_REVIEW,
        )
        
        can_proceed, reason = state_manager.can_proceed_to_next(state.id)
        
        assert can_proceed == False
        assert "review" in reason.lower()
    
    def test_cannot_proceed_failed(self, state_manager):
        """Test cannot proceed when failed."""
        state = state_manager.create_workflow()
        state_manager.update_workflow_status(state.id, WorkflowStatus.FAILED)
        
        can_proceed, reason = state_manager.can_proceed_to_next(state.id)
        
        assert can_proceed == False
        assert "failed" in reason.lower()
