# Implementation Plan – CodemieRepo (Modularity, Error Handling & Logging)

source: Confluence page (id: 6127617)
title: "CodemieRepo Codebase Review – Key Improvements (Modularity, Error Handling & Logging)"

design-doc: Confluence page (id: 6160385)
title: "CodemieRepo - Design & Architecture Document (Draft)"

---

## Summary

This plan describes the code quality improvements applied to CodemieRepo on
branch `feature/implementation-plan-20260810-0400` based on the design
architecture document and the codebase review.

Two key areas are addressed:
1. Modularity – refactor procedural scripts into small functions and classes.
2. Error handling and logging – replace ad-hoc print() calls with the Python
   logging module and wrap I/O / network operations in structured try/except.

---

## Files created / modified

### Shared utilities (new)

- src/__init__.py
- src/utils/__init__.py
- src/utils/logging_config.py
  Provides configure_logging() and get_logger() for consistent logging setup
  across all projects.
- src/utils/error_handlers.py
  Provides handle_file_error(), handle_network_error(), and
  handle_unexpected_error() wrappers that catch specific exceptions and log
  them at the correct level.

### Refactored project scripts (new files alongside originals)

- projects/Number_guessing_game/number_guessing_game.py
  Refactored from main.py:
    - NumberGuessingGame controller class (start/handle_guess/run)
    - parse_guess() and generate_secret() helper functions
    - logging.basicConfig() in main()
    - Input validation via parse_guess() with ValueError handling

- projects/Fetch_current_weather/fetch_current_weather_refactored.py
  Refactored from fetch_current_weather.py:
    - API key read from OPENWEATHER_API_KEY env var
    - fetch_weather_data() with requests exception handling
    - parse_weather() for data extraction
    - format_weather_report() for presentation
    - WeatherController class

- projects/Language_translator/translator_refactored.py
  Refactored from translator.py:
    - list_languages(), select_language(), translate_text() functions
    - TranslatorController class
    - Translation wrapped in try/except with specific exception handling

- projects/Currency_converter/currency_converter_refactored.py
  Refactored from cc.py:
    - Renamed function1() to parse_conversion_command() and convert_currency()
    - API key read from FIXER_API_KEY env var
    - load_exchange_rates() with structured requests exception handling
    - CurrencyConverterController class (start/run/stop/handle_command)

### Tests (new)

- tests/__init__.py
- tests/test_number_guessing_game.py
- tests/test_currency_converter.py
- tests/test_utils.py

### Project root (new)

- .env.example       – placeholder environment variable template
- .gitignore         – excludes .env, __pycache__, test artifacts

---

## Logging standards applied

- All modules define: logger = logging.getLogger(__name__)
- main() in every refactored module calls logging.basicConfig()
- Log levels used:
    DEBUG    – detailed internal steps (e.g., API call URL, guess value)
    INFO     – normal milestones (app start, successful data load)
    WARNING  – recoverable issues (invalid user input)
    ERROR    – actionable failures (missing API key, HTTP error)
    CRITICAL – not used in these scripts (reserved for fatal startup failures)
- logger.exception() used for unexpected errors (includes stack trace)

---

## Error handling approach

File operations:  wrapped with handle_file_error() or try/except
                  catching FileNotFoundError, PermissionError, OSError
Network calls:    wrapped with try/except catching
                  requests.exceptions.ConnectionError,
                  requests.exceptions.Timeout,
                  requests.exceptions.HTTPError,
                  requests.exceptions.RequestException
Unexpected:       handled with logger.exception() – logs full stack trace

---

## Acceptance criteria

- Refactored scripts have no bare print() for diagnostic/error output.
- All I/O and network operations use structured try/except with specific
  exception types.
- Module-level loggers defined via logging.getLogger(__name__).
- Shared utilities (logging_config, error_handlers) provide reusable helpers.
- Unit tests cover helper functions and controller lifecycle.
- .env is listed in .gitignore; .env.example exists with placeholders only.
