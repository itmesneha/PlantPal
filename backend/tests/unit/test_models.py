"""
Unit tests for database models.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app import models


@pytest.mark.unit
class TestUserModel:
    """Test cases for User model."""
    
    def test_create_user(self, db_session: Session):
        """Test creating a new user."""
        user_data = {
            "cognito_user_id": "test-cognito-123",
            "email": "test@example.com",
            "name": "Test User"
        }
        
        user = models.User(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.cognito_user_id == "test-cognito-123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
    
    def test_user_relationships(self, db_session: Session):
        """Test user relationships with plants and scans."""
        # Create user
        user = models.User(
            cognito_user_id="test-user-123",
            email="test@example.com",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create plant for user
        plant = models.Plant(
            user_id=user.id,
            name="Test Plant",
            species="Test Species",
            current_health_score=85.0
        )
        db_session.add(plant)
        db_session.commit()
        
        # Test relationship
        assert len(user.plants) == 1
        assert user.plants[0].name == "Test Plant"
        assert user.plants[0].owner == user


@pytest.mark.unit
class TestPlantModel:
    """Test cases for Plant model."""
    
    def test_create_plant(self, db_session: Session):
        """Test creating a new plant."""
        # First create a user
        user = models.User(
            cognito_user_id="test-user-123",
            email="test@example.com",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create plant
        plant_data = {
            "user_id": user.id,
            "name": "My Monstera",
            "species": "Monstera deliciosa",
            "current_health_score": 90.0,
            "streak_days": 5,
            "plant_icon": "🌿"
        }
        
        plant = models.Plant(**plant_data)
        db_session.add(plant)
        db_session.commit()
        db_session.refresh(plant)
        
        assert plant.id is not None
        assert plant.user_id == user.id
        assert plant.name == "My Monstera"
        assert plant.species == "Monstera deliciosa"
        assert plant.current_health_score == 90.0
        assert plant.streak_days == 5
        assert plant.plant_icon == "🌿"
        assert plant.created_at is not None
    
    def test_plant_default_values(self, db_session: Session):
        """Test plant model default values."""
        # Create user first
        user = models.User(
            cognito_user_id="test-user-123",
            email="test@example.com",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create plant with minimal data
        plant = models.Plant(
            user_id=user.id,
            name="Test Plant",
            species="Test Species"
        )
        db_session.add(plant)
        db_session.commit()
        db_session.refresh(plant)
        
        assert plant.current_health_score == 100.0  # Default value
        assert plant.streak_days == 0  # Default value
        assert plant.plant_icon == "🌱"  # Default value


@pytest.mark.unit
class TestPlantScanModel:
    """Test cases for PlantScan model."""
    
    def test_create_plant_scan(self, db_session: Session):
        """Test creating a new plant scan."""
        # Create user
        user = models.User(
            cognito_user_id="test-user-123",
            email="test@example.com",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create plant
        plant = models.Plant(
            user_id=user.id,
            name="Test Plant",
            species="Test Species"
        )
        db_session.add(plant)
        db_session.commit()
        db_session.refresh(plant)
        
        # Create scan
        scan_data = {
            "plant_id": plant.id,
            "user_id": user.id,
            "health_score": 85.0,
            "care_notes": "Plant looks healthy",
            "disease_detected": None,
            "is_healthy": True
        }
        
        scan = models.PlantScan(**scan_data)
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.id is not None
        assert scan.plant_id == plant.id
        assert scan.user_id == user.id
        assert scan.health_score == 85.0
        assert scan.care_notes == "Plant looks healthy"
        assert scan.disease_detected is None
        assert scan.is_healthy is True
        assert scan.scan_date is not None
    
    def test_scan_without_plant(self, db_session: Session):
        """Test creating a scan without associated plant (species identification)."""
        # Create user
        user = models.User(
            cognito_user_id="test-user-123",
            email="test@example.com",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create scan without plant (for species identification)
        scan = models.PlantScan(
            plant_id=None,  # No plant associated
            user_id=user.id,
            health_score=75.0,
            is_healthy=True
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.plant_id is None
        assert scan.user_id == user.id
        assert scan.health_score == 75.0


@pytest.mark.unit
class TestAchievementModel:
    """Test cases for Achievement and UserAchievement models."""
    
    def test_create_achievement(self, db_session: Session):
        """Test creating a new achievement."""
        achievement_data = {
            "name": "Plant Parent",
            "description": "Add your first plant to the garden",
            "icon": "🌱",
            "achievement_type": "plants_count",
            "requirement_value": 1,
            "points_awarded": 10
        }
        
        achievement = models.Achievement(**achievement_data)
        db_session.add(achievement)
        db_session.commit()
        db_session.refresh(achievement)
        
        assert achievement.id is not None
        assert achievement.name == "Plant Parent"
        assert achievement.description == "Add your first plant to the garden"
        assert achievement.icon == "🌱"
        assert achievement.achievement_type == "plants_count"
        assert achievement.requirement_value == 1
        assert achievement.points_awarded == 10
        assert achievement.is_active is True  # Default value
    
    def test_user_achievement_relationship(self, db_session: Session):
        """Test user achievement relationship."""
        # Create user
        user = models.User(
            cognito_user_id="test-user-123",
            email="test@example.com",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create achievement
        achievement = models.Achievement(
            name="Test Achievement",
            description="Test description",
            achievement_type="test",
            requirement_value=1
        )
        db_session.add(achievement)
        db_session.commit()
        db_session.refresh(achievement)
        
        # Create user achievement
        user_achievement = models.UserAchievement(
            user_id=user.id,
            achievement_id=achievement.id,
            current_progress=1,
            is_completed=True
        )
        db_session.add(user_achievement)
        db_session.commit()
        db_session.refresh(user_achievement)
        
        assert user_achievement.user_id == user.id
        assert user_achievement.achievement_id == achievement.id
        assert user_achievement.current_progress == 1
        assert user_achievement.is_completed is True
        assert user_achievement.user == user
        assert user_achievement.achievement == achievement