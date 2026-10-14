# Frontend Lift Report — Production Backend Integration

**Date:** 2026-10-14  
**Frontend:** Next.js 16.3.6 under `web/`  
**Backend origin:** `https://umifbt.onrender.com`  
**Deployment status:** **READY TO DEPLOY WITH DOCUMENTED LIMITATIONS**

## A. Repository findings

### Frontend architecture

The frontend is a Next.js App Router application with:

- React 19.
- TypeScript.
- Tailwind CSS.
- `next build` for production builds.
- `next start` for a self-hosted Node deployment.
- Static and dynamic App Router pages for reporter, handler, QA, issue, and feedback views.

The frontend package root is `web/`, with its own `package.json` and `package-lock.json`. The repository root is not a Node package.

### Backend communication

All browser API calls are centralized in:

[web/lib/api.ts](web/lib/api.ts)

The client uses `fetch()` and composes the configured backend origin with paths including:

- `/feedback`
- `/feedback/{id}`
- `/feedback/{id}/route`
- `/issues`
- `/issues/{id}`
- `/issues/{id}/notifications`
- `/qa/dashboard`
- `/qa/issues/{id}`
- `/issues/{id}/{action}`

Request failures are converted to user-visible errors rather than being treated as successful operations.

### Existing configuration before this lift

The client already used `NEXT_PUBLIC_API_URL`, but its fallback was:

```text
http://127.0.0.1:8000
```

The configured production origin is now documented through `web/.env.example`.

## B. Changes implemented

### `web/lib/api.ts`

The configured backend origin is now normalized by removing trailing slashes:

```typescript
const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "");
```

This prevents malformed URLs such as:

```text
https://umifbt.onrender.com//feedback
```

Local development remains supported through the existing localhost fallback or a local `.env.local` value.

### `web/.env.example`

Added:

```text
NEXT_PUBLIC_API_URL=https://umifbt.onrender.com
```

This is a public browser configuration value, not a secret. Database credentials, API keys, and private backend configuration must never be placed in frontend environment variables.

No backend routes, database schema, authentication behavior, or frontend business workflows were redesigned.

## C. Backend integration

### Live backend checks

Safe read-only requests to the deployed backend succeeded:

```text
GET https://umifbt.onrender.com/health
-> 200 {"status":"ok"}

GET https://umifbt.onrender.com/ready
-> 200 {"status":"ready"}
```

The backend readiness response confirms that the deployed service can reach its configured database.

### Endpoint compatibility

The frontend API client paths match the registered FastAPI routes for feedback, issues, workflow, notifications, QA, and dashboard operations. No obsolete backend origin or alternate API client was found in the frontend production code.

### CORS

The backend uses an explicit `CORS_ORIGINS` allowlist and does not use wildcard credentials. A preflight probe from an unrecognized origin returned HTTP 400 with no `Access-Control-Allow-Origin` header, confirming that the allowlist is enforced.

The actual Vercel deployment origin does not exist yet, so browser CORS compatibility with the final frontend URL cannot be verified. After Vercel assigns the production domain, add that exact origin to the backend's Render `CORS_ORIGINS` variable and redeploy the backend if necessary.

CORS is not authentication. The backend API routes remain unauthenticated, including sensitive read and mutation operations. This is documented as a limitation below.

## D. Validation results

| Check | Result | Evidence |
|---|---|---|
| Frontend dependency location | PASS | `web/package.json` and `web/package-lock.json` found. |
| Production backend URL configuration | PASS | `web/.env.example` contains `NEXT_PUBLIC_API_URL=https://umifbt.onrender.com`. |
| API URL normalization | PASS | `web/lib/api.ts` strips trailing slashes. |
| Live backend liveness | PASS | `/health` returned HTTP 200. |
| Live backend readiness | PASS | `/ready` returned HTTP 200. |
| Frontend lint | PASS | `npm run lint` completed successfully from `web/`. |
| Production build | PASS | `NEXT_PUBLIC_API_URL=https://umifbt.onrender.com npm run build` completed successfully. |
| TypeScript build check | PASS | Next.js build completed its TypeScript phase successfully. |
| Localhost/obsolete URL audit | PASS with local fallback | Only the intentional local fallback remains in `web/lib/api.ts`; production builds use `NEXT_PUBLIC_API_URL`. |
| Final Vercel-origin CORS check | NOT RUN | The final Vercel origin has not been created. |
| Real browser end-to-end flow | NOT RUN | Requires the deployed frontend URL and configured CORS origin. |

### Production build output

The successful build generated these application routes:

```text
/
/_not-found
/handler
/handler/tasks/[id]
/qa
/qa/issues/[id]
/reporter
/reporter/feedback
/reporter/feedback/[id]
```

## E. Render/Vercel hosting configuration

The frontend is a Next.js application, not a static export. The recommended independent deployment target is Vercel.

### Recommended Vercel settings

| Setting | Value |
|---|---|
| Framework preset | Next.js |
| Root directory | `web` |
| Install command | `npm ci` |
| Build command | `npm run build` |
| Start command | Not required on Vercel |
| Production environment variable | `NEXT_PUBLIC_API_URL=https://umifbt.onrender.com` |

The committed `web/package-lock.json` should be used by `npm ci`. Do not place backend secrets in Vercel environment variables.

### If using Render for the frontend instead

Use a Render Web Service with:

```text
Root directory: web
Build command: npm ci && npm run build
Start command: npm run start -- --hostname 0.0.0.0 --port $PORT
```

For a Next.js server deployment, configure the service as a Node environment. Do not configure `dist` or `build` as a static publish directory; this project uses Next.js server rendering for dynamic routes.

Vercel is preferred for this repository because the app is already a standard Next.js project and does not require a custom Render frontend service.

## F. Required deployment steps

### Vercel

1. Import the repository into Vercel.
2. Set the project root directory to `web`.
3. Set `NEXT_PUBLIC_API_URL` to:
   ```text
   https://umifbt.onrender.com
   ```
4. Deploy.
5. Open the assigned Vercel URL and exercise:
   - Reporter landing page.
   - Feedback submission page.
   - QA dashboard.
   - Handler issue queue.
6. Record the final Vercel origin.

### Render backend CORS update

After the Vercel domain is known, set the Render backend variable:

```text
CORS_ORIGINS=<existing-local-origins>,https://<actual-vercel-domain>
```

Use the exact scheme and host, without a trailing slash. Keep `allow_credentials` behavior aligned with the backend configuration. Redeploy the backend if Render does not apply environment changes automatically.

### Browser verification

After both deployments:

1. Open the Vercel URL.
2. Use browser developer tools to confirm API requests target `https://umifbt.onrender.com`.
3. Confirm there are no CORS errors.
4. Confirm `/health` and `/ready` remain healthy.
5. Verify read-only dashboard/issue views.
6. Do not submit real production records merely to prove connectivity unless an explicitly approved test-data cleanup plan exists.

## G. Remaining blockers and limitations

### Authentication

The backend API routes are currently unauthenticated. This includes feedback reads/writes, issue reads, lifecycle transitions, notifications, QA views, and conversation operations. A public frontend can therefore expose sensitive data and mutation operations if the routes are reachable.

The frontend has no implemented authentication/session flow to preserve or configure. The intended identity model must be decided before unrestricted public use.

### CORS

The exact Vercel origin must still be added to Render's `CORS_ORIGINS`. The backend's explicit allowlist behavior is verified, but the final browser-origin check is pending.

### Production data

The backend production database was intentionally initialized without demo data. The frontend build and health checks do not require demo records, but handler/routing workflows may require an approved handler-seeding operation before those workflows are used.

### External integrations

OpenRouter and email delivery were not exercised by the frontend deployment checks. Keep email disabled until provider configuration and delivery behavior are independently verified.

## H. Deployment decision

**READY TO DEPLOY WITH DOCUMENTED LIMITATIONS**

The frontend production configuration is centralized, the production build passes, the live backend is reachable and ready, and the exact Vercel settings are documented. The remaining manual steps are the Vercel deployment, recording its final origin, updating backend CORS, and deciding how authentication will protect the currently unauthenticated API.

