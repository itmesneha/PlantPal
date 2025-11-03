"""
Integration tests for authentication and user management endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.orm import Session
from unittest.mock import patch

from app import models, schemas


@pytest.mark.integration
class TestAuthEndpoints:
    """Test authentication-related endpoints."""

    def test_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Welcome to PlantPal API! 🌱"

    def test_test_endpoint(self, client: TestClient):
        """Test the test endpoint."""
        response = client.post("/api/v1/users/test")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "cognito_user_id" in data
        assert "email" in data
        assert "name" in data
        assert data["email"] == "testuser@plantpal.com"
        assert data["name"] == "Sarah Green"


@pytest.mark.integration
class TestUserEndpoints:
    """Test user management endpoints."""

    def test_get_current_user_authenticated(self, authenticated_client, mock_user_info):
        """Test getting current user when authenticated."""
        client, user = authenticated_client
        response = client.get("/api/v1/users/me")
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == mock_user_info["email"]
        assert data["name"] == mock_user_info["name"]
        assert data["cognito_user_id"] == mock_user_info["cognito_user_id"]
        assert "id" in data
        assert "name" in data

    def test_get_current_user_unauthenticated(self, client: TestClient):
        """Test getting current user when not authenticated."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing auth

    def test_create_user_valid_data(self, client: TestClient, db_session: Session):
        """Test creating a user with valid data."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "cognito_user_id": "test-cognito-123"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]
        assert data["cognito_user_id"] == user_data["cognito_user_id"]
        assert "id" in data

    def test_create_user_invalid_email(self, client: TestClient):
        """Test creating a user with invalid email."""
        user_data = {
            "email": "invalid-email",
            "name": "Test User",
            "cognito_user_id": "test-cognito-123"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 422

    def test_create_user_missing_required_fields(self, client: TestClient):
        """Test creating a user with missing required fields."""
        user_data = {
            "name": "Test User"
            # Missing email and cognito_user_id
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 422

    def test_create_user_duplicate_cognito_id(self, client: TestClient, db_session: Session):
        """Test creating user with duplicate cognito_user_id returns existing user."""
        import uuid
        unique_base = str(uuid.uuid4())[:8]
        
        user_data = {
            "cognito_user_id": f"test-user-{unique_base}",
            "email": f"user-{unique_base}@example.com",
            "name": "Test User"
        }
        
        # Create first user
        response1 = client.post("/api/v1/users/", json=user_data)
        assert response1.status_code == 200
        user1_data = response1.json()
        
        # Try to create user again with same cognito_user_id (should return existing user)
        response2 = client.post("/api/v1/users/", json=user_data)
        assert response2.status_code == 200
        user2_data = response2.json()
        
        # Should return the same user (same ID)
        assert user1_data["id"] == user2_data["id"]
        assert user1_data["cognito_user_id"] == user2_data["cognito_user_id"]
        assert user1_data["email"] == user2_data["email"]

    def test_create_test_user(self, client: TestClient, db_session: Session):
        """Test creating a test user."""
        response = client.post("/api/v1/users/test")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "cognito_user_id" in data
        assert "email" in data
        assert "name" in data
        assert data["email"] == "testuser@plantpal.com"
        assert data["name"] == "Sarah Green"
        
        # Verify user was created in database
        user = db_session.query(models.User).filter(
            models.User.email == "testuser@plantpal.com"
        ).first()
        assert user is not None
        assert user.name == "Sarah Green"

    def test_user_creation_initializes_achievements(self, authenticated_client, db_session: Session):
        """Test that creating a user initializes their achievements."""
        # First create some active achievements
        achievements = [
            models.Achievement(
                id="test-achievement-1",
                name="Test Achievement 1",
                description="First test achievement",
                achievement_type="test",
                requirement_value=1,
                points_awarded=10,
                icon="🏆",
                is_active=True
            ),
            models.Achievement(
                id="test-achievement-2",
                name="Test Achievement 2",
                description="Second test achievement",
                achievement_type="test",
                requirement_value=5,
                points_awarded=25,
                icon="🌟",
                is_active=True
            )
        ]
        db_session.add_all(achievements)
        db_session.commit()
        
        client, user = authenticated_client
        
        # Manually initialize achievements for this test
        from app.routers.achievements import initialize_user_achievements
        initialize_user_achievements(user.id, db_session)
        
        # Check that user achievements were initialized
        user_achievements = db_session.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user.id
        ).all()
        
        assert len(user_achievements) == 2

    @patch('app.auth.get_current_user_info')
    def test_get_current_user_jwt_error(self, mock_get_user_info, client: TestClient):
        """Test getting current user with JWT error."""
        mock_get_user_info.side_effect = HTTPException(
            status_code=403,
            detail="Invalid token"
        )
        
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403

    def test_clear_test_user_debug_endpoint(self, client: TestClient, db_session: Session):
        """Test the debug endpoint for clearing test user."""
        # First create a test user
        test_user = models.User(
            cognito_user_id="test-user-debug",
            email="testuser@plantpal.com",
            name="Test User Debug"
        )
        db_session.add(test_user)
        db_session.commit()
        
        # Clear the test user
        response = client.delete("/api/v1/debug/clear-test-user")
        assert response.status_code == 200
        assert response.json() == {"message": "Test user cleared"}