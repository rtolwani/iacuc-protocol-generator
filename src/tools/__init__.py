"""
Tools module.

Contains tools that agents can use for various tasks.
"""

from src.tools.rag_tools import (
    RegulatorySearchTool,
    SpeciesGuidanceTool,
    EuthanasiaMethodTool,
)
from src.tools.readability_tools import (
    ReadabilityScoreTool,
    analyze_readability,
    suggest_replacements,
)
from src.tools.pain_category_tool import (
    PainCategoryTool,
    classify_pain_category,
    PAIN_CATEGORIES,
)
from src.tools.literature_search_tool import (
    LiteratureSearchTool,
    generate_search_keywords,
    create_search_documentation,
    REQUIRED_DATABASES,
    ALTERNATIVES_DATABASES,
)

__all__ = [
    "RegulatorySearchTool",
    "SpeciesGuidanceTool",
    "EuthanasiaMethodTool",
    "ReadabilityScoreTool",
    "analyze_readability",
    "suggest_replacements",
    "PainCategoryTool",
    "classify_pain_category",
    "PAIN_CATEGORIES",
    "LiteratureSearchTool",
    "generate_search_keywords",
    "create_search_documentation",
    "REQUIRED_DATABASES",
    "ALTERNATIVES_DATABASES",
]
