#!/usr/bin/env python3
"""
Main Application Module

This is the entry point for the sample application used in PLANNER testing.
"""

import os
import yaml
import click
from .models import User, Config
from .utils import setup_logging, validate_config


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        click.echo(f"Config file {config_path} not found!")
        return {}


def initialize_app(config: dict) -> bool:
    """Initialize the application with given configuration."""
    if not validate_config(config):
        return False
    
    setup_logging(config.get('logging', {}))
    return True


@click.command()
@click.option('--config', default='config.yaml', help='Configuration file path')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def main(config: str, debug: bool):
    """Main application entry point."""
    click.echo("Starting Sample Application...")
    
    # Load configuration
    app_config = load_config(config)
    if debug:
        app_config['app']['debug'] = True
    
    # Initialize application
    if not initialize_app(app_config):
        click.echo("Failed to initialize application!")
        return 1
    
    # Create sample user
    user = User(name="Test User", email="test@example.com")
    click.echo(f"Created user: {user.name}")
    
    click.echo("Application started successfully!")
    return 0


if __name__ == '__main__':
    main()
