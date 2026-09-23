from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.reporter import Reporter


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    reporter_id: Mapped[int | None] = mapped_column(
        ForeignKey("reporters.id"), nullable=True
    )
    feedback_id: Mapped[int | None] = mapped_column(
        ForeignKey("feedbacks.id"), nullable=True, unique=True
    )
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    turns: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    collected_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    reporter: Mapped["Reporter"] = relationship(back_populates="conversations")
