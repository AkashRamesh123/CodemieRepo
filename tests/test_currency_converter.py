"""Unit tests for the refactored Currency Converter module."""

import sys
import os

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "projects", "Currency_converter"
    ),
)

from currency_converter_refactored import (
    convert_currency,
    parse_conversion_command,
    CurrencyConverterController,
)


# ---------------------------------------------------------------------------
# parse_conversion_command
# ---------------------------------------------------------------------------

class TestParseConversionCommand:
    def test_valid_command(self):
        result = parse_conversion_command("100 USD EUR")
        assert result == (100.0, "USD", "EUR")

    def test_lowercase_codes_normalised(self):
        result = parse_conversion_command("50 usd gbp")
        assert result == (50.0, "USD", "GBP")

    def test_float_amount(self):
        result = parse_conversion_command("1.5 EUR JPY")
        assert result == (1.5, "EUR", "JPY")

    def test_too_few_parts_returns_none(self):
        assert parse_conversion_command("100 USD") is None

    def test_too_many_parts_returns_none(self):
        assert parse_conversion_command("100 USD EUR GBP") is None

    def test_non_numeric_amount_returns_none(self):
        assert parse_conversion_command("abc USD EUR") is None

    def test_empty_string_returns_none(self):
        assert parse_conversion_command("") is None


# ---------------------------------------------------------------------------
# convert_currency
# ---------------------------------------------------------------------------

class TestConvertCurrency:
    _rates = {"EUR": 1.0, "USD": 1.1, "GBP": 0.85}

    def test_same_currency_returns_same_amount(self):
        result = convert_currency(100.0, "USD", "USD", self._rates)
        assert result == 100.0

    def test_known_conversion(self):
        result = convert_currency(100.0, "EUR", "USD", self._rates)
        assert result == round(100.0 * 1.1 / 1.0, 2)

    def test_unknown_from_code_returns_none(self):
        result = convert_currency(100.0, "XYZ", "USD", self._rates)
        assert result is None

    def test_unknown_to_code_returns_none(self):
        result = convert_currency(100.0, "USD", "XYZ", self._rates)
        assert result is None

    def test_result_rounded_to_2dp(self):
        rates = {"A": 1.0, "B": 3.0}
        result = convert_currency(1.0, "A", "B", rates)
        assert result == 3.0


# ---------------------------------------------------------------------------
# CurrencyConverterController
# ---------------------------------------------------------------------------

class TestCurrencyConverterController:
    def test_stop_sets_running_false(self):
        ctrl = CurrencyConverterController(api_key="fake")
        ctrl._running = True
        ctrl.stop()
        assert ctrl._running is False

    def test_stop_clears_rates(self):
        ctrl = CurrencyConverterController(api_key="fake")
        ctrl._rates = {"USD": 1.0}
        ctrl.stop()
        assert ctrl._rates is None
