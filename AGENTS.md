# Repository Guidelines

## Project Structure & Module Organization
- `edgard_site/` holds Django settings, URLs, and ASGI/WSGI entry points; change environment toggles here.
- Domain code lives in `apps/` with one app per concern (`core`, `customers`, `inventory`, `quotes`, `orders`, `grid`, `scheduler`, `integrations`); share cross-cutting helpers via `apps/core`.
- Templates reside in `templates/`; static assets ship from `static/`; uploaded media lands in `media/`.
- Keep tests close to code in `apps/<name>/tests.py` or a `tests/` package; mirror module names for discoverability.
- Use the checked-in `venv/` only as a reference; create your own local virtual environment and exclude it from commits.

## Build, Test, and Development Commands
- `python -m venv venv && venv\Scripts\activate` prepares and activates the Windows virtual environment.
- `pip install -r requirements.txt` installs Python dependencies, including Django REST Framework and Celery.
- `python manage.py migrate` applies database schema updates to the default SQLite store.
- `python manage.py runserver 192.168.178.30:8020` launches the API with debug toolbar enabled.
- `python manage.py test` executes the Django test runner across all installed apps; add `apps.quotes` or similar to scope runs.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and keep lines under 100 characters.
- Use `PascalCase` for models, serializers, and services; `snake_case` for functions, variables, and test names.
- Break features into modules named `models.py`, `serializers.py`, `views.py`, `tasks.py`; avoid large utility dumps; prefer app-specific helpers in `apps/core`.
- Favor f-strings for formatting, ORM lookups over raw SQL, and Django `settings` for feature flags.

## Testing Guidelines
- Write behavior-focused tests (`test_<method>_<expected>`); assert both success and failure paths for business logic in `apps.quotes` and scheduling flows.
- Stub external integrations via DRF APIClient or mock Celery tasks; keep fixtures/factories in `apps/core/tests/` for reuse.
- Aim for coverage on critical paths (quote pricing, inventory sync) before adding UI templates or migrations.

## Commit & Pull Request Guidelines
- Use concise, imperative commit subjects (`Add quote PDF rendering`); group related migrations and fixtures in the same commit.
- Reference tracker links or issue IDs in the body when applicable; document schema changes and manual test steps in PR descriptions.
- PRs should outline the problem, solution, validation, and include screenshots for template changes; request reviewers from affected module owners.

## Configuration & Security Notes
- Store secrets in an `.env` loaded via `django-environ`; never commit production keys such as `SECRET_KEY` or broker credentials.
- Update `ALLOWED_HOSTS`, CORS origins, and Celery broker/backend URLs per environment before release.
- Coordinate storage, email, and WeasyPrint dependencies with Ops; keep credentials in the shared password vault.
