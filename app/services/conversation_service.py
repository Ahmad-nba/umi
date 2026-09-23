from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import WorkflowError
from app.models.conversation import Conversation
from app.models.feedback import Feedback
from app.models.reporter import Reporter
from app.services.feedback_service import FeedbackService


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        reporter_name: str | None = None,
        reporter_contact: str | None = None,
    ) -> Conversation:
        reporter_id = None
        if reporter_contact:
            reporter = (
                self.db.query(Reporter)
                .filter(Reporter.contact == reporter_contact)
                .first()
            )
            if reporter is None:
                reporter = Reporter(
                    name=reporter_name or "Conversation Reporter",
                    contact=reporter_contact,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(reporter)
                self.db.flush()
            reporter_id = reporter.id

        conversation = Conversation(
            reporter_id=reporter_id,
            status="active",
            turns=[],
            collected_fields={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get(self, conversation_id: int) -> Conversation | None:
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def add_message(self, conversation_id: int, content: str) -> Conversation:
        conversation = self._require(conversation_id)
        if conversation.status != "active":
            raise WorkflowError(
                "Conversation is already closed", code="conversation_closed"
            )
        turns = list(conversation.turns or [])
        turns.append(
            {
                "role": "user",
                "content": content.strip(),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        conversation.turns = turns
        conversation.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def submit(self, conversation_id: int) -> tuple[Conversation, Feedback]:
        conversation = self._require(conversation_id)
        if conversation.feedback_id is not None:
            feedback = (
                self.db.query(Feedback)
                .filter(Feedback.id == conversation.feedback_id)
                .one()
            )
            return conversation, feedback
        if conversation.reporter_id is None:
            raise WorkflowError(
                "Reporter contact is required before submission",
                code="reporter_required",
            )
        turns = conversation.turns or []
        content = "\n".join(
            turn.get("content", "") for turn in turns if turn.get("content")
        ).strip()
        if not content:
            raise WorkflowError(
                "Conversation must contain a message before submission",
                code="message_required",
            )
        reporter = (
            self.db.query(Reporter)
            .filter(Reporter.id == conversation.reporter_id)
            .one()
        )
        feedback = FeedbackService(self.db).create_feedback(
            name=reporter.name,
            contact=reporter.contact,
            content=content,
            channel="conversation",
        )
        conversation.feedback_id = feedback.id
        conversation.status = "submitted"
        conversation.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation, feedback

    def _require(self, conversation_id: int) -> Conversation:
        conversation = self.get(conversation_id)
        if conversation is None:
            raise WorkflowError("Conversation not found", code="conversation_not_found")
        return conversation
