"""
Reusable error-handling helpers for CodemieRepo projects.

All helpers log the error at the appropriate level and return ``None`` so
callers can decide how to proceed (continue with a default, retry, or exit).

Usage
-----
    from src.utils.error_handlers import handle_file_error, handle_network_error

    data = handle_file_error(load_file, "data.csv")
    if data is None:
        # file could not be loaded – take a safe fallback path
        ...
"""

import logging
from typing import Any, Callable, Optional, Type

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def handle_file_error(
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Optional[Any]:
    """Call *func* and handle common file-I/O exceptions.

    Catches :exc:`FileNotFoundError`, :exc:`PermissionError`,
    :exc:`IsADirectoryError`, and any unexpected :exc:`Exception`, logging
    each at the appropriate level.

    Parameters
    ----------
    func:
        A callable that performs file I/O (e.g. ``open``, a custom reader).
    *args:
        Positional arguments forwarded to *func*.
    **kwargs:
        Keyword arguments forwarded to *func*.

    Returns
    -------
    The return value of *func* on success, or ``None`` on failure.
    """
    try:
        return func(*args, **kwargs)
    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
    except PermissionError as exc:
        logger.error("Permission denied accessing file: %s", exc)
    except IsADirectoryError as exc:
        logger.error("Expected a file but got a directory: %s", exc)
    except OSError as exc:
        logger.error("OS error while accessing file: %s", exc)
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error during file operation")
    return None


def handle_network_error(
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Optional[Any]:
    """Call *func* and handle common network / HTTP exceptions.

    Requires the ``requests`` library to be installed; if it is absent the
    function still works but will not catch ``requests``-specific exceptions.

    Parameters
    ----------
    func:
        A callable that performs a network operation (e.g. ``requests.get``).
    *args:
        Positional arguments forwarded to *func*.
    **kwargs:
        Keyword arguments forwarded to *func*.

    Returns
    -------
    The return value of *func* on success, or ``None`` on failure.
    """
    try:
        return func(*args, **kwargs)
    except ConnectionError as exc:
        logger.error("Network connection error: %s", exc)
    except TimeoutError as exc:
        logger.error("Network request timed out: %s", exc)
    except ValueError as exc:
        logger.error("Invalid value during network operation: %s", exc)
    except Exception:  # noqa: BLE001
        # Catches requests.exceptions.RequestException and everything else.
        logger.exception("Unexpected error during network operation")
    return None


def handle_unexpected_error(
    func: Callable[..., Any],
    *args: Any,
    exc_types: tuple[Type[Exception], ...] = (Exception,),
    default: Any = None,
    **kwargs: Any,
) -> Optional[Any]:
    """Generic error wrapper – catch *exc_types* and log a stack trace.

    Parameters
    ----------
    func:
        A callable to execute safely.
    *args:
        Positional arguments forwarded to *func*.
    exc_types:
        A tuple of exception classes to catch.  Defaults to ``(Exception,)``.
    default:
        Value returned on failure.  Defaults to ``None``.
    **kwargs:
        Keyword arguments forwarded to *func*.

    Returns
    -------
    The return value of *func* on success, or *default* on failure.
    """
    try:
        return func(*args, **kwargs)
    except exc_types:  # type: ignore[misc]
        logger.exception(
            "Unexpected error calling %s",
            getattr(func, "__qualname__", repr(func)),
        )
        return default
