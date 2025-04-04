from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Body, Query, Path
from fastapi.responses import JSONResponse

from app.domain.models import Document
from app.services.document_service import DocumentService
from app.api.dependencies import get_document_service
from app.core.exceptions import DocumentNotFoundError, ScraperError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=Dict[str, Any])
async def get_document(
    document_id: str = Path(..., description="The document ID"),
    document_service: DocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """
    Get a document by its ID.
    
    Args:
        document_id: The document ID
        document_service: Document service instance
        
    Returns:
        Document data
    """
    try:
        # Get the document
        document = document_service.get_document_by_id(document_id)
        
        # Convert document to dict
        return {
            "content": document.content,
            "metadata": document.metadata
        }
    except DocumentNotFoundError as e:
        logger.warning(f"Document not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/extract-pdf", response_model=Dict[str, Any])
async def extract_pdf_content(
    pdf_url: str = Body(..., description="URL of the PDF file"),
    title: Optional[str] = Body("PDF Document", description="Title of the document"),
    document_service: DocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """
    Extract content from a PDF file.
    
    Args:
        pdf_url: URL of the PDF file
        title: Title of the document
        document_service: Document service instance
        
    Returns:
        Document data with PDF content and metadata
    """
    try:
        # Extract PDF content
        document = document_service.extract_pdf_content(
            pdf_url=pdf_url,
            title=title
        )
        
        if not document:
            logger.warning(f"Failed to extract content from PDF: {pdf_url}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to extract content from PDF: {pdf_url}"
            )
        
        # Convert document to dict
        return {
            "content": document.content,
            "metadata": document.metadata
        }
    except Exception as e:
        logger.error(f"Error extracting PDF content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting PDF content: {str(e)}"
        )


@router.post("/upload-pdf", response_model=Dict[str, Any])
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    title: str = Form("Uploaded PDF Document", description="Title of the document"),
    document_service: DocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """
    Upload and extract content from a PDF file.
    
    Args:
        file: PDF file to upload
        title: Title of the document
        document_service: Document service instance
        
    Returns:
        Document data with PDF content and metadata
    """
    try:
        # Check if file is a PDF
        if not file.content_type or "pdf" not in file.content_type.lower():
            logger.warning(f"Uploaded file is not a PDF: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Uploaded file must be a PDF"
            )
        
        # Read file content
        pdf_content = await file.read()
        
        # Extract content from PDF
        content, metadata = document_service.pdf_extractor.extract_from_binary(
            pdf_binary=pdf_content,
            source=f"uploaded:{file.filename}",
            title=title
        )
        
        if not content:
            logger.warning(f"Failed to extract content from uploaded PDF: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to extract content from uploaded PDF"
            )
        
        # Create a document
        document = Document(content=content, metadata=metadata)
        
        # Generate a document ID
        doc_id = f"upload_{hash(content)}"
        document.metadata['id'] = doc_id
        
        # Store the document
        document_service.documents[doc_id] = document
        
        # Convert document to dict
        return {
            "content": document.content,
            "metadata": document.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing uploaded PDF: {str(e)}"
        )