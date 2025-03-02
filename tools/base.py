"""
Base class for all tools used by the Q&A Assistant.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BaseTool(ABC):
    """
    Abstract base class for all tools.

    All tools must implement the execute method and provide
    a tool_name, description, and parameters schema.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the tool with optional API key.

        Args:
            api_key (str, optional): API key for the service. Defaults to None.
        """
        self.api_key = api_key

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """
        Returns the name of the tool.

        Returns:
            str: Tool name
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Returns a description of what the tool does.

        Returns:
            str: Tool description
        """
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns the parameters schema for the tool.

        Returns:
            Dict[str, Dict[str, Any]]: Parameters schema in the format:
                {
                    "param_name": {
                        "type": "string|number|boolean",
                        "description": "Parameter description",
                        "required": True|False
                    },
                    ...
                }
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with the provided parameters.

        Args:
            **kwargs: Parameters for the tool execution

        Returns:
            Dict[str, Any]: Result of the tool execution
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation of the tool for the LLM prompt.

        Returns:
            Dict[str, Any]: Tool representation
        """
        return {
            "name": self.tool_name,
            "description": self.description,
            "parameters": self.parameters
        }