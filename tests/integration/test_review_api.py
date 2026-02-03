"""
Integration tests for Review API Endpoints.
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.review.state_manager import StateManager
from src.review.checkpoints import CheckpointManager, CheckpointType


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
def app():
    """Create test app."""
    return create_app()


@pytest.fixture
def client(app, temp_storage):
    """Create test client with overridden dependencies."""
    from src.api.routes.review import get_state_manager
    
    def override_state_manager():
        return StateManager(storage_path=temp_storage)
    
    app.dependency_overrides[get_state_manager] = override_state_manager
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def workflow_with_checkpoints(temp_storage):
    """Create a workflow with initialized checkpoints."""
    manager = StateManager(storage_path=temp_storage)
    checkpoint_mgr = CheckpointManager(manager)
    
    workflow = manager.create_workflow(
        input_data={"species": "mouse"},
    )
    checkpoint_mgr.initialize_checkpoints(workflow.id)
    
    return workflow, manager, checkpoint_mgr


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns healthy."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestCheckpointTypesEndpoint:
    """Tests for checkpoint types endpoint."""
    
    def test_list_checkpoint_types(self, client):
        """Test listing checkpoint types."""
        response = client.get("/api/v1/review/checkpoint-types")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_checkpoint_types_have_fields(self, client):
        """Test checkpoint types have required fields."""
        response = client.get("/api/v1/review/checkpoint-types")
        
        data = response.json()
        for item in data:
            assert "id" in item
            assert "name" in item
            assert "type" in item
            assert "required_agents" in item


class TestWorkflowEndpoints:
    """Tests for workflow endpoints."""
    
    def test_list_workflows_empty(self, client):
        """Test listing workflows when empty."""
        response = client.get("/api/v1/review/workflows")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_workflows_with_data(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test listing workflows with data."""
        # Create workflow in the same storage the client uses
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        response = client.get("/api/v1/review/workflows")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["workflow_id"] == workflow.id
    
    def test_get_workflow_not_found(self, client):
        """Test getting nonexistent workflow."""
        response = client.get("/api/v1/review/workflows/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_get_workflow(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test getting a workflow."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        response = client.get(f"/api/v1/review/workflows/{workflow.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == workflow.id


class TestCheckpointEndpoints:
    """Tests for checkpoint endpoints."""
    
    def test_list_checkpoints(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test listing checkpoints for a workflow."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        response = client.get(
            f"/api/v1/review/workflows/{workflow.id}/checkpoints"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_get_checkpoint_status(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test getting checkpoint status."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        response = client.get(
            f"/api/v1/review/workflows/{workflow.id}/checkpoints/intake_review"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["checkpoint_id"] == "intake_review"
    
    def test_get_invalid_checkpoint_type(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test getting invalid checkpoint type."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        response = client.get(
            f"/api/v1/review/workflows/{workflow.id}/checkpoints/invalid_type"
        )
        
        assert response.status_code == 400


class TestApprovalEndpoint:
    """Tests for approval endpoint."""
    
    def test_approve_checkpoint(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test approving a checkpoint."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        # Mark ready for review first
        cp_mgr.mark_ready_for_review(
            workflow.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        response = client.post(
            f"/api/v1/review/workflows/{workflow.id}/checkpoints/intake_review/approve",
            json={
                "reviewer_id": "reviewer_1",
                "comments": "Looks good",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
    
    def test_approve_nonexistent_workflow(self, client):
        """Test approving nonexistent workflow."""
        response = client.post(
            "/api/v1/review/workflows/nonexistent/checkpoints/intake_review/approve",
            json={
                "reviewer_id": "reviewer_1",
            },
        )
        
        assert response.status_code == 404


class TestRejectionEndpoint:
    """Tests for rejection endpoint."""
    
    def test_reject_checkpoint(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test rejecting a checkpoint."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        # Mark ready for review first
        cp_mgr.mark_ready_for_review(
            workflow.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        response = client.post(
            f"/api/v1/review/workflows/{workflow.id}/checkpoints/intake_review/reject",
            json={
                "reviewer_id": "reviewer_1",
                "comments": "Critical issues found",
                "specific_issues": ["Missing data", "Invalid format"],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"


class TestRevisionEndpoint:
    """Tests for revision endpoint."""
    
    def test_request_revision(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test requesting revision."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        # Mark ready for review first
        cp_mgr.mark_ready_for_review(
            workflow.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        response = client.post(
            f"/api/v1/review/workflows/{workflow.id}/checkpoints/intake_review/revision",
            json={
                "reviewer_id": "reviewer_1",
                "comments": "Please make changes",
                "specific_issues": ["Needs clarification"],
                "suggested_changes": "Add more detail to procedures",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "revision_requested"
        assert data["revision_count"] == 1


class TestPendingReviewsEndpoint:
    """Tests for pending reviews endpoint."""
    
    def test_list_pending_empty(self, client):
        """Test listing pending reviews when empty."""
        response = client.get("/api/v1/review/pending")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_pending_with_data(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test listing pending reviews."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        # Mark as ready for review
        cp_mgr.mark_ready_for_review(
            workflow.id,
            CheckpointType.INTAKE_REVIEW,
            {},
        )
        
        response = client.get("/api/v1/review/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["checkpoint_id"] == "intake_review"


class TestRequestValidation:
    """Tests for request validation."""
    
    def test_approval_missing_reviewer(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test approval fails without reviewer_id."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        response = client.post(
            f"/api/v1/review/workflows/{workflow.id}/checkpoints/intake_review/approve",
            json={},  # Missing reviewer_id
        )
        
        assert response.status_code == 422
    
    def test_rejection_missing_comments(
        self,
        client,
        workflow_with_checkpoints,
        temp_storage,
    ):
        """Test rejection fails without comments."""
        from src.api.routes.review import get_state_manager
        
        def override():
            return StateManager(storage_path=temp_storage)
        
        client.app.dependency_overrides[get_state_manager] = override
        
        workflow, manager, cp_mgr = workflow_with_checkpoints
        
        response = client.post(
            f"/api/v1/review/workflows/{workflow.id}/checkpoints/intake_review/reject",
            json={
                "reviewer_id": "reviewer_1",
                # Missing required comments
            },
        )
        
        assert response.status_code == 422
