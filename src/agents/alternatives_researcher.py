"""
Alternatives Researcher Agent.

An agent that generates 3Rs (Replacement, Reduction, Refinement) documentation
for IACUC protocols, including literature search documentation.
"""

from crewai import Agent, Task, Crew

from src.agents.llm import get_llm
from src.tools.literature_search_tool import (
    LiteratureSearchTool,
    generate_search_keywords,
    create_search_documentation,
)
from src.tools.rag_tools import RegulatorySearchTool


# 3Rs Framework Definitions
THREE_RS_DEFINITIONS = {
    "replacement": {
        "definition": (
            "Methods that avoid or replace the use of animals in research. "
            "Includes absolute replacement (non-animal methods) and relative "
            "replacement (using less sentient species)."
        ),
        "examples": [
            "In vitro cell/tissue cultures",
            "Computer modeling and simulation",
            "Organ-on-a-chip technology",
            "Human volunteers (when appropriate)",
            "Lower organisms (invertebrates)",
            "Microorganisms",
        ],
        "questions": [
            "Can this study be done without animals?",
            "Are there validated non-animal methods?",
            "Could a lower phylogenetic species be used?",
        ],
    },
    "reduction": {
        "definition": (
            "Methods that minimize the number of animals used while obtaining "
            "valid scientific results. Includes optimal experimental design "
            "and data sharing."
        ),
        "examples": [
            "Power analysis for sample size",
            "Pilot studies",
            "Improved experimental design",
            "Sharing animals between studies",
            "Using published data",
            "Non-invasive imaging (repeated measures)",
        ],
        "questions": [
            "What is the minimum number needed for statistical validity?",
            "Can animals serve as their own controls?",
            "Are there existing datasets that could be used?",
        ],
    },
    "refinement": {
        "definition": (
            "Methods that minimize pain, suffering, distress, and lasting harm "
            "while improving animal welfare throughout the study."
        ),
        "examples": [
            "Appropriate anesthesia and analgesia",
            "Humane endpoints",
            "Environmental enrichment",
            "Training animals to cooperate",
            "Non-invasive monitoring",
            "Improved surgical techniques",
        ],
        "questions": [
            "What anesthesia/analgesia will be used?",
            "Are humane endpoints defined?",
            "How will distress be monitored?",
        ],
    },
}


def generate_3rs_template(
    animal_model: str,
    procedures: str,
) -> dict:
    """
    Generate a 3Rs documentation template.
    
    Args:
        animal_model: Species being used
        procedures: Description of procedures
        
    Returns:
        Dictionary with 3Rs template sections
    """
    keywords = generate_search_keywords(animal_model, procedures)
    
    return {
        "animal_model": animal_model,
        "procedures": procedures,
        "replacement": {
            "search_conducted": False,
            "databases_searched": [],
            "keywords_used": keywords["replacement"],
            "alternatives_found": [],
            "justification": "",
        },
        "reduction": {
            "method": "",
            "sample_size_justification": "",
            "statistical_approach": "",
            "keywords_used": keywords["reduction"],
        },
        "refinement": {
            "anesthesia_plan": "",
            "analgesia_plan": "",
            "humane_endpoints": [],
            "monitoring_plan": "",
            "keywords_used": keywords["refinement"],
        },
    }


def create_alternatives_researcher_agent() -> Agent:
    """
    Create an Alternatives Researcher agent.
    
    This agent:
    - Searches for replacement alternatives
    - Documents reduction strategies
    - Identifies refinement methods
    - Generates USDA-compliant documentation
    
    Returns:
        Configured CrewAI Agent instance.
    """
    llm = get_llm()
    lit_search_tool = LiteratureSearchTool()
    rag_tool = RegulatorySearchTool()
    
    return Agent(
        role="Alternatives Researcher",
        goal=(
            "Thoroughly research and document alternatives to animal use (3Rs) "
            "for IACUC protocols. Generate USDA-compliant literature search "
            "documentation and identify replacement, reduction, and refinement "
            "strategies."
        ),
        backstory=(
            "You are an expert in the 3Rs of animal research ethics - Replacement, "
            "Reduction, and Refinement. You have extensive knowledge of alternative "
            "methods, in vitro technologies, and experimental design. You understand "
            "USDA requirements for alternatives documentation and can identify "
            "appropriate methods to minimize animal use while achieving scientific "
            "objectives. You're committed to animal welfare and ensuring protocols "
            "meet the highest ethical standards."
        ),
        llm=llm,
        tools=[lit_search_tool, rag_tool],
        verbose=False,
        allow_delegation=False,
    )


def create_alternatives_research_task(
    agent: Agent,
    animal_model: str,
    procedures: str,
    study_objectives: str,
) -> Task:
    """
    Create a task for alternatives research.
    
    Args:
        agent: The Alternatives Researcher agent
        animal_model: Species being used
        procedures: Description of procedures
        study_objectives: Scientific objectives of the study
        
    Returns:
        Configured CrewAI Task instance.
    """
    return Task(
        description=f"""
Research and document alternatives for this IACUC protocol:

ANIMAL MODEL: {animal_model}
PROCEDURES: {procedures}
STUDY OBJECTIVES: {study_objectives}

Your research must address all 3Rs:

1. REPLACEMENT:
   - Use the literature_search_documentation tool to generate search keywords
   - Identify if any non-animal alternatives exist
   - If no replacement possible, provide scientific justification
   - Consider: in vitro methods, computer models, lower organisms

2. REDUCTION:
   - Evaluate the experimental design
   - Recommend statistical approaches for minimum animal numbers
   - Identify ways to reduce animal use (pilot studies, shared controls, etc.)
   - Justify the proposed sample size

3. REFINEMENT:
   - Search regulatory guidance for species-specific refinements
   - Recommend anesthesia and analgesia protocols
   - Suggest humane endpoints and monitoring criteria
   - Identify ways to minimize pain and distress

Provide a comprehensive 3Rs analysis with specific recommendations.
""",
        expected_output=(
            "A detailed 3Rs analysis covering replacement alternatives searched, "
            "reduction strategies with sample size justification, and refinement "
            "methods with specific welfare recommendations."
        ),
        agent=agent,
    )


def research_alternatives(
    animal_model: str,
    procedures: str,
    study_objectives: str,
    verbose: bool = False,
) -> dict:
    """
    Research alternatives for a protocol.
    
    Main entry point for alternatives research.
    
    Args:
        animal_model: Species being used
        procedures: Description of procedures
        study_objectives: Scientific objectives
        verbose: Whether to show agent reasoning
        
    Returns:
        Dictionary with 3Rs analysis results.
    """
    # Generate template
    template = generate_3rs_template(animal_model, procedures)
    
    # Create agent and task
    agent = create_alternatives_researcher_agent()
    if verbose:
        agent.verbose = True
    
    task = create_alternatives_research_task(
        agent, animal_model, procedures, study_objectives
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=verbose,
    )
    
    # Run the research
    agent_result = crew.kickoff()
    
    return {
        "animal_model": animal_model,
        "procedures": procedures,
        "study_objectives": study_objectives,
        "template": template,
        "detailed_analysis": str(agent_result),
    }


# Quick 3Rs check without LLM
def quick_3rs_check(
    animal_model: str,
    procedures: str,
) -> dict:
    """
    Quick 3Rs assessment without LLM calls.
    
    Useful for testing or when fast results are needed.
    
    Args:
        animal_model: Species being used
        procedures: Description of procedures
        
    Returns:
        Dictionary with 3Rs keywords and template.
    """
    keywords = generate_search_keywords(animal_model, procedures)
    template = generate_3rs_template(animal_model, procedures)
    
    # Generate basic recommendations
    procedures_lower = procedures.lower()
    
    refinement_recommendations = []
    if "surgery" in procedures_lower:
        refinement_recommendations.extend([
            "Use appropriate anesthesia for all surgical procedures",
            "Provide post-operative analgesia",
            "Monitor for signs of pain using validated scoring system",
        ])
    
    if "tumor" in procedures_lower:
        refinement_recommendations.extend([
            "Define tumor size limits as humane endpoints",
            "Monitor body weight and condition daily",
            "Euthanize animals showing signs of distress",
        ])
    
    if not refinement_recommendations:
        refinement_recommendations = [
            "Consider environmental enrichment",
            "Minimize handling stress through habituation",
            "Define humane endpoints appropriate to the study",
        ]
    
    return {
        "animal_model": animal_model,
        "procedures": procedures,
        "replacement_keywords": keywords["replacement"],
        "reduction_keywords": keywords["reduction"],
        "refinement_keywords": keywords["refinement"],
        "refinement_recommendations": refinement_recommendations,
        "template": template,
        "databases_to_search": ["PubMed/MEDLINE", "AGRICOLA", "AWIC"],
    }


# Export key items
__all__ = [
    "create_alternatives_researcher_agent",
    "create_alternatives_research_task",
    "research_alternatives",
    "quick_3rs_check",
    "generate_3rs_template",
    "THREE_RS_DEFINITIONS",
]
