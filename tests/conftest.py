import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.database as core_db
from app.core.database import Base
from app.core.config import get_settings
from app.main import app

# Import models so SQLAlchemy metadata is registered before table creation.
from app.models import (
    conversation,
    event,
    feedback,
    handler,
    issue,
    notification,
    reporter,
)  # noqa: F401


@pytest.fixture()
def db_session():
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["OPENROUTER_API_KEY"] = ""
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    core_db.engine = engine
    core_db.SessionLocal = TestingSessionLocal
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    with TestClient(app) as test_client:
        yield test_client
