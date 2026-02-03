"""
Tests for configuration management.
"""

import pytest


class TestSettings:
    """Tests for Settings class."""

    def test_settings_loads_defaults(self, settings):
        """Settings should load with default values."""
        assert settings.environment == "testing"
        assert settings.debug is True

    def test_cors_origins_parsing(self, settings):
        """CORS origins string should be parsed into list."""
        settings.cors_origins = "http://localhost:3000,http://example.com"
        origins = settings.cors_origins_list
        assert len(origins) == 2
        assert "http://localhost:3000" in origins
        assert "http://example.com" in origins

    def test_api_key_validation(self, settings):
        """API key validation should report correct status."""
        settings.anthropic_api_key = None
        settings.openai_api_key = "test_key"

        status = settings.validate_api_keys()
        assert status["anthropic"] is False
        assert status["openai"] is True

    def test_api_key_validation_with_anthropic(self, settings):
        """API key validation with Anthropic key set."""
        settings.anthropic_api_key = "test_anthropic_key"
        settings.openai_api_key = None

        status = settings.validate_api_keys()
        assert status["anthropic"] is True
        assert status["openai"] is False
