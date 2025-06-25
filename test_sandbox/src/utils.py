"""
Utility Functions

This module contains utility functions used throughout the application.
"""

import logging
import os
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]) -> None:
    """Setup logging configuration."""
    level = config.get('level', 'INFO')
    format_str = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_str
    )


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate application configuration."""
    required_keys = ['app', 'database', 'api']
    
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required config key: {key}")
            return False
    
    # Validate app config
    app_config = config['app']
    if 'name' not in app_config or 'version' not in app_config:
        logging.error("App config missing name or version")
        return False
    
    return True


def get_env_var(key: str, default: str = None) -> str:
    """Get environment variable with optional default."""
    return os.getenv(key, default)


def format_response(success: bool, message: str, data: Any = None) -> Dict[str, Any]:
    """Format standard API response."""
    response = {
        'success': success,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return response


def calculate_hash(text: str) -> str:
    """Calculate simple hash of text."""
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()
