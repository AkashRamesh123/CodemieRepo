"""Fetch current weather for a given city using the OpenWeatherMap API.

Configuration
-------------
Set the following environment variable before running::

    export OPENWEATHER_API_KEY=<your_openweathermap_api_key>

Usage::

    python -m projects.Fetch_current_weather.fetch_current_weather
"""

from __future__ import annotations

import json

import requests

from projects.common.config import ConfigError, get_env
from projects.common.exceptions import ExternalAPIError, InvalidResponseError
from projects.common.logging_utils import get_logger

logger = get_logger(__name__)

BASE_URL = "http://api.openweathermap.org/data/2.5/weather"


def fetch_weather_data(city_name: str, api_key: str) -> dict:
    """Fetch raw weather JSON for *city_name* from OpenWeatherMap.

    Parameters
    ----------
    city_name:
        Name of the city to look up.
    api_key:
        Valid OpenWeatherMap API key (read from env – never hard-coded).

    Returns
    -------
    dict
        Parsed JSON response from the API.

    Raises
    ------
    ExternalAPIError
        On network or HTTP errors.
    InvalidResponseError
        When the response JSON is missing expected fields.
    """
    logger.info("Fetching weather data for city: %s", city_name)
    try:
        response = requests.get(
            BASE_URL,
            params={"appid": api_key, "q": city_name},
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Request to OpenWeatherMap timed out")
        raise ExternalAPIError("OpenWeatherMap request timed out") from None
    except requests.exceptions.ConnectionError as exc:
        logger.error("Network error contacting OpenWeatherMap: %s", exc)
        raise ExternalAPIError("Could not connect to OpenWeatherMap") from exc
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error from OpenWeatherMap: %s", exc)
        raise ExternalAPIError(
            f"OpenWeatherMap returned HTTP {response.status_code}"
        ) from exc

    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Invalid JSON received from OpenWeatherMap")
        raise InvalidResponseError("OpenWeatherMap returned non-JSON response") from exc

    if data.get("cod") == "404":
        logger.warning("City not found: %s", city_name)
        raise InvalidResponseError(f"City not found: {city_name!r}")

    return data


def parse_weather(data: dict) -> dict[str, str | float]:
    """Extract key weather fields from the raw API response.

    Parameters
    ----------
    data:
        Parsed JSON dict returned by :func:`fetch_weather_data`.

    Returns
    -------
    dict
        Dict with keys ``temperature``, ``pressure``, ``humidity``,
        ``description``.

    Raises
    ------
    InvalidResponseError
        When expected fields are absent from *data*.
    """
    try:
        main = data["main"]
        weather_list = data["weather"]
        return {
            "temperature": main["temp"],
            "pressure": main["pressure"],
            "humidity": main["humidity"],
            "description": weather_list[0]["description"],
        }
    except (KeyError, IndexError) as exc:
        logger.error("Unexpected response schema from OpenWeatherMap: %s", exc)
        raise InvalidResponseError(
            f"OpenWeatherMap response missing expected field: {exc}"
        ) from exc


def format_weather_report(city: str, weather: dict[str, str | float]) -> str:
    """Return a human-readable weather report string."""
    return (
        f"Weather in {city}:\n"
        f"  Temperature : {weather['temperature']} K\n"
        f"  Pressure    : {weather['pressure']} hPa\n"
        f"  Humidity    : {weather['humidity']} %\n"
        f"  Description : {weather['description']}"
    )


def main() -> int:
    """Entry point; returns 0 on success, 1 on configuration or API error."""
    try:
        api_key = get_env("OPENWEATHER_API_KEY")
    except ConfigError as exc:
        logger.error("%s", exc)
        return 1

    city_name = input("Enter city name: ").strip()
    if not city_name:
        logger.error("City name must not be blank")
        return 1

    try:
        data = fetch_weather_data(city_name, api_key)
        weather = parse_weather(data)
    except (ExternalAPIError, InvalidResponseError) as exc:
        logger.error("Failed to fetch weather: %s", exc)
        return 1

    report = format_weather_report(city_name, weather)
    logger.info("Weather data retrieved successfully for %s", city_name)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
