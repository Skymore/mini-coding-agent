"""
Data Models

This module contains data models used in the sample application.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User data model."""
    name: str
    email: EmailStr
    age: Optional[int] = None
    is_active: bool = True
    
    def __str__(self):
        return f"User(name='{self.name}', email='{self.email}')"
    
    def deactivate(self):
        """Deactivate the user."""
        self.is_active = False
    
    def activate(self):
        """Activate the user."""
        self.is_active = True


class Config(BaseModel):
    """Application configuration model."""
    app_name: str
    version: str
    debug: bool = False
    database_url: Optional[str] = None
    api_key: Optional[str] = None
    
    class Config:
        env_prefix = "APP_"


class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[dict] = None
    error_code: Optional[str] = None
