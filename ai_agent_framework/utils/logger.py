"""Logging configuration."""

import sys
from loguru import logger


def get_logger(name: str = "ai_agent"):
    """Get configured logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler with color
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG"
    )
    
    # Add file handler
    logger.add(
        f"logs/{name}.log",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level="INFO"
    )
    
    return logger.bind(name=name)
