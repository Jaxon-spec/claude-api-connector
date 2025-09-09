# claude_api_connector/core/connector.py
"""Main connector class for Claude API integration."""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
import aiohttp

from anthropic import Anthropic, AsyncAnthropic

from .config import APIConfig, ClaudeConfig
from .exceptions import (
    APIConnectionError, 
    ClaudeAPIError, 
    DataProcessingError,
    RateLimitError,
    AuthenticationError
)

logger = logging.getLogger(__name__)

class ClaudeConnector:
    """Main connector class for integrating Claude with external APIs."""
    
    def __init__(
        self, 
        anthropic_api_key: Optional[str] = None,
        api_config: Optional[APIConfig] = None,
        claude_config: Optional[ClaudeConfig] = None
    ):
        """Initialize the Claude connector.
        
        Args:
            anthropic_api_key: Anthropic API key (optional if set in env)
            api_config: Configuration for external API
            claude_config: Configuration for Claude API
        """
        # Setup Claude configuration
        if claude_config is None:
            claude_config = ClaudeConfig()
        if anthropic_api_key:
            claude_config.api_key = anthropic_api_key
            
        self.claude_config = claude_config
        self.api_config = api_config
        
        # Initialize Claude client (use async version)
        self.claude_client = AsyncAnthropic(api_key=self.claude_config.api_key)
        
        # Conversation management
        self.conversation_history: List[Dict[str, str]] = []
        
        # Rate limiting - improved sliding window
        self._request_times: List[float] = []
        self._last_cleanup = time.time()
        
        # Custom data processors
        self._data_processors: List[Callable] = []
        
    async def query_with_api_data(
        self,
        prompt: str,
        api_endpoint: str,
        api_params: Optional[Dict[str, Any]] = None,
        api_method: str = "GET",
        include_raw_data: bool = False
    ) -> Dict[str, Any]:
        """Query Claude with data from an external API.
        
        Args:
            prompt: The prompt to send to Claude
            api_endpoint: API endpoint to fetch data from
            api_params: Parameters for the API request
            api_method: HTTP method for the API request
            include_raw_data: Whether to include raw API response
            
        Returns:
            Dictionary containing Claude's response and metadata
        """
        try:
            # Fetch data from external API
            logger.info(f"Fetching data from {api_endpoint}")
            api_data = await self._fetch_api_data(api_endpoint, api_params, api_method)
            
            # Process the API data
            processed_data = self._process_data(api_data)
            
            # Create enhanced prompt with API data
            enhanced_prompt = self._create_enhanced_prompt(prompt, processed_data)
            
            # Query Claude
            logger.info("Sending query to Claude")
            claude_response = await self._query_claude(enhanced_prompt)
            
            # Prepare response
            result = {
                "response": claude_response,
                "prompt": prompt,
                "api_endpoint": api_endpoint,
                "processed_data_summary": self._summarize_data(processed_data),
                "timestamp": time.time()
            }
            
            if include_raw_data:
                result["raw_api_data"] = api_data
                result["processed_data"] = processed_data
                
            return result
            
        except Exception as e:
            logger.error(f"Error in query_with_api_data: {str(e)}")
            raise
    
    async def batch_process(
        self,
        endpoints: List[Dict[str, Any]],
        analysis_prompt: str,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Process multiple API endpoints and analyze with Claude.
        
        Args:
            endpoints: List of endpoint configurations
            analysis_prompt: Prompt for analyzing all the data
            max_concurrent: Maximum concurrent API requests
            
        Returns:
            Dictionary containing analysis results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_single_endpoint(endpoint_config: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                endpoint = endpoint_config.get("endpoint", "")
                params = endpoint_config.get("params", {})
                method = endpoint_config.get("method", "GET")
                
                try:
                    data = await self._fetch_api_data(endpoint, params, method)
                    return {
                        "endpoint": endpoint,
                        "data": self._process_data(data),
                        "success": True
                    }
                except Exception as e:
                    logger.error(f"Error fetching {endpoint}: {str(e)}")
                    return {
                        "endpoint": endpoint,
                        "error": str(e),
                        "success": False
                    }
        
        # Fetch all endpoints concurrently
        logger.info(f"Fetching data from {len(endpoints)} endpoints")
        results = await asyncio.gather(
            *[fetch_single_endpoint(config) for config in endpoints],
            return_exceptions=True
        )
        
        # Compile successful results
        successful_results = []
        failed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_results.append({"error": str(result), "success": False})
            elif isinstance(result, dict):
                if result.get("success"):
                    successful_results.append(result)
                else:
                    failed_results.append(result)
        
        # Create combined analysis prompt
        combined_data = {
            result["endpoint"]: result["data"] 
            for result in successful_results
        }
        
        enhanced_prompt = self._create_enhanced_prompt(analysis_prompt, combined_data)
        
        # Get Claude's analysis
        claude_response = await self._query_claude(enhanced_prompt)
        
        return {
            "analysis": claude_response,
            "successful_endpoints": len(successful_results),
            "failed_endpoints": len(failed_results),
            "failures": failed_results,
            "data_summary": self._summarize_data(combined_data),
            "timestamp": time.time()
        }
    
    async def stream_conversation(
        self,
        prompt: str,
        api_endpoint: Optional[str] = None,
        api_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Maintain conversation context across multiple queries.
        
        Args:
            prompt: The conversation prompt
            api_endpoint: Optional API endpoint for additional data
            api_params: Parameters for API request
            
        Returns:
            Dictionary containing response and conversation context
        """
        enhanced_prompt = prompt
        
        # Fetch API data if endpoint provided
        if api_endpoint:
            api_data = await self._fetch_api_data(api_endpoint, api_params)
            processed_data = self._process_data(api_data)
            enhanced_prompt = self._create_enhanced_prompt(prompt, processed_data)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": enhanced_prompt
        })
        
        # Query Claude with conversation context
        response = await self._query_claude_with_history()
        
        # Add Claude's response to history
        self.conversation_history.append({
            "role": "assistant", 
            "content": response
        })
        
        return {
            "response": response,
            "conversation_length": len(self.conversation_history),
            "timestamp": time.time()
        }
    
    def set_data_processor(self, processor: Callable[[Any], Any]) -> None:
        """Add a custom data processor function.
        
        Args:
            processor: Function that takes raw API data and returns processed data
        """
        self._data_processors.append(processor)
    
    def clear_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
    
    async def _fetch_api_data(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """Fetch data from external API."""
        if not self.api_config:
            raise APIConnectionError("No API configuration provided")
        
        # Rate limiting check
        await self._check_rate_limit()
        
        url = f"{self.api_config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Prepare request parameters
        request_params = {
            "timeout": aiohttp.ClientTimeout(total=self.api_config.timeout)
        }
        
        if params:
            if method.upper() == "GET":
                request_params["params"] = params.copy()
            else:
                request_params["json"] = params
        
        # Add API key to params if specified
        if (self.api_config.auth_type.value == "api_key" and 
            self.api_config.auth_param and 
            self.api_config.api_key):
            if "params" not in request_params:
                request_params["params"] = {}
            request_params["params"][self.api_config.auth_param] = self.api_config.api_key
        
        async with aiohttp.ClientSession(headers=self.api_config.headers) as session:
            
            for attempt in range(self.api_config.max_retries + 1):
                try:
                    async with session.request(method, url, **request_params) as response:
                        
                        # Record request time for rate limiting
                        self._request_times.append(time.time())
                        
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 60))
                            if attempt < self.api_config.max_retries:
                                logger.warning(f"Rate limited, retrying after {retry_after}s")
                                await asyncio.sleep(retry_after)
                                continue
                            else:
                                raise RateLimitError(
                                    "Rate limit exceeded", 
                                    retry_after=retry_after
                                )
                        
                        if response.status == 401:
                            raise AuthenticationError("Authentication failed")
                        
                        if not response.ok:
                            error_text = await response.text()
                            raise APIConnectionError(
                                f"API request failed: {response.status}",
                                status_code=response.status,
                                response_data=error_text
                            )
                        
                        # Try to parse JSON, fall back to text
                        try:
                            return await response.json()
                        except (json.JSONDecodeError, aiohttp.ContentTypeError):
                            text_data = await response.text()
                            return {"raw_text": text_data}
                
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < self.api_config.max_retries:
                        delay = self.api_config.retry_delay * (2 ** attempt)
                        logger.warning(f"Request failed, retrying in {delay}s: {str(e)}")
                        await asyncio.sleep(delay)
                    else:
                        raise APIConnectionError(f"API request failed after retries: {str(e)}")
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limits with improved sliding window."""
        if not self.api_config.rate_limit_requests:
            return
        
        now = time.time()
        
        # Clean up old requests periodically
        if now - self._last_cleanup > 10:  # Clean every 10 seconds
            window_start = now - self.api_config.rate_limit_window
            self._request_times = [t for t in self._request_times if t > window_start]
            self._last_cleanup = now
        
        # Check if we're at the limit
        window_start = now - self.api_config.rate_limit_window
        recent_requests = [t for t in self._request_times if t > window_start]
        
        if len(recent_requests) >= self.api_config.rate_limit_requests:
            sleep_time = recent_requests[0] + self.api_config.rate_limit_window - now
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
    
    def _process_data(self, data: Any) -> Any:
        """Process raw API data through custom processors."""
        processed = data
        
        for processor in self._data_processors:
            try:
                processed = processor(processed)
            except Exception as e:
                logger.error(f"Data processor failed: {str(e)}")
                raise DataProcessingError(f"Data processing failed: {str(e)}")
        
        return processed
    
    def _create_enhanced_prompt(self, prompt: str, data: Any) -> str:
        """Create an enhanced prompt that includes API data."""
        if not data:
            return prompt
        
        # Convert data to readable format with size limits
        if isinstance(data, dict):
            # Limit dict size for Claude
            limited_data = dict(list(data.items())[:20])  # First 20 items
            if len(data) > 20:
                limited_data["...truncated"] = f"{len(data) - 20} more items"
            data_str = json.dumps(limited_data, indent=2, default=str)
        elif isinstance(data, list):
            # Limit list size
            limited_data = data[:10]
            data_str = json.dumps(limited_data, indent=2, default=str)
            if len(data) > 10:
                data_str += f"\n... and {len(data) - 10} more items"
        else:
            data_str = str(data)[:5000]  # Limit string length
        
        enhanced_prompt = f"""{prompt}

Here is the relevant data to analyze:

```json
{data_str}
```

Please provide your analysis based on this data."""
        
        return enhanced_prompt
    
    async def _query_claude(self, prompt: str) -> str:
        """Query Claude with a single prompt."""
        try:
            response = await self.claude_client.messages.create(
                model=self.claude_config.model,
                max_tokens=self.claude_config.max_tokens,
                temperature=self.claude_config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            raise ClaudeAPIError(f"Claude API request failed: {str(e)}")
    
    async def _query_claude_with_history(self) -> str:
        """Query Claude with conversation history."""
        try:
            response = await self.claude_client.messages.create(
                model=self.claude_config.model,
                max_tokens=self.claude_config.max_tokens,
                temperature=self.claude_config.temperature,
                messages=self.conversation_history
            )
            
            return response.content[0].text
        
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            raise ClaudeAPIError(f"Claude API request failed: {str(e)}")
    
    def _summarize_data(self, data: Any) -> Dict[str, Any]:
        """Create a summary of the processed data."""
        if isinstance(data, dict):
            return {
                "type": "dictionary",
                "keys": list(data.keys())[:10],  # Limit keys shown
                "total_keys": len(data),
                "size_mb": len(json.dumps(data, default=str)) / 1024 / 1024
            }
        elif isinstance(data, list):
            return {
                "type": "list", 
                "length": len(data),
                "sample": data[:3] if data else [],
                "size_mb": len(json.dumps(data, default=str)) / 1024 / 1024
            }
        else:
            return {
                "type": type(data).__name__,
                "preview": str(data)[:100],
                "length": len(str(data))
            }

    async def close(self):
        """Clean up resources."""
        await self.claude_client.close()