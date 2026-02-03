"""
Veterinary Reviewer Agent.

An agent that simulates veterinary pre-review of IACUC protocols,
including drug dosage validation, humane endpoint assessment,
and welfare concern flagging.
"""

from enum import Enum
from typing import Optional

from crewai import Agent, Task, Crew
from pydantic import BaseModel, Field

from src.agents.llm import get_llm
from src.tools.formulary_tool import FormularyLookupTool, DrugFormulary
from src.tools.pain_category_tool import PainCategoryTool, classify_pain_category
from src.tools.rag_tools import RegulatorySearchTool


class Severity(str, Enum):
    """Severity levels for review findings."""
    CRITICAL = "critical"  # Must be addressed before approval
    WARNING = "warning"    # Should be addressed, may delay approval
    INFO = "info"          # Informational, recommendations


class ReviewFinding(BaseModel):
    """A single finding from veterinary review."""
    
    severity: Severity = Field(description="Severity level")
    category: str = Field(description="Category of finding")
    issue: str = Field(description="Description of the issue")
    recommendation: str = Field(description="Recommended action")
    reference: Optional[str] = Field(default=None, description="Regulatory reference")


class HumaneEndpoint(BaseModel):
    """Definition of a humane endpoint."""
    
    criterion: str = Field(description="Observable criterion")
    action: str = Field(description="Required action when criterion met")
    monitoring_frequency: str = Field(description="How often to monitor")


class VeterinaryReviewResult(BaseModel):
    """Complete veterinary review result."""
    
    protocol_summary: str = Field(description="Brief protocol summary")
    pain_category: str = Field(description="USDA pain category")
    findings: list[ReviewFinding] = Field(default_factory=list)
    recommended_endpoints: list[HumaneEndpoint] = Field(default_factory=list)
    drug_validations: list[dict] = Field(default_factory=list)
    overall_assessment: str = Field(description="Overall veterinary assessment")
    requires_revision: bool = Field(description="Whether protocol needs revision")


# Common welfare concerns by procedure type
WELFARE_CONCERNS = {
    "surgery": {
        "concerns": [
            "Adequate anesthesia depth",
            "Post-operative pain management",
            "Surgical site monitoring",
            "Recovery monitoring",
        ],
        "required_monitoring": "Daily for 7 days post-surgery, or until sutures removed",
    },
    "tumor": {
        "concerns": [
            "Tumor burden limits",
            "Body condition scoring",
            "Ulceration monitoring",
            "Mobility assessment",
        ],
        "required_monitoring": "At least 3 times weekly when tumors palpable",
    },
    "infectious": {
        "concerns": [
            "Disease progression monitoring",
            "Weight loss limits",
            "Isolation requirements",
            "Veterinary notification triggers",
        ],
        "required_monitoring": "Daily during active infection phase",
    },
    "behavioral": {
        "concerns": [
            "Stress indicators",
            "Social housing requirements",
            "Environmental enrichment",
            "Test duration limits",
        ],
        "required_monitoring": "Before and after behavioral sessions",
    },
    "restraint": {
        "concerns": [
            "Duration limits",
            "Acclimation protocol",
            "Distress indicators",
            "Alternative methods considered",
        ],
        "required_monitoring": "Continuous during restraint",
    },
}


# Standard humane endpoints by procedure type
STANDARD_ENDPOINTS = {
    "general": [
        HumaneEndpoint(
            criterion="Weight loss >20% of baseline",
            action="Immediate euthanasia",
            monitoring_frequency="Daily weighing if weight loss detected",
        ),
        HumaneEndpoint(
            criterion="Inability to reach food/water",
            action="Immediate euthanasia",
            monitoring_frequency="Daily observation",
        ),
        HumaneEndpoint(
            criterion="Moribund condition (non-responsive, hypothermic)",
            action="Immediate euthanasia",
            monitoring_frequency="Daily observation",
        ),
    ],
    "tumor": [
        HumaneEndpoint(
            criterion="Tumor >2cm in any dimension (mice) or >10% body weight",
            action="Euthanasia within 24 hours",
            monitoring_frequency="Tumor measurement 3x/week",
        ),
        HumaneEndpoint(
            criterion="Tumor ulceration or necrosis",
            action="Immediate veterinary consultation, likely euthanasia",
            monitoring_frequency="Daily visual inspection",
        ),
        HumaneEndpoint(
            criterion="Interference with ambulation or normal behavior",
            action="Euthanasia within 24 hours",
            monitoring_frequency="Daily observation",
        ),
    ],
    "surgery": [
        HumaneEndpoint(
            criterion="Surgical site dehiscence or severe infection",
            action="Veterinary consultation, possible euthanasia",
            monitoring_frequency="Daily until healed",
        ),
        HumaneEndpoint(
            criterion="Uncontrolled pain despite analgesics",
            action="Veterinary consultation, consider euthanasia",
            monitoring_frequency="Multiple times daily for 72 hours",
        ),
    ],
}


def identify_procedure_type(procedures: str) -> list[str]:
    """
    Identify procedure types from description.
    
    Args:
        procedures: Description of procedures
        
    Returns:
        List of identified procedure types.
    """
    procedures_lower = procedures.lower()
    types = []
    
    if any(kw in procedures_lower for kw in ["surgery", "surgical", "incision"]):
        types.append("surgery")
    if any(kw in procedures_lower for kw in ["tumor", "cancer", "carcinoma", "xenograft"]):
        types.append("tumor")
    if any(kw in procedures_lower for kw in ["infectious", "infection", "virus", "bacteria", "pathogen"]):
        types.append("infectious")
    if any(kw in procedures_lower for kw in ["behavior", "behavioral", "learning", "memory", "anxiety"]):
        types.append("behavioral")
    if any(kw in procedures_lower for kw in ["restraint", "immobilize", "restrain"]):
        types.append("restraint")
    
    return types if types else ["general"]


def generate_welfare_concerns(procedures: str) -> list[str]:
    """
    Generate welfare concerns based on procedures.
    
    Args:
        procedures: Description of procedures
        
    Returns:
        List of welfare concerns.
    """
    proc_types = identify_procedure_type(procedures)
    concerns = []
    
    for proc_type in proc_types:
        if proc_type in WELFARE_CONCERNS:
            concerns.extend(WELFARE_CONCERNS[proc_type]["concerns"])
    
    return list(set(concerns))  # Remove duplicates


def get_recommended_endpoints(procedures: str) -> list[HumaneEndpoint]:
    """
    Get recommended humane endpoints for procedures.
    
    Args:
        procedures: Description of procedures
        
    Returns:
        List of recommended humane endpoints.
    """
    proc_types = identify_procedure_type(procedures)
    endpoints = STANDARD_ENDPOINTS["general"].copy()
    
    for proc_type in proc_types:
        if proc_type in STANDARD_ENDPOINTS:
            endpoints.extend(STANDARD_ENDPOINTS[proc_type])
    
    return endpoints


def validate_protocol_drugs(
    drug_list: list[dict],
    species: str,
) -> list[dict]:
    """
    Validate all drugs in a protocol.
    
    Args:
        drug_list: List of drugs with doses
        species: Species being used
        
    Returns:
        List of validation results.
    """
    formulary = DrugFormulary()
    results = []
    
    for drug in drug_list:
        drug_name = drug.get("name", "")
        dose = drug.get("dose", "")
        
        validation = formulary.validate_dose(drug_name, species, dose)
        validation["drug_name"] = drug_name
        validation["proposed_dose"] = dose
        validation["species"] = species
        results.append(validation)
    
    return results


def create_veterinary_reviewer_agent() -> Agent:
    """
    Create a Veterinary Reviewer agent.
    
    This agent:
    - Reviews drug dosages against formulary
    - Assesses humane endpoints
    - Flags welfare concerns
    - Provides severity-rated findings
    
    Returns:
        Configured CrewAI Agent instance.
    """
    llm = get_llm()
    formulary_tool = FormularyLookupTool()
    pain_tool = PainCategoryTool()
    rag_tool = RegulatorySearchTool()
    
    return Agent(
        role="Veterinary Reviewer",
        goal=(
            "Conduct a thorough veterinary pre-review of IACUC protocols. "
            "Validate drug dosages, assess humane endpoints, identify welfare "
            "concerns, and provide severity-rated recommendations to ensure "
            "animal welfare standards are met."
        ),
        backstory=(
            "You are an experienced laboratory animal veterinarian with ACLAM "
            "board certification. You have conducted thousands of protocol reviews "
            "and are an expert in rodent and rabbit medicine. You're thorough but "
            "practical, focused on ensuring animal welfare while supporting "
            "legitimate research objectives. You're familiar with institutional "
            "drug formularies and regulatory requirements, and you know how to "
            "communicate concerns effectively to researchers."
        ),
        llm=llm,
        tools=[formulary_tool, pain_tool, rag_tool],
        verbose=False,
        allow_delegation=False,
    )


def create_veterinary_review_task(
    agent: Agent,
    species: str,
    procedures: str,
    drugs: list[dict],
    proposed_endpoints: Optional[list[str]] = None,
) -> Task:
    """
    Create a veterinary review task.
    
    Args:
        agent: The Veterinary Reviewer agent
        species: Species being used
        procedures: Description of procedures
        drugs: List of drugs with doses
        proposed_endpoints: Any endpoints already proposed
        
    Returns:
        Configured CrewAI Task instance.
    """
    drugs_str = "\n".join([
        f"  - {d.get('name', 'Unknown')}: {d.get('dose', 'Unknown')}"
        for d in drugs
    ])
    
    endpoints_str = ""
    if proposed_endpoints:
        endpoints_str = "\nProposed Endpoints:\n" + "\n".join([f"  - {e}" for e in proposed_endpoints])
    
    return Task(
        description=f"""
Conduct a veterinary pre-review of this IACUC protocol:

SPECIES: {species}
PROCEDURES: {procedures}

PROPOSED DRUGS:
{drugs_str}
{endpoints_str}

Your review must include:

1. DRUG VALIDATION:
   - Use the formulary_lookup tool to verify each drug's dose
   - Flag any doses outside approved ranges
   - Note any contraindications for the species/procedure

2. PAIN CATEGORY ASSESSMENT:
   - Use the pain_category_classifier to determine USDA category
   - Verify pain relief plan is appropriate for the category

3. HUMANE ENDPOINTS:
   - Assess if proposed endpoints are adequate
   - Recommend additional endpoints if needed
   - Specify monitoring frequency requirements

4. WELFARE CONCERNS:
   - Identify potential welfare issues specific to these procedures
   - Rate each concern as CRITICAL, WARNING, or INFO
   - Provide specific recommendations for each concern

5. OVERALL ASSESSMENT:
   - Summarize key veterinary concerns
   - Determine if protocol requires revision before approval
   - List any conditions for approval

Be thorough but constructive. Identify real concerns while supporting legitimate research.
""",
        expected_output=(
            "A comprehensive veterinary review with drug validations, humane endpoint "
            "assessment, severity-rated welfare concerns, and overall recommendation."
        ),
        agent=agent,
    )


def conduct_veterinary_review(
    species: str,
    procedures: str,
    drugs: list[dict],
    proposed_endpoints: Optional[list[str]] = None,
    verbose: bool = False,
) -> dict:
    """
    Conduct a veterinary review of a protocol.
    
    Main entry point for veterinary review.
    
    Args:
        species: Species being used
        procedures: Description of procedures
        drugs: List of drugs with doses
        proposed_endpoints: Any endpoints already proposed
        verbose: Whether to show agent reasoning
        
    Returns:
        Dictionary with review results.
    """
    # Create agent and task
    agent = create_veterinary_reviewer_agent()
    if verbose:
        agent.verbose = True
    
    task = create_veterinary_review_task(
        agent=agent,
        species=species,
        procedures=procedures,
        drugs=drugs,
        proposed_endpoints=proposed_endpoints,
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=verbose,
    )
    
    # Run the review
    agent_result = crew.kickoff()
    
    # Get quick assessments
    pain_result = classify_pain_category(procedures)
    drug_validations = validate_protocol_drugs(drugs, species)
    
    return {
        "species": species,
        "procedures": procedures,
        "pain_category": pain_result.category,
        "drug_validations": drug_validations,
        "recommended_endpoints": [e.model_dump() for e in get_recommended_endpoints(procedures)],
        "welfare_concerns": generate_welfare_concerns(procedures),
        "detailed_review": str(agent_result),
    }


# Quick review without LLM
def quick_veterinary_check(
    species: str,
    procedures: str,
    drugs: list[dict],
) -> dict:
    """
    Quick veterinary check without LLM calls.
    
    Args:
        species: Species being used
        procedures: Description of procedures
        drugs: List of drugs with doses
        
    Returns:
        Dictionary with quick assessment.
    """
    # Validate drugs
    drug_validations = validate_protocol_drugs(drugs, species)
    
    # Get pain category
    pain_result = classify_pain_category(procedures)
    
    # Get welfare concerns
    concerns = generate_welfare_concerns(procedures)
    
    # Get endpoints
    endpoints = get_recommended_endpoints(procedures)
    
    # Determine if revision needed
    critical_issues = []
    
    # Check for drug issues
    for validation in drug_validations:
        if validation["status"] in ["NOT_FOUND", "ABOVE_RANGE"]:
            critical_issues.append(f"Drug issue: {validation['message']}")
    
    # Check for Category E without justification
    if pain_result.requires_justification:
        critical_issues.append("Category E requires scientific justification for withholding pain relief")
    
    return {
        "species": species,
        "pain_category": {
            "category": pain_result.category,
            "name": pain_result.category_name,
            "requires_justification": pain_result.requires_justification,
        },
        "drug_validations": drug_validations,
        "welfare_concerns": concerns,
        "recommended_endpoints": [e.model_dump() for e in endpoints],
        "critical_issues": critical_issues,
        "requires_revision": len(critical_issues) > 0,
    }


# Export key items
__all__ = [
    "create_veterinary_reviewer_agent",
    "create_veterinary_review_task",
    "conduct_veterinary_review",
    "quick_veterinary_check",
    "validate_protocol_drugs",
    "generate_welfare_concerns",
    "get_recommended_endpoints",
    "Severity",
    "ReviewFinding",
    "HumaneEndpoint",
    "VeterinaryReviewResult",
    "WELFARE_CONCERNS",
    "STANDARD_ENDPOINTS",
]
