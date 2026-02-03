"""
Readability Scoring Tools.

Provides tools for measuring text readability and suggesting simplifications.
"""

from typing import Optional, Type

import textstat
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class ReadabilityInput(BaseModel):
    """Input schema for readability analysis."""
    
    text: str = Field(
        description="The text to analyze for readability"
    )
    target_grade: float = Field(
        default=7.0,
        description="Target reading grade level (default 7.0 for lay audience)"
    )


class ReadabilityResult(BaseModel):
    """Result of readability analysis."""
    
    flesch_kincaid_grade: float
    flesch_reading_ease: float
    passes_target: bool
    target_grade: float
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    suggestions: list[str]


def analyze_readability(text: str, target_grade: float = 7.0) -> ReadabilityResult:
    """
    Analyze text readability and provide suggestions.
    
    Args:
        text: The text to analyze
        target_grade: Target reading grade level
        
    Returns:
        ReadabilityResult with scores and suggestions
    """
    if not text or not text.strip():
        return ReadabilityResult(
            flesch_kincaid_grade=0.0,
            flesch_reading_ease=100.0,
            passes_target=True,
            target_grade=target_grade,
            word_count=0,
            sentence_count=0,
            avg_sentence_length=0.0,
            suggestions=["No text provided for analysis."],
        )
    
    # Calculate readability metrics
    fk_grade = textstat.flesch_kincaid_grade(text)
    fk_ease = textstat.flesch_reading_ease(text)
    word_count = textstat.lexicon_count(text, removepunct=True)
    sentence_count = textstat.sentence_count(text)
    
    # Calculate average sentence length
    avg_sentence_length = word_count / max(sentence_count, 1)
    
    # Determine if it passes the target
    passes_target = fk_grade <= target_grade
    
    # Generate suggestions
    suggestions = _generate_suggestions(
        fk_grade=fk_grade,
        fk_ease=fk_ease,
        avg_sentence_length=avg_sentence_length,
        target_grade=target_grade,
        text=text,
    )
    
    return ReadabilityResult(
        flesch_kincaid_grade=round(fk_grade, 1),
        flesch_reading_ease=round(fk_ease, 1),
        passes_target=passes_target,
        target_grade=target_grade,
        word_count=word_count,
        sentence_count=sentence_count,
        avg_sentence_length=round(avg_sentence_length, 1),
        suggestions=suggestions,
    )


def _generate_suggestions(
    fk_grade: float,
    fk_ease: float,
    avg_sentence_length: float,
    target_grade: float,
    text: str,
) -> list[str]:
    """Generate improvement suggestions based on readability metrics."""
    suggestions = []
    
    if fk_grade <= target_grade:
        suggestions.append(f"✓ Text meets target grade level ({fk_grade:.1f} ≤ {target_grade})")
        return suggestions
    
    suggestions.append(
        f"✗ Text is above target grade level ({fk_grade:.1f} > {target_grade}). "
        "Consider the following:"
    )
    
    # Sentence length suggestions
    if avg_sentence_length > 20:
        suggestions.append(
            f"• Shorten sentences: Average length is {avg_sentence_length:.1f} words. "
            "Aim for 15-20 words per sentence."
        )
    
    # Check for complex words (syllables > 2)
    difficult_words = textstat.difficult_words(text)
    if difficult_words > 0:
        suggestions.append(
            f"• Simplify vocabulary: Found {difficult_words} complex words. "
            "Replace with simpler alternatives."
        )
    
    # Check for passive voice indicators (simple heuristic)
    passive_indicators = ["was", "were", "been", "being", "is being", "are being"]
    passive_count = sum(1 for indicator in passive_indicators if f" {indicator} " in text.lower())
    if passive_count > 2:
        suggestions.append(
            "• Use active voice: Text may contain passive constructions. "
            "Rewrite in active voice for clarity."
        )
    
    # Technical jargon detection (common scientific terms)
    jargon_terms = [
        "methodology", "utilize", "implementation", "paradigm", "efficacy",
        "subsequently", "furthermore", "henceforth", "aforementioned",
        "notwithstanding", "characterization", "modulation", "pathogenesis",
        "pharmacokinetics", "bioavailability", "administration", "subcutaneous",
        "intraperitoneal", "analgesia", "anesthesia", "euthanasia",
    ]
    found_jargon = [term for term in jargon_terms if term.lower() in text.lower()]
    if found_jargon:
        suggestions.append(
            f"• Replace technical terms: Consider simplifying: {', '.join(found_jargon[:5])}"
        )
    
    # Flesch Reading Ease interpretation
    if fk_ease < 30:
        suggestions.append(
            "• Very difficult text (college graduate level). "
            "Major simplification needed for lay audience."
        )
    elif fk_ease < 50:
        suggestions.append(
            "• Difficult text (college level). "
            "Significant simplification recommended."
        )
    elif fk_ease < 60:
        suggestions.append(
            "• Fairly difficult text (high school level). "
            "Some simplification recommended."
        )
    
    return suggestions


# Common jargon replacements for scientific text
JARGON_REPLACEMENTS = {
    "utilize": "use",
    "methodology": "method",
    "subsequently": "then",
    "furthermore": "also",
    "administer": "give",
    "administration": "giving",
    "subcutaneous": "under the skin",
    "intraperitoneal": "into the belly",
    "intravenous": "into a vein",
    "analgesia": "pain relief",
    "anesthesia": "put to sleep",
    "euthanasia": "humane killing",
    "humane endpoint": "when to end the study for animal welfare",
    "efficacy": "how well it works",
    "bioavailability": "how much gets into the body",
    "pathogenesis": "how disease develops",
    "pharmacokinetics": "how the body handles drugs",
    "characterized": "described",
    "paradigm": "approach",
    "optimal": "best",
    "implement": "use",
    "facilitate": "help",
    "approximately": "about",
    "sufficient": "enough",
    "indicate": "show",
    "demonstrate": "show",
    "prior to": "before",
    "subsequent to": "after",
}


def suggest_replacements(text: str) -> dict[str, str]:
    """
    Find jargon in text and suggest simpler replacements.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary of found jargon terms to suggested replacements
    """
    found_replacements = {}
    text_lower = text.lower()
    
    for jargon, replacement in JARGON_REPLACEMENTS.items():
        if jargon.lower() in text_lower:
            found_replacements[jargon] = replacement
    
    return found_replacements


class ReadabilityScoreTool(BaseTool):
    """
    Tool for measuring text readability.
    
    Calculates Flesch-Kincaid grade level and provides suggestions
    for improving text accessibility for lay audiences.
    """
    
    name: str = "readability_score"
    description: str = """Analyze text readability using Flesch-Kincaid grade level.
Returns the grade level, whether it passes the target (default: grade 7), 
and specific suggestions for simplification. Use this to ensure lay summaries
are accessible to non-scientific audiences."""
    
    args_schema: Type[BaseModel] = ReadabilityInput
    
    def _run(self, text: str, target_grade: float = 7.0) -> str:
        """
        Analyze readability and return formatted results.
        
        Args:
            text: Text to analyze
            target_grade: Target grade level (default 7.0)
            
        Returns:
            Formatted readability analysis
        """
        result = analyze_readability(text, target_grade)
        
        # Format output
        status = "PASS ✓" if result.passes_target else "FAIL ✗"
        
        output = [
            f"Readability Analysis: {status}",
            f"─────────────────────────────",
            f"Flesch-Kincaid Grade: {result.flesch_kincaid_grade} (target: ≤{result.target_grade})",
            f"Flesch Reading Ease: {result.flesch_reading_ease} (higher is easier)",
            f"Word Count: {result.word_count}",
            f"Sentence Count: {result.sentence_count}",
            f"Avg Sentence Length: {result.avg_sentence_length} words",
            "",
            "Suggestions:",
        ]
        
        for suggestion in result.suggestions:
            output.append(f"  {suggestion}")
        
        # Add jargon replacements if any found
        replacements = suggest_replacements(text)
        if replacements and not result.passes_target:
            output.append("")
            output.append("Jargon Replacement Suggestions:")
            for jargon, replacement in list(replacements.items())[:10]:
                output.append(f"  • '{jargon}' → '{replacement}'")
        
        return "\n".join(output)
    
    async def _arun(self, text: str, target_grade: float = 7.0) -> str:
        """Async version - just calls sync version."""
        return self._run(text, target_grade)
