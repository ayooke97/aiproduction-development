from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Body, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError

from app.domain.models import SearchRequest, SearchResult, UserPreferences, Document
from app.services.query_service import QueryService
from app.api.dependencies import get_query_service
from app.core.exceptions import InvalidQueryError, ScraperError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/query", response_model=SearchResult)
async def search_query(
    request: SearchRequest,
    query_service: QueryService = Depends(get_query_service)
) -> SearchResult:
    """
    Search for legal documents based on a query.
    
    Args:
        request: Search request with query and preferences
        query_service: Query service instance
        
    Returns:
        Search result with documents and response
    """
    try:
        # Process the query
        result = query_service.process_query(
            query=request.query,
            user_preferences=request.preferences
        )
        
        return result
    except InvalidQueryError as e:
        logger.warning(f"Invalid query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ScraperError as e:
        logger.error(f"Scraper error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in search_query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/simple", response_model=SearchResult)
async def simple_search(
    query: str = Query(..., description="The search query"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
    verbosity: str = Query("detailed", description="Response verbosity (concise, detailed, comprehensive)"),
    format: str = Query("simple", description="Response format (simple, legal, technical)"),
    citations: bool = Query(True, description="Whether to include citations"),
    query_service: QueryService = Depends(get_query_service)
) -> SearchResult:
    """
    Simple search endpoint with query parameters.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        verbosity: Response verbosity
        format: Response format
        citations: Whether to include citations
        query_service: Query service instance
        
    Returns:
        Search result with documents and response
    """
    try:
        # Create user preferences
        preferences = UserPreferences(
            verbosity=verbosity,
            format=format,
            citations=citations,
            max_results=max_results
        )
        
        # Process the query
        result = query_service.process_query(
            query=query,
            user_preferences=preferences
        )
        
        return result
    except InvalidQueryError as e:
        logger.warning(f"Invalid query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in simple_search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/report", response_class=FileResponse)
async def generate_report(
    request: SearchRequest,
    query_service: QueryService = Depends(get_query_service)
) -> FileResponse:
    """
    Generate an HTML report of search results.
    
    Args:
        request: Search request with query and preferences
        query_service: Query service instance
        
    Returns:
        HTML report file
    """
    try:
        # Process the query
        result = query_service.process_query(
            query=request.query,
            user_preferences=request.preferences
        )
        
        # Convert documents back to Document objects
        documents = [
            Document(
                content=doc["content"],
                metadata=doc["metadata"]
            )
            for doc in result.documents
        ]
        
        # Generate the report
        report_path = query_service.generate_report(
            query=result.original_query,
            documents=documents,
            response=result.response
        )
        
        # Return the report file
        return FileResponse(
            path=report_path,
            media_type="text/html",
            filename=f"legal_report_{request.query.replace(' ', '_')}.html"
        )
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )