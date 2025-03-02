import json
import asyncio
import traceback
from typing import List, Dict, Any, AsyncGenerator, Optional
import re

from mistralai import Mistral

from assistant.memory import ConversationMemory
from assistant.prompts import get_system_prompt, get_tool_response_prompt
from tools.base import BaseTool
from config import LLM_CONFIG
from utils.logger import setup_logger
from config import SYSTEM_CONFIG

# Set up logger
logger = setup_logger("query_router", SYSTEM_CONFIG['LOG_LEVEL'])


class QueryRouter:
    """
    Routes user queries to either the LLM or appropriate tools.
    """

    def __init__(
        self,
        api_key: str,
        tools: List[BaseTool],
        memory: ConversationMemory
    ):
        """
        Initialize the query router.

        Args:
            api_key (str): API key for the LLM service
            tools (List[BaseTool]): List of available tools
            memory (ConversationMemory): Conversation memory manager
        """
        self.client = Mistral(api_key=api_key)
        self.tools = tools
        self.memory = memory
        self.logger = logger

        # Create a mapping of tool names to tool objects for easier lookup
        self.tool_map = {tool.tool_name: tool for tool in tools}

        # Log initialization
        tool_names = [tool.tool_name for tool in tools]
        self.logger.info(f"QueryRouter initialized with tools: {', '.join(tool_names)}")

    async def process_query(self, query: str) -> AsyncGenerator[str, None]:
        """
        Process a user query and route it to the appropriate handler.

        Args:
            query (str): User query

        Yields:
            str: Response chunks
        """
        self.logger.info(f"Processing query: {query}")

        # Add the user query to memory
        self.memory.add_user_message(query)

        # Prepare messages for the LLM, including conversation history
        messages = []

        # Add system prompt
        system_prompt = get_system_prompt([t.to_dict() for t in self.tools])
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        self.logger.debug(f"System prompt length: {len(system_prompt)} characters")

        # Add conversation history
        history = self.memory.get_messages()
        for msg in history[:-1]:  # Exclude the latest user message which we'll add separately
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        self.logger.debug(f"Added {len(history)-1} messages from conversation history")

        # Add the current user query
        messages.append({
            "role": "user",
            "content": query
        })

        try:
            self.logger.debug(f"Sending request to Mistral API with model: {LLM_CONFIG['MODEL']}")

            # Get routing decision from LLM
            response = await self.client.chat.stream_async(
                model=LLM_CONFIG['MODEL'],
                messages=messages,
                max_tokens=LLM_CONFIG['MAX_TOKENS'],
                temperature=LLM_CONFIG['TEMPERATURE']
            )

            # Collect the full response
            full_response = ""
            self.logger.debug("Starting to collect response chunks")
            async for chunk in response:
                if chunk.data.choices[0].delta.content is not None:
                    content = chunk.data.choices[0].delta.content
                    full_response += content

            self.logger.debug(f"Collected full response of length: {len(full_response)} characters")

            # Check if the response is a tool call (JSON format)
            tool_call = self._extract_tool_call(full_response)

            if tool_call and tool_call.get("use_tool", False):
                # This is a tool call
                tool_name = tool_call.get("tool_name")
                tool_parameters = tool_call.get("tool_parameters", {})

                self.logger.info(f"Tool call detected: {tool_name} with parameters: {tool_parameters}")

                if tool_name in self.tool_map:
                    # Execute the tool
                    tool = self.tool_map[tool_name]

                    # Yield a message indicating the tool is being used
                    indicator_msg = f"I'll check that for you using {tool_name}...\n\n"
                    yield indicator_msg

                    # Execute the tool and get the response
                    self.logger.debug(f"Executing tool: {tool_name}")
                    try:
                        tool_response = await tool.execute(**tool_parameters)
                        self.logger.debug(f"Tool response: {json.dumps(tool_response)}")
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {str(e)}"
                        self.logger.error(error_msg, exc_info=True)
                        tool_response = {
                            "error": error_msg,
                            "details": traceback.format_exc()
                        }

                    # Add tool response to memory
                    self.memory.add_tool_message(tool_name, tool_response)

                    # Format the tool response using the LLM
                    response_prompt = get_tool_response_prompt(tool_name, tool_response, query)

                    self.logger.debug(f"Sending tool response to LLM for formatting")
                    response = await self.client.chat.stream_async(
                        model=LLM_CONFIG['MODEL'],
                        messages=[{"role": "user", "content": response_prompt}],
                        max_tokens=LLM_CONFIG['MAX_TOKENS'],
                        temperature=LLM_CONFIG['TEMPERATURE']
                    )

                    # Stream the formatted response
                    formatted_response = ""
                    self.logger.debug("Starting to collect formatted response chunks")
                    async for chunk in response:
                        if chunk.data.choices[0].delta.content is not None:
                            content = chunk.data.choices[0].delta.content
                            formatted_response += content
                            yield content

                    self.logger.debug(f"Formatted response length: {len(formatted_response)} characters")

                    # Add the assistant's formatted response to memory
                    self.memory.add_assistant_message(formatted_response)

                else:
                    # Tool not found
                    error_msg = f"I attempted to use a tool called '{tool_name}', but it's not available. Let me answer based on what I know."
                    self.logger.warning(f"Tool not found: {tool_name}")
                    yield error_msg

                    # Fall back to general knowledge
                    self.logger.debug("Falling back to general knowledge")
                    async for chunk in self._answer_with_llm(query):
                        yield chunk

            else:
                # This is a general knowledge question, yield the LLM response directly
                self.logger.info("Using general knowledge to answer query")
                yield full_response

                # Add the assistant's response to memory
                self.memory.add_assistant_message(full_response)

        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            self.logger.error(f"Error processing query: {str(e)}", exc_info=True)
            yield error_msg

    async def _answer_with_llm(self, query: str) -> AsyncGenerator[str, None]:
        """
        Answer a query using the LLM's general knowledge.

        Args:
            query (str): User query

        Yields:
            str: Response chunks
        """
        # Prepare messages
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Answer the user's question based on your general knowledge."},
            {"role": "user", "content": query}
        ]

        try:
            # Get response from LLM
            response = await self.client.chat.stream_async(
                model=LLM_CONFIG['MODEL'],
                messages=messages,
                max_tokens=LLM_CONFIG['MAX_TOKENS'],
                temperature=LLM_CONFIG['TEMPERATURE']
            )

            # Stream the response
            full_response = ""
            async for chunk in response:
                if chunk.data.choices[0].delta.content is not None:
                    content = chunk.data.choices[0].delta.content
                    full_response += content
                    yield content

            # Add the assistant's response to memory
            self.memory.add_assistant_message(full_response)

        except Exception as e:
            error_msg = f"I encountered an error providing a general knowledge answer: {str(e)}"
            yield error_msg

    def _extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract a tool call from the LLM response.

        Args:
            text (str): LLM response text

        Returns:
            Optional[Dict[str, Any]]: Tool call parameters or None if no valid tool call
        """
        # Try to find JSON blocks in the response
        json_matches = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', text)

        if not json_matches:
            # Try to find JSON without code blocks
            json_matches = [text]

        for potential_json in json_matches:
            try:
                data = json.loads(potential_json)

                # Check if this looks like a tool call
                if isinstance(data, dict) and "use_tool" in data:
                    return data
            except json.JSONDecodeError:
                continue

        return None