from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.feedback import Feedback
    from app.models.handler import Handler
    from app.models.notification import Notification


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    feedback_id: Mapped[int] = mapped_column(
        ForeignKey("feedbacks.id"), nullable=False, unique=True
    )
    reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    handler_id: Mapped[int | None] = mapped_column(
        ForeignKey("handlers.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    feedback: Mapped["Feedback"] = relationship(back_populates="issues")
    handler: Mapped["Handler"] = relationship(back_populates="issues")
    events: Mapped[list["Event"]] = relationship(back_populates="issue")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="issue")
