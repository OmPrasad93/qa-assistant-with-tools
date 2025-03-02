"""
Weather tool for the Q&A Assistant.
Uses the OpenWeatherMap API to get weather information.
"""

import aiohttp
from typing import Dict, Any
import json
import traceback

from tools.base import BaseTool
from utils.logger import setup_logger
from config import SYSTEM_CONFIG


# Set up logger at module level
logger = setup_logger("weather_tool", SYSTEM_CONFIG['LOG_LEVEL'])


class WeatherTool(BaseTool):
    """
    Tool for fetching weather information using OpenWeatherMap API.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the weather tool.

        Args:
            api_key (str, optional): API key for OpenWeatherMap
        """
        super().__init__(api_key=api_key)
        self.logger = logger

        # Log initialization status
        if not api_key:
            self.logger.warning("Weather tool initialized without API key")
        else:
            self.logger.info("Weather tool initialized successfully")

    @property
    def tool_name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get current weather information for a specified location"

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "location": {
                "type": "string",
                "description": "The city name or location to get weather for (e.g., 'New York', 'London, UK')",
                "required": True
            },
            "units": {
                "type": "string",
                "description": "Units of measurement. Options: 'metric' (Celsius), 'imperial' (Fahrenheit), 'standard' (Kelvin)",
                "required": False
            }
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Get weather for the specified location.

        Args:
            location (str): City name or location
            units (str, optional): Units of measurement ('metric', 'imperial', or 'standard')
                                  Defaults to 'metric'.

        Returns:
            Dict[str, Any]: Weather information
        """
        location = kwargs.get("location")
        units = kwargs.get("units", "metric")

        self.logger.info(f"Fetching weather for location: {location} with units: {units}")

        if not location:
            self.logger.error("Location parameter is missing")
            raise ValueError("Location is required")

        # Check if API key is available
        if not self.api_key:
            self.logger.error("Weather API key is missing")
            return {
                "error": "Weather API key is missing",
                "details": "Please provide a valid OpenWeatherMap API key in the configuration"
            }

        # Validate units
        if units not in ["metric", "imperial", "standard"]:
            self.logger.warning(f"Invalid units '{units}', defaulting to 'metric'")
            units = "metric"  # Default to metric if invalid

        try:
            self.logger.debug(f"Making API request to OpenWeatherMap for {location}")
            async with aiohttp.ClientSession() as session:
                # Make API request to OpenWeatherMap
                url = "https://api.openweathermap.org/data/2.5/weather"
                params = {
                    "q": location,
                    "units": units,
                    "appid": self.api_key
                }

                self.logger.debug(f"API URL: {url}, Params: {params}")

                async with session.get(url, params=params) as response:
                    status_code = response.status
                    self.logger.debug(f"API response status code: {status_code}")

                    if status_code != 200:
                        error_data = await response.text()
                        self.logger.error(f"Weather API error: Status {status_code}, Response: {error_data}")
                        return {
                            "error": f"Weather API error: {status_code}",
                            "details": error_data
                        }

                    data = await response.json()
                    self.logger.debug(f"API response data: {json.dumps(data)}")

                    # Format the response
                    temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
                    wind_unit = "m/s" if units == "metric" else "mph" if units == "imperial" else "m/s"

                    formatted_response = {
                        "location": f"{data['name']}, {data.get('sys', {}).get('country', '')}",
                        "temperature": f"{data['main']['temp']}{temp_unit}",
                        "feels_like": f"{data['main']['feels_like']}{temp_unit}",
                        "condition": data['weather'][0]['main'],
                        "description": data['weather'][0]['description'],
                        "humidity": f"{data['main']['humidity']}%",
                        "wind_speed": f"{data['wind']['speed']} {wind_unit}",
                        "pressure": f"{data['main']['pressure']} hPa",
                        "timestamp": data['dt']
                    }

                    self.logger.info(f"Successfully retrieved weather for {location}")
                    return formatted_response

        except aiohttp.ClientError as e:
            error_msg = f"Network error connecting to weather API: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "details": traceback.format_exc()
            }
        except KeyError as e:
            error_msg = f"Unexpected data format from weather API (missing key: {str(e)})"
            self.logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "details": traceback.format_exc()
            }
        except Exception as e:
            error_msg = f"Error fetching weather data: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "details": traceback.format_exc()
            }