from typing import List, Dict, Any, Optional
from app.core.logging import get_logger
from app.domain.models import Document
from app.core.exceptions import DocumentNotFoundError, ScraperError
from app.infrastructure.scrapers.bpk_scraper import BPKScraper
from app.infrastructure.ai.openai_client import OpenAIClient
from app.infrastructure.ai.indobert import IndoBERTClient
from app.utils.pdf import PDFExtractor

logger = get_logger(__name__)


class DocumentService:
    """Service for document operations."""
    
    def __init__(
        self,
        bpk_scraper: BPKScraper,
        openai_client: Optional[OpenAIClient] = None,
        indobert_client: Optional[IndoBERTClient] = None
    ):
        """
        Initialize the document service.
        
        Args:
            bpk_scraper: BPK scraper instance
            openai_client: OpenAI client instance
            indobert_client: IndoBERT client instance
        """
        self.bpk_scraper = bpk_scraper
        self.openai_client = openai_client
        self.indobert_client = indobert_client
        self.pdf_extractor = PDFExtractor()
        
        # In-memory document storage (could be replaced with a database)
        self.documents = {}
    
    def search_documents(
        self, 
        query: str, 
        max_pages: int = 5, 
        max_results: int = 10
    ) -> List[Document]:
        """
        Search for documents based on a query.
        
        Args:
            query: The search query
            max_pages: Maximum number of pages to scrape
            max_results: Maximum number of results to return
            
        Returns:
            List of documents matching the query
        """
        try:
            logger.info(f"Searching for documents with query: {query}")
            
            # Use the BPK scraper to search for documents
            documents = self.bpk_scraper.search(
                query=query,
                max_pages=max_pages,
                max_results=max_results
            )
            
            # Store documents for future reference
            for i, doc in enumerate(documents):
                # Generate a document ID
                doc_id = f"doc_{hash(doc.content)}"
                doc.metadata['id'] = doc_id
                
                # Store the document
                self.documents[doc_id] = doc
            
            return documents
        except Exception as e:
            logger.error(f"Error searching for documents: {str(e)}")
            raise ScraperError(f"Error searching for documents: {str(e)}")
    
    def get_document_by_id(self, document_id: str) -> Document:
        """
        Get a document by its ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            The document if found
            
        Raises:
            DocumentNotFoundError: If the document is not found
        """
        document = self.documents.get(document_id)
        if not document:
            logger.warning(f"Document with ID {document_id} not found")
            raise DocumentNotFoundError(document_id)
        return document
    
    def extract_pdf_content(
        self, 
        pdf_url: str, 
        title: str = "PDF Document"
    ) -> Optional[Document]:
        """
        Extract content from a PDF file.
        
        Args:
            pdf_url: URL of the PDF file
            title: Title of the document
            
        Returns:
            Document with PDF content and metadata, or None if extraction fails
        """
        try:
            logger.info(f"Extracting content from PDF: {pdf_url}")
            
            # Download and extract the PDF
            content, metadata = self.pdf_extractor.download_and_extract(
                pdf_url=pdf_url,
                title=title
            )
            
            if not content:
                logger.warning(f"Failed to extract content from PDF: {pdf_url}")
                return None
            
            # Create a document
            document = Document(content=content, metadata=metadata)
            
            # Generate a document ID
            doc_id = f"pdf_{hash(content)}"
            document.metadata['id'] = doc_id
            
            # Store the document
            self.documents[doc_id] = document
            
            return document
        except Exception as e:
            logger.error(f"Error extracting PDF content: {str(e)}")
            return None
    
    def generate_report(
        self, 
        query: str, 
        documents: List[Document], 
        response: str
    ) -> str:
        """
        Generate an HTML report of the documents.
        
        Args:
            query: The original query
            documents: List of documents
            response: Generated response
            
        Returns:
            Path to the generated HTML file
        """
        try:
            logger.info(f"Generating report for query: {query}")
            
            # Use the BPK scraper to generate the HTML report
            report_path = self.bpk_scraper.generate_html_report(
                query=query,
                documents=documents,
                response=response
            )
            
            return report_path
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return f"Error generating report: {str(e)}"
    
    def rank_documents(
        self, 
        query: str, 
        documents: List[Document]
    ) -> List[Document]:
        """
        Rank documents by relevance to a query.
        
        Args:
            query: The query text
            documents: List of documents to rank
            
        Returns:
            Documents sorted by relevance
        """
        if not self.indobert_client or not self.indobert_client.is_available:
            logger.warning("IndoBERT is not available for document ranking")
            return documents
        
        try:
            logger.info("Ranking documents by relevance using IndoBERT")
            
            # Extract content and metadata for IndoBERT ranking
            doc_dicts = [
                {"content": doc.content, "metadata": doc.metadata}
                for doc in documents
            ]
            
            # Rank the documents
            ranked_docs = self.indobert_client.rank_documents(query, doc_dicts)
            
            # Convert back to Document objects
            ranked_documents = [
                Document(
                    content=doc["content"],
                    metadata=doc["metadata"]
                )
                for doc in ranked_docs
            ]
            
            return ranked_documents
        except Exception as e:
            logger.error(f"Error ranking documents: {str(e)}")
            return documents