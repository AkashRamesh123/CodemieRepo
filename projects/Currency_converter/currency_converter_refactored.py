"""Currency Converter - refactored (modular + logging + error handling).

Key improvements over the original cc.py:
- Renamed function1() to descriptive parse_conversion_command() and
  convert_currency() functions.
- API key read from FIXER_API_KEY environment variable.
- Network call wrapped with structured exception handling.
- CurrencyConverterController class with start/run/stop/handle_command.
- All print()-based diagnostics replaced by logging.
- main() entry-point configures logging and starts the controller.
"""

import logging
import os
import sys
from typing import Optional

import requests

logger = logging.getLogger(__name__)

API_KEY: str = os.environ.get("FIXER_API_KEY", "")
BASE_RATES_URL: str = "http://data.fixer.io/api/latest"

CURRENCIES = [
    "AED", "AFN", "ALL", "AMD", "ANG",
    "AOA", "ARS", "AUD", "AWG", "AZN",
    "BAM", "BBD", "BDT", "BGN", "BHD",
    "BIF", "BMD", "BND", "BOB", "BRL",
    "BSD", "BTC", "BTN", "BWP", "BYN",
    "CAD", "CDF", "CHF", "CLP", "CNY",
    "COP", "CRC", "CUC", "CUP", "CVE",
    "CZK", "DJF", "DKK", "DOP", "DZD",
    "EGP", "ERN", "ETB", "EUR", "FJD",
    "FKP", "GBP", "GEL", "GHS", "GIP",
    "GMD", "GNF", "GTQ", "GYD", "HKD",
    "HNL", "HRK", "HTG", "HUF", "IDR",
    "ILS", "INR", "IQD", "IRR", "ISK",
    "JMD", "JOD", "JPY", "KES", "KGS",
    "KHR", "KMF", "KPW", "KRW", "KWD",
    "KYD", "KZT", "LAK", "LBP", "LKR",
    "LRD", "LSL", "LYD", "MAD", "MDL",
    "MGA", "MKD", "MMK", "MNT", "MOP",
    "MRU", "MUR", "MVR", "MWK", "MXN",
    "MYR", "MZN", "NAD", "NGN", "NIO",
    "NOK", "NPR", "NZD", "OMR", "PAB",
    "PEN", "PGK", "PHP", "PKR", "PLN",
    "PYG", "QAR", "RON", "RSD", "RUB",
    "RWF", "SAR", "SBD", "SCR", "SDG",
    "SEK", "SGD", "SHP", "SLL", "SOS",
    "SRD", "STN", "SVC", "SYP", "SZL",
    "THB", "TJS", "TMT", "TND", "TOP",
    "TRY", "TTD", "TWD", "TZS", "UAH",
    "UGX", "USD", "UYU", "UZS", "VEF",
    "VND", "VUV", "WST", "XAF", "XAG",
    "XAU", "XCD", "XDR", "XOF", "XPF",
    "YER", "ZAR", "ZMK", "ZMW", "ZWL",
]


def load_exchange_rates(api_key: str) -> Optional[dict]:
    """Fetch the latest exchange rates from the Fixer.io API.

    Parameters
    ----------
    api_key : str
        Fixer.io API access key.

    Returns
    -------
    dict or None
        Mapping of currency codes to rates on success, None on failure.
    """
    if not api_key:
        logger.error(
            "API key not configured. Set the FIXER_API_KEY environment variable."
        )
        return None

    params = {"access_key": api_key}
    logger.debug("Fetching exchange rates from %s", BASE_RATES_URL)

    try:
        response = requests.get(BASE_RATES_URL, params=params, timeout=10)
        response.raise_for_status()
        data: dict = response.json()
        if not data.get("success", True):
            logger.error(
                "Fixer.io API error: %s", data.get("error", "unknown error")
            )
            return None
        rates: dict = data["rates"]
        logger.info(
            "Exchange rates loaded successfully (%d currencies).", len(rates)
        )
        return rates
    except requests.exceptions.ConnectionError as exc:
        logger.error("Connection error fetching exchange rates: %s", exc)
    except requests.exceptions.Timeout:
        logger.error("Timed out while fetching exchange rates.")
    except requests.exceptions.HTTPError as exc:
        logger.error(
            "HTTP error %d fetching exchange rates: %s",
            exc.response.status_code,
            exc,
        )
    except (KeyError, ValueError):
        logger.exception("Unexpected response format from exchange rate API.")
    except requests.exceptions.RequestException:
        logger.exception("Unexpected network error.")
    return None


def convert_currency(
    amount: float,
    from_code: str,
    to_code: str,
    rates: dict,
) -> Optional[float]:
    """Convert amount from one currency to another using EUR as the base.

    Returns the converted amount rounded to 2 dp, or None on unknown code.
    """
    if from_code not in rates:
        logger.error("Unknown source currency: %s", from_code)
        return None
    if to_code not in rates:
        logger.error("Unknown target currency: %s", to_code)
        return None
    result = round(amount * rates[to_code] / rates[from_code], 2)
    logger.debug("Converted %.2f %s to %.2f %s", amount, from_code, result, to_code)
    return result


def parse_conversion_command(raw: str) -> Optional[tuple]:
    """Parse user input into (amount, from_code, to_code).

    Expected format: <amount> <FROM> <TO>   e.g.  100 USD EUR
    Returns None on parse failure.
    """
    parts = raw.strip().split()
    if len(parts) != 3:
        logger.warning("Invalid command format (expected: amount FROM TO): %r", raw)
        return None
    amount_str, from_code, to_code = parts
    try:
        amount = float(amount_str)
    except ValueError:
        logger.warning("Non-numeric amount: %r", amount_str)
        return None
    return amount, from_code.upper(), to_code.upper()


class CurrencyConverterController:
    """Orchestrate the currency conversion session.

    Attributes
    ----------
    _api_key : str
        Fixer.io API key.
    _rates : dict or None
        Loaded exchange rates; populated by start().
    _running : bool
        Loop sentinel; set to False by stop().
    """

    def __init__(self, api_key: str = API_KEY) -> None:
        self._api_key = api_key
        self._rates: Optional[dict] = None
        self._running: bool = False

    def start(self) -> bool:
        """Load exchange rates; return True on success, False on failure."""
        self._rates = load_exchange_rates(self._api_key)
        if self._rates is None:
            logger.error("Failed to load exchange rates - cannot start.")
            return False
        self._running = True
        logger.info("CurrencyConverterController started.")
        return True

    def stop(self) -> None:
        """Release resources and signal the run loop to exit."""
        self._running = False
        self._rates = None
        logger.info("CurrencyConverterController stopped.")

    def handle_command(self, command: str) -> None:
        """Route a user command to the correct action.

        Supported inputs:
            Q                    - quit
            SHOW                 - list available currency codes
            <amount> <FROM> <TO> - perform a conversion
        """
        upper = command.strip().upper()

        if upper == "Q":
            print("Goodbye!")
            self.stop()
            sys.exit(0)

        if upper == "SHOW":
            print("\nAvailable currencies:\n  " + "  ".join(CURRENCIES))
            return

        parsed = parse_conversion_command(command)
        if parsed is None:
            print(
                "Invalid input. Format: <amount> <FROM> <TO>  (e.g. 100 USD EUR)\n"
                "Type SHOW to list currencies, Q to quit."
            )
            return

        amount, from_code, to_code = parsed
        if self._rates is None:
            logger.error("Exchange rates not loaded.")
            print("Exchange rates are unavailable.")
            return

        result = convert_currency(amount, from_code, to_code, self._rates)
        if result is None:
            print("Conversion failed: unknown code(s). Type SHOW to list.")
        else:
            print(
                str(amount) + " " + from_code
                + " = " + str(result) + " " + to_code
                + "  (as of latest rates)"
            )

    def run(self) -> None:
        """Run the interactive conversion loop until the user quits."""
        if not self.start():
            print(
                "Could not load exchange rates. "
                "Check your network connection and API key."
            )
            return

        print("Currency Converter")
        print("  Enter: <amount> <FROM> <TO>  |  SHOW to list codes  |  Q to quit\n")

        while self._running:
            try:
                command = input("> ")
            except (EOFError, KeyboardInterrupt):
                self.stop()
                break
            self.handle_command(command)


def main() -> None:
    """Configure logging and run the currency converter controller."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        stream=sys.stderr,
    )
    logger.info("Currency Converter application starting.")
    controller = CurrencyConverterController()
    controller.run()


if __name__ == "__main__":
    main()
