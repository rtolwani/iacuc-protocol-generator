"""
Review Checkpoints Definition.

Defines the 5 human review points in the protocol generation workflow.
"""

from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

from src.review.state_manager import (
    StateManager,
    WorkflowState,
    CheckpointData,
    CheckpointStatus,
    WorkflowStatus,
    ReviewerFeedback,
)


class CheckpointType(str, Enum):
    """Types of review checkpoints."""
    
    INTAKE_REVIEW = "intake_review"
    REGULATORY_REVIEW = "regulatory_review"
    STATISTICAL_REVIEW = "statistical_review"
    VETERINARY_REVIEW = "veterinary_review"
    FINAL_REVIEW = "final_review"


class CheckpointConfig(BaseModel):
    """Configuration for a checkpoint."""
    
    id: str = Field(description="Checkpoint ID")
    name: str = Field(description="Human-readable name")
    checkpoint_type: CheckpointType = Field(description="Type of checkpoint")
    description: str = Field(description="Description for reviewers")
    required_agents: list[str] = Field(description="Agents that must complete before this checkpoint")
    review_instructions: str = Field(description="Instructions for the reviewer")
    auto_approve_conditions: Optional[dict] = Field(default=None, description="Conditions for auto-approval")
    order: int = Field(description="Order in workflow")


# ============================================================================
# CHECKPOINT DEFINITIONS
# ============================================================================

CHECKPOINTS = {
    CheckpointType.INTAKE_REVIEW: CheckpointConfig(
        id="intake_review",
        name="Research Profile Review",
        checkpoint_type=CheckpointType.INTAKE_REVIEW,
        description="Review the extracted research parameters and ensure completeness",
        required_agents=["intake_specialist"],
        review_instructions="""
Please review the extracted research profile:
1. Verify species and strain are correctly identified
2. Confirm animal numbers are reasonable
3. Check that procedures are accurately captured
4. Identify any missing critical information
5. Ensure the research classification is appropriate

Approve if all essential information is captured correctly.
Request revision if critical details are missing or incorrect.
        """.strip(),
        auto_approve_conditions={
            "completeness_score": {"min": 0.9},
            "missing_required_fields": {"max": 0},
        },
        order=1,
    ),
    
    CheckpointType.REGULATORY_REVIEW: CheckpointConfig(
        id="regulatory_review",
        name="Regulatory Compliance Review",
        checkpoint_type=CheckpointType.REGULATORY_REVIEW,
        description="Review regulatory requirements and 3Rs documentation",
        required_agents=["regulatory_scout", "alternatives_researcher"],
        review_instructions="""
Please review the regulatory assessment:
1. Verify correct USDA pain category classification
2. Confirm all applicable regulations are identified
3. Check that 3Rs documentation is complete
4. Review alternatives search methodology
5. Ensure literature search databases are appropriate

Approve if regulatory requirements are properly identified.
Request revision if pain category seems incorrect or 3Rs incomplete.
        """.strip(),
        auto_approve_conditions={
            "pain_category_confidence": {"min": 0.8},
            "three_rs_sections_complete": {"min": 3},
        },
        order=2,
    ),
    
    CheckpointType.STATISTICAL_REVIEW: CheckpointConfig(
        id="statistical_review",
        name="Statistical Design Review",
        checkpoint_type=CheckpointType.STATISTICAL_REVIEW,
        description="Review sample size justification and statistical approach",
        required_agents=["statistical_consultant"],
        review_instructions="""
Please review the statistical analysis:
1. Verify power analysis calculations
2. Confirm appropriate statistical tests are selected
3. Check that sample size is justified
4. Review effect size assumptions
5. Ensure experimental design is sound

Approve if statistical justification is rigorous.
Request revision if power is insufficient or assumptions seem wrong.
        """.strip(),
        auto_approve_conditions={
            "power": {"min": 0.8},
            "sample_size_justified": True,
        },
        order=3,
    ),
    
    CheckpointType.VETERINARY_REVIEW: CheckpointConfig(
        id="veterinary_review",
        name="Veterinary/Welfare Review",
        checkpoint_type=CheckpointType.VETERINARY_REVIEW,
        description="Review animal welfare considerations and procedures",
        required_agents=["veterinary_reviewer", "procedure_writer"],
        review_instructions="""
Please review the veterinary and welfare aspects:
1. Verify anesthesia and analgesia protocols
2. Check drug dosages against formulary
3. Confirm humane endpoints are appropriate
4. Review monitoring schedules
5. Ensure euthanasia methods are AVMA-approved

Approve if welfare considerations are adequately addressed.
Request revision if dosages are incorrect or endpoints are missing.
        """.strip(),
        auto_approve_conditions={
            "drug_doses_validated": True,
            "endpoints_defined": True,
            "critical_issues": {"max": 0},
        },
        order=4,
    ),
    
    CheckpointType.FINAL_REVIEW: CheckpointConfig(
        id="final_review",
        name="Final Protocol Review",
        checkpoint_type=CheckpointType.FINAL_REVIEW,
        description="Final review of complete assembled protocol",
        required_agents=["protocol_assembler", "lay_summary_writer"],
        review_instructions="""
Please perform final review of the complete protocol:
1. Verify all sections are present and complete
2. Check for internal consistency
3. Review lay summary for clarity
4. Confirm regulatory compliance
5. Ensure protocol is ready for IACUC submission

Approve if protocol is complete and submission-ready.
Request revision if any sections need improvement.
        """.strip(),
        auto_approve_conditions={
            "completeness_score": {"min": 0.95},
            "consistency_errors": {"max": 0},
        },
        order=5,
    ),
}


class CheckpointManager:
    """
    Manages review checkpoints in the workflow.
    """
    
    def __init__(self, state_manager: StateManager):
        """
        Initialize checkpoint manager.
        
        Args:
            state_manager: StateManager for persistence.
        """
        self.state_manager = state_manager
    
    def get_checkpoint_config(
        self,
        checkpoint_type: CheckpointType,
    ) -> CheckpointConfig:
        """
        Get configuration for a checkpoint type.
        
        Args:
            checkpoint_type: Type of checkpoint
            
        Returns:
            CheckpointConfig for the type.
        """
        return CHECKPOINTS[checkpoint_type]
    
    def initialize_checkpoints(
        self,
        workflow_id: str,
    ) -> list[CheckpointData]:
        """
        Initialize all checkpoints for a workflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            List of created checkpoints.
        """
        checkpoints = []
        
        for config in sorted(CHECKPOINTS.values(), key=lambda c: c.order):
            checkpoint = self.state_manager.add_checkpoint(
                workflow_id,
                checkpoint_id=config.id,
                checkpoint_name=config.name,
                metadata={
                    "type": config.checkpoint_type.value,
                    "required_agents": config.required_agents,
                    "order": config.order,
                },
            )
            if checkpoint:
                checkpoints.append(checkpoint)
        
        return checkpoints
    
    def mark_ready_for_review(
        self,
        workflow_id: str,
        checkpoint_type: CheckpointType,
        agent_output: dict,
    ) -> Optional[CheckpointData]:
        """
        Mark a checkpoint as ready for review.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_type: Type of checkpoint
            agent_output: Output from the agent(s)
            
        Returns:
            Updated checkpoint or None.
        """
        config = CHECKPOINTS[checkpoint_type]
        state = self.state_manager.load_state(workflow_id)
        
        if not state or config.id not in state.checkpoints:
            return None
        
        # Update checkpoint with agent output
        checkpoint = state.checkpoints[config.id]
        checkpoint.agent_output = agent_output
        checkpoint.status = CheckpointStatus.READY_FOR_REVIEW
        
        # Update workflow status
        state.status = WorkflowStatus.AWAITING_REVIEW
        state.current_checkpoint = config.id
        
        self.state_manager.save_state(state)
        
        return checkpoint
    
    def check_auto_approval(
        self,
        workflow_id: str,
        checkpoint_type: CheckpointType,
    ) -> tuple[bool, list[str]]:
        """
        Check if checkpoint can be auto-approved.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_type: Type of checkpoint
            
        Returns:
            Tuple of (can_auto_approve, reasons).
        """
        config = CHECKPOINTS[checkpoint_type]
        
        if not config.auto_approve_conditions:
            return False, ["No auto-approval conditions defined"]
        
        state = self.state_manager.load_state(workflow_id)
        if not state or config.id not in state.checkpoints:
            return False, ["Checkpoint not found"]
        
        checkpoint = state.checkpoints[config.id]
        agent_output = checkpoint.agent_output or {}
        
        reasons = []
        
        for field, condition in config.auto_approve_conditions.items():
            value = agent_output.get(field)
            
            if isinstance(condition, dict):
                if "min" in condition:
                    if value is None or value < condition["min"]:
                        reasons.append(f"{field} below minimum ({value} < {condition['min']})")
                
                if "max" in condition:
                    if value is None or value > condition["max"]:
                        reasons.append(f"{field} above maximum ({value} > {condition['max']})")
            
            elif isinstance(condition, bool):
                if value != condition:
                    reasons.append(f"{field} is {value}, expected {condition}")
        
        can_approve = len(reasons) == 0
        return can_approve, reasons
    
    def approve(
        self,
        workflow_id: str,
        checkpoint_type: CheckpointType,
        reviewer_id: str,
        comments: Optional[str] = None,
    ) -> Optional[CheckpointData]:
        """
        Approve a checkpoint.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_type: Type of checkpoint
            reviewer_id: ID of the reviewer
            comments: Optional comments
            
        Returns:
            Updated checkpoint or None.
        """
        config = CHECKPOINTS[checkpoint_type]
        
        feedback = ReviewerFeedback(
            reviewer_id=reviewer_id,
            decision="approved",
            comments=comments,
        )
        
        return self.state_manager.add_reviewer_feedback(
            workflow_id,
            config.id,
            feedback,
        )
    
    def reject(
        self,
        workflow_id: str,
        checkpoint_type: CheckpointType,
        reviewer_id: str,
        comments: str,
        specific_issues: Optional[list[str]] = None,
    ) -> Optional[CheckpointData]:
        """
        Reject a checkpoint.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_type: Type of checkpoint
            reviewer_id: ID of the reviewer
            comments: Rejection reason
            specific_issues: List of specific issues
            
        Returns:
            Updated checkpoint or None.
        """
        config = CHECKPOINTS[checkpoint_type]
        
        feedback = ReviewerFeedback(
            reviewer_id=reviewer_id,
            decision="rejected",
            comments=comments,
            specific_issues=specific_issues or [],
        )
        
        checkpoint = self.state_manager.add_reviewer_feedback(
            workflow_id,
            config.id,
            feedback,
        )
        
        # Update workflow status
        if checkpoint:
            state = self.state_manager.load_state(workflow_id)
            if state:
                state.status = WorkflowStatus.FAILED
                self.state_manager.save_state(state)
        
        return checkpoint
    
    def request_revision(
        self,
        workflow_id: str,
        checkpoint_type: CheckpointType,
        reviewer_id: str,
        comments: str,
        specific_issues: Optional[list[str]] = None,
        suggested_changes: Optional[str] = None,
    ) -> Optional[CheckpointData]:
        """
        Request revision for a checkpoint.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_type: Type of checkpoint
            reviewer_id: ID of the reviewer
            comments: Revision request comments
            specific_issues: List of specific issues
            suggested_changes: Suggested changes
            
        Returns:
            Updated checkpoint or None.
        """
        config = CHECKPOINTS[checkpoint_type]
        
        feedback = ReviewerFeedback(
            reviewer_id=reviewer_id,
            decision="revision_requested",
            comments=comments,
            specific_issues=specific_issues or [],
            suggested_changes=suggested_changes,
        )
        
        checkpoint = self.state_manager.add_reviewer_feedback(
            workflow_id,
            config.id,
            feedback,
        )
        
        # Update workflow status
        if checkpoint:
            state = self.state_manager.load_state(workflow_id)
            if state:
                state.status = WorkflowStatus.REVISION_REQUESTED
                self.state_manager.save_state(state)
        
        return checkpoint
    
    def get_next_checkpoint(
        self,
        workflow_id: str,
    ) -> Optional[CheckpointConfig]:
        """
        Get the next checkpoint to process.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Next checkpoint config or None if all complete.
        """
        state = self.state_manager.load_state(workflow_id)
        if not state:
            return None
        
        # Find first non-approved checkpoint
        for config in sorted(CHECKPOINTS.values(), key=lambda c: c.order):
            if config.id in state.checkpoints:
                checkpoint = state.checkpoints[config.id]
                if checkpoint.status != CheckpointStatus.APPROVED:
                    return config
        
        return None
    
    def are_all_checkpoints_approved(
        self,
        workflow_id: str,
    ) -> bool:
        """
        Check if all checkpoints are approved.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            True if all approved.
        """
        state = self.state_manager.load_state(workflow_id)
        if not state:
            return False
        
        for config in CHECKPOINTS.values():
            if config.id not in state.checkpoints:
                return False
            if state.checkpoints[config.id].status != CheckpointStatus.APPROVED:
                return False
        
        return True
    
    def get_revision_feedback(
        self,
        workflow_id: str,
        checkpoint_type: CheckpointType,
    ) -> Optional[ReviewerFeedback]:
        """
        Get the most recent revision feedback for a checkpoint.
        
        Args:
            workflow_id: The workflow ID
            checkpoint_type: Type of checkpoint
            
        Returns:
            Most recent revision feedback or None.
        """
        config = CHECKPOINTS[checkpoint_type]
        state = self.state_manager.load_state(workflow_id)
        
        if not state or config.id not in state.checkpoints:
            return None
        
        checkpoint = state.checkpoints[config.id]
        
        # Find most recent revision request
        for feedback in reversed(checkpoint.feedback):
            if feedback.decision == "revision_requested":
                return feedback
        
        return None
    
    def get_checkpoint_summary(
        self,
        workflow_id: str,
    ) -> list[dict]:
        """
        Get summary of all checkpoints.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            List of checkpoint summaries.
        """
        state = self.state_manager.load_state(workflow_id)
        if not state:
            return []
        
        summaries = []
        
        for config in sorted(CHECKPOINTS.values(), key=lambda c: c.order):
            checkpoint = state.checkpoints.get(config.id)
            
            summary = {
                "id": config.id,
                "name": config.name,
                "type": config.checkpoint_type.value,
                "order": config.order,
                "status": checkpoint.status.value if checkpoint else "not_initialized",
                "revision_count": checkpoint.revision_count if checkpoint else 0,
            }
            
            summaries.append(summary)
        
        return summaries


# Export
__all__ = [
    "CheckpointType",
    "CheckpointConfig",
    "CHECKPOINTS",
    "CheckpointManager",
]
