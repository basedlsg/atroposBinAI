"""
Logging utilities for spatial RL environment.

Provides consistent, structured logging across all modules.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Sets up a properly configured logger with consistent formatting.

    Args:
        name: Logger name (typically __name__ from calling module)
        level: Logging level (default: INFO)
        format_string: Optional custom format string

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Task initialized successfully")
        2024-01-15 10:30:45 - spatial_env - INFO - Task initialized successfully
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Create formatter
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    formatter = logging.Formatter(
        format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def setup_detailed_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Sets up a logger with more detailed output including file/line numbers.

    Useful for debugging complex issues.

    Args:
        name: Logger name
        level: Logging level (default: DEBUG for detailed logging)

    Returns:
        Configured logger with detailed formatting
    """
    format_string = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[%(filename)s:%(lineno)d] - %(message)s'
    )
    return setup_logger(name, level, format_string)


def get_logger(name: str) -> logging.Logger:
    """
    Gets an existing logger or creates a new one with default settings.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set it up
    if not logger.handlers:
        return setup_logger(name)

    return logger
