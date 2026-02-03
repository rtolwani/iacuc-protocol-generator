"""
Checkpoint State Manager.

Manages workflow state persistence for human-in-the-loop review checkpoints.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Status of the overall workflow."""
    
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AWAITING_REVIEW = "awaiting_review"
    REVISION_REQUESTED = "revision_requested"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CheckpointStatus(str, Enum):
    """Status of a specific checkpoint."""
    
    PENDING = "pending"
    READY_FOR_REVIEW = "ready_for_review"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    SKIPPED = "skipped"


class ReviewerFeedback(BaseModel):
    """Feedback from a human reviewer."""
    
    reviewer_id: str = Field(description="ID of the reviewer")
    reviewer_name: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    decision: str = Field(description="approved, rejected, revision_requested")
    comments: Optional[str] = Field(default=None)
    specific_issues: list[str] = Field(default_factory=list)
    suggested_changes: Optional[str] = Field(default=None)


class CheckpointData(BaseModel):
    """Data for a single checkpoint."""
    
    id: str = Field(description="Unique checkpoint identifier")
    name: str = Field(description="Human-readable checkpoint name")
    status: CheckpointStatus = Field(default=CheckpointStatus.PENDING)
    agent_output: Optional[dict] = Field(default=None, description="Output from agent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    review_started_at: Optional[datetime] = Field(default=None)
    review_completed_at: Optional[datetime] = Field(default=None)
    feedback: list[ReviewerFeedback] = Field(default_factory=list)
    revision_count: int = Field(default=0)
    metadata: dict = Field(default_factory=dict)


class WorkflowState(BaseModel):
    """Complete state of a protocol generation workflow."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: Optional[str] = Field(default=None)
    status: WorkflowStatus = Field(default=WorkflowStatus.NOT_STARTED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Input data
    input_data: dict = Field(default_factory=dict)
    questionnaire_answers: dict = Field(default_factory=dict)
    
    # Checkpoints
    checkpoints: dict[str, CheckpointData] = Field(default_factory=dict)
    current_checkpoint: Optional[str] = Field(default=None)
    
    # Agent outputs
    agent_outputs: dict[str, Any] = Field(default_factory=dict)
    
    # Final output
    final_protocol: Optional[dict] = Field(default=None)
    
    # Error tracking
    errors: list[dict] = Field(default_factory=list)
    
    # Metadata
    metadata: dict = Field(default_factory=dict)


class StateManager:
    """
    Manages workflow state persistence.
    
    Supports file-based storage for simplicity.
    Can be extended to use database storage.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize state manager.
        
        Args:
            storage_path: Path to store state files. Defaults to ./workflow_states/
        """
        self.storage_path = storage_path or Path("./workflow_states")
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_state_file(self, workflow_id: str) -> Path:
        """Get the file path for a workflow state."""
        return self.storage_path / f"{workflow_id}.json"
    
    def create_workflow(
        self,
        input_data: Optional[dict] = None,
        questionnaire_answers: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> WorkflowState:
        """
        Create a new workflow.
        
        Args:
            input_data: Initial input data
            questionnaire_answers: Answers from questionnaire
            metadata: Additional metadata
            
        Returns:
            New WorkflowState.
        """
        state = WorkflowState(
            input_data=input_data or {},
            questionnaire_answers=questionnaire_answers or {},
            metadata=metadata or {},
        )
        
        self.save_state(state)
        return state
    
    def save_state(self, state: WorkflowState) -> None:
        """
        Save workflow state to storage.
        
        Args:
            state: The workflow state to save.
        """
        state.updated_at = datetime.utcnow()
        
        state_file = self._get_state_file(state.id)
        state_file.write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )
    
    def load_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Load workflow state from storage.
        
        Args:
            workflow_id: The workflow ID to load
            
        Returns:
            WorkflowState if found, None otherwise.
        """
        state_file = self._get_state_file(workflow_id)
        
        if not state_file.exists():
            return None
        
        data = json.loads(state_file.read_text(encoding="utf-8"))
        return WorkflowState.model_validate(data)
    
    def delete_state(self, workflow_id: str) -> bool:
        """
        Delete workflow state.
        
        Args:
            workflow_id: The workflow ID to delete
            
        Returns:
            True if deleted, False if not found.
        """
        state_file = self._get_state_file(workflow_id)
        
        if state_file.exists():
            state_file.unlink()
            return True
        return False
    
    def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
    ) -> list[WorkflowState]:
        """
        List all workflows, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of workflow states.
        """
        workflows = []
        
        for state_file in self.storage_path.glob("*.json"):
            try:
                state = self.load_state(state_file.stem)
                if state:
                    if status is None or state.status == status:
                        workflows.append(state)
            except Exception:
                continue  # Skip invalid files
        
        return workflows
    
    def update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStatus,
    ) -> Optional[WorkflowState]:
        """
        Update workflow status.
        
        Args:
            workflow_id: The workflow ID
            status: New status
            
        Returns:
            Updated state or None if not found.
        """
        state = self.load_state(workflow_id)
        if not state:
            return None
        
        state.status = status
        self.save_state(state)
        return state
    
    def add_checkpoint(
        self,
        workflow_id: str,
        checkpoint_id: str,
        checkpoint_name: str,
        agent_output: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[CheckpointData]:
        """
        Add a checkpoint to a workflow.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_id: Unique checkpoint ID
            checkpoint_name: Human-readable name
            agent_output: Output from the agent
            metadata: Additional metadata
            
        Returns:
            CheckpointData if successful, None if workflow not found.
        """
        state = self.load_state(workflow_id)
        if not state:
            return None
        
        checkpoint = CheckpointData(
            id=checkpoint_id,
            name=checkpoint_name,
            agent_output=agent_output,
            metadata=metadata or {},
        )
        
        state.checkpoints[checkpoint_id] = checkpoint
        state.current_checkpoint = checkpoint_id
        self.save_state(state)
        
        return checkpoint
    
    def update_checkpoint_status(
        self,
        workflow_id: str,
        checkpoint_id: str,
        status: CheckpointStatus,
    ) -> Optional[CheckpointData]:
        """
        Update checkpoint status.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_id: The checkpoint ID
            status: New status
            
        Returns:
            Updated checkpoint or None.
        """
        state = self.load_state(workflow_id)
        if not state or checkpoint_id not in state.checkpoints:
            return None
        
        checkpoint = state.checkpoints[checkpoint_id]
        checkpoint.status = status
        checkpoint.updated_at = datetime.utcnow()
        
        if status == CheckpointStatus.UNDER_REVIEW:
            checkpoint.review_started_at = datetime.utcnow()
        elif status in [
            CheckpointStatus.APPROVED,
            CheckpointStatus.REJECTED,
            CheckpointStatus.REVISION_REQUESTED,
        ]:
            checkpoint.review_completed_at = datetime.utcnow()
        
        self.save_state(state)
        return checkpoint
    
    def add_reviewer_feedback(
        self,
        workflow_id: str,
        checkpoint_id: str,
        feedback: ReviewerFeedback,
    ) -> Optional[CheckpointData]:
        """
        Add reviewer feedback to a checkpoint.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_id: The checkpoint ID
            feedback: Reviewer feedback
            
        Returns:
            Updated checkpoint or None.
        """
        state = self.load_state(workflow_id)
        if not state or checkpoint_id not in state.checkpoints:
            return None
        
        checkpoint = state.checkpoints[checkpoint_id]
        checkpoint.feedback.append(feedback)
        checkpoint.updated_at = datetime.utcnow()
        
        # Update status based on feedback
        if feedback.decision == "approved":
            checkpoint.status = CheckpointStatus.APPROVED
            checkpoint.review_completed_at = datetime.utcnow()
        elif feedback.decision == "rejected":
            checkpoint.status = CheckpointStatus.REJECTED
            checkpoint.review_completed_at = datetime.utcnow()
        elif feedback.decision == "revision_requested":
            checkpoint.status = CheckpointStatus.REVISION_REQUESTED
            checkpoint.revision_count += 1
        
        self.save_state(state)
        return checkpoint
    
    def store_agent_output(
        self,
        workflow_id: str,
        agent_name: str,
        output: Any,
    ) -> bool:
        """
        Store output from an agent.
        
        Args:
            workflow_id: The workflow ID
            agent_name: Name of the agent
            output: Agent output data
            
        Returns:
            True if successful, False if workflow not found.
        """
        state = self.load_state(workflow_id)
        if not state:
            return False
        
        state.agent_outputs[agent_name] = output
        self.save_state(state)
        return True
    
    def get_agent_output(
        self,
        workflow_id: str,
        agent_name: str,
    ) -> Optional[Any]:
        """
        Get stored output from an agent.
        
        Args:
            workflow_id: The workflow ID
            agent_name: Name of the agent
            
        Returns:
            Agent output or None.
        """
        state = self.load_state(workflow_id)
        if not state:
            return None
        
        return state.agent_outputs.get(agent_name)
    
    def add_error(
        self,
        workflow_id: str,
        error_type: str,
        error_message: str,
        details: Optional[dict] = None,
    ) -> bool:
        """
        Record an error in the workflow.
        
        Args:
            workflow_id: The workflow ID
            error_type: Type of error
            error_message: Error message
            details: Additional details
            
        Returns:
            True if successful.
        """
        state = self.load_state(workflow_id)
        if not state:
            return False
        
        state.errors.append({
            "type": error_type,
            "message": error_message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        self.save_state(state)
        return True
    
    def get_pending_reviews(self) -> list[tuple[WorkflowState, CheckpointData]]:
        """
        Get all checkpoints awaiting review.
        
        Returns:
            List of (workflow, checkpoint) tuples.
        """
        pending = []
        
        for workflow in self.list_workflows():
            for checkpoint in workflow.checkpoints.values():
                if checkpoint.status == CheckpointStatus.READY_FOR_REVIEW:
                    pending.append((workflow, checkpoint))
        
        return pending
    
    def can_proceed_to_next(self, workflow_id: str) -> tuple[bool, str]:
        """
        Check if workflow can proceed to next checkpoint.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Tuple of (can_proceed, reason).
        """
        state = self.load_state(workflow_id)
        if not state:
            return False, "Workflow not found"
        
        if state.status == WorkflowStatus.FAILED:
            return False, "Workflow has failed"
        
        if state.status == WorkflowStatus.CANCELLED:
            return False, "Workflow was cancelled"
        
        if state.current_checkpoint:
            current = state.checkpoints.get(state.current_checkpoint)
            if current:
                if current.status == CheckpointStatus.READY_FOR_REVIEW:
                    return False, "Awaiting review"
                if current.status == CheckpointStatus.UNDER_REVIEW:
                    return False, "Under review"
                if current.status == CheckpointStatus.REVISION_REQUESTED:
                    return False, "Revision requested"
                if current.status == CheckpointStatus.REJECTED:
                    return False, "Checkpoint rejected"
        
        return True, "OK"


# Export
__all__ = [
    "WorkflowStatus",
    "CheckpointStatus",
    "ReviewerFeedback",
    "CheckpointData",
    "WorkflowState",
    "StateManager",
]
