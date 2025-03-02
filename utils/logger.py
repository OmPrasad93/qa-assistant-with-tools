"""
Logging utility for the Q&A Assistant.
"""

import logging
import sys
import os
from typing import Optional
from datetime import datetime

from config import SYSTEM_CONFIG


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with the specified name and level.

    Args:
        name (str): Logger name
        level (Optional[str], optional): Logging level. Defaults to the level in SYSTEM_CONFIG.

    Returns:
        logging.Logger: Configured logger
    """
    # Determine log level
    level = level or SYSTEM_CONFIG['LOG_LEVEL']
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Make sure the logger doesn't have handlers already
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Set up file handler for logging to a file
    log_file = os.path.join(log_dir, f'{name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    # Add file handler to logger
    logger.addHandler(file_handler)

    # Log a message indicating logger setup
    logger.info(f"Logger initialized with level {level} - logging to {log_file}")

    return logger