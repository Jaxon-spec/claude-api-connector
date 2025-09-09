"""Custom exceptions for Claude API Connector."""

from typing import Optional

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
