"""
Power Analysis Tool.

Performs and validates sample size calculations for common statistical tests.
"""

import math
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from scipy import stats


class PowerAnalysisResult(BaseModel):
    """Result of a power analysis calculation."""
    
    test_type: str = Field(description="Type of statistical test")
    sample_size_per_group: int = Field(description="Required sample size per group")
    total_animals: int = Field(description="Total animals needed")
    power: float = Field(description="Statistical power (1 - beta)")
    alpha: float = Field(description="Significance level")
    effect_size: float = Field(description="Expected effect size")
    groups: int = Field(description="Number of groups")
    attrition_rate: float = Field(default=0.0, description="Expected attrition rate")
    adjusted_total: int = Field(description="Total with attrition adjustment")
    notes: str = Field(default="", description="Additional notes")


def calculate_t_test_sample_size(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_tailed: bool = True,
) -> int:
    """
    Calculate sample size for a two-sample t-test.
    
    Uses Cohen's d as effect size.
    
    Args:
        effect_size: Cohen's d (small=0.2, medium=0.5, large=0.8)
        alpha: Significance level (default 0.05)
        power: Desired power (default 0.80)
        two_tailed: Whether test is two-tailed (default True)
        
    Returns:
        Required sample size per group.
    """
    if two_tailed:
        alpha = alpha / 2
    
    z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    
    return math.ceil(n)


def calculate_anova_sample_size(
    effect_size: float,
    n_groups: int,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """
    Calculate sample size for one-way ANOVA.
    
    Uses Cohen's f as effect size.
    
    Args:
        effect_size: Cohen's f (small=0.1, medium=0.25, large=0.4)
        n_groups: Number of groups
        alpha: Significance level (default 0.05)
        power: Desired power (default 0.80)
        
    Returns:
        Required sample size per group.
    """
    # Using approximation for ANOVA power
    # Based on F-distribution approximation
    
    # Calculate non-centrality parameter lambda
    # For given n, lambda = n * k * f^2 where k = groups
    # We solve for n given desired power
    
    # Use iterative approach
    for n in range(3, 1000):
        df1 = n_groups - 1
        df2 = n_groups * (n - 1)
        
        # Non-centrality parameter
        ncp = n * n_groups * (effect_size ** 2)
        
        # Critical F value
        f_crit = stats.f.ppf(1 - alpha, df1, df2)
        
        # Calculate power (1 - beta)
        calculated_power = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)
        
        if calculated_power >= power:
            return n
    
    return 1000  # Cap at 1000


def calculate_chi_square_sample_size(
    effect_size: float,
    df: int = 1,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """
    Calculate sample size for chi-square test.
    
    Uses Cohen's w as effect size.
    
    Args:
        effect_size: Cohen's w (small=0.1, medium=0.3, large=0.5)
        df: Degrees of freedom
        alpha: Significance level (default 0.05)
        power: Desired power (default 0.80)
        
    Returns:
        Required total sample size.
    """
    # Using chi-square power formula
    # n = (z_alpha + z_beta)^2 / w^2
    
    z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    n = ((z_alpha + z_beta) / effect_size) ** 2
    
    # Adjust for df
    n = n * (1 + 0.1 * (df - 1))
    
    return math.ceil(n)


def adjust_for_attrition(sample_size: int, attrition_rate: float) -> int:
    """
    Adjust sample size for expected attrition.
    
    Args:
        sample_size: Base sample size
        attrition_rate: Expected attrition rate (0-1)
        
    Returns:
        Adjusted sample size.
    """
    if attrition_rate <= 0 or attrition_rate >= 1:
        return sample_size
    
    return math.ceil(sample_size / (1 - attrition_rate))


def get_effect_size_interpretation(
    effect_size: float,
    test_type: str,
) -> str:
    """
    Get interpretation of effect size.
    
    Args:
        effect_size: The effect size value
        test_type: Type of test (t_test, anova, chi_square)
        
    Returns:
        Interpretation string.
    """
    if test_type == "t_test":
        # Cohen's d
        if effect_size < 0.2:
            return "negligible"
        elif effect_size < 0.5:
            return "small"
        elif effect_size < 0.8:
            return "medium"
        else:
            return "large"
    elif test_type == "anova":
        # Cohen's f
        if effect_size < 0.1:
            return "negligible"
        elif effect_size < 0.25:
            return "small"
        elif effect_size < 0.4:
            return "medium"
        else:
            return "large"
    elif test_type == "chi_square":
        # Cohen's w
        if effect_size < 0.1:
            return "negligible"
        elif effect_size < 0.3:
            return "small"
        elif effect_size < 0.5:
            return "medium"
        else:
            return "large"
    
    return "unknown"


# Common effect sizes from literature
EFFECT_SIZE_GUIDELINES = {
    "t_test": {
        "small": 0.2,
        "medium": 0.5,
        "large": 0.8,
        "description": "Cohen's d",
    },
    "anova": {
        "small": 0.1,
        "medium": 0.25,
        "large": 0.4,
        "description": "Cohen's f",
    },
    "chi_square": {
        "small": 0.1,
        "medium": 0.3,
        "large": 0.5,
        "description": "Cohen's w",
    },
}


def perform_power_analysis(
    test_type: str,
    effect_size: float,
    n_groups: int = 2,
    alpha: float = 0.05,
    power: float = 0.80,
    attrition_rate: float = 0.0,
) -> PowerAnalysisResult:
    """
    Perform power analysis for a given test type.
    
    Args:
        test_type: Type of test (t_test, anova, chi_square)
        effect_size: Expected effect size
        n_groups: Number of groups (default 2)
        alpha: Significance level (default 0.05)
        power: Desired power (default 0.80)
        attrition_rate: Expected attrition rate (default 0)
        
    Returns:
        PowerAnalysisResult with sample size calculations.
    """
    test_type_lower = test_type.lower().replace("-", "_").replace(" ", "_")
    
    if test_type_lower in ["t_test", "ttest", "t"]:
        n_per_group = calculate_t_test_sample_size(effect_size, alpha, power)
        total = n_per_group * 2
        test_name = "Two-sample t-test"
        groups = 2
        
    elif test_type_lower in ["anova", "one_way_anova", "f_test"]:
        n_per_group = calculate_anova_sample_size(effect_size, n_groups, alpha, power)
        total = n_per_group * n_groups
        test_name = f"One-way ANOVA ({n_groups} groups)"
        groups = n_groups
        
    elif test_type_lower in ["chi_square", "chi2", "chisquare"]:
        total = calculate_chi_square_sample_size(effect_size, n_groups - 1, alpha, power)
        n_per_group = math.ceil(total / n_groups)
        test_name = "Chi-square test"
        groups = n_groups
        
    else:
        # Default to t-test
        n_per_group = calculate_t_test_sample_size(effect_size, alpha, power)
        total = n_per_group * 2
        test_name = "Two-sample t-test (default)"
        groups = 2
    
    adjusted_total = adjust_for_attrition(total, attrition_rate)
    
    interpretation = get_effect_size_interpretation(effect_size, test_type_lower.replace("ttest", "t_test"))
    
    return PowerAnalysisResult(
        test_type=test_name,
        sample_size_per_group=n_per_group,
        total_animals=total,
        power=power,
        alpha=alpha,
        effect_size=effect_size,
        groups=groups,
        attrition_rate=attrition_rate,
        adjusted_total=adjusted_total,
        notes=f"Effect size interpretation: {interpretation}",
    )


class PowerAnalysisTool(BaseTool):
    """
    Tool for performing power analysis and sample size calculations.
    
    Helps researchers determine appropriate sample sizes for their studies
    while minimizing animal use (supporting the Reduction principle of 3Rs).
    """
    
    name: str = "power_analysis"
    description: str = (
        "Calculate sample size for a study using power analysis. "
        "Input format: 'test_type: [t_test/anova/chi_square], effect_size: [value], "
        "groups: [number], alpha: [0.05], power: [0.80], attrition: [0.10]'. "
        "At minimum provide test_type and effect_size."
    )
    
    def _run(self, input_text: str) -> str:
        """
        Perform power analysis and return formatted results.
        
        Args:
            input_text: Parameters for power analysis
            
        Returns:
            Formatted power analysis results.
        """
        # Parse input
        test_type = "t_test"
        effect_size = 0.5  # Default medium
        n_groups = 2
        alpha = 0.05
        power = 0.80
        attrition = 0.0
        
        input_lower = input_text.lower()
        
        # Parse test type
        if "anova" in input_lower:
            test_type = "anova"
        elif "chi" in input_lower:
            test_type = "chi_square"
        elif "t_test" in input_lower or "t-test" in input_lower or "ttest" in input_lower:
            test_type = "t_test"
        
        # Parse numeric values
        parts = input_text.replace(",", " ").replace(":", " ").split()
        for i, part in enumerate(parts):
            try:
                val = float(part)
                prev_part = parts[i-1].lower() if i > 0 else ""
                
                if "effect" in prev_part:
                    effect_size = val
                elif "group" in prev_part:
                    n_groups = int(val)
                elif "alpha" in prev_part:
                    alpha = val
                elif "power" in prev_part:
                    power = val
                elif "attrition" in prev_part:
                    attrition = val
                elif 0 < val < 2 and effect_size == 0.5:  # Likely effect size
                    effect_size = val
            except (ValueError, IndexError):
                continue
        
        # Perform analysis
        result = perform_power_analysis(
            test_type=test_type,
            effect_size=effect_size,
            n_groups=n_groups,
            alpha=alpha,
            power=power,
            attrition_rate=attrition,
        )
        
        # Format output
        output = [
            "POWER ANALYSIS RESULTS",
            "=" * 50,
            "",
            f"Test Type: {result.test_type}",
            f"Effect Size: {result.effect_size} ({result.notes})",
            f"Alpha: {result.alpha}",
            f"Power: {result.power}",
            f"Number of Groups: {result.groups}",
            "",
            "SAMPLE SIZE REQUIREMENTS",
            "-" * 30,
            f"Per Group: {result.sample_size_per_group}",
            f"Total Animals: {result.total_animals}",
        ]
        
        if result.attrition_rate > 0:
            output.extend([
                "",
                f"Attrition Rate: {result.attrition_rate:.0%}",
                f"Adjusted Total: {result.adjusted_total}",
            ])
        
        output.extend([
            "",
            "RECOMMENDATION",
            "-" * 30,
            f"Minimum animals needed: {result.adjusted_total}",
            "",
            "Note: This calculation assumes normally distributed data",
            "and equal group sizes. Consult a statistician for complex designs.",
        ])
        
        return "\n".join(output)


# Export key items
__all__ = [
    "PowerAnalysisTool",
    "perform_power_analysis",
    "calculate_t_test_sample_size",
    "calculate_anova_sample_size",
    "calculate_chi_square_sample_size",
    "adjust_for_attrition",
    "PowerAnalysisResult",
    "EFFECT_SIZE_GUIDELINES",
]
