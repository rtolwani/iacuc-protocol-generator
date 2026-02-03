"""
Unit tests for Review Checkpoints.
"""

import tempfile
from pathlib import Path

import pytest

from src.review.state_manager import (
    StateManager,
    CheckpointStatus,
    WorkflowStatus,
)
from src.review.checkpoints import (
    CheckpointType,
    CheckpointConfig,
    CHECKPOINTS,
    CheckpointManager,
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


@pytest.fixture
def checkpoint_manager(state_manager):
    """Create checkpoint manager."""
    return CheckpointManager(state_manager)


@pytest.fixture
def workflow_with_checkpoints(state_manager, checkpoint_manager):
    """Create workflow with initialized checkpoints."""
    workflow = state_manager.create_workflow(
        input_data={"species": "mouse"},
    )
    checkpoint_manager.initialize_checkpoints(workflow.id)
    return workflow


class TestCheckpointType:
    """Tests for CheckpointType enum."""
    
    def test_all_types_exist(self):
        """Test all checkpoint types exist."""
        expected = [
            "intake_review",
            "regulatory_review",
            "statistical_review",
            "veterinary_review",
            "final_review",
        ]
        
        actual = [ct.value for ct in CheckpointType]
        
        for t in expected:
            assert t in actual
    
    def test_five_checkpoints(self):
        """Test there are exactly 5 checkpoint types."""
        assert len(CheckpointType) == 5


class TestCheckpointConfig:
    """Tests for CheckpointConfig model."""
    
    def test_create_config(self):
        """Test creating checkpoint config."""
        config = CheckpointConfig(
            id="test",
            name="Test Checkpoint",
            checkpoint_type=CheckpointType.INTAKE_REVIEW,
            description="Test description",
            required_agents=["agent1"],
            review_instructions="Test instructions",
            order=1,
        )
        
        assert config.id == "test"
        assert config.checkpoint_type == CheckpointType.INTAKE_REVIEW


class TestCheckpointDefinitions:
    """Tests for checkpoint definitions."""
    
    def test_all_types_have_config(self):
        """Test all types have configuration."""
        for checkpoint_type in CheckpointType:
            assert checkpoint_type in CHECKPOINTS
    
    def test_intake_review_config(self):
        """Test intake review configuration."""
        config = CHECKPOINTS[CheckpointType.INTAKE_REVIEW]
        
        assert config.id == "intake_review"
        assert "intake_specialist" in config.required_agents
        assert config.order == 1
    
    def test_regulatory_review_config(self):
        """Test regulatory review configuration."""
        config = CHECKPOINTS[CheckpointType.REGULATORY_REVIEW]
        
        assert config.id == "regulatory_review"
        assert "regulatory_scout" in config.required_agents
        assert "alternatives_researcher" in config.required_agents
    
    def test_statistical_review_config(self):
        """Test statistical review configuration."""
        config = CHECKPOINTS[CheckpointType.STATISTICAL_REVIEW]
        
        assert config.id == "statistical_review"
        assert "statistical_consultant" in config.required_agents
    
    def test_veterinary_review_config(self):
        """Test veterinary review configuration."""
        config = CHECKPOINTS[CheckpointType.VETERINARY_REVIEW]
        
        assert config.id == "veterinary_review"
        assert "veterinary_reviewer" in config.required_agents
        assert "procedure_writer" in config.required_agents
    
    def test_final_review_config(self):
        """Test final review configuration."""
        config = CHECKPOINTS[CheckpointType.FINAL_REVIEW]
        
        assert config.id == "final_review"
        assert "protocol_assembler" in config.required_agents
        assert config.order == 5
    
    def test_all_have_instructions(self):
        """Test all checkpoints have review instructions."""
        for config in CHECKPOINTS.values():
            assert config.review_instructions
            assert len(config.review_instructions) > 50
    
    def test_checkpoints_ordered(self):
        """Test checkpoints have correct order."""
        orders = [c.order for c in CHECKPOINTS.values()]
        assert sorted(orders) == [1, 2, 3, 4, 5]


class TestCheckpointManagerInit:
    """Tests for CheckpointManager initialization."""
    
    def test_create_manager(self, state_manager):
        """Test creating checkpoint manager."""
        manager = CheckpointManager(state_manager)
        
        assert manager.state_manager == state_manager
    
    def test_get_checkpoint_config(self, checkpoint_manager):
        """Test getting checkpoint config."""
        config = checkpoint_manager.get_checkpoint_config(
            CheckpointType.INTAKE_REVIEW
        )
        
        assert config.id == "intake_review"


class TestCheckpointInitialization:
    """Tests for checkpoint initialization."""
    
    def test_initialize_checkpoints(
        self,
        state_manager,
        checkpoint_manager,
    ):
        """Test initializing checkpoints."""
        workflow = state_manager.create_workflow()
        
        checkpoints = checkpoint_manager.initialize_checkpoints(workflow.id)
        
        assert len(checkpoints) == 5
    
    def test_checkpoints_stored(
        self,
        state_manager,
        checkpoint_manager,
    ):
        """Test checkpoints are stored in workflow."""
        workflow = state_manager.create_workflow()
        checkpoint_manager.initialize_checkpoints(workflow.id)
        
        loaded = state_manager.load_state(workflow.id)
        
        assert len(loaded.checkpoints) == 5
    
    def test_checkpoints_have_metadata(
        self,
        workflow_with_checkpoints,
        state_manager,
    ):
        """Test checkpoints have metadata."""
        loaded = state_manager.load_state(workflow_with_checkpoints.id)
        
        checkpoint = loaded.checkpoints["intake_review"]
        
        assert "type" in checkpoint.metadata
        assert "required_agents" in checkpoint.metadata


class TestMarkReadyForReview:
    """Tests for marking checkpoint ready for review."""
    
    def test_mark_ready(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
        state_manager,
    ):
        """Test marking checkpoint ready for review."""
        result = checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {"completeness_score": 0.95},
        )
        
        assert result is not None
        assert result.status == CheckpointStatus.READY_FOR_REVIEW
    
    def test_workflow_status_updated(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
        state_manager,
    ):
        """Test workflow status is updated."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        loaded = state_manager.load_state(workflow_with_checkpoints.id)
        
        assert loaded.status == WorkflowStatus.AWAITING_REVIEW


class TestAutoApproval:
    """Tests for auto-approval checking."""
    
    def test_can_auto_approve(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test can auto-approve when conditions met."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {
                "completeness_score": 0.95,
                "missing_required_fields": 0,
            },
        )
        
        can_approve, reasons = checkpoint_manager.check_auto_approval(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
        )
        
        assert can_approve == True
        assert len(reasons) == 0
    
    def test_cannot_auto_approve_low_score(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test cannot auto-approve when score too low."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {
                "completeness_score": 0.7,
                "missing_required_fields": 0,
            },
        )
        
        can_approve, reasons = checkpoint_manager.check_auto_approval(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
        )
        
        assert can_approve == False
        assert len(reasons) > 0


class TestApproval:
    """Tests for checkpoint approval."""
    
    def test_approve(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
        state_manager,
    ):
        """Test approving checkpoint."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        result = checkpoint_manager.approve(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            reviewer_id="reviewer_1",
            comments="Looks good",
        )
        
        assert result is not None
        assert result.status == CheckpointStatus.APPROVED
    
    def test_approval_has_feedback(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test approval records feedback."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        result = checkpoint_manager.approve(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            reviewer_id="reviewer_1",
        )
        
        assert len(result.feedback) == 1
        assert result.feedback[0].decision == "approved"


class TestRejection:
    """Tests for checkpoint rejection."""
    
    def test_reject(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test rejecting checkpoint."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        result = checkpoint_manager.reject(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            reviewer_id="reviewer_1",
            comments="Critical issues found",
            specific_issues=["Missing species", "No procedures"],
        )
        
        assert result is not None
        assert result.status == CheckpointStatus.REJECTED
    
    def test_rejection_updates_workflow(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
        state_manager,
    ):
        """Test rejection updates workflow status."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        checkpoint_manager.reject(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            reviewer_id="reviewer_1",
            comments="Critical issues",
        )
        
        loaded = state_manager.load_state(workflow_with_checkpoints.id)
        assert loaded.status == WorkflowStatus.FAILED


class TestRevisionRequest:
    """Tests for revision requests."""
    
    def test_request_revision(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test requesting revision."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        result = checkpoint_manager.request_revision(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            reviewer_id="reviewer_1",
            comments="Please fix the following",
            specific_issues=["Dosing unclear"],
            suggested_changes="Add detailed dosing table",
        )
        
        assert result is not None
        assert result.status == CheckpointStatus.REVISION_REQUESTED
    
    def test_revision_updates_workflow(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
        state_manager,
    ):
        """Test revision request updates workflow status."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        checkpoint_manager.request_revision(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            reviewer_id="reviewer_1",
            comments="Please revise",
        )
        
        loaded = state_manager.load_state(workflow_with_checkpoints.id)
        assert loaded.status == WorkflowStatus.REVISION_REQUESTED
    
    def test_get_revision_feedback(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test getting revision feedback."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        checkpoint_manager.request_revision(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            reviewer_id="reviewer_1",
            comments="Fix issues",
            suggested_changes="Add X",
        )
        
        feedback = checkpoint_manager.get_revision_feedback(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
        )
        
        assert feedback is not None
        assert feedback.suggested_changes == "Add X"


class TestCheckpointProgression:
    """Tests for checkpoint progression."""
    
    def test_get_next_checkpoint(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test getting next checkpoint."""
        next_cp = checkpoint_manager.get_next_checkpoint(
            workflow_with_checkpoints.id
        )
        
        assert next_cp is not None
        assert next_cp.id == "intake_review"
    
    def test_next_checkpoint_after_approval(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test next checkpoint advances after approval."""
        # Approve intake review
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        checkpoint_manager.approve(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            reviewer_id="r1",
        )
        
        next_cp = checkpoint_manager.get_next_checkpoint(
            workflow_with_checkpoints.id
        )
        
        assert next_cp is not None
        assert next_cp.id == "regulatory_review"
    
    def test_all_checkpoints_approved(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test checking if all checkpoints approved."""
        # Initially not all approved
        assert checkpoint_manager.are_all_checkpoints_approved(
            workflow_with_checkpoints.id
        ) == False
    
    def test_all_approved_after_completion(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test all approved after completing all checkpoints."""
        # Approve all checkpoints
        for cp_type in CheckpointType:
            checkpoint_manager.mark_ready_for_review(
                workflow_with_checkpoints.id,
                cp_type,
                {},
            )
            checkpoint_manager.approve(
                workflow_with_checkpoints.id,
                cp_type,
                reviewer_id="r1",
            )
        
        assert checkpoint_manager.are_all_checkpoints_approved(
            workflow_with_checkpoints.id
        ) == True


class TestCheckpointSummary:
    """Tests for checkpoint summary."""
    
    def test_get_summary(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test getting checkpoint summary."""
        summary = checkpoint_manager.get_checkpoint_summary(
            workflow_with_checkpoints.id
        )
        
        assert len(summary) == 5
    
    def test_summary_has_fields(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test summary has required fields."""
        summary = checkpoint_manager.get_checkpoint_summary(
            workflow_with_checkpoints.id
        )
        
        for item in summary:
            assert "id" in item
            assert "name" in item
            assert "status" in item
            assert "order" in item
    
    def test_summary_reflects_status(
        self,
        workflow_with_checkpoints,
        checkpoint_manager,
    ):
        """Test summary reflects checkpoint status."""
        checkpoint_manager.mark_ready_for_review(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        checkpoint_manager.approve(
            workflow_with_checkpoints.id,
            CheckpointType.INTAKE_REVIEW,
            reviewer_id="r1",
        )
        
        summary = checkpoint_manager.get_checkpoint_summary(
            workflow_with_checkpoints.id
        )
        
        intake = next(s for s in summary if s["id"] == "intake_review")
        assert intake["status"] == "approved"
