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
