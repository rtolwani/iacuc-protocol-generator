"""
Review API Endpoints.

Provides REST API for human-in-the-loop review operations.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.review.state_manager import (
    StateManager,
    WorkflowState,
    CheckpointData,
    CheckpointStatus,
    WorkflowStatus,
)
from src.review.checkpoints import (
    CheckpointType,
    CheckpointManager,
    CHECKPOINTS,
)


router = APIRouter(prefix="/review", tags=["review"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_state_manager() -> StateManager:
    """Get state manager instance."""
    return StateManager()


def get_checkpoint_manager(
    state_manager: StateManager = Depends(get_state_manager),
) -> CheckpointManager:
    """Get checkpoint manager instance."""
    return CheckpointManager(state_manager)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ApprovalRequest(BaseModel):
    """Request to approve a checkpoint."""
    
    reviewer_id: str = Field(description="ID of the reviewer")
    comments: Optional[str] = Field(default=None, description="Optional comments")


class RejectionRequest(BaseModel):
    """Request to reject a checkpoint."""
    
    reviewer_id: str = Field(description="ID of the reviewer")
    comments: str = Field(description="Rejection reason")
    specific_issues: list[str] = Field(
        default_factory=list,
        description="List of specific issues",
    )


class RevisionRequest(BaseModel):
    """Request to request revision."""
    
    reviewer_id: str = Field(description="ID of the reviewer")
    comments: str = Field(description="Revision request comments")
    specific_issues: list[str] = Field(
        default_factory=list,
        description="List of specific issues",
    )
    suggested_changes: Optional[str] = Field(
        default=None,
        description="Suggested changes",
    )


class CheckpointStatusResponse(BaseModel):
    """Response for checkpoint status."""
    
    checkpoint_id: str
    checkpoint_name: str
    status: str
    agent_output: Optional[dict] = None
    review_instructions: str
    revision_count: int = 0
    feedback: list[dict] = Field(default_factory=list)


class WorkflowStatusResponse(BaseModel):
    """Response for workflow status."""
    
    workflow_id: str
    status: str
    current_checkpoint: Optional[str] = None
    checkpoints: list[dict] = Field(default_factory=list)
    progress: float = 0.0


class PendingReviewResponse(BaseModel):
    """Response for pending reviews list."""
    
    workflow_id: str
    checkpoint_id: str
    checkpoint_name: str
    created_at: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/workflows", response_model=list[WorkflowStatusResponse])
async def list_workflows(
    status: Optional[str] = None,
    state_manager: StateManager = Depends(get_state_manager),
) -> list[WorkflowStatusResponse]:
    """
    List all workflows.
    
    Args:
        status: Optional status filter
    """
    workflow_status = None
    if status:
        try:
            workflow_status = WorkflowStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}",
            )
    
    workflows = state_manager.list_workflows(status=workflow_status)
    
    return [
        WorkflowStatusResponse(
            workflow_id=w.id,
            status=w.status.value,
            current_checkpoint=w.current_checkpoint,
            checkpoints=[
                {
                    "id": cp.id,
                    "name": cp.name,
                    "status": cp.status.value,
                }
                for cp in w.checkpoints.values()
            ],
            progress=_calculate_progress(w),
        )
        for w in workflows
    ]


@router.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow(
    workflow_id: str,
    state_manager: StateManager = Depends(get_state_manager),
) -> WorkflowStatusResponse:
    """
    Get workflow status.
    
    Args:
        workflow_id: The workflow ID
    """
    state = state_manager.load_state(workflow_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return WorkflowStatusResponse(
        workflow_id=state.id,
        status=state.status.value,
        current_checkpoint=state.current_checkpoint,
        checkpoints=[
            {
                "id": cp.id,
                "name": cp.name,
                "status": cp.status.value,
            }
            for cp in state.checkpoints.values()
        ],
        progress=_calculate_progress(state),
    )


@router.get("/workflows/{workflow_id}/checkpoints")
async def list_checkpoints(
    workflow_id: str,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager),
) -> list[dict]:
    """
    Get all checkpoints for a workflow.
    
    Args:
        workflow_id: The workflow ID
    """
    summary = checkpoint_manager.get_checkpoint_summary(workflow_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return summary


@router.get(
    "/workflows/{workflow_id}/checkpoints/{checkpoint_type}",
    response_model=CheckpointStatusResponse,
)
async def get_checkpoint_status(
    workflow_id: str,
    checkpoint_type: str,
    state_manager: StateManager = Depends(get_state_manager),
) -> CheckpointStatusResponse:
    """
    Get status of a specific checkpoint.
    
    Args:
        workflow_id: The workflow ID
        checkpoint_type: Type of checkpoint
    """
    # Validate checkpoint type
    try:
        cp_type = CheckpointType(checkpoint_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid checkpoint type: {checkpoint_type}",
        )
    
    state = state_manager.load_state(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    config = CHECKPOINTS[cp_type]
    
    if config.id not in state.checkpoints:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    
    checkpoint = state.checkpoints[config.id]
    
    return CheckpointStatusResponse(
        checkpoint_id=checkpoint.id,
        checkpoint_name=checkpoint.name,
        status=checkpoint.status.value,
        agent_output=checkpoint.agent_output,
        review_instructions=config.review_instructions,
        revision_count=checkpoint.revision_count,
        feedback=[
            {
                "reviewer_id": fb.reviewer_id,
                "decision": fb.decision,
                "comments": fb.comments,
                "timestamp": fb.timestamp.isoformat(),
            }
            for fb in checkpoint.feedback
        ],
    )


@router.post("/workflows/{workflow_id}/checkpoints/{checkpoint_type}/approve")
async def approve_checkpoint(
    workflow_id: str,
    checkpoint_type: str,
    request: ApprovalRequest,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager),
) -> dict:
    """
    Approve a checkpoint.
    
    Args:
        workflow_id: The workflow ID
        checkpoint_type: Type of checkpoint
        request: Approval request details
    """
    try:
        cp_type = CheckpointType(checkpoint_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid checkpoint type: {checkpoint_type}",
        )
    
    result = checkpoint_manager.approve(
        workflow_id,
        cp_type,
        reviewer_id=request.reviewer_id,
        comments=request.comments,
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Workflow or checkpoint not found",
        )
    
    return {
        "status": "approved",
        "checkpoint_id": result.id,
        "message": "Checkpoint approved successfully",
    }


@router.post("/workflows/{workflow_id}/checkpoints/{checkpoint_type}/reject")
async def reject_checkpoint(
    workflow_id: str,
    checkpoint_type: str,
    request: RejectionRequest,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager),
) -> dict:
    """
    Reject a checkpoint.
    
    Args:
        workflow_id: The workflow ID
        checkpoint_type: Type of checkpoint
        request: Rejection request details
    """
    try:
        cp_type = CheckpointType(checkpoint_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid checkpoint type: {checkpoint_type}",
        )
    
    result = checkpoint_manager.reject(
        workflow_id,
        cp_type,
        reviewer_id=request.reviewer_id,
        comments=request.comments,
        specific_issues=request.specific_issues,
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Workflow or checkpoint not found",
        )
    
    return {
        "status": "rejected",
        "checkpoint_id": result.id,
        "message": "Checkpoint rejected",
    }


@router.post("/workflows/{workflow_id}/checkpoints/{checkpoint_type}/revision")
async def request_revision(
    workflow_id: str,
    checkpoint_type: str,
    request: RevisionRequest,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager),
) -> dict:
    """
    Request revision for a checkpoint.
    
    Args:
        workflow_id: The workflow ID
        checkpoint_type: Type of checkpoint
        request: Revision request details
    """
    try:
        cp_type = CheckpointType(checkpoint_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid checkpoint type: {checkpoint_type}",
        )
    
    result = checkpoint_manager.request_revision(
        workflow_id,
        cp_type,
        reviewer_id=request.reviewer_id,
        comments=request.comments,
        specific_issues=request.specific_issues,
        suggested_changes=request.suggested_changes,
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Workflow or checkpoint not found",
        )
    
    return {
        "status": "revision_requested",
        "checkpoint_id": result.id,
        "revision_count": result.revision_count,
        "message": "Revision requested",
    }


@router.get("/pending", response_model=list[PendingReviewResponse])
async def list_pending_reviews(
    state_manager: StateManager = Depends(get_state_manager),
) -> list[PendingReviewResponse]:
    """
    Get all checkpoints awaiting review.
    """
    pending = state_manager.get_pending_reviews()
    
    return [
        PendingReviewResponse(
            workflow_id=workflow.id,
            checkpoint_id=checkpoint.id,
            checkpoint_name=checkpoint.name,
            created_at=checkpoint.created_at.isoformat(),
        )
        for workflow, checkpoint in pending
    ]


@router.get("/checkpoint-types")
async def list_checkpoint_types() -> list[dict]:
    """
    Get all available checkpoint types and their configurations.
    """
    return [
        {
            "id": config.id,
            "name": config.name,
            "type": config.checkpoint_type.value,
            "description": config.description,
            "required_agents": config.required_agents,
            "order": config.order,
        }
        for config in sorted(CHECKPOINTS.values(), key=lambda c: c.order)
    ]


# ============================================================================
# AI CREW EXECUTION
# ============================================================================

class RunCrewRequest(BaseModel):
    """Request to run AI crew on a protocol."""
    verbose: bool = Field(default=False, description="Show detailed agent output")


class RunCrewResponse(BaseModel):
    """Response from AI crew execution."""
    success: bool
    protocol_id: str
    agent_outputs: dict
    errors: list[str] = Field(default_factory=list)
    message: str


@router.post("/protocols/{protocol_id}/run-crew")
async def run_ai_crew(
    protocol_id: str,
    request: RunCrewRequest = RunCrewRequest(),
) -> RunCrewResponse:
    """
    Run the full CrewAI agents on a submitted protocol.
    
    This triggers all 8 agents to review and enhance the protocol:
    1. Intake Specialist - Extracts parameters
    2. Regulatory Scout - Identifies regulations  
    3. Lay Summary Writer - Creates lay summary
    4. Alternatives Researcher - Documents 3Rs
    5. Statistical Consultant - Reviews statistics
    6. Veterinary Reviewer - Reviews welfare
    7. Procedure Writer - Writes procedures
    8. Protocol Assembler - Compiles document
    """
    from src.api.routes.protocols import ProtocolStorage
    from src.agents.crew import generate_protocol, ProtocolInput
    
    # Load protocol
    storage = ProtocolStorage()
    protocol = storage.load(protocol_id)
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check status
    if protocol.status.value not in ["submitted", "under_review"]:
        raise HTTPException(
            status_code=400,
            detail=f"Protocol must be submitted for review. Current status: {protocol.status.value}"
        )
    
    # Update status to under_review
    from src.protocol.schema import ProtocolStatus
    protocol.status = ProtocolStatus.UNDER_REVIEW
    storage.save(protocol)
    
    try:
        # Build crew input from protocol
        animals = protocol.animals
        species = animals[0].species if animals else "Unknown"
        strain = animals[0].strain if animals and animals[0].strain else None
        total_animals = sum(a.total_number for a in animals) if animals else 0
        
        crew_input = ProtocolInput(
            title=protocol.title,
            pi_name=protocol.principal_investigator.name,
            species=species,
            strain=strain,
            total_animals=total_animals,
            research_description=protocol.scientific_objectives or protocol.lay_summary,
            procedures=protocol.experimental_design or "To be determined",
            study_duration=protocol.study_duration,
            primary_endpoint=None,
        )
        
        # Run the crew
        result = generate_protocol(crew_input, verbose=request.verbose)
        
        if result.success:
            # Update protocol with AI outputs (optional - store for review)
            return RunCrewResponse(
                success=True,
                protocol_id=protocol_id,
                agent_outputs=result.agent_outputs,
                errors=[],
                message="AI review completed successfully. Protocol is ready for human review."
            )
        else:
            return RunCrewResponse(
                success=False,
                protocol_id=protocol_id,
                agent_outputs={},
                errors=result.errors,
                message="AI review failed. See errors for details."
            )
            
    except Exception as e:
        return RunCrewResponse(
            success=False,
            protocol_id=protocol_id,
            agent_outputs={},
            errors=[str(e)],
            message=f"Error running AI crew: {str(e)}"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _calculate_progress(state: WorkflowState) -> float:
    """Calculate workflow progress as percentage."""
    if not state.checkpoints:
        return 0.0
    
    total = len(CHECKPOINTS)
    approved = sum(
        1 for cp in state.checkpoints.values()
        if cp.status == CheckpointStatus.APPROVED
    )
    
    return approved / total


# Export
__all__ = ["router"]
