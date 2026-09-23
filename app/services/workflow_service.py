from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.enums import EventType, IssueStatus
from app.core.exceptions import WorkflowError
from app.models.event import Event
from app.models.feedback import Feedback
from app.models.issue import Issue
from app.services.notification_service import NotificationService
from app.services.routing_service import RoutingService
from app.schemas.agent import FeedbackAnalysis
from app.agents.classifier import FeedbackClassifier


class WorkflowService:
    TRANSITION_TABLE = {
        IssueStatus.SUBMITTED.value: {IssueStatus.PROCESSING.value},
        IssueStatus.PROCESSING.value: {IssueStatus.ROUTED.value},
        IssueStatus.ROUTED.value: {IssueStatus.ACKNOWLEDGED.value},
        IssueStatus.ACKNOWLEDGED.value: {IssueStatus.IN_PROGRESS.value},
        IssueStatus.IN_PROGRESS.value: {IssueStatus.COMPLETED.value},
        IssueStatus.COMPLETED.value: {IssueStatus.AWAITING_CONFIRMATION.value},
        IssueStatus.AWAITING_CONFIRMATION.value: {
            IssueStatus.CONFIRMED.value,
            IssueStatus.IN_PROGRESS.value,
        },
        IssueStatus.CONFIRMED.value: {IssueStatus.CLOSED.value},
    }

    def __init__(
        self,
        db: Session,
        notification_service: NotificationService | None = None,
        classifier: FeedbackClassifier | None = None,
    ):
        self.db = db
        self.notification_service = notification_service or NotificationService(db)
        self.routing_service = RoutingService(db)
        self.classifier = classifier or FeedbackClassifier()

    def submit_feedback(self, feedback_id: int) -> Feedback:
        feedback = self.db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if feedback is None:
            raise WorkflowError("Feedback not found", code="feedback_not_found")
        feedback.status = "RECEIVED"
        self.db.commit()
        return feedback

    def process_feedback(self, feedback_id: int) -> FeedbackAnalysis:
        feedback = self.db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if feedback is None:
            raise WorkflowError("Feedback not found", code="feedback_not_found")
        analysis = self.classifier.analyze(feedback.content)
        feedback.status = "PROCESSED"
        self.db.commit()
        return analysis

    def create_and_route_issue(
        self, feedback_id: int, analysis: FeedbackAnalysis
    ) -> Issue:
        feedback = self.db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if feedback is None:
            raise WorkflowError("Feedback not found", code="feedback_not_found")

        existing_issue = (
            self.db.query(Issue).filter(Issue.feedback_id == feedback_id).first()
        )
        if existing_issue is not None:
            return existing_issue

        try:
            handler = self.routing_service.route_issue(analysis.department)
        except WorkflowError:
            self.db.rollback()
            raise
        issue = Issue(
            feedback_id=feedback.id,
            reference=self._next_reference(),
            title=analysis.summary.title(),
            summary=analysis.summary,
            category=analysis.category,
            issue_type=analysis.issue_type,
            priority=analysis.priority.value,
            department=analysis.department.value,
            handler_id=handler.id,
            status=IssueStatus.ROUTED.value,
        )
        self.db.add(issue)
        self.db.flush()
        self._record_event(
            issue.id,
            EventType.FEEDBACK_CLASSIFIED.value,
            "system",
            f"Feedback classified: {analysis.summary}",
            {
                "category": analysis.category,
                "issue_type": analysis.issue_type,
                "priority": analysis.priority.value,
                "department": analysis.department.value,
                "confidence": analysis.confidence,
            },
        )
        self._record_event(
            issue.id,
            EventType.ISSUE_CREATED.value,
            "system",
            f"Issue {issue.reference} created",
            {"department": issue.department},
        )
        self._record_event(
            issue.id,
            EventType.ISSUE_ROUTED.value,
            "system",
            f"Issue routed to {handler.department}",
            {"handler_id": handler.id, "department": issue.department},
        )
        self.notification_service.notify_issue(
            issue_id=issue.id,
            reporter_id=feedback.reporter_id,
            event_type=EventType.ISSUE_ROUTED.value,
            message=f"Your feedback {issue.reference} has been routed to {issue.department}.",
            channel="terminal",
        )
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def acknowledge_issue(self, issue_id: int) -> Issue:
        return self._transition(
            issue_id,
            IssueStatus.ROUTED.value,
            IssueStatus.ACKNOWLEDGED.value,
            EventType.REPORTER_ACKNOWLEDGED.value,
            "Acknowledged by reporter",
        )

    def start_issue(self, issue_id: int) -> Issue:
        return self._transition(
            issue_id,
            IssueStatus.ACKNOWLEDGED.value,
            IssueStatus.IN_PROGRESS.value,
            EventType.TASK_STARTED.value,
            "Issue is now in progress",
        )

    def complete_issue(self, issue_id: int, resolution: str) -> Issue:
        issue = self._transition(
            issue_id,
            IssueStatus.IN_PROGRESS.value,
            IssueStatus.COMPLETED.value,
            EventType.TASK_COMPLETED.value,
            "Issue completed",
        )
        issue.resolution = resolution
        issue.completed_at = datetime.now(timezone.utc)
        self.db.add(
            Event(
                issue_id=issue.id,
                event_type=EventType.REPORTER_NOTIFIED.value,
                actor="system",
                description="Resolution sent to reporter",
                metadata_={"resolution": resolution},
            )
        )
        self.notification_service.notify_issue(
            issue_id=issue.id,
            reporter_id=self._reporter_id_for_issue(issue.id),
            event_type=EventType.TASK_COMPLETED.value,
            message=f"Your feedback {issue.reference} has been addressed. Resolution: {resolution}",
            channel="terminal",
        )
        self._request_confirmation(issue.id)
        self.db.commit()
        return issue

    def request_confirmation(self, issue_id: int) -> Issue:
        return self._transition(
            issue_id,
            IssueStatus.COMPLETED.value,
            IssueStatus.AWAITING_CONFIRMATION.value,
            EventType.CONFIRMATION_REQUESTED.value,
            "Confirmation requested from reporter",
        )

    def confirm_issue(self, issue_id: int, confirmed: bool) -> Issue:
        target_status = (
            IssueStatus.CONFIRMED.value if confirmed else IssueStatus.IN_PROGRESS.value
        )
        event_type = (
            EventType.REPORTER_CONFIRMED.value
            if confirmed
            else EventType.TASK_STARTED.value
        )
        issue = self._transition(
            issue_id,
            IssueStatus.AWAITING_CONFIRMATION.value,
            target_status,
            event_type,
            (
                "Reporter confirmed resolution"
                if confirmed
                else "Reporter requested more work"
            ),
        )
        if not confirmed:
            self.notification_service.notify_issue(
                issue_id=issue.id,
                reporter_id=self._reporter_id_for_issue(issue.id),
                event_type=EventType.TASK_STARTED.value,
                message=f"Your feedback {issue.reference} remains active as further action is required.",
                channel="terminal",
            )
        return issue

    def close_issue(self, issue_id: int) -> Issue:
        return self._transition(
            issue_id,
            IssueStatus.CONFIRMED.value,
            IssueStatus.CLOSED.value,
            EventType.ISSUE_CLOSED.value,
            "Issue closed",
        )

    def _transition(
        self,
        issue_id: int,
        expected_current: str,
        next_status: str,
        event_type: str,
        description: str,
    ) -> Issue:
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
        if issue is None:
            raise WorkflowError("Issue not found", code="issue_not_found")
        if issue.status != expected_current:
            allowed = self.TRANSITION_TABLE.get(issue.status, set())
            raise WorkflowError(
                f"Invalid transition from {issue.status} to {next_status}. Allowed: {sorted(allowed)}",
                code="invalid_transition",
            )
        issue.status = next_status
        issue.updated_at = datetime.now(timezone.utc)
        self._record_event(issue.id, event_type, "system", description, {})
        self.notification_service.notify_issue(
            issue_id=issue.id,
            reporter_id=self._reporter_id_for_issue(issue.id),
            event_type=event_type,
            message=self._notification_message(issue, event_type, description),
            channel="terminal",
        )
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def _request_confirmation(self, issue_id: int) -> Issue:
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
        if issue is None:
            raise WorkflowError("Issue not found", code="issue_not_found")
        issue.status = IssueStatus.AWAITING_CONFIRMATION.value
        issue.updated_at = datetime.now(timezone.utc)
        self._record_event(
            issue.id,
            EventType.CONFIRMATION_REQUESTED.value,
            "system",
            "Confirmation requested from reporter",
            {},
        )
        self.notification_service.notify_issue(
            issue_id=issue.id,
            reporter_id=self._reporter_id_for_issue(issue.id),
            event_type=EventType.CONFIRMATION_REQUESTED.value,
            message=f"Did this resolve your issue? Feedback {issue.reference}",
            channel="terminal",
        )
        self.db.commit()
        self.db.refresh(issue)
        return issue

    def _record_event(
        self,
        issue_id: int,
        event_type: str,
        actor: str,
        description: str,
        metadata: dict,
    ) -> Event:
        event = Event(
            issue_id=issue_id,
            event_type=event_type,
            actor=actor,
            description=description,
            metadata_=metadata,
        )
        self.db.add(event)
        return event

    def _reporter_id_for_issue(self, issue_id: int) -> int:
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
        if issue is None:
            raise WorkflowError("Issue not found", code="issue_not_found")
        return issue.feedback.reporter_id

    @staticmethod
    def _notification_message(issue: Issue, event_type: str, description: str) -> str:
        mapping = {
            EventType.ISSUE_ROUTED.value: f"Your feedback {issue.reference} has been routed to {issue.department}.",
            EventType.TASK_STARTED.value: f"Your feedback {issue.reference} is now being worked on.",
            EventType.TASK_COMPLETED.value: f"Your feedback {issue.reference} has been addressed. Resolution: {issue.resolution or description}",
            EventType.CONFIRMATION_REQUESTED.value: f"Did this resolve your issue? {issue.reference}",
            EventType.REPORTER_ACKNOWLEDGED.value: f"Your feedback {issue.reference} has been acknowledged.",
            EventType.ISSUE_CLOSED.value: f"Your feedback {issue.reference} is now closed.",
        }
        return mapping.get(event_type, description)

    @staticmethod
    def _next_reference() -> str:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            last = db.query(Issue).order_by(Issue.id.desc()).first()
            next_number = (last.id if last else 0) + 1
        finally:
            db.close()
        return f"FW-{next_number:04d}"
