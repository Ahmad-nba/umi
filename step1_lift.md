# Step 1 Lift Verification Report

**Date:** 2026-10-14  
**Scope:** Neon connectivity, database configuration, initial Alembic migration, production startup behavior, and test evidence  
**Repository:** `Ahmad-nba/umi`

## Executive result

The first implementation step is complete for configuration, Neon connectivity, and schema management:

- The database is selected through `DATABASE_URL`.
- SQLite-specific `check_same_thread` options are applied only to SQLite.
- PostgreSQL connections use SQLAlchemy with the Psycopg 3 driver and connection pre-ping.
- The initial Alembic migration creates all seven ORM tables and their relationships.
- Production startup skips automatic schema creation and handler seeding.
- The original 41-test SQLite baseline still passes.
- The migration was applied successfully to a clean temporary SQLite database.
- A real connection to the configured Neon PostgreSQL database succeeded.
- The Neon database was empty before migration and now contains the expected schema at revision `20261014_0001`.

The configured Neon database was available and accepted the migration. Full application workflow testing against PostgreSQL remains pending because the configured target was not confirmed as a disposable integration-test database.

## 1. Database configuration

### Configuration source

The application uses the existing Pydantic settings layer in `app/core/config.py`.

The relevant behavior is:

```text
DATABASE_URL=<configured SQLAlchemy URL>
```

If `DATABASE_URL` is absent, local development falls back to:

```text
sqlite:///./data/feedback_watch_tower.db
```

Production should set an explicit PostgreSQL URL, for example a Neon-provided SQLAlchemy URL using the Psycopg dialect. Production does not silently fall back to SQLite as a deployment strategy.

The configured URL used the generic `postgresql://` scheme. The first connection attempt showed that SQLAlchemy then selected the absent `psycopg2` driver. The shared database and Alembic configuration now normalize that scheme to `postgresql+psycopg://`, selecting the installed Psycopg 3 driver without changing the supplied credentials.

### Engine selection

`app/core/database.py` selects the URL from the environment/settings and builds the SQLAlchemy engine.

The implementation is dialect-aware:

```python
connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
return create_engine(
    url,
    connect_args=connect_args,
    pool_pre_ping=not url.startswith("sqlite"),
)
```

This means:

| Database URL | `check_same_thread` | `pool_pre_ping` |
|---|---:|---:|
| `sqlite:///...` | Applied | Disabled |
| `postgresql+psycopg://...` | Not applied | Enabled |

The SQLite-specific option is therefore not passed to PostgreSQL. PostgreSQL uses normal SQLAlchemy pooling and stale-connection detection.

### Session lifecycle

The application continues to use synchronous SQLAlchemy sessions:

- `SessionLocal` creates request/session instances.
- `get_db()` yields a session to the API dependency.
- The session is closed in a `finally` block.
- Existing test fixtures can still replace the engine/session with an in-memory SQLite engine.

The application was not unnecessarily converted to asynchronous database access.

### CORS configuration

Allowed origins are now read from `CORS_ORIGINS` and normalized by trimming whitespace and trailing slashes. Local defaults remain:

```text
http://localhost:3000,http://127.0.0.1:3000
```

Production must provide explicit Vercel origin(s). Wildcard origins are rejected when `APP_ENV=production`.

## 2. Initial Alembic migration

The migration is:

[20261014_0001_initial_schema.py](C:/Users/Ashlink/dev/projects/umi-backup/alembic/versions/20261014_0001_initial_schema.py)

It is configured through:

- [alembic.ini](C:/Users/Ashlink/dev/projects/umi-backup/alembic.ini)
- [alembic/env.py](C:/Users/Ashlink/dev/projects/umi-backup/alembic/env.py)

The Alembic environment imports the ORM model modules and uses `Base.metadata` as the migration metadata. Database credentials are read from configuration/environment and are not embedded in migration files.

### Tables created

The initial migration creates the seven existing ORM tables:

1. `handlers`
2. `reporters`
3. `feedbacks`
4. `issues`
5. `events`
6. `notifications`
7. `conversations`

### Constraints and relationships

The migration preserves the model relationships:

| Table | Relationships and constraints |
|---|---|
| `handlers` | Integer primary key; indexed ID; handler fields; non-null `active` boolean. |
| `reporters` | Integer primary key; indexed ID; required name/contact/timestamp. |
| `feedbacks` | Foreign key to `reporters.id`; required content/channel/status/timestamp; nullable context. |
| `issues` | Foreign keys to `feedbacks.id` and nullable `handlers.id`; unique `feedback_id`; unique `reference`; lifecycle and classification fields. |
| `events` | Foreign key to `issues.id`; indexed `issue_id`; JSON `metadata`; event/timestamp fields. |
| `notifications` | Foreign keys to `issues.id` and `reporters.id`; indexed `issue_id`; delivery status/error fields. |
| `conversations` | Nullable foreign keys to `reporters.id` and `feedbacks.id`; unique `feedback_id`; JSON `turns` and `collected_fields`. |

The migration also creates the indexes declared by the ORM models, including primary-key indexes and the explicit event/notification issue indexes.

### Clean migration verification

The migration was applied to the configured Neon database with:

```text
alembic upgrade head
alembic current
```

Observed result:

```text
Context impl PostgresqlImpl.
Running upgrade  -> 20261014_0001, create the initial UMI schema
20261014_0001 (head)
```

Before applying the migration, a read-only inspection found no tables in the target schema and no rows to preserve. The existing local demo database was not used or modified.

### Direct Neon connectivity evidence

The application engine executed harmless identity queries successfully:

```text
backend: PostgreSQL
driver_selected: psycopg
sslmode_required: True
postgres_query_succeeded: True
version_prefix: PostgreSQL 18.6 (c021049) on aarch64-unknown-linux-gnu
database: neondb
schema: public
server_version: 18.6 (c021049)
tables: (none)          # before migration
```

Credentials and the complete connection URL were not written to this report.

### Neon schema verification

After migration, read-only catalog inspection confirmed:

```text
expected_tables_present: True
tables: conversations,events,feedbacks,handlers,issues,notifications,reporters
migration_revision: 20261014_0001
constraint_count: 64
index_count: 19
```

The verified columns include PostgreSQL `integer`, `character varying`, `text`, `boolean`, `timestamp without time zone`, and `json` types matching the ORM models. Foreign keys, primary keys, unique constraints, not-null constraints, and the expected issue/event/notification indexes were present.

### Production schema policy

Production schema creation is now intended to run explicitly:

```powershell
alembic upgrade head
```

This should run once as a Render release/pre-deploy command, not independently from every application worker.

## 3. Production startup and `create_all()`

The `init_db()` function still contains `Base.metadata.create_all()` for local SQLite compatibility. That behavior has not been removed from development because the existing local workflow and test assumptions depend on it.

However, `app/main.py` now gates startup initialization:

```python
@app.on_event("startup")
def startup_event() -> None:
    if get_settings().app_env.lower() == "production":
        return
    database.init_db()
    ...
```

Therefore:

- `APP_ENV=development`: startup may initialize the local SQLite schema and seed handlers.
- `APP_ENV=production`: startup does not call `database.init_db()`, does not call `create_all()`, and does not seed handlers.
- Production schema setup is performed explicitly with Alembic.
- Production handler setup is performed explicitly with:

```powershell
umienv\Scripts\python.exe -m app.seed
```

No demo rows are migrated. The existing SQLite database remains a local reference and is preserved.

## 4. Test results

### Existing baseline

The original full test suite was rerun after the changes:

```powershell
umienv\Scripts\python.exe -m pytest
```

Result:

```text
41 passed, 4 warnings in 3.16s
```

The warnings are existing dependency/framework deprecations involving Starlette/httpx and FastAPI startup events. They did not cause test failures.

The suite covers feedback, classification, issue routing, workflow lifecycle, notifications, conversations, QA, CLI behavior, and email notification behavior. The tests use in-memory SQLite, so they establish SQLite regression compatibility rather than PostgreSQL compatibility.

### PostgreSQL evidence

The following PostgreSQL workflow checks remain pending:

- `alembic upgrade head` against PostgreSQL.
- PostgreSQL table/constraint inspection.
- FastAPI startup with a PostgreSQL `DATABASE_URL`.
- Feedback submission and retrieval against PostgreSQL.
- Processing, routing, lifecycle, event, notification, and conversation workflows against PostgreSQL.
- PostgreSQL JSON, foreign-key, unique-constraint, timestamp, and rollback behavior.

No PostgreSQL application-workflow success is being claimed yet.

The reason is data safety: the configured Neon target was empty, but it was not confirmed to be a disposable integration-test database. The migration itself was safe on the empty target; seeding handlers or inserting workflow test records requires an explicitly isolated test database/branch.

### Production-mode startup check

With `APP_ENV=production`, the application was started through FastAPI's test client using the configured Neon URL. The health endpoint returned:

```text
production_startup_health_status: 200
production_startup_health_body: {'status': 'ok'}
engine_dialect: postgresql
engine_driver: psycopg
```

This confirms production startup does not call the local `create_all()` path. It is a liveness check only and does not replace the pending workflow integration tests.

## 5. Next validation step

Use an isolated local PostgreSQL database or a dedicated non-production Neon branch. Do not use production credentials or data.

Example workflow:

```powershell
$env:APP_ENV = "production"
$env:DATABASE_URL = "postgresql+psycopg://<user>:<password>@<host>:<port>/<database>"

alembic upgrade head
alembic current
umienv\Scripts\python.exe -m app.seed
umienv\Scripts\python.exe -m pytest
```

The PostgreSQL test run should be treated as the next gate. Until it passes, the migration is implemented but not fully validated.

## 6. Step 1 conclusion

### Verified

- Database selection is configuration-driven.
- SQLite-specific engine options are not passed to PostgreSQL.
- Psycopg 3 and Alembic dependencies are declared and installed in the project environment.
- The initial migration defines all seven tables and their constraints/relationships.
- A real Neon connection succeeds with PostgreSQL 18.6.
- A clean Neon migration reaches revision `20261014_0001`.
- Neon schema catalog verification confirms all seven tables, 64 constraints, and 19 indexes.
- Production startup bypasses `create_all()` and automatic seed work.
- The original 41 tests continue to pass.
- The demo SQLite database remains intact.

### Pending

- PostgreSQL workflow integration tests using a dedicated disposable database or Neon branch.
- Safe handler seeding verification on that isolated test target.
- Render release/start command validation.
- Vercel-to-Render CORS validation.

**Decision: CONDITIONAL PASS — Connectivity and migration work.** The Neon connection, migration, schema, production startup, and SQLite regression checks are verified. Full PostgreSQL application workflows must be run against an explicitly isolated test database before declaring PostgreSQL readiness or seeding/testing the configured target.
