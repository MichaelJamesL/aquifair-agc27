from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from neraca.core.config import Settings
from neraca.infrastructure import orm  # noqa: F401 - register tables
from neraca.infrastructure.database import Base, get_session
from neraca.main import create_app

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TEST_DATABASE_URL = os.getenv("NERACA_TEST_DATABASE_URL")


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    if TEST_DATABASE_URL:
        engine = create_engine(TEST_DATABASE_URL, future=True)
    else:
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    def override_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    settings = Settings(
        environment="test",
        data_dir=DATA_DIR,
        auto_create_tables=False,
        docs_enabled=True,
        database_url="sqlite+pysqlite:///:memory:",
    )
    app = create_app(settings)
    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
