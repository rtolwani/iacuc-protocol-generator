"""
Unit tests for Procedure Writer Agent.
"""

import pytest

from src.agents.procedure_writer import (
    create_procedure_writer_agent,
    create_procedure_writing_task,
    quick_procedure_generation,
    generate_drug_table,
    generate_monitoring_schedule,
    generate_procedure_steps,
    get_euthanasia_methods,
    DrugAdministrationEntry,
    MonitoringScheduleEntry,
    ProcedureStep,
    EuthanasiaMethod,
    AVMA_EUTHANASIA_METHODS,
)


class TestGenerateDrugTable:
    """Tests for drug table generation."""
    
    def test_surgery_generates_drug_table(self):
        """Test that surgical procedures generate drug table."""
        table = generate_drug_table("mouse", "surgery")
        
        assert len(table) > 0
        # Should have anesthesia and analgesia
        drug_names = [d.drug_name.lower() for d in table]
        assert any("ketamine" in name for name in drug_names)
    
    def test_drug_entries_have_required_fields(self):
        """Test that drug entries have all required fields."""
        table = generate_drug_table("mouse", "surgery")
        
        for entry in table:
            assert entry.drug_name is not None
            assert entry.dose is not None
            assert entry.route is not None
            assert entry.frequency is not None
            assert entry.timing is not None
            assert entry.purpose is not None
    
    def test_species_specific_dosing(self):
        """Test that dosing is species-specific."""
        mouse_table = generate_drug_table("mouse", "surgery")
        rat_table = generate_drug_table("rat", "surgery")
        
        # Both should have entries but may have different doses
        assert len(mouse_table) > 0
        assert len(rat_table) > 0


class TestGenerateMonitoringSchedule:
    """Tests for monitoring schedule generation."""
    
    def test_surgery_monitoring(self):
        """Test monitoring schedule for surgery."""
        schedule = generate_monitoring_schedule("surgery")
        
        assert len(schedule) > 0
        # Should have intra-operative and post-operative monitoring
        time_points = " ".join([s.time_point.lower() for s in schedule])
        assert "anesthesia" in time_points or "recovery" in time_points
    
    def test_tumor_monitoring(self):
        """Test monitoring schedule for tumor studies."""
        schedule = generate_monitoring_schedule("tumor implantation")
        
        assert len(schedule) > 0
        # Should include tumor measurements
        all_params = []
        for s in schedule:
            all_params.extend([p.lower() for p in s.parameters])
        
        assert any("tumor" in p for p in all_params)
    
    def test_monitoring_entries_have_required_fields(self):
        """Test that monitoring entries have all required fields."""
        schedule = generate_monitoring_schedule("surgery")
        
        for entry in schedule:
            assert entry.time_point is not None
            assert entry.parameters is not None
            assert len(entry.parameters) > 0
            assert entry.criteria is not None
            assert entry.action_if_abnormal is not None


class TestGenerateProcedureSteps:
    """Tests for procedure step generation."""
    
    def test_surgery_steps(self):
        """Test procedure steps for surgery."""
        steps = generate_procedure_steps("surgery", "mouse")
        
        assert len(steps) > 0
        # Should have numbered steps
        assert steps[0].step_number == 1
    
    def test_steps_are_sequential(self):
        """Test that steps are sequentially numbered."""
        steps = generate_procedure_steps("surgery", "mouse")
        
        for i, step in enumerate(steps, start=1):
            assert step.step_number == i
    
    def test_steps_have_descriptions(self):
        """Test that all steps have descriptions."""
        steps = generate_procedure_steps("surgery", "mouse")
        
        for step in steps:
            assert step.description is not None
            assert len(step.description) > 10


class TestGetEuthanasiaMethods:
    """Tests for euthanasia method retrieval."""
    
    def test_mouse_euthanasia(self):
        """Test getting euthanasia methods for mouse."""
        methods = get_euthanasia_methods("mouse")
        
        assert len(methods) > 0
    
    def test_rat_euthanasia(self):
        """Test getting euthanasia methods for rat."""
        methods = get_euthanasia_methods("rat")
        
        assert len(methods) > 0
    
    def test_rabbit_euthanasia(self):
        """Test getting euthanasia methods for rabbit."""
        methods = get_euthanasia_methods("rabbit")
        
        assert len(methods) > 0
    
    def test_unknown_species_returns_default(self):
        """Test that unknown species returns default method."""
        methods = get_euthanasia_methods("elephant")
        
        assert len(methods) > 0
        assert "pentobarbital" in methods[0].primary_method.lower()
    
    def test_methods_have_secondary_confirmation(self):
        """Test that all methods have secondary confirmation."""
        methods = get_euthanasia_methods("mouse")
        
        for method in methods:
            assert method.secondary_method is not None
            assert len(method.secondary_method) > 5
    
    def test_methods_have_classification(self):
        """Test that methods have AVMA classification."""
        methods = get_euthanasia_methods("mouse")
        
        for method in methods:
            assert method.classification in ["Acceptable", "Conditionally Acceptable"]


class TestQuickProcedureGeneration:
    """Tests for quick procedure generation."""
    
    def test_returns_all_sections(self):
        """Test that all sections are returned."""
        result = quick_procedure_generation("mouse", "surgery")
        
        assert "species" in result
        assert "procedure_steps" in result
        assert "drug_table" in result
        assert "monitoring_schedule" in result
        assert "euthanasia_methods" in result
    
    def test_surgery_generates_complete_documentation(self):
        """Test that surgery generates complete documentation."""
        result = quick_procedure_generation("mouse", "survival surgery")
        
        assert len(result["procedure_steps"]) > 0
        assert len(result["drug_table"]) > 0
        assert len(result["monitoring_schedule"]) > 0
        assert len(result["euthanasia_methods"]) > 0


class TestProcedureWriterAgent:
    """Tests for agent creation."""
    
    def test_create_agent(self):
        """Test that agent is created with correct configuration."""
        agent = create_procedure_writer_agent()
        
        assert agent.role == "Procedure Writer"
    
    def test_agent_has_required_tools(self):
        """Test that agent has required tools."""
        agent = create_procedure_writer_agent()
        
        tool_names = [t.name for t in agent.tools]
        
        assert "formulary_lookup" in tool_names
        assert "regulatory_search" in tool_names
        assert "euthanasia_methods" in tool_names
    
    def test_agent_backstory_mentions_experience(self):
        """Test that agent backstory mentions relevant experience."""
        agent = create_procedure_writer_agent()
        
        backstory_lower = agent.backstory.lower()
        assert "procedure" in backstory_lower or "protocol" in backstory_lower


class TestProcedureWritingTask:
    """Tests for task creation."""
    
    def test_create_task(self):
        """Test that task is created with correct content."""
        agent = create_procedure_writer_agent()
        
        task = create_procedure_writing_task(
            agent=agent,
            species="mouse",
            procedure_description="Survival craniotomy for electrode implantation",
        )
        
        assert task.agent == agent
        assert "mouse" in task.description
        assert "craniotomy" in task.description
    
    def test_task_includes_key_sections(self):
        """Test that task includes key sections."""
        agent = create_procedure_writer_agent()
        
        task = create_procedure_writing_task(
            agent=agent,
            species="rat",
            procedure_description="Surgery",
        )
        
        description_lower = task.description.lower()
        
        assert "step" in description_lower
        assert "drug" in description_lower
        assert "monitoring" in description_lower
        assert "euthanasia" in description_lower
    
    def test_task_includes_study_duration(self):
        """Test that study duration is included when provided."""
        agent = create_procedure_writer_agent()
        
        task = create_procedure_writing_task(
            agent=agent,
            species="mouse",
            procedure_description="Behavioral testing",
            study_duration="4 weeks",
        )
        
        assert "4 weeks" in task.description


class TestAVMAEuthanasiaConstants:
    """Tests for AVMA euthanasia constants."""
    
    def test_common_species_defined(self):
        """Test that common species are defined."""
        assert "mouse" in AVMA_EUTHANASIA_METHODS
        assert "rat" in AVMA_EUTHANASIA_METHODS
        assert "rabbit" in AVMA_EUTHANASIA_METHODS
    
    def test_methods_have_acceptable_category(self):
        """Test that all species have acceptable methods."""
        for species, methods in AVMA_EUTHANASIA_METHODS.items():
            assert "acceptable" in methods
            assert len(methods["acceptable"]) > 0
    
    def test_methods_are_euthanasia_method_objects(self):
        """Test that methods are EuthanasiaMethod objects."""
        for species, methods in AVMA_EUTHANASIA_METHODS.items():
            for method_list in methods.values():
                for method in method_list:
                    assert isinstance(method, EuthanasiaMethod)


class TestModels:
    """Tests for Pydantic models."""
    
    def test_drug_administration_entry(self):
        """Test DrugAdministrationEntry model."""
        entry = DrugAdministrationEntry(
            drug_name="Ketamine",
            dose="100 mg/kg",
            route="IP",
            frequency="Once",
            timing="Pre-operative",
            purpose="Anesthesia",
        )
        
        assert entry.drug_name == "Ketamine"
        assert entry.dose == "100 mg/kg"
    
    def test_monitoring_schedule_entry(self):
        """Test MonitoringScheduleEntry model."""
        entry = MonitoringScheduleEntry(
            time_point="Daily",
            parameters=["Body weight", "Food intake"],
            criteria="Normal values",
            action_if_abnormal="Consult veterinarian",
        )
        
        assert entry.time_point == "Daily"
        assert len(entry.parameters) == 2
    
    def test_procedure_step(self):
        """Test ProcedureStep model."""
        step = ProcedureStep(
            step_number=1,
            description="Weigh animal",
            duration="1 minute",
        )
        
        assert step.step_number == 1
        assert step.description == "Weigh animal"
    
    def test_euthanasia_method(self):
        """Test EuthanasiaMethod model."""
        method = EuthanasiaMethod(
            primary_method="CO2 inhalation",
            secondary_method="Cervical dislocation",
            species="mouse",
            classification="Acceptable",
        )
        
        assert method.primary_method == "CO2 inhalation"
        assert method.species == "mouse"
