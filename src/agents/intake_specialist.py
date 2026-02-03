"""
Intake Specialist Agent.

An agent that extracts research parameters from unstructured descriptions,
identifies gaps, and generates a structured research profile.
"""

from typing import Optional

from crewai import Agent, Task, Crew
from pydantic import BaseModel, Field

from src.agents.llm import get_llm
from src.tools.research_classifier import ResearchClassifierTool, classify_research


class ResearchProfile(BaseModel):
    """Structured research profile extracted from description."""
    
    # Basic info
    title: Optional[str] = Field(default=None, description="Project title")
    pi_name: Optional[str] = Field(default=None, description="Principal Investigator")
    
    # Species info
    species: Optional[str] = Field(default=None, description="Species to be used")
    strain: Optional[str] = Field(default=None, description="Strain/stock")
    source: Optional[str] = Field(default=None, description="Animal source/vendor")
    
    # Numbers
    total_animals: Optional[int] = Field(default=None, description="Total animals requested")
    animals_per_group: Optional[int] = Field(default=None, description="Animals per experimental group")
    number_of_groups: Optional[int] = Field(default=None, description="Number of groups")
    
    # Procedures
    procedures: list[str] = Field(default_factory=list, description="Procedures to be performed")
    anesthesia_method: Optional[str] = Field(default=None, description="Anesthesia method")
    analgesia_method: Optional[str] = Field(default=None, description="Analgesia method")
    euthanasia_method: Optional[str] = Field(default=None, description="Euthanasia method")
    
    # Study design
    study_duration: Optional[str] = Field(default=None, description="Duration of study")
    primary_endpoint: Optional[str] = Field(default=None, description="Primary endpoint")
    
    # Classification
    research_type: Optional[str] = Field(default=None, description="Research type classification")
    pain_category: Optional[str] = Field(default=None, description="Estimated pain category")
    
    # Completeness
    completeness_score: float = Field(default=0.0, description="Profile completeness 0-1")
    missing_fields: list[str] = Field(default_factory=list, description="Required fields not found")


class ClarifyingQuestion(BaseModel):
    """A clarifying question to fill in missing information."""
    
    field: str = Field(description="Field this question addresses")
    question: str = Field(description="The question to ask")
    priority: str = Field(description="Priority: required, recommended, optional")
    example_answer: Optional[str] = Field(default=None, description="Example of expected answer")


# Required fields for a complete protocol
REQUIRED_FIELDS = [
    "species",
    "total_animals",
    "procedures",
    "euthanasia_method",
]

RECOMMENDED_FIELDS = [
    "strain",
    "source",
    "animals_per_group",
    "number_of_groups",
    "anesthesia_method",
    "analgesia_method",
    "study_duration",
    "primary_endpoint",
]

# Question templates for missing fields
QUESTION_TEMPLATES = {
    "species": {
        "question": "What species will be used in this study?",
        "priority": "required",
        "example": "C57BL/6 mice",
    },
    "strain": {
        "question": "What strain or stock will be used?",
        "priority": "recommended",
        "example": "C57BL/6J or CD-1",
    },
    "source": {
        "question": "Where will the animals be obtained from?",
        "priority": "recommended",
        "example": "Jackson Labs, Charles River, or in-house breeding",
    },
    "total_animals": {
        "question": "How many animals are needed in total for this study?",
        "priority": "required",
        "example": "60 animals total",
    },
    "animals_per_group": {
        "question": "How many animals will be in each experimental group?",
        "priority": "recommended",
        "example": "10 animals per group",
    },
    "number_of_groups": {
        "question": "How many experimental groups will there be?",
        "priority": "recommended",
        "example": "6 groups (1 control + 5 treatment)",
    },
    "procedures": {
        "question": "What procedures will be performed on the animals?",
        "priority": "required",
        "example": "Survival surgery, weekly blood collection, behavioral testing",
    },
    "anesthesia_method": {
        "question": "What anesthesia will be used for procedures requiring it?",
        "priority": "recommended",
        "example": "Isoflurane inhalation or ketamine/xylazine injection",
    },
    "analgesia_method": {
        "question": "What analgesia will be provided for painful procedures?",
        "priority": "recommended",
        "example": "Buprenorphine 0.1 mg/kg SC pre- and post-procedure",
    },
    "euthanasia_method": {
        "question": "What euthanasia method will be used?",
        "priority": "required",
        "example": "CO2 inhalation followed by cervical dislocation",
    },
    "study_duration": {
        "question": "How long will the study last?",
        "priority": "recommended",
        "example": "8 weeks from first procedure to euthanasia",
    },
    "primary_endpoint": {
        "question": "What is the primary endpoint or outcome measure?",
        "priority": "recommended",
        "example": "Tumor volume at day 21",
    },
}


def extract_research_profile(description: str) -> ResearchProfile:
    """
    Extract a research profile from an unstructured description.
    
    Args:
        description: Unstructured research description
        
    Returns:
        Extracted ResearchProfile.
    """
    profile = ResearchProfile()
    description_lower = description.lower()
    
    # Try to extract species
    species_keywords = {
        "mice": "mouse", "mouse": "mouse",
        "rats": "rat", "rat": "rat",
        "rabbits": "rabbit", "rabbit": "rabbit",
        "guinea pigs": "guinea pig", "guinea pig": "guinea pig",
        "hamsters": "hamster", "hamster": "hamster",
        "dogs": "dog", "dog": "dog",
        "cats": "cat", "cat": "cat",
        "primates": "primate", "primate": "primate",
        "zebrafish": "zebrafish", "fish": "fish",
    }
    
    for keyword, species in species_keywords.items():
        if keyword in description_lower:
            profile.species = species
            break
    
    # Try to extract strain
    strains = ["c57bl/6", "balb/c", "cd-1", "sprague dawley", "wistar", 
               "new zealand white", "nude", "scid", "nod"]
    for strain in strains:
        if strain in description_lower:
            profile.strain = strain.upper() if len(strain) <= 5 else strain.title()
            break
    
    # Try to extract numbers
    import re
    
    # Look for patterns like "N=10", "n = 20", "10 animals", "20 mice"
    number_patterns = [
        r'n\s*=\s*(\d+)',
        r'(\d+)\s*(?:animals|mice|rats|subjects)',
        r'total\s*(?:of\s*)?(\d+)',
        r'(\d+)\s*per\s*group',
        r'(\d+)\s*groups?',
    ]
    
    for pattern in number_patterns[:3]:  # Total animals patterns
        match = re.search(pattern, description_lower)
        if match:
            profile.total_animals = int(match.group(1))
            break
    
    # Animals per group
    per_group_match = re.search(r'(\d+)\s*(?:per\s*group|/group|each\s*group)', description_lower)
    if per_group_match:
        profile.animals_per_group = int(per_group_match.group(1))
    
    # Number of groups
    groups_match = re.search(r'(\d+)\s*groups?', description_lower)
    if groups_match:
        profile.number_of_groups = int(groups_match.group(1))
    
    # Extract procedures
    procedure_keywords = {
        "surgery": "Surgery",
        "injection": "Injection",
        "blood collection": "Blood collection",
        "behavioral": "Behavioral testing",
        "imaging": "Imaging",
        "tumor": "Tumor implantation",
        "euthanasia": "Euthanasia",
    }
    
    for keyword, procedure in procedure_keywords.items():
        if keyword in description_lower:
            profile.procedures.append(procedure)
    
    # Extract anesthesia
    anesthesia_keywords = ["isoflurane", "ketamine", "pentobarbital", "anesthesia"]
    for kw in anesthesia_keywords:
        if kw in description_lower:
            profile.anesthesia_method = kw.title()
            break
    
    # Extract analgesia
    analgesia_keywords = ["buprenorphine", "carprofen", "meloxicam", "analgesia"]
    for kw in analgesia_keywords:
        if kw in description_lower:
            profile.analgesia_method = kw.title()
            break
    
    # Extract euthanasia
    euthanasia_keywords = ["co2", "carbon dioxide", "decapitation", "cervical dislocation", 
                          "pentobarbital overdose"]
    for kw in euthanasia_keywords:
        if kw in description_lower:
            profile.euthanasia_method = kw.title()
            break
    
    # Classify research
    if profile.species:
        classification = classify_research(description, profile.species)
        profile.research_type = classification.research_type
        profile.pain_category = classification.pain_category_estimate
    
    # Calculate completeness
    profile = calculate_completeness(profile)
    
    return profile


def calculate_completeness(profile: ResearchProfile) -> ResearchProfile:
    """
    Calculate completeness score and identify missing fields.
    
    Args:
        profile: Research profile to evaluate
        
    Returns:
        Profile with completeness_score and missing_fields populated.
    """
    missing = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        value = getattr(profile, field)
        if value is None or (isinstance(value, list) and len(value) == 0):
            missing.append(field)
    
    # Check recommended fields
    for field in RECOMMENDED_FIELDS:
        value = getattr(profile, field)
        if value is None:
            missing.append(field)
    
    total_fields = len(REQUIRED_FIELDS) + len(RECOMMENDED_FIELDS)
    filled_fields = total_fields - len(missing)
    
    profile.completeness_score = filled_fields / total_fields
    profile.missing_fields = missing
    
    return profile


def generate_clarifying_questions(profile: ResearchProfile) -> list[ClarifyingQuestion]:
    """
    Generate clarifying questions for missing information.
    
    Args:
        profile: Research profile with missing fields
        
    Returns:
        List of clarifying questions.
    """
    questions = []
    
    for field in profile.missing_fields:
        if field in QUESTION_TEMPLATES:
            template = QUESTION_TEMPLATES[field]
            questions.append(ClarifyingQuestion(
                field=field,
                question=template["question"],
                priority=template["priority"],
                example_answer=template.get("example"),
            ))
    
    # Sort by priority
    priority_order = {"required": 0, "recommended": 1, "optional": 2}
    questions.sort(key=lambda q: priority_order.get(q.priority, 2))
    
    return questions


def create_intake_specialist_agent() -> Agent:
    """
    Create an Intake Specialist agent.
    
    This agent:
    - Parses unstructured research descriptions
    - Extracts key parameters
    - Generates clarifying questions
    - Creates structured research profiles
    
    Returns:
        Configured CrewAI Agent instance.
    """
    llm = get_llm()
    classifier_tool = ResearchClassifierTool()
    
    return Agent(
        role="Intake Specialist",
        goal=(
            "Extract comprehensive research parameters from unstructured "
            "descriptions. Identify all key information needed for an IACUC "
            "protocol, note what's missing, and generate targeted clarifying "
            "questions to fill gaps."
        ),
        backstory=(
            "You are an experienced IACUC protocol coordinator who has "
            "processed hundreds of submissions. You're skilled at extracting "
            "key information from researchers' often incomplete descriptions. "
            "You know exactly what information is needed for a complete protocol "
            "and can quickly identify gaps. You ask focused, specific questions "
            "to get the missing details without overwhelming the researcher."
        ),
        llm=llm,
        tools=[classifier_tool],
        verbose=False,
        allow_delegation=False,
    )


def create_intake_task(
    agent: Agent,
    research_description: str,
) -> Task:
    """
    Create an intake task.
    
    Args:
        agent: The Intake Specialist agent
        research_description: Unstructured research description
        
    Returns:
        Configured CrewAI Task instance.
    """
    return Task(
        description=f"""
Process this research description and create a structured profile:

RESEARCH DESCRIPTION:
{research_description}

Your task:

1. EXTRACT INFORMATION:
   - Species and strain
   - Number of animals (total, per group, number of groups)
   - Procedures to be performed
   - Anesthesia and analgesia plans
   - Euthanasia method
   - Study duration and endpoints

2. CLASSIFY THE RESEARCH:
   - Use the research_classifier tool to identify research type
   - Note any special requirements (DEA, IBC, etc.)
   - Estimate pain category

3. IDENTIFY GAPS:
   - List all required information that is missing
   - List recommended information that would strengthen the protocol

4. GENERATE QUESTIONS:
   - Create specific, focused questions for each gap
   - Prioritize questions (required info first)
   - Provide examples of expected answers

Output a comprehensive intake summary with all extracted information and prioritized questions.
""",
        expected_output=(
            "A structured research profile with extracted information, "
            "identified gaps, and prioritized clarifying questions."
        ),
        agent=agent,
    )


def process_intake(
    research_description: str,
    verbose: bool = False,
) -> dict:
    """
    Process a research description through intake.
    
    Main entry point for intake processing.
    
    Args:
        research_description: Unstructured research description
        verbose: Whether to show agent reasoning
        
    Returns:
        Dictionary with intake results.
    """
    # Create agent and task
    agent = create_intake_specialist_agent()
    if verbose:
        agent.verbose = True
    
    task = create_intake_task(agent, research_description)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=verbose,
    )
    
    # Run intake
    agent_result = crew.kickoff()
    
    # Get quick extraction
    profile = extract_research_profile(research_description)
    questions = generate_clarifying_questions(profile)
    
    return {
        "profile": profile.model_dump(),
        "clarifying_questions": [q.model_dump() for q in questions],
        "completeness_score": profile.completeness_score,
        "detailed_analysis": str(agent_result),
    }


# Quick intake without LLM
def quick_intake(research_description: str) -> dict:
    """
    Quick intake processing without LLM calls.
    
    Args:
        research_description: Unstructured research description
        
    Returns:
        Dictionary with quick intake results.
    """
    profile = extract_research_profile(research_description)
    questions = generate_clarifying_questions(profile)
    
    return {
        "profile": profile.model_dump(),
        "clarifying_questions": [q.model_dump() for q in questions],
        "completeness_score": profile.completeness_score,
        "required_questions": [q.model_dump() for q in questions if q.priority == "required"],
        "missing_required": [f for f in profile.missing_fields if f in REQUIRED_FIELDS],
    }


# Export key items
__all__ = [
    "create_intake_specialist_agent",
    "create_intake_task",
    "process_intake",
    "quick_intake",
    "extract_research_profile",
    "generate_clarifying_questions",
    "calculate_completeness",
    "ResearchProfile",
    "ClarifyingQuestion",
    "REQUIRED_FIELDS",
    "RECOMMENDED_FIELDS",
]
