import os
from typing import Any, Dict, List, Optional, Union
import httpx
from app.core.logging import get_logger
from app.core.exceptions import OpenAIError, DependencyNotFoundError

logger = get_logger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "qwen2.5-72b-instruct",
        temperature: float = 0.0,
        max_tokens: int = 2000,
        timeout: int = 60
    ):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key
            base_url: OpenAI API base URL
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv(
            "OPENAI_BASE_URL", 
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.client = None
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
            self.is_available = False
            return
        
        try:
            self._initialize_client()
            self.is_available = True
            logger.info(f"OpenAI client initialized successfully with base URL: {self.base_url}")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            self.is_available = False
    
    def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        try:
            # Try to import OpenAI
            from openai import OpenAI
        except ImportError:
            logger.error("Failed to import OpenAI. Make sure it's installed.")
            raise DependencyNotFoundError("openai")
        
        try:
            # Create a custom httpx client with timeout
            http_client = httpx.Client(timeout=httpx.Timeout(self.timeout))
            
            # Initialize OpenAI client with custom HTTP client
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=http_client
            )
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            
            # Try alternative initialization without custom client
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except Exception as e2:
                logger.error(f"Error in alternative initialization: {str(e2)}")
                raise OpenAIError(f"Failed to initialize OpenAI client: {str(e)}, {str(e2)}")
    
    def invoke(self, prompt: Union[str, List[Dict[str, Any]]]) -> str:
        """
        Invoke the OpenAI API with a prompt.
        
        Args:
            prompt: The prompt text or a list of messages
            
        Returns:
            The generated text response
        """
        if not self.is_available or not self.client:
            logger.warning("OpenAI client not available, returning empty response")
            return "OpenAI processing unavailable"
        
        try:
            # Convert string prompt to message format if needed
            if isinstance(prompt, str):
                messages = [{"role": "user", "content": prompt}]
            else:
                messages = prompt
            
            logger.debug(f"Sending request to OpenAI with model {self.model}")
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract and return the generated text
            result = response.choices[0].message.content
            logger.debug("Successfully received response from OpenAI")
            
            return result
        except Exception as e:
            logger.error(f"Error invoking OpenAI: {str(e)}")
            raise OpenAIError(f"Error invoking OpenAI: {str(e)}")
    
    def extract_keywords(self, query: str, num_keywords: int = 5) -> List[str]:
        """
        Extract keywords from a query using OpenAI.
        
        Args:
            query: The query text
            num_keywords: Number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        if not self.is_available:
            # Return simple keyword extraction
            return [w for w in query.split() if len(w) > 3][:num_keywords]
        
        try:
            prompt = f"""
            As a legal expert in Indonesian law, extract the most important keywords from this query 
            that would be effective for searching on a legal document website.
            
            Original query: {query}
            
            Extract {num_keywords} specific keywords or phrases that are most relevant for 
            searching legal documents. Focus on legal terminology, document types, 
            or specific regulations.
            
            Format your response as a comma-separated list of keywords only, without any additional text.
            """
            
            response = self.invoke(prompt)
            
            # Parse comma-separated keywords
            keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
            
            # If no keywords extracted, fall back to simple extraction
            if not keywords:
                keywords = [w for w in query.split() if len(w) > 3][:num_keywords]
            
            return keywords
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            # Fall back to simple keyword extraction
            return [w for w in query.split() if len(w) > 3][:num_keywords]
    
    def generate_legal_response(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> str:
        """
        Generate a legal response based on the query and documents.
        
        Args:
            query: The original query
            documents: The retrieved documents
            user_preferences: User preferences for response formatting
            
        Returns:
            The generated response
        """
        if not self.is_available:
            # Generate a simple response
            return self._generate_simple_response(query, documents)
        
        try:
            # Prepare document summaries
            document_summaries = []
            for i, doc in enumerate(documents[:5]):  # Limit to 5 documents
                title = doc.get("metadata", {}).get("title", f"Document {i+1}")
                source = doc.get("metadata", {}).get("source", "Unknown source")
                content = doc.get("content", "")
                
                # Create a preview of the content
                preview = content[:1000] + "..." if len(content) > 1000 else content
                
                document_summaries.append(
                    f"Document {i+1}: {title}\nSource: {source}\nPreview: {preview}\n"
                )
            
            # Get verbosity instruction
            verbosity = user_preferences.get("verbosity", "detailed")
            if verbosity == "concise":
                verbosity_instruction = "Keep your response concise and to the point, focusing only on the most relevant information."
            elif verbosity == "comprehensive":
                verbosity_instruction = "Provide a comprehensive response that thoroughly analyzes all relevant information from the documents."
            else:  # detailed
                verbosity_instruction = "Provide a detailed response that covers the main points from the documents."
            
            # Get format instruction
            format_style = user_preferences.get("format", "simple")
            if format_style == "legal":
                format_instruction = "Use proper legal terminology and formatting appropriate for legal professionals."
            elif format_style == "technical":
                format_instruction = "Use technical language and provide specific details about legal mechanisms and procedures."
            else:  # simple
                format_instruction = "Use simple, everyday language that a non-legal expert can understand."
            
            # Get citation instruction
            include_citations = user_preferences.get("citations", True)
            if include_citations:
                citation_instruction = "Include citations to specific documents and sections when making claims."
            else:
                citation_instruction = "Do not include formal citations in your response."
            
            # Generate the prompt
            prompt = f"""
            As a legal expert in Indonesian law, answer the following query based on the provided legal documents.
            
            Original query: {query}
            
            Retrieved documents:
            {"".join(document_summaries)}
            
            Instructions:
            1. {verbosity_instruction}
            2. {format_instruction}
            3. {citation_instruction}
            4. Focus on directly answering the query based on the legal documents provided.
            5. If the documents don't contain sufficient information to answer the query, acknowledge this limitation.
            6. Include specific references to regulations and documents where relevant.
            
            Your response:
            """
            
            # Call the OpenAI API
            response = self.invoke(prompt)
            
            return response
        except Exception as e:
            logger.error(f"Error generating legal response: {str(e)}")
            return self._generate_simple_response(query, documents)
    
    def _generate_simple_response(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """
        Generate a simple response without using OpenAI.
        
        Args:
            query: The original query
            documents: The retrieved documents
            
        Returns:
            A simple response
        """
        response = f"Based on the retrieved documents, the query about '{query}' relates to the following legal information:\n\n"
        
        for i, doc in enumerate(documents[:3]):  # Limit to first 3 documents
            title = doc.get("metadata", {}).get("title", f"Document {i+1}")
            content = doc.get("content", "")
            preview = content[:200] + "..." if len(content) > 200 else content
            response += f"- {title}: {preview}\n\n"
        
        return response