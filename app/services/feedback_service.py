from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.enums import FeedbackStatus
from app.models.feedback import Feedback
from app.models.reporter import Reporter


class FeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def create_feedback(
        self,
        *,
        name: str,
        contact: str,
        content: str,
        channel: str = "form",
        context: str | None = None,
    ) -> Feedback:
        reporter = self.db.query(Reporter).filter(Reporter.contact == contact).first()
        if reporter is None:
            reporter = Reporter(
                name=name, contact=contact, created_at=datetime.now(timezone.utc)
            )
            self.db.add(reporter)
            self.db.flush()

        feedback = Feedback(
            reporter_id=reporter.id,
            channel=channel,
            content=content,
            context=context,
            submitted_at=datetime.now(timezone.utc),
            status=FeedbackStatus.RECEIVED.value,
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        self.db.refresh(reporter)
        return feedback

    def get_feedback(self, feedback_id: int) -> Feedback | None:
        return self.db.query(Feedback).filter(Feedback.id == feedback_id).first()

    def list_feedback(self):
        return self.db.query(Feedback).order_by(Feedback.submitted_at.desc()).all()
