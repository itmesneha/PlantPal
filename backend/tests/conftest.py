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

# CRITICAL: Override environment variables to ensure test isolation
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["HF_TOKEN"] = "test_token"
os.environ["PLANTNET_API_KEY"] = "test_key"
os.environ["OPENROUTER_API_KEY"] = "test_key"
os.environ["AWS_ACCESS_KEY_ID"] = "test_key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test_secret"
os.environ["COGNITO_USER_POOL_ID"] = "test_pool"
os.environ["COGNITO_CLIENT_ID"] = "test_client"

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
def mock_auth_dependency():
    """Mock authentication dependency for tests."""
    def mock_get_current_user_info():
        return {
            "cognito_user_id": "test-user-123",
            "email": "test@example.com",
            "name": "Test User",
            "username": "testuser"
        }
    
    from app.auth import get_current_user_info
    app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
    
    yield mock_get_current_user_info
    
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


@pytest.fixture
def test_db(db_session):
    """Alias for db_session to match test expectations."""
    return db_session


@pytest.fixture
def test_user(db_session):
    """Create a test user for testing."""
    user = models.User(
        cognito_user_id="test-user-123",
        email="test@example.com",
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_plant(db_session, test_user):
    """Create a test plant for testing."""
    plant = models.Plant(
        user_id=test_user.id,
        name="Test Plant",
        species="Test Species",
        current_health_score=75.0,
        streak_days=3
    )
    db_session.add(plant)
    db_session.commit()
    db_session.refresh(plant)
    return plant


@pytest.fixture
def test_plant_scan(db_session, test_plant, test_user):
    """Create a test plant scan for testing."""
    from datetime import datetime
    plant_scan = models.PlantScan(
        plant_id=test_plant.id,
        user_id=test_user.id,
        health_score=85.0,
        scan_date=datetime.utcnow(),
        care_notes="Test care notes",
        disease_detected=None,
        is_healthy=True
    )
    db_session.add(plant_scan)
    db_session.commit()
    db_session.refresh(plant_scan)
    return plant_scan


# Cleanup after tests
@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Clean up test database after each test."""
    yield
    # Remove any test database files that might have been created
    test_db_files = ["./test.db", "./test_plantpal.db", "./plantpal_test.db"]
    for db_file in test_db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except OSError:
                pass  # File might be in use, ignore