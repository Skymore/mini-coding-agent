# API Documentation

## Overview

This document describes the API endpoints and data models for the sample application.

## Data Models

### User

```python
class User(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None
    is_active: bool = True
```

### Config

```python
class Config(BaseModel):
    app_name: str
    version: str
    debug: bool = False
    database_url: Optional[str] = None
    api_key: Optional[str] = None
```

### APIResponse

```python
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error_code: Optional[str] = None
```

## Functions

### Main Functions

- `load_config(config_path: str)`: Load configuration from YAML file
- `initialize_app(config: dict)`: Initialize application with configuration
- `main()`: Main application entry point

### Utility Functions

- `setup_logging(config: dict)`: Setup logging configuration
- `validate_config(config: dict)`: Validate application configuration
- `get_env_var(key: str, default: str)`: Get environment variable
- `format_response(success: bool, message: str, data: Any)`: Format API response
- `calculate_hash(text: str)`: Calculate MD5 hash of text

## Usage Examples

### Basic Usage

```python
from src.main import main
from src.models import User

# Create user
user = User(name="John Doe", email="john@example.com")

# Run application
main()
```
