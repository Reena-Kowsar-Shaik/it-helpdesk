"""Application logger configuration and audit helper."""

import logging
import sys
from config import LOG_FILE

# Set up standard logger
logger = logging.getLogger("ITHelpdesk")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers if reloaded
if not logger.handlers:
    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


def log_audit(action: str, user: str, details: str = "", level: str = "INFO"):
    """Helper to log consistent structured audit events."""
    msg = f"[AUDIT] User: '{user}' | Action: '{action}'"
    if details:
        msg += f" | Details: {details}"

    if level.upper() == "WARNING":
        logger.warning(msg)
    elif level.upper() == "ERROR":
        logger.error(msg)
    else:
        logger.info(msg)


def log_error(context: str, error: Exception):
    """Log errors with context and exception message."""
    logger.error(f"[ERROR] Context: {context} | Exception: {type(error).__name__}: {str(error)}")
