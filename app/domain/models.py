from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime


class Document(BaseModel):
    """Document model representing a legal document."""
    content: str = Field(..., description="The document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    
    @property
    def page_content(self) -> str:
        """Compatibility with LangChain Document format."""
        return self.content
    
    def to_langchain_document(self):
        """Convert to LangChain Document format if available."""
        try:
            from langchain_core.documents import Document as LangChainDocument
            return LangChainDocument(page_content=self.content, metadata=self.metadata)
        except ImportError:
            return self
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create a Document from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        content = data.get("page_content") or data.get("content", "")
        metadata = data.get("metadata", {})
        
        return cls(content=content, metadata=metadata)


class SearchQuery(BaseModel):
    """Model representing a search query."""
    query: str = Field(..., min_length=1, description="The search query")
    max_pages: int = Field(default=5, ge=1, le=20, description="Maximum number of pages to search")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of results to return")
    

class UserPreferences(BaseModel):
    """Model representing user preferences for response formatting."""
    verbosity: str = Field(
        default="detailed", 
        description="Response verbosity level"
    )
    format: str = Field(
        default="simple", 
        description="Response format style"
    )
    citations: bool = Field(
        default=True, 
        description="Whether to include citations"
    )
    max_results: int = Field(
        default=5, 
        ge=1, 
        le=20, 
        description="Maximum number of results to return"
    )
    
    class Config:
        use_enum_values = True


class SearchRequest(BaseModel):
    """Model representing a search request with query and preferences."""
    query: str = Field(..., min_length=1, description="The search query")
    preferences: Optional[UserPreferences] = Field(
        default=None, 
        description="User preferences for response formatting"
    )


class SearchResult(BaseModel):
    """Model representing a search result."""
    original_query: str = Field(..., description="The original search query")
    keywords: List[str] = Field(default_factory=list, description="Keywords extracted from the query")
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved documents")
    response: str = Field(..., description="Generated response based on documents")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time of the search")


class ErrorResponse(BaseModel):
    """Model representing an error response."""
    detail: str = Field(..., description="Error detail")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time of the error")