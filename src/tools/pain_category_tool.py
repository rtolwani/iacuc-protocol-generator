"""
Pain Category Classification Tool.

Classifies research procedures into USDA pain categories (B-E).
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# USDA Pain Category Definitions
PAIN_CATEGORIES = {
    "B": {
        "name": "Category B - Breeding/Holding",
        "description": (
            "Animals being bred, conditioned, or held for use in teaching, testing, "
            "experiments, research, or surgery but not yet used for such purposes."
        ),
        "examples": [
            "Animals held for breeding colony",
            "Animals in conditioning/acclimation",
            "Animals held as sentinels",
            "Animals awaiting use in procedures",
        ],
    },
    "C": {
        "name": "Category C - No Pain/Distress",
        "description": (
            "Animals upon which teaching, research, experiments, or tests will be conducted "
            "involving no pain, distress, or use of pain-relieving drugs."
        ),
        "examples": [
            "Behavioral observations only",
            "Non-invasive imaging",
            "Blood collection (small volumes)",
            "Euthanasia followed by tissue harvest",
            "Diet studies with standard feeds",
            "Non-stressful handling",
        ],
    },
    "D": {
        "name": "Category D - Pain/Distress with Relief",
        "description": (
            "Animals upon which experiments, teaching, research, surgery, or tests will be "
            "conducted involving accompanying pain or distress to the animals and for which "
            "appropriate anesthetic, analgesic, or tranquilizing drugs will be used."
        ),
        "examples": [
            "Survival surgery with anesthesia and analgesia",
            "Non-survival surgery under anesthesia",
            "Blood collection requiring anesthesia",
            "Tumor implantation with pain management",
            "Injections causing transient pain (with relief)",
            "Antibody production with adjuvants (managed)",
            "Restraint procedures with sedation",
        ],
    },
    "E": {
        "name": "Category E - Unrelieved Pain/Distress",
        "description": (
            "Animals upon which teaching, experiments, research, surgery, or tests will be "
            "conducted involving accompanying pain or distress to the animals and for which "
            "the use of appropriate anesthetic, analgesic, or tranquilizing drugs will "
            "adversely affect the procedures, results, or interpretation."
        ),
        "examples": [
            "Pain studies without analgesia",
            "Toxicity studies at lethal doses",
            "Tumor studies to endpoint without analgesia",
            "Infectious disease studies with morbidity",
            "Paralytic agents without anesthesia",
            "Food/water deprivation beyond normal",
            "Severe stress models",
        ],
        "requires_justification": True,
    },
}

# Keywords that indicate specific procedures
PROCEDURE_KEYWORDS = {
    "surgery": {
        "survival_surgery": ["survival surgery", "surgical procedure", "operative", "implant"],
        "non_survival": ["non-survival", "terminal surgery", "acute surgery"],
    },
    "pain_indicators": {
        "high_pain": [
            "unrelieved pain", "without analgesia", "no pain relief",
            "toxicity", "lethal dose", "LD50", "maximum tolerated dose",
            "tumor burden", "moribund", "death as endpoint",
        ],
        "moderate_pain": [
            "surgery", "incision", "injection", "implant", "catheter",
            "tumor", "inflammation", "adjuvant", "wound",
        ],
        "low_pain": [
            "blood draw", "blood collection", "venipuncture",
            "restraint", "handling", "gavage",
        ],
        "no_pain": [
            "observation", "behavioral", "non-invasive", "imaging",
            "euthanasia only", "tissue harvest post-mortem",
        ],
    },
    "relief_indicators": {
        "has_relief": [
            "anesthesia", "anesthetic", "analgesia", "analgesic",
            "pain relief", "pain management", "sedation", "isoflurane",
            "ketamine", "buprenorphine", "carprofen", "meloxicam",
        ],
        "no_relief": [
            "without anesthesia", "without analgesia", "no pain relief",
            "unrelieved", "untreated pain",
        ],
    },
}


class PainCategoryResult(BaseModel):
    """Result of pain category classification."""
    
    category: str = Field(description="USDA pain category (B, C, D, or E)")
    category_name: str = Field(description="Full category name")
    confidence: str = Field(description="Confidence level: high, medium, or low")
    reasoning: str = Field(description="Explanation for the classification")
    requires_justification: bool = Field(
        default=False, 
        description="Whether Category E justification is required"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for the protocol"
    )


def classify_pain_category(procedures: str) -> PainCategoryResult:
    """
    Classify procedures into USDA pain category.
    
    Args:
        procedures: Description of the research procedures
        
    Returns:
        PainCategoryResult with classification and reasoning
    """
    procedures_lower = procedures.lower()
    
    # Check for Category B (breeding/holding only)
    if _is_breeding_holding_only(procedures_lower):
        return PainCategoryResult(
            category="B",
            category_name=PAIN_CATEGORIES["B"]["name"],
            confidence="high",
            reasoning="Animals are only being bred, conditioned, or held - no procedures described.",
            requires_justification=False,
            recommendations=["Ensure animals are monitored for health and welfare."],
        )
    
    # Check for indicators
    has_pain_procedure = _has_pain_indicators(procedures_lower)
    has_high_pain = _has_high_pain_indicators(procedures_lower)
    has_relief = _has_relief_indicators(procedures_lower)
    has_no_relief = _has_no_relief_indicators(procedures_lower)
    
    # Category E: Unrelieved pain/distress
    if has_high_pain or (has_pain_procedure and has_no_relief):
        recommendations = [
            "Scientific justification for withholding pain relief is REQUIRED.",
            "Describe why anesthetics/analgesics would interfere with the study.",
            "Define humane endpoints to minimize suffering.",
            "Consider if pilot study with fewer animals is possible.",
        ]
        return PainCategoryResult(
            category="E",
            category_name=PAIN_CATEGORIES["E"]["name"],
            confidence="high" if has_high_pain else "medium",
            reasoning=_build_category_e_reasoning(procedures_lower, has_high_pain, has_no_relief),
            requires_justification=True,
            recommendations=recommendations,
        )
    
    # Category D: Pain with relief
    if has_pain_procedure and has_relief:
        recommendations = [
            "Document specific anesthetics/analgesics with doses.",
            "Include monitoring protocol during and after procedures.",
            "Define criteria for additional pain relief.",
        ]
        return PainCategoryResult(
            category="D",
            category_name=PAIN_CATEGORIES["D"]["name"],
            confidence="high",
            reasoning=_build_category_d_reasoning(procedures_lower),
            requires_justification=False,
            recommendations=recommendations,
        )
    
    # Category D: Pain procedure without explicit relief mentioned (assume D, recommend)
    if has_pain_procedure:
        recommendations = [
            "Specify anesthesia/analgesia plan - this appears to be Category D.",
            "If pain relief would interfere with study, provide justification for Category E.",
            "Document monitoring and humane endpoints.",
        ]
        return PainCategoryResult(
            category="D",
            category_name=PAIN_CATEGORIES["D"]["name"],
            confidence="medium",
            reasoning=(
                "Procedures involve potential pain but pain relief plan is not explicitly stated. "
                "Assuming Category D with appropriate pain management. If pain relief cannot be "
                "provided, scientific justification is required for Category E."
            ),
            requires_justification=False,
            recommendations=recommendations,
        )
    
    # Category C: No pain/distress
    recommendations = [
        "Ensure procedures remain non-invasive as described.",
        "Monitor for unexpected stress or distress.",
    ]
    return PainCategoryResult(
        category="C",
        category_name=PAIN_CATEGORIES["C"]["name"],
        confidence="high" if _is_clearly_category_c(procedures_lower) else "medium",
        reasoning="Procedures described do not involve pain or distress to animals.",
        requires_justification=False,
        recommendations=recommendations,
    )


def _is_breeding_holding_only(text: str) -> bool:
    """Check if procedures are only breeding/holding."""
    breeding_keywords = ["breeding", "holding", "colony maintenance", "sentinel"]
    procedure_keywords = ["surgery", "injection", "blood", "tumor", "implant", "treatment"]
    
    has_breeding = any(kw in text for kw in breeding_keywords)
    has_procedures = any(kw in text for kw in procedure_keywords)
    
    return has_breeding and not has_procedures


def _has_pain_indicators(text: str) -> bool:
    """Check if procedures involve potential pain."""
    all_pain_keywords = (
        PROCEDURE_KEYWORDS["pain_indicators"]["high_pain"] +
        PROCEDURE_KEYWORDS["pain_indicators"]["moderate_pain"] +
        PROCEDURE_KEYWORDS["pain_indicators"]["low_pain"]
    )
    return any(kw in text for kw in all_pain_keywords)


def _has_high_pain_indicators(text: str) -> bool:
    """Check for high pain/distress indicators."""
    return any(kw in text for kw in PROCEDURE_KEYWORDS["pain_indicators"]["high_pain"])


def _has_relief_indicators(text: str) -> bool:
    """Check if pain relief is mentioned."""
    return any(kw in text for kw in PROCEDURE_KEYWORDS["relief_indicators"]["has_relief"])


def _has_no_relief_indicators(text: str) -> bool:
    """Check if text explicitly states no pain relief."""
    return any(kw in text for kw in PROCEDURE_KEYWORDS["relief_indicators"]["no_relief"])


def _is_clearly_category_c(text: str) -> bool:
    """Check if procedures are clearly Category C."""
    return any(kw in text for kw in PROCEDURE_KEYWORDS["pain_indicators"]["no_pain"])


def _build_category_e_reasoning(text: str, has_high_pain: bool, has_no_relief: bool) -> str:
    """Build reasoning for Category E classification."""
    reasons = []
    
    if has_high_pain:
        found = [kw for kw in PROCEDURE_KEYWORDS["pain_indicators"]["high_pain"] if kw in text]
        reasons.append(f"High pain/distress indicators found: {', '.join(found[:3])}")
    
    if has_no_relief:
        reasons.append("Text indicates pain relief will not be provided")
    
    reasons.append(
        "Category E requires scientific justification explaining why pain relief "
        "would adversely affect the study."
    )
    
    return " ".join(reasons)


def _build_category_d_reasoning(text: str) -> str:
    """Build reasoning for Category D classification."""
    pain_found = []
    relief_found = []
    
    for kw in PROCEDURE_KEYWORDS["pain_indicators"]["moderate_pain"]:
        if kw in text:
            pain_found.append(kw)
    
    for kw in PROCEDURE_KEYWORDS["relief_indicators"]["has_relief"]:
        if kw in text:
            relief_found.append(kw)
    
    return (
        f"Procedures involving potential pain ({', '.join(pain_found[:3])}) "
        f"with appropriate pain relief ({', '.join(relief_found[:3])})."
    )


class PainCategoryTool(BaseTool):
    """
    Tool for classifying research procedures into USDA pain categories.
    
    Analyzes procedure descriptions and determines the appropriate
    USDA pain category (B, C, D, or E) based on the level of pain
    or distress and whether relief measures are provided.
    """
    
    name: str = "pain_category_classifier"
    description: str = (
        "Classify research procedures into USDA pain categories (B, C, D, or E). "
        "Input should be a description of the research procedures. Returns the "
        "pain category, reasoning, and recommendations."
    )
    
    def _run(self, procedures: str) -> str:
        """
        Classify procedures and return formatted results.
        
        Args:
            procedures: Description of research procedures
            
        Returns:
            Formatted classification results
        """
        result = classify_pain_category(procedures)
        
        output = [
            f"USDA Pain Category Classification",
            f"═══════════════════════════════════",
            f"",
            f"Category: {result.category} - {result.category_name}",
            f"Confidence: {result.confidence.upper()}",
            f"",
            f"Reasoning:",
            f"  {result.reasoning}",
        ]
        
        if result.requires_justification:
            output.extend([
                f"",
                f"⚠️  CATEGORY E JUSTIFICATION REQUIRED",
                f"  Scientific justification must explain why pain relief",
                f"  would adversely affect the procedures or results.",
            ])
        
        output.extend([
            f"",
            f"Recommendations:",
        ])
        for rec in result.recommendations:
            output.append(f"  • {rec}")
        
        return "\n".join(output)


# Expose key items for import
__all__ = [
    "PainCategoryTool",
    "classify_pain_category",
    "PainCategoryResult",
    "PAIN_CATEGORIES",
]
