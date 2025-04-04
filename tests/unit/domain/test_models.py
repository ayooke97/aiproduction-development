import pytest
from pydantic import ValidationError
from datetime import datetime

from app.domain.models import (
    Document,
    SearchQuery,
    UserPreferences,
    SearchRequest,
    SearchResult,
    ErrorResponse
)


class TestDocument:
    """Tests for the Document model."""

    def test_document_creation(self):
        """Test creating a Document instance."""
        # Create a document
        doc = Document(
            content="Test content",
            metadata={"title": "Test Document", "source": "https://example.com"}
        )
        
        # Check attributes
        assert doc.content == "Test content"
        assert doc.metadata["title"] == "Test Document"
        assert doc.metadata["source"] == "https://example.com"
        
        # Check page_content property
        assert doc.page_content == "Test content"
    
    def test_document_from_dict(self):
        """Test creating a Document from a dictionary."""
        # Create a document from dict with content
        data = {
            "content": "Test content",
            "metadata": {"title": "Test Document"}
        }
        doc = Document.from_dict(data)
        
        assert doc.content == "Test content"
        assert doc.metadata["title"] == "Test Document"
        
        # Create a document from dict with page_content
        data = {
            "page_content": "Test page content",
            "metadata": {"title": "Test Document"}
        }
        doc = Document.from_dict(data)
        
        assert doc.content == "Test page content"
        assert doc.metadata["title"] == "Test Document"
    
    def test_document_from_dict_validation(self):
        """Test validation when creating a Document from an invalid dictionary."""
        # Try with invalid data
        with pytest.raises(ValueError, match="Data must be a dictionary"):
            Document.from_dict("not a dict")
    
    def test_to_langchain_document(self, monkeypatch):
        """Test converting to LangChain document."""
        # Mock LangChainDocument
        class MockLangChainDocument:
            def __init__(self, page_content="", metadata=None):
                self.page_content = page_content
                self.metadata = metadata or {}
        
        # Patch import
        import sys
        sys.modules['langchain_core.documents'] = type('mockmodule', (), {
            'Document': MockLangChainDocument
        })
        
        # Create document
        doc = Document(
            content="Test content",
            metadata={"title": "Test Document"}
        )
        
        # Convert to LangChain document
        lc_doc = doc.to_langchain_document()
        
        # Check conversion
        assert isinstance(lc_doc, MockLangChainDocument)
        assert lc_doc.page_content == "Test content"
        assert lc_doc.metadata["title"] == "Test Document"
        
        # Clean up
        del sys.modules['langchain_core.documents']


class TestSearchQuery:
    """Tests for the SearchQuery model."""

    def test_search_query_creation(self):
        """Test creating a SearchQuery instance."""
        # Create a search query
        query = SearchQuery(
            query="test query",
            max_pages=10,
            max_results=20
        )
        
        # Check attributes
        assert query.query == "test query"
        assert query.max_pages == 10
        assert query.max_results == 20
    
    def test_search_query_defaults(self):
        """Test default values for SearchQuery."""
        # Create with just the required field
        query = SearchQuery(query="test query")
        
        # Check defaults
        assert query.query == "test query"
        assert query.max_pages == 5  # Default
        assert query.max_results == 10  # Default
    
    def test_search_query_validation(self):
        """Test validation for SearchQuery."""
        # Empty query should fail
        with pytest.raises(ValidationError):
            SearchQuery(query="")
        
        # Max pages too low
        with pytest.raises(ValidationError):
            SearchQuery(query="test", max_pages=0)
        
        # Max pages too high
        with pytest.raises(ValidationError):
            SearchQuery(query="test", max_pages=21)
        
        # Max results too low
        with pytest.raises(ValidationError):
            SearchQuery(query="test", max_results=0)
        
        # Max results too high
        with pytest.raises(ValidationError):
            SearchQuery(query="test", max_results=51)


class TestUserPreferences:
    """Tests for the UserPreferences model."""

    def test_user_preferences_creation(self):
        """Test creating a UserPreferences instance."""
        # Create user preferences
        prefs = UserPreferences(
            verbosity="concise",
            format="legal",
            citations=False,
            max_results=15
        )
        
        # Check attributes
        assert prefs.verbosity == "concise"
        assert prefs.format == "legal"
        assert prefs.citations is False
        assert prefs.max_results == 15
    
    def test_user_preferences_defaults(self):
        """Test default values for UserPreferences."""
        # Create with no fields
        prefs = UserPreferences()
        
        # Check defaults
        assert prefs.verbosity == "detailed"
        assert prefs.format == "simple"
        assert prefs.citations is True
        assert prefs.max_results == 5
    
    def test_user_preferences_dict(self):
        """Test converting UserPreferences to dictionary."""
        # Create user preferences
        prefs = UserPreferences(
            verbosity="comprehensive",
            format="technical",
            citations=True,
            max_results=10
        )
        
        # Convert to dict
        prefs_dict = prefs.dict()
        
        # Check dict values
        assert prefs_dict["verbosity"] == "comprehensive"
        assert prefs_dict["format"] == "technical"
        assert prefs_dict["citations"] is True
        assert prefs_dict["max_results"] == 10


class TestSearchRequest:
    """Tests for the SearchRequest model."""

    def test_search_request_creation(self):
        """Test creating a SearchRequest instance."""
        # Create a search request
        req = SearchRequest(
            query="test query",
            preferences=UserPreferences(
                verbosity="comprehensive",
                format="legal",
                citations=True,
                max_results=10
            )
        )
        
        # Check attributes
        assert req.query == "test query"
        assert req.preferences.verbosity == "comprehensive"
        assert req.preferences.format == "legal"
        assert req.preferences.citations is True
        assert req.preferences.max_results == 10
    
    def test_search_request_without_preferences(self):
        """Test creating a SearchRequest without preferences."""
        # Create with just the query
        req = SearchRequest(query="test query")
        
        # Check preferences is None
        assert req.preferences is None
    
    def test_search_request_validation(self):
        """Test validation for SearchRequest."""
        # Empty query should fail
        with pytest.raises(ValidationError):
            SearchRequest(query="")


class TestSearchResult:
    """Tests for the SearchResult model."""

    def test_search_result_creation(self):
        """Test creating a SearchResult instance."""
        # Create a search result
        result = SearchResult(
            original_query="test query",
            keywords=["test", "query"],
            documents=[
                {
                    "content": "Test content",
                    "metadata": {"title": "Test Document"}
                }
            ],
            response="Test response"
        )
        
        # Check attributes
        assert result.original_query == "test query"
        assert result.keywords == ["test", "query"]
        assert len(result.documents) == 1
        assert result.documents[0]["content"] == "Test content"
        assert result.documents[0]["metadata"]["title"] == "Test Document"
        assert result.response == "Test response"
        assert isinstance(result.timestamp, datetime)
    
    def test_search_result_defaults(self):
        """Test default values for SearchResult."""
        # Create with just required fields
        result = SearchResult(
            original_query="test query",
            response="Test response"
        )
        
        # Check defaults
        assert result.keywords == []
        assert result.documents == []
        assert isinstance(result.timestamp, datetime)


class TestErrorResponse:
    """Tests for the ErrorResponse model."""

    def test_error_response_creation(self):
        """Test creating an ErrorResponse instance."""
        # Create an error response
        error = ErrorResponse(
            detail="Test error",
            status_code=404
        )
        
        # Check attributes
        assert error.detail == "Test error"
        assert error.status_code == 404
        assert isinstance(error.timestamp, datetime)