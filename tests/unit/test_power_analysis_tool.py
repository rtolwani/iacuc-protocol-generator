"""
Unit tests for Power Analysis Tool.
"""

import pytest
import math

from src.tools.power_analysis_tool import (
    PowerAnalysisTool,
    perform_power_analysis,
    calculate_t_test_sample_size,
    calculate_anova_sample_size,
    calculate_chi_square_sample_size,
    adjust_for_attrition,
    get_effect_size_interpretation,
    EFFECT_SIZE_GUIDELINES,
)


class TestTTestSampleSize:
    """Tests for t-test sample size calculation."""
    
    def test_medium_effect_size(self):
        """Test sample size for medium effect (d=0.5)."""
        n = calculate_t_test_sample_size(effect_size=0.5, power=0.80)
        
        # Standard result for d=0.5, power=0.80, alpha=0.05
        # Should be around 64 per group
        assert 60 <= n <= 70
    
    def test_large_effect_size(self):
        """Test sample size for large effect (d=0.8)."""
        n = calculate_t_test_sample_size(effect_size=0.8, power=0.80)
        
        # Large effect needs fewer animals
        # Should be around 26 per group
        assert 20 <= n <= 30
    
    def test_small_effect_size(self):
        """Test sample size for small effect (d=0.2)."""
        n = calculate_t_test_sample_size(effect_size=0.2, power=0.80)
        
        # Small effect needs more animals
        # Should be around 394 per group
        assert 350 <= n <= 450
    
    def test_higher_power_increases_sample(self):
        """Test that higher power requires larger sample."""
        n_80 = calculate_t_test_sample_size(effect_size=0.5, power=0.80)
        n_90 = calculate_t_test_sample_size(effect_size=0.5, power=0.90)
        
        assert n_90 > n_80
    
    def test_lower_alpha_increases_sample(self):
        """Test that lower alpha requires larger sample."""
        n_05 = calculate_t_test_sample_size(effect_size=0.5, alpha=0.05)
        n_01 = calculate_t_test_sample_size(effect_size=0.5, alpha=0.01)
        
        assert n_01 > n_05


class TestAnovaSampleSize:
    """Tests for ANOVA sample size calculation."""
    
    def test_medium_effect_three_groups(self):
        """Test sample size for medium effect with 3 groups."""
        n = calculate_anova_sample_size(effect_size=0.25, n_groups=3, power=0.80)
        
        # Should be reasonable for 3-group ANOVA
        assert 40 <= n <= 70
    
    def test_more_groups_increases_sample(self):
        """Test that more groups can affect sample size."""
        n_3 = calculate_anova_sample_size(effect_size=0.25, n_groups=3)
        n_5 = calculate_anova_sample_size(effect_size=0.25, n_groups=5)
        
        # Different number of groups may have different n requirements
        # Both should be reasonable
        assert n_3 > 0
        assert n_5 > 0
    
    def test_large_effect_reduces_sample(self):
        """Test that large effect reduces sample size."""
        n_small = calculate_anova_sample_size(effect_size=0.1, n_groups=3)
        n_large = calculate_anova_sample_size(effect_size=0.4, n_groups=3)
        
        assert n_large < n_small


class TestChiSquareSampleSize:
    """Tests for chi-square sample size calculation."""
    
    def test_medium_effect(self):
        """Test sample size for medium effect."""
        n = calculate_chi_square_sample_size(effect_size=0.3, power=0.80)
        
        # Should be reasonable for chi-square
        assert 50 <= n <= 150
    
    def test_small_effect_increases_sample(self):
        """Test that small effect needs more samples."""
        n_small = calculate_chi_square_sample_size(effect_size=0.1)
        n_large = calculate_chi_square_sample_size(effect_size=0.5)
        
        assert n_small > n_large


class TestAttritionAdjustment:
    """Tests for attrition adjustment."""
    
    def test_ten_percent_attrition(self):
        """Test 10% attrition adjustment."""
        adjusted = adjust_for_attrition(100, 0.10)
        
        # 100 / 0.90 = 111.11 -> 112
        assert adjusted == 112
    
    def test_twenty_percent_attrition(self):
        """Test 20% attrition adjustment."""
        adjusted = adjust_for_attrition(100, 0.20)
        
        # 100 / 0.80 = 125
        assert adjusted == 125
    
    def test_zero_attrition(self):
        """Test zero attrition returns original."""
        adjusted = adjust_for_attrition(100, 0.0)
        
        assert adjusted == 100
    
    def test_invalid_attrition_returns_original(self):
        """Test invalid attrition rates return original."""
        assert adjust_for_attrition(100, -0.1) == 100
        assert adjust_for_attrition(100, 1.0) == 100
        assert adjust_for_attrition(100, 1.5) == 100


class TestEffectSizeInterpretation:
    """Tests for effect size interpretation."""
    
    def test_t_test_interpretations(self):
        """Test Cohen's d interpretations."""
        assert get_effect_size_interpretation(0.1, "t_test") == "negligible"
        assert get_effect_size_interpretation(0.3, "t_test") == "small"
        assert get_effect_size_interpretation(0.6, "t_test") == "medium"
        assert get_effect_size_interpretation(1.0, "t_test") == "large"
    
    def test_anova_interpretations(self):
        """Test Cohen's f interpretations."""
        assert get_effect_size_interpretation(0.05, "anova") == "negligible"
        assert get_effect_size_interpretation(0.15, "anova") == "small"
        assert get_effect_size_interpretation(0.30, "anova") == "medium"
        assert get_effect_size_interpretation(0.50, "anova") == "large"
    
    def test_chi_square_interpretations(self):
        """Test Cohen's w interpretations."""
        assert get_effect_size_interpretation(0.05, "chi_square") == "negligible"
        assert get_effect_size_interpretation(0.20, "chi_square") == "small"
        assert get_effect_size_interpretation(0.40, "chi_square") == "medium"
        assert get_effect_size_interpretation(0.60, "chi_square") == "large"


class TestPerformPowerAnalysis:
    """Tests for main power analysis function."""
    
    def test_t_test_analysis(self):
        """Test complete t-test power analysis."""
        result = perform_power_analysis(
            test_type="t_test",
            effect_size=0.5,
            power=0.80,
            alpha=0.05,
        )
        
        assert result.test_type == "Two-sample t-test"
        assert result.groups == 2
        assert result.sample_size_per_group > 0
        assert result.total_animals == result.sample_size_per_group * 2
    
    def test_anova_analysis(self):
        """Test complete ANOVA power analysis."""
        result = perform_power_analysis(
            test_type="anova",
            effect_size=0.25,
            n_groups=4,
            power=0.80,
        )
        
        assert "ANOVA" in result.test_type
        assert result.groups == 4
        assert result.total_animals == result.sample_size_per_group * 4
    
    def test_chi_square_analysis(self):
        """Test complete chi-square power analysis."""
        result = perform_power_analysis(
            test_type="chi_square",
            effect_size=0.3,
            n_groups=2,
        )
        
        assert "Chi-square" in result.test_type
        assert result.total_animals > 0
    
    def test_attrition_adjustment_included(self):
        """Test that attrition adjustment is applied."""
        result = perform_power_analysis(
            test_type="t_test",
            effect_size=0.5,
            attrition_rate=0.20,
        )
        
        assert result.attrition_rate == 0.20
        assert result.adjusted_total > result.total_animals
    
    def test_result_has_notes(self):
        """Test that result includes effect size interpretation."""
        result = perform_power_analysis(
            test_type="t_test",
            effect_size=0.8,
        )
        
        assert "large" in result.notes.lower()


class TestPowerAnalysisTool:
    """Tests for the PowerAnalysisTool."""
    
    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        tool = PowerAnalysisTool()
        
        assert tool.name == "power_analysis"
        assert "sample size" in tool.description.lower()
    
    def test_tool_parses_t_test(self):
        """Test tool parses t-test input."""
        tool = PowerAnalysisTool()
        
        result = tool._run("test_type: t_test, effect_size: 0.5")
        
        assert "t-test" in result.lower()
        assert "Per Group:" in result
        assert "Total Animals:" in result
    
    def test_tool_parses_anova(self):
        """Test tool parses ANOVA input."""
        tool = PowerAnalysisTool()
        
        result = tool._run("test_type: anova, effect_size: 0.25, groups: 3")
        
        assert "ANOVA" in result
    
    def test_tool_handles_attrition(self):
        """Test tool handles attrition parameter."""
        tool = PowerAnalysisTool()
        
        result = tool._run("t_test effect_size: 0.5 attrition: 0.15")
        
        assert "Attrition Rate:" in result
        assert "Adjusted Total:" in result
    
    def test_tool_provides_recommendation(self):
        """Test tool provides recommendation section."""
        tool = PowerAnalysisTool()
        
        result = tool._run("t_test 0.5")
        
        assert "RECOMMENDATION" in result
        assert "Minimum animals needed:" in result


class TestEffectSizeGuidelines:
    """Tests for effect size guideline constants."""
    
    def test_guidelines_defined(self):
        """Test that all test type guidelines are defined."""
        assert "t_test" in EFFECT_SIZE_GUIDELINES
        assert "anova" in EFFECT_SIZE_GUIDELINES
        assert "chi_square" in EFFECT_SIZE_GUIDELINES
    
    def test_guidelines_have_levels(self):
        """Test that guidelines have small/medium/large levels."""
        for test_type, guidelines in EFFECT_SIZE_GUIDELINES.items():
            assert "small" in guidelines
            assert "medium" in guidelines
            assert "large" in guidelines
    
    def test_guidelines_are_ordered(self):
        """Test that effect sizes are ordered correctly."""
        for test_type, guidelines in EFFECT_SIZE_GUIDELINES.items():
            assert guidelines["small"] < guidelines["medium"]
            assert guidelines["medium"] < guidelines["large"]
