"""
API tests for plant management endpoints
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.main import app
from app import models
from app.auth import get_current_user_info


@pytest.mark.api
class TestPlantEndpoints:
    """Test plant management API endpoints"""

    def test_get_user_plants_success(self, client, db_session):
        """Test getting user's plants"""
        # Create a unique user for this test
        unique_user = models.User(
            cognito_user_id=f"test-user-plants-success-{datetime.now().timestamp()}",
            email=f"plants-success-{datetime.now().timestamp()}@example.com",
            name="Plants Success User"
        )
        db_session.add(unique_user)
        db_session.commit()
        db_session.refresh(unique_user)
        
        # Create a plant for the user
        plant = models.Plant(
            name="Test Plant",
            species="Test Species",
            user_id=unique_user.id,
            current_health_score=85,
            streak_days=5,
            last_check_in=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(plant)
        db_session.commit()
        
        # Mock authentication to return our test user
        def mock_get_current_user_info():
            return {
                "cognito_user_id": unique_user.cognito_user_id,
                "email": unique_user.email,
                "name": unique_user.name,
                "username": "testuser"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/plants/")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1
            assert data[0]["id"] == plant.id
            assert data[0]["name"] == plant.name
            assert data[0]["species"] == plant.species
        finally:
            app.dependency_overrides.clear()

    def test_get_user_plants_empty(self, client, db_session):
        """Test getting plants for user with no plants"""
        # Create a unique user for this test
        unique_user = models.User(
            cognito_user_id=f"test-user-plants-empty-{datetime.now().timestamp()}",
            email=f"plants-empty-{datetime.now().timestamp()}@example.com",
            name="Plants Empty User"
        )
        db_session.add(unique_user)
        db_session.commit()
        db_session.refresh(unique_user)
        
        # Mock authentication to return our test user
        def mock_get_current_user_info():
            return {
                "cognito_user_id": unique_user.cognito_user_id,
                "email": unique_user.email,
                "name": unique_user.name,
                "username": "testuser"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/plants/")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0
        finally:
            app.dependency_overrides.clear()

    def test_get_user_plants_user_not_found(self, client, db_session):
        """Test getting plants for non-existent user"""
        # Mock authentication with non-existent user
        def mock_get_current_user_info():
            return {
                "cognito_user_id": "non-existent-user",
                "email": "nonexistent@test.com",
                "name": "Non Existent",
                "username": "nonexistent"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/plants/")
            assert response.status_code == 404
            assert "User not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_user_plants_unauthorized(self, client):
        """Test getting plants without authentication"""
        response = client.get("/api/v1/plants/")
        assert response.status_code == 403

    def test_get_user_plants_pagination(self, client, db_session):
        """Test plants endpoint with pagination parameters"""
        # Create a unique user for this test
        unique_user = models.User(
            cognito_user_id=f"test-user-plants-pagination-{datetime.now().timestamp()}",
            email=f"plants-pagination-{datetime.now().timestamp()}@example.com",
            name="Plants Pagination User"
        )
        db_session.add(unique_user)
        db_session.commit()
        db_session.refresh(unique_user)
        
        # Create multiple plants
        for i in range(5):
            plant = models.Plant(
                user_id=unique_user.id,
                name=f"Test Plant {i}",
                species=f"Test Species {i}",
                current_health_score=85,
                streak_days=5,
                last_check_in=datetime.utcnow() - timedelta(days=1)
            )
            db_session.add(plant)
        db_session.commit()
        
        # Mock authentication to return our test user
        def mock_get_current_user_info():
            return {
                "cognito_user_id": unique_user.cognito_user_id,
                "email": unique_user.email,
                "name": unique_user.name,
                "username": "testuser"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            # Test pagination
            response = client.get("/api/v1/plants/?skip=2&limit=2")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 2
        finally:
            app.dependency_overrides.clear()

    def test_add_to_garden_success(self, client, db_session):
        """Test adding plant to garden"""
        # Create a unique user for this test
        unique_user = models.User(
            cognito_user_id=f"test-user-add-garden-{datetime.now().timestamp()}",
            email=f"add-garden-{datetime.now().timestamp()}@example.com",
            name="Add Garden User"
        )
        db_session.add(unique_user)
        db_session.commit()
        db_session.refresh(unique_user)
        
        # Initialize achievements for the test user
        from app.routers.achievements import initialize_user_achievements
        initialize_user_achievements(unique_user.id, db_session)
        
        # Mock authentication to return our test user
        def mock_get_current_user_info():
            return {
                "cognito_user_id": unique_user.cognito_user_id,
                "email": unique_user.email,
                "name": unique_user.name,
                "username": "testuser"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            plant_data = {
                "plant_name": "My Rose",
                "species": "Rosa rubiginosa",
                "health_score": 85.0,
                "plant_icon": "🌹"
            }
            
            response = client.post("/api/v1/plants/add-to-garden", json=plant_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] == True
            assert "plant_id" in data
            assert "message" in data
        finally:
            app.dependency_overrides.clear()

    def test_add_to_garden_user_not_found(self, client, db_session):
        """Test adding plant to garden for non-existent user"""
        # Mock authentication with non-existent user
        def mock_get_current_user_info():
            return {
                "cognito_user_id": "non-existent-user",
                "email": "nonexistent@test.com",
                "name": "Non Existent",
                "username": "nonexistent"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            plant_data = {
                "plant_name": "My Rose",
                "species": "Rosa rubiginosa",
                "health_score": 85.0,
                "plant_icon": "🌹"
            }
            
            response = client.post("/api/v1/plants/add-to-garden", json=plant_data)
            assert response.status_code == 404
            assert "User not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_add_to_garden_unauthorized(self, client):
        """Test adding plant to garden without authentication"""
        plant_data = {
            "plant_name": "My Rose",
            "species": "Rosa rubiginosa",
            "health_score": 85.0,
            "plant_icon": "🌹"
        }
        
        response = client.post("/api/v1/plants/add-to-garden", json=plant_data)
        assert response.status_code == 403

    def test_add_to_garden_invalid_data(self, client, db_session):
        """Test adding plant with invalid data"""
        # Create a unique user for this test
        unique_user = models.User(
            cognito_user_id=f"test-user-invalid-data-{datetime.now().timestamp()}",
            email=f"invalid-data-{datetime.now().timestamp()}@example.com",
            name="Invalid Data User"
        )
        db_session.add(unique_user)
        db_session.commit()
        db_session.refresh(unique_user)
        
        # Mock authentication to return our test user
        def mock_get_current_user_info():
            return {
                "cognito_user_id": unique_user.cognito_user_id,
                "email": unique_user.email,
                "name": unique_user.name,
                "username": "testuser"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            # Missing required fields
            invalid_data = {
                "species": "Rosa rubiginosa"
                # Missing plant_name
            }
            
            response = client.post("/api/v1/plants/add-to-garden", json=invalid_data)
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()

    def test_update_plant_success(self, client, db_session):
        """Test updating a plant"""
        # Create a unique user for this test
        user = models.User(
            id="test-user-update-success",
            cognito_user_id="test-cognito-update-success",
            email="test-update-success@example.com",
            name="Test User Update Success"
        )
        db_session.add(user)
        
        # Create a plant for this user
        plant = models.Plant(
            id="test-plant-update-success",
            user_id=user.id,
            name="Original Plant Name",
            species="Test Species",
            current_health_score=85.0,
            plant_icon="🌱"
        )
        db_session.add(plant)
        db_session.commit()
        
        # Mock authentication
        app.dependency_overrides[get_current_user_info] = lambda: {
            "cognito_user_id": user.cognito_user_id,
            "email": user.email,
            "name": user.name
        }
        
        try:
            update_data = {
                "name": "Updated Plant Name",
                "plant_icon": "🌺"
            }
            
            response = client.put(f"/api/v1/plants/{plant.id}", json=update_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["name"] == "Updated Plant Name"
            assert data["plant_icon"] == "🌺"
            assert data["id"] == plant.id
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_update_plant_not_found(self, client, db_session):
        """Test updating non-existent plant"""
        # Create a unique user for this test
        user = models.User(
            id="test-user-update-not-found",
            cognito_user_id="test-cognito-update-not-found",
            email="test-update-not-found@example.com",
            name="Test User Update Not Found"
        )
        db_session.add(user)
        db_session.commit()
        
        # Mock authentication
        app.dependency_overrides[get_current_user_info] = lambda: {
            "cognito_user_id": user.cognito_user_id,
            "email": user.email,
            "name": user.name
        }
        
        try:
            update_data = {
                "name": "Updated Plant Name"
            }
            
            response = client.put("/api/v1/plants/nonexistent-plant-id", json=update_data)
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_update_plant_unauthorized_user(self, client, db_session):
        """Test updating plant not owned by user"""
        # Create first user
        user1 = models.User(
            id="test-user-unauthorized-1",
            cognito_user_id="test-cognito-unauthorized-1",
            email="test-unauthorized-1@example.com",
            name="Test User 1"
        )
        db_session.add(user1)
        
        # Create another user and their plant
        other_user = models.User(
            id="test-user-unauthorized-2",
            cognito_user_id="test-cognito-unauthorized-2",
            email="test-unauthorized-2@example.com",
            name="Other User"
        )
        db_session.add(other_user)
        
        other_plant = models.Plant(
            id="test-plant-unauthorized",
            user_id=other_user.id,
            name="Other Plant",
            species="Other Species",
            current_health_score=85.0,
            plant_icon="🌱"
        )
        db_session.add(other_plant)
        db_session.commit()
        
        # Mock authentication as first user
        app.dependency_overrides[get_current_user_info] = lambda: {
            "cognito_user_id": user1.cognito_user_id,
            "email": user1.email,
            "name": user1.name
        }
        
        try:
            update_data = {
                "name": "Hacked Plant"
            }
            
            response = client.put(f"/api/v1/plants/{other_plant.id}", json=update_data)
            assert response.status_code == 404
            assert "Plant not found" in response.json()["detail"]
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_delete_plant_success(self, client, db_session):
        """Test deleting a plant"""
        # Create a unique user for this test
        user = models.User(
            id="test-user-delete-success",
            cognito_user_id="test-cognito-delete-success",
            email="test-delete-success@example.com",
            name="Test User Delete Success"
        )
        db_session.add(user)
        
        # Create a plant for this user
        plant = models.Plant(
            id="test-plant-delete-success",
            user_id=user.id,
            name="Plant to Delete",
            species="Test Species",
            current_health_score=85.0,
            plant_icon="🌱"
        )
        db_session.add(plant)
        db_session.commit()
        
        # Mock authentication
        app.dependency_overrides[get_current_user_info] = lambda: {
            "cognito_user_id": user.cognito_user_id,
            "email": user.email,
            "name": user.name
        }
        
        try:
            response = client.delete(f"/api/v1/plants/{plant.id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] == True
            assert "message" in data
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_delete_plant_not_found(self, client, test_db, test_user):
        """Test deleting a plant that doesn't exist"""
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
            response = client.delete("/api/v1/plants/999999")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_plant_endpoints_require_authentication(self, client):
        """Test that all plant endpoints require authentication"""
        endpoints = [
            ("/api/v1/plants/", "get"),
            ("/api/v1/plants/add-to-garden", "post"),
            ("/api/v1/plants/123", "put"),
            ("/api/v1/plants/123", "delete")
        ]
        
        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(endpoint)
            elif method == "post":
                response = client.post(endpoint, json={})
            elif method == "put":
                response = client.put(endpoint, json={})
            elif method == "delete":
                response = client.delete(endpoint)
            
            assert response.status_code == 403, f"Endpoint {endpoint} ({method}) should require authentication"