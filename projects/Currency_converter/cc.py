"""Currency converter using the Fixer.io API.

Configuration
-------------
Set the following environment variable before running::

    export CURRENCY_CONVERTER_API_KEY=<your_fixer_api_key>

Usage::

    python -m projects.Currency_converter.cc
"""

from __future__ import annotations

import json
import sys
from pprint import pprint

import requests

from projects.common.config import ConfigError, get_env
from projects.common.exceptions import ExternalAPIError, InvalidResponseError
from projects.common.logging_utils import get_logger

logger = get_logger(__name__)

BASE_URL = "http://data.fixer.io/api/latest"

CURRENCIES = [
    "AED : Emirati Dirham,United Arab Emirates Dirham",
    "AFN : Afghan Afghani,Afghanistan Afghani",
    "ALL : Albanian Lek,Albania Lek",
    "AMD : Armenian Dram,Armenia Dram",
    "ARS : Argentine Peso,Argentina Peso",
    "AUD : Australian Dollar,Australia Dollar",
    "AZN : Azerbaijan Manat",
    "BAM : Bosnian Convertible Mark",
    "BBD : Barbadian Dollar,Barbados Dollar",
    "BDT : Bangladeshi Taka",
    "BGN : Bulgarian Lev",
    "BHD : Bahraini Dinar",
    "BRL : Brazilian Real",
    "CAD : Canadian Dollar",
    "CHF : Swiss Franc",
    "CLP : Chilean Peso",
    "CNY : Chinese Yuan Renminbi",
    "COP : Colombian Peso",
    "CZK : Czech Koruna",
    "DKK : Danish Krone",
    "EGP : Egyptian Pound",
    "EUR : Euro,Euro Member Countries",
    "GBP : British Pound,United Kingdom Pound",
    "HKD : Hong Kong Dollar",
    "HUF : Hungarian Forint",
    "IDR : Indonesian Rupiah",
    "ILS : Israeli Shekel",
    "INR : Indian Rupee",
    "JPY : Japanese Yen",
    "KRW : South Korean Won",
    "KWD : Kuwaiti Dinar",
    "MXN : Mexican Peso",
    "MYR : Malaysian Ringgit",
    "NOK : Norwegian Krone",
    "NZD : New Zealand Dollar",
    "PHP : Philippine Peso",
    "PKR : Pakistani Rupee",
    "PLN : Polish Zloty",
    "RON : Romanian Leu",
    "RUB : Russian Ruble",
    "SAR : Saudi Arabian Riyal",
    "SEK : Swedish Krona",
    "SGD : Singapore Dollar",
    "THB : Thai Baht",
    "TRY : Turkish Lira",
    "TWD : Taiwan New Dollar",
    "UAH : Ukrainian Hryvnia",
    "USD : US Dollar,United States Dollar",
    "VND : Vietnamese Dong",
    "ZAR : South African Rand",
]


def load_exchange_rates(api_key: str) -> dict[str, float]:
    """Fetch the latest exchange rates from the Fixer.io API.

    Parameters
    ----------
    api_key:
        Valid Fixer.io API key (read from env – never hard-coded).

    Returns
    -------
    dict[str, float]
        Mapping of currency code → rate relative to EUR base.

    Raises
    ------
    ExternalAPIError
        On network or HTTP errors.
    InvalidResponseError
        When the response JSON is missing the expected ``rates`` field.
    """
    logger.info("Fetching latest exchange rates from Fixer.io")
    try:
        response = requests.get(
            BASE_URL,
            params={"access_key": api_key},
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Request to Fixer.io timed out")
        raise ExternalAPIError("Fixer.io request timed out") from None
    except requests.exceptions.ConnectionError as exc:
        logger.error("Network error contacting Fixer.io: %s", exc)
        raise ExternalAPIError("Could not connect to Fixer.io") from exc
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error from Fixer.io: %s", exc)
        raise ExternalAPIError(f"Fixer.io returned HTTP {response.status_code}") from exc

    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Invalid JSON received from Fixer.io")
        raise InvalidResponseError("Fixer.io returned non-JSON response") from exc

    if "rates" not in data:
        logger.error("Fixer.io response is missing 'rates' field: %s", list(data.keys()))
        raise InvalidResponseError("Fixer.io response missing 'rates' field")

    logger.info("Exchange rates loaded successfully (%d currencies)", len(data["rates"]))
    return data["rates"]


def parse_conversion_command(query: str) -> tuple[float, str, str]:
    """Parse a conversion query string into (amount, from_currency, to_currency).

    Expected format: ``<amount> <FROM> <TO>``  e.g. ``100 USD EUR``

    Raises
    ------
    ValueError
        When the query does not match the expected format.
    """
    parts = query.strip().split()
    if len(parts) != 3:
        raise ValueError(f"Expected '<amount> <FROM> <TO>', got: {query!r}")
    qty_str, from_c, to_c = parts
    try:
        qty = float(qty_str)
    except ValueError:
        raise ValueError(f"Amount must be a number, got: {qty_str!r}") from None
    return qty, from_c.upper(), to_c.upper()


def convert_currency(qty: float, from_c: str, to_c: str, rates: dict[str, float]) -> float:
    """Compute the converted amount using *rates*.

    Parameters
    ----------
    qty:
        Source amount.
    from_c, to_c:
        ISO 4217 currency codes.
    rates:
        Exchange rate dict keyed by currency code (EUR-based).

    Returns
    -------
    float
        Converted amount rounded to 2 decimal places.

    Raises
    ------
    InvalidResponseError
        When either currency code is absent from *rates*.
    """
    if from_c not in rates:
        raise InvalidResponseError(f"Currency not found in rate table: {from_c}")
    if to_c not in rates:
        raise InvalidResponseError(f"Currency not found in rate table: {to_c}")
    return round(qty * rates[to_c] / rates[from_c], 2)


def run(rates: dict[str, float]) -> None:
    """Interactive conversion loop."""
    while True:
        query = input(
            "\nSpecify: <amount> <FROM> <TO>  (e.g. 100 USD EUR)\n"
            "Type SHOW to list currencies, Q to quit.\n> "
        ).strip()

        if query.upper() == "Q":
            logger.info("User requested quit")
            break

        if query.upper() == "SHOW":
            pprint(CURRENCIES)
            continue

        try:
            qty, from_c, to_c = parse_conversion_command(query)
        except ValueError as exc:
            logger.warning("Bad input: %s", exc)
            continue

        try:
            amount = convert_currency(qty, from_c, to_c, rates)
        except InvalidResponseError as exc:
            logger.error("Conversion failed: %s", exc)
            continue

        logger.info("%s %s = %s %s", qty, from_c, amount, to_c)
        print(f"{qty} {from_c} = {amount} {to_c}")


def main() -> int:
    """Entry point; returns 0 on success, 1 on configuration or API error."""
    try:
        api_key = get_env("CURRENCY_CONVERTER_API_KEY")
    except ConfigError as exc:
        logger.error("%s", exc)
        return 1

    try:
        rates = load_exchange_rates(api_key)
    except (ExternalAPIError, InvalidResponseError) as exc:
        logger.error("Failed to load exchange rates: %s", exc)
        return 1

    run(rates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
