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
