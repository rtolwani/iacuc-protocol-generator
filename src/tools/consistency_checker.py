"""
Consistency Checker Tool.

Validates internal consistency of IACUC protocol documents.
Checks for mismatches in animal numbers, personnel, timelines, and other fields.
"""

import re
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ConsistencyIssue(BaseModel):
    """A consistency issue found in the protocol."""
    
    severity: str = Field(description="Severity: error, warning, info")
    category: str = Field(description="Category of issue")
    description: str = Field(description="Description of the issue")
    location: Optional[str] = Field(default=None, description="Where in document")
    suggestion: Optional[str] = Field(default=None, description="How to fix")


class ConsistencyReport(BaseModel):
    """Complete consistency check report."""
    
    is_consistent: bool = Field(description="Overall consistency status")
    total_issues: int = Field(default=0)
    errors: list[ConsistencyIssue] = Field(default_factory=list)
    warnings: list[ConsistencyIssue] = Field(default_factory=list)
    info: list[ConsistencyIssue] = Field(default_factory=list)
    summary: str = Field(default="", description="Summary of findings")


def extract_animal_numbers(text: str) -> dict[str, list[int]]:
    """
    Extract all animal numbers mentioned in the text.
    
    Args:
        text: Protocol text
        
    Returns:
        Dictionary mapping context to numbers found.
    """
    numbers = {
        "total": [],
        "per_group": [],
        "groups": [],
        "other": [],
    }
    
    text_lower = text.lower()
    
    # Total patterns
    total_patterns = [
        r'total\s*(?:of\s*)?(\d+)\s*(?:animals|mice|rats|subjects)?',
        r'(\d+)\s*(?:animals|mice|rats|subjects)\s*(?:total|in total)',
        r'n\s*=\s*(\d+)',
        r'requesting\s*(\d+)\s*(?:animals|mice|rats)',
    ]
    
    for pattern in total_patterns:
        matches = re.findall(pattern, text_lower)
        numbers["total"].extend([int(m) for m in matches])
    
    # Per group patterns
    per_group_patterns = [
        r'(\d+)\s*(?:per\s*group|/group|each\s*group)',
        r'(\d+)\s*(?:animals|mice|rats)\s*per\s*(?:group|condition)',
    ]
    
    for pattern in per_group_patterns:
        matches = re.findall(pattern, text_lower)
        numbers["per_group"].extend([int(m) for m in matches])
    
    # Group count patterns
    group_patterns = [
        r'(\d+)\s*(?:groups?|conditions?|treatment\s*arms?)',
        r'divided\s*into\s*(\d+)',
    ]
    
    for pattern in group_patterns:
        matches = re.findall(pattern, text_lower)
        numbers["groups"].extend([int(m) for m in matches])
    
    return numbers


def check_animal_number_consistency(text: str) -> list[ConsistencyIssue]:
    """
    Check if animal numbers are consistent throughout the document.
    
    Args:
        text: Protocol text
        
    Returns:
        List of consistency issues found.
    """
    issues = []
    numbers = extract_animal_numbers(text)
    
    # Check if totals are consistent
    unique_totals = list(set(numbers["total"]))
    if len(unique_totals) > 1:
        issues.append(ConsistencyIssue(
            severity="error",
            category="animal_numbers",
            description=f"Inconsistent total animal numbers: {unique_totals}",
            location="Multiple sections",
            suggestion="Ensure the same total is used throughout the protocol",
        ))
    
    # Check if per_group * groups = total
    if numbers["total"] and numbers["per_group"] and numbers["groups"]:
        total = numbers["total"][0]
        per_group = numbers["per_group"][0]
        num_groups = numbers["groups"][0]
        calculated = per_group * num_groups
        
        if calculated != total:
            issues.append(ConsistencyIssue(
                severity="error",
                category="animal_numbers",
                description=(
                    f"Animal number mismatch: {per_group} per group × "
                    f"{num_groups} groups = {calculated}, but total stated as {total}"
                ),
                location="Animal numbers section",
                suggestion=f"Verify calculations: either adjust total to {calculated} or revise group sizes",
            ))
    
    return issues


def extract_personnel(text: str) -> list[str]:
    """
    Extract personnel names mentioned in the text.
    
    Args:
        text: Protocol text
        
    Returns:
        List of personnel names found.
    """
    personnel = []
    
    # Common patterns for personnel
    patterns = [
        r'(?:Dr\.|Professor|Prof\.|Mr\.|Ms\.|Mrs\.)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'PI:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'Principal\s*Investigator:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'performed\s*by\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        personnel.extend(matches)
    
    return list(set(personnel))


def check_personnel_consistency(text: str) -> list[ConsistencyIssue]:
    """
    Check if personnel are consistently listed.
    
    Args:
        text: Protocol text
        
    Returns:
        List of consistency issues found.
    """
    issues = []
    text_lower = text.lower()
    
    # Check for unlisted personnel performing procedures
    procedure_keywords = ["surgery", "injection", "euthanasia", "blood collection"]
    
    for keyword in procedure_keywords:
        if keyword in text_lower:
            # Check if qualified personnel mentioned
            if "qualified" not in text_lower and "trained" not in text_lower:
                if keyword not in ["euthanasia"]:  # Often implicit for euthanasia
                    issues.append(ConsistencyIssue(
                        severity="warning",
                        category="personnel",
                        description=f"'{keyword}' mentioned without specifying qualified personnel",
                        location=f"Section mentioning {keyword}",
                        suggestion="Specify who will perform this procedure and their qualifications",
                    ))
    
    return issues


def extract_timeline_elements(text: str) -> dict[str, list[str]]:
    """
    Extract timeline elements from the text.
    
    Args:
        text: Protocol text
        
    Returns:
        Dictionary of timeline elements found.
    """
    timeline = {
        "durations": [],
        "timepoints": [],
        "frequencies": [],
    }
    
    text_lower = text.lower()
    
    # Duration patterns
    duration_patterns = [
        r'(\d+)\s*(?:days?|weeks?|months?)\s*(?:study|duration|period)',
        r'for\s*(\d+)\s*(?:days?|weeks?|months?)',
        r'up\s*to\s*(\d+)\s*(?:days?|weeks?|months?)',
    ]
    
    for pattern in duration_patterns:
        matches = re.findall(pattern, text_lower)
        timeline["durations"].extend(matches)
    
    # Timepoint patterns
    timepoint_patterns = [
        r'(?:day|week|month)\s*(\d+)',
        r'at\s*(\d+)\s*(?:days?|weeks?|hours?)',
        r'(\d+)\s*(?:hours?|days?)\s*post',
    ]
    
    for pattern in timepoint_patterns:
        matches = re.findall(pattern, text_lower)
        timeline["timepoints"].extend(matches)
    
    # Frequency patterns
    frequency_patterns = [
        r'(daily|weekly|monthly|twice\s*daily|every\s*\d+\s*(?:hours?|days?))',
    ]
    
    for pattern in frequency_patterns:
        matches = re.findall(pattern, text_lower)
        timeline["frequencies"].extend(matches)
    
    return timeline


def check_timeline_consistency(text: str) -> list[ConsistencyIssue]:
    """
    Check if timeline elements are consistent.
    
    Args:
        text: Protocol text
        
    Returns:
        List of consistency issues found.
    """
    issues = []
    timeline = extract_timeline_elements(text)
    
    # Check for multiple conflicting durations
    if len(set(timeline["durations"])) > 1:
        issues.append(ConsistencyIssue(
            severity="warning",
            category="timeline",
            description=f"Multiple study durations mentioned: {set(timeline['durations'])}",
            location="Timeline sections",
            suggestion="Clarify if these refer to different phases or if there's an inconsistency",
        ))
    
    return issues


def check_required_sections(text: str) -> list[ConsistencyIssue]:
    """
    Check if all required sections are present.
    
    Args:
        text: Protocol text
        
    Returns:
        List of consistency issues for missing sections.
    """
    issues = []
    text_lower = text.lower()
    
    required_elements = {
        "species": ["species", "mice", "rats", "rabbits", "animals"],
        "justification": ["justification", "rationale", "why"],
        "procedures": ["procedure", "method", "protocol"],
        "pain_management": ["anesthesia", "analgesia", "pain", "analgesic"],
        "euthanasia": ["euthanasia", "humane endpoint", "sacrifice"],
        "monitoring": ["monitor", "observe", "check", "welfare"],
    }
    
    for section, keywords in required_elements.items():
        if not any(kw in text_lower for kw in keywords):
            issues.append(ConsistencyIssue(
                severity="error",
                category="missing_section",
                description=f"Required element '{section}' not found in protocol",
                location="Overall document",
                suggestion=f"Add information about {section.replace('_', ' ')}",
            ))
    
    return issues


def check_contradictions(text: str) -> list[ConsistencyIssue]:
    """
    Check for logical contradictions in the text.
    
    Args:
        text: Protocol text
        
    Returns:
        List of contradiction issues found.
    """
    issues = []
    text_lower = text.lower()
    
    # Check for contradictory statements
    contradictions = [
        {
            "positive": "survival surgery",
            "negative": "non-survival",
            "both_present": "Protocol mentions both 'survival surgery' and 'non-survival' - clarify which applies",
        },
        {
            "positive": "no pain",
            "negative": "painful procedure",
            "both_present": "Protocol claims 'no pain' but mentions 'painful procedure'",
        },
        {
            "positive": "single procedure",
            "negative": "multiple procedures",
            "both_present": "Protocol mentions both 'single procedure' and 'multiple procedures'",
        },
    ]
    
    for contradiction in contradictions:
        if contradiction["positive"] in text_lower and contradiction["negative"] in text_lower:
            issues.append(ConsistencyIssue(
                severity="warning",
                category="contradiction",
                description=contradiction["both_present"],
                location="Multiple sections",
                suggestion="Review and clarify the contradictory statements",
            ))
    
    return issues


def check_protocol_consistency(text: str) -> ConsistencyReport:
    """
    Perform complete consistency check on a protocol.
    
    Args:
        text: Full protocol text
        
    Returns:
        ConsistencyReport with all findings.
    """
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_animal_number_consistency(text))
    all_issues.extend(check_personnel_consistency(text))
    all_issues.extend(check_timeline_consistency(text))
    all_issues.extend(check_required_sections(text))
    all_issues.extend(check_contradictions(text))
    
    # Categorize by severity
    errors = [i for i in all_issues if i.severity == "error"]
    warnings = [i for i in all_issues if i.severity == "warning"]
    info = [i for i in all_issues if i.severity == "info"]
    
    # Determine overall consistency
    is_consistent = len(errors) == 0
    
    # Generate summary
    if is_consistent and len(warnings) == 0:
        summary = "Protocol is internally consistent with no issues found."
    elif is_consistent:
        summary = f"Protocol is consistent but has {len(warnings)} warning(s) to review."
    else:
        summary = f"Protocol has {len(errors)} error(s) that must be addressed."
    
    return ConsistencyReport(
        is_consistent=is_consistent,
        total_issues=len(all_issues),
        errors=errors,
        warnings=warnings,
        info=info,
        summary=summary,
    )


class ConsistencyCheckerTool(BaseTool):
    """
    Tool for checking internal consistency of IACUC protocols.
    
    Validates animal numbers, personnel listings, timelines,
    and identifies contradictions or missing required elements.
    """
    
    name: str = "consistency_checker"
    description: str = (
        "Check a protocol document for internal consistency. "
        "Input is the full protocol text. "
        "Returns errors, warnings, and suggestions for fixes."
    )
    
    def _run(self, protocol_text: str) -> str:
        """
        Check protocol consistency and return formatted report.
        
        Args:
            protocol_text: The protocol text to check
            
        Returns:
            Formatted consistency report.
        """
        report = check_protocol_consistency(protocol_text)
        
        # Format output
        output = [
            "CONSISTENCY CHECK REPORT",
            "=" * 50,
            "",
            f"Status: {'✓ CONSISTENT' if report.is_consistent else '✗ INCONSISTENT'}",
            f"Total Issues: {report.total_issues}",
            "",
            report.summary,
        ]
        
        if report.errors:
            output.extend(["", "ERRORS (must fix):"])
            for i, error in enumerate(report.errors, 1):
                output.append(f"  {i}. [{error.category}] {error.description}")
                if error.suggestion:
                    output.append(f"     → {error.suggestion}")
        
        if report.warnings:
            output.extend(["", "WARNINGS (should review):"])
            for i, warning in enumerate(report.warnings, 1):
                output.append(f"  {i}. [{warning.category}] {warning.description}")
                if warning.suggestion:
                    output.append(f"     → {warning.suggestion}")
        
        if report.info:
            output.extend(["", "INFO:"])
            for i, info_item in enumerate(report.info, 1):
                output.append(f"  {i}. {info_item.description}")
        
        if report.total_issues == 0:
            output.extend(["", "No consistency issues found. Protocol appears complete and consistent."])
        
        return "\n".join(output)


# Export key items
__all__ = [
    "ConsistencyCheckerTool",
    "check_protocol_consistency",
    "check_animal_number_consistency",
    "check_personnel_consistency",
    "check_timeline_consistency",
    "check_required_sections",
    "check_contradictions",
    "extract_animal_numbers",
    "ConsistencyReport",
    "ConsistencyIssue",
]
