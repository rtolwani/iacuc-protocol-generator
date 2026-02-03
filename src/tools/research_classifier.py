"""
Research Classifier Tool.

Classifies research type and identifies special requirements for IACUC protocols.
"""

from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ResearchClassification(BaseModel):
    """Complete research classification result."""
    
    research_type: str = Field(description="Primary research type")
    procedure_types: list[str] = Field(description="Identified procedure types")
    species_category: str = Field(description="Species regulatory category")
    pain_category_estimate: str = Field(description="Estimated USDA pain category")
    special_requirements: list[str] = Field(default_factory=list)
    required_permits: list[str] = Field(default_factory=list)
    suggested_agents: list[str] = Field(description="Agents needed for this protocol")
    flags: list[str] = Field(default_factory=list, description="Special flags/warnings")


# Research type definitions
RESEARCH_TYPES = {
    "basic": {
        "keywords": ["mechanism", "pathway", "molecular", "cellular", "fundamental", "basic science"],
        "description": "Basic/fundamental research to understand mechanisms",
    },
    "preclinical": {
        "keywords": ["drug", "therapy", "treatment", "efficacy", "pharmaceutical", "preclinical", "translational"],
        "description": "Preclinical drug development or therapeutic testing",
    },
    "behavioral": {
        "keywords": ["behavior", "behavioral", "learning", "memory", "cognition", "anxiety", "depression", "social"],
        "description": "Behavioral or neuroscience research",
    },
    "surgical": {
        "keywords": ["surgery", "surgical", "implant", "transplant", "model creation"],
        "description": "Research requiring surgical procedures",
    },
    "oncology": {
        "keywords": ["tumor", "cancer", "oncology", "carcinoma", "xenograft", "metastasis"],
        "description": "Cancer/oncology research",
    },
    "infectious_disease": {
        "keywords": ["infection", "infectious", "virus", "bacteria", "pathogen", "vaccine", "immunity"],
        "description": "Infectious disease research",
    },
    "toxicology": {
        "keywords": ["toxicity", "toxic", "toxicology", "safety", "LD50", "dose-response"],
        "description": "Toxicology or safety testing",
    },
    "teaching": {
        "keywords": ["teaching", "training", "education", "demonstration", "course"],
        "description": "Teaching or training purposes",
    },
    "breeding": {
        "keywords": ["breeding", "colony", "production", "genotyping"],
        "description": "Breeding colony maintenance",
    },
}

# Procedure type definitions
PROCEDURE_TYPES = {
    "survival_surgery": {
        "keywords": ["survival surgery", "surgical procedure", "implant", "craniotomy"],
        "requirements": ["Sterile technique", "Post-operative analgesia", "Monitoring protocol"],
    },
    "non_survival_surgery": {
        "keywords": ["non-survival", "terminal surgery", "acute surgery"],
        "requirements": ["Anesthesia protocol", "Tissue collection plan"],
    },
    "injection": {
        "keywords": ["injection", "inject", "administer", "dose", "IP", "IV", "SC", "IM"],
        "requirements": ["Injection volume limits", "Needle size specification"],
    },
    "blood_collection": {
        "keywords": ["blood", "bleed", "venipuncture", "cardiac puncture", "retro-orbital"],
        "requirements": ["Volume limits", "Recovery time if serial"],
    },
    "imaging": {
        "keywords": ["imaging", "MRI", "CT", "PET", "ultrasound", "bioluminescence"],
        "requirements": ["Anesthesia for imaging", "Contrast agent protocol"],
    },
    "behavioral_testing": {
        "keywords": ["maze", "test", "behavioral", "fear conditioning", "open field"],
        "requirements": ["Test duration limits", "Rest periods"],
    },
    "food_water_restriction": {
        "keywords": ["food restriction", "water restriction", "fasting", "deprivation"],
        "requirements": ["Body weight monitoring", "Restriction limits"],
    },
    "tumor_implantation": {
        "keywords": ["tumor", "implant", "xenograft", "inoculate", "cancer cells"],
        "requirements": ["Tumor size limits", "Humane endpoints"],
    },
    "euthanasia": {
        "keywords": ["euthanasia", "euthanize", "sacrifice", "terminal"],
        "requirements": ["AVMA-approved method", "Secondary confirmation"],
    },
}

# Species categories
SPECIES_CATEGORIES = {
    "usda_covered": {
        "species": ["dog", "cat", "rabbit", "hamster", "guinea pig", "primate", "monkey", 
                   "pig", "sheep", "goat", "horse", "cow", "cattle"],
        "requirements": ["USDA Annual Report", "Pain Category Reporting"],
    },
    "usda_exempt": {
        "species": ["mouse", "mice", "rat", "rats", "bird", "birds", "fish", "zebrafish"],
        "requirements": ["PHS Policy Compliance", "IACUC Oversight"],
    },
    "wildlife": {
        "species": ["wild", "wildlife", "field study", "free-ranging"],
        "requirements": ["Wildlife Permits", "Collection Permits"],
    },
    "aquatic": {
        "species": ["fish", "zebrafish", "aquatic", "amphibian", "frog", "xenopus"],
        "requirements": ["Water quality monitoring", "Tank specifications"],
    },
}

# Special requirement flags
SPECIAL_REQUIREMENTS = {
    "dea_controlled": {
        "keywords": ["ketamine", "morphine", "fentanyl", "oxycodone", "controlled substance",
                    "schedule II", "schedule III", "schedule IV"],
        "requirement": "DEA Registration Required",
        "permit": "DEA Controlled Substance License",
    },
    "biohazard": {
        "keywords": ["biohazard", "BSL-2", "BSL-3", "infectious", "pathogen", "virus", 
                    "bacteria", "recombinant"],
        "requirement": "IBC Approval Required",
        "permit": "Institutional Biosafety Committee Approval",
    },
    "radiation": {
        "keywords": ["radiation", "radioactive", "isotope", "x-ray", "irradiation"],
        "requirement": "Radiation Safety Approval Required",
        "permit": "Radiation Safety Committee Approval",
    },
    "human_tissue": {
        "keywords": ["human tissue", "human cells", "patient samples", "clinical samples"],
        "requirement": "IRB Coordination Required",
        "permit": "IRB Approval or Exemption",
    },
    "field_study": {
        "keywords": ["field", "wild", "natural habitat", "free-ranging", "capture"],
        "requirement": "Wildlife Permits Required",
        "permit": "State/Federal Wildlife Permits",
    },
    "endangered": {
        "keywords": ["endangered", "threatened", "protected species", "CITES"],
        "requirement": "USFWS Permit Required",
        "permit": "US Fish & Wildlife Service Permit",
    },
    "multiple_surgery": {
        "keywords": ["multiple survival", "second surgery", "re-operation", "staged"],
        "requirement": "Multiple Survival Surgery Justification",
        "permit": None,
    },
}


def classify_research_type(description: str) -> str:
    """
    Classify the primary research type.
    
    Args:
        description: Research description text
        
    Returns:
        Primary research type.
    """
    description_lower = description.lower()
    
    scores = {}
    for rtype, info in RESEARCH_TYPES.items():
        score = sum(1 for kw in info["keywords"] if kw in description_lower)
        if score > 0:
            scores[rtype] = score
    
    if scores:
        return max(scores, key=scores.get)
    
    return "basic"  # Default


def identify_procedure_types(description: str) -> list[str]:
    """
    Identify all procedure types in the description.
    
    Args:
        description: Research description text
        
    Returns:
        List of procedure types.
    """
    description_lower = description.lower()
    procedures = []
    
    for proc_type, info in PROCEDURE_TYPES.items():
        if any(kw in description_lower for kw in info["keywords"]):
            procedures.append(proc_type)
    
    return procedures if procedures else ["observation"]


def identify_species_category(species: str) -> str:
    """
    Identify the regulatory category for a species.
    
    Args:
        species: Species name
        
    Returns:
        Species regulatory category.
    """
    species_lower = species.lower()
    
    for category, info in SPECIES_CATEGORIES.items():
        if any(s in species_lower for s in info["species"]):
            return category
    
    return "usda_exempt"  # Default for most lab animals


def identify_special_requirements(description: str) -> tuple[list[str], list[str]]:
    """
    Identify special requirements and permits needed.
    
    Args:
        description: Research description text
        
    Returns:
        Tuple of (requirements list, permits list).
    """
    description_lower = description.lower()
    requirements = []
    permits = []
    
    for req_type, info in SPECIAL_REQUIREMENTS.items():
        if any(kw in description_lower for kw in info["keywords"]):
            requirements.append(info["requirement"])
            if info.get("permit"):
                permits.append(info["permit"])
    
    return requirements, permits


def estimate_pain_category(procedures: list[str], description: str) -> str:
    """
    Estimate USDA pain category based on procedures.
    
    Args:
        procedures: List of procedure types
        description: Full description
        
    Returns:
        Estimated pain category (B, C, D, or E).
    """
    description_lower = description.lower()
    
    # Check for Category E indicators
    if any(kw in description_lower for kw in ["without analgesia", "no pain relief", 
                                               "unrelieved", "lethal dose", "death as endpoint"]):
        return "E"
    
    # Check for Category D indicators
    pain_procedures = ["survival_surgery", "tumor_implantation", "injection"]
    if any(p in procedures for p in pain_procedures):
        return "D"
    
    # Check for Category B (breeding only)
    if procedures == ["observation"] or "breeding" in description_lower:
        if "experiment" not in description_lower and "test" not in description_lower:
            return "B"
    
    # Default to Category C for most non-painful procedures
    return "C"


def determine_required_agents(
    research_type: str,
    procedures: list[str],
    special_requirements: list[str],
) -> list[str]:
    """
    Determine which agents are needed for this protocol.
    
    Args:
        research_type: Primary research type
        procedures: List of procedure types
        special_requirements: List of special requirements
        
    Returns:
        List of agent names needed.
    """
    agents = [
        "Intake Specialist",  # Always needed
        "Regulatory Scout",   # Always needed
        "Lay Summary Writer", # Always needed
    ]
    
    # Add based on procedures
    if any(p in procedures for p in ["survival_surgery", "non_survival_surgery", 
                                      "injection", "blood_collection"]):
        agents.append("Veterinary Reviewer")
        agents.append("Procedure Writer")
    
    if any(p in procedures for p in ["tumor_implantation", "behavioral_testing"]):
        agents.append("Alternatives Researcher")
    
    # Statistical consultant if doing comparative studies
    agents.append("Statistical Consultant")
    
    # Always need assembler
    agents.append("Protocol Assembler")
    
    return agents


def classify_research(
    description: str,
    species: str,
) -> ResearchClassification:
    """
    Perform complete research classification.
    
    Args:
        description: Research description text
        species: Species being used
        
    Returns:
        Complete ResearchClassification.
    """
    research_type = classify_research_type(description)
    procedures = identify_procedure_types(description)
    species_category = identify_species_category(species)
    pain_category = estimate_pain_category(procedures, description)
    requirements, permits = identify_special_requirements(description)
    agents = determine_required_agents(research_type, procedures, requirements)
    
    # Generate flags
    flags = []
    if pain_category == "E":
        flags.append("Category E: Scientific justification required for withholding pain relief")
    if "DEA" in " ".join(requirements):
        flags.append("Controlled substances: DEA registration verification needed")
    if "IBC" in " ".join(requirements):
        flags.append("Biohazard: IBC approval must be obtained before IACUC approval")
    if species_category == "usda_covered":
        flags.append("USDA-covered species: Annual reporting requirements apply")
    if "multiple_surgery" in description.lower() or "second surgery" in description.lower():
        flags.append("Multiple survival surgery: Requires specific scientific justification")
    
    return ResearchClassification(
        research_type=research_type,
        procedure_types=procedures,
        species_category=species_category,
        pain_category_estimate=pain_category,
        special_requirements=requirements,
        required_permits=permits,
        suggested_agents=agents,
        flags=flags,
    )


class ResearchClassifierTool(BaseTool):
    """
    Tool for classifying research type and identifying requirements.
    
    Used by intake agents to understand the scope of a research project
    and determine which agents and processes are needed.
    """
    
    name: str = "research_classifier"
    description: str = (
        "Classify a research project and identify special requirements. "
        "Input format: 'species: [species], description: [research description]'. "
        "Returns research type, procedure types, and special requirements."
    )
    
    def _run(self, input_text: str) -> str:
        """
        Classify research and return formatted results.
        
        Args:
            input_text: Species and research description
            
        Returns:
            Formatted classification results.
        """
        # Parse input
        species = "laboratory animal"
        description = input_text
        
        if "species:" in input_text.lower():
            parts = input_text.split(",", 1)
            for part in parts:
                if "species:" in part.lower():
                    species = part.split(":")[-1].strip()
                elif "description:" in part.lower():
                    description = part.split(":", 1)[-1].strip()
                else:
                    description = part.strip()
        
        # Classify
        result = classify_research(description, species)
        
        # Format output
        output = [
            "RESEARCH CLASSIFICATION",
            "=" * 50,
            "",
            f"Research Type: {result.research_type.replace('_', ' ').title()}",
            f"Species Category: {result.species_category.replace('_', ' ').title()}",
            f"Estimated Pain Category: {result.pain_category_estimate}",
            "",
            "Procedure Types:",
        ]
        
        for proc in result.procedure_types:
            output.append(f"  • {proc.replace('_', ' ').title()}")
        
        if result.special_requirements:
            output.extend(["", "Special Requirements:"])
            for req in result.special_requirements:
                output.append(f"  ⚠ {req}")
        
        if result.required_permits:
            output.extend(["", "Required Permits:"])
            for permit in result.required_permits:
                output.append(f"  📋 {permit}")
        
        if result.flags:
            output.extend(["", "Flags/Warnings:"])
            for flag in result.flags:
                output.append(f"  🚩 {flag}")
        
        output.extend(["", "Suggested Agent Workflow:"])
        for i, agent in enumerate(result.suggested_agents, 1):
            output.append(f"  {i}. {agent}")
        
        return "\n".join(output)


# Export key items
__all__ = [
    "ResearchClassifierTool",
    "classify_research",
    "classify_research_type",
    "identify_procedure_types",
    "identify_species_category",
    "identify_special_requirements",
    "estimate_pain_category",
    "ResearchClassification",
    "RESEARCH_TYPES",
    "PROCEDURE_TYPES",
    "SPECIES_CATEGORIES",
    "SPECIAL_REQUIREMENTS",
]
