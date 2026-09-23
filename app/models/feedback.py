from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.issue import Issue
    from app.models.reporter import Reporter


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("reporters.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="form", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="RECEIVED", nullable=False)

    reporter: Mapped["Reporter"] = relationship(back_populates="feedbacks")
    issues: Mapped[list["Issue"]] = relationship(back_populates="feedback")
