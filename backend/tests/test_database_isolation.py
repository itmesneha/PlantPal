"""
Test to verify database isolation is working correctly.
"""
import pytest
import os
from sqlalchemy import create_engine, text
from app.database import get_db


def test_database_isolation():
    """Test that tests are using the correct isolated database."""
    # Check that DATABASE_URL environment variable is overridden
    assert os.environ.get("DATABASE_URL") == "sqlite:///:memory:"
    
    # Verify we're not using the production database
    db_url = os.environ.get("DATABASE_URL")
    assert "postgresql" not in db_url
    assert "plantpal-postgres" not in db_url
    assert "rds.amazonaws.com" not in db_url
    
    print(f"✅ Test database URL: {db_url}")


def test_no_production_data_contamination(db_session):
    """Test that we start with a clean database for each test."""
    from app import models
    
    # Check that we start with no users
    user_count = db_session.query(models.User).count()
    assert user_count == 0, f"Expected 0 users, found {user_count}"
    
    # Check that we start with no plants
    plant_count = db_session.query(models.Plant).count()
    assert plant_count == 0, f"Expected 0 plants, found {plant_count}"
    
    print("✅ Database starts clean for each test")


def test_database_engine_type(db_session):
    """Test that we're using SQLite in-memory database."""
    # Get the database engine URL
    engine_url = str(db_session.bind.url)
    
    # Verify it's SQLite in-memory
    assert "sqlite" in engine_url
    assert ":memory:" in engine_url
    
    print(f"✅ Using correct database engine: {engine_url}")


def test_data_isolation_between_tests(db_session):
    """Test that data created in one test doesn't affect another."""
    from app import models
    
    # Create a test user
    user = models.User(
        cognito_user_id="isolation-test-123",
        email="isolation@test.com",
        name="Isolation Test User"
    )
    db_session.add(user)
    db_session.commit()
    
    # Verify user was created
    user_count = db_session.query(models.User).count()
    assert user_count == 1
    
    print("✅ Data isolation test passed - user created in isolated environment")
    
    # Note: This user will be automatically cleaned up by the transaction rollback