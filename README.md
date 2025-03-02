# Q&A Assistant

An AI-powered question-answering system that combines general knowledge from an LLM with real-time data from specialized tools.

## Overview

Q&A Assistant is a conversational AI system that can:

1. Answer general knowledge questions directly using a Large Language Model (Mistral AI)
2. Fetch real-time information using specialized tools (currently Weather and Stock Price APIs)
3. Maintain conversation context through a memory system

The system intelligently routes queries to either the LLM or the appropriate tool based on the nature of the question.

## Features

- **Intelligent Query Routing**: Automatically decides whether to use the LLM or call an external API based on the query
- **Tool Integration**: External API integration for real-time data (Weather and Stock prices)
- **Conversational Memory**: Maintains context across multiple conversation turns
- **Streaming Responses**: Delivers responses in chunks for a more interactive experience
- **Robust Error Handling**: Graceful fallbacks if tools are unavailable or return errors
- **Comprehensive Logging**: Detailed logs for debugging and monitoring


## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/qa-assistant.git
cd qa-assistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up API keys in config.py or as environment variables:
```bash
export MISTRAL_API_KEY="your_mistral_api_key"
export WEATHER_API_KEY="your_openweathermap_api_key"
export ALPHA_VANTAGE_API_KEY="your_alphavantage_api_key"
```

## Usage

### Basic Usage

Run the Q&A Assistant:

```bash
python main.py
```

Interact with the assistant through the command line.

### Example Conversation

Here's a real conversation example showing how the assistant uses both tools and general knowledge:

```
🧑 You: What is the weather like in Delhi

🤖 Assistant: I'll check that for you using get_weather...

The weather in Delhi, India right now is quite hazy with a temperature of 16.05 
degrees Celsius. The temperature feels like 15.36 degrees Celsius, and the 
humidity is currently at 63%. The wind is blowing at a speed of 1.03 meters per 
second, and the atmospheric pressure is 1011 hPa. It might be a good idea to 
wear comfortable clothing and carry an umbrella due to the haze. Enjoy your day in Delhi!

🧑 You: What is the season in Delhi given that it is the month of March

🤖 Assistant: The month of March falls in the spring season in Delhi, India. 
This season is characterized by warm and pleasant weather, with temperatures 
ranging from 10 to 25 degrees Celsius. The air is often dry during this period, 
making it an enjoyable time to explore the city and its many attractions.

🧑 You: Yes but I am asking if apples are abundant in spring in Delhi

🤖 Assistant: I apologize for the confusion earlier. To answer your question about 
whether apples are abundant in spring in Delhi, I would need to use external tools 
to check for real-time or specialized information. However, I am currently unable 
to access such tools.

As a general knowledge assistant, I can tell you that apples are not a native 
fruit to India and are not typically abundant in Delhi during the spring season. 
You can check with local markets or fruit vendors for the availability of apples 
during this time.

🧑 You: Okay but can you tell me the Apple stock price

🤖 Assistant: I'll check that for you using get_stock_price...

Of course! As of March 3, 2025, the Apple Inc. (AAPL) stock price is $241.84. 
Since the previous closing price of $237.3, the stock has seen an increase of $4.54, 
which equates to a 1.91% change. The trading volume for this day was approximately 
56,833,600 shares.
```

This example demonstrates how the assistant:
1. Uses the weather tool for real-time weather information
2. Provides general knowledge about seasons in Delhi
3. Clarifies limitations for certain queries
4. Switches to the stock tool when detecting a request for stock information

### Command-Line Options

```bash
# Run with debug logging
python main.py --debug

# Set a specific logging level
python main.py --log-level=INFO

# Adjust the conversation memory (number of turns to remember)
python main.py --max-turns=15
```

### Special Commands

- `exit`, `quit`, or `bye`: Exit the application
- `clear` or `reset`: Clear the conversation memory

## API Keys

The application requires the following API keys:

1. **Mistral AI API** - For the language model
   - Sign up at: https://console.mistral.ai/
   
2. **OpenWeatherMap API** - For the weather tool
   - Sign up at: https://openweathermap.org/api
   
3. **Alpha Vantage API** - For the stock price tool
   - Sign up at: https://www.alphavantage.co/

## Extending with New Tools

To add a new tool:

1. Create a new class in the `tools/` directory that inherits from `BaseTool`
2. Implement the required methods (tool_name, description, parameters, execute)
3. Add the tool to the list of available tools in `main.py`

Example of a minimal new tool:

```python
from tools.base import BaseTool

class MyNewTool(BaseTool):
    @property
    def tool_name(self) -> str:
        return "my_new_tool"
    
    @property
    def description(self) -> str:
        return "Description of what my tool does"
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "param1": {
                "type": "string",
                "description": "Description of parameter 1",
                "required": True
            }
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        # Implementation goes here
        return {"result": "output"}
```

## Troubleshooting

### Logs

Logs are stored in the `logs/` directory. To increase verbosity, run with the `--debug` flag.

### Common Issues

- **Tool API Errors**: Check that your API keys are correctly set and that you have internet connectivity
- **Memory Issues**: If the assistant seems to forget context, try increasing `--max-turns`
- **Incorrect Tool Selection**: The system may occasionally route to the wrong tool. You can always reset with the `clear` command


