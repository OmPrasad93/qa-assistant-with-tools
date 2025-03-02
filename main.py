#!/usr/bin/env python3
"""
Main entry point for the Q&A Assistant application.
This script initializes the assistant and handles the CLI interface.
"""

import asyncio
import os
import sys
from typing import List, Dict, Any
import argparse

from assistant.router import QueryRouter
from assistant.memory import ConversationMemory
from tools.weather import WeatherTool
from tools.stock import StockTool
from utils.logger import setup_logger
from config import API_KEYS, SYSTEM_CONFIG

# Set up logger
logger = setup_logger("qa_assistant")


async def main():
    """
    Main function to run the Q&A Assistant.
    """
    print("🤖 Welcome to the Q&A Assistant! (Type 'exit' to quit)")
    print("---------------------------------------------------")

    # Check for required API keys
    missing_keys = []
    if not API_KEYS['MISTRAL_API_KEY']:
        missing_keys.append("MISTRAL_API_KEY")
    if not API_KEYS['WEATHER_API_KEY']:
        missing_keys.append("WEATHER_API_KEY")
    if not API_KEYS['ALPHA_VANTAGE_API_KEY']:
        missing_keys.append("ALPHA_VANTAGE_API_KEY")

    if missing_keys:
        print(f"⚠️  Warning: The following API keys are missing: {', '.join(missing_keys)}")
        print("Some functionality may be limited. You can set these in config.py or as environment variables.")
        logger.warning(f"Missing API keys: {', '.join(missing_keys)}")

    # Initialize tools
    try:
        logger.info("Initializing tools...")
        weather_tool = WeatherTool(api_key=API_KEYS['WEATHER_API_KEY'])
        stock_tool = StockTool(api_key=API_KEYS['ALPHA_VANTAGE_API_KEY'])

        # Initialize memory and router
        logger.info("Initializing memory and router...")
        memory = ConversationMemory(max_turns=args.max_turns)
        router = QueryRouter(
            api_key=API_KEYS['MISTRAL_API_KEY'],
            tools=[weather_tool, stock_tool],
            memory=memory
        )

        logger.info("Q&A Assistant initialized successfully with %d tools", len([weather_tool, stock_tool]))

        # Main interaction loop
        while True:
            # Get user input
            try:
                user_query = input("\n🧑 You: ")

                # Check for exit command
                if user_query.lower() in ['exit', 'quit', 'bye']:
                    print("\n🤖 Thank you for using Q&A Assistant. Goodbye!")
                    logger.info("User exited application")
                    break

                # Check for clear command
                if user_query.lower() in ['clear', 'reset']:
                    memory.clear()
                    print("\n🤖 Memory cleared. Let's start fresh!")
                    logger.info("Memory cleared by user")
                    continue

                # Check for empty query
                if not user_query.strip():
                    print("\n🤖 Please enter a question or command.")
                    continue

                # Process the query
                logger.info("Processing user query: %s", user_query)
                print("\n🤖 Assistant: ", end="")
                async for response_chunk in router.process_query(user_query):
                    print(response_chunk, end="", flush=True)
                print()  # Add newline after response

            except KeyboardInterrupt:
                # Handle Ctrl+C during input
                print("\n\n🤖 Interrupted. Type 'exit' to quit or continue with a new query.")
                logger.info("User interrupted input")
                continue

            except Exception as e:
                logger.error("Error processing query: %s", str(e), exc_info=SYSTEM_CONFIG['DEBUG_MODE'])
                print(f"\n❌ Error: {str(e)}")

    except Exception as e:
        logger.error("Failed to initialize Q&A Assistant: %s", str(e), exc_info=True)
        print(f"\n❌ Critical Error: {str(e)}")
        print("Q&A Assistant could not be initialized. Please check your configuration and API keys.")


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Q&A Assistant - An AI-powered question answering system")

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=SYSTEM_CONFIG['LOG_LEVEL'],
        help="Set the logging level"
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="Maximum number of conversation turns to remember"
    )

    return parser.parse_args()


if __name__ == "__main__":
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Update system configuration based on arguments
        if args.debug:
            SYSTEM_CONFIG['DEBUG_MODE'] = True
            SYSTEM_CONFIG['LOG_LEVEL'] = "DEBUG"
        else:
            SYSTEM_CONFIG['LOG_LEVEL'] = args.log_level

        # Re-configure logger with updated settings
        logger = setup_logger("qa_assistant", SYSTEM_CONFIG['LOG_LEVEL'])
        logger.info(f"Starting Q&A Assistant with log level: {SYSTEM_CONFIG['LOG_LEVEL']}")
        logger.info(f"Debug mode: {SYSTEM_CONFIG['DEBUG_MODE']}")
        logger.info(f"Max conversation turns: {args.max_turns}")

        # Run the main function
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\n\n🤖 Assistant shutting down. Goodbye!")

    except Exception as e:
        logger.critical("Unhandled exception: %s", str(e), exc_info=True)
        print(f"\n💥 Fatal error: {str(e)}")
        sys.exit(1)