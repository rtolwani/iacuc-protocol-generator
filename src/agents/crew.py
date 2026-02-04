"""
Complete IACUC Protocol Generation Crew.

Orchestrates all 8 agents to generate a complete IACUC protocol.
"""

from typing import Optional

from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field

from src.agents.llm import get_llm

# Import all agents
from src.agents.lay_summary_writer import create_lay_summary_writer_agent, create_lay_summary_task
from src.agents.regulatory_scout import create_regulatory_scout_agent, create_regulatory_scout_task
from src.agents.alternatives_researcher import create_alternatives_researcher_agent, create_alternatives_research_task
from src.agents.statistical_consultant import create_statistical_consultant_agent, create_statistical_review_task
from src.agents.veterinary_reviewer import create_veterinary_reviewer_agent, create_veterinary_review_task
from src.agents.procedure_writer import create_procedure_writer_agent, create_procedure_writing_task
from src.agents.intake_specialist import create_intake_specialist_agent, create_intake_task
from src.agents.protocol_assembler import create_protocol_assembler_agent, create_assembly_task


class ProtocolInput(BaseModel):
    """Input for protocol generation."""
    
    title: str = Field(description="Protocol title")
    pi_name: str = Field(description="Principal Investigator name")
    species: str = Field(description="Species to be used")
    strain: Optional[str] = Field(default=None, description="Strain/stock")
    total_animals: int = Field(description="Total number of animals")
    research_description: str = Field(description="Description of the research")
    procedures: str = Field(description="Procedures to be performed")
    study_duration: Optional[str] = Field(default=None, description="Duration of study")
    primary_endpoint: Optional[str] = Field(default=None, description="Primary outcome measure")


class CrewResult(BaseModel):
    """Result from crew execution."""
    
    success: bool = Field(default=False)
    protocol_sections: dict = Field(default_factory=dict)
    agent_outputs: dict = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


def create_all_agents() -> dict[str, Agent]:
    """
    Create all 8 agents for the crew.
    
    Returns:
        Dictionary of agent name to Agent instance.
    """
    return {
        "intake_specialist": create_intake_specialist_agent(),
        "regulatory_scout": create_regulatory_scout_agent(),
        "lay_summary_writer": create_lay_summary_writer_agent(),
        "alternatives_researcher": create_alternatives_researcher_agent(),
        "statistical_consultant": create_statistical_consultant_agent(),
        "veterinary_reviewer": create_veterinary_reviewer_agent(),
        "procedure_writer": create_procedure_writer_agent(),
        "protocol_assembler": create_protocol_assembler_agent(),
    }


def create_protocol_tasks(
    agents: dict[str, Agent],
    protocol_input: ProtocolInput,
) -> list[Task]:
    """
    Create all tasks for protocol generation.
    
    Tasks are ordered with dependencies:
    1. Intake Specialist - Extracts parameters
    2. Regulatory Scout - Identifies regulations
    3. Lay Summary Writer - Creates lay summary
    4. Alternatives Researcher - Documents 3Rs
    5. Statistical Consultant - Reviews statistics
    6. Veterinary Reviewer - Reviews welfare
    7. Procedure Writer - Writes procedures
    8. Protocol Assembler - Compiles document
    
    Args:
        agents: Dictionary of agents
        protocol_input: Input for protocol generation
        
    Returns:
        List of tasks in execution order.
    """
    # Build description string
    full_description = f"""
Title: {protocol_input.title}
PI: {protocol_input.pi_name}
Species: {protocol_input.species}
{f"Strain: {protocol_input.strain}" if protocol_input.strain else ""}
Total Animals: {protocol_input.total_animals}
{f"Study Duration: {protocol_input.study_duration}" if protocol_input.study_duration else ""}
{f"Primary Endpoint: {protocol_input.primary_endpoint}" if protocol_input.primary_endpoint else ""}

Research Description:
{protocol_input.research_description}

Procedures:
{protocol_input.procedures}
"""
    
    # Task 1: Intake Specialist
    task_intake = Task(
        description=f"""
Process this research description and extract all key parameters:

{full_description}

Extract:
- Species and strain information
- Number of animals and groups
- All procedures to be performed
- Pain category estimate
- Special requirements (DEA, IBC, etc.)
- Any missing information that needs clarification

Output a structured research profile.
""",
        expected_output="Structured research profile with all extracted parameters",
        agent=agents["intake_specialist"],
    )
    
    # Task 2: Regulatory Scout
    task_regulatory = Task(
        description=f"""
Based on the research profile from the Intake Specialist, identify all applicable regulations.

Species: {protocol_input.species}
Procedures: {protocol_input.procedures}

Identify:
- USDA pain category (B, C, D, or E)
- Applicable regulations (USDA AWA, PHS Policy, etc.)
- Required permits or approvals (DEA, IBC, etc.)
- Species-specific requirements
- Any regulatory flags or concerns
""",
        expected_output="Regulatory assessment with pain category and applicable requirements",
        agent=agents["regulatory_scout"],
        context=[task_intake],
    )
    
    # Task 3: Lay Summary Writer
    task_lay_summary = Task(
        description=f"""
Write a lay summary for this research project that can be understood by non-scientists.

Title: {protocol_input.title}
Research Description: {protocol_input.research_description}

The summary should:
- Be written at a college reading level (grade 14)
- Avoid technical jargon
- Explain why animals are needed
- Describe what will happen in simple terms
- Be approximately 200-300 words
""",
        expected_output="Clear, accessible lay summary of the research",
        agent=agents["lay_summary_writer"],
        context=[task_intake],
    )
    
    # Task 4: Alternatives Researcher
    task_alternatives = Task(
        description=f"""
Document the alternatives search for the 3Rs (Replacement, Reduction, Refinement).

Species: {protocol_input.species}
Procedures: {protocol_input.procedures}

Document:
- Literature search strategy for alternatives
- Required databases (PubMed, AWIC, etc.)
- Keywords used
- Justification for why alternatives cannot be used
- Refinement measures to minimize pain/distress
- Reduction measures (sample size justification)
""",
        expected_output="Complete 3Rs documentation with search strategy",
        agent=agents["alternatives_researcher"],
        context=[task_regulatory],
    )
    
    # Task 5: Statistical Consultant
    task_statistics = Task(
        description=f"""
Review the statistical design for this study.

Total Animals: {protocol_input.total_animals}
Research Description: {protocol_input.research_description}

Provide:
- Recommended experimental design
- Power analysis justification for sample size
- Appropriate statistical tests
- Assessment of whether animal numbers are justified
- Recommendations if sample size seems too high or low
""",
        expected_output="Statistical review with power analysis and recommendations",
        agent=agents["statistical_consultant"],
        context=[task_intake],
    )
    
    # Task 6: Veterinary Reviewer
    task_veterinary = Task(
        description=f"""
Perform veterinary pre-review of this protocol.

Species: {protocol_input.species}
Procedures: {protocol_input.procedures}

Review:
- Welfare concerns for the procedures
- Recommended monitoring schedule
- Humane endpoints
- Pain management recommendations
- Drug dosing verification (if applicable)
- Housing and husbandry considerations
""",
        expected_output="Veterinary review with welfare recommendations and endpoints",
        agent=agents["veterinary_reviewer"],
        context=[task_regulatory, task_intake],
    )
    
    # Task 7: Procedure Writer
    task_procedures = Task(
        description=f"""
Write detailed procedure descriptions for this protocol.

Species: {protocol_input.species}
Procedures: {protocol_input.procedures}

Include:
- Step-by-step procedure descriptions
- Drug administration table (if applicable)
- Monitoring schedule
- Euthanasia method with AVMA compliance
- Emergency procedures
""",
        expected_output="Detailed procedure descriptions with drug tables and monitoring",
        agent=agents["procedure_writer"],
        context=[task_veterinary, task_regulatory],
    )
    
    # Task 8: Protocol Assembler
    task_assembly = Task(
        description=f"""
Compile all sections into a complete IACUC protocol document.

Protocol Title: {protocol_input.title}
PI: {protocol_input.pi_name}

Assemble the following sections from previous agent outputs:
1. Project Summary (from Lay Summary Writer)
2. Scientific Justification
3. Species and Numbers
4. Alternatives Search (from Alternatives Researcher)
5. Statistical Justification (from Statistical Consultant)
6. Procedures (from Procedure Writer)
7. Anesthesia and Analgesia
8. Monitoring and Endpoints (from Veterinary Reviewer)
9. Euthanasia
10. Personnel

Run consistency checks and generate a completeness report.
""",
        expected_output="Complete, validated IACUC protocol document",
        agent=agents["protocol_assembler"],
        context=[
            task_lay_summary,
            task_alternatives,
            task_statistics,
            task_procedures,
            task_veterinary,
        ],
    )
    
    return [
        task_intake,
        task_regulatory,
        task_lay_summary,
        task_alternatives,
        task_statistics,
        task_veterinary,
        task_procedures,
        task_assembly,
    ]


def create_protocol_crew(
    protocol_input: ProtocolInput,
    verbose: bool = False,
) -> Crew:
    """
    Create a crew for protocol generation.
    
    Args:
        protocol_input: Input for protocol generation
        verbose: Whether to show agent reasoning
        
    Returns:
        Configured Crew instance.
    """
    agents = create_all_agents()
    
    if verbose:
        for agent in agents.values():
            agent.verbose = True
    
    tasks = create_protocol_tasks(agents, protocol_input)
    
    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
    )


def generate_protocol(
    protocol_input: ProtocolInput,
    verbose: bool = False,
) -> CrewResult:
    """
    Generate a complete IACUC protocol.
    
    Main entry point for protocol generation.
    
    Args:
        protocol_input: Input for protocol generation
        verbose: Whether to show agent reasoning
        
    Returns:
        CrewResult with generated protocol.
    """
    try:
        crew = create_protocol_crew(protocol_input, verbose)
        result = crew.kickoff()
        
        # Extract results from each task
        agent_outputs = {}
        for i, task in enumerate(crew.tasks):
            task_name = [
                "intake", "regulatory", "lay_summary", "alternatives",
                "statistics", "veterinary", "procedures", "assembly"
            ][i]
            agent_outputs[task_name] = str(task.output) if task.output else ""
        
        # Build protocol sections
        protocol_sections = {
            "title": protocol_input.title,
            "pi_name": protocol_input.pi_name,
            "species": protocol_input.species,
            "total_animals": protocol_input.total_animals,
            "lay_summary": agent_outputs.get("lay_summary", ""),
            "regulatory_assessment": agent_outputs.get("regulatory", ""),
            "alternatives_documentation": agent_outputs.get("alternatives", ""),
            "statistical_justification": agent_outputs.get("statistics", ""),
            "veterinary_review": agent_outputs.get("veterinary", ""),
            "procedures": agent_outputs.get("procedures", ""),
            "final_protocol": agent_outputs.get("assembly", ""),
        }
        
        return CrewResult(
            success=True,
            protocol_sections=protocol_sections,
            agent_outputs=agent_outputs,
            errors=[],
        )
        
    except Exception as e:
        return CrewResult(
            success=False,
            protocol_sections={},
            agent_outputs={},
            errors=[str(e)],
        )


def quick_crew_check(protocol_input: ProtocolInput) -> dict:
    """
    Quick validation without running LLM calls.
    
    Validates input and shows what the crew would do.
    
    Args:
        protocol_input: Input for protocol generation
        
    Returns:
        Dictionary with validation results and task preview.
    """
    # Validate input
    validation_errors = []
    
    if not protocol_input.title:
        validation_errors.append("Protocol title is required")
    if not protocol_input.species:
        validation_errors.append("Species is required")
    if protocol_input.total_animals <= 0:
        validation_errors.append("Total animals must be positive")
    if not protocol_input.research_description:
        validation_errors.append("Research description is required")
    if not protocol_input.procedures:
        validation_errors.append("Procedures are required")
    
    # Create agents to show what would be used
    agents = create_all_agents()
    
    # Build task summary
    task_summary = [
        "1. Intake Specialist: Extract research parameters",
        "2. Regulatory Scout: Identify applicable regulations",
        "3. Lay Summary Writer: Create accessible summary",
        "4. Alternatives Researcher: Document 3Rs search",
        "5. Statistical Consultant: Review sample size",
        "6. Veterinary Reviewer: Pre-review welfare concerns",
        "7. Procedure Writer: Write detailed procedures",
        "8. Protocol Assembler: Compile final document",
    ]
    
    return {
        "is_valid": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "agents": list(agents.keys()),
        "task_sequence": task_summary,
        "input_summary": {
            "title": protocol_input.title,
            "species": protocol_input.species,
            "total_animals": protocol_input.total_animals,
            "has_strain": protocol_input.strain is not None,
            "has_duration": protocol_input.study_duration is not None,
            "has_endpoint": protocol_input.primary_endpoint is not None,
        },
    }


def generate_protocol_fast(
    protocol_input: ProtocolInput,
    verbose: bool = False,
) -> CrewResult:
    """
    Generate protocol using optimized parallel execution.
    
    ~3x faster than sequential by:
    1. Running independent agents in parallel
    2. Using Haiku for simpler tasks
    3. Reduced max_tokens
    
    Args:
        protocol_input: Input for protocol generation
        verbose: Whether to show agent reasoning
        
    Returns:
        CrewResult with generated protocol.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from src.agents.llm import get_fast_llm, get_standard_llm
    
    try:
        agent_outputs = {}
        
        # Build description string
        full_description = f"""
Title: {protocol_input.title}
PI: {protocol_input.pi_name}
Species: {protocol_input.species}
{f"Strain: {protocol_input.strain}" if protocol_input.strain else ""}
Total Animals: {protocol_input.total_animals}
{f"Study Duration: {protocol_input.study_duration}" if protocol_input.study_duration else ""}

Research Description:
{protocol_input.research_description}

Procedures:
{protocol_input.procedures}
"""
        
        # Phase 1: Run 4 independent agents in parallel (using fast model)
        fast_llm = get_fast_llm(max_tokens=1024)
        standard_llm = get_standard_llm(max_tokens=2048)
        
        def run_agent_task(name: str, prompt: str, use_fast: bool = True):
            """Run a single agent task."""
            llm = fast_llm if use_fast else standard_llm
            response = llm.invoke(prompt)
            return name, response.content
        
        phase1_tasks = [
            ("intake", f"Extract key parameters from this protocol:\n{full_description}\n\nList: species, strain, animal count, procedures, pain category estimate.", True),
            ("lay_summary", f"Write a 150-word lay summary for non-scientists:\n{full_description}", True),
            ("regulatory", f"Identify USDA pain category and regulations for: {protocol_input.species} - {protocol_input.procedures}", True),
            ("statistics", f"Briefly assess sample size of {protocol_input.total_animals} {protocol_input.species} for this study. Is it justified?", True),
        ]
        
        if verbose:
            print("Phase 1: Running 4 agents in parallel...")
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(run_agent_task, name, prompt, fast): name 
                      for name, prompt, fast in phase1_tasks}
            for future in as_completed(futures):
                name, result = future.result()
                agent_outputs[name] = result
                if verbose:
                    print(f"  ✓ {name} complete")
        
        # Phase 2: Run 3 dependent agents in parallel (using standard model for complex tasks)
        phase2_tasks = [
            ("alternatives", f"Document 3Rs (Replacement, Reduction, Refinement) for: {protocol_input.species} - {protocol_input.procedures}\nContext: {agent_outputs.get('regulatory', '')[:500]}", False),
            ("veterinary", f"Veterinary review for {protocol_input.species} with {protocol_input.procedures}. Include: pain category, monitoring, humane endpoints.", False),
            ("procedures", f"Write detailed procedure descriptions for: {protocol_input.procedures}\nSpecies: {protocol_input.species}", False),
        ]
        
        if verbose:
            print("Phase 2: Running 3 agents in parallel...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(run_agent_task, name, prompt, fast): name 
                      for name, prompt, fast in phase2_tasks}
            for future in as_completed(futures):
                name, result = future.result()
                agent_outputs[name] = result
                if verbose:
                    print(f"  ✓ {name} complete")
        
        # Phase 3: Final assembly (single agent)
        if verbose:
            print("Phase 3: Assembling final protocol...")
        
        assembly_prompt = f"""
Compile this into a complete IACUC protocol document:

Title: {protocol_input.title}
PI: {protocol_input.pi_name}

Lay Summary:
{agent_outputs.get('lay_summary', '')}

Regulatory:
{agent_outputs.get('regulatory', '')}

Statistics:
{agent_outputs.get('statistics', '')}

3Rs:
{agent_outputs.get('alternatives', '')}

Veterinary:
{agent_outputs.get('veterinary', '')}

Procedures:
{agent_outputs.get('procedures', '')}

Format as a structured protocol with clear sections.
"""
        _, assembly_result = run_agent_task("assembly", assembly_prompt, False)
        agent_outputs["assembly"] = assembly_result
        
        # Build protocol sections
        protocol_sections = {
            "title": protocol_input.title,
            "pi_name": protocol_input.pi_name,
            "species": protocol_input.species,
            "total_animals": protocol_input.total_animals,
            "lay_summary": agent_outputs.get("lay_summary", ""),
            "regulatory_assessment": agent_outputs.get("regulatory", ""),
            "alternatives_documentation": agent_outputs.get("alternatives", ""),
            "statistical_justification": agent_outputs.get("statistics", ""),
            "veterinary_review": agent_outputs.get("veterinary", ""),
            "procedures": agent_outputs.get("procedures", ""),
            "final_protocol": agent_outputs.get("assembly", ""),
        }
        
        return CrewResult(
            success=True,
            protocol_sections=protocol_sections,
            agent_outputs=agent_outputs,
            errors=[],
        )
        
    except Exception as e:
        return CrewResult(
            success=False,
            protocol_sections={},
            agent_outputs={},
            errors=[str(e)],
        )


# Export key items
__all__ = [
    "create_all_agents",
    "create_protocol_tasks",
    "create_protocol_crew",
    "generate_protocol",
    "generate_protocol_fast",
    "quick_crew_check",
    "ProtocolInput",
    "CrewResult",
]
