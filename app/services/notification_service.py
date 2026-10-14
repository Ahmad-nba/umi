from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Protocol

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import NotificationStatus
from app.core.logging import logger
from app.models.issue import Issue
from app.models.notification import Notification
from app.models.reporter import Reporter
from app.notifications.email_adapter import EmailNotificationAdapter
from app.notifications.sender_client import DeliveryResult, SenderClient


class NotificationAdapter(Protocol):
    channel: str
    send: Callable[..., DeliveryResult]


class TerminalNotificationAdapter:
    channel = "terminal"

    def send(
        self,
        *,
        recipient: str,
        reporter_name: str,
        event_type: str,
        message: str,
        reference: str,
        feedback_id: int,
    ) -> DeliveryResult:
        _ = (recipient, reporter_name, event_type, message, reference, feedback_id)
        return DeliveryResult(True)


class NotificationService:
    def __init__(self, db: Session, adapter: NotificationAdapter | None = None):
        self.db = db
        self.adapter = adapter or self._configured_adapter()

    def notify_issue(
        self,
        *,
        issue_id: int,
        reporter_id: int,
        event_type: str,
        message: str,
        channel: str = "terminal",
    ) -> Notification:
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
        reporter = self.db.query(Reporter).filter(Reporter.id == reporter_id).first()
        if (issue is None or reporter is None) and self.adapter.channel != "terminal":
            raise ValueError(
                "Email notifications require an existing issue and reporter"
            )
        effective_channel = self.adapter.channel if channel == "terminal" else channel
        existing = (
            self.db.query(Notification)
            .filter(
                Notification.issue_id == issue_id,
                Notification.reporter_id == reporter_id,
                Notification.event_type == event_type,
                Notification.channel == effective_channel,
                Notification.message == message,
            )
            .first()
        )
        if existing is not None:
            return existing

        notification = Notification(
            issue_id=issue_id,
            reporter_id=reporter_id,
            channel=effective_channel,
            event_type=event_type,
            message=message,
            status=NotificationStatus.PENDING.value,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        result = self.adapter.send(
            recipient=reporter.contact if reporter else "",
            reporter_name=reporter.name if reporter else "Reporter",
            event_type=event_type,
            message=message,
            reference=issue.reference if issue else "",
            feedback_id=issue.feedback_id if issue else 0,
        )
        notification.status = (
            NotificationStatus.SENT.value
            if result.delivered
            else NotificationStatus.FAILED.value
        )
        notification.delivery_error = result.error_message
        self.db.commit()
        self.db.refresh(notification)
        logger.info(
            (
                "email_notification_sent"
                if result.delivered
                else "email_notification_failed"
            ),
            extra={
                "notification_id": notification.id,
                "issue_id": issue_id,
                "event_type": event_type,
                "channel": effective_channel,
                "delivery_status": notification.status,
                "error_type": result.error_type,
            },
        )
        return notification

    def list_notifications_for_issue(self, issue_id: int):
        return (
            self.db.query(Notification)
            .filter(Notification.issue_id == issue_id)
            .order_by(Notification.created_at.asc())
            .all()
        )

    @staticmethod
    def _configured_adapter() -> NotificationAdapter:
        settings = get_settings()
        if (
            settings.sender_enabled
            and settings.sender_api_key
            and settings.sender_from_email
        ):
            return EmailNotificationAdapter(
                SenderClient(
                    api_key=settings.sender_api_key,
                    api_url=settings.sender_api_url,
                    from_email=settings.sender_from_email,
                    from_name=settings.sender_from_name,
                )
            )
        return TerminalNotificationAdapter()
