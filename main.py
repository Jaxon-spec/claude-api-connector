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
