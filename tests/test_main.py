import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.e2e
class TestMainApplication:
    """Tests for the main FastAPI application."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "docs_url" in data
        assert "redoc_url" in data
        assert "api_prefix" in data
    
    def test_health_check_endpoint(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_openapi_schema(self, client: TestClient):
        """Test the OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema
    
    def test_docs_endpoint(self, client: TestClient):
        """Test the Swagger UI docs endpoint."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_endpoint(self, client: TestClient):
        """Test the ReDoc docs endpoint."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_process_time_header(self, client: TestClient):
        """Test that X-Process-Time header is added to responses."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time > 0
    
    def test_not_found_handling(self, client: TestClient):
        """Test handling of non-existent routes."""
        response = client.get("/non-existent-route")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Not Found"


@pytest.mark.e2e
class TestErrorHandling:
    """Tests for API error handling."""
    
    def test_validation_error_handling(self, client: TestClient):
        """Test handling of validation errors."""
        # Send an invalid request (missing required field)
        response = client.post("/api/v1/search/query", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "timestamp" in data
    
    def test_method_not_allowed_handling(self, client: TestClient):
        """Test handling of method not allowed errors."""
        # Try to use POST on a GET endpoint
        response = client.post("/health")
        
        assert response.status_code == 405
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Method Not Allowed"