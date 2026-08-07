# Implementation Plan – CodemieRepo Improvements (Input Validation/Auth + View Modularization)

Source Story (Confluence): CodemieRepo Codebase Review – Identified Improvements (Input Validation/Auth + View Modularization)
Confluence URL: https://akashramesh291099.atlassian.net/wiki/spaces/EC/pages/5308417/CodemieRepo+Codebase+Review+Identified+Improvements+Input+Validation+Auth+View+Modularization

Ownership: This plan is implementation-focused and auditable. All changes should land via a PR so they are reviewable and reversible.

## High-level overview (bullet points)

- Harden registration and login flows by centralizing input validation using Django Forms/ModelForms and Django’s built-in auth APIs.
- Add password policy enforcement via `django.contrib.auth.password_validation` and basic brute-force mitigations (rate-limit/lockout).
- If applicable, add audit logging for auth events (failed logins, account creations) without logging sensitive data.
- Refactor duplicated functionality in views into reusable helpers/services and optionally migrate high-drift paths to class-based views (CBVs) for consistency.
- Introduce tests for auth and key view behavior to prevent regressions during refactoring.

## Detailed technical steps

### 0) Pre-flight: validate current state

1. Create a local dev env: `python -m venv .venv && source .venv/bin/activate` (or Windows equivalent).
2. Install deps: `pip install -r requirements.txt` (and/or poetry if used).
3. Run tests (if any) and server to establish baseline: `python manage.py test`, `python manage.py runserver`.
4. Locate auth endpoints and view implementations: search for `register`, `login`, `authenticate`, locate url conf and templates.
   - Output: a short list of exact modules/files to be touched (e.g., `app/views.py`, `app/urls.py`, `templates/*`).

### 1) Improvement 1 — Input validation + authentication hardening

#### 1.1) Centralize validation with Django Forms/ModelForms

1. Create a new forms module (or extend if exists): `<app>/forms.py` with:
   - `RegistrationForm` (username, password1, password2) with match check.
   - `LoginForm` (username, password).
2. Validation rules to enforce:
   - Required fields; max lengths aligned with Django User.
   - Username pattern/allowed chars (align with Django’s validators as applicable).
   - Consistent error messages (don’t leak user existence in login flow).
3. Switch views to consume `form.cleaned_data` only.
   - Avoid direct `request.POST['x']` usage except for form binding.

#### 1.2) Use Django Auth APIs correctly

Registration:
1. Create user via Django’s User model (or current custom user):
   - `User.objects.create_user(username, password=pwd)` so password is hashed.
2. Optionally auto-login after successful registration via `login()` if required by UX.
3. Handle duplicate usernames gracefully using form errors (avoid raw exception exposure).

Login:
1. Call `authenticate(request, username, password)`.
2. On success: call `login(request, user)` and redirect.
3. On failure: return a generic error (no user enumeration).

#### 1.3) Enforce password policies

1. Inspect `settings.py` for `AUTH_PASSWORD_VALIDATORS`.
   - If missing, add standard validators: UserAttributeSimilarity, MinimumLength, CommonPassword, NumericPassword.
2. Update registration form to validate via password validators (e.g., call `validate_password()` in `clean_password2`) if not using Django’s built-in `UserCreationForm`.

#### 1.4) Brute-force mitigations (rate limit/lockout)

Choose one approach (lightweight and reversible):

- Option A: add `django-axes` (account lockout on repeated failures)
  1. Add to requirements and install.
  2. Add `axes` to `INSTALLED_APPS` and middleware per docs.
  3. Configure thresholds and lockout durations in settings.
  4. Validate behavior with test logins; ensure admin/service accounts are not accidentally locked out.

- Option B: request-level rate limiting via `django-ratelimit` for login endpoints.
  1–4. Similar: add dep, decorate login view, configure rate.

#### 1.5) Audit logging (secure)

Implement logging for:
- User registration success/failure (without passwords/POST dumps).
- Login failure rates (optional).

Guidelines:
- Never log plaintext passwords, full POST bodies, session ids, or access tokens.
- If logging username/email, consider masking/hashing in high-sensitivity environments.

### 2) Improvement 2 — View modularization and reuse

#### 2.1) Audit and classify duplication in views

1. Identify repeated patterns:
   - Loading course objects and handling not-found.
   - Permission/auth checks.
   - Common context dict construction for templates.
   - Similar error handling/redirect patterns.
2. Group into categories: (a) data fetch, (b) validation, (c) auth, (d) response/rendering.

#### 2.2) Extract helpers/services

1. Add a `services/` or `helpers/` package in the app:
   - `<app>/services/auth.py` (e.g., `perform_login()` in one place)
   - `<app>/services/courses.py` (e.g., `get_course_or_404()`)
2. Use Django utilities where possible: `get_object_or_404`, `login_required`, mixins (`LoginRequiredMixin`) to reduce custom code surface area.
3. Keep services side-effect aware:
   - Services can return domain objects or raise controlled exceptions.
   - Views handle HTTP concerns (request/response, redirects).

#### 2.3) Migrate selected views to CBVs (optional but recommended)

1. Identify high-traffic or complex function-based views and replace with:
   - `FormView` for login/register flows (or `django.contrib.auth.views.LoginView` for login).
   - `ListView`/`DetailView` for course content pages.
2. Ensure URL patterns update cleanly; keep old URLs stable to avoid breaking clients/bookmarks.

#### 2.4) Standardize error handling and responses

1. Create shared helpers for:
   - consistent 404/403 handling
   - consistent messages framework usage (if enabled)
2. Avoid leaking sensitive auth state in error responses.

### 3) Testing plan (must-have)

#### 3.1) Unit tests for forms

- Test required fields, max lengths, and username constraints.
- Test password match and password validator errors.

#### 3.2) Integration tests for auth flow

- Register success → user created and password hashed.
- Register duplicate username → proper form error.
- Login success → session established.
- Login failure → generic error, no user enumeration.
- If rate-limit/lockout enabled → verify threshold behavior.

#### 3.3) Regression tests for refactored views

- Validate course endpoints still render/return expected status codes.
- Validate permissions still enforced.

### 4) Deployment & rollout

1. Ship behind a short-lived feature branch + PR.
2. If adding dependencies (axes/ratelimit), confirm:
   - requirements locked
   - settings documented
   - migrations applied if required (axes may require DB tables depending on backend)
3. Rollout order:
   - merge to main
   - deploy to staging
   - smoke test login/register and key pages
   - deploy to production

### 5) Observability & auditability

- Add changelog notes in PR description.
- Ensure logs do not contain credentials.
- Keep all changes reversible:
  - single PR
  - revert commit possible

### 6) Acceptance criteria

- Registration and login use Django Form validation (no raw `request.POST` usage for core validation).
- Password policies enforced via Django validators.
- Brute-force mitigation enabled and verified.
- Views show reduced duplication (shared helpers/services and/or CBVs).
- Tests added and passing in CI/local.
