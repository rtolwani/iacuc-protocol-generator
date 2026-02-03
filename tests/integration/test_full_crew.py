"""
Integration tests for the complete 8-agent crew.

Note: Tests marked with @pytest.mark.integration require API keys
and may take several minutes to complete.
"""

import pytest

from src.agents.crew import (
    create_all_agents,
    create_protocol_tasks,
    create_protocol_crew,
    quick_crew_check,
    ProtocolInput,
    CrewResult,
)


# Sample input for testing
SAMPLE_BEHAVIORAL_INPUT = ProtocolInput(
    title="Effects of Environmental Enrichment on Anxiety-Related Behavior",
    pi_name="Dr. Jane Smith",
    species="mouse",
    strain="C57BL/6J",
    total_animals=60,
    research_description=(
        "This study investigates how environmental enrichment affects "
        "anxiety-related behaviors in mice. Animals will be housed in "
        "standard or enriched environments for 4 weeks, then tested in "
        "the elevated plus maze and open field test."
    ),
    procedures=(
        "Behavioral testing including elevated plus maze (10 min/session) "
        "and open field test (30 min/session). Animals will be habituated "
        "to handling for 1 week before testing. Euthanasia by CO2 "
        "inhalation followed by cervical dislocation for tissue collection."
    ),
    study_duration="6 weeks",
    primary_endpoint="Time spent in open arms of elevated plus maze",
)

SAMPLE_SURGICAL_INPUT = ProtocolInput(
    title="Cranial Window Implantation for In Vivo Imaging",
    pi_name="Dr. John Doe",
    species="mouse",
    strain="Thy1-GFP",
    total_animals=30,
    research_description=(
        "This study uses in vivo two-photon microscopy to image "
        "neuronal activity through a chronic cranial window. The "
        "window allows repeated imaging sessions over several weeks."
    ),
    procedures=(
        "Survival surgery for cranial window implantation under "
        "isoflurane anesthesia. Post-operative analgesia with "
        "buprenorphine. Weekly imaging sessions under brief anesthesia. "
        "Euthanasia by pentobarbital overdose at study end."
    ),
    study_duration="8 weeks",
    primary_endpoint="Neuronal activity patterns",
)


class TestCreateAllAgents:
    """Tests for agent creation."""
    
    def test_creates_all_eight_agents(self):
        """Test that all 8 agents are created."""
        agents = create_all_agents()
        
        assert len(agents) == 8
    
    def test_agent_names(self):
        """Test that expected agents are present."""
        agents = create_all_agents()
        
        expected_agents = [
            "intake_specialist",
            "regulatory_scout",
            "lay_summary_writer",
            "alternatives_researcher",
            "statistical_consultant",
            "veterinary_reviewer",
            "procedure_writer",
            "protocol_assembler",
        ]
        
        for name in expected_agents:
            assert name in agents
    
    def test_agents_have_tools(self):
        """Test that agents have appropriate tools."""
        agents = create_all_agents()
        
        # At least some agents should have tools
        agents_with_tools = [a for a in agents.values() if a.tools]
        assert len(agents_with_tools) > 0


class TestCreateProtocolTasks:
    """Tests for task creation."""
    
    def test_creates_eight_tasks(self):
        """Test that 8 tasks are created."""
        agents = create_all_agents()
        tasks = create_protocol_tasks(agents, SAMPLE_BEHAVIORAL_INPUT)
        
        assert len(tasks) == 8
    
    def test_tasks_have_agents(self):
        """Test that each task has an agent assigned."""
        agents = create_all_agents()
        tasks = create_protocol_tasks(agents, SAMPLE_BEHAVIORAL_INPUT)
        
        for task in tasks:
            assert task.agent is not None
    
    def test_tasks_have_descriptions(self):
        """Test that tasks have descriptions."""
        agents = create_all_agents()
        tasks = create_protocol_tasks(agents, SAMPLE_BEHAVIORAL_INPUT)
        
        for task in tasks:
            assert task.description
            assert len(task.description) > 50
    
    def test_tasks_include_input_data(self):
        """Test that tasks include input data."""
        agents = create_all_agents()
        tasks = create_protocol_tasks(agents, SAMPLE_BEHAVIORAL_INPUT)
        
        # First task should include the title
        assert "Environmental Enrichment" in tasks[0].description
    
    def test_later_tasks_have_context(self):
        """Test that later tasks have context from earlier tasks."""
        agents = create_all_agents()
        tasks = create_protocol_tasks(agents, SAMPLE_BEHAVIORAL_INPUT)
        
        # Protocol assembler (last task) should have context
        assembly_task = tasks[-1]
        assert assembly_task.context is not None
        assert len(assembly_task.context) > 0


class TestCreateProtocolCrew:
    """Tests for crew creation."""
    
    def test_creates_crew(self):
        """Test that crew is created."""
        crew = create_protocol_crew(SAMPLE_BEHAVIORAL_INPUT)
        
        assert crew is not None
    
    def test_crew_has_all_agents(self):
        """Test that crew has all agents."""
        crew = create_protocol_crew(SAMPLE_BEHAVIORAL_INPUT)
        
        assert len(crew.agents) == 8
    
    def test_crew_has_all_tasks(self):
        """Test that crew has all tasks."""
        crew = create_protocol_crew(SAMPLE_BEHAVIORAL_INPUT)
        
        assert len(crew.tasks) == 8


class TestQuickCrewCheck:
    """Tests for quick validation."""
    
    def test_valid_input_passes(self):
        """Test that valid input passes validation."""
        result = quick_crew_check(SAMPLE_BEHAVIORAL_INPUT)
        
        assert result["is_valid"]
        assert len(result["validation_errors"]) == 0
    
    def test_invalid_input_fails(self):
        """Test that invalid input fails validation."""
        invalid_input = ProtocolInput(
            title="",
            pi_name="Test",
            species="",
            total_animals=0,
            research_description="",
            procedures="",
        )
        
        result = quick_crew_check(invalid_input)
        
        assert not result["is_valid"]
        assert len(result["validation_errors"]) > 0
    
    def test_returns_task_sequence(self):
        """Test that task sequence is returned."""
        result = quick_crew_check(SAMPLE_BEHAVIORAL_INPUT)
        
        assert "task_sequence" in result
        assert len(result["task_sequence"]) == 8
    
    def test_returns_agent_list(self):
        """Test that agent list is returned."""
        result = quick_crew_check(SAMPLE_BEHAVIORAL_INPUT)
        
        assert "agents" in result
        assert len(result["agents"]) == 8
    
    def test_returns_input_summary(self):
        """Test that input summary is returned."""
        result = quick_crew_check(SAMPLE_BEHAVIORAL_INPUT)
        
        assert "input_summary" in result
        assert result["input_summary"]["species"] == "mouse"
        assert result["input_summary"]["total_animals"] == 60


class TestProtocolInputModel:
    """Tests for ProtocolInput model."""
    
    def test_create_basic_input(self):
        """Test creating basic input."""
        input_data = ProtocolInput(
            title="Test Protocol",
            pi_name="Dr. Test",
            species="mouse",
            total_animals=20,
            research_description="Test description",
            procedures="Test procedures",
        )
        
        assert input_data.title == "Test Protocol"
        assert input_data.species == "mouse"
    
    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        input_data = ProtocolInput(
            title="Test",
            pi_name="Test",
            species="mouse",
            total_animals=10,
            research_description="Test",
            procedures="Test",
        )
        
        assert input_data.strain is None
        assert input_data.study_duration is None
        assert input_data.primary_endpoint is None


class TestCrewResultModel:
    """Tests for CrewResult model."""
    
    def test_create_success_result(self):
        """Test creating success result."""
        result = CrewResult(
            success=True,
            protocol_sections={"title": "Test"},
            agent_outputs={"intake": "Output"},
            errors=[],
        )
        
        assert result.success
        assert len(result.errors) == 0
    
    def test_create_failure_result(self):
        """Test creating failure result."""
        result = CrewResult(
            success=False,
            protocol_sections={},
            agent_outputs={},
            errors=["Something went wrong"],
        )
        
        assert not result.success
        assert len(result.errors) == 1


class TestDifferentInputTypes:
    """Tests with different input types."""
    
    def test_behavioral_study_input(self):
        """Test with behavioral study input."""
        result = quick_crew_check(SAMPLE_BEHAVIORAL_INPUT)
        
        assert result["is_valid"]
    
    def test_surgical_study_input(self):
        """Test with surgical study input."""
        result = quick_crew_check(SAMPLE_SURGICAL_INPUT)
        
        assert result["is_valid"]
    
    def test_tumor_model_input(self):
        """Test with tumor model input."""
        tumor_input = ProtocolInput(
            title="Efficacy of Novel Anti-Cancer Agent",
            pi_name="Dr. Cancer Researcher",
            species="mouse",
            strain="BALB/c nude",
            total_animals=80,
            research_description=(
                "Testing the efficacy of a novel anti-cancer compound "
                "in a subcutaneous tumor xenograft model."
            ),
            procedures=(
                "Subcutaneous implantation of tumor cells. "
                "Daily compound administration by oral gavage. "
                "Tumor measurements twice weekly. "
                "Euthanasia when tumor reaches 1500mm3."
            ),
            study_duration="6 weeks",
            primary_endpoint="Tumor volume",
        )
        
        result = quick_crew_check(tumor_input)
        
        assert result["is_valid"]


@pytest.mark.integration
class TestFullCrewExecution:
    """
    Integration tests that run the full crew.
    
    These tests require API keys and may take several minutes.
    Run with: pytest -m integration --timeout=300
    """
    
    @pytest.mark.timeout(300)
    def test_generate_behavioral_protocol(self):
        """Test generating a behavioral study protocol."""
        from src.agents.crew import generate_protocol
        
        result = generate_protocol(SAMPLE_BEHAVIORAL_INPUT, verbose=False)
        
        # Should succeed
        assert result.success
        
        # Should have protocol sections
        assert "lay_summary" in result.protocol_sections
        assert "procedures" in result.protocol_sections
        
        # Should have agent outputs
        assert len(result.agent_outputs) > 0
    
    @pytest.mark.timeout(300)
    def test_generate_surgical_protocol(self):
        """Test generating a surgical study protocol."""
        from src.agents.crew import generate_protocol
        
        result = generate_protocol(SAMPLE_SURGICAL_INPUT, verbose=False)
        
        # Should succeed
        assert result.success
        
        # Should mention anesthesia given it's a surgical protocol
        combined_output = " ".join(str(v) for v in result.agent_outputs.values())
        assert "anesthesia" in combined_output.lower() or "isoflurane" in combined_output.lower()
