"""
API tests for dashboard endpoints using dependency overrides
"""
import pytest
from datetime import datetime, timedelta
from app.main import app
from app import models
from app.auth import get_current_user_info


@pytest.mark.api
class TestDashboardEndpoints:
    """Test dashboard API endpoints"""

    def test_get_dashboard_success(self, client, db_session):
        """Test getting dashboard data"""
        # Create a unique user and plant for this test
        user = models.User(
            cognito_user_id="dashboard-user-123",
            email="dashboard@test.com",
            name="Dashboard User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        plant = models.Plant(
            user_id=user.id,
            name="Test Plant",
            species="Test Species",
            current_health_score=85.0,
            streak_days=5,
            last_check_in=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(plant)
        db_session.commit()
        
        # Mock authentication
        def mock_get_current_user_info():
            return {
                "cognito_user_id": user.cognito_user_id,
                "email": user.email,
                "name": user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/dashboard")
            assert response.status_code == 200
            
            data = response.json()
            assert "user" in data
            assert "stats" in data
            assert "recent_plants" in data
            assert "recent_achievements" in data
            
            # Check user data
            assert data["user"]["email"] == user.email
            
            # Check stats structure
            stats = data["stats"]
            assert "total_plants" in stats
            assert "healthy_plants" in stats
            assert "plants_needing_care" in stats
            assert "current_streak" in stats
            assert "total_scans" in stats
            assert "achievements_earned" in stats
        finally:
            app.dependency_overrides.clear()

    def test_get_dashboard_user_not_found(self, client, db_session):
        """Test getting dashboard for non-existent user"""
        # Mock authentication for non-existent user
        def mock_get_current_user_info():
            return {
                "cognito_user_id": "non-existent-user",
                "email": "nonexistent@example.com", 
                "name": "Non Existent User",
                "username": "nonexistent"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/dashboard")
            assert response.status_code == 404
            assert response.json()["detail"] == "User not found"
        finally:
            app.dependency_overrides.clear()

    def test_get_dashboard_unauthorized(self, client):
        """Test getting dashboard without authentication"""
        response = client.get("/api/v1/dashboard")
        assert response.status_code == 403

    def test_get_dashboard_with_multiple_plants(self, client, db_session):
        """Test dashboard with multiple plants of varying health"""
        # Create user
        user = models.User(
            cognito_user_id="multi-plant-user-123",
            email="multiplant@test.com",
            name="Multi Plant User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create plants with different health scores
        plants = [
            models.Plant(
                user_id=user.id,
                name="Healthy Plant 1",
                species="Species A",
                current_health_score=85.0,
                streak_days=10,
                last_check_in=datetime.utcnow() - timedelta(days=1)
            ),
            models.Plant(
                user_id=user.id,
                name="Healthy Plant 2",
                species="Species B",
                current_health_score=75.0,
                streak_days=7,
                last_check_in=datetime.utcnow() - timedelta(days=2)
            ),
            models.Plant(
                user_id=user.id,
                name="Sick Plant",
                species="Species C",
                current_health_score=45.0,
                streak_days=2,
                last_check_in=datetime.utcnow() - timedelta(days=10)
            )
        ]
        
        for plant in plants:
            db_session.add(plant)
        db_session.commit()
        
        # Mock authentication
        def mock_get_current_user_info():
            return {
                "cognito_user_id": user.cognito_user_id,
                "email": user.email,
                "name": user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/dashboard")
            assert response.status_code == 200
            
            data = response.json()
            stats = data["stats"]
            
            # Should have 3 total plants, 2 healthy, 1 needing care
            assert stats["total_plants"] == 3
            assert stats["healthy_plants"] == 2
            assert stats["plants_needing_care"] == 1
        finally:
            app.dependency_overrides.clear()

    def test_get_dashboard_empty_user(self, client, db_session):
        """Test dashboard for user with no plants"""
        # Mock authentication for non-existent user (should return 404)
        def mock_get_current_user_info():
            return {
                "cognito_user_id": "empty-user",
                "email": "empty@example.com",
                "name": "Empty User",
                "username": "emptyuser"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/dashboard")
            assert response.status_code == 404
            assert response.json()["detail"] == "User not found"
        finally:
            app.dependency_overrides.clear()

    def test_get_dashboard_recent_plants_limit(self, client, db_session):
        """Test that recent plants are limited to 5"""
        # Create user
        user = models.User(
            cognito_user_id="limit-user-123",
            email="limit@test.com",
            name="Limit User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create 7 plants to test the limit
        for i in range(7):
            plant = models.Plant(
                user_id=user.id,
                name=f"Plant {i+1}",
                species=f"Species {i+1}",
                current_health_score=80.0,
                streak_days=i+1,
                last_check_in=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(plant)
        db_session.commit()
        
        # Mock authentication
        def mock_get_current_user_info():
            return {
                "cognito_user_id": user.cognito_user_id,
                "email": user.email,
                "name": user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/dashboard")
            assert response.status_code == 200
            
            data = response.json()
            
            # Should have 7 total plants but only 5 recent plants
            assert data["stats"]["total_plants"] == 7
            assert len(data["recent_plants"]) <= 5
        finally:
            app.dependency_overrides.clear()

    def test_get_dashboard_needs_attention_flag(self, client, db_session):
        """Test that needs_attention flag is set correctly"""
        # Create user
        user = models.User(
            cognito_user_id="attention-user-123",
            email="attention@test.com",
            name="Attention User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create plants - one needing attention, one healthy
        sick_plant = models.Plant(
            user_id=user.id,
            name="Sick Plant",
            species="Unhealthy Species",
            current_health_score=65.0,  # Below 70 threshold
            streak_days=2,
            last_check_in=datetime.utcnow() - timedelta(days=10)
        )
        
        healthy_plant = models.Plant(
            user_id=user.id,
            name="Healthy Plant",
            species="Happy Species",
            current_health_score=85.0,  # Above 70 threshold
            streak_days=15,
            last_check_in=datetime.utcnow() - timedelta(days=1)
        )
        
        db_session.add(sick_plant)
        db_session.add(healthy_plant)
        db_session.commit()
        
        # Mock authentication
        def mock_get_current_user_info():
            return {
                "cognito_user_id": user.cognito_user_id,
                "email": user.email,
                "name": user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/dashboard")
            assert response.status_code == 200
            
            data = response.json()
            recent_plants = data["recent_plants"]
            
            # Find the plants in the response
            sick_plant_data = None
            healthy_plant_data = None
            
            for plant_data in recent_plants:
                if plant_data["name"] == "Sick Plant":
                    sick_plant_data = plant_data
                elif plant_data["name"] == "Healthy Plant":
                    healthy_plant_data = plant_data
            
            # Check needs_attention flags
            assert sick_plant_data is not None
            assert healthy_plant_data is not None
            assert sick_plant_data["needs_attention"] == True
            assert healthy_plant_data["needs_attention"] == False
        finally:
            app.dependency_overrides.clear()