# Full Backend Lift Report — Render Readiness

**Date:** 2026-10-14  
**Target:** Render Web Service running the FastAPI backend  
**Database:** Already-migrated Neon PostgreSQL database  
**Deployment status:** **PREPARED, NOT DEPLOYED**

## Executive result

The repository is ready for the Render operator to configure a Python Web Service with the commands below:

**Build command**

```bash
pip install -r requirements.txt
```

**Start command**

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Health check path**

```text
/ready
```

The ASGI import path is verified as `app.main:app`. The build command was executed successfully in the project environment, and the production-shaped Uvicorn command was smoke-tested locally. Both `/health` and `/ready` returned HTTP 200, including a live database readiness query.

No Render deployment was performed because no authenticated Render deployment tool or service URL was available. The final public URL will be assigned by Render after the service is created.

## 1. Repository and runtime verification

### Application entry point

The application is exposed by:

```text
app.main:app
```

`app/main.py` creates the FastAPI application and registers the feedback, issue, workflow, notification, QA, conversation, and health routers.

### Production dependencies

[requirements.txt](requirements.txt) contains the required runtime packages:

- FastAPI
- Uvicorn
- SQLAlchemy
- `psycopg[binary]`
- Alembic
- Pydantic and `pydantic-settings`

The command below completed successfully:

```powershell
umienv\Scripts\python.exe -m pip install -r requirements.txt
```

All required packages were already installed in the active environment. Render should run the equivalent Linux command:

```bash
pip install -r requirements.txt
```

### Repository state

The repository was clean at the start of this phase. No unrelated changes were present, and no Render deployment files, Dockerfile, or Procfile were required for the standard Python Web Service configuration.

## 2. Render service configuration

Create a **Web Service** using the repository and intended production branch.

| Render setting | Value |
|---|---|
| Runtime | Python 3 |
| Root directory | Repository root |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/ready` |
| Auto-deploy | Recommended after the first successful manual verification |

Do not add `--reload` to the start command. Do not use a fixed port. Render supplies `PORT`, and the service must bind to `0.0.0.0`.

Do not run Alembic migrations from every web-service startup. The Neon database has already been migrated to revision `20261014_0001`. Future schema changes should be applied once through a reviewed Render release/pre-deploy job or a controlled operator command before the web service is restarted.

## 3. Render environment variables

Add these through Render's secure environment-variable UI. Do not paste secret values into source control, `render.yaml`, or this report.

| Variable | Required for startup | Purpose |
|---|---:|---|
| `APP_ENV` | Yes | Set to `production`; disables startup `create_all()` and automatic handler seeding. |
| `DATABASE_URL` | Yes | Neon PostgreSQL connection URL. Use the supplied Neon value through Render's secret configuration. |
| `CORS_ORIGINS` | Yes before browser integration | Comma-separated, explicit frontend origins. Add the real Vercel URL after deployment; do not use `*`. |
| `FRONTEND_BASE_URL` | Recommended | Public frontend URL used in notification links. Use the actual Vercel URL when available. |
| `OPENROUTER_API_KEY` | Optional | Enables the external LLM classifier. If absent, the application uses its existing deterministic fallback. |
| `OPENROUTER_MODEL` | Optional | LLM model selection; defaults to `openrouter/auto`. |
| `SENDER_ENABLED` | Optional | Keep `false` until email delivery is independently verified. |
| `SENDER_API_KEY` | Required when email enabled | Sender provider credential. |
| `SENDER_FROM_EMAIL` | Required when email enabled | Provider-verified sender address. |
| `SENDER_FROM_NAME` | Optional | Email display name; defaults to `UMI Feedback Watch Tower`. |
| `SENDER_API_URL` | Optional | Sender API endpoint; defaults to the configured Sender endpoint. |

The committed [.env.example](.env.example) contains placeholders/defaults only. The local `.env` file is ignored by Git and must not be uploaded to Render.

## 4. Database and startup behavior

### PostgreSQL selection

The application reads `DATABASE_URL` through `pydantic-settings`. Generic `postgresql://` URLs are normalized to `postgresql+psycopg://`, selecting the installed Psycopg 3 driver.

SQLite-only options are applied only for SQLite:

```python
connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
```

Production therefore does not require a local SQLite file and does not pass `check_same_thread` to PostgreSQL.

### Production startup

When `APP_ENV=production`, startup returns before calling the development initializer. It does not:

- Call `Base.metadata.create_all()`.
- Apply SQLite compatibility `ALTER TABLE` statements.
- Seed handler records.
- Seed demo data.
- Reset or delete database contents.

Schema management remains an explicit Alembic operation. The current Neon database was already verified at revision `20261014_0001`.

Because the production database is intentionally not seeded with demo data, the service can start and pass health checks, but issue routing may require handler records before the full workflow is used. Do not seed the configured database during this deployment preparation phase.

## 5. Health checks

### Liveness

```text
GET /health
```

Returns:

```json
{"status": "ok"}
```

This endpoint does not query the database and is suitable for basic process liveness.

### Readiness

```text
GET /ready
```

The readiness endpoint uses the configured SQLAlchemy engine and executes `SELECT 1`. It returns:

```json
{"status": "ready"}
```

with HTTP 200 when the database is reachable. Database errors return HTTP 503 with the non-sensitive response:

```json
{"detail": "database unavailable"}
```

It does not run migrations, seed records, modify tables, expose credentials, or return connection details. Configure Render's health check path as `/ready`.

## 6. Local production-shaped verification

The exact Render-style server command was run locally with a test port:

```powershell
$env:APP_ENV = "production"
$env:PORT = "8765"
umienv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port $env:PORT
```

The smoke requests returned:

```text
GET /health -> 200 {"status":"ok"}
GET /ready  -> 200 {"status":"ready"}
```

The running engine reported:

```text
engine_dialect: postgresql
engine_driver: psycopg
```

This verifies the application can run in production mode against the configured PostgreSQL database without startup schema creation or seed work. It is not a substitute for a deployed Render URL.

## 7. Regression test results

The existing isolated SQLite suite was run independently:

```powershell
umienv\Scripts\python.exe -m pytest
```

Result:

```text
41 passed, 4 warnings in 3.55s
```

Warnings are existing Starlette/httpx and FastAPI startup-event deprecations. No tests failed.

The Neon schema and connection were previously verified separately, but no write-oriented workflow tests were run against the configured database in this phase. The database was intentionally not seeded or modified with test records.

## 8. Route-level security assessment

The backend currently has no authentication or authorization dependency on its API routers. CORS does not protect these routes. This is a blocker for exposing mutation and sensitive read endpoints publicly.

| Method/path family | Operation | Current protection | Public exposure risk |
|---|---|---|---|
| `GET /health`, `GET /ready` | Liveness/readiness | None | Intended public health checks; responses are non-sensitive. |
| `POST/GET /feedback` | Submit/list feedback | None | Unauthenticated submissions and disclosure of reporter/feedback data. |
| `GET /feedback/{id}` | Read feedback | None | Direct access to submitted content and reporter-linked data. |
| `POST /feedback/{id}/process` | Classify feedback | None | Unauthenticated workflow mutation and possible external LLM use. |
| `POST /feedback/{id}/route` | Route feedback | None | Unauthenticated issue creation/routing mutation. |
| `GET /issues`, `GET /issues/{id}` | Read issues | None | Disclosure of operational issue data. |
| `POST /issues/{id}/acknowledge`, `/start`, `/complete`, `/confirm`, `/close` | Change lifecycle | None | Anyone could change workflow state. |
| `GET /issues/{id}/notifications` | Read notifications | None | Disclosure of reporter notification content. |
| `GET /qa/dashboard`, `GET /qa/issues/{id}` | QA management views | None | Disclosure of operational and reporter data. |
| `POST/GET /conversations` | Create/read conversations | None | Unauthenticated data creation and disclosure. |
| `POST /conversations/{id}/messages` | Add conversation data | None | Unauthenticated mutation of conversation records. |
| `POST /conversations/{id}/submit` | Convert conversation to feedback | None | Unauthenticated feedback creation and workflow trigger. |

No authentication was invented in this deployment preparation because the intended identity model and frontend authentication flow are not defined. The service can be made technically reachable, but it should not be treated as safely public until the route protection decision is resolved.

## 9. What the operator should do in Render

1. Create a Render Web Service from the intended repository/branch.
2. Set the build command to:
   ```text
   pip install -r requirements.txt
   ```
3. Set the start command to:
   ```text
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Set the health check path to:
   ```text
   /ready
   ```
5. Add `APP_ENV=production`.
6. Add the Neon `DATABASE_URL` through Render's secret environment configuration.
7. Add explicit `CORS_ORIGINS`; use the actual Vercel origin once the frontend is deployed.
8. Add optional LLM/email variables only when those services are ready. Keep `SENDER_ENABLED=false` initially.
9. Deploy without running a database reset or demo-data seed.
10. After Render assigns a public URL, verify:
    - `GET https://<render-service>.onrender.com/health`
    - `GET https://<render-service>.onrender.com/ready`
    - `GET https://<render-service>.onrender.com/docs`
11. Inspect Render startup logs for dependency, port, configuration, or database errors.

Do not run write-path smoke tests against the Neon production database merely to prove that the service is reachable.

## 10. Remaining blockers

### Technical readiness

- **Resolved:** Render build command.
- **Resolved:** Render start command and `0.0.0.0` binding.
- **Resolved:** ASGI import path.
- **Resolved:** PostgreSQL driver dependency.
- **Resolved:** Production startup does not create tables or seed data.
- **Resolved:** Database readiness endpoint.
- **Resolved:** Local production-shaped startup smoke test.
- **Pending:** Real Render deployment and public URL smoke test.

### Public exposure readiness

- **Blocker:** API routes are unauthenticated and include sensitive reads and state-changing operations.
- **Pending:** The intended authentication/authorization model and frontend identity flow.
- **Pending:** Actual Vercel origin for production CORS.
- **Known limitation:** No handler seed records exist in the intentionally clean production database; routing workflows may need an explicitly approved setup/seed action later.

## 11. Final deployment decision

**PREPARED, NOT DEPLOYED**

The repository is configured for Render and the exact build/start commands have been verified locally. Once the Render environment variables are entered, the service should be able to start and expose its health/readiness endpoints at the Render public URL.

This report does **not** claim that a Render service has been deployed. It also does not claim that the current unauthenticated API is safe for unrestricted public use. Before directing real users to mutation or data endpoints, add the agreed authentication/authorization boundary and configure the actual frontend origin.

