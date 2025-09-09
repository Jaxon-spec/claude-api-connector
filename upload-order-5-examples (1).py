# main.py
"""Main example script demonstrating various use cases."""

import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from claude_api_connector import ClaudeConnector, APIConfig
from claude_api_connector.core.config import AuthType
from claude_api_connector.core.exceptions import ClaudeConnectorError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_functionality():
    """Test basic connector functionality with a public API."""
    print("🧪 Testing Basic Functionality")
    print("-" * 40)
    
    try:
        # Test with JSONPlaceholder (public API, no auth needed)
        config = APIConfig(
            base_url="https://jsonplaceholder.typicode.com",
            timeout=10
        )
        
        connector = ClaudeConnector(api_config=config)
        
        # Test single query
        result = await connector.query_with_api_data(
            prompt="Analyze this user data and tell me about this person's profile",
            api_endpoint="/users/1"
        )
        
        print(f"✅ Single query successful")
        print(f"Response preview: {result['response'][:200]}...")
        
        # Test batch processing
        endpoints = [
            {"endpoint": "/users/1"},
            {"endpoint": "/users/1/posts", "params": {"_limit": 3}},
            {"endpoint": "/users/1/albums", "params": {"_limit": 2}}
        ]
        
        batch_result = await connector.batch_process(
            endpoints=endpoints,
            analysis_prompt="Provide insights about this user based on their profile, posts, and albums."
        )
        
        print(f"✅ Batch processing successful")
        print(f"Successful endpoints: {batch_result['successful_endpoints']}")
        print(f"Analysis preview: {batch_result['analysis'][:200]}...")
        
        await connector.close()
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

async def test_conversation_mode():
    """Test conversation management."""
    print("\n💬 Testing Conversation Mode")
    print("-" * 40)
    
    try:
        config = APIConfig(
            base_url="https://jsonplaceholder.typicode.com",
            timeout=10
        )
        
        connector = ClaudeConnector(api_config=config)
        
        # First message in conversation
        result1 = await connector.stream_conversation(
            "Tell me about this user",
            api_endpoint="/users/1"
        )
        
        # Follow-up message (Claude should remember context)
        result2 = await connector.stream_conversation(
            "What posts has this user made? Limit to 3 posts.",
            api_endpoint="/users/1/posts",
            api_params={"_limit": 3}
        )
        
        print(f"✅ Conversation mode successful")
        print(f"Conversation length: {result2['conversation_length']} messages")
        print(f"Follow-up response: {result2['response'][:200]}...")
        
        await connector.close()
        return True
        
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        return False

async def test_error_handling():
    """Test error handling with invalid endpoints."""
    print("\n⚠️  Testing Error Handling")
    print("-" * 40)
    
    try:
        config = APIConfig(
            base_url="https://jsonplaceholder.typicode.com",
            timeout=10
        )
        
        connector = ClaudeConnector(api_config=config)
        
        # Test with non-existent endpoint
        try:
            await connector.query_with_api_data(
                prompt="This should fail",
                api_endpoint="/non-existent-endpoint"
            )
            print("❌ Error handling failed - should have thrown exception")
            return False
        except ClaudeConnectorError:
            print("✅ Error handling successful - caught expected exception")
            
        await connector.close()
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🤖 Claude API Connector - Test Suite")
    print("=" * 50)
    
    # Check required environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY environment variable is required")
        print("Please set your Claude API key:")
        print("export ANTHROPIC_API_KEY='your-api-key-here'")
        return
    
    # Run tests
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Conversation Mode", test_conversation_mode),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            if success:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The connector is working correctly.")
    elif passed > 0:
        print("⚠️  Some tests passed. Check the failures above.")
    else:
        print("❌ All tests failed. Please check your configuration.")
    
    print(f"\n📚 Next steps:")
    print(f"1. Set up API keys for services you want to use")
    print(f"2. Check the examples/ directory for more detailed usage")
    print(f"3. Read the documentation for advanced features")

if __name__ == "__main__":
    asyncio.run(main())

# examples/weather_example.py
"""Example: Weather API integration with Claude."""

import asyncio
import logging
from claude_api_connector import ClaudeConnector, APIConfig
from claude_api_connector.core.config import AuthType
from claude_api_connector.core.exceptions import APIConnectionError, ClaudeAPIError

logger = logging.getLogger(__name__)

class WeatherClaudeConnector:
    """Specialized connector for weather data analysis with improved error handling."""
    
    def __init__(self, openweather_api_key: str):
        if not openweather_api_key:
            raise ValueError("OpenWeatherMap API key is required")
            
        # Configure OpenWeatherMap API
        weather_config = APIConfig(
            base_url="https://api.openweathermap.org/data/2.5",
            auth_type=AuthType.API_KEY,
            auth_param="appid",
            api_key=openweather_api_key,
            timeout=15,
            max_retries=2
        )
        
        self.connector = ClaudeConnector(api_config=weather_config)
        
        # Add weather data processor
        self.connector.set_data_processor(self._process_weather_data)
    
    def _process_weather_data(self, weather_data: dict) -> dict:
        """Process raw weather data for better Claude analysis."""
        try:
            if "main" in weather_data:
                return {
                    "location": weather_data.get("name", "Unknown"),
                    "country": weather_data.get("sys", {}).get("country", "Unknown"),
                    "coordinates": weather_data.get("coord", {}),
                    "temperature": {
                        "current": weather_data["main"]["temp"],
                        "feels_like": weather_data["main"]["feels_like"],
                        "min": weather_data["main"]["temp_min"],
                        "max": weather_data["main"]["temp_max"]
                    },
                    "humidity": weather_data["main"]["humidity"],
                    "pressure": weather_data["main"]["pressure"],
                    "weather": weather_data["weather"][0] if weather_data["weather"] else {},
                    "wind": weather_data.get("wind", {}),
                    "visibility": weather_data.get("visibility"),
                    "clouds": weather_data.get("clouds", {}),
                    "timestamp": weather_data.get("dt"),
                    "sunrise": weather_data.get("sys", {}).get("sunrise"),
                    "sunset": weather_data.get("sys", {}).get("sunset")
                }
            return weather_data
        except Exception as e:
            logger.error(f"Weather data processing failed: {e}")
            return weather_data  # Return original data if processing fails
    
    async def get_weather_analysis(self, city: str) -> str:
        """Get weather analysis for a city with error handling."""
        try:
            result = await self.connector.query_with_api_data(
                prompt=f"Provide a comprehensive weather analysis for {city}. Include current conditions, comfort level, and any recommendations for outdoor activities or clothing.",
                api_endpoint="/weather",
                api_params={"q": city, "units": "metric"}
            )
            return result["response"]
        except APIConnectionError as e:
            if e.status_code == 404:
                return f"City '{city}' not found. Please check the spelling or try a different city name."
            elif e.status_code == 401:
                return "Weather API authentication failed. Please check your API key."
            else:
                return f"Weather API error: {str(e)}"
        except ClaudeAPIError as e:
            return f"Claude analysis failed: {str(e)}"
    
    async def close(self):
        """Clean up resources."""
        await self.connector.close()

# examples/github_example.py
"""Example: GitHub API integration with Claude."""

import asyncio
from claude_api_connector import ClaudeConnector, APIConfig
from claude_api_connector.core.config import AuthType

class GitHubClaudeConnector:
    """Specialized connector for GitHub repository analysis."""
    
    def __init__(self, github_token: str):
        # Configure GitHub API
        github_config = APIConfig(
            base_url="https://api.github.com",
            auth_type=AuthType.BEARER,
            api_key=github_token,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=30
        )
        
        self.connector = ClaudeConnector(api_config=github_config)
    
    async def analyze_repository(self, repo_path: str) -> str:
        """Analyze a GitHub repository."""
        # Get repository info, recent commits, and issues
        endpoints = [
            {"endpoint": f"/repos/{repo_path}"},
            {"endpoint": f"/repos/{repo_path}/commits", "params": {"per_page": 10}},
            {"endpoint": f"/repos/{repo_path}/issues", "params": {"state": "open", "per_page": 10}},
            {"endpoint": f"/repos/{repo_path}/languages"}
        ]
        
        result = await self.connector.batch_process(
            endpoints=endpoints,
            analysis_prompt=f"Analyze this GitHub repository ({repo_path}). Provide insights about the project's health, recent activity, technology stack, and any notable issues or patterns."
        )
        return result["analysis"]
    
    async def close(self):
        """Clean up resources."""
        await self.connector.close()

# claude_api_connector/utils/helpers.py
"""Utility functions for the Claude API Connector."""

import json
import csv
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Union, Optional
import logging

logger = logging.getLogger(__name__)

def parse_json_safely(data: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string."""
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        return None

def csv_to_dict_list(csv_string: str) -> List[Dict[str, Any]]:
    """Convert CSV string to list of dictionaries."""
    try:
        reader = csv.DictReader(csv_string.strip().split('\n'))
        return list(reader)
    except Exception as e:
        logger.error(f"CSV parsing failed: {e}")
        return []

def xml_to_dict(xml_string: str) -> Optional[Dict[str, Any]]:
    """Convert XML string to dictionary."""
    try:
        root = ET.fromstring(xml_string)
        
        def elem_to_dict(elem):
            result = {}
            for child in elem:
                if len(child) == 0:
                    result[child.tag] = child.text
                else:
                    result[child.tag] = elem_to_dict(child)
            return result
        
        return {root.tag: elem_to_dict(root)}
    except ET.ParseError as e:
        logger.error(f"XML parsing failed: {e}")
        return None

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def sanitize_for_claude(data: Any, max_size: int = 50000) -> str:
    """Sanitize and truncate data for Claude processing."""
    if isinstance(data, (dict, list)):
        json_str = json.dumps(data, default=str, indent=2)
    else:
        json_str = str(data)
    
    if len(json_str) > max_size:
        json_str = json_str[:max_size] + "... [truncated]"
    
    return json_str