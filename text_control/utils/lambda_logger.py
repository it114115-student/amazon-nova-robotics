"""
Lambda-compatible logging utility
"""

import logging
import os


def get_lambda_logger(name: str, level: str = None) -> logging.Logger:
    """
    Get a Lambda-compatible logger

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If not provided, uses LOG_LEVEL environment variable or defaults to INFO

    Returns:
        Configured logger instance
    """
    # Determine log level
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Convert string level to logging constant
    numeric_level = getattr(logging, level, logging.INFO)

    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Only add handler if none exists (prevents duplicate logs in Lambda)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(numeric_level)

        # Use a format that works well in CloudWatch
        formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Allow propagation for development environment, prevent in Lambda
    logger.propagate = not os.getenv("AWS_LAMBDA_FUNCTION_NAME")

    return logger


def configure_root_logger():
    """
    Configure the root logger for Lambda environment
    This should be called once at the module level
    """
    root_logger = logging.getLogger()

    # Set level from environment or default to INFO
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, level, logging.INFO)
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add a single StreamHandler for Lambda
    handler = logging.StreamHandler()
    handler.setLevel(numeric_level)
    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


# Auto-configure if running in Lambda environment
if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    configure_root_logger()
