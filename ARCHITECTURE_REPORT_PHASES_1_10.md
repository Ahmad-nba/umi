# UMI Feedback Watch Tower

## Architecture and Implementation Report: Phases 1-10

**Audience:** Senior engineer / architecture reviewer  
**System type:** Backend-first FastAPI prototype  
**Current maturity:** Tested demonstrator, not production-ready  
**Validation status:** 35 tests passing at the time of this report

## 1. Executive Summary

UMI is implemented as a synchronous modular monolith that converts participant feedback into a structured issue, assigns ownership, tracks resolution, requests confirmation, and closes the issue.

The implemented primary lifecycle is:

```text
Feedback intake
  -> classification
  -> issue creation and routing
  -> acknowledgement
  -> work started
  -> resolution recorded
  -> confirmation requested
  -> confirmation accepted or rejected
  -> closure
```

The system also provides:

- A terminal notification persistence layer.
- QA dashboard and issue timeline views.
- An executable CLI demonstration of the complete lifecycle.
- A conversation intake path that converts collected messages into normal feedback records.

The architecture is intentionally simple and appropriate for a prototype: one Python process, one FastAPI application, synchronous services, SQLAlchemy ORM, and SQLite persistence. The major architectural limitation is that it still relies on global database objects, startup `create_all()` behavior, synchronous external LLM calls, and unauthenticated APIs. Those are the primary concerns for Phase 11 hardening.

## 2. Technology and Runtime Foundation

### 2.1 Runtime stack

- Python 3.11+ target; development environment uses the project virtual environment `umienv`.
- FastAPI for HTTP routing and request validation.
- Uvicorn for local application serving.
- Pydantic 2 and `pydantic-settings` for schemas and environment configuration.
- SQLAlchemy ORM for persistence and relationships.
- SQLite as the default local database.
- HTTPX for OpenRouter requests.
- Pytest for automated tests.

### 2.2 Application entrypoint

[app/main.py](app/main.py) creates the FastAPI application, registers routers, initializes the database on startup, and seeds default handlers.

Startup currently performs:

1. `database.init_db()`.
2. Creation of missing tables through SQLAlchemy metadata.
3. A SQLite compatibility alteration for the Phase 10 `conversations.feedback_id` column.
4. Seeding of four active handlers when the handler table is empty.

The startup seeding is suitable for a local prototype but should be replaced with explicit migrations and deployment-safe seed/configuration procedures in production.

### 2.3 Configuration

[app/core/config.py](app/core/config.py) supports:

- `APP_ENV`
- `DATABASE_URL`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`

The normal local default is:

```text
sqlite:///./data/feedback_watch_tower.db
```

The environment template is [.env.example](.env.example). Secrets are expected to be supplied through `.env` or deployment configuration and should not be committed.

## 3. Layered Architecture

The application follows a modular-monolith structure:

```text
HTTP/API layer
  app/api
      |
      v
Application/service layer
  app/services
      |
      +--> app/agents       Classification and LLM boundary
      |
      v
Domain/persistence layer
  app/models, app/schemas, app/core/enums.py
      |
      v
SQLAlchemy engine/session
  app/core/database.py
```

### 3.1 API layer

The API layer owns:

- HTTP paths and methods.
- Request/response schema selection.
- HTTP status mapping.
- Dependency injection of SQLAlchemy sessions.
- Serialization of domain objects into response structures.

The layer currently repeats some issue serialization logic across endpoints. A shared serializer or response mapper would reduce duplication during hardening.

### 3.2 Service layer

The service layer owns business operations:

- `FeedbackService`: reporter reuse and feedback persistence.
- `ConversationService`: conversation creation, message collection, and submission into feedback.
- `RoutingService`: active handler selection and administration fallback.
- `IssueService`: direct issue persistence and retrieval.
- `WorkflowService`: classification handoff, issue routing, state transitions, events, and notification calls.
- `NotificationService`: persistence through the terminal notification adapter.
- `QAService`: manager-oriented summaries, next actions, event timelines, and notification counts.

### 3.3 Agent layer

[app/agents/llm_client.py](app/agents/llm_client.py) is the only external LLM boundary. It either:

- Calls OpenRouter using the configured API key and model; or
- Uses deterministic keyword classification when no key is configured.

[app/agents/classifier.py](app/agents/classifier.py) validates provider output using the `FeedbackAnalysis` Pydantic schema and returns a safe administrative fallback for invalid output.

This isolates provider-specific behavior from the rest of the workflow and allows tests to run offline.

## 4. Persistence Model

The database contains seven mapped tables.

### 4.1 Reporter

Stores participant identity:

- `id`
- `name`
- `contact`
- `created_at`

A reporter can own feedback, notifications, and conversations. Reporter reuse is currently implemented through an application-level lookup by contact.

### 4.2 Feedback

Represents the initial participant finding:

- `id`
- `reporter_id`
- `channel`
- `content`
- `context`
- `submitted_at`
- `status`

Feedback status currently uses `RECEIVED` and `PROCESSED`.

### 4.3 Handler

Represents a responsible team or person:

- `id`
- `name`
- `department`
- `contact`
- `active`

Startup seeds handlers for Academic Affairs, IT, Facilities, and Administration.

### 4.4 Issue

Represents the actionable, owned QA finding:

- `id`
- `feedback_id`
- `reference`
- `title`
- `summary`
- `category`
- `issue_type`
- `priority`
- `department`
- `handler_id`
- `status`
- `resolution`
- `created_at`
- `updated_at`
- `completed_at`

`feedback_id` is unique, enforcing one canonical issue per feedback item at the model level.

### 4.5 Event

Represents the issue timeline:

- `id`
- `issue_id`
- `event_type`
- `actor`
- `description`
- JSON `metadata`
- `created_at`

Events record classification, issue creation, routing, workflow transitions, confirmation, and closure.

### 4.6 Notification

Represents a notification generated for the reporter:

- `id`
- `issue_id`
- `reporter_id`
- `channel`
- `event_type`
- `message`
- `status`
- `created_at`

The current adapter is terminal/database-backed and immediately records notifications as `SENT`.

### 4.7 Conversation

Represents an alternative intake path:

- `id`
- optional `reporter_id`
- optional unique `feedback_id`
- `status`
- JSON `turns`
- JSON `collected_fields`
- `created_at`
- `updated_at`

Conversation messages are currently user turns. A submitted conversation creates one normal feedback record with `channel="conversation"`.

## 5. Endpoint Design

There are currently 24 registered operations across eight router modules.

### 5.1 Health

```text
GET /health
```

Returns the process-level health response:

```json
{ "status": "ok" }
```

A database-aware readiness endpoint is still needed for production hardening.

### 5.2 Feedback

```text
POST /feedback
GET  /feedback
GET  /feedback/{feedback_id}
POST /feedback/{feedback_id}/process
POST /feedback/{feedback_id}/route
```

Responsibilities:

- Validate and persist participant feedback.
- Reuse reporters by contact.
- Classify feedback.
- Create one routed issue per feedback.
- Expose feedback state and classification output.

### 5.3 Issues

```text
GET /issues
GET /issues/{issue_id}
```

These endpoints expose issue identity, classification, assigned handler, status, resolution, and timestamps.

### 5.4 Workflow

```text
POST /issues/{issue_id}/acknowledge
POST /issues/{issue_id}/start
POST /issues/{issue_id}/complete
POST /issues/{issue_id}/confirm
POST /issues/{issue_id}/close
```

Workflow request bodies are typed:

```json
{ "resolution": "Corrected the issue." }
```

```json
{ "confirmed": true }
```

Responses include both a human-readable message and the updated issue representation.

### 5.5 Notifications

```text
GET /issues/{issue_id}/notifications
```

Returns notifications in chronological order and returns `404` for a missing issue.

### 5.6 QA views

```text
GET /qa/dashboard
GET /qa/issues/{issue_id}
```

The dashboard returns:

- Total issue count.
- Counts grouped by status.
- Issue summaries.
- Next action for each issue.

The issue detail view returns:

- Issue summary.
- Chronological event timeline.
- Notification count.

### 5.7 Conversations

```text
POST /conversations
GET  /conversations/{conversation_id}
POST /conversations/{conversation_id}/messages
POST /conversations/{conversation_id}/submit
```

Conversation creation may be anonymous. Submission requires reporter identity because the existing feedback model requires a reporter.

## 6. Phase-by-Phase Implementation

### Phase 1: Foundation

**Purpose:** Establish a runnable backend and persistence foundation.

Implemented:

- FastAPI application entrypoint.
- Health endpoint.
- SQLAlchemy declarative base, engine, session factory, and database dependency.
- Pydantic settings.
- Shared logging setup.
- SQLite data directory creation.
- Initial model registration and table creation.
- Local virtual environment and dependency declaration.

**How it supports later phases:** Every later service and API depends on the database session, model registry, settings, and application entrypoint created here.

### Phase 2: Feedback Domain

**Purpose:** Capture a structured participant finding.

Implemented:

- Reporter and feedback models.
- Feedback creation, retrieval, and listing.
- Reporter reuse by contact.
- Input trimming and whitespace validation.
- `RECEIVED` feedback state.
- Feedback API tests.

**Dependency relationship:** Phase 2 sits directly on Phase 1 persistence. It becomes the source record consumed by classification and issue routing.

### Phase 3: Agent Intelligence

**Purpose:** Convert unstructured feedback into structured analysis.

Implemented:

- OpenRouter client boundary.
- Deterministic local fallback when no API key is configured.
- Classification prompt.
- `FeedbackAnalysis` schema with priority, department, and confidence validation.
- Safe fallback for invalid or malformed provider output.
- `POST /feedback/{id}/process`.

**Dependency relationship:** Phase 3 consumes Phase 2 feedback content and produces the structured data required by Phase 4 issue creation and routing.

### Phase 4: Issue and Routing

**Purpose:** Turn classified feedback into owned, actionable work.

Implemented:

- Handler model and startup seeding.
- Department-specific active handler lookup.
- Administration fallback routing.
- Issue creation with generated references.
- Classification, creation, and routing events.
- Initial routing notification.
- Idempotent route operation per feedback.
- Issue list/detail endpoints.
- `POST /feedback/{id}/route`.

**Dependency relationship:** Phase 4 consumes Phase 3 analysis and Phase 2 reporter/feedback records. It produces the routed issue required by the workflow engine.

### Phase 5: Workflow Engine

**Purpose:** Enforce the controlled issue state machine.

Implemented lifecycle:

```text
ROUTED
  -> ACKNOWLEDGED
  -> IN_PROGRESS
  -> COMPLETED
  -> AWAITING_CONFIRMATION
  -> CONFIRMED
  -> CLOSED
```

Also supported:

```text
AWAITING_CONFIRMATION -> IN_PROGRESS
```

when the reporter rejects the proposed fix.

Implemented:

- Transition table and expected-state validation.
- Event creation for transitions.
- Resolution and completion timestamp persistence.
- Typed workflow request payloads.
- HTTP `409` for invalid transitions.
- HTTP `404` for missing issues.
- Updated issue returned from each transition endpoint.

**Dependency relationship:** Phase 5 operates on the routed issues created in Phase 4 and invokes Phase 6 notification behavior during transitions.

### Phase 6: Notifications

**Purpose:** Persist and expose communication generated by workflow changes.

Implemented:

- Terminal notification adapter.
- Notification persistence with `SENT` status.
- Reporter and issue associations.
- Chronological notification listing.
- Public notification endpoint.
- Notification tests for creation, ordering, and retrieval.

**Dependency relationship:** Phase 6 is called by Phase 4 routing and Phase 5 transitions. It gives the workflow an observable communication trail without introducing external delivery infrastructure.

### Phase 7: Lifecycle Wiring

**Purpose:** Make the full report-to-closure path executable through the public API.

Implemented:

- Router registration for workflow and notification APIs.
- End-to-end lifecycle test.
- Consistent typed request and response behavior.
- Public visibility of final issue state and notifications.

**Dependency relationship:** Phase 7 integrates Phases 2 through 6 into one externally testable workflow.

### Phase 8: QA Service

**Purpose:** Provide management-oriented views over the lifecycle data.

Implemented:

- `QAService` aggregate layer.
- Dashboard grouped by issue status.
- Next-action calculation based on current status.
- Issue timeline aggregation from events.
- Notification count aggregation.
- `/qa/dashboard` and `/qa/issues/{id}` endpoints.

**Dependency relationship:** Phase 8 is read-oriented and consumes issues, events, and notifications generated by Phases 4 through 7. It does not duplicate their write logic.

### Phase 9: CLI Demo

**Purpose:** Prove the system can execute its intended story outside an individual test.

Implemented:

- `scripts/demo.py`.
- Feedback creation.
- Routing.
- Acknowledgement.
- Work start.
- Completion.
- Confirmation.
- Closure.
- Final issue and notification output.
- Dedicated CLI demo test.

Run with:

```bash
umienv/Scripts/python.exe -m scripts.demo
```

Expected result includes:

```text
Final status: CLOSED
```

**Dependency relationship:** Phase 9 depends on every previous phase and serves as the simplest operational proof of the complete workflow.

### Phase 10: Conversation Backend

**Purpose:** Add a lightweight alternative intake path without creating a second issue system.

Implemented:

- Conversation model normalization.
- Reporter-aware conversation creation.
- Anonymous conversation drafting.
- Message turn storage.
- Conversation retrieval.
- Submission into the existing feedback service.
- `channel="conversation"` feedback records.
- Unique conversation-to-feedback linkage.
- Idempotent repeated submission.
- Closed-conversation protection.
- SQLite compatibility update for existing databases.

**Dependency relationship:** Phase 10 sits beside Phase 2 as another intake path. Once submitted, it enters the same Phase 2 feedback model and can continue through Phases 3 to 9 without a parallel workflow implementation.

## 7. Test and Verification Status

The repository currently contains dedicated milestone tests from Phases 1 through 10 plus additional unit coverage.

The latest full suite result was:

```text
35 passed
```

The test strategy includes:

- API contract tests.
- Service-level persistence tests.
- Deterministic offline classifier tests.
- Fake-provider LLM parsing tests.
- State transition tests.
- Notification ordering tests.
- Full lifecycle integration tests.
- QA dashboard/timeline tests.
- CLI demo execution tests.
- Conversation submission and idempotency tests.

The test fixture uses an in-memory SQLite database with `StaticPool` and rebinds the application database session for API tests. This makes tests isolated from the normal local database, but the global rebinding approach should be replaced with explicit dependency overrides before parallel CI execution.

## 8. Current Architectural Risks

### 8.1 Security and authorization

All endpoints are currently unauthenticated. Any caller can read feedback, inspect issues, view conversations, and advance workflow state. There are no roles for participants, managers, fix owners, or verifiers.

### 8.2 Migration strategy

The application uses `Base.metadata.create_all()` and a SQLite-specific `ALTER TABLE`. There is no Alembic migration history, rollback path, or production schema deployment strategy.

### 8.3 Transaction boundaries

Workflow and notification services commit independently. A failure after one nested commit can leave status, events, and notifications partially persisted.

### 8.4 Concurrency

Issue references are generated by querying the latest issue from a separate session. Concurrent requests can race. Reporter reuse also has an application-level lookup without a database uniqueness constraint.

### 8.5 External provider behavior

LLM requests are synchronous and do not yet have production retry, circuit-breaker, redaction, rate-limit, or provider data-sharing controls.

### 8.6 Notification delivery

Notifications are persisted as terminal records only. There is no email, SMS, webhook, queue, retry, or delivery-failure implementation.

### 8.7 Data exposure and retention

Reporter contacts, feedback, resolutions, and conversation transcripts are returned directly. There is no retention, deletion, masking, audit identity, or privacy policy implementation.

### 8.8 Database dependency typing and diagnostics

The database dependency `get_db()` is a generator but is annotated as returning `Session`. Static diagnostics also identify unused imports and logging/database typing issues. These should be resolved before making static analysis a CI gate.

### 8.9 Lifecycle semantics

The declared state table contains `SUBMITTED` and `PROCESSING`, but the primary route creates issues directly in `ROUTED`. Failed confirmation returns to `IN_PROGRESS` while retaining the previous resolution and completion timestamp. These semantics should be made explicit before production use.

## 9. Recommended Senior-Review Next Steps

### Priority 1: Production safety

1. Add authentication and role-based authorization.
2. Add ownership checks for feedback, conversations, and issues.
3. Introduce Alembic migrations.
4. Replace global database rebinding with FastAPI dependency overrides.
5. Make workflow and notification writes atomic.
6. Add database constraints for reporter contact and issue references.

### Priority 2: Operational reliability

1. Add `/live` and `/ready` endpoints.
2. Add database readiness checks.
3. Add structured request/correlation logging.
4. Add stable unexpected-error handling.
5. Add LLM timeout, retry, rate-limit, and redaction policies.
6. Add notification failure/retry behavior.

### Priority 3: API maturity

1. Add pagination and filtering to feedback, issue, notification, and QA lists.
2. Centralize response serialization.
3. Version the API.
4. Add explicit handler-management endpoints or configuration.
5. Add event/timeline response schemas consistently.

### Priority 4: Data and privacy

1. Define retention and deletion behavior.
2. Mask contact information by caller role.
3. Add authenticated actor identity to events.
4. Document external LLM data processing.
5. Add secret rotation and incident-response procedures.

### Priority 5: CI and release gates

Recommended commands:

```bash
umienv/Scripts/python.exe -m pytest -q
umienv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing
umienv/Scripts/python.exe -m compileall app tests scripts
umienv/Scripts/python.exe -m pip check
```

For a production-oriented pipeline, add formatting, linting, type checking, dependency auditing, migration checks, and a coverage threshold.

## 10. Architectural Conclusion

Phases 1 through 10 form a coherent prototype architecture rather than a set of disconnected examples. The most important design choice is the shared `Feedback` and `Issue` lifecycle: both form submissions and conversation submissions converge into the same domain workflow, which avoids creating separate logic for each intake channel.

The system currently proves the central product story:

```text
A participant reports a finding
  -> UMI structures and classifies it
  -> a responsible handler is assigned
  -> work progresses through explicit states
  -> the reporter is notified
  -> the fix is confirmed
  -> the issue is closed
```

The next architectural step is not another major feature. It is converting this reliable demonstrator into a controlled service through security, transaction boundaries, migrations, observability, privacy controls, and deployment discipline.
