"""
Unit tests for Protocol Export.
"""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from src.protocol.schema import (
    Protocol,
    PersonnelInfo,
    AnimalInfo,
    ProcedureInfo,
    DrugInfo,
    HumaneEndpoint,
    USDACategory,
)
from src.protocol.export import (
    PDFExporter,
    MarkdownExporter,
    export_to_pdf,
    export_to_markdown,
)


@pytest.fixture
def sample_protocol():
    """Create sample protocol for testing."""
    return Protocol(
        title="Test Protocol for Export Testing Purposes",
        principal_investigator=PersonnelInfo(
            name="Dr. Test User",
            role="Principal Investigator",
            email="test@test.edu",
        ),
        department="Test Department",
        funding_sources=["NIH", "NSF"],
        study_duration="12 months",
        lay_summary="This is a test protocol for validating the export functionality. It contains all the necessary information to generate proper export files for IACUC submission review.",
        personnel=[
            PersonnelInfo(name="Dr. Test User", role="PI", qualifications=["PhD"]),
            PersonnelInfo(name="Student One", role="Graduate Student", qualifications=["Training Cert"]),
        ],
        animals=[
            AnimalInfo(
                species="Mouse",
                strain="C57BL/6J",
                sex="both",
                total_number=40,
                source="Jackson Laboratory",
            )
        ],
        usda_category=USDACategory.D,
        total_animals=40,
        animal_number_justification="Power analysis indicates n=10 per group × 4 groups = 40 mice",
        scientific_objectives="Test objective",
        scientific_rationale="Test rationale",
        potential_benefits="Test benefits",
        replacement_statement="Test replacement",
        reduction_statement="Test reduction",
        refinement_statement="Test refinement",
        experimental_design="Test design",
        statistical_methods="Test statistics",
        procedures=[
            ProcedureInfo(
                name="Test Procedure",
                description="This is a test procedure description",
                frequency="Daily",
            )
        ],
        anesthesia_protocols=[
            DrugInfo(
                drug_name="Isoflurane",
                dose="2%",
                route="Inhalation",
                purpose="Anesthesia",
            )
        ],
        analgesia_protocols=[
            DrugInfo(
                drug_name="Buprenorphine",
                dose="0.1 mg/kg",
                route="SC",
                purpose="Analgesia",
            )
        ],
        humane_endpoints=[
            HumaneEndpoint(
                criterion="Weight loss",
                measurement="Daily weighing",
                threshold=">20%",
                action="Euthanasia",
            )
        ],
        monitoring_schedule="Daily observation",
        euthanasia_method="CO2 followed by cervical dislocation",
    )


class TestPDFExporter:
    """Tests for PDFExporter class."""
    
    def test_create_exporter(self):
        """Test creating PDF exporter."""
        exporter = PDFExporter()
        assert exporter.institution_name == "University Research Institution"
    
    def test_create_exporter_custom_institution(self):
        """Test creating exporter with custom institution."""
        exporter = PDFExporter(institution_name="Test University")
        assert exporter.institution_name == "Test University"
    
    def test_export_returns_bytes(self, sample_protocol):
        """Test export returns bytes."""
        exporter = PDFExporter()
        result = exporter.export(sample_protocol)
        
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_export_starts_with_pdf_header(self, sample_protocol):
        """Test exported PDF has correct header."""
        exporter = PDFExporter()
        result = exporter.export(sample_protocol)
        
        # PDF files start with %PDF
        assert result[:4] == b'%PDF'
    
    def test_export_to_file(self, sample_protocol):
        """Test exporting PDF to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_protocol.pdf"
            
            exporter = PDFExporter()
            exporter.export(sample_protocol, output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0


class TestMarkdownExporter:
    """Tests for MarkdownExporter class."""
    
    def test_create_exporter(self):
        """Test creating Markdown exporter."""
        exporter = MarkdownExporter()
        assert exporter.institution_name == "University Research Institution"
    
    def test_export_returns_string(self, sample_protocol):
        """Test export returns string."""
        exporter = MarkdownExporter()
        result = exporter.export(sample_protocol)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_export_contains_title(self, sample_protocol):
        """Test export contains protocol title."""
        exporter = MarkdownExporter()
        result = exporter.export(sample_protocol)
        
        assert sample_protocol.title in result
    
    def test_export_contains_pi_name(self, sample_protocol):
        """Test export contains PI name."""
        exporter = MarkdownExporter()
        result = exporter.export(sample_protocol)
        
        assert sample_protocol.principal_investigator.name in result
    
    def test_export_contains_all_sections(self, sample_protocol):
        """Test export contains all 13 section headers."""
        exporter = MarkdownExporter()
        result = exporter.export(sample_protocol)
        
        expected_sections = [
            "1. General Information",
            "2. Lay Summary",
            "3. Personnel",
            "4. Species and Animal Numbers",
            "5. Rationale",
            "6. Alternatives",
            "7. Experimental Design",
            "8. Procedures",
            "9. Anesthesia",
            "11. Humane Endpoints",
            "12. Euthanasia",
            "13. Hazardous",
        ]
        
        for section in expected_sections:
            assert section in result, f"Missing section: {section}"
    
    def test_export_contains_tables(self, sample_protocol):
        """Test export contains markdown tables."""
        exporter = MarkdownExporter()
        result = exporter.export(sample_protocol)
        
        # Markdown tables have |---...| separators
        assert "|------" in result
    
    def test_export_to_file(self, sample_protocol):
        """Test exporting Markdown to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_protocol.md"
            
            exporter = MarkdownExporter()
            exporter.export(sample_protocol, output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            assert len(content) > 0


class TestExportToPdf:
    """Tests for export_to_pdf convenience function."""
    
    def test_export_to_pdf(self, sample_protocol):
        """Test convenience function."""
        result = export_to_pdf(sample_protocol)
        
        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'
    
    def test_export_to_pdf_with_institution(self, sample_protocol):
        """Test with custom institution."""
        result = export_to_pdf(
            sample_protocol,
            institution_name="Custom University",
        )
        
        assert len(result) > 0


class TestExportToMarkdown:
    """Tests for export_to_markdown convenience function."""
    
    def test_export_to_markdown(self, sample_protocol):
        """Test convenience function."""
        result = export_to_markdown(sample_protocol)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_export_to_markdown_with_institution(self, sample_protocol):
        """Test with custom institution."""
        result = export_to_markdown(
            sample_protocol,
            institution_name="Custom University",
        )
        
        assert "Custom University" in result


class TestExportContent:
    """Tests for export content correctness."""
    
    def test_markdown_has_usda_category(self, sample_protocol):
        """Test USDA category is included."""
        result = export_to_markdown(sample_protocol)
        
        assert sample_protocol.usda_category.value in result
    
    def test_markdown_has_animal_numbers(self, sample_protocol):
        """Test animal numbers are included."""
        result = export_to_markdown(sample_protocol)
        
        assert str(sample_protocol.total_animals) in result
    
    def test_markdown_has_euthanasia_method(self, sample_protocol):
        """Test euthanasia method is included."""
        result = export_to_markdown(sample_protocol)
        
        assert sample_protocol.euthanasia_method in result
    
    def test_markdown_has_endpoints(self, sample_protocol):
        """Test humane endpoints are included."""
        result = export_to_markdown(sample_protocol)
        
        for endpoint in sample_protocol.humane_endpoints:
            assert endpoint.criterion in result
    
    def test_markdown_has_drugs(self, sample_protocol):
        """Test drug information is included."""
        result = export_to_markdown(sample_protocol)
        
        for drug in sample_protocol.anesthesia_protocols:
            assert drug.drug_name in result
        
        for drug in sample_protocol.analgesia_protocols:
            assert drug.drug_name in result


class TestEmptyOptionalFields:
    """Tests for protocols with empty optional fields."""
    
    def test_export_without_personnel(self):
        """Test export works without additional personnel."""
        protocol = Protocol(
            title="Test Protocol for Export Without Personnel",
            principal_investigator=PersonnelInfo(
                name="Dr. Test",
                role="PI",
                email="test@test.edu",
            ),
            department="Test",
            study_duration="12 months",
            lay_summary="A" * 100,  # Meet minimum length
            animals=[AnimalInfo(species="Mouse", sex="both", total_number=10, source="vendor")],
            usda_category=USDACategory.C,
            total_animals=10,
            animal_number_justification="Test",
            scientific_objectives="Test",
            scientific_rationale="Test",
            potential_benefits="Test",
            replacement_statement="Test",
            reduction_statement="Test",
            refinement_statement="Test",
            experimental_design="Test",
            statistical_methods="Test",
            procedures=[ProcedureInfo(name="Test", description="Test")],
            humane_endpoints=[HumaneEndpoint(criterion="Test", measurement="Test", threshold="Test", action="Test")],
            monitoring_schedule="Test",
            euthanasia_method="CO2",
            personnel=[],  # Empty
        )
        
        # Should not raise
        result = export_to_markdown(protocol)
        assert "No additional personnel specified" in result
    
    def test_export_without_anesthesia(self):
        """Test export works without anesthesia protocols."""
        protocol = Protocol(
            title="Test Protocol for Export Without Anesthesia",
            principal_investigator=PersonnelInfo(
                name="Dr. Test",
                role="PI",
                email="test@test.edu",
            ),
            department="Test",
            study_duration="12 months",
            lay_summary="A" * 100,
            animals=[AnimalInfo(species="Mouse", sex="both", total_number=10, source="vendor")],
            usda_category=USDACategory.C,
            total_animals=10,
            animal_number_justification="Test",
            scientific_objectives="Test",
            scientific_rationale="Test",
            potential_benefits="Test",
            replacement_statement="Test",
            reduction_statement="Test",
            refinement_statement="Test",
            experimental_design="Test",
            statistical_methods="Test",
            procedures=[ProcedureInfo(name="Test", description="Test")],
            humane_endpoints=[HumaneEndpoint(criterion="Test", measurement="Test", threshold="Test", action="Test")],
            monitoring_schedule="Test",
            euthanasia_method="CO2",
            anesthesia_protocols=[],  # Empty
            analgesia_protocols=[],  # Empty
        )
        
        # Should not raise
        pdf_result = export_to_pdf(protocol)
        md_result = export_to_markdown(protocol)
        
        assert len(pdf_result) > 0
        assert len(md_result) > 0
