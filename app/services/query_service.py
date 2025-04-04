from typing import List, Dict, Any, Optional
from app.core.logging import get_logger
from app.domain.models import Document, SearchResult, UserPreferences
from app.core.exceptions import InvalidQueryError, ScraperError
from app.services.document_service import DocumentService
from app.infrastructure.ai.openai_client import OpenAIClient

logger = get_logger(__name__)


class QueryService:
    """Service for processing legal queries."""
    
    def __init__(
        self,
        document_service: DocumentService,
        openai_client: Optional[OpenAIClient] = None
    ):
        """
        Initialize the query service.
        
        Args:
            document_service: Document service instance
            openai_client: OpenAI client instance
        """
        self.document_service = document_service
        self.openai_client = openai_client
    
    def process_query(
        self,
        query: str,
        user_preferences: Optional[UserPreferences] = None
    ) -> SearchResult:
        """
        Process a legal query and generate a response.
        
        Args:
            query: The user's query
            user_preferences: User preferences for response formatting
            
        Returns:
            Search result with documents and response
        """
        if not query or len(query.strip()) == 0:
            logger.warning("Empty query received")
            raise InvalidQueryError("Query cannot be empty")
        
        try:
            logger.info(f"Processing query: {query}")
            
            # Extract keywords if OpenAI is available
            keywords = []
            if self.openai_client and self.openai_client.is_available:
                try:
                    keywords = self.openai_client.extract_keywords(query)
                    logger.info(f"Extracted keywords: {', '.join(keywords)}")
                except Exception as e:
                    logger.warning(f"Error extracting keywords: {str(e)}")
                    # Fall back to simple extraction
                    keywords = self._simple_keyword_extraction(query)
            else:
                # Fall back to simple extraction
                keywords = self._simple_keyword_extraction(query)
            
            # Set default preferences if not provided
            if not user_preferences:
                user_preferences = UserPreferences()
            
            # Search for documents
            documents = self.document_service.search_documents(
                query=query,
                max_pages=5,
                max_results=user_preferences.max_results
            )
            
            # Generate response
            response = self._generate_response(query, documents, user_preferences.dict())
            
            # Create search result
            search_result = SearchResult(
                original_query=query,
                keywords=keywords,
                documents=[self._convert_document_to_dict(doc) for doc in documents],
                response=response
            )
            
            return search_result
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise ScraperError(f"Error processing query: {str(e)}")
    
    def _simple_keyword_extraction(self, query: str, max_keywords: int = 5) -> List[str]:
        """
        Extract keywords from a query without using external services.
        
        Args:
            query: The query text
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        # Split query into words
        words = query.lower().split()
        
        # Keep only words longer than 3 characters
        keywords = [word for word in words if len(word) > 3]
        
        # Deduplicate and limit to max_keywords
        unique_keywords = list(dict.fromkeys(keywords))[:max_keywords]
        
        return unique_keywords
    
    def _generate_response(
        self,
        query: str,
        documents: List[Document],
        user_preferences: Dict[str, Any]
    ) -> str:
        """
        Generate a response based on the query and retrieved documents.
        
        Args:
            query: The user's query
            documents: Retrieved documents
            user_preferences: User preferences for response formatting
            
        Returns:
            Generated response
        """
        if not documents:
            return f"I couldn't find any relevant legal documents for your query: '{query}'."
        
        # Use OpenAI for response generation if available
        if self.openai_client and self.openai_client.is_available:
            try:
                response = self.openai_client.generate_legal_response(
                    query=query,
                    documents=[self._convert_document_to_dict(doc) for doc in documents],
                    user_preferences=user_preferences
                )
                return response
            except Exception as e:
                logger.warning(f"Error generating response with OpenAI: {str(e)}")
                # Fall back to simple response
                return self._generate_simple_response(query, documents)
        else:
            # Use simple response generation
            return self._generate_simple_response(query, documents)
    
    def _generate_simple_response(self, query: str, documents: List[Document]) -> str:
        """
        Generate a simple response without external services.
        
        Args:
            query: The user's query
            documents: Retrieved documents
            
        Returns:
            Simple response based on documents
        """
        response = f"Based on the retrieved documents, here is information related to your query about '{query}':\n\n"
        
        # Add information from the top 3 documents
        for i, doc in enumerate(documents[:3]):
            title = doc.metadata.get('title', f"Document {i+1}")
            doc_type = doc.metadata.get('type', 'Unknown')
            source = doc.metadata.get('source', 'Unknown source')
            
            # Add document summary
            response += f"Document {i+1}: {title} ({doc_type})\n"
            response += f"Source: {source}\n"
            
            # Add content preview (first 200 characters)
            preview = doc.content[:200].replace('\n', ' ') + "..." if len(doc.content) > 200 else doc.content
            response += f"Preview: {preview}\n\n"
        
        # Add concluding note
        response += "For more detailed information, please review the full documents in the search results."
        
        return response
    
    def _convert_document_to_dict(self, document: Document) -> Dict[str, Any]:
        """
        Convert a Document object to a dictionary.
        
        Args:
            document: Document object
            
        Returns:
            Dictionary representation of the document
        """
        return {
            "content": document.content,
            "metadata": document.metadata
        }
    
    def generate_report(
        self,
        query: str,
        documents: List[Document],
        response: str
    ) -> str:
        """
        Generate an HTML report of the search results.
        
        Args:
            query: The original query
            documents: List of retrieved documents
            response: Generated response
            
        Returns:
            Path to the generated HTML file
        """
        return self.document_service.generate_report(
            query=query,
            documents=documents,
            response=response
        )