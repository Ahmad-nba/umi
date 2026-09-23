from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import Department, IssueStatus, Priority
from app.core.logging import logger
from app.models.handler import Handler
from app.models.issue import Issue


class IssueService:
    def __init__(self, db: Session):
        self.db = db

    def create_issue(
        self,
        *,
        feedback_id: int,
        title: str,
        summary: str,
        category: str,
        issue_type: str,
        priority: Priority | str,
        department: Department | str,
        handler: Handler | None = None,
    ) -> Issue:
        if handler is None:
            handler = (
                self.db.query(Handler)
                .filter(Handler.department == str(department))
                .first()
            )

        normalized_department = str(department)
        normalized_priority = str(priority)
        issue = Issue(
            feedback_id=feedback_id,
            reference=self._next_reference(),
            title=title,
            summary=summary,
            category=category,
            issue_type=issue_type,
            priority=normalized_priority,
            department=normalized_department,
            handler_id=handler.id if handler else None,
            status=IssueStatus.SUBMITTED.value,
        )
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        logger.info(
            "issue_created",
            extra={
                "issue_id": issue.id,
                "reference": issue.reference,
                "department": issue.department,
            },
        )
        return issue

    def get_issue(self, issue_id: int) -> Issue | None:
        return self.db.query(Issue).filter(Issue.id == issue_id).first()

    def list_issues(self):
        return self.db.query(Issue).order_by(Issue.created_at.desc()).all()

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
