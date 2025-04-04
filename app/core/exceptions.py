from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        status_code: int = 500,
        detail: str = "An unexpected error occurred",
        headers: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(self.detail)
    
    def __str__(self) -> str:
        return f"{self.status_code}: {self.detail}"


class DocumentNotFoundError(BaseAPIException):
    """Exception raised when a document is not found."""
    
    def __init__(self, document_id: str):
        super().__init__(
            status_code=404,
            detail=f"Document with ID {document_id} not found"
        )


class InvalidQueryError(BaseAPIException):
    """Exception raised when a query is invalid."""
    
    def __init__(self, detail: str = "Invalid query"):
        super().__init__(
            status_code=400,
            detail=detail
        )


class ScraperError(BaseAPIException):
    """Exception raised when there's an error with the scraper."""
    
    def __init__(self, detail: str = "Error scraping data"):
        super().__init__(
            status_code=500,
            detail=detail
        )


class OpenAIError(BaseAPIException):
    """Exception raised when there's an error with OpenAI."""
    
    def __init__(self, detail: str = "OpenAI API error"):
        super().__init__(
            status_code=500,
            detail=detail
        )


class InternalServerError(BaseAPIException):
    """Exception raised for internal server errors."""
    
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=500,
            detail=detail
        )


class UnauthorizedError(BaseAPIException):
    """Exception raised when a user is not authorized."""
    
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=401,
            detail=detail
        )


class ResourceExistsError(BaseAPIException):
    """Exception raised when a resource already exists."""
    
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=409,
            detail=detail
        )


class DependencyNotFoundError(BaseAPIException):
    """Exception raised when a required dependency is not found."""
    
    def __init__(self, dependency_name: str):
        super().__init__(
            status_code=500,
            detail=f"Required dependency '{dependency_name}' not found or not correctly configured"
        )