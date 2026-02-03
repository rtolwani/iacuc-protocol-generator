"""
Integration tests for Protocol API Endpoints.
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.routes.protocols import ProtocolStorage, get_storage


@pytest.fixture
def temp_storage():
    """Create temporary storage for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def app():
    """Create test app."""
    return create_app()


@pytest.fixture
def client(app, temp_storage):
    """Create test client with overridden dependencies."""
    def override_storage():
        return ProtocolStorage(storage_path=temp_storage)
    
    app.dependency_overrides[get_storage] = override_storage
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


class TestCreateProtocol:
    """Tests for protocol creation."""
    
    def test_create_protocol(self, client):
        """Test creating a new protocol."""
        response = client.post(
            "/api/v1/protocols",
            json={
                "title": "Effects of Novel Compound on Disease Model",
                "pi_name": "Dr. Jane Smith",
                "pi_email": "jsmith@university.edu",
                "department": "Neuroscience",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "Protocol created successfully"
    
    def test_create_protocol_title_too_short(self, client):
        """Test that short titles are rejected."""
        response = client.post(
            "/api/v1/protocols",
            json={
                "title": "Short",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        
        assert response.status_code == 422


class TestListProtocols:
    """Tests for protocol listing."""
    
    def test_list_empty(self, client):
        """Test listing when no protocols exist."""
        response = client.get("/api/v1/protocols")
        
        assert response.status_code == 200
        data = response.json()
        assert data["protocols"] == []
        assert data["total"] == 0
    
    def test_list_with_protocols(self, client):
        """Test listing with existing protocols."""
        # Create a protocol
        client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Listing Test",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        
        response = client.get("/api/v1/protocols")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["protocols"]) == 1
        assert data["total"] == 1
    
    def test_list_filter_by_status(self, client):
        """Test filtering by status."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Status Filter",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        
        # Filter by draft (default status)
        response = client.get("/api/v1/protocols?status=draft")
        
        assert response.status_code == 200
        assert response.json()["total"] == 1
        
        # Filter by submitted (should be empty)
        response = client.get("/api/v1/protocols?status=submitted")
        
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestGetProtocol:
    """Tests for getting a protocol."""
    
    def test_get_protocol(self, client):
        """Test getting a specific protocol."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Get Test",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        protocol_id = create_resp.json()["id"]
        
        response = client.get(f"/api/v1/protocols/{protocol_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == protocol_id
        assert data["title"] == "Test Protocol for Get Test"
    
    def test_get_protocol_not_found(self, client):
        """Test getting nonexistent protocol."""
        response = client.get("/api/v1/protocols/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_get_protocol_summary(self, client):
        """Test getting protocol summary."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Summary Test",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        protocol_id = create_resp.json()["id"]
        
        response = client.get(f"/api/v1/protocols/{protocol_id}/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "completeness" in data
        assert "pi_name" in data


class TestUpdateProtocol:
    """Tests for updating a protocol."""
    
    def test_update_protocol(self, client):
        """Test updating protocol fields."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Update Test",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        protocol_id = create_resp.json()["id"]
        
        # Update
        response = client.put(
            f"/api/v1/protocols/{protocol_id}",
            json={
                "scientific_objectives": "Study the effects of X on Y",
                "euthanasia_method": "CO2 followed by cervical dislocation",
            },
        )
        
        assert response.status_code == 200
        
        # Verify update
        get_resp = client.get(f"/api/v1/protocols/{protocol_id}")
        assert get_resp.json()["scientific_objectives"] == "Study the effects of X on Y"
    
    def test_update_nonexistent(self, client):
        """Test updating nonexistent protocol."""
        response = client.put(
            "/api/v1/protocols/nonexistent-id",
            json={"scientific_objectives": "Test"},
        )
        
        assert response.status_code == 404


class TestDeleteProtocol:
    """Tests for deleting a protocol."""
    
    def test_delete_protocol(self, client):
        """Test deleting a protocol."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Delete Test",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        protocol_id = create_resp.json()["id"]
        
        # Delete
        response = client.delete(f"/api/v1/protocols/{protocol_id}")
        
        assert response.status_code == 200
        
        # Verify deleted
        get_resp = client.get(f"/api/v1/protocols/{protocol_id}")
        assert get_resp.status_code == 404
    
    def test_delete_nonexistent(self, client):
        """Test deleting nonexistent protocol."""
        response = client.delete("/api/v1/protocols/nonexistent-id")
        
        assert response.status_code == 404


class TestAddAnimal:
    """Tests for adding animal information."""
    
    def test_add_animal(self, client):
        """Test adding animal info."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Animal Test",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        protocol_id = create_resp.json()["id"]
        
        # Add animal
        response = client.post(
            f"/api/v1/protocols/{protocol_id}/animals",
            json={
                "species": "Mouse",
                "strain": "C57BL/6J",
                "sex": "both",
                "total_number": 60,
                "source": "Jackson Laboratory",
            },
        )
        
        assert response.status_code == 200
        assert response.json()["total_animals"] == 60
    
    def test_add_multiple_animals(self, client):
        """Test adding multiple animal groups."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Multiple Animals",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        protocol_id = create_resp.json()["id"]
        
        # Add first animal group
        client.post(
            f"/api/v1/protocols/{protocol_id}/animals",
            json={
                "species": "Mouse",
                "sex": "male",
                "total_number": 30,
                "source": "vendor",
            },
        )
        
        # Add second animal group
        response = client.post(
            f"/api/v1/protocols/{protocol_id}/animals",
            json={
                "species": "Rat",
                "sex": "female",
                "total_number": 20,
                "source": "vendor",
            },
        )
        
        assert response.status_code == 200
        assert response.json()["total_animals"] == 50


class TestUpdateStatus:
    """Tests for status updates."""
    
    def test_update_status(self, client):
        """Test updating protocol status."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Status Update",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        protocol_id = create_resp.json()["id"]
        
        # Update status
        response = client.put(
            f"/api/v1/protocols/{protocol_id}/status?status=submitted"
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "submitted"
    
    def test_invalid_status(self, client):
        """Test invalid status value."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Invalid Status",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        protocol_id = create_resp.json()["id"]
        
        response = client.put(
            f"/api/v1/protocols/{protocol_id}/status?status=invalid"
        )
        
        assert response.status_code == 400


class TestMissingSections:
    """Tests for missing sections endpoint."""
    
    def test_get_missing_sections(self, client):
        """Test getting missing sections."""
        # Create a protocol
        create_resp = client.post(
            "/api/v1/protocols",
            json={
                "title": "Test Protocol for Missing Sections",
                "pi_name": "Dr. Test",
                "pi_email": "test@test.edu",
                "department": "Test",
            },
        )
        protocol_id = create_resp.json()["id"]
        
        response = client.get(f"/api/v1/protocols/{protocol_id}/missing-sections")
        
        assert response.status_code == 200
        data = response.json()
        assert "missing_sections" in data
        assert "completeness" in data
        assert "is_complete" in data
