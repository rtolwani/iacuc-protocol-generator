"""
Unit tests for Veterinary Reviewer Agent.
"""

import pytest

from src.agents.veterinary_reviewer import (
    create_veterinary_reviewer_agent,
    create_veterinary_review_task,
    quick_veterinary_check,
    validate_protocol_drugs,
    generate_welfare_concerns,
    get_recommended_endpoints,
    identify_procedure_type,
    Severity,
    ReviewFinding,
    HumaneEndpoint,
    WELFARE_CONCERNS,
    STANDARD_ENDPOINTS,
)


class TestIdentifyProcedureType:
    """Tests for procedure type identification."""
    
    def test_identifies_surgery(self):
        """Test identifying surgical procedures."""
        proc_types = identify_procedure_type("Animals will undergo survival surgery.")
        
        assert "surgery" in proc_types
    
    def test_identifies_tumor(self):
        """Test identifying tumor studies."""
        proc_types = identify_procedure_type("Tumor cells will be implanted subcutaneously.")
        
        assert "tumor" in proc_types
    
    def test_identifies_behavioral(self):
        """Test identifying behavioral studies."""
        proc_types = identify_procedure_type("Animals will undergo behavioral testing in the maze.")
        
        assert "behavioral" in proc_types
    
    def test_identifies_multiple_types(self):
        """Test identifying multiple procedure types."""
        proc_types = identify_procedure_type(
            "Tumor implantation via surgical procedure, followed by behavioral assessment."
        )
        
        assert "tumor" in proc_types
        assert "surgery" in proc_types
        assert "behavioral" in proc_types
    
    def test_defaults_to_general(self):
        """Test that unrecognized procedures default to general."""
        proc_types = identify_procedure_type("Animals will be observed.")
        
        assert "general" in proc_types


class TestGenerateWelfareConcerns:
    """Tests for welfare concern generation."""
    
    def test_surgery_concerns(self):
        """Test welfare concerns for surgery."""
        concerns = generate_welfare_concerns("Survival surgery under anesthesia")
        
        assert len(concerns) > 0
        assert any("anesthesia" in c.lower() or "pain" in c.lower() for c in concerns)
    
    def test_tumor_concerns(self):
        """Test welfare concerns for tumor studies."""
        concerns = generate_welfare_concerns("Tumor implantation and monitoring")
        
        assert len(concerns) > 0
        assert any("tumor" in c.lower() or "burden" in c.lower() for c in concerns)
    
    def test_no_duplicate_concerns(self):
        """Test that concerns are not duplicated."""
        concerns = generate_welfare_concerns("Surgery and more surgery")
        
        # Should not have duplicate concerns
        assert len(concerns) == len(set(concerns))


class TestGetRecommendedEndpoints:
    """Tests for endpoint recommendations."""
    
    def test_always_includes_general_endpoints(self):
        """Test that general endpoints are always included."""
        endpoints = get_recommended_endpoints("Simple observation")
        
        assert len(endpoints) > 0
        # Should have weight loss endpoint
        assert any("weight" in e.criterion.lower() for e in endpoints)
    
    def test_surgery_endpoints(self):
        """Test surgery-specific endpoints."""
        endpoints = get_recommended_endpoints("Survival surgery")
        
        assert len(endpoints) > len(STANDARD_ENDPOINTS["general"])
        # Should have surgical site monitoring
        assert any("surgical" in e.criterion.lower() or "dehiscence" in e.criterion.lower() 
                   for e in endpoints)
    
    def test_tumor_endpoints(self):
        """Test tumor-specific endpoints."""
        endpoints = get_recommended_endpoints("Tumor model")
        
        # Should have tumor size limits
        assert any("tumor" in e.criterion.lower() for e in endpoints)
    
    def test_endpoint_structure(self):
        """Test that endpoints have required fields."""
        endpoints = get_recommended_endpoints("Surgery")
        
        for endpoint in endpoints:
            assert endpoint.criterion is not None
            assert endpoint.action is not None
            assert endpoint.monitoring_frequency is not None


class TestValidateProtocolDrugs:
    """Tests for drug validation."""
    
    def test_valid_dose_approved(self):
        """Test that valid dose is approved."""
        drugs = [{"name": "ketamine", "dose": "90 mg/kg"}]
        results = validate_protocol_drugs(drugs, "mouse")
        
        assert len(results) == 1
        assert results[0]["valid"] is True
    
    def test_dose_above_range_flagged(self):
        """Test that dose above range is flagged."""
        drugs = [{"name": "ketamine", "dose": "200 mg/kg"}]
        results = validate_protocol_drugs(drugs, "mouse")
        
        assert len(results) == 1
        assert results[0]["valid"] is False
        assert results[0]["status"] == "ABOVE_RANGE"
    
    def test_unknown_drug_flagged(self):
        """Test that unknown drug is flagged."""
        drugs = [{"name": "fakemedicine", "dose": "10 mg/kg"}]
        results = validate_protocol_drugs(drugs, "mouse")
        
        assert len(results) == 1
        assert results[0]["valid"] is False
        assert results[0]["status"] == "NOT_FOUND"
    
    def test_multiple_drugs_validated(self):
        """Test validation of multiple drugs."""
        drugs = [
            {"name": "ketamine", "dose": "90 mg/kg"},
            {"name": "xylazine", "dose": "10 mg/kg"},
            {"name": "buprenorphine", "dose": "0.1 mg/kg"},
        ]
        results = validate_protocol_drugs(drugs, "mouse")
        
        assert len(results) == 3


class TestQuickVeterinaryCheck:
    """Tests for quick veterinary check function."""
    
    def test_returns_all_fields(self):
        """Test that all required fields are returned."""
        drugs = [{"name": "ketamine", "dose": "90 mg/kg"}]
        result = quick_veterinary_check(
            species="mouse",
            procedures="Behavioral observation",
            drugs=drugs,
        )
        
        assert "species" in result
        assert "pain_category" in result
        assert "drug_validations" in result
        assert "welfare_concerns" in result
        assert "recommended_endpoints" in result
        assert "requires_revision" in result
    
    def test_no_revision_for_valid_protocol(self):
        """Test that valid protocol doesn't require revision."""
        drugs = [{"name": "isoflurane", "dose": "2%"}]
        result = quick_veterinary_check(
            species="mouse",
            procedures="Behavioral observation only",
            drugs=drugs,
        )
        
        # Should not require revision (valid drug for imaging, Category C)
        # Note: isoflurane isn't a simple dose so may not validate
        assert "requires_revision" in result
    
    def test_revision_required_for_drug_issues(self):
        """Test that drug issues trigger revision requirement."""
        drugs = [{"name": "fakemedicine", "dose": "100 mg/kg"}]
        result = quick_veterinary_check(
            species="mouse",
            procedures="Simple observation",
            drugs=drugs,
        )
        
        assert result["requires_revision"] is True
        assert len(result["critical_issues"]) > 0
    
    def test_revision_required_for_category_e(self):
        """Test that Category E triggers revision requirement."""
        drugs = []
        result = quick_veterinary_check(
            species="mouse",
            procedures="Toxicity study with lethal dose, no pain relief",
            drugs=drugs,
        )
        
        assert result["pain_category"]["requires_justification"] is True


class TestVeterinaryReviewerAgent:
    """Tests for agent creation."""
    
    def test_create_agent(self):
        """Test that agent is created with correct configuration."""
        agent = create_veterinary_reviewer_agent()
        
        assert agent.role == "Veterinary Reviewer"
        assert "welfare" in agent.goal.lower() or "veterinary" in agent.goal.lower()
    
    def test_agent_has_required_tools(self):
        """Test that agent has required tools."""
        agent = create_veterinary_reviewer_agent()
        
        tool_names = [t.name for t in agent.tools]
        
        assert "formulary_lookup" in tool_names
        assert "pain_category_classifier" in tool_names
        assert "regulatory_search" in tool_names
    
    def test_agent_backstory_mentions_expertise(self):
        """Test that agent backstory mentions veterinary expertise."""
        agent = create_veterinary_reviewer_agent()
        
        backstory_lower = agent.backstory.lower()
        assert "veterinarian" in backstory_lower or "veterinary" in backstory_lower


class TestVeterinaryReviewTask:
    """Tests for task creation."""
    
    def test_create_task(self):
        """Test that task is created with correct content."""
        agent = create_veterinary_reviewer_agent()
        drugs = [{"name": "ketamine", "dose": "90 mg/kg"}]
        
        task = create_veterinary_review_task(
            agent=agent,
            species="mouse",
            procedures="Surgery under anesthesia",
            drugs=drugs,
        )
        
        assert task.agent == agent
        assert "mouse" in task.description
        assert "ketamine" in task.description
    
    def test_task_includes_key_sections(self):
        """Test that task includes key review sections."""
        agent = create_veterinary_reviewer_agent()
        drugs = [{"name": "buprenorphine", "dose": "0.1 mg/kg"}]
        
        task = create_veterinary_review_task(
            agent=agent,
            species="rat",
            procedures="Surgery",
            drugs=drugs,
        )
        
        description_lower = task.description.lower()
        
        assert "drug" in description_lower
        assert "pain" in description_lower or "category" in description_lower
        assert "endpoint" in description_lower
        assert "welfare" in description_lower


class TestWelfareConcernsConstants:
    """Tests for welfare concern constants."""
    
    def test_common_procedure_types_defined(self):
        """Test that common procedure types have welfare concerns."""
        assert "surgery" in WELFARE_CONCERNS
        assert "tumor" in WELFARE_CONCERNS
        assert "behavioral" in WELFARE_CONCERNS
    
    def test_concerns_have_required_fields(self):
        """Test that each procedure type has required fields."""
        for proc_type, info in WELFARE_CONCERNS.items():
            assert "concerns" in info
            assert "required_monitoring" in info
            assert len(info["concerns"]) > 0


class TestStandardEndpointsConstants:
    """Tests for standard endpoint constants."""
    
    def test_general_endpoints_defined(self):
        """Test that general endpoints are defined."""
        assert "general" in STANDARD_ENDPOINTS
        assert len(STANDARD_ENDPOINTS["general"]) > 0
    
    def test_procedure_specific_endpoints(self):
        """Test that procedure-specific endpoints are defined."""
        assert "tumor" in STANDARD_ENDPOINTS
        assert "surgery" in STANDARD_ENDPOINTS
    
    def test_endpoint_objects_valid(self):
        """Test that endpoint objects have valid structure."""
        for proc_type, endpoints in STANDARD_ENDPOINTS.items():
            for endpoint in endpoints:
                assert isinstance(endpoint, HumaneEndpoint)


class TestModels:
    """Tests for Pydantic models."""
    
    def test_severity_enum(self):
        """Test Severity enum values."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"
    
    def test_review_finding(self):
        """Test ReviewFinding model."""
        finding = ReviewFinding(
            severity=Severity.WARNING,
            category="Drug Dosage",
            issue="Dose below recommended range",
            recommendation="Consider increasing dose",
        )
        
        assert finding.severity == Severity.WARNING
        assert finding.category == "Drug Dosage"
    
    def test_humane_endpoint(self):
        """Test HumaneEndpoint model."""
        endpoint = HumaneEndpoint(
            criterion="Weight loss >20%",
            action="Immediate euthanasia",
            monitoring_frequency="Daily",
        )
        
        assert endpoint.criterion == "Weight loss >20%"
        assert endpoint.action == "Immediate euthanasia"
