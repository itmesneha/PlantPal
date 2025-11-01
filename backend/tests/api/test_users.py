"""
API tests for user authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.auth import get_current_user_info


@pytest.mark.api
class TestUserEndpoints:
    """Test user authentication and management endpoints"""

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]

    def test_get_current_user_new_user(self, client: TestClient, test_db):
        """Test get current user creates new user from JWT claims"""
        # Mock user info
        mock_user_info = {
            "cognito_user_id": "test-cognito-123",
            "email": "newuser@test.com",
            "name": "New User"
        }
        
        # Override the dependency
        async def mock_get_current_user_info():
            return mock_user_info
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/users/me")
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "newuser@test.com"
            assert data["name"] == "New User"
            assert data["cognito_user_id"] == "test-cognito-123"
            assert "id" in data
            assert "created_at" in data
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_current_user_existing_user(self, client: TestClient, test_db, test_user):
        """Test get current user returns existing user"""
        # Mock user info
        mock_user_info = {
            "cognito_user_id": test_user.cognito_user_id,
            "email": test_user.email,
            "name": test_user.name
        }
        
        # Override the dependency
        async def mock_get_current_user_info():
            return mock_user_info
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/users/me")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == test_user.id
            assert data["email"] == test_user.email
            assert data["name"] == test_user.name
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_create_user_success(self, client: TestClient, test_db):
        """Test creating a new user via API"""
        user_data = {
            "cognito_user_id": "new-cognito-456",
            "email": "apiuser@test.com",
            "name": "API User"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "apiuser@test.com"
        assert data["name"] == "API User"
        assert data["cognito_user_id"] == "new-cognito-456"

    def test_create_user_duplicate(self, client: TestClient, test_db, test_user):
        """Test creating user with existing cognito_user_id returns existing user"""
        user_data = {
            "cognito_user_id": test_user.cognito_user_id,
            "email": "duplicate@test.com",
            "name": "Duplicate User"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should return existing user, not create new one
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email  # Original email preserved
        assert data["name"] == test_user.name    # Original name preserved

    def test_create_test_user_new(self, client: TestClient, test_db):
        """Test creating a new test user"""
        response = client.post("/api/v1/users/test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "testuser@plantpal.com"
        assert data["name"] == "Sarah Green"
        assert "cognito_user_id" in data
        assert data["cognito_user_id"].startswith("test-user-")

    def test_create_test_user_existing(self, client: TestClient, test_db):
        """Test creating test user when one already exists"""
        # First create a test user
        response1 = client.post("/api/v1/users/test")
        assert response1.status_code == 200
        user1_data = response1.json()
        
        # Try to create another test user
        response2 = client.post("/api/v1/users/test")
        assert response2.status_code == 200
        user2_data = response2.json()
        
        # Should return the same user
        assert user1_data["id"] == user2_data["id"]
        assert user1_data["email"] == user2_data["email"]

    def test_create_user_invalid_data(self, client: TestClient, test_db):
        """Test creating user with invalid data"""
        invalid_data = {
            "email": "invalid-email",  # Missing cognito_user_id and name
        }
        
        response = client.post("/api/v1/users/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_get_current_user_auth_error(self, client: TestClient, test_db):
        """Test get current user handles authentication errors"""
        # Override the dependency to raise an HTTPException
        async def mock_get_current_user_info():
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/users/me")
            assert response.status_code == 401
            assert "detail" in response.json()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_user_endpoints_require_valid_json(self, client: TestClient, test_db):
        """Test that user creation endpoints require valid JSON"""
        response = client.post(
            "/api/v1/users/", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_get_current_user_with_minimal_jwt_claims(self, client: TestClient, test_db):
        """Test get current user with minimal JWT claims (only required fields)"""
        # Mock user info with minimal claims
        mock_user_info = {
            "cognito_user_id": "minimal-user-123",
            "email": "minimal@test.com",
            "name": None,
            "username": None
        }
        
        # Override the dependency
        async def mock_get_current_user_info():
            return mock_user_info
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/users/me")
            assert response.status_code == 200
            
            data = response.json()
            assert data["email"] == "minimal@test.com"
            assert data["name"] == "Plant Lover"  # Should use default fallback when name and username are None
            assert data["cognito_user_id"] == "minimal-user-123"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_current_user_with_no_name_or_username(self, client: TestClient, test_db):
        """Test get current user when JWT has no name or username"""
        # Mock user info with no name or username
        mock_user_info = {
            "cognito_user_id": "noname-user-123",
            "email": "noname@test.com",
            "name": None,
            "username": None
        }
        
        # Override the dependency
        async def mock_get_current_user_info():
            return mock_user_info
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/users/me")
            assert response.status_code == 200
            
            data = response.json()
            assert data["email"] == "noname@test.com"
            assert data["name"] == "Plant Lover"  # Should use default fallback
            assert data["cognito_user_id"] == "noname-user-123"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()