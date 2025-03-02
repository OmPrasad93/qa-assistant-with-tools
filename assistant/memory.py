"""
Conversation memory management for the Q&A Assistant.
Stores and retrieves conversation history.
"""

from typing import List, Dict, Any, Optional
from collections import deque
import json


class ConversationMemory:
    """
    Manages conversation memory for the Q&A Assistant.

    Stores the conversation history as a list of messages and provides
    methods to add and retrieve messages.
    """

    def __init__(self, max_turns: int = 10):
        """
        Initialize the conversation memory.

        Args:
            max_turns (int, optional): Maximum number of conversation turns to remember.
                                      Defaults to 10.
        """
        self.max_turns = max_turns
        self.messages = []

    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the conversation history.

        Args:
            content (str): Message content
        """
        self.messages.append({
            "role": "user",
            "content": content
        })
        self._truncate_history()

    def add_assistant_message(self, content: str) -> None:
        """
        Add an assistant message to the conversation history.

        Args:
            content (str): Message content
        """
        self.messages.append({
            "role": "assistant",
            "content": content
        })
        self._truncate_history()

    def add_tool_message(self, tool_name: str, content: Dict[str, Any]) -> None:
        """
        Add a tool response message to the conversation history.

        Args:
            tool_name (str): Name of the tool
            content (Dict[str, Any]): Tool response content
        """
        self.messages.append({
            "role": "tool",
            "tool_name": tool_name,
            "content": json.dumps(content)
        })
        self._truncate_history()

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get all messages in the conversation history.

        Returns:
            List[Dict[str, Any]]: List of messages
        """
        return self.messages.copy()

    def get_formatted_history(self) -> str:
        """
        Get a human-readable formatted string of the conversation history.

        Returns:
            str: Formatted conversation history
        """
        formatted = []
        for msg in self.messages:
            role = msg["role"]
            if role == "user":
                formatted.append(f"User: {msg['content']}")
            elif role == "assistant":
                formatted.append(f"Assistant: {msg['content']}")
            elif role == "tool":
                tool_name = msg.get("tool_name", "unknown_tool")
                content = json.loads(msg["content"])
                formatted.append(f"Tool ({tool_name}): {json.dumps(content, indent=2)}")

        return "\n\n".join(formatted)

    def clear(self) -> None:
        """
        Clear all messages from the conversation history.
        """
        self.messages = []

    def _truncate_history(self) -> None:
        """
        Truncate the conversation history to the maximum number of turns.
        A turn consists of a user message and its corresponding assistant response.
        """
        if len(self.messages) <= self.max_turns * 2:
            return

        # Remove theoldest turns while preserving complete exchanges
        # Keep the system message if it exists
        has_system = self.messages and self.messages[0]["role"] == "system"
        start_idx = 1 if has_system else 0

        # Calculate how many messages to remove
        num_to_remove = len(self.messages) - (self.max_turns * 2) - (1 if has_system else 0)

        # Remove the oldest non-system messages
        self.messages = self.messages[:start_idx] + self.messages[start_idx + num_to_remove:]