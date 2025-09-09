# claude_api_connector/__init__.py
"""Claude API Connector - Universal API integration for Claude."""

from .core.connector import ClaudeConnector
from .core.config import APIConfig
from .core.exceptions import (
    ClaudeConnectorError,
    APIConnectionError,
    ClaudeAPIError,
    DataProcessingError
)

__version__ = "1.0.0"
__all__ = [
    "ClaudeConnector",
    "APIConfig", 
    "ClaudeConnectorError",
    "APIConnectionError",
    "ClaudeAPIError",
    "DataProcessingError"
]

# claude_api_connector/core/__init__.py
"""Core components for Claude API Connector."""

# claude_api_connector/utils/__init__.py
"""Utility functions for Claude API Connector."""

# claude_api_connector/core/config.py
"""Configuration classes for API connections."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
import os
from enum import Enum

class AuthType(Enum):
    """Supported authentication types."""
    BEARER = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"
    CUSTOM = "custom"

@dataclass
class APIConfig:
    """Configuration for external API connections."""
    
    base_url: str
    auth_type: AuthType = AuthType.BEARER
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_requests: Optional[int] = None
    rate_limit_window: int = 60
    
    # Authentication parameters
    api_key: Optional[str] = None
    auth_header: str = "Authorization"
    auth_param: Optional[str] = None  # For API key in query params
    
    def __post_init__(self):
        """Validate and setup configuration."""
        if not self.base_url:
            raise ValueError("base_url is required")
        
        # Set up authentication headers
        if self.api_key:
            if self.auth_type == AuthType.BEARER:
                self.headers[self.auth_header] = f"Bearer {self.api_key}"
            elif self.auth_type == AuthType.API_KEY and not self.auth_param:
                self.headers[self.auth_header] = self.api_key

@dataclass 
class ClaudeConfig:
    """Configuration for Claude API."""
    
    api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4000
    temperature: float = 0.0
    enable_memory: bool = False
    conversation_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate Claude configuration."""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter required")

# claude_api_connector/core/exceptions.py
"""Custom exceptions for Claude API Connector."""

class ClaudeConnectorError(Exception):
    """Base exception for Claude API Connector."""
    pass

class APIConnectionError(ClaudeConnectorError):
    """Exception raised when external API connection fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class ClaudeAPIError(ClaudeConnectorError):
    """Exception raised when Claude API interaction fails."""
    pass

class DataProcessingError(ClaudeConnectorError):
    """Exception raised when data processing fails."""
    pass

class AuthenticationError(ClaudeConnectorError):
    """Exception raised when authentication fails."""
    pass

class RateLimitError(ClaudeConnectorError):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after