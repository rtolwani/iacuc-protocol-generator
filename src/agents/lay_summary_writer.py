"""
Lay Summary Writer Agent.

An agent that simplifies technical research descriptions into
accessible lay summaries for non-scientific audiences.
"""

from crewai import Agent, Task, Crew

from src.agents.llm import get_llm
from src.tools.readability_tools import ReadabilityScoreTool, analyze_readability


def create_lay_summary_writer_agent() -> Agent:
    """
    Create a Lay Summary Writer agent.
    
    This agent takes technical research descriptions and rewrites them
    at a 7th grade reading level or below, ensuring they are accessible
    to the general public.
    
    Returns:
        Configured CrewAI Agent instance.
    """
    llm = get_llm()
    readability_tool = ReadabilityScoreTool()
    
    return Agent(
        role="Lay Summary Writer",
        goal=(
            "Transform technical research descriptions into clear, accessible "
            "summaries that educated readers can understand. Target a college "
            "reading level (Flesch-Kincaid grade ≤ 14.0) while preserving the "
            "essential meaning and purpose of the research."
        ),
        backstory=(
            "You are an expert science communicator with years of experience "
            "translating complex scientific concepts for educated lay audiences. "
            "You understand that IACUC summaries should be readable by "
            "committee members and educated community representatives. You have "
            "a gift for clarifying dense scientific writing while maintaining "
            "appropriate technical accuracy. You know that clarity and precision "
            "must be balanced in effective summaries."
        ),
        llm=llm,
        tools=[readability_tool],
        verbose=False,
        allow_delegation=False,
    )


def create_lay_summary_task(
    agent: Agent,
    technical_text: str,
    max_iterations: int = 3,
) -> Task:
    """
    Create a task for the Lay Summary Writer agent.
    
    Args:
        agent: The Lay Summary Writer agent
        technical_text: The technical text to simplify
        max_iterations: Maximum rewrite attempts
        
    Returns:
        Configured CrewAI Task instance.
    """
    return Task(
        description=f"""
Transform the following technical research description into an accessible summary:

---
{technical_text}
---

REQUIREMENTS:
1. Use the readability_score tool to check your summary
2. The summary MUST have a Flesch-Kincaid grade of 14.0 or below (college level)
3. Keep the summary concise (3-5 sentences is ideal)
4. Preserve the essential purpose and meaning of the research
5. Clarify overly technical jargon but maintain appropriate scientific terms
6. Use clear, well-structured sentences
7. Prefer active voice when possible

PROCESS:
1. First, write a clearer version of the summary
2. Use the readability_score tool to check it
3. If it fails (grade > 14.0), rewrite to improve clarity
4. Repeat until it passes or you've tried {max_iterations} times

Your final answer should be ONLY the summary text that passes the readability check.
Do not include the readability scores or any other metadata - just the summary itself.
""",
        expected_output=(
            "A clear, accessible summary at college reading level (grade 14 or below), "
            "written in 3-5 well-structured sentences with appropriate scientific terminology."
        ),
        agent=agent,
    )


def generate_lay_summary(
    technical_text: str,
    max_iterations: int = 3,
    verbose: bool = False,
) -> dict:
    """
    Generate a lay summary from technical text.
    
    This is the main entry point for generating lay summaries.
    
    Args:
        technical_text: The technical research description to simplify
        max_iterations: Maximum rewrite attempts
        verbose: Whether to show agent reasoning
        
    Returns:
        Dictionary containing:
        - summary: The generated lay summary
        - readability: Readability analysis of the summary
        - passes: Whether the summary meets the grade 7 target
    """
    # Create agent and task
    agent = create_lay_summary_writer_agent()
    if verbose:
        agent.verbose = True
    
    task = create_lay_summary_task(agent, technical_text, max_iterations)
    
    # Create and run crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=verbose,
    )
    
    result = crew.kickoff()
    
    # Get the summary text
    summary = str(result).strip()
    
    # Analyze final readability
    readability = analyze_readability(summary, target_grade=14.0)
    
    return {
        "summary": summary,
        "readability": {
            "grade": readability.flesch_kincaid_grade,
            "ease": readability.flesch_reading_ease,
            "word_count": readability.word_count,
            "sentence_count": readability.sentence_count,
        },
        "passes": readability.passes_target,
    }


# Example technical texts for testing
EXAMPLE_TECHNICAL_TEXTS = {
    "behavioral": """
    This protocol investigates the effects of chronic stress paradigms on 
    cognitive function in C57BL/6J mice utilizing a battery of behavioral 
    assessments including the Morris water maze for spatial memory, the 
    elevated plus maze for anxiety-related behaviors, and novel object 
    recognition for working memory. Animals will be subjected to chronic 
    unpredictable mild stress (CUMS) for 28 days, following which behavioral 
    testing will be conducted. Tissue will be harvested for subsequent 
    immunohistochemical and molecular analyses.
    """,
    
    "surgical": """
    The proposed research involves bilateral stereotaxic injection of 
    adeno-associated viral vectors (AAV) into the hippocampal formation 
    of adult Sprague-Dawley rats for optogenetic manipulation of specific 
    neuronal populations. Animals will undergo survival surgery under 
    isoflurane anesthesia with pre-operative carprofen administration. 
    Post-operative monitoring will occur daily for 7 days, with animals 
    remaining in study for up to 8 weeks prior to terminal procedures.
    """,
    
    "tumor_model": """
    This study employs a syngeneic orthotopic tumor model utilizing 
    4T1 mammary carcinoma cells implanted into the fourth mammary fat 
    pad of BALB/c mice. Tumor progression will be monitored via caliper 
    measurements and bioluminescence imaging. Animals will receive 
    experimental therapeutics via intraperitoneal injection on a q3d 
    schedule. Humane endpoints include tumor burden exceeding 2000mm³ 
    or significant deterioration in body condition score.
    """,
}
