"""
Protocol Data Models.

Pydantic models for complete IACUC protocol structure with all 13 sections.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ProtocolStatus(str, Enum):
    """Status of a protocol."""
    
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class USDACategory(str, Enum):
    """USDA pain categories."""
    
    B = "B"  # Breeding, conditioning, holding
    C = "C"  # No pain or minimal pain
    D = "D"  # Pain relieved by anesthesia/analgesia
    E = "E"  # Pain NOT relieved


# ============================================================================
# NESTED MODELS
# ============================================================================

class PersonnelInfo(BaseModel):
    """Information about a person on the protocol."""
    
    name: str = Field(description="Full name")
    role: str = Field(description="Role (PI, Co-PI, Student, Technician, etc.)")
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    department: Optional[str] = Field(default=None)
    qualifications: list[str] = Field(default_factory=list, description="Relevant training/certifications")
    responsibilities: list[str] = Field(default_factory=list, description="Specific responsibilities")


class AnimalInfo(BaseModel):
    """Information about animals used."""
    
    species: str = Field(description="Species common name")
    scientific_name: Optional[str] = Field(default=None)
    strain: Optional[str] = Field(default=None, description="Strain, stock, or breed")
    sex: str = Field(description="male, female, or both")
    age_range: Optional[str] = Field(default=None, description="Age range at study start")
    weight_range: Optional[str] = Field(default=None, description="Weight range")
    total_number: int = Field(description="Total animals requested", ge=1)
    number_per_group: Optional[int] = Field(default=None, ge=1)
    number_of_groups: Optional[int] = Field(default=None, ge=1)
    source: str = Field(description="Commercial vendor, breeding colony, etc.")
    vendor_name: Optional[str] = Field(default=None)
    genetic_modification: Optional[str] = Field(default=None)
    housing_requirements: Optional[str] = Field(default=None)


class DrugInfo(BaseModel):
    """Information about a drug used in the protocol."""
    
    drug_name: str = Field(description="Drug name")
    dose: str = Field(description="Dose with units")
    route: str = Field(description="Route of administration")
    frequency: Optional[str] = Field(default=None)
    duration: Optional[str] = Field(default=None)
    purpose: str = Field(description="Anesthesia, analgesia, treatment, etc.")
    dea_schedule: Optional[str] = Field(default=None)


class ProcedureInfo(BaseModel):
    """Information about a procedure."""
    
    name: str = Field(description="Procedure name")
    description: str = Field(description="Detailed description")
    frequency: Optional[str] = Field(default=None)
    duration: Optional[str] = Field(default=None)
    anesthesia_required: bool = Field(default=False)
    anesthesia_protocol: Optional[str] = Field(default=None)
    analgesia_required: bool = Field(default=False)
    analgesia_protocol: Optional[str] = Field(default=None)
    recovery_expected: bool = Field(default=True)
    special_considerations: Optional[str] = Field(default=None)


class HumaneEndpoint(BaseModel):
    """Humane endpoint criteria."""
    
    criterion: str = Field(description="Endpoint criterion")
    measurement: str = Field(description="How it will be assessed")
    threshold: str = Field(description="Threshold for intervention")
    action: str = Field(description="Action taken when threshold met")


class LiteratureSearch(BaseModel):
    """Literature search documentation for alternatives."""
    
    databases_searched: list[str] = Field(description="Databases used")
    search_date: date = Field(description="Date of search")
    search_terms: list[str] = Field(description="Search terms used")
    years_covered: str = Field(description="Year range covered")
    results_summary: str = Field(description="Summary of findings")


class ProtocolSection(BaseModel):
    """Generic protocol section."""
    
    title: str = Field(description="Section title")
    content: str = Field(description="Section content")
    is_complete: bool = Field(default=False)
    last_updated: Optional[datetime] = Field(default=None)


# ============================================================================
# MAIN PROTOCOL MODEL - ALL 13 SECTIONS
# ============================================================================

class Protocol(BaseModel):
    """
    Complete IACUC Protocol with all 13 required sections.
    
    Sections:
    1. General Information
    2. Lay Summary
    3. Personnel
    4. Species and Animal Numbers
    5. Rationale and Scientific Justification
    6. Alternatives (3Rs)
    7. Experimental Design
    8. Procedures
    9. Anesthesia and Analgesia
    10. Surgical Procedures
    11. Humane Endpoints
    12. Euthanasia
    13. Hazardous Materials
    """
    
    # Metadata
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    protocol_number: Optional[str] = Field(default=None, description="Assigned protocol number")
    version: int = Field(default=1)
    status: ProtocolStatus = Field(default=ProtocolStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    expiration_date: Optional[date] = Field(default=None)
    
    # Section 1: General Information
    title: str = Field(description="Protocol title", min_length=10, max_length=300)
    principal_investigator: PersonnelInfo = Field(description="PI information")
    department: str = Field(description="Department/Division")
    funding_sources: list[str] = Field(default_factory=list)
    funding_agency_numbers: list[str] = Field(default_factory=list)
    study_duration: str = Field(description="Expected study duration")
    
    # Section 2: Lay Summary
    lay_summary: str = Field(
        description="Non-technical summary understandable by non-scientists",
        min_length=100,
    )
    
    # Section 3: Personnel
    personnel: list[PersonnelInfo] = Field(
        default_factory=list,
        description="All personnel on the protocol",
    )
    
    # Section 4: Species and Animal Numbers
    animals: list[AnimalInfo] = Field(description="Animal information")
    usda_category: USDACategory = Field(description="USDA pain category")
    total_animals: int = Field(description="Total animals across all species", ge=1)
    animal_number_justification: str = Field(
        description="Statistical/scientific justification for animal numbers",
    )
    
    # Section 5: Rationale and Scientific Justification
    scientific_objectives: str = Field(description="Research objectives")
    scientific_rationale: str = Field(
        description="Why animal use is necessary",
    )
    potential_benefits: str = Field(
        description="Expected scientific/medical benefits",
    )
    
    # Section 6: Alternatives (3Rs)
    replacement_statement: str = Field(
        description="Why animal use cannot be replaced",
    )
    reduction_statement: str = Field(
        description="How animal numbers are minimized",
    )
    refinement_statement: str = Field(
        description="How procedures minimize pain/distress",
    )
    literature_search: Optional[LiteratureSearch] = Field(
        default=None,
        description="Documentation of alternatives search",
    )
    
    # Section 7: Experimental Design
    experimental_design: str = Field(
        description="Description of experimental groups and design",
    )
    statistical_methods: str = Field(
        description="Statistical analysis plan",
    )
    power_analysis: Optional[str] = Field(
        default=None,
        description="Power analysis results",
    )
    group_assignments: list[dict] = Field(
        default_factory=list,
        description="Group assignments table",
    )
    
    # Section 8: Procedures
    procedures: list[ProcedureInfo] = Field(
        description="All procedures to be performed",
    )
    procedure_timeline: Optional[str] = Field(
        default=None,
        description="Timeline of procedures",
    )
    
    # Section 9: Anesthesia and Analgesia
    anesthesia_protocols: list[DrugInfo] = Field(
        default_factory=list,
        description="Anesthesia drugs and protocols",
    )
    analgesia_protocols: list[DrugInfo] = Field(
        default_factory=list,
        description="Analgesia drugs and protocols",
    )
    monitoring_during_anesthesia: Optional[str] = Field(
        default=None,
        description="How animals will be monitored during anesthesia",
    )
    
    # Section 10: Surgical Procedures
    surgical_procedures: list[ProcedureInfo] = Field(
        default_factory=list,
        description="Detailed surgical procedure descriptions",
    )
    aseptic_technique: Optional[str] = Field(
        default=None,
        description="Description of aseptic technique",
    )
    post_operative_care: Optional[str] = Field(
        default=None,
        description="Post-operative care and monitoring",
    )
    multiple_survival_surgeries: bool = Field(default=False)
    multiple_surgery_justification: Optional[str] = Field(default=None)
    
    # Section 11: Humane Endpoints
    humane_endpoints: list[HumaneEndpoint] = Field(
        description="Criteria for early euthanasia",
    )
    monitoring_schedule: str = Field(
        description="Frequency and type of health monitoring",
    )
    responsible_person: Optional[str] = Field(
        default=None,
        description="Person responsible for endpoint monitoring",
    )
    
    # Section 12: Euthanasia
    euthanasia_method: str = Field(description="Primary euthanasia method")
    euthanasia_justification: Optional[str] = Field(
        default=None,
        description="Justification if method requires it",
    )
    secondary_method: Optional[str] = Field(
        default=None,
        description="Secondary/confirmation method",
    )
    avma_compliant: bool = Field(
        default=True,
        description="Method is AVMA approved",
    )
    
    # Section 13: Hazardous Materials
    hazardous_materials: list[dict] = Field(
        default_factory=list,
        description="List of hazardous materials used",
    )
    biohazard_level: Optional[str] = Field(default=None)
    radiation_use: bool = Field(default=False)
    ibc_approval: Optional[str] = Field(
        default=None,
        description="IBC approval number if applicable",
    )
    
    # Additional fields
    additional_sections: dict[str, ProtocolSection] = Field(
        default_factory=dict,
        description="Any additional custom sections",
    )
    attachments: list[str] = Field(
        default_factory=list,
        description="List of attachment filenames",
    )
    notes: Optional[str] = Field(default=None)
    
    @field_validator('total_animals')
    @classmethod
    def validate_total_animals(cls, v, info):
        """Validate total animals is positive."""
        if v < 1:
            raise ValueError("Total animals must be at least 1")
        return v
    
    def calculate_completeness(self) -> float:
        """
        Calculate protocol completeness score.
        
        Returns:
            Completeness score from 0 to 1.
        """
        required_fields = [
            self.title,
            self.principal_investigator,
            self.lay_summary,
            self.animals,
            self.scientific_objectives,
            self.scientific_rationale,
            self.replacement_statement,
            self.reduction_statement,
            self.refinement_statement,
            self.experimental_design,
            self.procedures,
            self.humane_endpoints,
            self.euthanasia_method,
        ]
        
        filled = sum(1 for f in required_fields if f)
        return filled / len(required_fields)
    
    def get_missing_sections(self) -> list[str]:
        """
        Get list of missing or incomplete sections.
        
        Returns:
            List of section names that are missing/incomplete.
        """
        missing = []
        
        section_checks = [
            ("Title", self.title),
            ("Principal Investigator", self.principal_investigator),
            ("Lay Summary", self.lay_summary),
            ("Animals", bool(self.animals)),
            ("Scientific Objectives", self.scientific_objectives),
            ("Scientific Rationale", self.scientific_rationale),
            ("Replacement Statement", self.replacement_statement),
            ("Reduction Statement", self.reduction_statement),
            ("Refinement Statement", self.refinement_statement),
            ("Experimental Design", self.experimental_design),
            ("Procedures", bool(self.procedures)),
            ("Humane Endpoints", bool(self.humane_endpoints)),
            ("Euthanasia Method", self.euthanasia_method),
        ]
        
        for name, value in section_checks:
            if not value:
                missing.append(name)
        
        return missing
    
    def to_summary_dict(self) -> dict:
        """
        Get summary dictionary for display.
        
        Returns:
            Summary dictionary with key information.
        """
        return {
            "id": self.id,
            "protocol_number": self.protocol_number,
            "title": self.title,
            "status": self.status.value,
            "pi_name": self.principal_investigator.name,
            "species": [a.species for a in self.animals],
            "total_animals": self.total_animals,
            "usda_category": self.usda_category.value,
            "completeness": self.calculate_completeness(),
            "created_at": self.created_at.isoformat(),
        }


# ============================================================================
# PROTOCOL CREATION HELPERS
# ============================================================================

def create_empty_protocol(
    title: str,
    pi_name: str,
    pi_email: str,
    department: str,
) -> Protocol:
    """
    Create an empty protocol with minimal required fields.
    
    Args:
        title: Protocol title
        pi_name: PI name
        pi_email: PI email
        department: Department
        
    Returns:
        New Protocol with defaults.
    """
    return Protocol(
        title=title,
        principal_investigator=PersonnelInfo(
            name=pi_name,
            role="Principal Investigator",
            email=pi_email,
        ),
        department=department,
        study_duration="12 months",
        lay_summary="This section will describe the research project in plain language that can be understood by non-scientists. To be completed with project-specific details.",
        animals=[
            AnimalInfo(
                species="TBD",
                sex="both",
                total_number=1,
                source="TBD",
            )
        ],
        usda_category=USDACategory.C,
        total_animals=1,
        animal_number_justification="To be completed.",
        scientific_objectives="To be completed.",
        scientific_rationale="To be completed.",
        potential_benefits="To be completed.",
        replacement_statement="To be completed.",
        reduction_statement="To be completed.",
        refinement_statement="To be completed.",
        experimental_design="To be completed.",
        statistical_methods="To be completed.",
        procedures=[
            ProcedureInfo(
                name="TBD",
                description="To be completed.",
                purpose="TBD",
            )
        ],
        humane_endpoints=[
            HumaneEndpoint(
                criterion="TBD",
                measurement="TBD",
                threshold="TBD",
                action="Euthanasia",
            )
        ],
        monitoring_schedule="To be completed.",
        euthanasia_method="TBD",
    )


# Export
__all__ = [
    "ProtocolStatus",
    "USDACategory",
    "PersonnelInfo",
    "AnimalInfo",
    "DrugInfo",
    "ProcedureInfo",
    "HumaneEndpoint",
    "LiteratureSearch",
    "ProtocolSection",
    "Protocol",
    "create_empty_protocol",
]
