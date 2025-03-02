"""
Stock price tool for the Q&A Assistant.
Uses the Alpha Vantage API to get stock information.
"""

import aiohttp
from typing import Dict, Any
from datetime import datetime
import json
import traceback

from tools.base import BaseTool
from utils.logger import setup_logger
from config import SYSTEM_CONFIG


# Set up logger at module level
logger = setup_logger("stock_tool", SYSTEM_CONFIG['LOG_LEVEL'])


class StockTool(BaseTool):
    """
    Tool for fetching stock price information using Alpha Vantage API.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the stock tool.

        Args:
            api_key (str, optional): API key for Alpha Vantage
        """
        super().__init__(api_key=api_key)
        self.logger = logger

        # Log initialization status
        if not api_key:
            self.logger.warning("Stock tool initialized without API key")
        else:
            self.logger.info("Stock tool initialized successfully")

    @property
    def tool_name(self) -> str:
        return "get_stock_price"

    @property
    def description(self) -> str:
        return "Get current stock price information for a specified ticker symbol"

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "symbol": {
                "type": "string",
                "description": "The stock ticker symbol (e.g., 'AAPL' for Apple, 'MSFT' for Microsoft)",
                "required": True
            }
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Get stock price information for the specified ticker symbol.

        Args:
            symbol (str): Stock ticker symbol

        Returns:
            Dict[str, Any]: Stock price information
        """
        symbol = kwargs.get("symbol")

        self.logger.info(f"Fetching stock price for symbol: {symbol}")

        if not symbol:
            self.logger.error("Stock symbol parameter is missing")
            raise ValueError("Stock symbol is required")

        # Check if API key is available
        if not self.api_key:
            self.logger.error("Alpha Vantage API key is missing")
            return {
                "error": "Alpha Vantage API key is missing",
                "details": "Please provide a valid Alpha Vantage API key in the configuration"
            }

        # Clean up the symbol (remove any whitespace, convert to uppercase)
        symbol = symbol.strip().upper()
        self.logger.debug(f"Processed symbol: {symbol}")

        try:
            self.logger.debug(f"Making API request to Alpha Vantage for {symbol}")
            async with aiohttp.ClientSession() as session:
                # Make API request to Alpha Vantage
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": self.api_key
                }

                self.logger.debug(f"API URL: {url}, Params: {params}")

                async with session.get(url, params=params) as response:
                    status_code = response.status
                    self.logger.debug(f"API response status code: {status_code}")

                    if status_code != 200:
                        error_data = await response.text()
                        self.logger.error(f"Stock API error: Status {status_code}, Response: {error_data}")
                        return {
                            "error": f"Stock API error: {status_code}",
                            "details": error_data
                        }

                    data = await response.json()
                    self.logger.debug(f"API response data: {json.dumps(data)}")

                    # Check if we have valid data
                    if "Global Quote" not in data or not data["Global Quote"]:
                        error_msg = f"No data found for symbol: {symbol}"
                        self.logger.error(error_msg)
                        return {
                            "error": error_msg,
                            "details": "The requested stock symbol may be invalid or not available"
                        }

                    quote = data["Global Quote"]

                    # Format the response
                    try:
                        formatted_response = {
                            "symbol": quote.get("01. symbol", symbol),
                            "price": float(quote.get("05. price", 0)),
                            "change": float(quote.get("09. change", 0)),
                            "change_percent": quote.get("10. change percent", "0%"),
                            "volume": int(quote.get("06. volume", 0)),
                            "latest_trading_day": quote.get("07. latest trading day", "N/A"),
                            "previous_close": float(quote.get("08. previous close", 0))
                        }
                    except (ValueError, TypeError) as e:
                        self.logger.error(f"Error parsing stock data: {str(e)}", exc_info=True)
                        return {
                            "error": f"Error parsing stock data: {str(e)}",
                            "details": f"Raw data: {json.dumps(quote)}"
                        }

                    # Add timestamp of when we fetched this data
                    formatted_response["fetched_at"] = datetime.now().isoformat()

                    self.logger.info(f"Successfully retrieved stock price for {symbol}")
                    return formatted_response

        except aiohttp.ClientError as e:
            error_msg = f"Network error connecting to stock API: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "details": traceback.format_exc()
            }
        except Exception as e:
            error_msg = f"Error fetching stock data: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "details": traceback.format_exc()
            }