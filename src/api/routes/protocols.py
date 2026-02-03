"""
Protocol API Endpoints.

Provides CRUD operations for IACUC protocols.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from src.protocol.schema import (
    Protocol,
    ProtocolStatus,
    PersonnelInfo,
    AnimalInfo,
    USDACategory,
    create_empty_protocol,
)


router = APIRouter(prefix="/protocols", tags=["protocols"])


# ============================================================================
# STORAGE (File-based for simplicity)
# ============================================================================

class ProtocolStorage:
    """File-based protocol storage."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./protocols")
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, protocol_id: str) -> Path:
        return self.storage_path / f"{protocol_id}.json"
    
    def save(self, protocol: Protocol) -> None:
        protocol.updated_at = datetime.utcnow()
        file_path = self._get_file_path(protocol.id)
        file_path.write_text(protocol.model_dump_json(indent=2), encoding="utf-8")
    
    def load(self, protocol_id: str) -> Optional[Protocol]:
        file_path = self._get_file_path(protocol_id)
        if not file_path.exists():
            return None
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return Protocol.model_validate(data)
    
    def delete(self, protocol_id: str) -> bool:
        file_path = self._get_file_path(protocol_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def list_all(
        self,
        status: Optional[ProtocolStatus] = None,
        pi_name: Optional[str] = None,
    ) -> list[Protocol]:
        protocols = []
        for file_path in self.storage_path.glob("*.json"):
            try:
                protocol = self.load(file_path.stem)
                if protocol:
                    if status and protocol.status != status:
                        continue
                    if pi_name and pi_name.lower() not in protocol.principal_investigator.name.lower():
                        continue
                    protocols.append(protocol)
            except Exception:
                continue
        return protocols


def get_storage() -> ProtocolStorage:
    """Get protocol storage instance."""
    return ProtocolStorage()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateProtocolRequest(BaseModel):
    """Request to create a new protocol."""
    
    title: str = Field(min_length=10, max_length=300)
    pi_name: str = Field(description="Principal investigator name")
    pi_email: str = Field(description="PI email")
    department: str = Field(description="Department")


class UpdateProtocolRequest(BaseModel):
    """Request to update protocol fields."""
    
    title: Optional[str] = Field(default=None, min_length=10, max_length=300)
    lay_summary: Optional[str] = Field(default=None, min_length=50)
    scientific_objectives: Optional[str] = Field(default=None)
    scientific_rationale: Optional[str] = Field(default=None)
    replacement_statement: Optional[str] = Field(default=None)
    reduction_statement: Optional[str] = Field(default=None)
    refinement_statement: Optional[str] = Field(default=None)
    experimental_design: Optional[str] = Field(default=None)
    statistical_methods: Optional[str] = Field(default=None)
    monitoring_schedule: Optional[str] = Field(default=None)
    euthanasia_method: Optional[str] = Field(default=None)


class AddAnimalRequest(BaseModel):
    """Request to add animal info."""
    
    species: str
    strain: Optional[str] = None
    sex: str
    total_number: int = Field(ge=1)
    source: str
    genetic_modification: Optional[str] = None


class ProtocolSummaryResponse(BaseModel):
    """Summary response for protocol list."""
    
    id: str
    protocol_number: Optional[str]
    title: str
    status: str
    pi_name: str
    species: list[str]
    total_animals: int
    usda_category: str
    completeness: float
    created_at: str
    updated_at: str


class ProtocolListResponse(BaseModel):
    """Response for protocol list."""
    
    protocols: list[ProtocolSummaryResponse]
    total: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("", response_model=dict)
async def create_protocol(
    request: CreateProtocolRequest,
    storage: ProtocolStorage = Depends(get_storage),
) -> dict:
    """
    Create a new protocol.
    
    Creates an empty protocol with minimal required information.
    """
    protocol = create_empty_protocol(
        title=request.title,
        pi_name=request.pi_name,
        pi_email=request.pi_email,
        department=request.department,
    )
    
    storage.save(protocol)
    
    return {
        "id": protocol.id,
        "message": "Protocol created successfully",
        "completeness": protocol.calculate_completeness(),
    }


@router.get("", response_model=ProtocolListResponse)
async def list_protocols(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    pi_name: Optional[str] = Query(default=None, description="Filter by PI name"),
    storage: ProtocolStorage = Depends(get_storage),
) -> ProtocolListResponse:
    """
    List all protocols with optional filtering.
    """
    # Parse status if provided
    protocol_status = None
    if status:
        try:
            protocol_status = ProtocolStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}",
            )
    
    protocols = storage.list_all(status=protocol_status, pi_name=pi_name)
    
    summaries = [
        ProtocolSummaryResponse(
            id=p.id,
            protocol_number=p.protocol_number,
            title=p.title,
            status=p.status.value,
            pi_name=p.principal_investigator.name,
            species=[a.species for a in p.animals],
            total_animals=p.total_animals,
            usda_category=p.usda_category.value,
            completeness=p.calculate_completeness(),
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in protocols
    ]
    
    return ProtocolListResponse(
        protocols=summaries,
        total=len(summaries),
    )


@router.get("/{protocol_id}")
async def get_protocol(
    protocol_id: str,
    storage: ProtocolStorage = Depends(get_storage),
) -> dict:
    """
    Get a specific protocol by ID.
    """
    protocol = storage.load(protocol_id)
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return protocol.model_dump()


@router.get("/{protocol_id}/summary")
async def get_protocol_summary(
    protocol_id: str,
    storage: ProtocolStorage = Depends(get_storage),
) -> ProtocolSummaryResponse:
    """
    Get protocol summary.
    """
    protocol = storage.load(protocol_id)
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return ProtocolSummaryResponse(
        id=protocol.id,
        protocol_number=protocol.protocol_number,
        title=protocol.title,
        status=protocol.status.value,
        pi_name=protocol.principal_investigator.name,
        species=[a.species for a in protocol.animals],
        total_animals=protocol.total_animals,
        usda_category=protocol.usda_category.value,
        completeness=protocol.calculate_completeness(),
        created_at=protocol.created_at.isoformat(),
        updated_at=protocol.updated_at.isoformat(),
    )


@router.put("/{protocol_id}")
async def update_protocol(
    protocol_id: str,
    request: UpdateProtocolRequest,
    storage: ProtocolStorage = Depends(get_storage),
) -> dict:
    """
    Update protocol fields.
    """
    protocol = storage.load(protocol_id)
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            setattr(protocol, field, value)
    
    storage.save(protocol)
    
    return {
        "id": protocol.id,
        "message": "Protocol updated successfully",
        "completeness": protocol.calculate_completeness(),
    }


@router.delete("/{protocol_id}")
async def delete_protocol(
    protocol_id: str,
    storage: ProtocolStorage = Depends(get_storage),
) -> dict:
    """
    Delete a protocol.
    """
    if not storage.delete(protocol_id):
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return {"message": "Protocol deleted successfully"}


@router.post("/{protocol_id}/animals")
async def add_animal(
    protocol_id: str,
    request: AddAnimalRequest,
    storage: ProtocolStorage = Depends(get_storage),
) -> dict:
    """
    Add animal information to a protocol.
    """
    protocol = storage.load(protocol_id)
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    animal = AnimalInfo(
        species=request.species,
        strain=request.strain,
        sex=request.sex,
        total_number=request.total_number,
        source=request.source,
        genetic_modification=request.genetic_modification,
    )
    
    # Replace TBD placeholder or add new
    if protocol.animals and protocol.animals[0].species == "TBD":
        protocol.animals = [animal]
    else:
        protocol.animals.append(animal)
    
    # Update total animals
    protocol.total_animals = sum(a.total_number for a in protocol.animals)
    
    storage.save(protocol)
    
    return {
        "message": "Animal information added",
        "total_animals": protocol.total_animals,
    }


@router.put("/{protocol_id}/status")
async def update_status(
    protocol_id: str,
    status: str,
    storage: ProtocolStorage = Depends(get_storage),
) -> dict:
    """
    Update protocol status.
    """
    protocol = storage.load(protocol_id)
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    try:
        new_status = ProtocolStatus(status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {status}",
        )
    
    protocol.status = new_status
    
    # Set timestamps based on status
    if new_status == ProtocolStatus.SUBMITTED:
        protocol.submitted_at = datetime.utcnow()
    elif new_status == ProtocolStatus.APPROVED:
        protocol.approved_at = datetime.utcnow()
    
    storage.save(protocol)
    
    return {
        "id": protocol.id,
        "status": protocol.status.value,
        "message": f"Status updated to {status}",
    }


@router.get("/{protocol_id}/missing-sections")
async def get_missing_sections(
    protocol_id: str,
    storage: ProtocolStorage = Depends(get_storage),
) -> dict:
    """
    Get list of missing/incomplete sections.
    """
    protocol = storage.load(protocol_id)
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    missing = protocol.get_missing_sections()
    
    return {
        "protocol_id": protocol_id,
        "missing_sections": missing,
        "completeness": protocol.calculate_completeness(),
        "is_complete": len(missing) == 0,
    }


# Export
__all__ = ["router"]
