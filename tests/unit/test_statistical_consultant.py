"""
Unit tests for Statistical Consultant Agent.
"""

import pytest

from src.agents.statistical_consultant import (
    create_statistical_consultant_agent,
    create_statistical_review_task,
    validate_sample_size,
    recommend_statistical_test,
    quick_statistical_check,
    EXPERIMENTAL_DESIGNS,
    STATISTICAL_TESTS,
)


class TestExperimentalDesigns:
    """Tests for experimental design definitions."""
    
    def test_common_designs_defined(self):
        """Test that common designs are defined."""
        assert "parallel" in EXPERIMENTAL_DESIGNS
        assert "crossover" in EXPERIMENTAL_DESIGNS
        assert "factorial" in EXPERIMENTAL_DESIGNS
        assert "repeated_measures" in EXPERIMENTAL_DESIGNS
    
    def test_designs_have_required_fields(self):
        """Test that designs have required fields."""
        for design_name, design_info in EXPERIMENTAL_DESIGNS.items():
            assert "name" in design_info
            assert "description" in design_info
            assert "advantages" in design_info
            assert "disadvantages" in design_info


class TestStatisticalTests:
    """Tests for statistical test definitions."""
    
    def test_common_tests_defined(self):
        """Test that common tests are defined."""
        assert "t_test" in STATISTICAL_TESTS
        assert "anova" in STATISTICAL_TESTS
        assert "chi_square" in STATISTICAL_TESTS
        assert "survival" in STATISTICAL_TESTS
    
    def test_tests_have_required_fields(self):
        """Test that tests have required fields."""
        for test_name, test_info in STATISTICAL_TESTS.items():
            assert "name" in test_info
            assert "use_when" in test_info


class TestRecommendStatisticalTest:
    """Tests for test recommendation function."""
    
    def test_two_groups_continuous(self):
        """Test recommendation for 2 groups with continuous data."""
        result = recommend_statistical_test(
            n_groups=2,
            data_type="continuous",
            repeated_measures=False,
        )
        
        assert "t-test" in result["recommended"]["name"].lower()
    
    def test_three_groups_continuous(self):
        """Test recommendation for 3+ groups with continuous data."""
        result = recommend_statistical_test(
            n_groups=4,
            data_type="continuous",
            repeated_measures=False,
        )
        
        assert "anova" in result["recommended"]["name"].lower()
    
    def test_repeated_measures(self):
        """Test recommendation for repeated measures."""
        result = recommend_statistical_test(
            n_groups=3,
            data_type="continuous",
            repeated_measures=True,
        )
        
        assert "repeated" in result["recommended"]["name"].lower()
    
    def test_categorical_data(self):
        """Test recommendation for categorical data."""
        result = recommend_statistical_test(
            n_groups=2,
            data_type="categorical",
        )
        
        assert "chi" in result["recommended"]["name"].lower()
    
    def test_survival_data(self):
        """Test recommendation for time-to-event data."""
        result = recommend_statistical_test(
            n_groups=2,
            data_type="time_to_event",
        )
        
        assert "survival" in result["recommended"]["name"].lower()
    
    def test_includes_reason(self):
        """Test that recommendation includes reasoning."""
        result = recommend_statistical_test(
            n_groups=2,
            data_type="continuous",
        )
        
        assert "reason" in result
        assert len(result["reason"]) > 10


class TestValidateSampleSize:
    """Tests for sample size validation."""
    
    def test_adequate_sample_size(self):
        """Test validation of adequate sample size."""
        result = validate_sample_size(
            proposed_n=100,
            test_type="t_test",
            effect_size=0.5,
        )
        
        assert result["status"] == "ADEQUATE"
        assert result["proposed_n"] == 100
    
    def test_inadequate_sample_size(self):
        """Test validation of inadequate sample size."""
        result = validate_sample_size(
            proposed_n=5,  # Too small for medium effect
            test_type="t_test",
            effect_size=0.5,
        )
        
        assert result["status"] == "INADEQUATE"
        assert result["required_n"] > result["proposed_n"]
    
    def test_marginal_sample_size(self):
        """Test validation of marginally adequate sample size."""
        # First get the required n
        adequate_result = validate_sample_size(
            proposed_n=1000,  # Definitely adequate
            test_type="t_test",
            effect_size=0.5,
        )
        required = adequate_result["required_n"]
        
        # Test with marginally less
        marginal_n = int(required * 0.92)  # 8% below required
        result = validate_sample_size(
            proposed_n=marginal_n,
            test_type="t_test",
            effect_size=0.5,
        )
        
        assert result["status"] in ["MARGINAL", "INADEQUATE"]
    
    def test_includes_full_analysis(self):
        """Test that validation includes full power analysis."""
        result = validate_sample_size(
            proposed_n=50,
            test_type="t_test",
            effect_size=0.5,
        )
        
        assert "full_analysis" in result
        assert result["full_analysis"].power == 0.80


class TestQuickStatisticalCheck:
    """Tests for quick statistical check function."""
    
    def test_returns_validation_and_recommendation(self):
        """Test that quick check returns both validation and recommendation."""
        result = quick_statistical_check(
            proposed_n=50,
            n_groups=2,
            effect_size=0.5,
        )
        
        assert "sample_size_validation" in result
        assert "recommended_test" in result
    
    def test_validates_adequate_sample(self):
        """Test quick check with adequate sample."""
        result = quick_statistical_check(
            proposed_n=100,
            n_groups=2,
            effect_size=0.5,
            test_type="t_test",
        )
        
        assert result["sample_size_validation"]["status"] == "ADEQUATE"
    
    def test_recommends_appropriate_test(self):
        """Test quick check recommends appropriate test."""
        result = quick_statistical_check(
            proposed_n=50,
            n_groups=4,
            data_type="continuous",
        )
        
        assert "anova" in result["recommended_test"]["recommended"]["name"].lower()
    
    def test_includes_effect_size_info(self):
        """Test that effect size information is included."""
        result = quick_statistical_check(
            proposed_n=50,
            test_type="t_test",
        )
        
        assert "effect_size_used" in result


class TestStatisticalConsultantAgent:
    """Tests for agent creation."""
    
    def test_create_agent(self):
        """Test that agent is created with correct configuration."""
        agent = create_statistical_consultant_agent()
        
        assert agent.role == "Statistical Consultant"
        assert "statistical" in agent.goal.lower() or "sample size" in agent.goal.lower()
    
    def test_agent_has_power_tool(self):
        """Test that agent has power analysis tool."""
        agent = create_statistical_consultant_agent()
        
        tool_names = [t.name for t in agent.tools]
        assert "power_analysis" in tool_names
    
    def test_agent_backstory_includes_expertise(self):
        """Test that agent backstory mentions statistical expertise."""
        agent = create_statistical_consultant_agent()
        
        backstory_lower = agent.backstory.lower()
        assert "statistic" in backstory_lower or "power" in backstory_lower


class TestStatisticalReviewTask:
    """Tests for task creation."""
    
    def test_create_task(self):
        """Test that task is created with correct content."""
        agent = create_statistical_consultant_agent()
        task = create_statistical_review_task(
            agent=agent,
            study_design="Parallel group, randomized",
            proposed_sample_size=15,
            n_groups=2,
            primary_outcome="Tumor volume",
            expected_effect="50% reduction",
        )
        
        assert task.agent == agent
        assert "15" in task.description
        assert "Tumor volume" in task.description
    
    def test_task_includes_key_sections(self):
        """Test that task description includes key review sections."""
        agent = create_statistical_consultant_agent()
        task = create_statistical_review_task(
            agent=agent,
            study_design="Crossover",
            proposed_sample_size=10,
            n_groups=2,
            primary_outcome="Blood pressure",
            expected_effect="10 mmHg decrease",
        )
        
        description_lower = task.description.lower()
        
        assert "sample size" in description_lower
        assert "statistical test" in description_lower
        assert "design" in description_lower
    
    def test_task_mentions_reduction(self):
        """Test that task mentions reduction principle."""
        agent = create_statistical_consultant_agent()
        task = create_statistical_review_task(
            agent=agent,
            study_design="Parallel",
            proposed_sample_size=20,
            n_groups=3,
            primary_outcome="Weight",
            expected_effect="Large",
        )
        
        description_lower = task.description.lower()
        assert "reduction" in description_lower or "reduce" in description_lower


class TestIntegration:
    """Integration tests (without actual LLM calls)."""
    
    def test_workflow_setup(self):
        """Test that full workflow can be set up."""
        agent = create_statistical_consultant_agent()
        task = create_statistical_review_task(
            agent=agent,
            study_design="Parallel group design",
            proposed_sample_size=10,
            n_groups=2,
            primary_outcome="Behavioral score",
            expected_effect="Medium (d=0.5)",
        )
        
        from crewai import Crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False,
        )
        
        assert len(crew.agents) == 1
        assert len(crew.tasks) == 1
    
    def test_quick_check_consistency(self):
        """Test that quick check gives consistent results."""
        result1 = quick_statistical_check(proposed_n=50, effect_size=0.5)
        result2 = quick_statistical_check(proposed_n=50, effect_size=0.5)
        
        assert result1["sample_size_validation"]["status"] == result2["sample_size_validation"]["status"]
        assert result1["sample_size_validation"]["required_n"] == result2["sample_size_validation"]["required_n"]
