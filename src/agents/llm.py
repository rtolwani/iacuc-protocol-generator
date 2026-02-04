"""
LLM Configuration for CrewAI Agents.

Provides configured LLM instances for use with CrewAI agents.
"""

from langchain_anthropic import ChatAnthropic

from src.config import get_settings

# Model tiers for different task complexities
FAST_MODEL = "claude-3-haiku-20240307"  # Fast, good for simple tasks
STANDARD_MODEL = "claude-sonnet-4-20250514"  # Balanced
ADVANCED_MODEL = "claude-sonnet-4-20250514"  # Complex reasoning


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


def get_fast_llm(max_tokens: int = 1024) -> ChatAnthropic:
    """
    Get a fast LLM (Haiku) for simpler tasks.
    
    ~10x faster than Sonnet, good for:
    - Intake/extraction tasks
    - Simple summaries
    - Formatting tasks
    
    Returns:
        ChatAnthropic instance with Haiku model.
    """
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        raise ValueError("Anthropic API key not configured.")
    
    return ChatAnthropic(
        model=FAST_MODEL,
        temperature=0.2,
        max_tokens=max_tokens,
        anthropic_api_key=settings.anthropic_api_key,
    )


def get_standard_llm(max_tokens: int = 2048) -> ChatAnthropic:
    """
    Get standard LLM (Sonnet) for balanced tasks.
    
    Returns:
        ChatAnthropic instance with Sonnet model.
    """
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        raise ValueError("Anthropic API key not configured.")
    
    return ChatAnthropic(
        model=STANDARD_MODEL,
        temperature=0.3,
        max_tokens=max_tokens,
        anthropic_api_key=settings.anthropic_api_key,
    )
