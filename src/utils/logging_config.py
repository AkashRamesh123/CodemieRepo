"""
Centralised logging configuration for CodemieRepo projects.

Usage
-----
    from src.utils.logging_config import get_logger, configure_logging

    # (Optional) call once at application startup to customise the root logger:
    configure_logging(level="DEBUG", log_file="app.log")

    # Then in every module:
    logger = get_logger(__name__)
    logger.info("Application started")
"""

import logging
import logging.handlers
import sys
from typing import Optional


_FORMATTER_PATTERN = (
    "%(asctime)s  %(levelname)-8s  %(name)s:%(lineno)d  %(message)s"
)


def configure_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """Configure the root logger with console (and optional file) handlers.

    Parameters
    ----------
    level:
        Minimum log level to emit.  One of ``"DEBUG"``, ``"INFO"``,
        ``"WARNING"``, ``"ERROR"``, ``"CRITICAL"``.  Defaults to ``"INFO"``.
    log_file:
        Optional path to a rotating log file.  When *None* only the console
        (stderr) handler is attached.
    max_bytes:
        Maximum size of each log-file segment before rotation.  Ignored when
        *log_file* is ``None``.  Defaults to 5 MB.
    backup_count:
        Number of rotated log-file segments to keep.  Ignored when *log_file*
        is ``None``.  Defaults to 3.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(_FORMATTER_PATTERN)

    # Console handler – always present.
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [console_handler]

    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(level=numeric_level, handlers=handlers, force=True)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger.

    If ``configure_logging`` has not been called yet, a minimal default
    configuration (INFO level, stderr) is applied so that the first log call
    does not silently drop messages.

    Parameters
    ----------
    name:
        Typically ``__name__`` of the calling module.

    Returns
    -------
    logging.Logger
    """
    logger = logging.getLogger(name)

    # Ensure at least a NullHandler is present so libraries stay silent by
    # default, while still returning a fully-usable logger instance.
    if not logging.root.handlers:
        configure_logging()

    return logger
