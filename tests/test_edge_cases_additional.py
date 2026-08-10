"""Additional edge-case unit tests for refactored projects.

These tests complement the existing baseline tests by covering schema drift,
invalid JSON, HTTP error pathways, and boundary inputs.
"""

from __future__ import annotations

import pytest
import requests

from projects.common.exceptions import ExternalAPIError, InvalidResponseError
from projects.Currency_converter import cc
from projects.Fetch_current_weather import fetch_current_weather as weather


# ---------------------------------------------------------------------------
# Currency Converter edge cases
# ---------------------------------------------------------------------------


class TestParseConversionCommandEdgeCases:
    @pytest.mark.parametrize(
        "query",
        [
            "  100   usd   eur  ",  # extra whitespace
            "\n100 USD EUR\t",  # newlines/tabs
        ],
    )
    def test_whitespace_is_handled(self, query: str):
        qty, from_c, to_c = cc.parse_conversion_command(query)
        assert qty == pytest.approx(100.0)
        assert from_c == "USD"
        assert to_c == "EUR"

    def test_rejects_too_many_parts(self):
        with pytest.raises(ValueError, match="Expected"):
            cc.parse_conversion_command("100 USD EUR NOW")


class TestConvertCurrencyEdgeCases:
    def test_negative_amount_is_allowed_and_converted(self):
        rates = {"EUR": 1.0, "USD": 2.0}
        result = cc.convert_currency(-10.0, "EUR", "USD", rates)
        assert result == pytest.approx(-20.0)

    def test_zero_rate_raises_zero_division_error(self):
        # This is an edge case: a zero 'from' rate is invalid and should not
        # silently pass. The current implementation will raise ZeroDivisionError.
        rates = {"EUR": 0.0, "USD": 1.0}
        with pytest.raises(ZeroDivisionError):
            cc.convert_currency(10.0, "EUR", "USD", rates)


class TestLoadExchangeRatesEdgeCases:
    def test_raises_on_http_error(self, requests_mock):
        requests_mock.get(cc.BASE_URL, status_code=401)
        with pytest.raises(ExternalAPIError, match="HTTP 401"):
            cc.load_exchange_rates("dummy_key")

    def test_raises_on_invalid_json(self, requests_mock):
        requests_mock.get(cc.BASE_URL, text="not-json")
        with pytest.raises(InvalidResponseError, match="non-JSON"):
            cc.load_exchange_rates("dummy_key")


# ---------------------------------------------------------------------------
# Weather Fetcher edge cases
# ---------------------------------------------------------------------------


class TestFetchWeatherDataEdgeCases:
    def test_city_not_found_when_cod_is_int_404_is_not_misdetected(self, requests_mock):
        # The implementation checks for string "404"; ensure integer 404 is not
        # treated as the special-case 'not found' branch in fetch_weather_data.
        requests_mock.get(
            weather.BASE_URL,
            json={"cod": 404, "message": "city not found"},
        )
        data = weather.fetch_weather_data("Atlantis", "dummy_key")
        assert data["cod"] == 404

    def test_raises_on_invalid_json(self, requests_mock):
        requests_mock.get(weather.BASE_URL, text="<html>nope</html>")
        with pytest.raises(InvalidResponseError, match="non-JSON"):
            weather.fetch_weather_data("London", "dummy_key")


class TestParseWeatherEdgeCases:
    def test_missing_description_field_raises(self):
        bad = {
            "main": {"temp": 300, "pressure": 1000, "humidity": 50},
            "weather": [{}],
        }
        with pytest.raises(InvalidResponseError, match="description"):
            weather.parse_weather(bad)


class TestFormatWeatherReportEdgeCases:
    def test_report_includes_units_and_labels(self):
        report = weather.format_weather_report(
            "Paris",
            {
                "temperature": 280.0,
                "pressure": 1005,
                "humidity": 80,
                "description": "mist",
            },
        )
        assert "Weather in Paris" in report
        assert "Temperature" in report and " K" in report
        assert "Pressure" in report and " hPa" in report
        assert "Humidity" in report and " %" in report
        assert "Description" in report and "mist" in report
