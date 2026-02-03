"""
Regulatory Scout Agent.

An agent that identifies all applicable regulations, pain categories,
and permit requirements for research protocols.
"""

from crewai import Agent, Task, Crew

from src.agents.llm import get_llm
from src.tools.pain_category_tool import PainCategoryTool, classify_pain_category
from src.tools.rag_tools import RegulatorySearchTool


# Species regulatory categorization
SPECIES_REGULATIONS = {
    "usda_covered": {
        "species": [
            "dog", "cat", "rabbit", "hamster", "guinea pig", "gerbil",
            "non-human primate", "primate", "monkey", "pig", "sheep",
            "goat", "horse", "cow", "cattle",
        ],
        "requirements": [
            "USDA Animal Welfare Act registration required",
            "Annual USDA inspection",
            "USDA pain category reporting mandatory",
        ],
    },
    "usda_exempt": {
        "species": [
            "mouse", "mice", "rat", "rats", "bird", "birds",
            "fish", "zebrafish", "reptile", "amphibian",
        ],
        "requirements": [
            "Not covered by USDA Animal Welfare Act",
            "Still covered by PHS Policy if federally funded",
            "IACUC oversight still required",
        ],
    },
    "wildlife": {
        "species": [
            "wild", "wildlife", "field", "native",
        ],
        "requirements": [
            "May require state wildlife permits",
            "May require federal permits (USFWS)",
            "Check endangered species status",
        ],
    },
}

# Procedure-specific regulations
PROCEDURE_REGULATIONS = {
    "survival_surgery": {
        "keywords": ["survival surgery", "surgical", "surgery"],
        "regulations": [
            "Aseptic technique required (The Guide)",
            "Dedicated surgical area or space",
            "Post-operative monitoring required",
            "Anesthesia and analgesia protocols required",
        ],
    },
    "multiple_survival_surgery": {
        "keywords": ["multiple survival", "second surgery", "re-operation"],
        "regulations": [
            "Scientific justification required for multiple surgeries",
            "IACUC must specifically approve",
            "Cost savings alone not sufficient justification",
        ],
    },
    "food_water_restriction": {
        "keywords": ["food restriction", "water restriction", "deprivation", "fasting"],
        "regulations": [
            "Scientific justification required",
            "Body weight monitoring mandatory",
            "Defined limits and endpoints required",
        ],
    },
    "restraint": {
        "keywords": ["restraint", "immobilization", "physical restraint"],
        "regulations": [
            "Duration limits must be specified",
            "Training/acclimation period required",
            "Alternatives to physical restraint considered",
        ],
    },
    "hazardous_agents": {
        "keywords": ["biohazard", "infectious", "radiation", "carcinogen", "toxin"],
        "regulations": [
            "IBC approval may be required",
            "Radiation safety approval may be required", 
            "Special housing/containment requirements",
        ],
    },
    "controlled_substances": {
        "keywords": ["dea", "controlled substance", "schedule", "ketamine", "morphine", "fentanyl"],
        "regulations": [
            "DEA registration required",
            "Controlled substance logs mandatory",
            "Secure storage required",
        ],
    },
    "field_studies": {
        "keywords": ["field", "wild", "free-ranging", "natural habitat"],
        "regulations": [
            "IACUC approval still required",
            "Collection permits may be needed",
            "State and federal wildlife regulations apply",
        ],
    },
    "euthanasia": {
        "keywords": ["euthanasia", "euthanize", "sacrifice"],
        "regulations": [
            "AVMA Guidelines for Euthanasia must be followed",
            "Method must be appropriate for species",
            "Secondary method required to confirm death",
        ],
    },
}


def identify_species_category(species: str) -> dict:
    """
    Identify the regulatory category for a species.
    
    Args:
        species: Species name
        
    Returns:
        Dictionary with category and requirements
    """
    species_lower = species.lower()
    
    # Check USDA covered
    for s in SPECIES_REGULATIONS["usda_covered"]["species"]:
        if s in species_lower:
            return {
                "category": "USDA Covered",
                "species": species,
                "requirements": SPECIES_REGULATIONS["usda_covered"]["requirements"],
            }
    
    # Check wildlife
    for s in SPECIES_REGULATIONS["wildlife"]["species"]:
        if s in species_lower:
            return {
                "category": "Wildlife",
                "species": species,
                "requirements": SPECIES_REGULATIONS["wildlife"]["requirements"],
            }
    
    # Default to USDA exempt
    return {
        "category": "USDA Exempt (PHS Policy applies)",
        "species": species,
        "requirements": SPECIES_REGULATIONS["usda_exempt"]["requirements"],
    }


def identify_procedure_requirements(procedures: str) -> list[dict]:
    """
    Identify regulatory requirements based on procedures.
    
    Args:
        procedures: Description of procedures
        
    Returns:
        List of applicable regulatory requirements
    """
    procedures_lower = procedures.lower()
    requirements = []
    
    for proc_type, proc_info in PROCEDURE_REGULATIONS.items():
        for keyword in proc_info["keywords"]:
            if keyword in procedures_lower:
                requirements.append({
                    "type": proc_type.replace("_", " ").title(),
                    "regulations": proc_info["regulations"],
                })
                break  # Only add each type once
    
    return requirements


def create_regulatory_scout_agent() -> Agent:
    """
    Create a Regulatory Scout agent.
    
    This agent analyzes research protocols to identify:
    - USDA pain category
    - Applicable regulations
    - Species-specific requirements
    - Permit requirements
    
    Returns:
        Configured CrewAI Agent instance.
    """
    llm = get_llm()
    pain_tool = PainCategoryTool()
    rag_tool = RegulatorySearchTool()
    
    return Agent(
        role="Regulatory Scout",
        goal=(
            "Thoroughly analyze research protocols to identify all applicable "
            "regulations, determine the correct USDA pain category, and flag "
            "any permit requirements or special considerations."
        ),
        backstory=(
            "You are an experienced IACUC coordinator with deep knowledge of "
            "federal regulations including the Animal Welfare Act, PHS Policy, "
            "and The Guide. You've reviewed thousands of protocols and know "
            "exactly what regulatory requirements apply to different types of "
            "research. You're meticulous about ensuring researchers understand "
            "all applicable rules and never miss a permit requirement."
        ),
        llm=llm,
        tools=[pain_tool, rag_tool],
        verbose=False,
        allow_delegation=False,
    )


def create_regulatory_scout_task(
    agent: Agent,
    species: str,
    procedures: str,
) -> Task:
    """
    Create a task for the Regulatory Scout agent.
    
    Args:
        agent: The Regulatory Scout agent
        species: Species being used
        procedures: Description of procedures
        
    Returns:
        Configured CrewAI Task instance.
    """
    return Task(
        description=f"""
Analyze this research protocol and identify all regulatory requirements:

SPECIES: {species}
PROCEDURES: {procedures}

Your analysis must include:

1. PAIN CATEGORY: Use the pain_category_classifier tool to determine the USDA pain category.

2. SPECIES REGULATIONS: Identify whether this species is:
   - USDA covered (requires AWA compliance)
   - USDA exempt (mice, rats, birds, fish - still require IACUC/PHS)
   - Wildlife (may require permits)

3. APPLICABLE REGULATIONS: Search the regulatory knowledge base for:
   - Requirements specific to the procedures described
   - Species-specific housing and care requirements
   - Any special permits or approvals needed

4. PERMIT REQUIREMENTS: Flag if any of these are needed:
   - DEA registration (controlled substances)
   - IBC approval (biohazards)
   - Radiation safety approval
   - Wildlife permits

Provide a comprehensive regulatory summary with specific citations where possible.
""",
        expected_output=(
            "A comprehensive regulatory analysis including pain category, "
            "species classification, applicable regulations with citations, "
            "and any permit requirements."
        ),
        agent=agent,
    )


def analyze_protocol_regulations(
    species: str,
    procedures: str,
    verbose: bool = False,
) -> dict:
    """
    Analyze a protocol for regulatory requirements.
    
    This is the main entry point for regulatory analysis.
    
    Args:
        species: Species being used
        procedures: Description of procedures
        verbose: Whether to show agent reasoning
        
    Returns:
        Dictionary containing regulatory analysis results.
    """
    # Get quick assessments
    species_info = identify_species_category(species)
    procedure_reqs = identify_procedure_requirements(procedures)
    pain_category = classify_pain_category(procedures)
    
    # Create agent for detailed analysis
    agent = create_regulatory_scout_agent()
    if verbose:
        agent.verbose = True
    
    task = create_regulatory_scout_task(agent, species, procedures)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=verbose,
    )
    
    # Run the analysis
    agent_result = crew.kickoff()
    
    return {
        "species": species,
        "species_category": species_info,
        "pain_category": {
            "category": pain_category.category,
            "name": pain_category.category_name,
            "confidence": pain_category.confidence,
            "requires_justification": pain_category.requires_justification,
        },
        "procedure_requirements": procedure_reqs,
        "detailed_analysis": str(agent_result),
    }


# Quick analysis without LLM (for testing/fast results)
def quick_regulatory_check(species: str, procedures: str) -> dict:
    """
    Perform quick regulatory check without LLM calls.
    
    Useful for testing or when fast results are needed.
    
    Args:
        species: Species being used
        procedures: Description of procedures
        
    Returns:
        Dictionary with basic regulatory info.
    """
    species_info = identify_species_category(species)
    procedure_reqs = identify_procedure_requirements(procedures)
    pain_result = classify_pain_category(procedures)
    
    return {
        "species": species,
        "species_category": species_info["category"],
        "species_requirements": species_info["requirements"],
        "pain_category": pain_result.category,
        "pain_category_name": pain_result.category_name,
        "requires_justification": pain_result.requires_justification,
        "procedure_requirements": procedure_reqs,
        "recommendations": pain_result.recommendations,
    }
