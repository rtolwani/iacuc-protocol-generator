"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and provides
fixtures available to all test files.
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"


@pytest.fixture
def settings():
    """Provide test settings."""
    from src.config import Settings

    return Settings(
        environment="testing",
        debug=True,
        database_url="sqlite:///./data/test_iacuc.db",
        chroma_persist_dir="./data/test_chroma",
    )


@pytest.fixture
def sample_research_description():
    """Sample research description for testing."""
    return """
    We will conduct a Morris water maze study in C57BL/6J mice
    to assess spatial learning and memory following traumatic brain injury.
    40 mice (20 male, 20 female) aged 8-12 weeks will be used.
    Mice will undergo a controlled cortical impact injury under isoflurane
    anesthesia with buprenorphine analgesia. Daily behavioral testing will
    occur for 5 days starting 7 days post-injury. Animals will be euthanized
    by CO2 asphyxiation followed by cervical dislocation at study end.
    """


@pytest.fixture
def sample_technical_text():
    """Sample technical text for lay summary testing."""
    return """
    The pharmacokinetic profile of the novel therapeutic agent will be
    characterized through serial blood sampling and subsequent liquid
    chromatography-mass spectrometry analysis. Bioavailability will be
    assessed by comparing area under the curve (AUC) values following
    intravenous and oral administration. The compound's distribution
    to target tissues will be evaluated using autoradiography with
    tritium-labeled compound.
    """


@pytest.fixture
def sample_simple_text():
    """Sample simple text that should pass readability check."""
    return """
    We want to test a new medicine that might help people with cancer.
    To do this safely, we first need to test it in mice. We will give
    the medicine to the mice and watch to see if it helps shrink tumors.
    We will also make sure the medicine does not hurt the mice. The mice
    will not feel pain because we will give them medicine to prevent it.
    """
