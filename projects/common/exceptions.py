"""Shared exception types for CodemieRepo projects."""

from __future__ import annotations


class ExternalAPIError(RuntimeError):
    """Raised when an external API call fails (network error, bad status)."""


class InvalidResponseError(RuntimeError):
    """Raised when an API response has an unexpected or missing field."""
