"""
Agents module.

Contains CrewAI agents for IACUC protocol generation.
"""

from src.agents.llm import get_llm, get_llm_for_task

__all__ = [
    "get_llm",
    "get_llm_for_task",
]
