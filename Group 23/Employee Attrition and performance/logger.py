# ============================================================
# logger.py
#
# Structured logging configuration.
# Replaces all print() statements throughout the codebase.
#
# Usage:
#   from logger import get_logger
#   logger = get_logger(__name__)
#   logger.info("Model loaded successfully")
#   logger.error("Prediction failed: %s", error)
# ============================================================

import logging
import logging.handlers
import sys
from pathlib import Path


# ============================================================
# LOG DIRECTORY
# ============================================================

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


# ============================================================
# FORMATTERS
# ============================================================

CONSOLE_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

FILE_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)


# ============================================================
# SETUP ROOT LOGGER (called once at import time)
# ============================================================

def _setup_root_logger(level: str = "INFO") -> None:
    """
    Configure the root logger with a console handler and a
    rotating file handler.  Called once when this module is
    first imported.
    """

    root = logging.getLogger()

    if root.handlers:
        # Already configured — avoid duplicate handlers
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(numeric_level)

    # ----------------------------------------------------------
    # Console handler — INFO and above, colourised level label
    # ----------------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(
        logging.Formatter(CONSOLE_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    )
    root.addHandler(console_handler)

    # ----------------------------------------------------------
    # Rotating file handler — keeps last 5 × 5 MB log files
    # ----------------------------------------------------------
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(FILE_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    )
    root.addHandler(file_handler)


# ============================================================
# PUBLIC API
# ============================================================

def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A configured :class:`logging.Logger` instance.

    Example::

        from logger import get_logger
        logger = get_logger(__name__)
        logger.info("Server starting on port %d", 5000)
    """
    return logging.getLogger(name)


# ============================================================
# INITIALISE ON IMPORT
# ============================================================

# Import LOG_LEVEL from config if available; fall back to INFO
try:
    from config import LOG_LEVEL as _configured_level
except ImportError:
    _configured_level = "INFO"

_setup_root_logger(_configured_level)
