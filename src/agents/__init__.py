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

__all__ = [
    "get_llm",
    "get_llm_for_task",
    "create_lay_summary_writer_agent",
    "create_lay_summary_task",
    "generate_lay_summary",
]
