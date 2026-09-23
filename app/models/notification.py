from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.issue import Issue
    from app.models.reporter import Reporter


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issues.id"), nullable=False, index=True
    )
    reporter_id: Mapped[int] = mapped_column(ForeignKey("reporters.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="terminal", nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    issue: Mapped["Issue"] = relationship(back_populates="notifications")
    reporter: Mapped["Reporter"] = relationship(back_populates="notifications")
