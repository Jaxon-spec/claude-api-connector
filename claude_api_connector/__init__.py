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
