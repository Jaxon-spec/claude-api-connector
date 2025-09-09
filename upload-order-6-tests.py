# tests/__init__.py
"""Test suite for Claude API Connector."""

# tests/conftest.py
"""Pytest configuration and fixtures."""

import pytest
import asyncio
import os

# Set test environment variables
os.environ["ANTHROPIC_API_KEY"] = "test-key"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# tests/test_config.py
"""Tests for configuration classes."""

import pytest
import os
from claude_api_connector.core.config import APIConfig, ClaudeConfig, AuthType

class TestAPIConfig:
    """Test cases for APIConfig."""
    
    def test_basic_config_creation(self):
        """Test basic API config creation."""
        config = APIConfig(
            base_url="https://api.test.com",
            api_key="test-key"
        )
        
        assert config.base_url == "https://api.test.com"
        assert config.api_key == "test-key"
        assert config.auth_type == AuthType.BEARER
    
    def test_bearer_auth_setup(self):
        """Test bearer authentication setup."""
        config = APIConfig(
            base_url="https://api.test.com",
            auth_type=AuthType.BEARER,
            api_key="test-key"
        )
        
        assert config.headers["Authorization"] == "Bearer test-key"
    
    def test_api_key_auth_setup(self):
        """Test API key authentication setup."""
        config = APIConfig(
            base_url="https://api.test.com",
            auth_type=AuthType.API_KEY,
            api_key="test-key"
        )
        
        assert config.headers["Authorization"] == "test-key"
    
    def test_invalid_base_url(self):
        """Test validation of base URL."""
        with pytest.raises(ValueError):
            APIConfig(base_url="")

class TestClaudeConfig:
    """Test cases for ClaudeConfig."""
    
    def test_config_with_api_key(self):
        """Test Claude config with provided API key."""
        config = ClaudeConfig(api_key="test-claude-key")
        
        assert config.api_key == "test-claude-key"
        assert config.model == "claude-3-5-sonnet-20241022"
    
    def test_config_with_env_var(self):
        """Test Claude config with environment variable."""
        os.environ["ANTHROPIC_API_KEY"] = "env-test-key"
        
        config = ClaudeConfig()
        assert config.api_key == "env-test-key"
        
        # Clean up
        del os.environ["ANTHROPIC_API_KEY"]

# tests/test_connector.py
"""Tests for the main ClaudeConnector class."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import json

from claude_api_connector import ClaudeConnector, APIConfig
from claude_api_connector.core.config import AuthType, ClaudeConfig
from claude_api_connector.core.exceptions import APIConnectionError, ClaudeAPIError

@pytest.fixture
def api_config():
    """Create a test API configuration."""
    return APIConfig(
        base_url="https://api.test.com",
        auth_type=AuthType.BEARER,
        api_key="test-key",
        timeout=10
    )

@pytest.fixture
def claude_config():
    """Create a test Claude configuration."""
    return ClaudeConfig(
        api_key="test-claude-key",
        model="claude-3-5-sonnet-20241022"
    )

@pytest.fixture
def connector(api_config, claude_config):
    """Create a test connector instance."""
    return ClaudeConnector(
        api_config=api_config,
        claude_config=claude_config
    )

class TestClaudeConnector:
    """Test cases for ClaudeConnector."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, connector):
        """Test connector initialization."""
        assert connector.api_config is not None
        assert connector.claude_config is not None
        assert connector.conversation_history == []
    
    @pytest.mark.asyncio
    async def test_query_with_api_data_success(self, connector):
        """Test successful API query and Claude response."""
        mock_api_data = {"test": "data", "value": 42}
        mock_claude_response = "This is a test analysis."
        
        with patch.object(connector, '_fetch_api_data', return_value=mock_api_data), \
             patch.object(connector, '_query_claude', return_value=mock_claude_response):
            
            result = await connector.query_with_api_data(
                prompt="Analyze this data",
                api_endpoint="/test"
            )
            
            assert result["response"] == mock_claude_response
            assert result["prompt"] == "Analyze this data"
            assert result["api_endpoint"] == "/test"
            assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_batch_process_success(self, connector):
        """Test successful batch processing."""
        mock_api_data = {"batch": "data"}
        mock_claude_response = "Batch analysis complete."
        
        endpoints = [
            {"endpoint": "/test1", "params": {"id": 1}},
            {"endpoint": "/test2", "params": {"id": 2}}
        ]
        
        with patch.object(connector, '_fetch_api_data', return_value=mock_api_data), \
             patch.object(connector, '_query_claude', return_value=mock_claude_response):
            
            result = await connector.batch_process(
                endpoints=endpoints,
                analysis_prompt="Analyze all data"
            )
            
            assert result["analysis"] == mock_claude_response
            assert result["successful_endpoints"] == 2
            assert result["failed_endpoints"] == 0
    
    @pytest.mark.asyncio
    async def test_conversation_stream(self, connector):
        """Test conversation streaming functionality."""
        mock_claude_response = "Conversation response."
        
        with patch.object(connector, '_query_claude_with_history', return_value=mock_claude_response):
            
            result = await connector.stream_conversation("Hello Claude")
            
            assert result["response"] == mock_claude_response
            assert len(connector.conversation_history) == 2  # User + Assistant
            assert connector.conversation_history[0]["role"] == "user"
            assert connector.conversation_history[1]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_api_connection_error(self, connector):
        """Test handling of API connection errors."""
        with patch.object(connector, '_fetch_api_data', side_effect=APIConnectionError("Connection failed")):
            
            with pytest.raises(APIConnectionError):
                await connector.query_with_api_data(
                    prompt="Test", 
                    api_endpoint="/fail"
                )
    
    def test_data_processor(self, connector):
        """Test custom data processor functionality."""
        def test_processor(data):
            data["processed"] = True
            return data
        
        connector.set_data_processor(test_processor)
        
        test_data = {"original": "data"}
        processed = connector._process_data(test_data)
        
        assert processed["processed"] is True
        assert processed["original"] == "data"
    
    def test_conversation_clearing(self, connector):
        """Test conversation history clearing."""
        connector.conversation_history = [{"role": "user", "content": "test"}]
        connector.clear_conversation()
        assert connector.conversation_history == []

# tests/test_utils.py
"""Tests for utility functions."""

import pytest
from claude_api_connector.utils.helpers import (
    parse_json_safely,
    csv_to_dict_list,
    xml_to_dict,
    flatten_dict,
    sanitize_for_claude
)

class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_parse_json_safely_valid(self):
        """Test JSON parsing with valid JSON."""
        json_str = '{"test": "data", "number": 42}'
        result = parse_json_safely(json_str)
        
        assert result == {"test": "data", "number": 42}
    
    def test_parse_json_safely_invalid(self):
        """Test JSON parsing with invalid JSON."""
        invalid_json = '{"test": invalid}'
        result = parse_json_safely(invalid_json)
        
        assert result is None
    
    def test_csv_to_dict_list(self):
        """Test CSV to dictionary conversion."""
        csv_str = "name,age\nJohn,30\nJane,25"
        result = csv_to_dict_list(csv_str)
        
        expected = [
            {"name": "John", "age": "30"},
            {"name": "Jane", "age": "25"}
        ]
        assert result == expected
    
    def test_flatten_dict(self):
        """Test dictionary flattening."""
        nested_dict = {
            "level1": {
                "level2": {
                    "value": "test"
                },
                "simple": "data"
            }
        }
        
        result = flatten_dict(nested_dict)
        expected = {
            "level1.level2.value": "test",
            "level1.simple": "data"
        }
        
        assert result == expected
    
    def test_sanitize_for_claude(self):
        """Test data sanitization for Claude."""
        large_data = {"key": "x" * 60000}  # Exceeds default max_size
        result = sanitize_for_claude(large_data, max_size=100)
        
        assert len(result) <= 115  # 100 + "... [truncated]"
        assert "truncated" in result