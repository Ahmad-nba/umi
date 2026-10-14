# Email Notification Architecture

## Current notification path

The workflow layer creates notifications through `NotificationService` during routing and issue transitions. The existing service persists a `Notification` row using `TerminalNotificationAdapter`, with `channel="terminal"` and `status="SENT"`. Notifications are exposed through `GET /issues/{issue_id}/notifications` and consumed by the CLI and web UI.

## Sender insertion point

Sender is added below the existing notification service:

```text
WorkflowService
    -> NotificationService
        -> TerminalNotificationAdapter, when Sender is disabled
        -> EmailNotificationAdapter, when Sender is enabled
            -> SenderClient
                -> Sender API
```

Workflow and domain modules do not import Sender or email code. The notification service remains responsible for creating the notification record. The adapter only delivers it.

## Delivery lifecycle

1. Create a notification with `PENDING` status.
2. Resolve the reporter contact from the existing `Reporter` record.
3. Select the configured adapter.
4. Deliver through terminal or Sender.
5. Update the same row to `SENT` or `FAILED`.
6. Commit the delivery result without deleting or rolling back the underlying issue workflow.

Failures store a safe error category/message on the notification and never store API keys or authorization headers.

## Configuration

The backend reads:

- `SENDER_API_KEY`
- `SENDER_FROM_EMAIL`
- `SENDER_FROM_NAME`
- `SENDER_ENABLED`
- `SENDER_API_URL` (optional override for tests or compatible Sender gateways)
- `FRONTEND_BASE_URL`

When Sender is disabled or incomplete, the existing terminal/database notification path remains active and the application starts normally.

## Templates and tracking

Email subjects and bodies are generated in `app/notifications/templates.py` from structured notification data. Templates support routing, completion, confirmation, and feedback-received events. Reporter tracking links use `FRONTEND_BASE_URL` and the existing `/reporter/feedback/{feedback_id}` route.

## Known limitations

- Delivery is synchronous because the prototype has no queue infrastructure.
- The current notification table has no separate delivery-attempt table or retry scheduler.
- Contact values are still general strings; email delivery requires an email-shaped contact and safely fails otherwise.
- Sender credentials must be supplied through deployment environment configuration for real delivery.
