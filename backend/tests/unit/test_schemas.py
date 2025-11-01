"""
Unit tests for Pydantic schemas.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app import schemas


@pytest.mark.unit
class TestUserSchemas:
    """Test cases for User schemas."""
    
    def test_user_create_valid(self):
        """Test creating a valid UserCreate schema."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "cognito_user_id": "test-cognito-123"
        }
        
        user = schemas.UserCreate(**user_data)
        
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.cognito_user_id == "test-cognito-123"
    
    def test_user_create_invalid_email(self):
        """Test UserCreate with invalid email."""
        user_data = {
            "email": "invalid-email",
            "name": "Test User",
            "cognito_user_id": "test-cognito-123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            schemas.UserCreate(**user_data)
        
        assert "value is not a valid email address" in str(exc_info.value)
    
    def test_user_update_optional_fields(self):
        """Test UserUpdate with optional fields."""
        # Test with name
        user_update = schemas.UserUpdate(name="Updated Name")
        assert user_update.name == "Updated Name"
        
        # Test with no fields (all optional)
        user_update_empty = schemas.UserUpdate()
        assert user_update_empty.name is None


@pytest.mark.unit
class TestPlantSchemas:
    """Test cases for Plant schemas."""
    
    def test_plant_create_valid(self):
        """Test creating a valid PlantCreate schema."""
        plant_data = {
            "name": "My Monstera",
            "species": "Monstera deliciosa"
        }
        
        plant = schemas.PlantCreate(**plant_data)
        
        assert plant.name == "My Monstera"
        assert plant.species == "Monstera deliciosa"
    
    def test_add_to_garden_request_valid(self):
        """Test creating a valid AddToGardenRequest schema."""
        request_data = {
            "plant_name": "My Fiddle Leaf Fig",
            "species": "Ficus lyrata",
            "health_score": 85.0,
            "plant_icon": "🌿",
            "disease_detected": None,
            "is_healthy": True,
            "care_notes": "Looks healthy with good leaf color"
        }
        
        request = schemas.AddToGardenRequest(**request_data)
        
        assert request.plant_name == "My Fiddle Leaf Fig"
        assert request.species == "Ficus lyrata"
        assert request.health_score == 85.0
        assert request.plant_icon == "🌿"
        assert request.disease_detected is None
        assert request.is_healthy is True
        assert request.care_notes == "Looks healthy with good leaf color"
    
    def test_add_to_garden_request_defaults(self):
        """Test AddToGardenRequest with default values."""
        request_data = {
            "plant_name": "Test Plant",
            "species": "Test Species"
        }
        
        request = schemas.AddToGardenRequest(**request_data)
        
        assert request.health_score == 100.0  # Default value
        assert request.plant_icon is None  # Default value
        assert request.disease_detected is None  # Default value
        assert request.is_healthy is True  # Default value
        assert request.care_notes is None  # Default value
    
    def test_plant_update_optional_fields(self):
        """Test PlantUpdate with optional fields."""
        # Test with name only
        update = schemas.PlantUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.current_health_score is None
        
        # Test with health score only
        update = schemas.PlantUpdate(current_health_score=75.0)
        assert update.name is None
        assert update.current_health_score == 75.0
        
        # Test with no fields
        update = schemas.PlantUpdate()
        assert update.name is None
        assert update.current_health_score is None


@pytest.mark.unit
class TestPlantScanSchemas:
    """Test cases for PlantScan schemas."""
    
    def test_plant_scan_create_valid(self):
        """Test creating a valid PlantScanCreate schema."""
        scan_data = {
            "plant_id": "test-plant-123",
            "health_score": 90.0,
            "care_notes": "Plant looks very healthy",
            "disease_detected": None,
            "is_healthy": True
        }
        
        scan = schemas.PlantScanCreate(**scan_data)
        
        assert scan.plant_id == "test-plant-123"
        assert scan.health_score == 90.0
        assert scan.care_notes == "Plant looks very healthy"
        assert scan.disease_detected is None
        assert scan.is_healthy is True
    
    def test_plant_scan_create_defaults(self):
        """Test PlantScanCreate with default values."""
        scan_data = {
            "plant_id": "test-plant-123",
            "health_score": 85.0
        }
        
        scan = schemas.PlantScanCreate(**scan_data)
        
        assert scan.care_notes is None  # Default value
        assert scan.disease_detected is None  # Default value
        assert scan.is_healthy is True  # Default value
    
    def test_scan_result_valid(self):
        """Test creating a valid ScanResult schema."""
        result_data = {
            "species": "Monstera deliciosa",
            "confidence": 0.95,
            "is_healthy": True,
            "disease": None,
            "health_score": 88.0,
            "care_recommendations": [
                "Water when top inch of soil is dry",
                "Provide bright, indirect light",
                "Maintain humidity above 50%"
            ]
        }
        
        result = schemas.ScanResult(**result_data)
        
        assert result.species == "Monstera deliciosa"
        assert result.confidence == 0.95
        assert result.is_healthy is True
        assert result.disease is None
        assert result.health_score == 88.0
        assert len(result.care_recommendations) == 3
        assert "Water when top inch of soil is dry" in result.care_recommendations


@pytest.mark.unit
class TestAchievementSchemas:
    """Test cases for Achievement schemas."""
    
    def test_achievement_create_valid(self):
        """Test creating a valid AchievementCreate schema."""
        achievement_data = {
            "name": "Plant Parent",
            "description": "Add your first plant to the garden",
            "icon": "🌱",
            "achievement_type": "plants_count",
            "requirement_value": 1,
            "points_awarded": 10
        }
        
        achievement = schemas.AchievementCreate(**achievement_data)
        
        assert achievement.name == "Plant Parent"
        assert achievement.description == "Add your first plant to the garden"
        assert achievement.icon == "🌱"
        assert achievement.achievement_type == "plants_count"
        assert achievement.requirement_value == 1
        assert achievement.points_awarded == 10
    
    def test_achievement_create_defaults(self):
        """Test AchievementCreate with default values."""
        achievement_data = {
            "name": "Test Achievement",
            "description": "Test description",
            "achievement_type": "test",
            "requirement_value": 5
        }
        
        achievement = schemas.AchievementCreate(**achievement_data)
        
        assert achievement.icon is None  # Default value
        assert achievement.points_awarded == 10  # Default value
    
    def test_user_achievement_create_valid(self):
        """Test creating a valid UserAchievementCreate schema."""
        user_achievement_data = {
            "achievement_id": "test-achievement-123",
            "current_progress": 3
        }
        
        user_achievement = schemas.UserAchievementCreate(**user_achievement_data)
        
        assert user_achievement.achievement_id == "test-achievement-123"
        assert user_achievement.current_progress == 3
    
    def test_user_achievement_create_defaults(self):
        """Test UserAchievementCreate with default values."""
        user_achievement_data = {
            "achievement_id": "test-achievement-123"
        }
        
        user_achievement = schemas.UserAchievementCreate(**user_achievement_data)
        
        assert user_achievement.current_progress == 0  # Default value


@pytest.mark.unit
class TestDashboardSchemas:
    """Test cases for Dashboard schemas."""
    
    def test_dashboard_stats_valid(self):
        """Test creating a valid DashboardStats schema."""
        stats_data = {
            "total_plants": 5,
            "healthy_plants": 4,
            "plants_needing_care": 1,
            "current_streak": 7,
            "total_scans": 15,
            "achievements_earned": 3,
            "coins_earned": 125
        }
        
        stats = schemas.DashboardStats(**stats_data)
        
        assert stats.total_plants == 5
        assert stats.healthy_plants == 4
        assert stats.plants_needing_care == 1
        assert stats.current_streak == 7
        assert stats.total_scans == 15
        assert stats.achievements_earned == 3
        assert stats.coins_earned == 125
    
    def test_dashboard_plant_valid(self):
        """Test creating a valid DashboardPlant schema."""
        plant_data = {
            "id": "test-plant-123",
            "name": "My Monstera",
            "species": "Monstera deliciosa",
            "health_score": 85.0,
            "streak_days": 5,
            "last_check_in": datetime.now(),
            "needs_attention": False
        }
        
        plant = schemas.DashboardPlant(**plant_data)
        
        assert plant.id == "test-plant-123"
        assert plant.name == "My Monstera"
        assert plant.species == "Monstera deliciosa"
        assert plant.health_score == 85.0
        assert plant.streak_days == 5
        assert plant.needs_attention is False


@pytest.mark.unit
class TestPlantIdentificationSchemas:
    """Test cases for Plant Identification schemas."""
    
    def test_plant_identification_request_with_base64(self):
        """Test PlantIdentificationRequest with base64 image."""
        request_data = {
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        }
        
        request = schemas.PlantIdentificationRequest(**request_data)
        
        assert request.image_base64 is not None
        assert request.image_url is None
    
    def test_plant_identification_request_with_url(self):
        """Test PlantIdentificationRequest with image URL."""
        request_data = {
            "image_url": "https://example.com/plant.jpg"
        }
        
        request = schemas.PlantIdentificationRequest(**request_data)
        
        assert request.image_base64 is None
        assert request.image_url == "https://example.com/plant.jpg"
    
    def test_plant_identification_response_valid(self):
        """Test creating a valid PlantIdentificationResponse schema."""
        response_data = {
            "species": "Monstera deliciosa",
            "common_name": "Swiss Cheese Plant",
            "confidence": 0.92,
            "care_difficulty": "Easy",
            "care_recommendations": [
                "Water when top inch of soil is dry",
                "Provide bright, indirect light"
            ]
        }
        
        response = schemas.PlantIdentificationResponse(**response_data)
        
        assert response.species == "Monstera deliciosa"
        assert response.common_name == "Swiss Cheese Plant"
        assert response.confidence == 0.92
        assert response.care_difficulty == "Easy"
        assert len(response.care_recommendations) == 2


@pytest.mark.unit
class TestErrorSchemas:
    """Test cases for Error schemas."""
    
    def test_error_response_valid(self):
        """Test creating a valid ErrorResponse schema."""
        error_data = {
            "detail": "Plant not found",
            "error_code": "PLANT_NOT_FOUND"
        }
        
        error = schemas.ErrorResponse(**error_data)
        
        assert error.detail == "Plant not found"
        assert error.error_code == "PLANT_NOT_FOUND"
    
    def test_error_response_without_code(self):
        """Test ErrorResponse without error code."""
        error_data = {
            "detail": "Something went wrong"
        }
        
        error = schemas.ErrorResponse(**error_data)
        
        assert error.detail == "Something went wrong"
        assert error.error_code is None