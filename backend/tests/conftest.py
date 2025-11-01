"""
Test configuration and fixtures for PlantPal backend tests.
"""
import pytest
import os
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app import models

# Test database URL - using SQLite for testing (in-memory for better performance)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_info():
    """Mock user info for authentication tests."""
    return {
        "cognito_user_id": "test-user-123",
        "email": "test@example.com",
        "name": "Test User",
        "username": "testuser"
    }


@pytest.fixture
def authenticated_client(client: TestClient, db_session: Session, mock_user_info):
    """Create an authenticated test client."""
    # Create a test user in the database
    user = models.User(
        cognito_user_id=mock_user_info["cognito_user_id"],
        email=mock_user_info["email"],
        name=mock_user_info["name"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Mock the authentication dependency
    def mock_get_current_user_info():
        return mock_user_info
    
    from app.auth import get_current_user_info
    app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
    
    yield client, user
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_plant_data():
    """Sample plant data for testing."""
    return {
        "name": "My Monstera",
        "species": "Monstera deliciosa",
        "current_health_score": 85.0,
        "plant_icon": "🌿"
    }


@pytest.fixture
def sample_scan_data():
    """Sample scan data for testing."""
    return {
        "health_score": 90.0,
        "care_notes": "Plant looks healthy with good leaf color",
        "disease_detected": None,
        "is_healthy": True
    }


# Cleanup after tests
@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Clean up test database after each test."""
    yield
    # Remove test database file if it exists
    if os.path.exists("./test.db"):
        os.remove("./test.db")