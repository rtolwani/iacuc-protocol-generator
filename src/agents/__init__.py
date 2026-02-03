"""
Agents module.

Contains CrewAI agents for IACUC protocol generation.
"""

from src.agents.llm import get_llm, get_llm_for_task
from src.agents.lay_summary_writer import (
    create_lay_summary_writer_agent,
    create_lay_summary_task,
    generate_lay_summary,
)
from src.agents.regulatory_scout import (
    create_regulatory_scout_agent,
    create_regulatory_scout_task,
    analyze_protocol_regulations,
    quick_regulatory_check,
)
from src.agents.alternatives_researcher import (
    create_alternatives_researcher_agent,
    create_alternatives_research_task,
    research_alternatives,
    quick_3rs_check,
)
from src.agents.statistical_consultant import (
    create_statistical_consultant_agent,
    create_statistical_review_task,
    review_protocol_statistics,
    quick_statistical_check,
)
from src.agents.veterinary_reviewer import (
    create_veterinary_reviewer_agent,
    create_veterinary_review_task,
    conduct_veterinary_review,
    quick_veterinary_check,
)
from src.agents.procedure_writer import (
    create_procedure_writer_agent,
    create_procedure_writing_task,
    write_procedure_documentation,
    quick_procedure_generation,
)
from src.agents.intake_specialist import (
    create_intake_specialist_agent,
    create_intake_task,
    process_intake,
    quick_intake,
)
from src.agents.protocol_assembler import (
    create_protocol_assembler_agent,
    create_assembly_task,
    assemble_protocol,
    quick_assemble,
)

__all__ = [
    "get_llm",
    "get_llm_for_task",
    "create_lay_summary_writer_agent",
    "create_lay_summary_task",
    "generate_lay_summary",
    "create_regulatory_scout_agent",
    "create_regulatory_scout_task",
    "analyze_protocol_regulations",
    "quick_regulatory_check",
    "create_alternatives_researcher_agent",
    "create_alternatives_research_task",
    "research_alternatives",
    "quick_3rs_check",
    "create_statistical_consultant_agent",
    "create_statistical_review_task",
    "review_protocol_statistics",
    "quick_statistical_check",
    "create_veterinary_reviewer_agent",
    "create_veterinary_review_task",
    "conduct_veterinary_review",
    "quick_veterinary_check",
    "create_procedure_writer_agent",
    "create_procedure_writing_task",
    "write_procedure_documentation",
    "quick_procedure_generation",
    "create_intake_specialist_agent",
    "create_intake_task",
    "process_intake",
    "quick_intake",
    "create_protocol_assembler_agent",
    "create_assembly_task",
    "assemble_protocol",
    "quick_assemble",
]
