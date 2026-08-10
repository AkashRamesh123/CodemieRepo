"""Shared configuration loader for CodemieRepo projects.

Reads values from environment variables so that secrets are never hard-coded
in source files.  Call ``get_env()`` to retrieve a required or optional env
var; a ``ConfigError`` is raised for missing required variables so callers
get a clear, actionable message instead of a KeyError traceback.
"""

from __future__ import annotations

import os


class ConfigError(RuntimeError):
    """Raised when a required environment variable is absent or blank."""


def get_env(name: str, *, required: bool = True, default: str | None = None) -> str:
    """Return the value of environment variable *name*.

    Parameters
    ----------
    name:
        Name of the environment variable to read.
    required:
        When ``True`` (default) and the variable is absent or blank, raise
        :class:`ConfigError`.  When ``False``, return *default* instead.
    default:
        Fallback value used when *required* is ``False`` and the variable is
        not set.  Ignored when *required* is ``True``.

    Returns
    -------
    str
        The variable value (stripped of leading/trailing whitespace).

    Raises
    ------
    ConfigError
        When *required* is ``True`` and the variable is absent or blank.
    """
    value = os.environ.get(name, "").strip()
    if not value:
        if required:
            raise ConfigError(
                f"Missing required environment variable: {name}. "
                f"Set it before running this script (see .env.example)."
            )
        return default or ""
    return value
