import httpx

from app.core.config import get_settings
from app.core.enums import EventType, NotificationStatus
from app.models.feedback import Feedback
from app.models.issue import Issue
from app.models.reporter import Reporter
from app.notifications.email_adapter import EmailNotificationAdapter
from app.notifications.sender_client import SenderClient
from app.notifications.templates import render_email
from app.services.notification_service import NotificationService


class FakeResponse:
    def __init__(self, status_code=202):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://api.sender.test/v1/email")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                "provider failure", request=request, response=response
            )


def _issue(db_session):
    reporter = Reporter(name="Grace", contact="grace@example.com")
    db_session.add(reporter)
    db_session.flush()
    feedback = Feedback(
        reporter_id=reporter.id,
        channel="form",
        content="Marks are missing",
    )
    db_session.add(feedback)
    db_session.flush()
    issue = Issue(
        feedback_id=feedback.id,
        reference="FW-EMAIL-0001",
        title="Missing marks",
        summary="Marks are missing",
        category="Academic",
        issue_type="Missing Marks",
        priority="HIGH",
        department="Academic Affairs",
        status="ROUTED",
    )
    db_session.add(issue)
    db_session.commit()
    return issue, reporter


def test_sender_client_builds_authenticated_email_request(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("app.notifications.sender_client.httpx.post", fake_post)
    result = SenderClient(
        api_key="secret-key",
        api_url="https://api.sender.test/v1/email",
        from_email="updates@umi.example",
        from_name="UMI",
    ).send_email(
        recipient="grace@example.com",
        subject="Update",
        body="Hello",
    )

    assert result.delivered is True
    assert captured["url"] == "https://api.sender.test/v1/email"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer secret-key"
    assert captured["kwargs"]["json"]["to"] == [{"email": "grace@example.com"}]
    assert captured["kwargs"]["json"]["subject"] == "Update"
    assert "secret-key" not in str(result)


def test_sender_client_handles_http_and_timeout_failures(monkeypatch):
    monkeypatch.setattr(
        "app.notifications.sender_client.httpx.post",
        lambda *args, **kwargs: FakeResponse(503),
    )
    failed = SenderClient(
        api_key="secret-key",
        api_url="https://api.sender.test/v1/email",
        from_email="updates@umi.example",
        from_name="UMI",
    ).send_email(recipient="grace@example.com", subject="Update", body="Hello")
    assert failed.delivered is False
    assert failed.error_type == "http_error"
    assert "secret-key" not in str(failed)

    def timeout(*args, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr("app.notifications.sender_client.httpx.post", timeout)
    timed_out = SenderClient(
        api_key="secret-key",
        api_url="https://api.sender.test/v1/email",
        from_email="updates@umi.example",
        from_name="UMI",
    ).send_email(recipient="grace@example.com", subject="Update", body="Hello")
    assert timed_out.error_type == "timeout"


def test_email_template_uses_configured_frontend_url(monkeypatch):
    monkeypatch.setenv("FRONTEND_BASE_URL", "https://watch.example")
    get_settings.cache_clear()
    email = render_email(
        event_type=EventType.CONFIRMATION_REQUESTED.value,
        reporter_name="Grace",
        reference="FW-0001",
        message="Please confirm the resolution.",
        feedback_id=42,
    )
    assert "https://watch.example/reporter/feedback/42" in email.body
    assert "FW-0001" in email.subject
    get_settings.cache_clear()


def test_email_notification_success_and_failure_are_persisted(monkeypatch, db_session):
    issue, reporter = _issue(db_session)
    monkeypatch.setattr(
        "app.notifications.sender_client.httpx.post",
        lambda *args, **kwargs: FakeResponse(),
    )
    adapter = EmailNotificationAdapter(
        SenderClient(
            api_key="secret-key",
            api_url="https://api.sender.test/v1/email",
            from_email="updates@umi.example",
            from_name="UMI",
        )
    )
    sent = NotificationService(db_session, adapter=adapter).notify_issue(
        issue_id=issue.id,
        reporter_id=reporter.id,
        event_type=EventType.ISSUE_ROUTED.value,
        message="Your feedback was routed to Academic Affairs.",
    )
    assert sent.channel == "email"
    assert sent.status == NotificationStatus.SENT.value

    monkeypatch.setattr(
        "app.notifications.sender_client.httpx.post",
        lambda *args, **kwargs: FakeResponse(503),
    )
    failed = NotificationService(db_session, adapter=adapter).notify_issue(
        issue_id=issue.id,
        reporter_id=reporter.id,
        event_type=EventType.TASK_COMPLETED.value,
        message="Your issue was completed.",
    )
    assert failed.status == NotificationStatus.FAILED.value
    assert failed.delivery_error == "Sender returned HTTP 503"


def test_sender_disabled_keeps_terminal_notifications(db_session):
    notification = NotificationService(db_session).notify_issue(
        issue_id=1,
        reporter_id=1,
        event_type=EventType.ISSUE_ROUTED.value,
        message="Issue routed",
    )
    assert notification.channel == "terminal"
    assert notification.status == NotificationStatus.SENT.value


def test_configured_sender_is_used_by_existing_notification_flow(
    monkeypatch, db_session
):
    issue, reporter = _issue(db_session)
    monkeypatch.setenv("SENDER_ENABLED", "true")
    monkeypatch.setenv("SENDER_API_KEY", "secret-key")
    monkeypatch.setenv("SENDER_FROM_EMAIL", "updates@umi.example")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.notifications.sender_client.httpx.post",
        lambda *args, **kwargs: FakeResponse(),
    )

    notification = NotificationService(db_session).notify_issue(
        issue_id=issue.id,
        reporter_id=reporter.id,
        event_type=EventType.ISSUE_ROUTED.value,
        message="Your feedback was routed to Academic Affairs.",
    )

    assert notification.channel == "email"
    assert notification.status == NotificationStatus.SENT.value
    get_settings.cache_clear()
