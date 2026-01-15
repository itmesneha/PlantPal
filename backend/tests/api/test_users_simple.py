"""
Simplified API tests for user endpoints using dependency overrides
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.auth import get_current_user_info

client = TestClient(app)


@pytest.mark.api
class TestUserEndpointsSimple:
    """Test user API endpoints with proper authentication mocking"""

    def test_get_current_user_unauthorized(self):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403

    def test_get_current_user_new_user(self, test_db):
        """Test getting current user creates new user if not exists"""
        # Override the authentication dependency
        def mock_get_current_user_info():
            return {
                "cognito_user_id": "new-user-123",
                "email": "newuser@test.com",
                "name": "New User"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/users/me")
            assert response.status_code == 200
            
            data = response.json()
            assert data["email"] == "newuser@test.com"
            assert data["name"] == "New User"
            assert data["cognito_user_id"] == "new-user-123"
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_get_current_user_existing_user(self, test_db):
        """Test getting existing user"""
        # Create a unique user for this test
        from app import models
        unique_user = models.User(
            cognito_user_id="existing-user-unique-123",
            email="existing@unique.com",
            name="Existing User"
        )
        test_db.add(unique_user)
        test_db.commit()
        test_db.refresh(unique_user)
        
        # Override the authentication dependency to return this user's info
        def mock_get_current_user_info():
            return {
                "cognito_user_id": unique_user.cognito_user_id,
                "email": unique_user.email,
                "name": unique_user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/users/me")
            assert response.status_code == 200
            
            data = response.json()
            assert data["email"] == unique_user.email
            assert data["name"] == unique_user.name
            assert data["cognito_user_id"] == unique_user.cognito_user_id
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_create_user_success(self, test_db):
        """Test creating a new user"""
        user_data = {
            "cognito_user_id": "create-user-123",
            "email": "createuser@test.com",
            "name": "Create User"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200  # API returns 200 for both new and existing users
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]

    def test_create_user_duplicate(self, test_db):
        """Test creating duplicate user returns existing user"""
        # Create a unique user for this test
        from app import models
        unique_user = models.User(
            cognito_user_id="duplicate-user-unique-456",
            email="duplicate@unique.com",
            name="Duplicate User"
        )
        test_db.add(unique_user)
        test_db.commit()
        test_db.refresh(unique_user)
        
        # Try to create the same user again
        user_data = {
            "cognito_user_id": unique_user.cognito_user_id,
            "email": unique_user.email,
            "name": unique_user.name
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200  # Returns existing user
        
        data = response.json()
        assert data["email"] == unique_user.email
        assert data["name"] == unique_user.name
        assert data["cognito_user_id"] == unique_user.cognito_user_id

    def test_create_test_user_new(self, test_db):
        """Test creating a new test user"""
        response = client.post("/api/v1/users/test")
        assert response.status_code == 200  # API returns 200 for both new and existing users
        
        data = response.json()
        assert data["email"] == "testuser@plantpal.com"
        # The name might be different if user already exists, so just check it's not empty
        assert data["name"] is not None
        assert len(data["name"]) > 0

    def test_create_test_user_existing(self, test_db):
        """Test creating test user when it already exists"""
        # Create test user first
        test_user = models.User(
            cognito_user_id="test-user-plantpal",
            email="testuser@plantpal.com",
            name="Test User"
        )
        test_db.add(test_user)
        test_db.commit()
        
        response = client.post("/api/v1/users/test")
        assert response.status_code == 200  # Returns existing user
        
        data = response.json()
        assert data["email"] == "testuser@plantpal.com"

    def test_create_user_invalid_data(self, test_db):
        """Test creating user with invalid data"""
        user_data = {
            "email": "invalid-email",  # Invalid email format
            "name": "Test User"
            # Missing cognito_user_id
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 422  # Validation error