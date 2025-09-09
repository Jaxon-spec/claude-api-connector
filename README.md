Claude API Connector
A flexible Python framework for connecting any API to Claude, enabling seamless integration and data exchange between Claude and external services.

Features
🔌 Universal API Connector: Connect to any REST API with minimal configuration
🤖 Claude Integration: Built-in Claude API client with conversation management
🛡️ Security First: Secure API key management and request validation
📊 JSON/Text Support: Primary support for JSON and text data with CSV/XML utilities
⚡ Async Support: High-performance async operations
🔄 Error Handling: Comprehensive error handling and retry logic
📖 Working Examples: Ready-to-use examples for popular APIs
Installation
From Source
bash
git clone https://github.com/theRealDanB/claude-api-connector.git
cd claude-api-connector
pip install -r requirements.txt
pip install -e .
Environment Setup
Create a .env file:

env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_TIMEOUT=30
MAX_RETRIES=3
LOG_LEVEL=INFO
Quick Start
python
import asyncio
from claude_api_connector import ClaudeConnector, APIConfig

async def main():
    # Configure your external API
    api_config = APIConfig(
        base_url="https://api.example.com",
        headers={"Authorization": "Bearer YOUR_API_KEY"},
        timeout=30
    )

    # Initialize Claude connector
    connector = ClaudeConnector(
        anthropic_api_key="your-claude-api-key",
        api_config=api_config
    )

    # Connect and query
    result = await connector.query_with_api_data(
        prompt="Analyze this weather data",
        api_endpoint="/weather/current",
        api_params={"city": "San Francisco"}
    )

    print(result["response"])
    await connector.close()

# Run the example
asyncio.run(main())
Working Examples
Test with Public API (No Keys Required)
python
import asyncio
from claude_api_connector import ClaudeConnector, APIConfig

async def test_basic():
    # JSONPlaceholder - free public API
    config = APIConfig(base_url="https://jsonplaceholder.typicode.com")
    connector = ClaudeConnector(api_config=config)
    
    result = await connector.query_with_api_data(
        prompt="Tell me about this user's profile",
        api_endpoint="/users/1"
    )
    
    print(result["response"])
    await connector.close()

asyncio.run(test_basic())
Weather API Integration
python
from claude_api_connector import ClaudeConnector, APIConfig
from claude_api_connector.core.config import AuthType

async def weather_example():
    weather_config = APIConfig(
        base_url="https://api.openweathermap.org/data/2.5",
        auth_type=AuthType.API_KEY,
        auth_param="appid",
        api_key="your_weather_api_key"
    )
    
    connector = ClaudeConnector(api_config=weather_config)
    
    result = await connector.query_with_api_data(
        prompt="What's the weather like? Any recommendations?",
        api_endpoint="/weather",
        api_params={"q": "London", "units": "metric"}
    )
    
    print(result["response"])
    await connector.close()
Core Features
Batch Processing
python
endpoints = [
    {"endpoint": "/users", "params": {"active": True}},
    {"endpoint": "/orders", "params": {"status": "completed"}},
    {"endpoint": "/products", "params": {"category": "electronics"}}
]

result = await connector.batch_process(
    endpoints=endpoints,
    analysis_prompt="Provide a comprehensive business overview"
)

print(result["analysis"])
Conversation Memory
python
# First query - Claude remembers this context
result1 = await connector.stream_conversation(
    prompt="Analyze this sales data",
    api_endpoint="/sales/monthly"
)

# Follow-up query - Claude maintains context
result2 = await connector.stream_conversation(
    prompt="Now compare it to last year",
    api_endpoint="/sales/yearly"  
)
Custom Data Processing
python
def custom_processor(api_response):
    # Your custom data transformation logic
    processed_data = transform_data(api_response)
    return processed_data

connector.set_data_processor(custom_processor)
Supported APIs
This connector works with any REST API, including:

Weather: OpenWeatherMap, AccuWeather
Development: GitHub, GitLab, Jira
Social Media: Twitter, Reddit, LinkedIn
E-commerce: Shopify, WooCommerce, Stripe
Cloud Services: AWS, Google Cloud, Azure
And many more...
Testing
Run the included test suite:

bash
# Set your Claude API key
export ANTHROPIC_API_KEY="your_key_here"

# Run tests (uses public APIs, no additional keys needed)
python main.py

# Run specific tests  
pytest tests/
Error Handling
python
from claude_api_connector.core.exceptions import (
    APIConnectionError, 
    ClaudeAPIError
)

try:
    result = await connector.query_with_api_data(
        prompt="Analyze this data",
        api_endpoint="/data"
    )
except APIConnectionError as e:
    print(f"API connection failed: {e}")
except ClaudeAPIError as e:
    print(f"Claude API error: {e}")
Important Notes
Claude API Costs
Each query to Claude costs based on input/output tokens
Large datasets will increase costs
Consider data size limits and preprocessing
Rate Limits
Respects both external API and Claude rate limits
Built-in retry logic with exponential backoff
Configurable concurrent request limits
Data Size Considerations
Large API responses are automatically truncated for Claude
Implement custom processors for data summarization
Consider batch processing for multiple small requests vs. large single requests
Development
bash
# Development setup
git clone https://github.com/theRealDanB/claude-api-connector.git
cd claude-api-connector
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .

# Run tests
pytest tests/

# Format code
black claude_api_connector/ tests/ examples/
Contributing
Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Make your changes and add tests
Ensure tests pass (pytest)
Format code (black .)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request
Troubleshooting
Common Issues
"No module named claude_api_connector"
bash
pip install -e .
"ANTHROPIC_API_KEY not found"
bash
export ANTHROPIC_API_KEY="your_key_here"
# or create .env file
API Authentication Errors
Verify your API keys are correct
Check the API documentation for auth requirements
Ensure proper AuthType (BEARER, API_KEY, etc.)
Rate Limit Errors
Increase delays between requests
Reduce batch_process concurrent limit
Check API provider rate limits
License
This project is licensed under the MIT License - see the LICENSE file for details.

Support
🐛 Issue Tracker
💬 Discussions
Built with ❤️ for seamless AI-API integration

