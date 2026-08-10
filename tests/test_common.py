"""Unit tests for the projects/common shared infrastructure."""

from __future__ import annotations

import logging
import os

import pytest

from projects.common.config import ConfigError, get_env
from projects.common.exceptions import ExternalAPIError, InvalidResponseError
from projects.common.logging_utils import get_logger


# ---------------------------------------------------------------------------
# config.get_env
# ---------------------------------------------------------------------------


class TestGetEnv:
    def test_returns_set_variable(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "hello")
        assert get_env("TEST_KEY") == "hello"

    def test_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "  value  ")
        assert get_env("TEST_KEY") == "value"

    def test_raises_config_error_when_required_and_missing(self, monkeypatch):
        monkeypatch.delenv("TEST_KEY", raising=False)
        with pytest.raises(ConfigError, match="TEST_KEY"):
            get_env("TEST_KEY")

    def test_raises_config_error_when_required_and_blank(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "   ")
        with pytest.raises(ConfigError, match="TEST_KEY"):
            get_env("TEST_KEY")

    def test_returns_default_when_not_required_and_missing(self, monkeypatch):
        monkeypatch.delenv("TEST_KEY", raising=False)
        assert get_env("TEST_KEY", required=False, default="fallback") == "fallback"

    def test_returns_empty_string_when_not_required_no_default(self, monkeypatch):
        monkeypatch.delenv("TEST_KEY", raising=False)
        assert get_env("TEST_KEY", required=False) == ""


# ---------------------------------------------------------------------------
# logging_utils.get_logger
# ---------------------------------------------------------------------------


class TestGetLogger:
    def test_returns_logger_instance(self):
        logger = get_logger("test.common.logger_a")
        assert isinstance(logger, logging.Logger)

    def test_idempotent_no_duplicate_handlers(self):
        name = "test.common.logger_idempotent"
        logger1 = get_logger(name)
        initial_count = len(logger1.handlers)
        logger2 = get_logger(name)
        assert len(logger2.handlers) == initial_count

    def test_respects_log_level_env(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        logger = get_logger("test.common.logger_debug", level_env="LOG_LEVEL")
        assert logger.level == logging.DEBUG

    def test_defaults_to_info_on_unknown_level(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "NOTAREALEVEL")
        logger = get_logger("test.common.logger_unknown", level_env="LOG_LEVEL")
        assert logger.level == logging.INFO

    def test_propagate_is_false(self):
        logger = get_logger("test.common.logger_propagate")
        assert logger.propagate is False


# ---------------------------------------------------------------------------
# exception types
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    def test_external_api_error_is_runtime_error(self):
        exc = ExternalAPIError("boom")
        assert isinstance(exc, RuntimeError)
        assert "boom" in str(exc)

    def test_invalid_response_error_is_runtime_error(self):
        exc = InvalidResponseError("bad schema")
        assert isinstance(exc, RuntimeError)
        assert "bad schema" in str(exc)

    def test_config_error_is_runtime_error(self):
        exc = ConfigError("missing key")
        assert isinstance(exc, RuntimeError)
        assert "missing key" in str(exc)
