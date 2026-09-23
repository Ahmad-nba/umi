from datetime import datetime, timezone

from app.core.enums import EventType, NotificationStatus
from app.models.notification import Notification
from app.services.notification_service import NotificationService


def test_phase6_notification_service_persists_sent_terminal_notification(
    db_session,
):
    notification = NotificationService(db_session).notify_issue(
        issue_id=1,
        reporter_id=1,
        event_type=EventType.ISSUE_ROUTED.value,
        message="Issue routed",
    )

    assert notification.status == NotificationStatus.SENT.value
    assert notification.channel == "terminal"
    assert notification.message == "Issue routed"
    assert notification.created_at is not None


def test_phase6_notifications_are_listed_chronologically(db_session):
    first = Notification(
        issue_id=1,
        reporter_id=1,
        channel="terminal",
        event_type="FIRST",
        message="First",
        status=NotificationStatus.SENT.value,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    second = Notification(
        issue_id=1,
        reporter_id=1,
        channel="terminal",
        event_type="SECOND",
        message="Second",
        status=NotificationStatus.SENT.value,
        created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    db_session.add_all([second, first])
    db_session.commit()

    listed = NotificationService(db_session).list_notifications_for_issue(1)

    assert [item.event_type for item in listed] == ["FIRST", "SECOND"]


def test_phase6_notification_endpoint_exposes_workflow_notifications(client):
    feedback_id = client.post(
        "/feedback",
        json={
            "name": "Notifier",
            "contact": "notifier@example.com",
            "content": "Marks missing from portal",
        },
    ).json()["id"]
    issue_id = client.post(f"/feedback/{feedback_id}/route").json()["issue"]["id"]

    response = client.get(f"/issues/{issue_id}/notifications")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["event_type"] == EventType.ISSUE_ROUTED.value
    assert response.json()[0]["status"] == NotificationStatus.SENT.value


def test_phase6_notification_endpoint_returns_404_for_missing_issue(client):
    response = client.get("/issues/999/notifications")

    assert response.status_code == 404
