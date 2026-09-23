from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.feedback import Feedback
    from app.models.notification import Notification


class Reporter(Base):
    __tablename__ = "reporters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="reporter")
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="reporter"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="reporter"
    )
