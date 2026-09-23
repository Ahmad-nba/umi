from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _database_path() -> str:
    db_url = os.getenv("DATABASE_URL") or get_settings().database_url
    if db_url.startswith("sqlite:///./"):
        path = Path(db_url.replace("sqlite:///./", "./", 1))
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"
    return db_url


def build_engine(database_url: str | None = None):
    url = database_url or _database_path()
    return create_engine(url, connect_args={"check_same_thread": False})


engine = build_engine()
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def reset_database(database_url: str | None = None) -> None:
    global engine, SessionLocal
    engine = build_engine(database_url)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import (
        conversation,
        event,
        feedback,
        handler,
        issue,
        notification,
        reporter,
    )

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        columns = {
            column["name"] for column in inspect(engine).get_columns("conversations")
        }
        if "feedback_id" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE conversations ADD COLUMN feedback_id INTEGER")
                )
