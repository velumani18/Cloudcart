"""Pytest fixtures for CloudCart."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database import Base, get_db
import backend.database
import backend.services.outbox_service
import backend.models  # ensure models are registered
from backend.seed import seed_database
from backend.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in memory once for the test session and seed."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    seed_database(session)
    session.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(monkeypatch):
    """Provide TestClient with overridden DB session."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    monkeypatch.setattr(backend.database, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(backend.database, "engine", test_engine)
    monkeypatch.setattr(backend.services.outbox_service, "SessionLocal", TestingSessionLocal)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
