import pytest
import requests
import os
import time
from unittest.mock import patch

from fastapi.testclient import TestClient


@pytest.mark.e2e
class TestFullAPIFlow:
    """End-to-end tests for the full API flow with mocked backend services."""
    
    @patch("app.api.dependencies.get_query_service")
    @patch("app.api.dependencies.get_document_service")
    def test_search_and_get_document_flow(
        self,
        mock_get_document_service,
        mock_get_query_service,
        client,
        mock_query_service,
        mock_document_service
    ):
        """
        Test the full search and document retrieval flow.
        
        1. Search for documents
        2. Get a specific document from the search results
        3. Generate a report
        """
        # Setup mocks
        mock_get_query_service.return_value = mock_query_service
        mock_get_document_service.return_value = mock_document_service
        
        # Step 1: Search for documents
        search_payload = {
            "query": "test legal document",
            "preferences": {
                "verbosity": "detailed",
                "format": "simple",
                "citations": True,
                "max_results": 5
            }
        }
        
        search_response = client.post("/api/v1/search/query", json=search_payload)
        assert search_response.status_code == 200
        search_result = search_response.json()
        
        # Verify search result
        assert search_result["original_query"] == "test legal document"
        assert len(search_result["documents"]) > 0
        assert "response" in search_result
        
        # Get document ID from search results
        document_id = search_result["documents"][0]["metadata"]["id"]
        
        # Step 2: Get specific document
        document_response = client.get(f"/api/v1/documents/{document_id}")
        assert document_response.status_code == 200
        document = document_response.json()
        
        # Verify document
        assert "content" in document
        assert "metadata" in document
        assert document["metadata"]["id"] == document_id
        
        # Step 3: Generate a report
        # Use patching to avoid actual file creation
        with patch("fastapi.responses.FileResponse") as mock_file_response:
            mock_file_response.return_value.status_code = 200
            report_response = client.post("/api/v1/search/report", json=search_payload)
        
        assert report_response.status_code == 200
    
    @patch("app.infrastructure.scrapers.bpk_scraper.BPKScraper.search")
    @patch("app.api.dependencies.get_openai_client")
    @patch("app.api.dependencies.get_indobert_client")
    def test_search_with_mock_scraper(
        self,
        mock_get_indobert,
        mock_get_openai,
        mock_search,
        client,
        mock_openai_client,
        mock_indobert_client,
        sample_document
    ):
        """Test search with a mocked scraper."""
        # Setup mocks
        mock_get_openai.return_value = mock_openai_client
        mock_get_indobert.return_value = mock_indobert_client
        mock_search.return_value = [sample_document]
        
        # Make request
        response = client.get(
            "/api/v1/search/simple",
            params={"query": "test query", "max_results": 1}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["original_query"] == "test query"
        assert len(data["documents"]) == 1
        
        # Verify mock was called
        mock_search.assert_called_once()


@pytest.mark.e2e
class TestErrorFlows:
    """End-to-end tests for error scenarios."""
    
    def test_invalid_query_flow(self, client):
        """Test flow with an invalid (empty) query."""
        # Make request with empty query
        payload = {
            "query": "",  # Empty query
            "preferences": {
                "verbosity": "detailed",
                "format": "simple",
                "citations": True,
                "max_results": 5
            }
        }
        
        response = client.post("/api/v1/search/query", json=payload)
        
        # Verify error response
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "timestamp" in data
        assert "status_code" in data
    
    def test_non_existent_document_flow(self, client):
        """Test flow with a non-existent document ID."""
        # Try to get a non-existent document
        response = client.get("/api/v1/documents/non_existent_id")
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "timestamp" in data
        assert "status_code" in data
    
    def test_invalid_pdf_url_flow(self, client):
        """Test flow with an invalid PDF URL."""
        # Try to extract content from an invalid PDF URL
        payload = {
            "pdf_url": "not-a-valid-url",
            "title": "Invalid PDF"
        }
        
        response = client.post("/api/v1/documents/extract-pdf", json=payload)
        
        # Response should indicate error
        assert response.status_code in [400, 422, 500]
        data = response.json()
        assert "detail" in data