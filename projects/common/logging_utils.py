"""Shared logging helpers for CodemieRepo projects.

Usage::

    from projects.common.logging_utils import get_logger

    logger = get_logger(__name__)
    logger.info("Starting %s", "my-script")

The log level is controlled by the ``LOG_LEVEL`` environment variable
(default: ``INFO``).  Valid values are standard Python level names:
``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``.
"""

from __future__ import annotations

import logging
import os

_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def get_logger(name: str, level_env: str = "LOG_LEVEL") -> logging.Logger:
    """Return a named logger configured with a ``StreamHandler``.

    The call is idempotent: if the logger already has handlers attached,
    the existing logger is returned unchanged so that duplicate log lines
    are not produced on repeated imports.

    Parameters
    ----------
    name:
        Logger name – pass ``__name__`` from the calling module.
    level_env:
        Name of the environment variable whose value sets the log level
        (default ``"LOG_LEVEL"``).  Falls back to ``INFO`` if the variable
        is absent or holds an unrecognised level name.

    Returns
    -------
    logging.Logger
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    raw_level = os.environ.get(level_env, "INFO").upper()
    level = getattr(logging, raw_level, logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(fmt=_FORMAT, datefmt=_DATE_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = False

    return logger
