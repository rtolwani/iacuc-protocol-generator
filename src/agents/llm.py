"""
LLM Configuration for CrewAI Agents.

Provides configured LLM instances for use with CrewAI agents.
"""

from langchain_anthropic import ChatAnthropic

from src.config import get_settings


def get_llm() -> ChatAnthropic:
    """
    Get a configured LLM instance for CrewAI agents.
    
    Returns:
        ChatAnthropic instance configured with settings from environment.
    
    Raises:
        ValueError: If Anthropic API key is not configured.
    """
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        raise ValueError(
            "Anthropic API key not configured. "
            "Set ANTHROPIC_API_KEY in your .env file."
        )
    
    return ChatAnthropic(
        model=settings.default_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        anthropic_api_key=settings.anthropic_api_key,
    )


def get_llm_for_task(
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ChatAnthropic:
    """
    Get a configured LLM with optional overrides for specific tasks.
    
    Args:
        temperature: Override default temperature (0.0-1.0)
        max_tokens: Override default max tokens
        
    Returns:
        ChatAnthropic instance with specified settings.
    """
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        raise ValueError(
            "Anthropic API key not configured. "
            "Set ANTHROPIC_API_KEY in your .env file."
        )
    
    return ChatAnthropic(
        model=settings.default_model,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        max_tokens=max_tokens if max_tokens is not None else settings.llm_max_tokens,
        anthropic_api_key=settings.anthropic_api_key,
    )
