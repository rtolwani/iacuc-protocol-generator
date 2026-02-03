"""
Unit tests for CrewAI setup with Claude.
"""

import pytest
from unittest.mock import patch, MagicMock

from crewai import Agent, Task, Crew

from src.agents.llm import get_llm, get_llm_for_task
from src.config import get_settings


class TestLLMConfiguration:
    """Tests for LLM configuration."""
    
    def test_get_llm_returns_anthropic(self):
        """Test that get_llm returns a ChatAnthropic instance."""
        llm = get_llm()
        
        # Should be a ChatAnthropic instance
        assert llm is not None
        assert "claude" in llm.model.lower()
    
    def test_get_llm_uses_settings(self):
        """Test that get_llm uses settings from config."""
        settings = get_settings()
        llm = get_llm()
        
        assert llm.temperature == settings.llm_temperature
        assert llm.max_tokens == settings.llm_max_tokens
    
    def test_get_llm_for_task_with_overrides(self):
        """Test that get_llm_for_task allows overrides."""
        llm = get_llm_for_task(temperature=0.8, max_tokens=2048)
        
        assert llm.temperature == 0.8
        assert llm.max_tokens == 2048
    
    def test_get_llm_for_task_without_overrides(self):
        """Test that get_llm_for_task uses defaults when no overrides."""
        settings = get_settings()
        llm = get_llm_for_task()
        
        assert llm.temperature == settings.llm_temperature
        assert llm.max_tokens == settings.llm_max_tokens


class TestCrewAIWithClaude:
    """Tests for CrewAI integration with Claude."""
    
    def test_create_simple_agent(self):
        """Test creating a simple CrewAI agent with Claude."""
        llm = get_llm()
        
        agent = Agent(
            role="Test Agent",
            goal="Complete a simple test task",
            backstory="You are a test agent created to verify CrewAI works with Claude.",
            llm=llm,
            verbose=False,
        )
        
        assert agent.role == "Test Agent"
        assert agent.llm is not None
    
    def test_create_task_for_agent(self):
        """Test creating a task for an agent."""
        llm = get_llm()
        
        agent = Agent(
            role="Greeter",
            goal="Greet users politely",
            backstory="You are a friendly greeter.",
            llm=llm,
            verbose=False,
        )
        
        task = Task(
            description="Say hello and introduce yourself in one sentence.",
            expected_output="A friendly greeting.",
            agent=agent,
        )
        
        assert task.description is not None
        assert task.agent == agent
    
    @pytest.mark.integration
    def test_simple_agent_task_execution(self):
        """
        Test that a simple agent can complete a task using Claude.
        
        This test makes an actual API call to Claude.
        Mark as integration test to allow skipping in fast test runs.
        """
        llm = get_llm()
        
        agent = Agent(
            role="Calculator",
            goal="Perform simple calculations accurately",
            backstory="You are a precise calculator that gives concise answers.",
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        
        task = Task(
            description="What is 2 + 2? Reply with just the number.",
            expected_output="A single number.",
            agent=agent,
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False,
        )
        
        result = crew.kickoff()
        
        # The result should contain "4"
        assert "4" in str(result)
    
    def test_create_crew_with_multiple_agents(self):
        """Test creating a crew with multiple agents."""
        llm = get_llm()
        
        agent1 = Agent(
            role="Researcher",
            goal="Research topics thoroughly",
            backstory="You are an expert researcher.",
            llm=llm,
            verbose=False,
        )
        
        agent2 = Agent(
            role="Writer",
            goal="Write clear content",
            backstory="You are a skilled writer.",
            llm=llm,
            verbose=False,
        )
        
        task1 = Task(
            description="Research a topic.",
            expected_output="Research findings.",
            agent=agent1,
        )
        
        task2 = Task(
            description="Write about the research.",
            expected_output="Written content.",
            agent=agent2,
        )
        
        crew = Crew(
            agents=[agent1, agent2],
            tasks=[task1, task2],
            verbose=False,
        )
        
        assert len(crew.agents) == 2
        assert len(crew.tasks) == 2
