import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from app.core.logging import get_logger
from app.domain.models import Document
from app.core.exceptions import ScraperError

logger = get_logger(__name__)


class BaseScraper(ABC):
    """Base class for legal document scrapers."""
    
    def __init__(self, request_timeout: int = 30):
        """
        Initialize the base scraper.
        
        Args:
            request_timeout: Request timeout in seconds
        """
        self.request_timeout = request_timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         'Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    @abstractmethod
    def search(self, query: str, max_pages: int = 5, max_results: int = 10) -> List[Document]:
        """
        Search for legal documents based on the query.
        
        Args:
            query: The user's query
            max_pages: Maximum number of pages to scrape
            max_results: Maximum number of results to return
            
        Returns:
            List of document objects with content and metadata
        """
        pass
    
    def create_session(self, retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
        """
        Create a requests session with retry capabilities.
        
        Args:
            retries: Number of retries
            backoff_factor: Backoff factor for retries
            
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # Apply retry strategy to session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_page_content(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[BeautifulSoup]:
        """
        Get the content of a page as BeautifulSoup object.
        
        Args:
            url: The URL to fetch
            params: Optional query parameters
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            # Use session with retries
            session = self.create_session()
            
            # Make the request
            response = session.get(
                url, 
                params=params, 
                headers=self.headers, 
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing content from {url}: {str(e)}")
            return None
    
    def find_pdf_links(self, url: str) -> List[Dict[str, str]]:
        """
        Find PDF links on a given website page.
        
        Args:
            url: URL of the page to search for PDF links
            
        Returns:
            List of PDF URLs found on the page
        """
        pdf_links = []
        
        try:
            logger.info(f"Searching for PDF links on {url}")
            
            # Get the page content
            soup = self.get_page_content(url)
            if not soup:
                return []
            
            # Find all links on the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Check if the link is a PDF
                if href.lower().endswith('.pdf'):
                    # Make sure the URL is absolute
                    if not href.startswith('http'):
                        href = urljoin(url, href)
                    
                    pdf_links.append({
                        'url': href,
                        'text': link.get_text().strip() or os.path.basename(href),
                        'source_page': url
                    })
            
            logger.info(f"Found {len(pdf_links)} PDF links on {url}")
            return pdf_links
            
        except Exception as e:
            logger.error(f"Error finding PDF links: {str(e)}")
            return []
    
    def extract_elements(
        self, 
        soup: BeautifulSoup, 
        selectors: List[str],
        get_text: bool = True,
        strip: bool = True
    ) -> Optional[Any]:
        """
        Extract elements from a BeautifulSoup object using multiple selectors.
        
        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try
            get_text: Whether to get the text from the element
            strip: Whether to strip the text
            
        Returns:
            The extracted element, text, or None if not found
        """
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if get_text:
                    text = element.get_text()
                    return text.strip() if strip else text
                return element
        return None
    
    def extract_all_elements(
        self, 
        soup: BeautifulSoup, 
        selectors: List[str],
        get_text: bool = True,
        strip: bool = True
    ) -> List[Any]:
        """
        Extract all matching elements from a BeautifulSoup object using multiple selectors.
        
        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try
            get_text: Whether to get the text from the elements
            strip: Whether to strip the text
            
        Returns:
            List of extracted elements or texts
        """
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                if get_text:
                    texts = [elem.get_text() for elem in elements]
                    if strip:
                        texts = [text.strip() for text in texts]
                    return texts
                return elements
        return []