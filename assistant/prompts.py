"""
Prompt templates for the Q&A Assistant.
"""

from typing import List, Dict, Any
import json


def get_system_prompt(tools: List[Dict[str, Any]]) -> str:
    """
    Generate the system prompt for the Q&A Assistant.

    This includes instructions on when to use tools vs. general knowledge
    and how to format the responses.

    Args:
        tools (List[Dict[str, Any]]): List of available tools

    Returns:
        str: System prompt for the LLM
    """
    tools_json = json.dumps(tools, indent=2)

    return f"""You are an intelligent Q&A Assistant designed to help users by answering questions and performing actions.

Your capabilities:
1. Answer general knowledge questions directly using your built-in knowledge
2. Call external tools to fetch real-time or specialized information when needed

AVAILABLE TOOLS:
{tools_json}

INSTRUCTIONS:
- For general knowledge questions that don't require real-time data (like "Who is Albert Einstein?"), answer directly.
- For questions about real-time information (like weather, stock prices) or specialized data, use the appropriate tool.
- Analyze each query carefully to determine if it requires a tool or can be answered with general knowledge.

HOW TO USE TOOLS:
If a query requires a tool, respond in the following format:

```json
{{
  "use_tool": true,
  "tool_name": "[name of the tool]",
  "tool_parameters": {{
    "[parameter name]": "[parameter value]",
    ...
  }}
}}
```

EXAMPLES:

Example 1 (General Knowledge):
User: "What is the capital of France?"
Assistant: "The capital of France is Paris."

Example 2 (Weather Tool):
User: "What's the weather in New York right now?"
Assistant: ```json
{{
  "use_tool": true,
  "tool_name": "get_weather",
  "tool_parameters": {{
    "location": "New York"
  }}
}}

Example 3 (General Knowledge):
User: "What is the season in Delhi if current month is March?"
Assistant: "It is spring season."
```

Example 4 (Stock Tool):
User: "What's the current price of Apple stock?"
Assistant: ```json
{{
  "use_tool": true,
  "tool_name": "get_stock_price",
  "tool_parameters": {{
    "symbol": "AAPL"
  }}
}}
```

IMPORTANT:
- Always format tool calls as valid JSON.
- Only use the tools that are listed above.
- If a question is ambiguous, ask for clarification instead of using a tool. Better to clarify than to answer wrongly.
"""


def get_tool_response_prompt(tool_name: str, tool_response: Dict[str, Any], user_query: str) -> str:
    """
    Generate a prompt to have the LLM translate a tool response into natural language.

    Args:
        tool_name (str): Name of the tool
        tool_response (Dict[str, Any]): Tool response data
        user_query (str): Original user query

    Returns:
        str: Prompt for the LLM
    """
    response_json = json.dumps(tool_response, indent=2)

    return f"""The user asked: "{user_query}"

You used the "{tool_name}" tool, which returned the following information:

{response_json}

Please format this information into a natural, helpful response that directly answers the user's question.
If there was an error in the tool response, explain what went wrong in a friendly manner and suggest alternatives if possible.
"""