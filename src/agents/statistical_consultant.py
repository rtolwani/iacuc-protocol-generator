"""
Statistical Consultant Agent.

An agent that validates sample sizes, recommends statistical approaches,
and ensures appropriate experimental design for IACUC protocols.
"""

from crewai import Agent, Task, Crew

from src.agents.llm import get_llm
from src.tools.power_analysis_tool import (
    PowerAnalysisTool,
    perform_power_analysis,
    EFFECT_SIZE_GUIDELINES,
)


# Common experimental designs
EXPERIMENTAL_DESIGNS = {
    "parallel": {
        "name": "Parallel Group Design",
        "description": "Different groups receive different treatments simultaneously",
        "advantages": ["Simple to implement", "No carryover effects"],
        "disadvantages": ["Requires more animals", "Inter-subject variability"],
        "recommended_for": ["Acute studies", "Toxicity studies", "Most behavioral studies"],
    },
    "crossover": {
        "name": "Crossover Design",
        "description": "Same animals receive all treatments in sequence",
        "advantages": ["Fewer animals needed", "Controls for individual variation"],
        "disadvantages": ["Carryover effects possible", "Longer study duration"],
        "recommended_for": ["Chronic studies", "Pharmacokinetic studies"],
    },
    "factorial": {
        "name": "Factorial Design",
        "description": "Multiple factors tested simultaneously",
        "advantages": ["Tests interactions", "More efficient"],
        "disadvantages": ["Complex analysis", "More groups needed"],
        "recommended_for": ["Dose-response studies", "Drug combination studies"],
    },
    "repeated_measures": {
        "name": "Repeated Measures Design",
        "description": "Same animals measured at multiple time points",
        "advantages": ["Tracks changes over time", "Reduces variability"],
        "disadvantages": ["Practice effects", "Dropout bias"],
        "recommended_for": ["Longitudinal studies", "Learning studies"],
    },
}


# Statistical test selection guide
STATISTICAL_TESTS = {
    "t_test": {
        "name": "Student's t-test",
        "use_when": "Comparing means of 2 groups",
        "assumptions": ["Normal distribution", "Equal variances (for unpaired)"],
        "alternatives": ["Mann-Whitney U (non-parametric)", "Welch's t-test (unequal variances)"],
    },
    "anova": {
        "name": "One-way ANOVA",
        "use_when": "Comparing means of 3+ groups",
        "assumptions": ["Normal distribution", "Homogeneity of variances"],
        "alternatives": ["Kruskal-Wallis (non-parametric)", "Welch's ANOVA"],
        "post_hoc": ["Tukey HSD", "Bonferroni", "Dunnett (vs control)"],
    },
    "two_way_anova": {
        "name": "Two-way ANOVA",
        "use_when": "Testing effects of 2 factors and their interaction",
        "assumptions": ["Normal distribution", "Homogeneity of variances"],
        "alternatives": ["Aligned rank transform ANOVA"],
    },
    "repeated_measures_anova": {
        "name": "Repeated Measures ANOVA",
        "use_when": "Comparing same subjects across 3+ time points",
        "assumptions": ["Sphericity", "Normal distribution"],
        "alternatives": ["Friedman test (non-parametric)", "Mixed-effects model"],
    },
    "chi_square": {
        "name": "Chi-square test",
        "use_when": "Comparing categorical outcomes",
        "assumptions": ["Expected frequencies ≥ 5"],
        "alternatives": ["Fisher's exact test (small samples)"],
    },
    "survival": {
        "name": "Survival Analysis",
        "use_when": "Time-to-event data",
        "methods": ["Kaplan-Meier curves", "Log-rank test", "Cox regression"],
        "assumptions": ["Non-informative censoring"],
    },
}


def recommend_statistical_test(
    n_groups: int,
    data_type: str,
    repeated_measures: bool = False,
) -> dict:
    """
    Recommend appropriate statistical test.
    
    Args:
        n_groups: Number of groups to compare
        data_type: Type of data (continuous, categorical, time_to_event)
        repeated_measures: Whether same subjects measured multiple times
        
    Returns:
        Dictionary with test recommendation and alternatives.
    """
    if data_type == "time_to_event":
        return {
            "recommended": STATISTICAL_TESTS["survival"],
            "reason": "Time-to-event data requires survival analysis methods",
        }
    
    if data_type == "categorical":
        return {
            "recommended": STATISTICAL_TESTS["chi_square"],
            "reason": "Categorical outcomes require chi-square or Fisher's exact test",
        }
    
    # Continuous data
    if n_groups == 2:
        if repeated_measures:
            return {
                "recommended": {
                    "name": "Paired t-test",
                    "use_when": "Comparing same subjects at 2 time points",
                    "alternatives": ["Wilcoxon signed-rank test"],
                },
                "reason": "Two time points with same subjects requires paired analysis",
            }
        return {
            "recommended": STATISTICAL_TESTS["t_test"],
            "reason": "Comparing two independent groups with continuous outcome",
        }
    
    # 3+ groups
    if repeated_measures:
        return {
            "recommended": STATISTICAL_TESTS["repeated_measures_anova"],
            "reason": "Multiple time points with same subjects",
        }
    
    return {
        "recommended": STATISTICAL_TESTS["anova"],
        "reason": f"Comparing {n_groups} independent groups with continuous outcome",
    }


def validate_sample_size(
    proposed_n: int,
    test_type: str,
    effect_size: float,
    n_groups: int = 2,
    power: float = 0.80,
    alpha: float = 0.05,
) -> dict:
    """
    Validate a proposed sample size.
    
    Args:
        proposed_n: Proposed sample size per group
        test_type: Type of statistical test
        effect_size: Expected effect size
        n_groups: Number of groups
        power: Desired power
        alpha: Significance level
        
    Returns:
        Dictionary with validation results.
    """
    result = perform_power_analysis(
        test_type=test_type,
        effect_size=effect_size,
        n_groups=n_groups,
        power=power,
        alpha=alpha,
    )
    
    required_n = result.sample_size_per_group
    
    if proposed_n >= required_n:
        status = "ADEQUATE"
        message = f"Sample size of {proposed_n} meets or exceeds the required {required_n} per group."
    elif proposed_n >= required_n * 0.9:
        status = "MARGINAL"
        message = f"Sample size of {proposed_n} is slightly below the ideal {required_n}. Consider increasing."
    else:
        status = "INADEQUATE"
        message = f"Sample size of {proposed_n} is below the required {required_n} per group for {power:.0%} power."
    
    return {
        "status": status,
        "proposed_n": proposed_n,
        "required_n": required_n,
        "power": power,
        "effect_size": effect_size,
        "message": message,
        "full_analysis": result,
    }


def create_statistical_consultant_agent() -> Agent:
    """
    Create a Statistical Consultant agent.
    
    This agent:
    - Validates sample size calculations
    - Recommends appropriate statistical tests
    - Reviews experimental designs
    - Supports the Reduction principle of 3Rs
    
    Returns:
        Configured CrewAI Agent instance.
    """
    llm = get_llm()
    power_tool = PowerAnalysisTool()
    
    return Agent(
        role="Statistical Consultant",
        goal=(
            "Ensure appropriate statistical design and sample size calculations "
            "for IACUC protocols. Validate that studies use the minimum number "
            "of animals needed for scientific validity while maintaining "
            "adequate statistical power."
        ),
        backstory=(
            "You are an experienced biostatistician who specializes in animal "
            "research. You have reviewed thousands of IACUC protocols and helped "
            "researchers optimize their experimental designs. You understand both "
            "the scientific need for adequate sample sizes and the ethical "
            "imperative to minimize animal use. You're an expert in power "
            "analysis, experimental design, and statistical methods for "
            "preclinical research."
        ),
        llm=llm,
        tools=[power_tool],
        verbose=False,
        allow_delegation=False,
    )


def create_statistical_review_task(
    agent: Agent,
    study_design: str,
    proposed_sample_size: int,
    n_groups: int,
    primary_outcome: str,
    expected_effect: str,
) -> Task:
    """
    Create a task for statistical review.
    
    Args:
        agent: The Statistical Consultant agent
        study_design: Description of study design
        proposed_sample_size: Proposed sample size per group
        n_groups: Number of groups
        primary_outcome: Primary outcome measure
        expected_effect: Expected effect or effect size
        
    Returns:
        Configured CrewAI Task instance.
    """
    return Task(
        description=f"""
Review the statistical aspects of this IACUC protocol:

STUDY DESIGN: {study_design}
PROPOSED SAMPLE SIZE: {proposed_sample_size} per group
NUMBER OF GROUPS: {n_groups}
PRIMARY OUTCOME: {primary_outcome}
EXPECTED EFFECT: {expected_effect}

Your review must include:

1. SAMPLE SIZE VALIDATION:
   - Use the power_analysis tool to verify the proposed sample size
   - Determine if the sample size provides adequate power (≥80%)
   - If inadequate, recommend the appropriate sample size

2. STATISTICAL TEST RECOMMENDATION:
   - Identify the appropriate statistical test for the primary outcome
   - Note any assumptions that must be met
   - Suggest alternatives if data doesn't meet assumptions

3. EXPERIMENTAL DESIGN ASSESSMENT:
   - Evaluate if the design is appropriate for the study objectives
   - Identify potential confounds or biases
   - Recommend improvements if needed

4. REDUCTION OPPORTUNITIES:
   - Suggest ways to reduce animal numbers while maintaining power
   - Consider alternative designs (crossover, repeated measures)
   - Identify if pilot data could help refine estimates

Provide a comprehensive statistical assessment with specific recommendations.
""",
        expected_output=(
            "A statistical review with sample size validation, test recommendations, "
            "design assessment, and reduction opportunities."
        ),
        agent=agent,
    )


def review_protocol_statistics(
    study_design: str,
    proposed_sample_size: int,
    n_groups: int,
    primary_outcome: str,
    expected_effect: str,
    verbose: bool = False,
) -> dict:
    """
    Review statistical aspects of a protocol.
    
    Main entry point for statistical review.
    
    Args:
        study_design: Description of study design
        proposed_sample_size: Proposed sample size per group
        n_groups: Number of groups
        primary_outcome: Primary outcome measure
        expected_effect: Expected effect description
        verbose: Whether to show agent reasoning
        
    Returns:
        Dictionary with statistical review results.
    """
    # Create agent and task
    agent = create_statistical_consultant_agent()
    if verbose:
        agent.verbose = True
    
    task = create_statistical_review_task(
        agent=agent,
        study_design=study_design,
        proposed_sample_size=proposed_sample_size,
        n_groups=n_groups,
        primary_outcome=primary_outcome,
        expected_effect=expected_effect,
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=verbose,
    )
    
    # Run the review
    agent_result = crew.kickoff()
    
    return {
        "study_design": study_design,
        "proposed_sample_size": proposed_sample_size,
        "n_groups": n_groups,
        "primary_outcome": primary_outcome,
        "detailed_review": str(agent_result),
    }


# Quick statistical check without LLM
def quick_statistical_check(
    proposed_n: int,
    n_groups: int = 2,
    effect_size: float = 0.5,
    test_type: str = "t_test",
    data_type: str = "continuous",
    repeated_measures: bool = False,
) -> dict:
    """
    Quick statistical check without LLM calls.
    
    Args:
        proposed_n: Proposed sample size per group
        n_groups: Number of groups
        effect_size: Expected effect size
        test_type: Type of statistical test
        data_type: Type of data (continuous, categorical, time_to_event)
        repeated_measures: Whether same subjects measured multiple times
        
    Returns:
        Dictionary with quick statistical assessment.
    """
    # Validate sample size
    validation = validate_sample_size(
        proposed_n=proposed_n,
        test_type=test_type,
        effect_size=effect_size,
        n_groups=n_groups,
    )
    
    # Recommend test
    test_recommendation = recommend_statistical_test(
        n_groups=n_groups,
        data_type=data_type,
        repeated_measures=repeated_measures,
    )
    
    return {
        "sample_size_validation": validation,
        "recommended_test": test_recommendation,
        "effect_size_used": effect_size,
        "effect_size_interpretation": EFFECT_SIZE_GUIDELINES.get(test_type, {}),
    }


# Export key items
__all__ = [
    "create_statistical_consultant_agent",
    "create_statistical_review_task",
    "review_protocol_statistics",
    "quick_statistical_check",
    "validate_sample_size",
    "recommend_statistical_test",
    "EXPERIMENTAL_DESIGNS",
    "STATISTICAL_TESTS",
]
