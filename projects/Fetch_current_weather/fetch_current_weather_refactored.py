"""
Fetch Current Weather – refactored (modular + logging + error handling).

Improvements over the original ``fetch_current_weather.py``
------------------------------------------------------------
* Hardcoded values (``api_key``, ``base_url``) moved to named constants and
  read from environment variables so secrets are never committed to source.
* Network call wrapped in ``fetch_weather_data`` with structured error
  handling (``requests`` exceptions, HTTP error codes, JSON parsing).
* Presentation logic extracted into ``format_weather_report``.
* ``WeatherController`` class orchestrates the flow.
* All print-based diagnostics replaced by ``logging``.
* ``main()`` entry-point sets up logging and runs the controller.
"""

import logging
import os
import sys
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration – read from environment variables with safe defaults.
# ---------------------------------------------------------------------------

API_KEY: str = os.environ.get("OPENWEATHER_API_KEY", "")
BASE_URL: str = os.environ.get(
    "OPENWEATHER_BASE_URL",
    "https://api.openweathermap.org/data/2.5/weather",
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def fetch_weather_data(city_name: str, api_key: str) -> Optional[dict[str, Any]]:
    """Retrieve raw weather data from the OpenWeatherMap API.

    Parameters
    ----------
    city_name:
        Name of the city to look up.
    api_key:
        OpenWeatherMap API key.

    Returns
    -------
    A dictionary containing the JSON response on success, or ``None`` on any
    error (connection failure, HTTP error, invalid JSON).
    """
    if not api_key:
        logger.error(
            "API key is not set. "
            "Set the OPENWEATHER_API_KEY environment variable."
        )
        return None

    params = {"q": city_name, "appid": api_key}
    logger.debug("Requesting weather for city=%r, url=%s", city_name, BASE_URL)

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        logger.info("Successfully fetched weather data for %r.", city_name)
        return data
    except requests.exceptions.ConnectionError as exc:
        logger.error("Connection error while fetching weather: %s", exc)
    except requests.exceptions.Timeout:
        logger.error("Request timed out fetching weather for %r.", city_name)
    except requests.exceptions.HTTPError as exc:
        logger.error(
            "HTTP error %d for city %r: %s",
            exc.response.status_code,
            city_name,
            exc,
        )
    except requests.exceptions.JSONDecodeError:
        logger.error("Failed to decode JSON response from weather API.")
    except requests.exceptions.RequestException:
        logger.exception("Unexpected error fetching weather data.")
    return None


def parse_weather(data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract the relevant fields from the raw API response.

    Parameters
    ----------
    data:
        Raw dictionary returned by :func:`fetch_weather_data`.

    Returns
    -------
    A simplified dictionary with keys ``temperature``, ``pressure``,
    ``humidity``, and ``description``, or ``None`` if *data* is missing
    expected fields.
    """
    try:
        main = data["main"]
        weather = data["weather"][0]
        return {
            "temperature": main["temp"],
            "pressure": main["pressure"],
            "humidity": main["humidity"],
            "description": weather["description"],
        }
    except (KeyError, IndexError) as exc:
        logger.error("Unexpected weather API response structure: %s", exc)
        return None


def format_weather_report(city: str, weather: dict[str, Any]) -> str:
    """Format parsed weather data into a human-readable report.

    Parameters
    ----------
    city:
        Name of the city.
    weather:
        Parsed weather dictionary from :func:`parse_weather`.

    Returns
    -------
    A multi-line formatted string.
    """
    return (
        f"Weather in {city}\n"
        f"  Temperature  : {weather['temperature']:.2f} K\n"
        f"  Pressure     : {weather['pressure']} hPa\n"
        f"  Humidity     : {weather['humidity']} %\n"
        f"  Description  : {weather['description']}"
    )


# ---------------------------------------------------------------------------
# Controller class
# ---------------------------------------------------------------------------


class WeatherController:
    """Orchestrate the weather lookup flow.

    Parameters
    ----------
    api_key:
        OpenWeatherMap API key.  Defaults to :data:`API_KEY` (read from env).
    """

    def __init__(self, api_key: str = API_KEY) -> None:
        self._api_key = api_key

    def run(self) -> None:
        """Prompt for a city name, fetch weather, and print the report."""
        city = input("Enter city name: ").strip()
        if not city:
            logger.warning("Empty city name entered.")
            print("City name cannot be empty.")
            return

        logger.info("Looking up weather for city=%r", city)
        raw_data = fetch_weather_data(city, self._api_key)

        if raw_data is None:
            print(f"Could not retrieve weather data for '{city}'.")
            return

        weather = parse_weather(raw_data)
        if weather is None:
            print("Weather data is in an unexpected format.")
            return

        report = format_weather_report(city, weather)
        print(report)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Configure logging and run the weather controller."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        stream=sys.stderr,
    )
    if not API_KEY:
        logger.warning(
            "OPENWEATHER_API_KEY is not set – requests will fail. "
            "Export the variable before running."
        )

    logger.info("Weather application starting.")
    controller = WeatherController()
    controller.run()


if __name__ == "__main__":
    main()
