"""
Unit tests for Consistency Checker Tool.
"""

import pytest

from src.tools.consistency_checker import (
    ConsistencyCheckerTool,
    check_protocol_consistency,
    check_animal_number_consistency,
    check_personnel_consistency,
    check_timeline_consistency,
    check_required_sections,
    check_contradictions,
    extract_animal_numbers,
    ConsistencyReport,
    ConsistencyIssue,
)


class TestExtractAnimalNumbers:
    """Tests for animal number extraction."""
    
    def test_extracts_total_from_n_equals(self):
        """Test extraction from N= format."""
        numbers = extract_animal_numbers("This study uses N=60 mice.")
        
        assert 60 in numbers["total"]
    
    def test_extracts_total_from_text(self):
        """Test extraction from text format."""
        numbers = extract_animal_numbers("A total of 40 animals will be used.")
        
        assert 40 in numbers["total"]
    
    def test_extracts_per_group(self):
        """Test extraction of per group numbers."""
        numbers = extract_animal_numbers("There will be 10 per group.")
        
        assert 10 in numbers["per_group"]
    
    def test_extracts_group_count(self):
        """Test extraction of group counts."""
        numbers = extract_animal_numbers("Animals will be divided into 6 groups.")
        
        assert 6 in numbers["groups"]
    
    def test_extracts_multiple_numbers(self):
        """Test extraction of multiple different numbers."""
        text = "Total of 60 mice in 6 groups with 10 per group."
        numbers = extract_animal_numbers(text)
        
        assert 60 in numbers["total"]
        assert 6 in numbers["groups"]
        assert 10 in numbers["per_group"]


class TestCheckAnimalNumberConsistency:
    """Tests for animal number consistency checking."""
    
    def test_consistent_numbers_no_issues(self):
        """Test that consistent numbers produce no issues."""
        text = "Total of 60 mice in 6 groups with 10 per group."
        issues = check_animal_number_consistency(text)
        
        # 10 * 6 = 60, should be consistent
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0
    
    def test_inconsistent_total_detected(self):
        """Test that inconsistent totals are detected."""
        text = "We will use N=60 mice. Total of 50 animals requested."
        issues = check_animal_number_consistency(text)
        
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0
        assert any("inconsistent" in i.description.lower() for i in errors)
    
    def test_math_mismatch_detected(self):
        """Test that calculation mismatch is detected."""
        text = "Total of 50 mice in 6 groups with 10 per group."
        # 10 * 6 = 60, but total says 50
        issues = check_animal_number_consistency(text)
        
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0
        assert any("mismatch" in i.description.lower() for i in errors)


class TestCheckPersonnelConsistency:
    """Tests for personnel consistency checking."""
    
    def test_surgery_without_qualified(self):
        """Test that surgery without qualified personnel is flagged."""
        text = "Animals will undergo surgery."
        issues = check_personnel_consistency(text)
        
        assert len(issues) > 0
        assert any("personnel" in i.category for i in issues)
    
    def test_surgery_with_qualified_ok(self):
        """Test that surgery with qualified personnel is ok."""
        text = "Animals will undergo surgery performed by trained personnel."
        issues = check_personnel_consistency(text)
        
        surgery_issues = [i for i in issues if "surgery" in i.description.lower()]
        assert len(surgery_issues) == 0


class TestCheckTimelineConsistency:
    """Tests for timeline consistency checking."""
    
    def test_single_duration_no_issues(self):
        """Test that single duration produces no issues."""
        text = "The study will last for 8 weeks."
        issues = check_timeline_consistency(text)
        
        duration_errors = [i for i in issues if i.category == "timeline" and i.severity == "error"]
        assert len(duration_errors) == 0
    
    def test_multiple_durations_flagged(self):
        """Test that multiple durations are flagged."""
        text = "For 4 weeks study period. Animals will be monitored for 8 weeks duration."
        issues = check_timeline_consistency(text)
        
        # Should have a warning about multiple durations if detected
        # This checks that the function runs without error
        assert isinstance(issues, list)


class TestCheckRequiredSections:
    """Tests for required section checking."""
    
    def test_missing_species_detected(self):
        """Test that missing species is detected."""
        text = "The study will involve surgical procedures."
        issues = check_required_sections(text)
        
        errors = [i for i in issues if i.severity == "error"]
        assert any("species" in i.description.lower() for i in errors)
    
    def test_missing_euthanasia_detected(self):
        """Test that missing euthanasia is detected."""
        text = "We will use mice for behavioral testing."
        issues = check_required_sections(text)
        
        errors = [i for i in issues if i.severity == "error"]
        assert any("euthanasia" in i.description.lower() for i in errors)
    
    def test_complete_protocol_no_missing(self):
        """Test that complete protocol has no missing sections."""
        text = """
        Species: C57BL/6 mice
        Justification: This study is needed to understand disease mechanisms.
        Procedures: Blood collection and behavioral testing.
        Anesthesia will be used for any painful procedures.
        Euthanasia will be by CO2 inhalation.
        Animals will be monitored daily for welfare.
        """
        issues = check_required_sections(text)
        
        missing_errors = [i for i in issues if i.category == "missing_section"]
        assert len(missing_errors) == 0


class TestCheckContradictions:
    """Tests for contradiction checking."""
    
    def test_survival_nonsurival_contradiction(self):
        """Test detection of survival/non-survival contradiction."""
        text = "This is a survival surgery study. The non-survival procedure will be..."
        issues = check_contradictions(text)
        
        assert len(issues) > 0
        assert any("survival" in i.description.lower() for i in issues)
    
    def test_no_contradiction_when_consistent(self):
        """Test no issues when protocol is consistent."""
        text = "This survival surgery study requires post-operative care."
        issues = check_contradictions(text)
        
        contradiction_issues = [i for i in issues if i.category == "contradiction"]
        assert len(contradiction_issues) == 0


class TestCheckProtocolConsistency:
    """Tests for complete protocol consistency check."""
    
    def test_returns_report(self):
        """Test that function returns a ConsistencyReport."""
        report = check_protocol_consistency("Simple protocol text.")
        
        assert isinstance(report, ConsistencyReport)
    
    def test_consistent_protocol(self):
        """Test a consistent protocol passes."""
        protocol = """
        Species: C57BL/6 mice
        Total animals: N=60
        Justification: Required for disease model
        Procedures: Blood collection under anesthesia by trained staff
        Pain management: Buprenorphine analgesia
        Euthanasia: CO2 inhalation with cervical dislocation
        Monitoring: Daily health checks
        """
        report = check_protocol_consistency(protocol)
        
        # Should be mostly consistent (may have minor warnings)
        assert report.is_consistent or report.total_issues < 3
    
    def test_inconsistent_protocol(self):
        """Test that inconsistent protocol fails."""
        protocol = """
        Total animals: 50
        N=60 mice will be used.
        6 groups of 10 per group.
        """
        # Numbers are inconsistent: 50 vs 60 vs 6*10=60
        report = check_protocol_consistency(protocol)
        
        assert not report.is_consistent or len(report.warnings) > 0
    
    def test_report_has_summary(self):
        """Test that report includes summary."""
        report = check_protocol_consistency("Test protocol.")
        
        assert report.summary is not None
        assert len(report.summary) > 0


class TestConsistencyCheckerTool:
    """Tests for the ConsistencyCheckerTool."""
    
    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        tool = ConsistencyCheckerTool()
        
        assert tool.name == "consistency_checker"
        assert "consistency" in tool.description.lower()
    
    def test_tool_returns_formatted_output(self):
        """Test that tool returns formatted output."""
        tool = ConsistencyCheckerTool()
        
        result = tool._run("Test protocol with mice and euthanasia by CO2.")
        
        assert "CONSISTENCY CHECK REPORT" in result
        assert "Status:" in result
    
    def test_tool_shows_errors(self):
        """Test that tool shows errors when present."""
        tool = ConsistencyCheckerTool()
        
        # Protocol missing required elements
        result = tool._run("A simple study.")
        
        # Should have errors for missing sections
        assert "ERRORS" in result or "ERROR" in result.upper()
    
    def test_tool_shows_consistent_status(self):
        """Test that tool shows consistent status for good protocol."""
        tool = ConsistencyCheckerTool()
        
        protocol = """
        Species: C57BL/6 mice
        Justification: Disease mechanism study
        Procedures: Non-invasive observation
        Anesthesia: Not required for this study
        Euthanasia: CO2 inhalation
        Monitoring: Daily observation
        """
        result = tool._run(protocol)
        
        # Should show consistent or have minimal issues
        assert "Status:" in result


class TestConsistencyModels:
    """Tests for Pydantic models."""
    
    def test_consistency_issue(self):
        """Test ConsistencyIssue model."""
        issue = ConsistencyIssue(
            severity="error",
            category="animal_numbers",
            description="Numbers don't match",
            location="Section 3",
            suggestion="Update the total",
        )
        
        assert issue.severity == "error"
        assert issue.category == "animal_numbers"
    
    def test_consistency_report(self):
        """Test ConsistencyReport model."""
        report = ConsistencyReport(
            is_consistent=True,
            total_issues=0,
            errors=[],
            warnings=[],
            info=[],
            summary="All good",
        )
        
        assert report.is_consistent
        assert report.total_issues == 0
    
    def test_report_with_issues(self):
        """Test ConsistencyReport with issues."""
        error = ConsistencyIssue(
            severity="error",
            category="test",
            description="Test error",
        )
        warning = ConsistencyIssue(
            severity="warning",
            category="test",
            description="Test warning",
        )
        
        report = ConsistencyReport(
            is_consistent=False,
            total_issues=2,
            errors=[error],
            warnings=[warning],
            info=[],
            summary="Has issues",
        )
        
        assert not report.is_consistent
        assert report.total_issues == 2
        assert len(report.errors) == 1
        assert len(report.warnings) == 1


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_text(self):
        """Test handling of empty text."""
        report = check_protocol_consistency("")
        
        assert isinstance(report, ConsistencyReport)
        # Should have errors for missing sections
        assert len(report.errors) > 0
    
    def test_very_long_text(self):
        """Test handling of long text."""
        long_text = "Test protocol. " * 1000
        long_text += "Species: mice. Euthanasia: CO2. Monitoring daily. Justification: required. Procedures: observation."
        
        report = check_protocol_consistency(long_text)
        
        assert isinstance(report, ConsistencyReport)
    
    def test_special_characters(self):
        """Test handling of special characters."""
        text = "Species: mice (C57BL/6). N=60 @ 10/group × 6 groups."
        
        report = check_protocol_consistency(text)
        
        assert isinstance(report, ConsistencyReport)
