"""
API tests for plant scanning endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from io import BytesIO
from PIL import Image
import json
from app.main import app
from app import models
from app.auth import get_current_user_info

client = TestClient(app)


@pytest.mark.api
class TestScanEndpoints:
    """Test plant scanning API endpoints"""

    def test_scan_test_endpoint(self):
        """Test scan test endpoint"""
        response = client.get("/api/v1/scan-test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Scan route is working!"
        assert data["status"] == "ok"

    def test_scan_simple_success(self, client, db_session):
        """Test simple scan endpoint"""
        # Mock authentication using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": "test-user-123",
                "email": "test@example.com",
                "name": "Test User"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            # Create a test image
            image = Image.new('RGB', (100, 100), color='green')
            img_bytes = BytesIO()
            image.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            response = client.post(
                "/api/v1/scan-simple",
                files={"image": ("test.jpg", img_bytes, "image/jpeg")}
            )
            assert response.status_code == 200
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
        
        data = response.json()
        assert data["species"] == "Test Plant"
        assert data["confidence"] == 0.95
        assert data["is_healthy"] == True
        assert data["health_score"] == 100.0
        assert "care_recommendations" in data

    def test_scan_simple_unauthorized(self):
        """Test scan simple without authentication"""
        image = Image.new('RGB', (100, 100), color='green')
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        response = client.post(
            "/api/v1/scan-simple",
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )
        assert response.status_code == 403

    def test_scan_simple_no_image(self):
        """Test scan simple without image"""
        # Mock authentication using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": "test-user-123",
                "email": "test@example.com",
                "name": "Test User"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.post("/api/v1/scan-simple")
            assert response.status_code == 422
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    @patch('app.routers.scan.query_plantnet_api_async')
    @patch('app.routers.scan.query_huggingface_model_async')
    def test_scan_full_success(self, mock_hf, mock_plantnet, client, db_session):
        """Test full scan endpoint with mocked external APIs"""
        # Create test user and plant
        test_user = models.User(
            cognito_user_id="test-user-123",
            email="test@example.com",
            name="Test User"
        )
        db_session.add(test_user)
        db_session.commit()
        
        test_plant = models.Plant(
            user_id=test_user.id,
            species="Rosa rubiginosa",
            name="Test Rose",
            current_health_score=100.0
        )
        db_session.add(test_plant)
        db_session.commit()
        
        # Mock authentication using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": test_user.cognito_user_id,
                "email": test_user.email,
                "name": test_user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            # Mock PlantNet API response
            mock_plantnet.return_value = {
                "results": [
                    {
                        "species": {"scientificNameWithoutAuthor": "Rosa rubiginosa"},
                        "score": 0.85
                    }
                ]
            }
            
            # Mock Hugging Face API response
            mock_hf.return_value = [
                {"label": "healthy", "score": 0.9},
                {"label": "leaf_spot", "score": 0.1}
            ]
            
            # Create a test image
            image = Image.new('RGB', (100, 100), color='green')
            img_bytes = BytesIO()
            image.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            response = client.post(
                "/api/v1/scan",
                files={"image": ("test.jpg", img_bytes, "image/jpeg")},
                data={"plant_id": str(test_plant.id)}
            )
            assert response.status_code == 200
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
        
        data = response.json()
        assert "species" in data
        assert "confidence" in data
        assert "is_healthy" in data
        assert "health_score" in data

    @patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'})
    @patch('aiohttp.ClientSession.post')
    def test_care_recommendations_success(self, mock_post, client, db_session):
        """Test care recommendations endpoint"""
        # Mock authentication using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": "test-user-123",
                "email": "test@example.com",
                "name": "Test User"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            # Mock OpenRouter API response
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Water regularly. Provide bright light. Fertilize monthly. Prune dead leaves."
                        }
                    }
                ]
            }
            mock_response.raise_for_status = AsyncMock()
            mock_post.return_value.__aenter__.return_value = mock_response
            
            request_data = {
                "species": "Rosa rubiginosa",
                "disease": None
            }
            
            response = client.post("/api/v1/care-recommendations", json=request_data)
            assert response.status_code == 200
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
        
        data = response.json()
        assert "care_recommendations" in data
        assert isinstance(data["care_recommendations"], list)

    def test_care_recommendations_no_api_key(self, client, db_session):
        """Test care recommendations without API key"""
        # Mock authentication using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": "test-user-123",
                "email": "test@example.com",
                "name": "Test User"
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            request_data = {
                "species": "Rosa rubiginosa"
            }
            
            with patch.dict('os.environ', {}, clear=True):
                response = client.post("/api/v1/care-recommendations", json=request_data)
                assert response.status_code == 503
                assert "OpenRouter API key not configured" in response.json()["detail"]
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_care_recommendations_unauthorized(self):
        """Test care recommendations without authentication"""
        request_data = {
            "species": "Rosa rubiginosa"
        }
        
        response = client.post("/api/v1/care-recommendations", json=request_data)
        assert response.status_code == 403

    def test_get_latest_plant_health_success(self, client, db_session):
        """Test get latest plant health endpoint"""
        # Create test user
        test_user = models.User(
            cognito_user_id="test-user-health-success",
            email="health-success@example.com",
            name="Health Success User"
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
        
        # Create test plant
        test_plant = models.Plant(
            user_id=test_user.id,
            name="Test Plant",
            species="Test Species",
            current_health_score=75.0,
            streak_days=3
        )
        db_session.add(test_plant)
        db_session.commit()
        db_session.refresh(test_plant)
        
        # Create test plant scan
        from datetime import datetime
        test_plant_scan = models.PlantScan(
            plant_id=test_plant.id,
            user_id=test_user.id,
            health_score=85.0,
            scan_date=datetime.utcnow(),
            care_notes="Test care notes",
            disease_detected=None,
            is_healthy=True
        )
        db_session.add(test_plant_scan)
        db_session.commit()
        
        # Mock authentication using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": test_user.cognito_user_id,
                "email": test_user.email,
                "name": test_user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get(f"/api/v1/latest-health/{test_plant.id}")
            assert response.status_code == 200
            
            data = response.json()
            assert "health_score" in data
            assert "is_healthy" in data
            assert "last_scan_date" in data
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_latest_plant_health_not_found(self, client, db_session):
        """Test get latest plant health for non-existent plant"""
        # Create test user
        test_user = models.User(
            cognito_user_id="test-user-not-found",
            email="test@example.com",
            name="Test User"
        )
        db_session.add(test_user)
        db_session.commit()
        
        # Mock authentication using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": test_user.cognito_user_id,
                "email": test_user.email,
                "name": test_user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get("/api/v1/latest-health/999999")
            assert response.status_code == 404
            assert "Plant not found" in response.json()["detail"]
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_latest_plant_scan_success(self, client, db_session):
        """Test get latest plant scan endpoint"""
        # Create test user
        test_user = models.User(
            cognito_user_id="test-user-scan-success",
            email="scan-success@example.com",
            name="Scan Success User"
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
        
        # Create test plant
        test_plant = models.Plant(
            user_id=test_user.id,
            name="Test Plant",
            species="Test Species",
            current_health_score=75.0,
            streak_days=3
        )
        db_session.add(test_plant)
        db_session.commit()
        db_session.refresh(test_plant)
        
        # Create test plant scan
        from datetime import datetime
        test_plant_scan = models.PlantScan(
            plant_id=test_plant.id,
            user_id=test_user.id,
            health_score=85.0,
            scan_date=datetime.utcnow(),
            care_notes="Test care notes",
            disease_detected=None,
            is_healthy=True
        )
        db_session.add(test_plant_scan)
        db_session.commit()
        
        # Mock authentication using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": test_user.cognito_user_id,
                "email": test_user.email,
                "name": test_user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get(f"/api/v1/latest/{test_plant.id}")
            assert response.status_code == 200
            
            data = response.json()
            assert "id" in data
            assert "health_score" in data
            assert "scan_date" in data
            assert data["plant_id"] == test_plant.id
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_plant_scan_history_success(self, client, db_session):
        """Test get plant scan history endpoint"""
        # Create test user
        test_user = models.User(
            cognito_user_id="test-user-history-success",
            email="history-success@example.com",
            name="History Success User"
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
        
        # Create test plant
        test_plant = models.Plant(
            user_id=test_user.id,
            name="Test Plant",
            species="Test Species",
            current_health_score=75.0,
            streak_days=3
        )
        db_session.add(test_plant)
        db_session.commit()
        db_session.refresh(test_plant)
        
        # Create test plant scan
        from datetime import datetime
        test_plant_scan = models.PlantScan(
            plant_id=test_plant.id,
            user_id=test_user.id,
            health_score=85.0,
            scan_date=datetime.utcnow(),
            care_notes="Test care notes",
            disease_detected=None,
            is_healthy=True
        )
        db_session.add(test_plant_scan)
        db_session.commit()
        
        # Mock authentication using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": test_user.cognito_user_id,
                "email": test_user.email,
                "name": test_user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get(f"/api/v1/history/{test_plant.id}")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            if len(data) > 0:
                assert "id" in data[0]
                assert "plant_id" in data[0]
                assert "health_score" in data[0]
                assert "scan_date" in data[0]
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_plant_scan_history_unauthorized_plant(self, client, db_session):
        """Test get scan history for plant not owned by user"""
        # Create test user
        test_user = models.User(
            cognito_user_id="test-user-unauthorized",
            email="test@example.com",
            name="Test User"
        )
        db_session.add(test_user)
        db_session.commit()
        
        # Create another user and their plant
        other_user = models.User(
            cognito_user_id="other-user-123",
            email="other@test.com",
            name="Other User"
        )
        db_session.add(other_user)
        db_session.commit()
        
        other_plant = models.Plant(
            user_id=other_user.id,
            name="Other Plant",
            species="Other Species",
            current_health_score=100.0
        )
        db_session.add(other_plant)
        db_session.commit()
        
        # Mock authentication as first user using dependency override
        def mock_get_current_user_info():
            return {
                "cognito_user_id": test_user.cognito_user_id,
                "email": test_user.email,
                "name": test_user.name
            }
        
        app.dependency_overrides[get_current_user_info] = mock_get_current_user_info
        
        try:
            response = client.get(f"/api/v1/history/{other_plant.id}")
            assert response.status_code == 404
            assert "Plant not found" in response.json()["detail"]
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_scan_endpoints_require_authentication(self):
        """Test that all scan endpoints require authentication"""
        endpoints = [
            ("/api/v1/scan-simple", "post"),
            ("/api/v1/scan", "post"),
            ("/api/v1/care-recommendations", "post"),
            ("/api/v1/latest-health/123", "get"),
            ("/api/v1/latest/123", "get"),
            ("/api/v1/history/123", "get")
        ]
        
        for endpoint, method in endpoints:
            if method == "post":
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)
            
            assert response.status_code == 403, f"Endpoint {endpoint} should require authentication"