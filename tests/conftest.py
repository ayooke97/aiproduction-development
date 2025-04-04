import os
import sys
import json
from typing import Dict, Any, List, Generator, Optional
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.config import get_settings, Settings
from app.domain.models import Document, SearchResult, UserPreferences
from app.core.exceptions import DocumentNotFoundError, ScraperError
from app.infrastructure.ai.openai_client import OpenAIClient
from app.infrastructure.ai.indobert import IndoBERTClient
from app.infrastructure.scrapers.bpk_scraper import BPKScraper
from app.services.document_service import DocumentService
from app.services.query_service import QueryService
from app.utils.pdf import PDFExtractor


@pytest.fixture
def test_app() -> FastAPI:
    """Fixture for FastAPI application."""
    return app


@pytest.fixture
def client() -> TestClient:
    """Fixture for FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def test_settings() -> Settings:
    """Fixture for test settings."""
    return Settings(
        API_V1_STR="/api/v1",
        PROJECT_NAME="Test BPK Legal Document API",
        DEBUG=True,
        OPENAI_API_KEY="test_api_key",
        OPENAI_BASE_URL="https://test-openai-url.com",
        OPENAI_MODEL="test-model",
        MAX_PAGES_DEFAULT=3,
        MAX_RESULTS_DEFAULT=5,
        REQUEST_TIMEOUT=10,
        ENABLE_BPK_SCRAPER=True,
        ENABLE_PERATURAN_SCRAPER=True,
        ENABLE_OPENAI=True,
        ENABLE_INDOBERT=True,
        CACHE_RESULTS=True,
        CACHE_TTL=3600
    )


@pytest.fixture
def mock_settings(test_settings: Settings) -> Generator:
    """Mock settings fixture."""
    with patch("app.config.get_settings", return_value=test_settings):
        yield test_settings


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Fixture for mock OpenAI client."""
    mock_client = MagicMock(spec=OpenAIClient)
    mock_client.is_available = True
    
    # Mock invoke method
    mock_client.invoke.return_value = "This is a test response from OpenAI."
    
    # Mock extract_keywords method
    mock_client.extract_keywords.return_value = ["keyword1", "keyword2", "keyword3"]
    
    # Mock generate_legal_response method
    mock_client.generate_legal_response.return_value = "This is a legal response from OpenAI."
    
    return mock_client


@pytest.fixture
def mock_indobert_client() -> MagicMock:
    """Fixture for mock IndoBERT client."""
    mock_client = MagicMock(spec=IndoBERTClient)
    mock_client.is_available = True
    
    # Mock get_embeddings method
    mock_client.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
    
    # Mock calculate_similarity method
    mock_client.calculate_similarity.return_value = 0.75
    
    # Mock rank_documents method
    mock_client.rank_documents.return_value = [
        {
            "content": "Test content 1",
            "metadata": {"title": "Test Document 1", "relevance_score": 0.9}
        },
        {
            "content": "Test content 2",
            "metadata": {"title": "Test Document 2", "relevance_score": 0.7}
        }
    ]
    
    return mock_client


@pytest.fixture
def mock_pdf_extractor() -> MagicMock:
    """Fixture for mock PDF extractor."""
    mock_extractor = MagicMock(spec=PDFExtractor)
    mock_extractor.is_available = True
    
    # Mock download_and_extract method
    mock_extractor.download_and_extract.return_value = (
        "Test PDF content.",
        {
            "title": "Test PDF",
            "source": "https://example.com/test.pdf",
            "pages": 5,
            "type": "pdf"
        }
    )
    
    # Mock extract_from_binary method
    mock_extractor.extract_from_binary.return_value = (
        "Test binary PDF content.",
        {
            "title": "Test Binary PDF",
            "source": "uploaded_file",
            "pages": 3,
            "type": "pdf"
        }
    )
    
    return mock_extractor


@pytest.fixture
def mock_bpk_scraper(mock_openai_client: MagicMock, mock_indobert_client: MagicMock) -> MagicMock:
    """Fixture for mock BPK scraper."""
    mock_scraper = MagicMock(spec=BPKScraper)
    
    # Mock search method
    mock_docs = [
        Document(
            content="Test content 1",
            metadata={
                "title": "Test Document 1",
                "source": "https://example.com/doc1",
                "type": "Legal Document",
                "date": "2023-01-01"
            }
        ),
        Document(
            content="Test content 2",
            metadata={
                "title": "Test Document 2",
                "source": "https://example.com/doc2",
                "type": "Legal Document",
                "date": "2023-01-02"
            }
        )
    ]
    mock_scraper.search.return_value = mock_docs
    
    # Mock preprocess_query method
    mock_scraper.preprocess_query.return_value = "enhanced test query"
    
    # Mock generate_html_report method
    mock_scraper.generate_html_report.return_value = "test_report.html"
    
    # Set mock clients
    mock_scraper.openai_client = mock_openai_client
    mock_scraper.indobert_client = mock_indobert_client
    
    return mock_scraper


@pytest.fixture
def mock_document_service(mock_bpk_scraper: MagicMock, mock_pdf_extractor: MagicMock) -> MagicMock:
    """Fixture for mock document service."""
    mock_service = MagicMock(spec=DocumentService)
    
    # Set mock PDF extractor
    mock_service.pdf_extractor = mock_pdf_extractor
    
    # Mock search_documents method
    mock_docs = [
        Document(
            content="Test content 1",
            metadata={
                "id": "doc_123",
                "title": "Test Document 1",
                "source": "https://example.com/doc1",
                "type": "Legal Document",
                "date": "2023-01-01"
            }
        ),
        Document(
            content="Test content 2",
            metadata={
                "id": "doc_456",
                "title": "Test Document 2",
                "source": "https://example.com/doc2",
                "type": "Legal Document",
                "date": "2023-01-02"
            }
        )
    ]
    mock_service.search_documents.return_value = mock_docs
    
    # Mock get_document_by_id method
    def get_doc_by_id(doc_id: str) -> Document:
        if doc_id == "doc_123":
            return mock_docs[0]
        elif doc_id == "doc_456":
            return mock_docs[1]
        else:
            raise DocumentNotFoundError(doc_id)
    
    mock_service.get_document_by_id.side_effect = get_doc_by_id
    
    # Mock extract_pdf_content method
    mock_service.extract_pdf_content.return_value = Document(
        content="Test PDF content",
        metadata={
            "id": "pdf_789",
            "title": "Test PDF",
            "source": "https://example.com/test.pdf",
            "type": "pdf",
            "pages": 5
        }
    )
    
    # Mock generate_report method
    mock_service.generate_report.return_value = "test_report.html"
    
    # Set up documents dictionary
    mock_service.documents = {
        "doc_123": mock_docs[0],
        "doc_456": mock_docs[1],
        "pdf_789": Document(
            content="Test PDF content",
            metadata={
                "id": "pdf_789",
                "title": "Test PDF",
                "source": "https://example.com/test.pdf",
                "type": "pdf",
                "pages": 5
            }
        )
    }
    
    return mock_service


@pytest.fixture
def mock_query_service(mock_document_service: MagicMock, mock_openai_client: MagicMock) -> MagicMock:
    """Fixture for mock query service."""
    mock_service = MagicMock(spec=QueryService)
    
    # Set mock dependencies
    mock_service.document_service = mock_document_service
    mock_service.openai_client = mock_openai_client
    
    # Mock process_query method
    mock_service.process_query.return_value = SearchResult(
        original_query="test query",
        keywords=["test", "query", "legal"],
        documents=[
            {
                "content": "Test content 1",
                "metadata": {
                    "id": "doc_123",
                    "title": "Test Document 1",
                    "source": "https://example.com/doc1"
                }
            },
            {
                "content": "Test content 2",
                "metadata": {
                    "id": "doc_456",
                    "title": "Test Document 2",
                    "source": "https://example.com/doc2"
                }
            }
        ],
        response="This is a test response based on the documents."
    )
    
    # Mock generate_report method
    mock_service.generate_report.return_value = "test_report.html"
    
    return mock_service


@pytest.fixture
def sample_document() -> Document:
    """Fixture for a sample document."""
    return Document(
        content="This is test content for a legal document.",
        metadata={
            "id": "test_doc_1",
            "title": "Test Legal Document",
            "source": "https://example.com/test_doc",
            "type": "Legal Document",
            "date": "2023-01-01"
        }
    )


@pytest.fixture
def sample_search_result() -> SearchResult:
    """Fixture for a sample search result."""
    return SearchResult(
        original_query="test legal query",
        keywords=["test", "legal", "document"],
        documents=[
            {
                "content": "This is test content for a legal document.",
                "metadata": {
                    "id": "test_doc_1",
                    "title": "Test Legal Document",
                    "source": "https://example.com/test_doc",
                    "type": "Legal Document",
                    "date": "2023-01-01"
                }
            }
        ],
        response="This is a test response based on the legal document."
    )


@pytest.fixture
def sample_user_preferences() -> UserPreferences:
    """Fixture for sample user preferences."""
    return UserPreferences(
        verbosity="detailed",
        format="simple",
        citations=True,
        max_results=5
    )


@pytest.fixture
def sample_html_content() -> str:
    """Fixture for sample HTML content from a web page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Legal Document</title>
    </head>
    <body>
        <div class="card">
            <h3 class="fw-bold text-gray-800 mb-5">
                <a href="/Home/Detail/12345">Test Legal Document 1</a>
            </h3>
            <div class="text-gray-600">
                <span>Regulation</span>
                <span>2023-01-01</span>
            </div>
            <div class="card-text">
                This is a test legal document content preview.
            </div>
        </div>
        <div class="card">
            <h3 class="fw-bold text-gray-800 mb-5">
                <a href="/Home/Detail/67890">Test Legal Document 2</a>
            </h3>
            <div class="text-gray-600">
                <span>Law</span>
                <span>2023-01-02</span>
            </div>
            <div class="card-text">
                This is another test legal document content preview.
            </div>
        </div>
    </body>
    </html>
    """