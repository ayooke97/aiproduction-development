import os
import tempfile
from typing import Dict, Any, Optional, Tuple
import requests
from app.core.logging import get_logger
from app.core.exceptions import DependencyNotFoundError

logger = get_logger(__name__)


class PDFExtractor:
    """Utility class for extracting content from PDF files."""
    
    def __init__(self):
        """Initialize the PDF extractor."""
        self.is_available = False
        
        try:
            # Try importing PyPDF2
            import PyPDF2
            self.is_available = True
            logger.info("PyPDF2 initialized successfully")
        except ImportError:
            logger.warning("PyPDF2 is not available. PDF extraction will be disabled.")
    
    def download_and_extract(
        self, 
        pdf_url: str, 
        headers: Optional[Dict[str, str]] = None,
        title: str = "PDF Document"
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Download a PDF file and extract its text content.
        
        Args:
            pdf_url: URL of the PDF file
            headers: HTTP headers for the request
            title: Title of the document
            
        Returns:
            Tuple of (content, metadata) or (None, None) if extraction fails
        """
        if not self.is_available:
            logger.warning("PyPDF2 is not available. Cannot extract PDF content.")
            return None, None
            
        # Default headers
        if not headers:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                             'Chrome/91.0.4472.124 Safari/537.36'
            }
            
        try:
            logger.info(f"Downloading PDF from {pdf_url}")
            
            # Download the PDF
            response = requests.get(pdf_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(response.content)
                temp_pdf_path = temp_pdf.name
                
            try:
                # Import here to ensure available
                import PyPDF2
                
                # Extract text from the PDF
                logger.info("Extracting text from PDF")
                
                try:
                    pdf_reader = PyPDF2.PdfReader(temp_pdf_path)
                    
                    # Extract metadata
                    metadata = {
                        "source": pdf_url,
                        "title": title or os.path.basename(pdf_url),
                        "pages": len(pdf_reader.pages),
                        "type": "pdf"
                    }
                    
                    # Extract PDF info dictionary if available
                    if hasattr(pdf_reader, 'metadata') and pdf_reader.metadata:
                        for key, value in pdf_reader.metadata.items():
                            if key.startswith('/'):
                                clean_key = key[1:].lower()
                                if isinstance(value, str):
                                    metadata[clean_key] = value
                    
                    # Extract text content
                    content = ""
                    for i, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            content += f"\n--- Page {i+1} ---\n"
                            content += page_text
                    
                    logger.info(f"Successfully extracted {len(pdf_reader.pages)} pages from PDF")
                    
                    # Return the extracted content and metadata
                    return content, metadata
                    
                except Exception as e:
                    logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
                    return None, None
                    
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_pdf_path)
                except Exception as e:
                    logger.warning(f"Could not delete temporary PDF file: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error downloading or processing PDF: {str(e)}", exc_info=True)
            return None, None
    
    def extract_from_binary(
        self, 
        pdf_binary: bytes,
        source: str = "uploaded_file",
        title: str = "Uploaded PDF Document"
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Extract text from a PDF binary content.
        
        Args:
            pdf_binary: Binary content of the PDF
            source: Source identifier
            title: Title of the document
            
        Returns:
            Tuple of (content, metadata) or (None, None) if extraction fails
        """
        if not self.is_available:
            logger.warning("PyPDF2 is not available. Cannot extract PDF content.")
            return None, None
            
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(pdf_binary)
                temp_pdf_path = temp_pdf.name
                
            try:
                # Import here to ensure available
                import PyPDF2
                
                # Extract text from the PDF
                logger.info("Extracting text from PDF binary")
                
                try:
                    pdf_reader = PyPDF2.PdfReader(temp_pdf_path)
                    
                    # Extract metadata
                    metadata = {
                        "source": source,
                        "title": title,
                        "pages": len(pdf_reader.pages),
                        "type": "pdf"
                    }
                    
                    # Extract PDF info dictionary if available
                    if hasattr(pdf_reader, 'metadata') and pdf_reader.metadata:
                        for key, value in pdf_reader.metadata.items():
                            if key.startswith('/'):
                                clean_key = key[1:].lower()
                                if isinstance(value, str):
                                    metadata[clean_key] = value
                    
                    # Extract text content
                    content = ""
                    for i, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            content += f"\n--- Page {i+1} ---\n"
                            content += page_text
                    
                    logger.info(f"Successfully extracted {len(pdf_reader.pages)} pages from PDF binary")
                    
                    # Return the extracted content and metadata
                    return content, metadata
                    
                except Exception as e:
                    logger.error(f"Error extracting text from PDF binary: {str(e)}", exc_info=True)
                    return None, None
                    
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_pdf_path)
                except Exception as e:
                    logger.warning(f"Could not delete temporary PDF file: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error processing PDF binary: {str(e)}", exc_info=True)
            return None, None