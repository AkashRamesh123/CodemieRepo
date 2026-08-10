"""Unit tests for the refactored Currency Converter."""

from __future__ import annotations

import pytest
import requests

from projects.common.config import ConfigError
from projects.common.exceptions import ExternalAPIError, InvalidResponseError
from projects.Currency_converter.cc import (
    convert_currency,
    load_exchange_rates,
    parse_conversion_command,
)


# ---------------------------------------------------------------------------
# parse_conversion_command
# ---------------------------------------------------------------------------


class TestParseConversionCommand:
    def test_valid_query(self):
        qty, from_c, to_c = parse_conversion_command("100 USD EUR")
        assert qty == 100.0
        assert from_c == "USD"
        assert to_c == "EUR"

    def test_lowercase_codes_are_uppercased(self):
        qty, from_c, to_c = parse_conversion_command("50 usd eur")
        assert from_c == "USD"
        assert to_c == "EUR"

    def test_float_amount(self):
        qty, _, _ = parse_conversion_command("9.99 GBP JPY")
        assert qty == pytest.approx(9.99)

    def test_missing_to_currency_raises(self):
        with pytest.raises(ValueError):
            parse_conversion_command("100 USD")

    def test_non_numeric_amount_raises(self):
        with pytest.raises(ValueError, match="number"):
            parse_conversion_command("abc USD EUR")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_conversion_command("")


# ---------------------------------------------------------------------------
# convert_currency
# ---------------------------------------------------------------------------


RATES = {"EUR": 1.0, "USD": 1.1, "GBP": 0.85, "JPY": 160.0}


class TestConvertCurrency:
    def test_eur_to_usd(self):
        result = convert_currency(100.0, "EUR", "USD", RATES)
        assert result == pytest.approx(110.0)

    def test_usd_to_eur(self):
        result = convert_currency(110.0, "USD", "EUR", RATES)
        assert result == pytest.approx(100.0)

    def test_same_currency_returns_same_amount(self):
        result = convert_currency(42.0, "USD", "USD", RATES)
        assert result == pytest.approx(42.0)

    def test_unknown_from_currency_raises(self):
        with pytest.raises(InvalidResponseError, match="XYZ"):
            convert_currency(100.0, "XYZ", "USD", RATES)

    def test_unknown_to_currency_raises(self):
        with pytest.raises(InvalidResponseError, match="XYZ"):
            convert_currency(100.0, "USD", "XYZ", RATES)

    def test_result_rounded_to_two_places(self):
        result = convert_currency(1.0, "USD", "JPY", RATES)
        assert result == round(1.0 * RATES["JPY"] / RATES["USD"], 2)


# ---------------------------------------------------------------------------
# load_exchange_rates (mocked network)
# ---------------------------------------------------------------------------


class TestLoadExchangeRates:
    def test_returns_rates_on_success(self, requests_mock):
        requests_mock.get(
            "http://data.fixer.io/api/latest",
            json={"success": True, "rates": {"USD": 1.1, "GBP": 0.85}},
        )
        rates = load_exchange_rates("dummy_key")
        assert rates["USD"] == pytest.approx(1.1)

    def test_raises_on_missing_rates_field(self, requests_mock):
        requests_mock.get(
            "http://data.fixer.io/api/latest",
            json={"success": False, "error": {}},
        )
        with pytest.raises(InvalidResponseError, match="rates"):
            load_exchange_rates("dummy_key")

    def test_raises_on_timeout(self, requests_mock):
        requests_mock.get(
            "http://data.fixer.io/api/latest",
            exc=requests.exceptions.Timeout,
        )
        with pytest.raises(ExternalAPIError, match="timed out"):
            load_exchange_rates("dummy_key")

    def test_raises_on_connection_error(self, requests_mock):
        requests_mock.get(
            "http://data.fixer.io/api/latest",
            exc=requests.exceptions.ConnectionError,
        )
        with pytest.raises(ExternalAPIError, match="connect"):
            load_exchange_rates("dummy_key")
