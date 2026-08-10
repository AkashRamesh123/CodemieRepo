"""Unit tests for the shared src/utils module."""

import logging
import sys
import os

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "src"),
)

from utils.logging_config import configure_logging, get_logger
from utils.error_handlers import (
    handle_file_error,
    handle_network_error,
    handle_unexpected_error,
)


# ---------------------------------------------------------------------------
# logging_config
# ---------------------------------------------------------------------------

class TestConfigureLogging:
    def test_returns_none(self):
        result = configure_logging(level="WARNING")
        assert result is None

    def test_root_handler_present_after_configure(self):
        configure_logging(level="DEBUG")
        assert len(logging.root.handlers) > 0


class TestGetLogger:
    def test_returns_logger_instance(self):
        lg = get_logger("test.module")
        assert isinstance(lg, logging.Logger)

    def test_logger_name_preserved(self):
        lg = get_logger("my.custom.name")
        assert lg.name == "my.custom.name"


# ---------------------------------------------------------------------------
# error_handlers
# ---------------------------------------------------------------------------

class TestHandleFileError:
    def test_success_returns_value(self):
        result = handle_file_error(lambda: 42)
        assert result == 42

    def test_file_not_found_returns_none(self):
        def raise_fnf():
            raise FileNotFoundError("no such file")
        result = handle_file_error(raise_fnf)
        assert result is None

    def test_permission_error_returns_none(self):
        def raise_perm():
            raise PermissionError("denied")
        result = handle_file_error(raise_perm)
        assert result is None

    def test_unexpected_exception_returns_none(self):
        def raise_unexpected():
            raise RuntimeError("unexpected")
        result = handle_file_error(raise_unexpected)
        assert result is None

    def test_args_forwarded_to_func(self):
        result = handle_file_error(lambda x, y: x + y, 3, 4)
        assert result == 7


class TestHandleNetworkError:
    def test_success_returns_value(self):
        result = handle_network_error(lambda: "data")
        assert result == "data"

    def test_connection_error_returns_none(self):
        def raise_conn():
            raise ConnectionError("refused")
        result = handle_network_error(raise_conn)
        assert result is None

    def test_timeout_returns_none(self):
        def raise_timeout():
            raise TimeoutError("timed out")
        result = handle_network_error(raise_timeout)
        assert result is None

    def test_unexpected_exception_returns_none(self):
        def raise_unexpected():
            raise ValueError("bad value")
        result = handle_network_error(raise_unexpected)
        assert result is None


class TestHandleUnexpectedError:
    def test_success_returns_value(self):
        result = handle_unexpected_error(lambda: "ok")
        assert result == "ok"

    def test_exception_returns_default_none(self):
        def raises():
            raise Exception("boom")
        result = handle_unexpected_error(raises)
        assert result is None

    def test_exception_returns_custom_default(self):
        def raises():
            raise Exception("boom")
        result = handle_unexpected_error(raises, default="fallback")
        assert result == "fallback"

    def test_non_matching_exc_type_propagates(self):
        def raises():
            raise ValueError("unexpected")
        import pytest
        with pytest.raises(ValueError):
            handle_unexpected_error(raises, exc_types=(TypeError,))
