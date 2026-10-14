# Production CORS Incident Report

## Final status

**FIX IMPLEMENTED, BROWSER VERIFICATION PENDING**

The backend source now includes the configured `FRONTEND_BASE_URL` in the
CORS allowlist in addition to the comma-separated `CORS_ORIGINS` values. The
backend must be redeployed with the actual deployed frontend origin configured
in Render before the production browser flow can be verified.

## Root cause

The backend is a FastAPI application served by Uvicorn from
`app.main:app`. It registers Starlette `CORSMiddleware` through
`app.add_middleware`, before requests reach application routes. There is no
custom `OPTIONS /feedback` route and no feedback dependency that handles
preflight requests.

The frontend API client in `web/lib/api.ts` sends:

- `POST /feedback`
- JSON request data
- `Content-Type: application/json`
- no authentication header
- no credentialed browser session

Because a cross-origin JSON POST is not a CORS “simple request”, the browser
must first send:

```text
OPTIONS /feedback
Origin: <frontend-origin>
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
```

The live diagnostic evidence distinguishes the failure:

| Origin | Preflight result |
|---|---|
| `http://localhost:3000` | HTTP 200 |
| `http://127.0.0.1:3000` | HTTP 200 |
| An unapproved production origin | HTTP 400 |

Successful responses included a matching
`Access-Control-Allow-Origin`, permitted `POST` in
`Access-Control-Allow-Methods`, and permitted `content-type` in
`Access-Control-Allow-Headers`. The rejected response was therefore produced
by CORS origin validation, not by the feedback route, an invalid HTTP method,
an unsupported header, authentication, or middleware ordering.

The production frontend hostname was not present in the repository or
available from the diagnostic information. The most likely deployed
configuration was therefore either a missing Render `CORS_ORIGINS` value,
leaving only the local defaults, or a value that omitted the actual frontend
origin.

## Files changed

### `app/core/config.py`

`cors_origin_list` now combines:

1. Explicit origins from `CORS_ORIGINS`.
2. The configured `FRONTEND_BASE_URL`.

Trailing slashes continue to be normalized, blank entries are ignored, and the
existing production wildcard rejection remains in effect. No route, database
schema, authentication, or feedback behavior was changed.

## Production CORS configuration

Set the exact Vercel production origin in Render. For example, if the browser
address bar shows `https://umi.example.com`, configure:

```text
FRONTEND_BASE_URL=https://umi.example.com
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

If the frontend is served from a Vercel hostname instead, use that exact
hostname, including `https://` and excluding a trailing slash. Do not use
`*`, and do not include paths or query strings.

The frontend sends no credentials, so `allow_credentials=True` does not grant
the frontend authentication. Existing application routes remain unauthenticated
and require a separate security decision.

## Verification results

| Check | Result | Evidence |
|---|---|---|
| Backend framework and entry point inspected | PASS | FastAPI application at `app.main:app` |
| CORS middleware and order inspected | PASS | Starlette `CORSMiddleware` handles preflight before route processing |
| Frontend request inspected | PASS | `POST /feedback`, JSON body, `content-type`, no auth header |
| Approved localhost preflight | PASS | Live HTTP 200 with matching origin and allowed POST/header |
| Unapproved-origin diagnostic | PASS | Live HTTP 400, confirming origin allowlist rejection |
| Configured frontend-origin simulation | PASS | Local production-mode simulation returned HTTP 200 |
| `Access-Control-Allow-Origin` | PASS in simulation | Matched configured frontend origin |
| `Access-Control-Allow-Methods` | PASS in simulation | Included `POST` |
| `Access-Control-Allow-Headers` | PASS in simulation | Included `content-type` |
| Existing regression suite | PASS | 41 tests passed, 4 existing deprecation warnings |
| Actual production frontend origin | NOT RUN | Exact deployed origin was not available |
| Post-redeploy live preflight | NOT RUN | Requires Render environment update and redeployment |
| Browser feedback submission | NOT RUN | Requires the deployed frontend URL and browser verification |
| Actual feedback write in production | NOT RUN | Intentionally not performed for safety |

The local preflight simulation returned:

```text
status: 200
allow_origin: https://frontend.example.com
allow_methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
allow_headers: content-type
```

The placeholder origin above was used only for local configuration testing; it
is not asserted to be the real production frontend origin.

## Deployment requirements

1. Confirm the exact public frontend origin from Vercel or the browser address
   bar.
2. Set `FRONTEND_BASE_URL` in the Render backend to that origin.
3. Preserve local origins in `CORS_ORIGINS` if local development is still
   needed.
4. Redeploy the backend so the source change and environment configuration are
   active.
5. Repeat the preflight diagnostic with the exact origin:

```bash
curl -i -X OPTIONS "https://umifbt.onrender.com/feedback" \
  -H "Origin: https://YOUR-ACTUAL-FRONTEND-DOMAIN" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"
```

The expected result is HTTP 200 or 204 with:

```text
Access-Control-Allow-Origin: https://YOUR-ACTUAL-FRONTEND-DOMAIN
Access-Control-Allow-Methods: ... POST ...
Access-Control-Allow-Headers: ... content-type ...
```

No database migration, schema change, seed, production write, or automatic
deployment was performed for this incident.
