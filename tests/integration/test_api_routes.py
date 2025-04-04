import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.api.dependencies import get_query_service, get_document_service
from app.core.exceptions import InvalidQueryError, DocumentNotFoundError


@pytest.mark.integration
class TestSearchRoutes:
    """Tests for the search routes."""
    
    @patch("app.api.routes.search.get_query_service")
    def test_search_query_endpoint(self, mock_get_query_service, client, mock_query_service):
        """Test the search query endpoint."""
        # Setup mock
        mock_get_query_service.return_value = mock_query_service
        
        # Define request payload
        payload = {
            "query": "test query",
            "preferences": {
                "verbosity": "detailed",
                "format": "simple",
                "citations": True,
                "max_results": 5
            }
        }
        
        # Make request
        response = client.post("/api/v1/search/query", json=payload)
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["original_query"] == "test query"
        assert len(data["keywords"]) > 0
        assert len(data["documents"]) > 0
        assert "response" in data
        
        # Verify service called
        mock_query_service.process_query.assert_called_once()
    
    @patch("app.api.routes.search.get_query_service")
    def test_search_query_invalid_query(self, mock_get_query_service, client, mock_query_service):
        """Test the search query endpoint with an invalid query."""
        # Setup mock to raise exception
        mock_get_query_service.return_value = mock_query_service
        mock_query_service.process_query.side_effect = InvalidQueryError("Invalid query")
        
        # Define request payload with empty query
        payload = {
            "query": "",
            "preferences": {
                "verbosity": "detailed",
                "format": "simple",
                "citations": True,
                "max_results": 5
            }
        }
        
        # Make request
        response = client.post("/api/v1/search/query", json=payload)
        
        # Assert response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid query" in data["detail"]
    
    @patch("app.api.routes.search.get_query_service")
    def test_simple_search_endpoint(self, mock_get_query_service, client, mock_query_service):
        """Test the simple search endpoint."""
        # Setup mock
        mock_get_query_service.return_value = mock_query_service
        
        # Make request
        response = client.get("/api/v1/search/simple?query=test%20query&max_results=5")
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["original_query"] == "test query"
        assert len(data["keywords"]) > 0
        assert len(data["documents"]) > 0
        assert "response" in data
        
        # Verify service called
        mock_query_service.process_query.assert_called_once()
    
    @patch("app.api.routes.search.get_query_service")
    def test_generate_report_endpoint(self, mock_get_query_service, client, mock_query_service):
        """Test the generate report endpoint."""
        # Setup mock
        mock_get_query_service.return_value = mock_query_service
        mock_query_service.generate_report.return_value = "test_report.html"
        
        # Define request payload
        payload = {
            "query": "test query",
            "preferences": {
                "verbosity": "detailed",
                "format": "simple",
                "citations": True,
                "max_results": 5
            }
        }
        
        # Make request
        with patch("fastapi.responses.FileResponse") as mock_file_response:
            mock_file_response.return_value.status_code = 200
            response = client.post("/api/v1/search/report", json=payload)
        
        # Assert response
        assert response.status_code == 200


@pytest.mark.integration
class TestDocumentRoutes:
    """Tests for the document routes."""
    
    @patch("app.api.routes.documents.get_document_service")
    def test_get_document_endpoint(self, mock_get_document_service, client, mock_document_service):
        """Test the get document endpoint."""
        # Setup mock
        mock_get_document_service.return_value = mock_document_service
        
        # Make request
        response = client.get("/api/v1/documents/doc_123")
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "metadata" in data
        assert data["metadata"]["id"] == "doc_123"
        
        # Verify service called
        mock_document_service.get_document_by_id.assert_called_once_with("doc_123")
    
    @patch("app.api.routes.documents.get_document_service")
    def test_get_document_not_found(self, mock_get_document_service, client, mock_document_service):
        """Test the get document endpoint with a non-existent document ID."""
        # Setup mock to raise exception
        mock_get_document_service.return_value = mock_document_service
        mock_document_service.get_document_by_id.side_effect = DocumentNotFoundError("doc_999")
        
        # Make request
        response = client.get("/api/v1/documents/doc_999")
        
        # Assert response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    @patch("app.api.routes.documents.get_document_service")
    def test_extract_pdf_content_endpoint(self, mock_get_document_service, client, mock_document_service):
        """Test the extract PDF content endpoint."""
        # Setup mock
        mock_get_document_service.return_value = mock_document_service
        
        # Define request payload
        payload = {
            "pdf_url": "https://example.com/test.pdf",
            "title": "Test PDF"
        }
        
        # Make request
        response = client.post("/api/v1/documents/extract-pdf", json=payload)
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "metadata" in data
        assert data["metadata"]["title"] == "Test PDF"
        
        # Verify service called
        mock_document_service.extract_pdf_content.assert_called_once()
    
    @patch("app.api.routes.documents.get_document_service")
    def test_extract_pdf_content_failure(self, mock_get_document_service, client, mock_document_service):
        """Test the extract PDF content endpoint when extraction fails."""
        # Setup mock to return None
        mock_get_document_service.return_value = mock_document_service
        mock_document_service.extract_pdf_content.return_value = None
        
        # Define request payload
        payload = {
            "pdf_url": "https://example.com/invalid.pdf",
            "title": "Invalid PDF"
        }
        
        # Make request
        response = client.post("/api/v1/documents/extract-pdf", json=payload)
        
        # Assert response
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "Failed to extract content" in data["detail"]