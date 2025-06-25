"""
Tests for utils module
"""

import pytest
from unittest.mock import patch
from src.utils import validate_config, format_response, calculate_hash


class TestValidateConfig:
    """Test configuration validation."""
    
    def test_validate_config_valid(self):
        """Test validation with valid config."""
        config = {
            'app': {'name': 'test', 'version': '1.0'},
            'database': {'host': 'localhost'},
            'api': {'port': 8000}
        }
        assert validate_config(config) is True
    
    def test_validate_config_missing_keys(self):
        """Test validation with missing required keys."""
        config = {'app': {'name': 'test'}}
        assert validate_config(config) is False
    
    def test_validate_config_missing_app_details(self):
        """Test validation with missing app details."""
        config = {
            'app': {'name': 'test'},  # missing version
            'database': {},
            'api': {}
        }
        assert validate_config(config) is False


class TestFormatResponse:
    """Test response formatting."""
    
    def test_format_response_success(self):
        """Test successful response formatting."""
        result = format_response(True, "Success", {"key": "value"})
        expected = {
            'success': True,
            'message': "Success",
            'data': {"key": "value"}
        }
        assert result == expected
    
    def test_format_response_no_data(self):
        """Test response formatting without data."""
        result = format_response(False, "Error")
        expected = {
            'success': False,
            'message': "Error"
        }
        assert result == expected


class TestCalculateHash:
    """Test hash calculation."""
    
    def test_calculate_hash(self):
        """Test hash calculation."""
        text = "hello world"
        result = calculate_hash(text)
        assert isinstance(result, str)
        assert len(result) == 32  # MD5 hash length
