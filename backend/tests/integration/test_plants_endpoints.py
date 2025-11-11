"""
Integration tests for plants endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app import models, schemas


@pytest.mark.integration
class TestPlantsEndpoints:
    """Test plants management endpoints."""

    def test_get_user_plants_empty_garden(self, authenticated_client, db_session: Session):
        """Test getting plants when user has no plants."""
        client, user = authenticated_client
        response = client.get("/api/v1/plants/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_user_plants_with_plants(self, authenticated_client, db_session: Session, mock_user_info):
        """Test getting plants when user has plants in garden."""
        client, user = authenticated_client

        # Create test plants
        plant1 = models.Plant(
            user_id=user.id,
            name="Rose",
            species="Rosa rubiginosa",
            current_health_score=85.0,
            plant_icon="🌹",
            streak_days=5
        )
        plant2 = models.Plant(
            user_id=user.id,
            name="Sunflower",
            species="Helianthus annuus",
            current_health_score=92.0,
            plant_icon="🌻",
            streak_days=3
        )
        db_session.add_all([plant1, plant2])
        db_session.commit()

        response = client.get("/api/v1/plants/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Check plant data
        plant_names = [plant["name"] for plant in data]
        assert "Rose" in plant_names
        assert "Sunflower" in plant_names

    def test_get_user_plants_pagination(self, authenticated_client, db_session: Session, mock_user_info):
        """Test plants pagination."""
        client, user = authenticated_client

        # Create multiple plants
        plants = []
        for i in range(5):
            plant = models.Plant(
                user_id=user.id,
                name=f"Plant {i+1}",
                species=f"Species {i+1}",
                current_health_score=80.0 + i,
                plant_icon="🌱",
                streak_days=i+1
            )
            plants.append(plant)
        db_session.add_all(plants)
        db_session.commit()

        # Test pagination
        response = client.get("/api/v1/plants/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_add_to_garden_success(self, authenticated_client, db_session: Session, mock_user_info):
        """Test successfully adding a plant to garden."""
        client, user = authenticated_client

        plant_data = {
            "plant_name": "My Rose",
            "species": "Rosa rubiginosa",
            "health_score": 85.0,
            "plant_icon": "🌹",
            "care_notes": "Needs daily watering",
            "disease_detected": None,  # String or None, not boolean
            "is_healthy": True
        }

        with patch('app.routers.plants.update_achievement_progress') as mock_achievement:
            mock_achievement.return_value = []
            response = client.post("/api/v1/plants/add-to-garden", json=plant_data)

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plant_id" in data
        assert "My Rose" in data["message"]
        assert data["plant"]["name"] == "My Rose"
        assert data["plant"]["species"] == "Rosa rubiginosa"

        # Verify plant was created in database
        plant = db_session.query(models.Plant).filter(
            models.Plant.id == data["plant_id"]
        ).first()
        assert plant is not None
        assert plant.name == "My Rose"
        assert plant.user_id == user.id

    def test_add_to_garden_user_not_found(self, client: TestClient):
        """Test adding plant when user is not authenticated."""
        plant_data = {
            "plant_name": "My Rose",
            "species": "Rosa rubiginosa",
            "health_score": 85.0
        }

        response = client.post("/api/v1/plants/add-to-garden", json=plant_data)
        assert response.status_code == 403  # FastAPI returns 403 for missing auth

    def test_update_plant_success(self, authenticated_client, db_session: Session, mock_user_info):
        """Test successfully updating a plant."""
        client, user = authenticated_client

        plant = models.Plant(
            user_id=user.id,
            name="Old Name",
            species="Rosa rubiginosa",
            current_health_score=85.0,
            plant_icon="🌹",
            streak_days=5
        )
        db_session.add(plant)
        db_session.commit()

        update_data = {
            "name": "New Rose Name",
            "plant_icon": "🌺"
        }

        response = client.put(f"/api/v1/plants/{plant.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Rose Name"
        assert data["plant_icon"] == "🌺"
        assert data["species"] == "Rosa rubiginosa"  # Unchanged

        # Verify in database
        updated_plant = db_session.query(models.Plant).filter(
            models.Plant.id == plant.id
        ).first()
        assert updated_plant.name == "New Rose Name"
        assert updated_plant.plant_icon == "🌺"

    def test_update_plant_not_found(self, authenticated_client, db_session: Session, mock_user_info):
        """Test updating a non-existent plant."""
        client, user = authenticated_client

        update_data = {"name": "New Name"}
        response = client.put("/api/v1/plants/nonexistent-id", json=update_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_plant_wrong_owner(self, authenticated_client, db_session: Session, mock_user_info):
        """Test updating a plant owned by another user."""
        client, user = authenticated_client
        
        # Create another user
        user1 = models.User(
            cognito_user_id="other-user-id",
            email="other@plantpal.com",
            name="Other User"
        )
        db_session.add(user1)
        db_session.flush()

        # Create plant owned by user1
        plant = models.Plant(
            user_id=user1.id,
            name="Other's Plant",
            species="Rosa rubiginosa",
            current_health_score=85.0
        )
        db_session.add(plant)
        db_session.commit()

        # Try to update as user2
        update_data = {"name": "Hacked Name"}
        response = client.put(f"/api/v1/plants/{plant.id}", json=update_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_plant_success(self, authenticated_client, db_session: Session, mock_user_info):
        """Test successfully deleting a plant."""
        client, user = authenticated_client

        plant = models.Plant(
            user_id=user.id,
            name="To Delete",
            species="Rosa rubiginosa",
            current_health_score=85.0
        )
        db_session.add(plant)
        db_session.commit()
        plant_id = plant.id

        response = client.delete(f"/api/v1/plants/{plant_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "To Delete" in data["message"]
        assert data["deleted_plant_id"] == plant_id

        # Verify plant was deleted
        deleted_plant = db_session.query(models.Plant).filter(
            models.Plant.id == plant_id
        ).first()
        assert deleted_plant is None

    def test_delete_plant_with_scans(self, authenticated_client, db_session: Session, mock_user_info):
        """Test deleting a plant that has associated scans."""
        client, user = authenticated_client

        plant = models.Plant(
            user_id=user.id,
            name="Plant with Scans",
            species="Rosa rubiginosa",
            current_health_score=85.0
        )
        db_session.add(plant)
        db_session.flush()

        # Create associated scans
        scan1 = models.PlantScan(
            user_id=user.id,
            plant_id=plant.id,
            health_score=85.0,
            is_healthy=True,
            care_notes="Looking good"
        )
        scan2 = models.PlantScan(
            user_id=user.id,
            plant_id=plant.id,
            health_score=90.0,
            is_healthy=True,
            care_notes="Even better"
        )
        db_session.add_all([scan1, scan2])
        db_session.commit()
        plant_id = plant.id

        response = client.delete(f"/api/v1/plants/{plant_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify plant and scans were deleted
        deleted_plant = db_session.query(models.Plant).filter(
            models.Plant.id == plant_id
        ).first()
        assert deleted_plant is None

        remaining_scans = db_session.query(models.PlantScan).filter(
            models.PlantScan.plant_id == plant_id
        ).all()
        assert len(remaining_scans) == 0

    def test_delete_plant_not_found(self, authenticated_client, db_session: Session, mock_user_info):
        """Test deleting a non-existent plant."""
        client, user = authenticated_client

        response = client.delete("/api/v1/plants/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_plant_wrong_owner(self, authenticated_client, db_session: Session, mock_user_info):
        """Test deleting a plant owned by another user."""
        client, user = authenticated_client
        
        # Create another user
        user1 = models.User(
            cognito_user_id="other-user-id",
            email="other@plantpal.com",
            name="Other User"
        )
        db_session.add(user1)
        db_session.flush()

        # Create plant owned by user1
        plant = models.Plant(
            user_id=user1.id,
            name="Other's Plant",
            species="Rosa rubiginosa",
            current_health_score=85.0
        )
        db_session.add(plant)
        db_session.commit()

        # Try to delete as user2
        response = client.delete(f"/api/v1/plants/{plant.id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_plants_workflow_integration(self, authenticated_client, db_session: Session, mock_user_info):
        """Test complete plants workflow: add -> get -> update -> delete."""
        client, user = authenticated_client

        # 1. Add plant to garden
        plant_data = {
            "plant_name": "Workflow Rose",
            "species": "Rosa rubiginosa",
            "health_score": 85.0,
            "plant_icon": "🌹",
            "is_healthy": True
        }

        with patch('app.routers.plants.update_achievement_progress') as mock_achievement:
            mock_achievement.return_value = []
            add_response = client.post("/api/v1/plants/add-to-garden", json=plant_data)

        assert add_response.status_code == 200
        plant_id = add_response.json()["plant_id"]

        # 2. Get plants list
        get_response = client.get("/api/v1/plants/")
        assert get_response.status_code == 200
        plants = get_response.json()
        assert len(plants) == 1
        assert plants[0]["name"] == "Workflow Rose"

        # 3. Update plant
        update_data = {"name": "Updated Workflow Rose", "plant_icon": "🌺"}
        update_response = client.put(f"/api/v1/plants/{plant_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Workflow Rose"

        # 4. Delete plant
        delete_response = client.delete(f"/api/v1/plants/{plant_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] is True

        # 5. Verify plant is gone
        final_get_response = client.get("/api/v1/plants/")
        assert final_get_response.status_code == 200
        assert len(final_get_response.json()) == 0