"""
Configuration file for the Q&A Assistant.
Contains API keys and other configuration parameters.
"""

import os
from typing import Dict

# API keys (load from environment variables if available)
API_KEYS: Dict[str, str] = {
    'MISTRAL_API_KEY': os.environ.get('MISTRAL_API_KEY'),
    'WEATHER_API_KEY': os.environ.get('WEATHER_API_KEY'),  # OpenWeatherMap API key
    'ALPHA_VANTAGE_API_KEY': os.environ.get('ALPHA_VANTAGE_API_KEY'),  # Alpha Vantage API key
}

# LLM configuration
LLM_CONFIG = {
    'MODEL': 'mistral-tiny',  # Model to use
    'MAX_TOKENS': 1024,       # Maximum number of tokens in the response
    'TEMPERATURE': 0.7,       # Randomness of the model's output
}

# System configuration
SYSTEM_CONFIG = {
    'DEBUG_MODE': os.environ.get('DEBUG_MODE', 'False').lower() == 'true',
    'LOG_LEVEL': os.environ.get('LOG_LEVEL', 'INFO'),
}