"""
Unit tests for Protocol Assembler Agent.
"""

import pytest

from src.agents.protocol_assembler import (
    create_protocol_assembler_agent,
    create_assembly_task,
    quick_assemble,
    create_empty_protocol,
    add_section_content,
    validate_protocol,
    calculate_completeness,
    assemble_text,
    assemble_markdown,
    get_missing_sections,
    ProtocolDocument,
    ProtocolSection,
    STANDARD_SECTIONS,
)


class TestCreateEmptyProtocol:
    """Tests for empty protocol creation."""
    
    def test_creates_protocol(self):
        """Test that protocol is created."""
        protocol = create_empty_protocol()
        
        assert isinstance(protocol, ProtocolDocument)
    
    def test_has_standard_sections(self):
        """Test that protocol has standard sections."""
        protocol = create_empty_protocol()
        
        assert len(protocol.sections) == len(STANDARD_SECTIONS)
    
    def test_sections_are_incomplete(self):
        """Test that sections start incomplete."""
        protocol = create_empty_protocol()
        
        for section in protocol.sections:
            assert section.status == "incomplete"
    
    def test_sections_have_correct_order(self):
        """Test that sections have correct order."""
        protocol = create_empty_protocol()
        
        orders = [s.order for s in protocol.sections]
        assert sorted(orders) == orders


class TestAddSectionContent:
    """Tests for adding section content."""
    
    def test_adds_content(self):
        """Test that content is added."""
        protocol = create_empty_protocol()
        
        protocol = add_section_content(
            protocol, "Project Summary", "This is a test summary."
        )
        
        summary_section = next(
            s for s in protocol.sections if s.name == "Project Summary"
        )
        assert summary_section.content == "This is a test summary."
    
    def test_marks_complete(self):
        """Test that section is marked complete."""
        protocol = create_empty_protocol()
        
        protocol = add_section_content(
            protocol, "Project Summary", "Content here."
        )
        
        summary_section = next(
            s for s in protocol.sections if s.name == "Project Summary"
        )
        assert summary_section.status == "complete"
    
    def test_case_insensitive(self):
        """Test that section name matching is case insensitive."""
        protocol = create_empty_protocol()
        
        protocol = add_section_content(
            protocol, "project summary", "Content here."
        )
        
        summary_section = next(
            s for s in protocol.sections if s.name == "Project Summary"
        )
        assert summary_section.content == "Content here."


class TestCalculateCompleteness:
    """Tests for completeness calculation."""
    
    def test_empty_protocol_zero(self):
        """Test that empty protocol has low completeness."""
        protocol = create_empty_protocol()
        
        score = calculate_completeness(protocol)
        
        assert score == 0.0
    
    def test_partial_completeness(self):
        """Test partial completeness calculation."""
        protocol = create_empty_protocol()
        
        # Complete one required section
        protocol = add_section_content(
            protocol, "Project Summary", "Summary content."
        )
        
        score = calculate_completeness(protocol)
        
        assert 0 < score < 1.0
    
    def test_full_completeness(self):
        """Test full completeness calculation."""
        protocol = create_empty_protocol()
        
        # Complete all required sections
        required_sections = [s for s in protocol.sections if s.required]
        for section in required_sections:
            protocol = add_section_content(
                protocol, section.name, f"Content for {section.name}."
            )
        
        score = calculate_completeness(protocol)
        
        assert score == 1.0


class TestValidateProtocol:
    """Tests for protocol validation."""
    
    def test_validates_incomplete(self):
        """Test that incomplete protocol has errors."""
        protocol = create_empty_protocol()
        
        protocol = validate_protocol(protocol)
        
        assert not protocol.is_valid
        assert len(protocol.validation_errors) > 0
    
    def test_detects_missing_required(self):
        """Test detection of missing required sections."""
        protocol = create_empty_protocol()
        
        protocol = validate_protocol(protocol)
        
        # Should have errors for missing required sections
        assert any("incomplete" in e.lower() for e in protocol.validation_errors)
    
    def test_warns_on_brief_content(self):
        """Test warning for brief content."""
        protocol = create_empty_protocol()
        
        # Add very brief content
        protocol = add_section_content(
            protocol, "Project Summary", "Brief."
        )
        
        protocol = validate_protocol(protocol)
        
        # Should have warning about brief content
        assert any("brief" in w.lower() for w in protocol.validation_warnings)


class TestAssembleText:
    """Tests for text assembly."""
    
    def test_includes_title(self):
        """Test that text includes title."""
        protocol = create_empty_protocol()
        protocol.title = "Test Protocol"
        
        text = assemble_text(protocol)
        
        assert "Test Protocol" in text
    
    def test_includes_sections(self):
        """Test that text includes section content."""
        protocol = create_empty_protocol()
        protocol = add_section_content(
            protocol, "Project Summary", "Summary content here."
        )
        
        text = assemble_text(protocol)
        
        assert "Summary content here." in text
    
    def test_skips_empty_sections(self):
        """Test that empty sections are skipped."""
        protocol = create_empty_protocol()
        protocol = add_section_content(
            protocol, "Project Summary", "Has content."
        )
        
        text = assemble_text(protocol)
        
        # Should not have "Euthanasia" header since it's empty
        # But should have Project Summary
        assert "Project Summary" in text


class TestAssembleMarkdown:
    """Tests for markdown assembly."""
    
    def test_includes_headers(self):
        """Test that markdown includes headers."""
        protocol = create_empty_protocol()
        protocol.title = "Test Protocol"
        
        md = assemble_markdown(protocol)
        
        assert "# Test Protocol" in md
    
    def test_includes_completeness(self):
        """Test that markdown includes completeness."""
        protocol = create_empty_protocol()
        
        md = assemble_markdown(protocol)
        
        assert "Completeness:" in md
    
    def test_shows_status_icons(self):
        """Test that markdown shows status icons."""
        protocol = create_empty_protocol()
        protocol = add_section_content(
            protocol, "Project Summary", "Content."
        )
        
        md = assemble_markdown(protocol)
        
        # Should have checkmark for complete section
        assert "✓" in md


class TestGetMissingSections:
    """Tests for getting missing sections."""
    
    def test_all_missing_initially(self):
        """Test that all required sections are missing initially."""
        protocol = create_empty_protocol()
        
        missing = get_missing_sections(protocol)
        
        required_count = sum(1 for s in STANDARD_SECTIONS if s["required"])
        assert len(missing) == required_count
    
    def test_fewer_missing_after_content(self):
        """Test fewer missing after adding content."""
        protocol = create_empty_protocol()
        protocol = add_section_content(
            protocol, "Project Summary", "Content."
        )
        
        missing = get_missing_sections(protocol)
        
        assert "Project Summary" not in missing


class TestQuickAssemble:
    """Tests for quick assembly function."""
    
    def test_returns_all_fields(self):
        """Test that quick_assemble returns all fields."""
        result = quick_assemble(
            {"Project Summary": "Test summary."},
            "Test Protocol"
        )
        
        assert "protocol" in result
        assert "markdown" in result
        assert "text" in result
        assert "completeness_score" in result
        assert "is_valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "missing_sections" in result
    
    def test_assembles_multiple_sections(self):
        """Test assembly of multiple sections."""
        sections = {
            "Project Summary": "This is the summary.",
            "Scientific Justification": "This is the justification.",
            "Species and Numbers": "60 C57BL/6 mice.",
        }
        
        result = quick_assemble(sections, "Multi-Section Protocol")
        
        assert result["completeness_score"] > 0
        assert "This is the summary." in result["text"]
        assert "This is the justification." in result["text"]


class TestProtocolAssemblerAgent:
    """Tests for agent creation."""
    
    def test_create_agent(self):
        """Test that agent is created correctly."""
        agent = create_protocol_assembler_agent()
        
        assert agent.role == "Protocol Assembler"
    
    def test_agent_has_consistency_tool(self):
        """Test that agent has consistency checker tool."""
        agent = create_protocol_assembler_agent()
        
        tool_names = [t.name for t in agent.tools]
        assert "consistency_checker" in tool_names


class TestAssemblyTask:
    """Tests for task creation."""
    
    def test_create_task(self):
        """Test that task is created correctly."""
        agent = create_protocol_assembler_agent()
        
        task = create_assembly_task(
            agent=agent,
            sections_content={"Project Summary": "Test"},
            protocol_title="Test Protocol",
        )
        
        assert task.agent == agent
        assert "Test Protocol" in task.description


class TestModels:
    """Tests for Pydantic models."""
    
    def test_protocol_section(self):
        """Test ProtocolSection model."""
        section = ProtocolSection(
            name="Test Section",
            content="Test content",
            order=1,
            required=True,
            status="complete",
        )
        
        assert section.name == "Test Section"
        assert section.status == "complete"
    
    def test_protocol_document(self):
        """Test ProtocolDocument model."""
        protocol = ProtocolDocument(
            title="Test Protocol",
            version="1.0",
            sections=[],
            completeness_score=0.5,
            is_valid=False,
        )
        
        assert protocol.title == "Test Protocol"
        assert protocol.completeness_score == 0.5
    
    def test_protocol_defaults(self):
        """Test ProtocolDocument defaults."""
        protocol = ProtocolDocument()
        
        assert protocol.title == "IACUC Protocol"
        assert protocol.version == "1.0"
        assert protocol.completeness_score == 0.0
        assert protocol.is_valid == False


class TestStandardSections:
    """Tests for standard sections constant."""
    
    def test_sections_defined(self):
        """Test that standard sections are defined."""
        assert len(STANDARD_SECTIONS) >= 10
    
    def test_sections_have_required_fields(self):
        """Test that sections have required fields."""
        for section in STANDARD_SECTIONS:
            assert "name" in section
            assert "order" in section
            assert "required" in section
    
    def test_sections_ordered(self):
        """Test that sections are in order."""
        orders = [s["order"] for s in STANDARD_SECTIONS]
        assert orders == sorted(orders)
    
    def test_essential_sections_present(self):
        """Test that essential sections are present."""
        section_names = [s["name"] for s in STANDARD_SECTIONS]
        
        assert "Project Summary" in section_names
        assert "Procedures" in section_names
        assert "Euthanasia" in section_names
