# DNS Discovery — Asset Discovery Service

A backend microservice for an Attack Surface Management platform: manages a list of
domains an organization wants monitored, performs passive DNS discovery against them
in the background, and exposes the discovered assets (DNS records) via a JWT-authenticated,
role-based API.

## Tech stack

- Python 3.12, FastAPI
- SQLAlchemy 2.x (async, `asyncpg` driver) + Alembic migrations
- PostgreSQL (Supabase-hosted in this setup)
- `python-jose` (JWT) + `passlib`/`bcrypt` (password hashing)
- `dnspython` (async DNS resolution) + FastAPI `BackgroundTasks` (discovery worker)
- Pytest + `pytest-asyncio`

## Installation

1. **Clone the repo and create a virtualenv:**
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Configure environment variables.** Copy `.env_example` to `.env` and fill in real
   values (see [Environment variables](#environment-variables) below).

   > If your database password contains special characters (`@`, `:`, `/`, `%`, etc.),
   > they must be percent-encoded in `DATABASE_URL` (e.g. a literal `@` becomes `%40`),
   > otherwise the URL's `user:password@host` boundary parses incorrectly.

3. **Run migrations:**
   ```
   alembic upgrade head
   ```

4. **Run the app:**
   ```
   python main.py
   ```
   or
   ```
   uvicorn main:app --reload
   ```
   API docs (Swagger UI) are then available at `http://localhost:8000/docs`.

## How to run with Docker

```
docker compose up --build
```

This starts two containers:
- `db` — a local Postgres 16 instance (not your Supabase database), with a healthcheck
  (`pg_isready`) that the `api` container waits on before starting.
- `api` — builds this repo's `Dockerfile`, runs `alembic upgrade head` against the `db`
  container, then starts `uvicorn` on port 8000.

**You still need a real `.env` file** (copy `.env_example` → `.env`, fill in real
values) before running this — `docker-compose.yml` loads it via `env_file` for
`JWT_SECRET_KEY`, `MAIL_*`, `SUPABASE_URL`/`SUPABASE_KEY`, etc. The one exception is
`DATABASE_URL`: `docker-compose.yml` overrides it to point at the local `db` container
instead of whatever's in your `.env`, so the containerized run never touches your real
(Supabase) database.

Once it's up, Swagger UI is at `http://localhost:8000/docs`, and `GET /health` reports
API + database connectivity.

## How to run the test suite

```
pytest
```

or, without an activated venv:
```
.venv\Scripts\python.exe -m pytest
```

Useful variations:
- `pytest -v` — verbose, one line per test
- `pytest app/domains/tests/` — just one module's tests
- `pytest app/domains/tests/test_domain_api.py::test_create_domain_success` — a single test
- `pytest -x` — stop at the first failure

**Note:** these tests run against the real database configured in `.env` — there's no
separate test database wired up. Every fixture in the root `conftest.py` cleans up
whatever it creates (test users, test domains — and cascade-deletes take care of their
scans/assets), so a clean run leaves no residue. `app/scans/tests/test_scan_worker.py`
mocks DNS resolution directly (`app.scans.worker._resolve_record`), so it never makes a
real network call; other tests that create domains do incidentally trigger a real,
harmless DNS lookup against well-known public domains (see `conftest.py`'s
`next_test_domain()`) as part of the automatic-scan-on-create flow.

## Architecture overview

The code is organized by feature, not by technical layer — each of `users`, `domains`,
`scans`, `assets` under `app/` is a self-contained vertical slice:

```
app/<feature>/
    models.py            SQLAlchemy models
    dto/                  Pydantic request/response schemas (validation lives here)
    dao/                  data-access layer (raw DB queries)
    service/              thin business-logic layer between routes and DAOs
    urls.py               FastAPI router for this feature
    tests/                pytest tests for this feature
app/core/
    models.py             shared declarative Base
    constants.py           user-facing message strings
    settings/config.py     Pydantic Settings (.env)
    utils/                 auth (JWT/RBAC), password hashing, mail, generic DB helpers
    urls.py                aggregates every feature router under /api/v1
```

Request flow: `urls.py` (route + RBAC dependency) → `service` → `dao` → SQLAlchemy model.
Every route either returns data directly or raises `HTTPException` with a consistent
`{"error": "..."}` (or, for validation, FastAPI's own `{"detail": [...]}`) body — see
the exception handling note below.

**Auth & RBAC.** `CommonAuthUtils.get_current_active_user` resolves a bearer token to a
full, active `User` row; `CommonAuthUtils.require_roles(*roles)` is a dependency factory
that layers a role check on top of it (`Depends(require_roles(UserRole.ADMIN))`). Roles
are `ADMIN` / `ANALYST` / `VIEWER`, matching the assignment's RBAC matrix — Admin manages
users and can delete domains, Analyst can create domains and trigger scans but not
delete, Viewer is read-only everywhere.

**Domain → Scan → Asset lifecycle.** Creating a domain (`POST /api/v1/domains`)
immediately creates a `PENDING` `Scan` row and schedules the actual discovery work via
FastAPI's `BackgroundTasks` (`app/scans/worker.py::run_discovery_scan`) — the HTTP
response returns right away, matching the spec's "API requests return immediately"
requirement. The worker resolves `A`/`AAAA`/`NS`/`MX` records (`dnspython`,
`dns.asyncresolver`, 5s timeout per record type so one unresponsive domain can't hang
the worker), persists each as an `Asset` row, and moves both the `Scan` and its parent
`Domain` through `PENDING → RUNNING → COMPLETED`/`FAILED` together. Any unhandled
exception anywhere in the worker is caught and turned into a `FAILED` scan with the
captured error message — it's never left stuck in `RUNNING`. A manual re-scan
(`POST /api/v1/domains/{id}/scan`) rejects with `409` if a scan is already `RUNNING`
for that domain.

**Why `BackgroundTasks` and not Celery/Redis.** The assignment's required stack (§10.1)
doesn't include a task queue; Celery/Redis are explicitly listed as bonus/optional
(§10.2, §19). `BackgroundTasks` satisfies the actual functional requirement (§8 —
discovery runs asynchronously, API returns immediately) without adding a broker,
a second worker process, or another moving part to the Docker setup, given the
project's time constraints. The discovery logic itself (`run_discovery_scan`) doesn't
know or care how it's invoked, so swapping the call site for `.delay()` later, if ever
needed, is a small, isolated change.

**Logging.** `app/core/logging_config.py` configures both a console handler and a
`TimedRotatingFileHandler` (rotates at midnight, keeps 30 days, then deletes older
files automatically) writing to `logs/app.log`. Request/response lines, auth events
(login success/failure, registration), scan worker lifecycle (started/completed/failed
with asset counts), and unhandled route errors are all logged.

**Centralized exception handling.** Routes raise `HTTPException` with a consistent
`{"error": "..."}` detail body and the correct status code (`401`/`403`/`404`/`409`/`500`
as appropriate) instead of silently returning `200` with an error string in the body.
Pydantic validation failures (invalid FQDN, weak password, etc.) are intercepted by a
global `RequestValidationError` handler in `main.py` and re-mapped from FastAPI's
default `422` to `400`, matching the spec's documented error codes.

## Environment variables

All required variables live in `.env` (see `.env_example` for the full list of keys —
copy it to `.env` and fill in real values):

| Variable | Purpose |
|---|---|
| `SUPABASE_URL` / `SUPABASE_KEY` | Supabase project credentials |
| `DATABASE_URL` | Postgres connection string, `asyncpg` driver (`postgresql+asyncpg://...`) |
| `ALGORITHM` | JWT signing algorithm (e.g. `HS256`) |
| `JWT_SECRET_KEY` / `JWT_REFRESH_SECRET_KEY` | JWT signing secrets (access vs. refresh tokens) |
| `MAIL_USERNAME` / `MAIL_PASSWORD` / `MAIL_FROM` | Outgoing mail credentials, used for forgot-password emails |

`MAIL_PORT`, `MAIL_SERVER`, `MAIL_STARTTLS`, `MAIL_SSL_TLS` have sane defaults in
`app/core/settings/config.py` and don't need to be set unless you're overriding them.

## Key design decisions and trade-offs

- **`docker-compose.yml` runs its own local Postgres container**, not the Supabase
  database used for local (non-Docker) development. The spec requires "the database
  container starting and becoming healthy" as part of `docker compose up --build`,
  which only makes sense with a locally-owned database — so `DATABASE_URL` is
  overridden specifically for the containerized `api` service to point at the local
  `db` service, while every other setting (JWT secrets, mail, Supabase client
  credentials) still comes from your real `.env` via `env_file`.
- **Feature-based project structure**, not the layout suggested in the assignment
  (`api/`, `models/`, `schemas/`, `services/`, `repositories/`, `workers/`). Grouping by
  feature (`users`, `domains`, `scans`, `assets`) keeps everything related to one
  business concept in one place and was the structure already established in this
  codebase before this assignment's features were added to it.
- **`full_name` instead of `name`, uppercase role enum values** (`"ADMIN"` not
  `"admin"`) on the `User` model — aligned to match the spec's exact request/response
  examples (§6.1, §7.1) rather than the field names originally in this codebase.
- **Hard delete for domains** (`DELETE /domains/{id}` actually removes the row, with
  `ON DELETE CASCADE` down to `scans` and `assets`) rather than the soft-delete
  (`is_active = False`) pattern used elsewhere in this codebase for users — the spec
  explicitly says "permanently remove," and cascading a soft-delete flag through three
  tables would need its own filtering logic everywhere assets/scans are read.
- **`scans.error_message` and `scans.created_at`** were added beyond the spec's
  suggested schema (§7.3) — a captured error message is required functionally (§8:
  "Worker failures must set the scan to FAILED with a captured error message"), and
  `created_at` is needed to order scan history before `started_at` is set (a `PENDING`
  scan has no `started_at` yet).
- **`/register/` and `/login`** (not `/auth/register`/`/auth/login` as shown in the
  spec) — pre-existing route paths in this codebase, left as-is; every other route
  matches the spec's paths exactly.
- **Tests run against the real dev database**, not an isolated test database — there
  wasn't time to stand up a separate test Postgres instance/Docker service, so tests
  create and clean up their own data instead. A real trade-off, not a design choice;
  see Future improvements.

## Ideas for future improvement

- A dedicated test database service in `docker-compose.yml` (with its own `DATABASE_URL`
  override for test runs), instead of tests running against the same dev database.
- Rate limiting on `/login` and `/register/` (brute-force protection).
- Audit logging of sensitive actions (domain deletion, role changes).
- Automatic retry of `FAILED` scans with backoff.
- Redis-backed caching for `GET /domains`/`GET /assets` list endpoints under real load.
- CI (GitHub Actions) running `pytest` + linting on every push.
