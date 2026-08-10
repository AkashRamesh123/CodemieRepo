"""Unit tests for the refactored Weather Fetcher."""

from __future__ import annotations

import pytest
import requests

from projects.common.exceptions import ExternalAPIError, InvalidResponseError
from projects.Fetch_current_weather.fetch_current_weather import (
    fetch_weather_data,
    format_weather_report,
    parse_weather,
)

SAMPLE_RESPONSE = {
    "cod": 200,
    "main": {"temp": 295.15, "pressure": 1012, "humidity": 60},
    "weather": [{"description": "clear sky", "icon": "01d"}],
    "name": "London",
}


# ---------------------------------------------------------------------------
# parse_weather
# ---------------------------------------------------------------------------


class TestParseWeather:
    def test_extracts_all_fields(self):
        result = parse_weather(SAMPLE_RESPONSE)
        assert result["temperature"] == pytest.approx(295.15)
        assert result["pressure"] == 1012
        assert result["humidity"] == 60
        assert result["description"] == "clear sky"

    def test_missing_main_raises(self):
        with pytest.raises(InvalidResponseError):
            parse_weather({"weather": [{"description": "x"}]})

    def test_missing_weather_list_raises(self):
        with pytest.raises(InvalidResponseError):
            parse_weather({"main": {"temp": 300, "pressure": 1000, "humidity": 50}})

    def test_empty_weather_list_raises(self):
        data = dict(SAMPLE_RESPONSE)
        data["weather"] = []
        with pytest.raises(InvalidResponseError):
            parse_weather(data)


# ---------------------------------------------------------------------------
# format_weather_report
# ---------------------------------------------------------------------------


class TestFormatWeatherReport:
    def test_contains_city_name(self):
        weather = parse_weather(SAMPLE_RESPONSE)
        report = format_weather_report("London", weather)
        assert "London" in report

    def test_contains_temperature(self):
        weather = parse_weather(SAMPLE_RESPONSE)
        report = format_weather_report("London", weather)
        assert "295.15" in report

    def test_contains_description(self):
        weather = parse_weather(SAMPLE_RESPONSE)
        report = format_weather_report("London", weather)
        assert "clear sky" in report


# ---------------------------------------------------------------------------
# fetch_weather_data (mocked network)
# ---------------------------------------------------------------------------


class TestFetchWeatherData:
    def test_returns_data_on_success(self, requests_mock):
        requests_mock.get(
            "http://api.openweathermap.org/data/2.5/weather",
            json=SAMPLE_RESPONSE,
        )
        data = fetch_weather_data("London", "dummy_key")
        assert data["name"] == "London"

    def test_raises_on_city_not_found(self, requests_mock):
        requests_mock.get(
            "http://api.openweathermap.org/data/2.5/weather",
            json={"cod": "404", "message": "city not found"},
        )
        with pytest.raises(InvalidResponseError, match="not found"):
            fetch_weather_data("Atlantis", "dummy_key")

    def test_raises_on_timeout(self, requests_mock):
        requests_mock.get(
            "http://api.openweathermap.org/data/2.5/weather",
            exc=requests.exceptions.Timeout,
        )
        with pytest.raises(ExternalAPIError, match="timed out"):
            fetch_weather_data("London", "dummy_key")

    def test_raises_on_connection_error(self, requests_mock):
        requests_mock.get(
            "http://api.openweathermap.org/data/2.5/weather",
            exc=requests.exceptions.ConnectionError,
        )
        with pytest.raises(ExternalAPIError, match="connect"):
            fetch_weather_data("London", "dummy_key")

    def test_raises_on_http_error(self, requests_mock):
        requests_mock.get(
            "http://api.openweathermap.org/data/2.5/weather",
            status_code=401,
        )
        with pytest.raises(ExternalAPIError):
            fetch_weather_data("London", "dummy_key")
