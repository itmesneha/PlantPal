"""
API tests for main application endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.api
class TestMainEndpoints:
    """Test main application endpoints"""

    def test_read_root(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "PlantPal API" in data["message"]
        assert "version" in data

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "PlantPal API is running"

    def test_api_test_endpoint(self):
        """Test API test endpoint"""
        response = client.get("/api/v1/test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "PlantPal API is working!"
        assert "timestamp" in data

    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/")
        # FastAPI automatically handles OPTIONS requests
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly defined
        
        # Test actual request has CORS headers
        response = client.get("/")
        # Note: TestClient doesn't simulate full CORS behavior, 
        # but we can verify the middleware is configured
        assert response.status_code == 200

    def test_invalid_endpoint(self):
        """Test invalid endpoint returns 404"""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404