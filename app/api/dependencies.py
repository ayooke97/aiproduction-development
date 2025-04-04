from functools import lru_cache
from typing import Dict, Any, Optional

from app.config import get_settings
from app.infrastructure.ai.openai_client import OpenAIClient
from app.infrastructure.ai.indobert import IndoBERTClient
from app.infrastructure.scrapers.bpk_scraper import BPKScraper
from app.services.document_service import DocumentService
from app.services.query_service import QueryService


@lru_cache()
def get_openai_client() -> Optional[OpenAIClient]:
    """
    Get or create an OpenAI client instance.
    
    Returns:
        OpenAI client instance or None if disabled
    """
    settings = get_settings()
    
    # Check if OpenAI is enabled
    if not settings.ENABLE_OPENAI:
        return None
    
    # Create OpenAI client
    client = OpenAIClient(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        model=settings.OPENAI_MODEL
    )
    
    # Return client only if it's available
    return client if client.is_available else None


@lru_cache()
def get_indobert_client() -> Optional[IndoBERTClient]:
    """
    Get or create an IndoBERT client instance.
    
    Returns:
        IndoBERT client instance or None if disabled
    """
    settings = get_settings()
    
    # Check if IndoBERT is enabled
    if not settings.ENABLE_INDOBERT:
        return None
    
    # Create IndoBERT client
    client = IndoBERTClient(use_gpu=True)
    
    # Return client only if it's available
    return client if client.is_available else None


@lru_cache()
def get_bpk_scraper() -> BPKScraper:
    """
    Get or create a BPK scraper instance.
    
    Returns:
        BPK scraper instance
    """
    settings = get_settings()
    
    # Get dependencies
    openai_client = get_openai_client()
    indobert_client = get_indobert_client()
    
    # Create BPK scraper
    scraper = BPKScraper(
        openai_client=openai_client,
        indobert_client=indobert_client,
        request_timeout=settings.REQUEST_TIMEOUT
    )
    
    return scraper


@lru_cache()
def get_document_service() -> DocumentService:
    """
    Get or create a document service instance.
    
    Returns:
        Document service instance
    """
    # Get dependencies
    bpk_scraper = get_bpk_scraper()
    openai_client = get_openai_client()
    indobert_client = get_indobert_client()
    
    # Create document service
    service = DocumentService(
        bpk_scraper=bpk_scraper,
        openai_client=openai_client,
        indobert_client=indobert_client
    )
    
    return service


@lru_cache()
def get_query_service() -> QueryService:
    """
    Get or create a query service instance.
    
    Returns:
        Query service instance
    """
    # Get dependencies
    document_service = get_document_service()
    openai_client = get_openai_client()
    
    # Create query service
    service = QueryService(
        document_service=document_service,
        openai_client=openai_client
    )
    
    return service