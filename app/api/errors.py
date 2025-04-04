from typing import Dict, Any
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.logging import get_logger
from app.core.exceptions import (
    BaseAPIException, 
    DocumentNotFoundError, 
    InvalidQueryError, 
    ScraperError, 
    OpenAIError, 
    InternalServerError
)

logger = get_logger(__name__)


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle validation errors.
    
    Args:
        request: FastAPI request
        exc: Validation exception
        
    Returns:
        JSON response with error details
    """
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        loc = " -> ".join([str(location) for location in error.get("loc", [])])
        msg = error.get("msg", "")
        error_messages.append(f"{loc}: {msg}")
    
    error_detail = "; ".join(error_messages)
    logger.warning(f"Validation error: {error_detail}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_detail,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "timestamp": datetime.now().isoformat()
        }
    )


async def api_exception_handler(
    request: Request, 
    exc: BaseAPIException
) -> JSONResponse:
    """
    Handle API exceptions.
    
    Args:
        request: FastAPI request
        exc: API exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"API exception: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        },
        headers=exc.headers or {}
    )


async def document_not_found_handler(
    request: Request, 
    exc: DocumentNotFoundError
) -> JSONResponse:
    """
    Handle document not found errors.
    
    Args:
        request: FastAPI request
        exc: Document not found exception
        
    Returns:
        JSON response with error details
    """
    logger.warning(f"Document not found: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


async def invalid_query_handler(
    request: Request, 
    exc: InvalidQueryError
) -> JSONResponse:
    """
    Handle invalid query errors.
    
    Args:
        request: FastAPI request
        exc: Invalid query exception
        
    Returns:
        JSON response with error details
    """
    logger.warning(f"Invalid query: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


async def scraper_error_handler(
    request: Request, 
    exc: ScraperError
) -> JSONResponse:
    """
    Handle scraper errors.
    
    Args:
        request: FastAPI request
        exc: Scraper exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Scraper error: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


async def openai_error_handler(
    request: Request, 
    exc: OpenAIError
) -> JSONResponse:
    """
    Handle OpenAI errors.
    
    Args:
        request: FastAPI request
        exc: OpenAI exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"OpenAI error: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """
    Handle general exceptions.
    
    Args:
        request: FastAPI request
        exc: Any exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "timestamp": datetime.now().isoformat()
        }
    )