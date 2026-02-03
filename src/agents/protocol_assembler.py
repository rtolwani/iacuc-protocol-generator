"""
Protocol Assembler Agent.

Agent that compiles all protocol sections into a complete document,
runs consistency checks, and validates completeness.
"""

from typing import Optional
from datetime import datetime

from crewai import Agent, Task, Crew
from pydantic import BaseModel, Field

from src.agents.llm import get_llm
from src.tools.consistency_checker import ConsistencyCheckerTool, check_protocol_consistency


class ProtocolSection(BaseModel):
    """A section of the protocol document."""
    
    name: str = Field(description="Section name")
    content: str = Field(description="Section content")
    order: int = Field(description="Section order in document")
    required: bool = Field(default=True, description="Whether section is required")
    status: str = Field(default="incomplete", description="complete, incomplete, or needs_review")


class ProtocolDocument(BaseModel):
    """Complete protocol document."""
    
    title: str = Field(default="IACUC Protocol")
    version: str = Field(default="1.0")
    date_created: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    sections: list[ProtocolSection] = Field(default_factory=list)
    completeness_score: float = Field(default=0.0)
    is_valid: bool = Field(default=False)
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)


# Standard protocol sections in order
STANDARD_SECTIONS = [
    {
        "name": "Project Summary",
        "order": 1,
        "required": True,
        "description": "Lay summary of the research project",
    },
    {
        "name": "Scientific Justification",
        "order": 2,
        "required": True,
        "description": "Scientific rationale for using animals",
    },
    {
        "name": "Species and Numbers",
        "order": 3,
        "required": True,
        "description": "Species, strain, source, and number of animals",
    },
    {
        "name": "Alternatives Search",
        "order": 4,
        "required": True,
        "description": "3Rs documentation and literature search",
    },
    {
        "name": "Statistical Justification",
        "order": 5,
        "required": True,
        "description": "Sample size calculation and statistical design",
    },
    {
        "name": "Procedures",
        "order": 6,
        "required": True,
        "description": "Detailed experimental procedures",
    },
    {
        "name": "Anesthesia and Analgesia",
        "order": 7,
        "required": True,
        "description": "Pain management plan",
    },
    {
        "name": "Monitoring and Endpoints",
        "order": 8,
        "required": True,
        "description": "Monitoring schedule and humane endpoints",
    },
    {
        "name": "Euthanasia",
        "order": 9,
        "required": True,
        "description": "Euthanasia method and justification",
    },
    {
        "name": "Personnel",
        "order": 10,
        "required": True,
        "description": "Qualified personnel and training",
    },
    {
        "name": "Hazards",
        "order": 11,
        "required": False,
        "description": "Biological, chemical, or physical hazards",
    },
    {
        "name": "Special Considerations",
        "order": 12,
        "required": False,
        "description": "Field studies, multiple surgeries, etc.",
    },
]


def create_empty_protocol() -> ProtocolDocument:
    """
    Create an empty protocol document with standard sections.
    
    Returns:
        ProtocolDocument with empty sections.
    """
    sections = []
    for section_def in STANDARD_SECTIONS:
        sections.append(ProtocolSection(
            name=section_def["name"],
            content="",
            order=section_def["order"],
            required=section_def["required"],
            status="incomplete",
        ))
    
    return ProtocolDocument(sections=sections)


def add_section_content(
    protocol: ProtocolDocument,
    section_name: str,
    content: str,
) -> ProtocolDocument:
    """
    Add content to a protocol section.
    
    Args:
        protocol: The protocol document
        section_name: Name of section to update
        content: Content to add
        
    Returns:
        Updated protocol document.
    """
    for section in protocol.sections:
        if section.name.lower() == section_name.lower():
            section.content = content
            section.status = "complete" if content.strip() else "incomplete"
            break
    
    return protocol


def calculate_completeness(protocol: ProtocolDocument) -> float:
    """
    Calculate protocol completeness score.
    
    Args:
        protocol: Protocol document to evaluate
        
    Returns:
        Completeness score from 0 to 1.
    """
    required_sections = [s for s in protocol.sections if s.required]
    completed_required = [s for s in required_sections if s.status == "complete"]
    
    if not required_sections:
        return 1.0
    
    return len(completed_required) / len(required_sections)


def validate_protocol(protocol: ProtocolDocument) -> ProtocolDocument:
    """
    Validate protocol document for completeness and consistency.
    
    Args:
        protocol: Protocol document to validate
        
    Returns:
        Protocol with validation results.
    """
    errors = []
    warnings = []
    
    # Check required sections
    for section in protocol.sections:
        if section.required and section.status != "complete":
            errors.append(f"Required section '{section.name}' is incomplete")
    
    # Check for minimum content
    for section in protocol.sections:
        if section.status == "complete" and len(section.content.strip()) < 50:
            warnings.append(f"Section '{section.name}' may be too brief")
    
    # Run consistency check on full document
    full_text = assemble_text(protocol)
    if full_text:
        consistency_report = check_protocol_consistency(full_text)
        
        for error in consistency_report.errors:
            errors.append(f"[{error.category}] {error.description}")
        
        for warning in consistency_report.warnings:
            warnings.append(f"[{warning.category}] {warning.description}")
    
    # Update protocol
    protocol.validation_errors = errors
    protocol.validation_warnings = warnings
    protocol.is_valid = len(errors) == 0
    protocol.completeness_score = calculate_completeness(protocol)
    
    return protocol


def assemble_text(protocol: ProtocolDocument) -> str:
    """
    Assemble protocol into plain text.
    
    Args:
        protocol: Protocol document
        
    Returns:
        Assembled text document.
    """
    lines = [
        f"# {protocol.title}",
        f"Version: {protocol.version}",
        f"Date: {protocol.date_created}",
        "",
        "=" * 60,
        "",
    ]
    
    sorted_sections = sorted(protocol.sections, key=lambda s: s.order)
    
    for section in sorted_sections:
        if section.content.strip():
            lines.extend([
                f"## {section.name}",
                "",
                section.content,
                "",
                "-" * 40,
                "",
            ])
    
    return "\n".join(lines)


def assemble_markdown(protocol: ProtocolDocument) -> str:
    """
    Assemble protocol into markdown format.
    
    Args:
        protocol: Protocol document
        
    Returns:
        Markdown formatted document.
    """
    lines = [
        f"# {protocol.title}",
        "",
        f"**Version:** {protocol.version}  ",
        f"**Date:** {protocol.date_created}  ",
        f"**Completeness:** {protocol.completeness_score * 100:.0f}%  ",
        "",
        "---",
        "",
    ]
    
    sorted_sections = sorted(protocol.sections, key=lambda s: s.order)
    
    for section in sorted_sections:
        status_icon = "✓" if section.status == "complete" else "○"
        lines.append(f"## {status_icon} {section.name}")
        lines.append("")
        
        if section.content.strip():
            lines.append(section.content)
        else:
            lines.append("*[Section not yet completed]*")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    if protocol.validation_errors:
        lines.extend([
            "## Validation Errors",
            "",
        ])
        for error in protocol.validation_errors:
            lines.append(f"- ❌ {error}")
        lines.append("")
    
    if protocol.validation_warnings:
        lines.extend([
            "## Validation Warnings",
            "",
        ])
        for warning in protocol.validation_warnings:
            lines.append(f"- ⚠️ {warning}")
        lines.append("")
    
    return "\n".join(lines)


def get_missing_sections(protocol: ProtocolDocument) -> list[str]:
    """
    Get list of missing required sections.
    
    Args:
        protocol: Protocol document
        
    Returns:
        List of missing section names.
    """
    missing = []
    for section in protocol.sections:
        if section.required and section.status != "complete":
            missing.append(section.name)
    return missing


def create_protocol_assembler_agent() -> Agent:
    """
    Create a Protocol Assembler agent.
    
    This agent:
    - Compiles all sections into final document
    - Runs consistency checks
    - Validates completeness
    - Flags missing required fields
    
    Returns:
        Configured CrewAI Agent instance.
    """
    llm = get_llm()
    consistency_tool = ConsistencyCheckerTool()
    
    return Agent(
        role="Protocol Assembler",
        goal=(
            "Compile all protocol sections into a complete, well-organized "
            "IACUC protocol document. Ensure all required sections are present, "
            "verify internal consistency, and generate a completeness report."
        ),
        backstory=(
            "You are a meticulous protocol coordinator who ensures every "
            "submission is complete and professionally formatted. You have "
            "an eye for detail and can quickly identify missing information "
            "or inconsistencies. You take pride in producing protocols that "
            "sail through IACUC review on the first submission."
        ),
        llm=llm,
        tools=[consistency_tool],
        verbose=False,
        allow_delegation=False,
    )


def create_assembly_task(
    agent: Agent,
    sections_content: dict[str, str],
    protocol_title: str = "IACUC Protocol",
) -> Task:
    """
    Create an assembly task.
    
    Args:
        agent: The Protocol Assembler agent
        sections_content: Dictionary of section name to content
        protocol_title: Title for the protocol
        
    Returns:
        Configured CrewAI Task instance.
    """
    sections_list = "\n".join([
        f"- {name}: {len(content)} characters"
        for name, content in sections_content.items()
    ])
    
    return Task(
        description=f"""
Assemble the following sections into a complete IACUC protocol:

PROTOCOL TITLE: {protocol_title}

AVAILABLE SECTIONS:
{sections_list}

Your tasks:

1. ORGANIZE SECTIONS:
   - Arrange sections in proper order
   - Ensure logical flow between sections
   - Add appropriate transitions if needed

2. VALIDATE COMPLETENESS:
   - Identify any missing required sections
   - Note sections that need more detail
   - Calculate overall completeness score

3. CHECK CONSISTENCY:
   - Use the consistency_checker tool on the full document
   - Identify any contradictions or mismatches
   - Flag animal number discrepancies

4. GENERATE REPORT:
   - Summarize what's complete
   - List what's missing or needs improvement
   - Provide recommendations for IACUC approval readiness

Output a complete protocol document with validation summary.
""",
        expected_output=(
            "A complete, organized protocol document with validation "
            "summary and recommendations."
        ),
        agent=agent,
    )


def assemble_protocol(
    sections_content: dict[str, str],
    protocol_title: str = "IACUC Protocol",
    verbose: bool = False,
) -> dict:
    """
    Assemble a complete protocol from sections.
    
    Main entry point for protocol assembly.
    
    Args:
        sections_content: Dictionary of section name to content
        protocol_title: Title for the protocol
        verbose: Whether to show agent reasoning
        
    Returns:
        Dictionary with assembled protocol and validation results.
    """
    # Create protocol
    protocol = create_empty_protocol()
    protocol.title = protocol_title
    
    # Add content
    for section_name, content in sections_content.items():
        protocol = add_section_content(protocol, section_name, content)
    
    # Validate
    protocol = validate_protocol(protocol)
    
    # Create agent for additional review
    agent = create_protocol_assembler_agent()
    if verbose:
        agent.verbose = True
    
    task = create_assembly_task(agent, sections_content, protocol_title)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=verbose,
    )
    
    agent_result = crew.kickoff()
    
    return {
        "protocol": protocol.model_dump(),
        "markdown": assemble_markdown(protocol),
        "text": assemble_text(protocol),
        "completeness_score": protocol.completeness_score,
        "is_valid": protocol.is_valid,
        "errors": protocol.validation_errors,
        "warnings": protocol.validation_warnings,
        "missing_sections": get_missing_sections(protocol),
        "agent_review": str(agent_result),
    }


def quick_assemble(
    sections_content: dict[str, str],
    protocol_title: str = "IACUC Protocol",
) -> dict:
    """
    Quick protocol assembly without LLM calls.
    
    Args:
        sections_content: Dictionary of section name to content
        protocol_title: Title for the protocol
        
    Returns:
        Dictionary with assembled protocol and validation results.
    """
    # Create protocol
    protocol = create_empty_protocol()
    protocol.title = protocol_title
    
    # Add content
    for section_name, content in sections_content.items():
        protocol = add_section_content(protocol, section_name, content)
    
    # Validate
    protocol = validate_protocol(protocol)
    
    return {
        "protocol": protocol.model_dump(),
        "markdown": assemble_markdown(protocol),
        "text": assemble_text(protocol),
        "completeness_score": protocol.completeness_score,
        "is_valid": protocol.is_valid,
        "errors": protocol.validation_errors,
        "warnings": protocol.validation_warnings,
        "missing_sections": get_missing_sections(protocol),
    }


# Export key items
__all__ = [
    "create_protocol_assembler_agent",
    "create_assembly_task",
    "assemble_protocol",
    "quick_assemble",
    "create_empty_protocol",
    "add_section_content",
    "validate_protocol",
    "calculate_completeness",
    "assemble_text",
    "assemble_markdown",
    "get_missing_sections",
    "ProtocolDocument",
    "ProtocolSection",
    "STANDARD_SECTIONS",
]
