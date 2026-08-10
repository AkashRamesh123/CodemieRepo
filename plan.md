# Implementation Plan: Security/Configuration Refactor & Logging/Error Handling Enhancements

Source: Confluence story – "Security/Configuration Refactor & Logging/Error Handling Enhancements".

## High-level overview

- Remove hard-coded API credentials from source files and replace with environment-variable lookups.
- Introduce a shared `projects/common/` package providing reusable config loading, logging setup, and exception types.
- Replace all `print()` diagnostic calls with structured `logging` calls.
- Add consistent, structured error handling around all external HTTP calls with timeouts, `raise_for_status()`, and user-friendly failure messages.

## Identified security issues

1. `projects/Currency_converter/cc.py` – API key embedded in URL string (leaked credential).
2. `projects/Fetch_current_weather/fetch_current_weather.py` – placeholder `api_key` assigned as a string literal in source.
3. No `.gitignore` – risk of committing `.env` files with secrets.

## Detailed technical steps

### 1) Shared infrastructure (new `projects/common/` package)

- `projects/__init__.py` – makes `projects/` importable as a package.
- `projects/common/__init__.py` – package marker.
- `projects/common/config.py`:
  - `class ConfigError(RuntimeError)` – raised when a required env var is missing.
  - `def get_env(name, *, required=True, default=None) -> str` – reads env var; raises `ConfigError` if required and absent.
- `projects/common/logging_utils.py`:
  - `def get_logger(name, level_env="LOG_LEVEL") -> logging.Logger` – returns a named logger with a `StreamHandler`; idempotent (no duplicate handlers); level controlled by `LOG_LEVEL` env var (default `INFO`).
- `projects/common/exceptions.py`:
  - `class ExternalAPIError(RuntimeError)` – network/API failures.
  - `class InvalidResponseError(RuntimeError)` – unexpected response schema.

### 2) Security/configuration refactor

#### Currency converter (`projects/Currency_converter/cc.py`)
- Remove hard-coded access key from the URL.
- Read API key via `get_env("CURRENCY_CONVERTER_API_KEY")`.
- Build HTTP request with `params={"access_key": api_key}` (not string interpolation).
- Add `timeout=10` to requests call.

#### Weather fetcher (`projects/Fetch_current_weather/fetch_current_weather.py`)
- Replace `api_key = "Your_API_Key"` with `api_key = get_env("OPENWEATHER_API_KEY")`.
- Build request with `params={"appid": api_key, "q": city_name}`.
- Add `timeout=10`.

### 3) Logging enhancements

- Both scripts instantiate `logger = get_logger(__name__)`.
- All `print()` calls replaced with `logger.info/warning/error/exception()`.

### 4) Structured error handling

- Wrap each HTTP call with specific exception handling:
  - `requests.exceptions.Timeout` → `logger.error("request timed out")`
  - `requests.exceptions.ConnectionError` → `logger.error("network error")`
  - `requests.exceptions.HTTPError` → `logger.error("HTTP %s", response.status_code)`
  - `json.JSONDecodeError` → `logger.error("invalid JSON")`
  - `ConfigError` → `logger.error("missing env var: %s", e)`
- Validate JSON response fields before use; raise `InvalidResponseError` on bad schema.
- Wrap scripts in `main() -> int` + `if __name__ == "__main__": raise SystemExit(main())`.

### 5) Supporting files

- `.env.example` – documents required env vars with placeholder values.
- `.gitignore` – ensures `.env`, `__pycache__`, and test artefacts are excluded.

## Acceptance criteria

- `python -c "from projects.common.config import get_env"` succeeds.
- Running either script without env vars set prints a clear "missing env var" error (not a traceback with a key).
- Running with a valid env var uses it without the key appearing in source code.
- All existing `print()` diagnostics in the two scripts replaced by `logging` calls.
