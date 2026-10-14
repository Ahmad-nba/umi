# UMI Production Preparation Report

**Date:** 2026-10-14  
**Repository:** `Ahmad-nba/umi`  
**Target deployment:** Render (FastAPI backend), Neon PostgreSQL, Vercel (Next.js frontend)  
**Status:** PostgreSQL compatibility implementation complete; PostgreSQL server validation and cloud deployment are not yet complete.

## 1. Executive summary

UMI is a working, synchronous FastAPI modular monolith. It uses SQLAlchemy 2.x, Pydantic 2, SQLite persistence, deterministic/offline classification when no LLM key is configured, and a Next.js frontend under `web/`. The implemented workflow covers feedback intake, classification, issue creation/routing, lifecycle transitions, notifications, QA views, and conversation intake.

The current implementation is suitable for a tested demonstrator, not for an internet-facing production deployment. The primary production blockers are:

1. SQLite is still the default and only exercised database.
2. There is no Alembic (or equivalent) migration history.
3. Startup calls `Base.metadata.create_all()` and performs seed work rather than running controlled migrations.
4. CORS is hard-coded to local frontend origins.
5. API routes are currently unauthenticated, as also noted in the existing architecture report.
6. The health endpoint is liveness-only and does not prove database readiness.
7. External LLM and email integrations have not been verified against production credentials/services.
8. Deployment commands, environment variables, and rollback procedures are not yet encoded as a tested deployment workflow.

The selected implementation retains SQLAlchemy and the existing service/API contract, adds PostgreSQL support through `DATABASE_URL`, adds the PostgreSQL driver, introduces versioned migrations, and preserves SQLite for local development/tests. A broad rewrite or frontend redesign was not warranted.

## 2. Evidence reviewed

The assessment is based on:

- `app/main.py`, `app/core/config.py`, and `app/core/database.py`.
- SQLAlchemy models in `app/models/`.
- API routers in `app/api/` and services in `app/services/`.
- `requirements.txt` and `pyproject.toml`.
- Existing documentation in `ARCHITECTURE_REPORT_PHASES_1_10.md`, `README.md`, and `postgress_lift.md`.
- The current Git working tree.
- The complete automated test suite.

### Baseline command and result

```text
umienv\Scripts\python.exe -m pytest
41 passed, 4 warnings in 3.08s
```

The warnings are deprecations for Starlette/httpx compatibility and FastAPI `on_event` startup handlers. The tests use an in-memory SQLite database; this result does **not** prove PostgreSQL compatibility or cloud readiness.

## 3. Current architecture

### Runtime and application layers

- **HTTP layer:** FastAPI routers under `app/api/`.
- **Business layer:** synchronous services under `app/services/`.
- **Agent boundary:** `app/agents/llm_client.py` and `classifier.py`.
- **Persistence:** SQLAlchemy ORM models under `app/models/`.
- **Configuration:** `pydantic-settings` in `app/core/config.py`.
- **Server:** Uvicorn; local command is `uvicorn app.main:app --reload`.
- **Frontend:** Next.js application under `web/`, intended to call the backend on port 8000.

`app/main.py` constructs the application, registers routers, adds CORS middleware, and runs database initialization and handler seeding on startup.

### Existing API surface

The current routers expose:

- `/health`
- Feedback creation, listing, retrieval, processing, and routing.
- Issue listing and retrieval.
- Workflow actions: acknowledge, start, complete, confirm, and close.
- Notifications by issue.
- QA dashboard and issue detail.
- Conversation creation, message collection, and submission.

The routes use `Depends(get_db)` and synchronous SQLAlchemy `Session` objects. No authentication or authorization dependency is currently applied to these routes.

### Current database lifecycle

`app/core/database.py`:

- Reads `DATABASE_URL`, falling back to `sqlite:///./data/feedback_watch_tower.db`.
- Builds a global SQLAlchemy engine and `SessionLocal`.
- Uses `check_same_thread=False` unconditionally when creating the engine.
- Provides request-scoped sessions through `get_db()` and closes them in `finally`.
- Provides `reset_database()` for tests and local workflows.
- Calls `Base.metadata.create_all()` during initialization.
- Applies SQLite-only `ALTER TABLE` compatibility patches for `conversations.feedback_id` and `notifications.delivery_error`.

The current session cleanup is good for the existing synchronous request model, but the global engine/session rebinding pattern is fragile for parallel tests and makes deployment lifecycle control less explicit.

## 4. Persistence schema inventory

The ORM currently maps seven tables:

| Table | Key data and constraints |
|---|---|
| `reporters` | Integer primary key; name, contact, created timestamp. |
| `feedbacks` | Reporter foreign key; channel, content, optional context, submission timestamp, status. |
| `handlers` | Name, department, contact, active boolean. |
| `issues` | Feedback foreign key; unique `feedback_id`; unique reference; classification/routing fields; optional handler; lifecycle timestamps and resolution. |
| `events` | Issue foreign key; event type, actor, description, JSON metadata, timestamp. |
| `notifications` | Issue and reporter foreign keys; channel, event type, message, status, optional delivery error, timestamp. |
| `conversations` | Optional reporter and unique feedback foreign keys; status, JSON turns, JSON collected fields, timestamps. |

### PostgreSQL compatibility observations

SQLAlchemy models already use portable types for the main schema, including `Boolean`, `DateTime`, and `JSON`, so retaining the ORM is lower risk than replacing it with raw SQL.

The migration must still explicitly verify:

- Integer primary-key generation and preservation of existing IDs.
- Timestamp timezone policy. The current model uses `DateTime` without an explicit timezone.
- JSON defaults and serialization for `events.metadata`, conversation turns, and collected fields.
- Foreign-key enforcement and delete/update behavior.
- Unique constraints on issue references, feedback-to-issue links, and conversation-to-feedback links.
- Case and whitespace behavior in application-level reporter lookup.
- Any SQLite-specific query behavior not visible in the model declarations.

## 5. Working-tree and change-management status

The repository was already dirty before this report. Existing changes include:

- Modified notification configuration, model, schema, API, and service files.
- New `app/notifications/` email adapter files.
- New email notification architecture documentation.
- New phase 11 email notification tests.
- Modified frontend pages and shared frontend types.
- Modified `.env.example`.
- Untracked `postgress_lift.md`.

These changes were not reverted or merged into this report. `production_prep.md` is an additional documentation file only. No application code, database file, environment file, or existing user change was modified by this report.

## 6. Recommended migration strategy

### Selected approach: retain SQLAlchemy, add controlled PostgreSQL support

Use the existing ORM and service layer, with a PostgreSQL SQLAlchemy URL supplied through `DATABASE_URL`. Add a PostgreSQL DBAPI driver and Alembic for versioned schema changes. Keep SQLite available only for local development and fast unit tests, with an explicit configuration path.

This is preferable because it:

- Changes the fewest business-logic files.
- Preserves existing models and API response contracts.
- Avoids a risky raw-SQL placeholder/row/transaction rewrite.
- Gives production a repeatable schema deployment process.
- Allows existing SQLite tests to remain fast while adding a real PostgreSQL test lane.

### Options not selected

- **Raw `psycopg` rewrite:** unnecessary and increases risk around result handling, placeholders, transactions, and connection cleanup.
- **New ORM or framework:** duplicates existing infrastructure and does not improve the immediate production path.
- **Keeping SQLite in production:** unsuitable for Render restarts and multiple workers because the local filesystem is not durable production storage.

## 7. Implementation plan

### Phase 1 — Configuration and driver

1. Add the selected PostgreSQL SQLAlchemy driver to `requirements.txt`.
2. Set production `DATABASE_URL` to the Neon connection string only through Render/Neon environment configuration.
3. Make engine options dialect-aware; do not pass SQLite-only `check_same_thread` options to PostgreSQL.
4. Fail clearly on an invalid or missing production database URL.
5. Keep the local SQLite default only for development, and document that it is not a production option.
6. Make CORS origins configurable, for example through a comma-separated `CORS_ORIGINS` setting, while retaining localhost defaults for development.

### Phase 2 — Schema migrations

1. Add Alembic configuration and an initial migration representing the seven current tables, constraints, indexes, and JSON columns.
2. Stop relying on uncontrolled startup `create_all()` in production.
3. Replace the SQLite-only schema patching behavior with versioned migrations.
4. Keep startup seeding idempotent, or move it to an explicit release/setup command so multiple workers cannot race to initialize production data.
5. Run migrations once as a Render release/pre-deploy command, not from every worker.

### Phase 3 — Data preservation decision

The existing SQLite records are demo data. They do not need to be transferred to Neon. The migration will preserve the **schema and database setup**, not the demo rows:

1. Leave `data/feedback_watch_tower.db` intact.
2. Create a clean PostgreSQL database from the initial Alembic migration.
3. Seed only the standard handler records through the idempotent setup process.
4. Do not copy demo reporters, feedback, issues, events, notifications, or conversations.
5. Keep the SQLite file as a local reference/rollback artifact.

If this data policy changes later, create a separately reviewed export/import procedure before moving any records.

### Phase 4 — Production safety

Before public deployment:

- Add authentication and authorization to administrative, handler, QA, and workflow actions.
- Add a database-backed readiness check separate from the cheap liveness endpoint.
- Avoid returning internal exception details.
- Audit request logging so feedback content, API keys, and email credentials are not logged.
- Set explicit production CORS origins and do not combine wildcard origins with credentials.
- Define timeouts and failure behavior for OpenRouter and email delivery.
- Confirm that notification failures do not leave partially committed workflow state.

## 8. Expected files to change in the implementation phase

The implementation changed:

- `requirements.txt`
- `app/core/config.py`
- `app/core/database.py`
- `app/main.py`
- `alembic.ini` and new Alembic configuration/migration files.
- `.env.example`.
- `docs/production/database-setup.md`.
- `production_prep.md`.

The notification files currently changed in the working tree should be reviewed separately and merged carefully with database changes.

## 9. Validation plan

### Already verified

- Full existing suite: **41 passed**.
- Clean temporary SQLite database migrated successfully to Alembic revision `20261014_0001`.
- SQLite engine behavior remains compatible, including the existing test fixtures.
- PostgreSQL-specific engine configuration is syntactically wired through `DATABASE_URL`.
- Core feedback, workflow, routing, notifications, conversations, QA, CLI, and email-notification tests are present.
- FastAPI startup path is exercised by the existing `TestClient` fixtures against SQLite.

### Not yet verified

- PostgreSQL driver installation and connection.
- Neon schema creation and connectivity.
- Alembic upgrade behavior on PostgreSQL.
- PostgreSQL-backed API workflows.
- PostgreSQL JSON, timestamp, uniqueness, and foreign-key behavior.
- Render build/start/release commands.
- Vercel-to-Render CORS behavior.
- OpenRouter and Sender email end-to-end delivery.
- Authentication/authorization, because those controls are not currently implemented.

### Required PostgreSQL test matrix

Run against an isolated local PostgreSQL database or a dedicated non-production Neon branch:

1. Apply migrations from an empty database.
2. Start FastAPI with the PostgreSQL `DATABASE_URL`.
3. Submit, retrieve, process, and route feedback.
4. Execute every issue lifecycle transition.
5. Verify event and notification persistence.
6. Create and submit a conversation.
7. Verify invalid input and transaction rollback behavior.
8. Verify foreign keys, unique constraints, JSON values, and timestamps.
9. Run the complete regression suite against PostgreSQL.
10. Separately run the SQLite suite to ensure local development remains intact.

## 10. Deployment readiness

### Backend runtime

Current local command:

```text
uvicorn app.main:app --reload
```

The production command should omit `--reload`, bind to `0.0.0.0`, and use Render's `PORT` environment variable. The exact Render command must be tested before deployment.

### Environment variables currently represented

| Variable | Purpose | Production status |
|---|---|---|
| `APP_ENV` | Environment label | Must be set to production value. |
| `DATABASE_URL` | SQLAlchemy database URL | Must point to Neon; not yet verified. |
| `OPENROUTER_API_KEY` | Optional LLM provider credential | Secret; external call not verified. |
| `OPENROUTER_MODEL` | LLM model selection | Must be reviewed for production cost/reliability. |
| `SENDER_API_KEY` | Email provider credential | Secret; delivery not verified end to end. |
| `SENDER_FROM_EMAIL` | Email sender address | Must be configured and provider-verified. |
| `SENDER_FROM_NAME` | Email display name | Configurable. |
| `SENDER_ENABLED` | Email delivery feature flag | Keep disabled until provider configuration is verified. |
| `SENDER_API_URL` | Email provider endpoint | Must be reviewed and timeout-tested. |
| `FRONTEND_BASE_URL` | Links from notifications to frontend | Must be the deployed Vercel URL. |
| `CORS_ORIGINS` | **Required addition** for explicit frontend origins | Not implemented yet. |

Never commit actual values for database URLs, API keys, or email credentials.

### Health checks

`GET /health` currently returns `{"status": "ok"}` without checking the database. It is appropriate as a liveness endpoint only. Add a separate readiness check that performs a lightweight database query and returns a non-success status when the database is unavailable. Do not expose connection strings or stack traces.

### CORS

Current CORS allows only:

- `http://localhost:3000`
- `http://127.0.0.1:3000`

This must become environment-configurable before the Vercel frontend can call a deployed Render backend. Keep explicit origins and credentials policy; do not use `*` with credentials.

## 11. Rollback strategy

### Application rollback

- Deploy the previous application revision if a release fails.
- Keep migrations backward-compatible during releases where possible.
- Do not run destructive downgrade migrations automatically in a production incident.

### Database rollback

- Take a Neon backup/branch before applying a material schema change.
- For the initial migration, rollback is a deployment rollback plus restoring/branching the database if data was written under an incompatible schema.
- Keep the original SQLite database and migration/export artifacts untouched until acceptance.
- Treat data repair as an explicit, reviewed operation; never delete or recreate unknown production tables as an ad hoc fix.

## 12. Prioritized action list

### P0 — Required before public deployment

- Add PostgreSQL driver and verify a real PostgreSQL connection.
- Add and test Alembic migrations.
- Replace production startup `create_all()` with an explicit migration release step.
- Configure Render `PORT`, start command, secrets, and Neon `DATABASE_URL`.
- Make CORS configurable and add the deployed frontend origin.
- Implement authentication/authorization for non-public operations.
- Add database readiness checks.
- Verify transaction boundaries and external notification failure behavior.

### P1 — Required for a reliable demo

- Run the full regression suite against PostgreSQL.
- Initialize Neon with a clean schema; no migration of the current demo rows is required.
- Test OpenRouter and email integrations with non-production credentials.
- Add structured, redacted production logging.
- Add migration and deployment documentation.
- Resolve or track the current FastAPI and httpx deprecation warnings.

### P2 — Follow-up hardening

- Add CI checks for tests, migrations, and dependency vulnerabilities.
- Add request IDs, metrics, and error monitoring.
- Add pagination and query limits to list endpoints.
- Add rate limiting and abuse protection.
- Define data retention, privacy, and audit-log policies.
- Replace deprecated FastAPI startup events with lifespan handling.

## 13. Implementation status and final status

### Completed in this change

- Added `psycopg[binary]` and Alembic dependencies.
- Added dialect-aware SQLAlchemy engine options so SQLite receives `check_same_thread` while PostgreSQL does not.
- Added configurable, normalized CORS origins through `CORS_ORIGINS`.
- Added an initial Alembic migration for all seven ORM tables, constraints, indexes, and JSON columns.
- Kept local SQLite startup initialization for development/tests.
- Disabled automatic schema creation and handler seeding during production application startup.
- Added `python -m app.seed` for explicit, idempotent handler setup after production migrations.
- Added [database-setup.md](docs/production/database-setup.md) with clean-database setup and validation commands.
- Preserved the existing SQLite demo database; no demo rows were copied.

### Not yet verified

- No PostgreSQL server or isolated Neon branch was available in this environment, so PostgreSQL migration/application tests were not run.
- Render release/start commands and Vercel-to-Render CORS were not tested.
- Authentication/authorization remains a separate production blocker.

**The project is not yet ready for public production deployment.** It is ready for the next validation phase: apply the migration to an isolated PostgreSQL database, run the application workflow tests against it, seed handlers explicitly, and then validate Render/Neon connectivity.

The current evidence supports the following narrower conclusion:

> The existing SQLite-backed application remains a functioning tested demonstrator with 41 passing tests. PostgreSQL support and schema migration are implemented and validated against a clean temporary SQLite migration database, but PostgreSQL connectivity, Neon, Render, Vercel integration, authentication, and full production readiness remain unverified or incomplete.
