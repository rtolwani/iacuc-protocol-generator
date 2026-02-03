"""
Literature Search Documentation Tool.

Generates USDA-compliant documentation for alternatives searches
required in IACUC protocols.
"""

from datetime import date, datetime
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# USDA Required Databases
REQUIRED_DATABASES = {
    "pubmed": {
        "name": "PubMed/MEDLINE",
        "url": "https://pubmed.ncbi.nlm.nih.gov/",
        "description": "NIH biomedical literature database",
    },
    "agricola": {
        "name": "AGRICOLA",
        "url": "https://agricola.nal.usda.gov/",
        "description": "USDA agricultural literature database",
    },
    "awic": {
        "name": "AWIC (Animal Welfare Information Center)",
        "url": "https://www.nal.usda.gov/awic",
        "description": "USDA animal welfare resources",
    },
}

# Common Alternatives Databases
ALTERNATIVES_DATABASES = {
    "altbib": {
        "name": "AltBib",
        "url": "https://awic.nal.usda.gov/altbib",
        "description": "Bibliography on alternatives to animal testing",
    },
    "altweb": {
        "name": "AltWeb",
        "url": "https://altweb.jhsph.edu/",
        "description": "Johns Hopkins alternatives resources",
    },
    "frame": {
        "name": "FRAME",
        "url": "https://frame.org.uk/",
        "description": "Fund for Replacement of Animals",
    },
    "norina": {
        "name": "NORINA",
        "url": "https://norina.no/",
        "description": "Norwegian alternatives database",
    },
    "cab_abstracts": {
        "name": "CAB Abstracts",
        "url": "https://www.cabi.org/",
        "description": "Comprehensive life sciences database",
    },
}


class LiteratureSearchRecord(BaseModel):
    """Record of a literature search for alternatives."""
    
    database: str = Field(description="Database searched")
    search_date: str = Field(description="Date search was performed")
    date_range: str = Field(description="Time period covered by search")
    keywords: list[str] = Field(description="Search terms used")
    search_string: str = Field(description="Exact search query")
    results_count: int = Field(description="Number of results returned")
    relevant_count: int = Field(description="Number of relevant results")
    notes: str = Field(default="", description="Additional notes")


class AlternativesSearchDocumentation(BaseModel):
    """Complete documentation of alternatives search."""
    
    search_date: str = Field(description="Date search was conducted")
    searcher_name: str = Field(description="Name of person conducting search")
    animal_model: str = Field(description="Animal model being used")
    procedures: str = Field(description="Procedures requiring alternatives search")
    
    # 3Rs focus
    replacement_keywords: list[str] = Field(default_factory=list)
    reduction_keywords: list[str] = Field(default_factory=list)
    refinement_keywords: list[str] = Field(default_factory=list)
    
    # Search records
    searches: list[LiteratureSearchRecord] = Field(default_factory=list)
    
    # Conclusions
    replacement_available: bool = Field(default=False)
    reduction_methods: list[str] = Field(default_factory=list)
    refinement_methods: list[str] = Field(default_factory=list)
    justification: str = Field(default="")


def generate_search_keywords(
    animal_model: str,
    procedures: str,
) -> dict[str, list[str]]:
    """
    Generate recommended search keywords for alternatives.
    
    Args:
        animal_model: The animal species/model
        procedures: Description of procedures
        
    Returns:
        Dictionary with replacement, reduction, refinement keywords
    """
    procedures_lower = procedures.lower()
    
    # Base replacement keywords
    replacement_keywords = [
        "in vitro",
        "cell culture",
        "computer model",
        "simulation",
        "non-animal",
        "alternative method",
        f"{animal_model} alternative",
    ]
    
    # Procedure-specific replacement keywords
    if "toxicity" in procedures_lower or "toxicology" in procedures_lower:
        replacement_keywords.extend([
            "in vitro toxicity",
            "organ-on-chip",
            "computational toxicology",
            "3D tissue model",
        ])
    
    if "pain" in procedures_lower or "analgesia" in procedures_lower:
        replacement_keywords.extend([
            "pain model alternative",
            "nociception in vitro",
        ])
    
    if "behavior" in procedures_lower:
        replacement_keywords.extend([
            "behavioral simulation",
            "computational behavior",
        ])
    
    # Base reduction keywords
    reduction_keywords = [
        "sample size",
        "power analysis",
        "statistical design",
        "pilot study",
        "minimal number",
        f"{animal_model} number reduction",
        "experimental design optimization",
    ]
    
    # Base refinement keywords
    refinement_keywords = [
        "humane endpoint",
        "pain assessment",
        "welfare assessment",
        "anesthesia",
        "analgesia",
        "environmental enrichment",
        f"{animal_model} refinement",
        "distress minimization",
        "scoring system",
    ]
    
    # Procedure-specific refinement
    if "surgery" in procedures_lower:
        refinement_keywords.extend([
            "surgical refinement",
            "post-operative care",
            "aseptic technique improvement",
        ])
    
    if "tumor" in procedures_lower:
        refinement_keywords.extend([
            "tumor endpoint",
            "tumor burden scoring",
            "early tumor endpoint",
        ])
    
    return {
        "replacement": replacement_keywords,
        "reduction": reduction_keywords,
        "refinement": refinement_keywords,
    }


def generate_search_string(
    keywords: list[str],
    boolean_operator: str = "OR",
) -> str:
    """
    Generate a formatted database search string.
    
    Args:
        keywords: List of search terms
        boolean_operator: Boolean operator to join terms
        
    Returns:
        Formatted search string
    """
    formatted_terms = []
    for kw in keywords:
        if " " in kw:
            formatted_terms.append(f'"{kw}"')
        else:
            formatted_terms.append(kw)
    
    return f" {boolean_operator} ".join(formatted_terms)


def format_search_documentation(
    doc: AlternativesSearchDocumentation,
) -> str:
    """
    Format alternatives search documentation for IACUC protocol.
    
    Args:
        doc: Complete search documentation
        
    Returns:
        Formatted documentation string
    """
    output = []
    
    # Header
    output.append("=" * 70)
    output.append("LITERATURE SEARCH FOR ALTERNATIVES")
    output.append("USDA-Compliant Documentation")
    output.append("=" * 70)
    output.append("")
    
    # Basic info
    output.append(f"Search Date: {doc.search_date}")
    output.append(f"Conducted By: {doc.searcher_name}")
    output.append(f"Animal Model: {doc.animal_model}")
    output.append(f"Procedures: {doc.procedures}")
    output.append("")
    
    # Keywords used
    output.append("-" * 40)
    output.append("SEARCH KEYWORDS")
    output.append("-" * 40)
    
    if doc.replacement_keywords:
        output.append("\nReplacement Keywords:")
        for kw in doc.replacement_keywords:
            output.append(f"  • {kw}")
    
    if doc.reduction_keywords:
        output.append("\nReduction Keywords:")
        for kw in doc.reduction_keywords:
            output.append(f"  • {kw}")
    
    if doc.refinement_keywords:
        output.append("\nRefinement Keywords:")
        for kw in doc.refinement_keywords:
            output.append(f"  • {kw}")
    
    output.append("")
    
    # Search records
    output.append("-" * 40)
    output.append("DATABASE SEARCHES")
    output.append("-" * 40)
    
    for i, search in enumerate(doc.searches, 1):
        output.append(f"\nSearch #{i}: {search.database}")
        output.append(f"  Date: {search.search_date}")
        output.append(f"  Period Covered: {search.date_range}")
        output.append(f"  Search String: {search.search_string}")
        output.append(f"  Results: {search.results_count} total, {search.relevant_count} relevant")
        if search.notes:
            output.append(f"  Notes: {search.notes}")
    
    output.append("")
    
    # Conclusions
    output.append("-" * 40)
    output.append("SEARCH CONCLUSIONS")
    output.append("-" * 40)
    
    output.append(f"\nReplacement Available: {'Yes' if doc.replacement_available else 'No'}")
    
    if doc.reduction_methods:
        output.append("\nReduction Methods Identified:")
        for method in doc.reduction_methods:
            output.append(f"  • {method}")
    
    if doc.refinement_methods:
        output.append("\nRefinement Methods Identified:")
        for method in doc.refinement_methods:
            output.append(f"  • {method}")
    
    if doc.justification:
        output.append(f"\nJustification for Animal Use:")
        output.append(f"  {doc.justification}")
    
    output.append("")
    output.append("=" * 70)
    
    return "\n".join(output)


class LiteratureSearchTool(BaseTool):
    """
    Tool for generating USDA-compliant literature search documentation.
    
    Helps researchers document their search for alternatives to animal use,
    including replacement, reduction, and refinement (3Rs) methods.
    """
    
    name: str = "literature_search_documentation"
    description: str = (
        "Generate documentation for alternatives literature search. "
        "Input should be 'animal_model: [species], procedures: [description]'. "
        "Returns recommended keywords and documentation template."
    )
    
    def _run(self, input_text: str) -> str:
        """
        Generate literature search documentation template.
        
        Args:
            input_text: Description of animal model and procedures
            
        Returns:
            Documentation template with recommended keywords
        """
        # Parse input
        animal_model = "laboratory animal"
        procedures = input_text
        
        if "animal_model:" in input_text.lower():
            parts = input_text.split(",")
            for part in parts:
                if "animal_model:" in part.lower():
                    animal_model = part.split(":")[-1].strip()
                elif "procedures:" in part.lower():
                    procedures = part.split(":")[-1].strip()
        
        # Generate keywords
        keywords = generate_search_keywords(animal_model, procedures)
        
        # Create template documentation
        today = date.today().strftime("%Y-%m-%d")
        year_ago = date(date.today().year - 10, 1, 1).strftime("%Y")
        
        doc = AlternativesSearchDocumentation(
            search_date=today,
            searcher_name="[RESEARCHER NAME]",
            animal_model=animal_model,
            procedures=procedures,
            replacement_keywords=keywords["replacement"],
            reduction_keywords=keywords["reduction"],
            refinement_keywords=keywords["refinement"],
            searches=[
                LiteratureSearchRecord(
                    database="PubMed/MEDLINE",
                    search_date=today,
                    date_range=f"{year_ago}-present",
                    keywords=keywords["replacement"][:5],
                    search_string=generate_search_string(keywords["replacement"][:5]),
                    results_count=0,
                    relevant_count=0,
                    notes="[Document relevant findings]",
                ),
                LiteratureSearchRecord(
                    database="AGRICOLA",
                    search_date=today,
                    date_range=f"{year_ago}-present",
                    keywords=keywords["replacement"][:5],
                    search_string=generate_search_string(keywords["replacement"][:5]),
                    results_count=0,
                    relevant_count=0,
                    notes="[Document relevant findings]",
                ),
            ],
            replacement_available=False,
            justification=(
                f"Based on the literature search conducted on {today}, no suitable "
                f"replacement alternatives were identified for the proposed {animal_model} "
                f"model. The following justifies continued animal use: [ADD JUSTIFICATION]"
            ),
        )
        
        return format_search_documentation(doc)


# Helper functions for external use
def create_search_documentation(
    animal_model: str,
    procedures: str,
    searcher_name: str,
    searches: Optional[list[dict]] = None,
    replacement_available: bool = False,
    reduction_methods: Optional[list[str]] = None,
    refinement_methods: Optional[list[str]] = None,
    justification: str = "",
) -> str:
    """
    Create complete literature search documentation.
    
    Args:
        animal_model: Species/model being used
        procedures: Description of procedures
        searcher_name: Name of person conducting search
        searches: List of search records (dicts)
        replacement_available: Whether replacement alternatives exist
        reduction_methods: List of reduction methods found
        refinement_methods: List of refinement methods found
        justification: Justification for animal use
        
    Returns:
        Formatted documentation string
    """
    keywords = generate_search_keywords(animal_model, procedures)
    today = date.today().strftime("%Y-%m-%d")
    
    search_records = []
    if searches:
        for s in searches:
            search_records.append(LiteratureSearchRecord(**s))
    
    doc = AlternativesSearchDocumentation(
        search_date=today,
        searcher_name=searcher_name,
        animal_model=animal_model,
        procedures=procedures,
        replacement_keywords=keywords["replacement"],
        reduction_keywords=keywords["reduction"],
        refinement_keywords=keywords["refinement"],
        searches=search_records,
        replacement_available=replacement_available,
        reduction_methods=reduction_methods or [],
        refinement_methods=refinement_methods or [],
        justification=justification,
    )
    
    return format_search_documentation(doc)


# Export key items
__all__ = [
    "LiteratureSearchTool",
    "generate_search_keywords",
    "generate_search_string",
    "create_search_documentation",
    "format_search_documentation",
    "LiteratureSearchRecord",
    "AlternativesSearchDocumentation",
    "REQUIRED_DATABASES",
    "ALTERNATIVES_DATABASES",
]
