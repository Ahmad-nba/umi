from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.enums import NotificationStatus
from app.models.notification import Notification


class TerminalNotificationAdapter:
    def send(
        self,
        *,
        issue_id: int,
        reporter_id: int,
        event_type: str,
        message: str,
        channel: str = "terminal",
    ) -> Notification:
        notification = Notification(
            issue_id=issue_id,
            reporter_id=reporter_id,
            channel=channel,
            event_type=event_type,
            message=message,
            status=NotificationStatus.SENT.value,
            created_at=datetime.now(timezone.utc),
        )
        return notification


class NotificationService:
    def __init__(self, db: Session, adapter: TerminalNotificationAdapter | None = None):
        self.db = db
        self.adapter = adapter or TerminalNotificationAdapter()

    def notify_issue(
        self,
        *,
        issue_id: int,
        reporter_id: int,
        event_type: str,
        message: str,
        channel: str = "terminal",
    ) -> Notification:
        notification = self.adapter.send(
            issue_id=issue_id,
            reporter_id=reporter_id,
            event_type=event_type,
            message=message,
            channel=channel,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_notifications_for_issue(self, issue_id: int):
        return (
            self.db.query(Notification)
            .filter(Notification.issue_id == issue_id)
            .order_by(Notification.created_at.asc())
            .all()
        )
