# Implementation Plan - CodemieRepo Code Quality & Security Improvements

Source story: Confluence - "CodemieRepo: Recommended Code Quality & Security Improvements" (https://akashramesh291099.atlassian.net/wiki/spaces/EC/pages/5341185/CodemieRepo+Recommended+Code+Quality+Security+Improvements)

> Security note: This plan avoids embedding any secrets. All configuration values should be supplied via environment variables or secret managers.

---

## High-level overview

- Strengthen the user registration flow by adding robust input validation (email, password, username) and consistent error responses.
- Remove hard-coded configuration/values (DB credentials, secret keys, endpoints) from source and migrate to environment-based configuration.
  - Optionally support local development with a `.env` file (local-only) and `python-dotenv`.
- Improve authorization/data safety by ensuring database interactions are parameterized (or ORM).
- Add tests for validation and config behavior to prevent regressions.

---

## Detailed technical steps

### 0) Pre-implementation checks (1–2 hours)

1. **Locate the actual implementation points in the repo**
   - Search for registration/signup routes (e.g., `/register`, `signup`, `auth`).
   - Search for hard-coded config keys: `SECRET_KEY`, `DB_`, `PASSWORD`, `api_key`, `database`, hostnames, URLs.
   - Record a list of file paths to include in the PR description (auditable).
2. **Identify the web framework**
   - Flask vs FastAPI vs Django to select the most native validation mechanism.
3. **Baseline tests**
   - Run existing tests (or add a minimal test harness) to verify behavior before/after.

### 1) Enhance input validation in user registration

1. **Add centralized validation helpers**
   - Create a module (e.g., `app/validation.py` or `utils/validation.py`) that exposes:
     - `is_valid_email(email)`
     - `is_strong_password(password)`
     - `is_valid_username(username)`
   - Decide error style: return `(bool, message)` or raise a custom `ValidationError`.
2. **Email validation**
   - Implement syntax validation using either:
     - lightweight regex, or
     - a validation library (e.g., `email-validator`).
   - Reject invalid input before any DB/account creation occurs.
3. **Password policy**
   - Enforce minimum length (e.g., >=8).
   - Enforce complexity: upper, lower, digit, symbol.
   - Optional: add common-password/breached-password checks if risk profile justifies it.
4. **Username constraints**
   - Allow a safe set (e.g., `^[A-Za-z0-9_.]+$`).
   - Enforce length bounds (3–30).
   - Ensure DB uniqueness is enforced (unique index/constraint) and handle conflicts gracefully.
5. **Secure DB patterns**
   - Audit registration flow DB interactions and ensure parameterized queries or ORM are used.
   - If raw SQL is used, replace formatted strings with placeholders.
6. **Consistent error responses**
   - Standardize validation failure responses (HTTP 400, structured JSON if API).
   - Avoid echoing back sensitive values.

### 2) Refactor hard-coded configuration to environment variables

1. **Inventory hard-coded settings**
   - Document all config items to migrate: DB user, DB pass, DB name, `SECRET_KEY`, any API keys/endpoints.
2. **Introduce a single config module**
   - Create `config.py` (or equivalent) that:
     - reads from `os.environ`
     - validates required values on startup (fail-fast)
     - keeps non-sensitive defaults only for development.
3. **Local development support (optional)**
   - Add `python-dotenv` as a development dependency and load `.env` only in local/dev.
4. **Add `.env.example`**
   - Commit a safe example with placeholders (NOT secrets) listing required vars.
5. **Update `.gitignore`**
   - Ensure `.env` and other secret files are ignored.
6. **Migrate code usages**
   - Replace hard-coded settings in DB connection/app init with `config` reads.
   - Update README/docs with env setup steps.

### 3) Testing and QA

1. **Unit tests for validation**
   - Email: valid/invalid patterns.
   - Password: length/class requirements edge cases.
   - Username: allowed chars/length bounds.
2. **Config validation tests**
   - Missing env vars should fail fast with clear messages.
   - Dev defaults should never enable insecure prod states.
3. **Integration tests (optional)**
   - Registration flow end-to-end: invalid input => 400, valid => success.

### 4) Deployment / rollout / rollback

- **Rollout**: deploy to dev/staging, confirm env vars are provided, run tests, then promote to prod.
- **Rollback**: revert PR or redeploy previous release; old config can be restored temporarily if needed for a short transition.

---

## Acceptance criteria

- Registration endpoint enforces email/password/username rules and returns consistent validation errors.
- No secrets/credentials remain hard-coded in the repo.
- App startup validates required env vars and fails fast with actionable errors.
- `.env` remains ignored; `.env.example` exists with placeholders.
- Tests added/updated and pass in CI.
