from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from app.core.enums import IssueStatus
from app.models.event import Event
from app.models.issue import Issue
from app.models.notification import Notification


class QAService:
    NEXT_ACTIONS = {
        IssueStatus.ROUTED.value: "Acknowledge issue",
        IssueStatus.ACKNOWLEDGED.value: "Start work",
        IssueStatus.IN_PROGRESS.value: "Complete fix",
        IssueStatus.COMPLETED.value: "Await confirmation",
        IssueStatus.AWAITING_CONFIRMATION.value: "Confirm resolution",
        IssueStatus.CONFIRMED.value: "Close issue",
        IssueStatus.CLOSED.value: "Complete",
    }

    def __init__(self, db: Session):
        self.db = db

    def dashboard(self) -> dict:
        issues = self.db.query(Issue).order_by(Issue.created_at.desc()).all()
        return {
            "total_issues": len(issues),
            "by_status": dict(Counter(issue.status for issue in issues)),
            "issues": [self._summary(issue) for issue in issues],
        }

    def issue_detail(self, issue_id: int) -> dict | None:
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
        if issue is None:
            return None
        events = (
            self.db.query(Event)
            .filter(Event.issue_id == issue_id)
            .order_by(Event.created_at.asc(), Event.id.asc())
            .all()
        )
        return {
            "issue": self._summary(issue),
            "events": [self._event(event) for event in events],
            "notification_count": self.db.query(Notification)
            .filter(Notification.issue_id == issue_id)
            .count(),
        }

    def _summary(self, issue: Issue) -> dict:
        return {
            "id": issue.id,
            "reference": issue.reference,
            "status": issue.status,
            "priority": issue.priority,
            "department": issue.department,
            "handler_id": issue.handler_id,
            "next_action": self.NEXT_ACTIONS.get(issue.status, "Review issue"),
        }

    @staticmethod
    def _event(event: Event) -> dict:
        return {
            "id": event.id,
            "issue_id": event.issue_id,
            "event_type": event.event_type,
            "actor": event.actor,
            "description": event.description,
            "metadata": event.metadata_,
            "created_at": event.created_at.isoformat(),
        }
