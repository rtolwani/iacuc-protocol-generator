"""
Unit tests for Literature Search Documentation Tool.
"""

import pytest
from datetime import date

from src.tools.literature_search_tool import (
    LiteratureSearchTool,
    generate_search_keywords,
    generate_search_string,
    create_search_documentation,
    format_search_documentation,
    LiteratureSearchRecord,
    AlternativesSearchDocumentation,
    REQUIRED_DATABASES,
    ALTERNATIVES_DATABASES,
)


class TestGenerateSearchKeywords:
    """Tests for keyword generation."""
    
    def test_generates_replacement_keywords(self):
        """Test that replacement keywords are generated."""
        keywords = generate_search_keywords("mouse", "behavioral testing")
        
        assert "replacement" in keywords
        assert len(keywords["replacement"]) > 0
        assert "in vitro" in keywords["replacement"]
    
    def test_generates_reduction_keywords(self):
        """Test that reduction keywords are generated."""
        keywords = generate_search_keywords("rat", "surgery")
        
        assert "reduction" in keywords
        assert len(keywords["reduction"]) > 0
        assert "sample size" in keywords["reduction"]
    
    def test_generates_refinement_keywords(self):
        """Test that refinement keywords are generated."""
        keywords = generate_search_keywords("rabbit", "drug administration")
        
        assert "refinement" in keywords
        assert len(keywords["refinement"]) > 0
        assert "humane endpoint" in keywords["refinement"]
    
    def test_includes_animal_model_in_keywords(self):
        """Test that animal model is included in keywords."""
        keywords = generate_search_keywords("guinea pig", "testing")
        
        assert any("guinea pig" in kw for kw in keywords["replacement"])
    
    def test_toxicity_adds_specific_keywords(self):
        """Test that toxicity procedures add specific keywords."""
        keywords = generate_search_keywords("mouse", "toxicity study")
        
        # Should have toxicity-specific alternatives
        assert any("toxicity" in kw.lower() or "organ-on-chip" in kw.lower() 
                   for kw in keywords["replacement"])
    
    def test_surgery_adds_refinement_keywords(self):
        """Test that surgery procedures add refinement keywords."""
        keywords = generate_search_keywords("rat", "survival surgery")
        
        assert any("surgical" in kw.lower() or "post-operative" in kw.lower()
                   for kw in keywords["refinement"])
    
    def test_tumor_adds_endpoint_keywords(self):
        """Test that tumor studies add endpoint keywords."""
        keywords = generate_search_keywords("mouse", "tumor model")
        
        assert any("tumor" in kw.lower() and "endpoint" in kw.lower()
                   for kw in keywords["refinement"])


class TestGenerateSearchString:
    """Tests for search string generation."""
    
    def test_joins_keywords_with_or(self):
        """Test default OR joining."""
        keywords = ["pain", "analgesia", "refinement"]
        result = generate_search_string(keywords)
        
        assert "pain OR analgesia OR refinement" == result
    
    def test_joins_keywords_with_and(self):
        """Test AND joining."""
        keywords = ["mouse", "alternative"]
        result = generate_search_string(keywords, boolean_operator="AND")
        
        assert "mouse AND alternative" == result
    
    def test_quotes_multi_word_terms(self):
        """Test that multi-word terms are quoted."""
        keywords = ["in vitro", "cell culture", "mouse"]
        result = generate_search_string(keywords)
        
        assert '"in vitro"' in result
        assert '"cell culture"' in result
        assert "mouse" in result  # Single word not quoted


class TestLiteratureSearchRecord:
    """Tests for search record model."""
    
    def test_create_search_record(self):
        """Test creating a search record."""
        record = LiteratureSearchRecord(
            database="PubMed",
            search_date="2024-01-15",
            date_range="2014-2024",
            keywords=["mouse", "alternative"],
            search_string="mouse OR alternative",
            results_count=150,
            relevant_count=5,
            notes="Found some relevant papers",
        )
        
        assert record.database == "PubMed"
        assert record.results_count == 150
        assert record.relevant_count == 5


class TestAlternativesSearchDocumentation:
    """Tests for search documentation model."""
    
    def test_create_documentation(self):
        """Test creating documentation model."""
        doc = AlternativesSearchDocumentation(
            search_date="2024-01-15",
            searcher_name="Test Researcher",
            animal_model="mouse",
            procedures="behavioral testing",
            replacement_keywords=["in vitro"],
            reduction_keywords=["sample size"],
            refinement_keywords=["humane endpoint"],
        )
        
        assert doc.animal_model == "mouse"
        assert not doc.replacement_available


class TestFormatSearchDocumentation:
    """Tests for documentation formatting."""
    
    def test_format_includes_required_sections(self):
        """Test that formatted output includes all required sections."""
        doc = AlternativesSearchDocumentation(
            search_date="2024-01-15",
            searcher_name="Dr. Smith",
            animal_model="mouse",
            procedures="behavioral testing",
            replacement_keywords=["in vitro", "cell culture"],
            reduction_keywords=["power analysis"],
            refinement_keywords=["humane endpoint"],
            searches=[
                LiteratureSearchRecord(
                    database="PubMed",
                    search_date="2024-01-15",
                    date_range="2014-2024",
                    keywords=["mouse", "alternative"],
                    search_string="mouse OR alternative",
                    results_count=100,
                    relevant_count=3,
                )
            ],
            replacement_available=False,
            justification="No suitable alternatives identified.",
        )
        
        result = format_search_documentation(doc)
        
        # Check required sections
        assert "LITERATURE SEARCH FOR ALTERNATIVES" in result
        assert "USDA-Compliant" in result
        assert "Search Date" in result
        assert "Dr. Smith" in result
        assert "mouse" in result
        assert "SEARCH KEYWORDS" in result
        assert "DATABASE SEARCHES" in result
        assert "SEARCH CONCLUSIONS" in result
        assert "Replacement Available: No" in result
    
    def test_format_includes_search_details(self):
        """Test that search details are included."""
        doc = AlternativesSearchDocumentation(
            search_date="2024-01-15",
            searcher_name="Researcher",
            animal_model="rat",
            procedures="testing",
            searches=[
                LiteratureSearchRecord(
                    database="AGRICOLA",
                    search_date="2024-01-15",
                    date_range="2014-2024",
                    keywords=["rat"],
                    search_string="rat",
                    results_count=50,
                    relevant_count=2,
                )
            ],
        )
        
        result = format_search_documentation(doc)
        
        assert "AGRICOLA" in result
        assert "50 total" in result
        assert "2 relevant" in result


class TestLiteratureSearchTool:
    """Tests for the LiteratureSearchTool."""
    
    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        tool = LiteratureSearchTool()
        
        assert tool.name == "literature_search_documentation"
        assert "alternatives" in tool.description.lower()
    
    def test_tool_generates_documentation(self):
        """Test tool generates documentation."""
        tool = LiteratureSearchTool()
        
        result = tool._run("animal_model: mouse, procedures: behavioral testing")
        
        assert "LITERATURE SEARCH" in result
        assert "mouse" in result
        assert "behavioral" in result
    
    def test_tool_handles_simple_input(self):
        """Test tool handles simple text input."""
        tool = LiteratureSearchTool()
        
        result = tool._run("toxicity testing in rats")
        
        assert "LITERATURE SEARCH" in result
        assert "toxicity" in result.lower()
    
    def test_tool_includes_recommended_databases(self):
        """Test tool includes recommended databases."""
        tool = LiteratureSearchTool()
        
        result = tool._run("animal_model: rabbit, procedures: surgery")
        
        # Should include at least PubMed and AGRICOLA
        assert "PubMed" in result
        assert "AGRICOLA" in result


class TestCreateSearchDocumentation:
    """Tests for the helper function."""
    
    def test_create_complete_documentation(self):
        """Test creating complete documentation."""
        result = create_search_documentation(
            animal_model="mouse",
            procedures="behavioral testing",
            searcher_name="Dr. Jones",
            searches=[
                {
                    "database": "PubMed",
                    "search_date": "2024-01-15",
                    "date_range": "2014-2024",
                    "keywords": ["mouse", "behavior", "alternative"],
                    "search_string": "mouse AND behavior AND alternative",
                    "results_count": 75,
                    "relevant_count": 4,
                }
            ],
            replacement_available=False,
            reduction_methods=["Power analysis performed"],
            refinement_methods=["Humane endpoints established"],
            justification="Live animal observation required for this behavioral study.",
        )
        
        assert "Dr. Jones" in result
        assert "PubMed" in result
        assert "75 total, 4 relevant" in result
        assert "Power analysis" in result
        assert "Humane endpoints" in result
        assert "Live animal observation" in result


class TestDatabaseConstants:
    """Tests for database constant definitions."""
    
    def test_required_databases_defined(self):
        """Test that required USDA databases are defined."""
        assert "pubmed" in REQUIRED_DATABASES
        assert "agricola" in REQUIRED_DATABASES
        assert "awic" in REQUIRED_DATABASES
    
    def test_alternatives_databases_defined(self):
        """Test that alternatives databases are defined."""
        assert "altbib" in ALTERNATIVES_DATABASES
        assert "altweb" in ALTERNATIVES_DATABASES
        assert "norina" in ALTERNATIVES_DATABASES
    
    def test_database_structure(self):
        """Test that databases have required fields."""
        for db_id, db_info in REQUIRED_DATABASES.items():
            assert "name" in db_info
            assert "url" in db_info
            assert "description" in db_info
