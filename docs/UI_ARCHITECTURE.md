# Feedback Watch Tower UI Architecture

## Backend Integration

The web client consumes the existing FastAPI application as the system of record. The current backend routes are:

- Feedback: `POST /feedback`, `GET /feedback`, `GET /feedback/{id}`, `POST /feedback/{id}/process`, `POST /feedback/{id}/route`
- Issues: `GET /issues`, `GET /issues/{id}`
- Workflow: `POST /issues/{id}/acknowledge`, `/start`, `/complete`, `/confirm`, `/close`
- Notifications: `GET /issues/{id}/notifications`
- QA: `GET /qa/dashboard`, `GET /qa/issues/{id}`
- Conversations: `POST /conversations`, `GET /conversations/{id}`, `POST /conversations/{id}/messages`, `POST /conversations/{id}/submit`

The browser never calculates classification, routing, workflow transitions, notification generation, or closure. It sends commands to the backend and renders the returned domain state.

## Frontend Architecture

The client is a Next.js App Router application under `web/`:

- `app/`: route-level persona experiences.
- `components/`: small reusable presentation components.
- `lib/api.ts`: typed fetch boundary and backend error normalization.
- `lib/*-api.ts`: role-oriented API calls.
- `types/`: TypeScript mirrors of backend response shapes.
- `public/`: static assets.

Persona navigation is explicit for the demo and can later be replaced by authentication without changing the page responsibilities.

## Persona Journeys

### Reporter

`/reporter` explains purpose and starts intake. `/reporter/feedback` submits through `POST /feedback`. The returned feedback ID routes to `/reporter/feedback/{id}`, where the UI reads the issue, timeline, and notifications. Confirmation calls the existing `/confirm` and `/close` workflow endpoints.

### Handler

`/handler` reads issues from `GET /issues`. A task detail view reads the issue, timeline, and notifications, then invokes `/acknowledge`, `/start`, and `/complete` as permitted by the backend state.

### QA

`/qa` reads `GET /qa/dashboard` for aggregate status and next actions. Issue detail reads `GET /qa/issues/{id}` and notification data for lifecycle inspection.

## API/View Gaps

The current backend is sufficient for a demo client, but has known presentation gaps:

- Feedback and issue list endpoints have no pagination or server-side filtering.
- Issue detail does not directly include the full feedback or handler record.
- QA dashboard does not expose category, department, feedback, or notification aggregates beyond its current issue summaries.
- There is no authentication or ownership model, so persona switching is demo-only.
- The rejection path returns an issue to `IN_PROGRESS` but does not accept a rejection reason.
- The notification adapter persists terminal notifications but does not deliver external email.

The initial UI uses existing routes without creating duplicate backend view endpoints. Thin read endpoints can be added later if the QA or reporter experiences require larger aggregate payloads.
