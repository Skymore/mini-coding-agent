"""
Tests for main module
"""

import pytest
import yaml
from unittest.mock import patch, mock_open
from src.main import load_config, initialize_app


class TestLoadConfig:
    """Test configuration loading."""
    
    def test_load_config_success(self):
        """Test successful config loading."""
        mock_config = {'app': {'name': 'test'}}
        mock_yaml = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=mock_yaml)):
            result = load_config('test.yaml')
            assert result == mock_config
    
    def test_load_config_file_not_found(self):
        """Test config loading when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = load_config('missing.yaml')
            assert result == {}


class TestInitializeApp:
    """Test application initialization."""
    
    @patch('src.main.validate_config')
    @patch('src.main.setup_logging')
    def test_initialize_app_success(self, mock_logging, mock_validate):
        """Test successful app initialization."""
        mock_validate.return_value = True
        config = {'logging': {'level': 'INFO'}}
        
        result = initialize_app(config)
        
        assert result is True
        mock_validate.assert_called_once_with(config)
        mock_logging.assert_called_once_with({'level': 'INFO'})
    
    @patch('src.main.validate_config')
    def test_initialize_app_invalid_config(self, mock_validate):
        """Test app initialization with invalid config."""
        mock_validate.return_value = False
        
        result = initialize_app({})
        
        assert result is False
