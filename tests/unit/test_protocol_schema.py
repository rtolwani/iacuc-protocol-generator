"""
Unit tests for Protocol Data Models.
"""

import pytest
from datetime import date, datetime

from src.protocol.schema import (
    ProtocolStatus,
    USDACategory,
    PersonnelInfo,
    AnimalInfo,
    DrugInfo,
    ProcedureInfo,
    HumaneEndpoint,
    LiteratureSearch,
    ProtocolSection,
    Protocol,
    create_empty_protocol,
)


class TestProtocolStatus:
    """Tests for ProtocolStatus enum."""
    
    def test_all_statuses_exist(self):
        """Test all expected statuses exist."""
        expected = [
            "draft", "submitted", "under_review", "approved",
            "revision_requested", "expired", "suspended", "terminated"
        ]
        
        actual = [s.value for s in ProtocolStatus]
        
        for status in expected:
            assert status in actual


class TestUSDACategory:
    """Tests for USDACategory enum."""
    
    def test_all_categories_exist(self):
        """Test all USDA categories exist."""
        assert USDACategory.B.value == "B"
        assert USDACategory.C.value == "C"
        assert USDACategory.D.value == "D"
        assert USDACategory.E.value == "E"


class TestPersonnelInfo:
    """Tests for PersonnelInfo model."""
    
    def test_create_minimal(self):
        """Test creating with minimal fields."""
        person = PersonnelInfo(
            name="Dr. Jane Smith",
            role="Principal Investigator",
        )
        
        assert person.name == "Dr. Jane Smith"
        assert person.role == "Principal Investigator"
    
    def test_create_full(self):
        """Test creating with all fields."""
        person = PersonnelInfo(
            name="Dr. Jane Smith",
            role="Principal Investigator",
            email="jsmith@university.edu",
            phone="555-1234",
            department="Neuroscience",
            qualifications=["PhD", "IACUC Training"],
            responsibilities=["Protocol oversight", "Data analysis"],
        )
        
        assert len(person.qualifications) == 2
        assert len(person.responsibilities) == 2


class TestAnimalInfo:
    """Tests for AnimalInfo model."""
    
    def test_create_minimal(self):
        """Test creating with minimal fields."""
        animal = AnimalInfo(
            species="Mouse",
            sex="both",
            total_number=60,
            source="Jackson Laboratory",
        )
        
        assert animal.species == "Mouse"
        assert animal.total_number == 60
    
    def test_create_full(self):
        """Test creating with all fields."""
        animal = AnimalInfo(
            species="Mouse",
            scientific_name="Mus musculus",
            strain="C57BL/6J",
            sex="male",
            age_range="8-12 weeks",
            weight_range="20-25g",
            total_number=60,
            number_per_group=10,
            number_of_groups=6,
            source="commercial",
            vendor_name="Jackson Laboratory",
            genetic_modification="APP/PS1 transgenic",
            housing_requirements="Standard caging",
        )
        
        assert animal.strain == "C57BL/6J"
        assert animal.genetic_modification is not None
    
    def test_total_number_validation(self):
        """Test total number must be positive."""
        with pytest.raises(ValueError):
            AnimalInfo(
                species="Mouse",
                sex="both",
                total_number=0,
                source="vendor",
            )


class TestDrugInfo:
    """Tests for DrugInfo model."""
    
    def test_create_drug(self):
        """Test creating drug info."""
        drug = DrugInfo(
            drug_name="Ketamine",
            dose="100 mg/kg",
            route="IP",
            frequency="Once",
            duration="N/A",
            purpose="Anesthesia",
            dea_schedule="III",
        )
        
        assert drug.drug_name == "Ketamine"
        assert drug.dea_schedule == "III"


class TestProcedureInfo:
    """Tests for ProcedureInfo model."""
    
    def test_create_procedure(self):
        """Test creating procedure info."""
        proc = ProcedureInfo(
            name="Blood Collection",
            description="Submandibular blood collection",
            frequency="Weekly",
            anesthesia_required=False,
            analgesia_required=False,
        )
        
        assert proc.name == "Blood Collection"
        assert proc.anesthesia_required == False
    
    def test_surgical_procedure(self):
        """Test surgical procedure with all fields."""
        proc = ProcedureInfo(
            name="Craniotomy",
            description="Stereotaxic surgery for electrode implantation",
            duration="2 hours",
            anesthesia_required=True,
            anesthesia_protocol="Isoflurane 2-3%",
            analgesia_required=True,
            analgesia_protocol="Buprenorphine 0.1 mg/kg",
            recovery_expected=True,
            special_considerations="Maintain body temperature",
        )
        
        assert proc.anesthesia_required == True
        assert "Isoflurane" in proc.anesthesia_protocol


class TestHumaneEndpoint:
    """Tests for HumaneEndpoint model."""
    
    def test_create_endpoint(self):
        """Test creating humane endpoint."""
        endpoint = HumaneEndpoint(
            criterion="Weight loss",
            measurement="Daily weighing",
            threshold=">20% from baseline",
            action="Euthanasia",
        )
        
        assert endpoint.criterion == "Weight loss"
        assert "20%" in endpoint.threshold


class TestLiteratureSearch:
    """Tests for LiteratureSearch model."""
    
    def test_create_search(self):
        """Test creating literature search record."""
        search = LiteratureSearch(
            databases_searched=["PubMed", "AWIC"],
            search_date=date(2024, 1, 15),
            search_terms=["alternatives", "mouse model", "Alzheimer's"],
            years_covered="2014-2024",
            results_summary="No suitable alternatives identified",
        )
        
        assert len(search.databases_searched) == 2
        assert "PubMed" in search.databases_searched


class TestProtocolSection:
    """Tests for ProtocolSection model."""
    
    def test_create_section(self):
        """Test creating protocol section."""
        section = ProtocolSection(
            title="Custom Section",
            content="Section content here",
            is_complete=True,
        )
        
        assert section.title == "Custom Section"
        assert section.is_complete == True


class TestProtocol:
    """Tests for Protocol model."""
    
    @pytest.fixture
    def sample_protocol(self):
        """Create sample protocol for testing."""
        return Protocol(
            title="Effects of Novel Compound X on Alzheimer's Disease Model",
            principal_investigator=PersonnelInfo(
                name="Dr. Jane Smith",
                role="Principal Investigator",
                email="jsmith@university.edu",
            ),
            department="Department of Neuroscience",
            funding_sources=["NIH"],
            study_duration="12 months",
            lay_summary="This study investigates whether a new drug can slow memory loss in mice with Alzheimer's disease-like symptoms. We will give the drug to mice and test their memory using maze tests.",
            animals=[
                AnimalInfo(
                    species="Mouse",
                    strain="APP/PS1",
                    sex="both",
                    total_number=60,
                    source="Jackson Laboratory",
                )
            ],
            usda_category=USDACategory.D,
            total_animals=60,
            animal_number_justification="Power analysis (α=0.05, β=0.80, effect size=0.5) requires n=10 per group × 6 groups = 60 mice.",
            scientific_objectives="Evaluate efficacy of Compound X in reducing amyloid burden.",
            scientific_rationale="Animal models are necessary to assess CNS penetration and behavioral effects.",
            potential_benefits="May lead to new treatment for Alzheimer's disease.",
            replacement_statement="No in vitro models can assess cognitive function.",
            reduction_statement="Power analysis ensures minimum animals needed.",
            refinement_statement="Anesthesia and analgesia provided for all procedures.",
            experimental_design="Randomized controlled trial with 6 groups.",
            statistical_methods="Two-way ANOVA with post-hoc tests.",
            procedures=[
                ProcedureInfo(
                    name="Morris Water Maze",
                    description="Spatial learning assessment",
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
            monitoring_schedule="Daily observation, weekly detailed exam",
            euthanasia_method="CO2 followed by cervical dislocation",
        )
    
    def test_create_protocol(self, sample_protocol):
        """Test creating protocol."""
        assert sample_protocol.title.startswith("Effects")
        assert sample_protocol.total_animals == 60
    
    def test_protocol_has_id(self, sample_protocol):
        """Test protocol has unique ID."""
        assert sample_protocol.id is not None
        assert len(sample_protocol.id) > 10
    
    def test_protocol_default_status(self, sample_protocol):
        """Test protocol default status is draft."""
        assert sample_protocol.status == ProtocolStatus.DRAFT
    
    def test_calculate_completeness(self, sample_protocol):
        """Test completeness calculation."""
        completeness = sample_protocol.calculate_completeness()
        
        assert 0 <= completeness <= 1
        assert completeness > 0.5  # Sample protocol is mostly complete
    
    def test_get_missing_sections_complete(self, sample_protocol):
        """Test missing sections for complete protocol."""
        missing = sample_protocol.get_missing_sections()
        
        # Sample protocol should be mostly complete
        assert len(missing) == 0
    
    def test_to_summary_dict(self, sample_protocol):
        """Test summary dictionary generation."""
        summary = sample_protocol.to_summary_dict()
        
        assert "id" in summary
        assert "title" in summary
        assert "status" in summary
        assert "pi_name" in summary
        assert summary["pi_name"] == "Dr. Jane Smith"
    
    def test_title_min_length(self):
        """Test title minimum length validation."""
        with pytest.raises(ValueError):
            Protocol(
                title="Short",  # Too short
                principal_investigator=PersonnelInfo(
                    name="Dr. Test",
                    role="PI",
                ),
                department="Test",
                study_duration="12 months",
                lay_summary="x" * 100,
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
            )


class TestCreateEmptyProtocol:
    """Tests for create_empty_protocol helper."""
    
    def test_create_empty(self):
        """Test creating empty protocol."""
        protocol = create_empty_protocol(
            title="New Research Protocol for Testing",
            pi_name="Dr. John Doe",
            pi_email="jdoe@university.edu",
            department="Biology",
        )
        
        assert protocol.title == "New Research Protocol for Testing"
        assert protocol.principal_investigator.name == "Dr. John Doe"
    
    def test_empty_protocol_has_defaults(self):
        """Test empty protocol has default values."""
        protocol = create_empty_protocol(
            title="New Research Protocol for Testing",
            pi_name="Dr. John Doe",
            pi_email="jdoe@university.edu",
            department="Biology",
        )
        
        assert protocol.status == ProtocolStatus.DRAFT
        assert protocol.usda_category == USDACategory.C
    
    def test_empty_protocol_completeness(self):
        """Test empty protocol has some completeness."""
        protocol = create_empty_protocol(
            title="New Research Protocol for Testing",
            pi_name="Dr. John Doe",
            pi_email="jdoe@university.edu",
            department="Biology",
        )
        
        completeness = protocol.calculate_completeness()
        assert completeness > 0  # Has required fields filled with placeholders


class TestProtocolVersioning:
    """Tests for protocol versioning."""
    
    def test_default_version(self):
        """Test default version is 1."""
        protocol = create_empty_protocol(
            title="Test Protocol for Version Testing",
            pi_name="Dr. Test",
            pi_email="test@test.edu",
            department="Test",
        )
        
        assert protocol.version == 1


class TestAllThirteenSections:
    """Tests to verify all 13 sections are present."""
    
    @pytest.fixture
    def full_protocol(self):
        """Create protocol with all sections."""
        return Protocol(
            # Section 1: General Information
            title="Complete Protocol Testing All Sections",
            principal_investigator=PersonnelInfo(name="Dr. Test", role="PI", email="test@test.edu"),
            department="Test Department",
            funding_sources=["NIH R01"],
            study_duration="24 months",
            
            # Section 2: Lay Summary
            lay_summary="This is a lay summary that explains the research in simple terms that anyone can understand. The study will investigate important scientific questions using well-established laboratory methods.",
            
            # Section 3: Personnel
            personnel=[
                PersonnelInfo(name="Dr. Test", role="PI"),
                PersonnelInfo(name="Student", role="Graduate Student"),
            ],
            
            # Section 4: Species and Animal Numbers
            animals=[AnimalInfo(species="Mouse", sex="both", total_number=100, source="vendor")],
            usda_category=USDACategory.D,
            total_animals=100,
            animal_number_justification="Statistical justification provided.",
            
            # Section 5: Rationale
            scientific_objectives="Research objectives.",
            scientific_rationale="Why animals are necessary.",
            potential_benefits="Expected benefits.",
            
            # Section 6: Alternatives (3Rs)
            replacement_statement="Replacement rationale.",
            reduction_statement="Reduction rationale.",
            refinement_statement="Refinement rationale.",
            literature_search=LiteratureSearch(
                databases_searched=["PubMed"],
                search_date=date.today(),
                search_terms=["alternatives"],
                years_covered="2020-2024",
                results_summary="No alternatives found.",
            ),
            
            # Section 7: Experimental Design
            experimental_design="Design description.",
            statistical_methods="Statistical methods.",
            power_analysis="Power analysis results.",
            
            # Section 8: Procedures
            procedures=[ProcedureInfo(name="Test Procedure", description="Description")],
            procedure_timeline="Week 1-4: Acclimation",
            
            # Section 9: Anesthesia and Analgesia
            anesthesia_protocols=[DrugInfo(drug_name="Isoflurane", dose="2%", route="inhalation", purpose="anesthesia")],
            analgesia_protocols=[DrugInfo(drug_name="Buprenorphine", dose="0.1mg/kg", route="SC", purpose="analgesia")],
            monitoring_during_anesthesia="Respiratory rate monitoring.",
            
            # Section 10: Surgical Procedures
            surgical_procedures=[ProcedureInfo(name="Surgery", description="Surgical procedure", anesthesia_required=True)],
            aseptic_technique="Sterile technique description.",
            post_operative_care="Post-op care description.",
            
            # Section 11: Humane Endpoints
            humane_endpoints=[HumaneEndpoint(criterion="Weight", measurement="Daily", threshold="20%", action="Euthanasia")],
            monitoring_schedule="Daily monitoring.",
            
            # Section 12: Euthanasia
            euthanasia_method="CO2 followed by cervical dislocation",
            secondary_method="Cervical dislocation",
            avma_compliant=True,
            
            # Section 13: Hazardous Materials
            hazardous_materials=[],
            biohazard_level=None,
            radiation_use=False,
        )
    
    def test_section_1_general_info(self, full_protocol):
        """Test Section 1: General Information."""
        assert full_protocol.title
        assert full_protocol.principal_investigator
        assert full_protocol.department
        assert full_protocol.study_duration
    
    def test_section_2_lay_summary(self, full_protocol):
        """Test Section 2: Lay Summary."""
        assert full_protocol.lay_summary
        assert len(full_protocol.lay_summary) >= 100
    
    def test_section_3_personnel(self, full_protocol):
        """Test Section 3: Personnel."""
        assert len(full_protocol.personnel) >= 1
    
    def test_section_4_animals(self, full_protocol):
        """Test Section 4: Species and Animal Numbers."""
        assert full_protocol.animals
        assert full_protocol.total_animals > 0
        assert full_protocol.usda_category
    
    def test_section_5_rationale(self, full_protocol):
        """Test Section 5: Rationale."""
        assert full_protocol.scientific_objectives
        assert full_protocol.scientific_rationale
    
    def test_section_6_alternatives(self, full_protocol):
        """Test Section 6: Alternatives (3Rs)."""
        assert full_protocol.replacement_statement
        assert full_protocol.reduction_statement
        assert full_protocol.refinement_statement
    
    def test_section_7_design(self, full_protocol):
        """Test Section 7: Experimental Design."""
        assert full_protocol.experimental_design
        assert full_protocol.statistical_methods
    
    def test_section_8_procedures(self, full_protocol):
        """Test Section 8: Procedures."""
        assert full_protocol.procedures
    
    def test_section_9_anesthesia(self, full_protocol):
        """Test Section 9: Anesthesia and Analgesia."""
        assert full_protocol.anesthesia_protocols or full_protocol.analgesia_protocols
    
    def test_section_10_surgery(self, full_protocol):
        """Test Section 10: Surgical Procedures."""
        # May be empty if no surgery
        assert full_protocol.surgical_procedures is not None
    
    def test_section_11_endpoints(self, full_protocol):
        """Test Section 11: Humane Endpoints."""
        assert full_protocol.humane_endpoints
        assert full_protocol.monitoring_schedule
    
    def test_section_12_euthanasia(self, full_protocol):
        """Test Section 12: Euthanasia."""
        assert full_protocol.euthanasia_method
    
    def test_section_13_hazards(self, full_protocol):
        """Test Section 13: Hazardous Materials."""
        # Can be empty if no hazards
        assert full_protocol.hazardous_materials is not None
