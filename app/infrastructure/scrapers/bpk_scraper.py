import os
import re
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from app.core.logging import get_logger
from app.domain.models import Document
from app.core.exceptions import ScraperError
from app.infrastructure.scrapers.base import BaseScraper
from app.utils.pdf import PDFExtractor
from app.utils.text import IndonesianTextProcessor

logger = get_logger(__name__)


class BPKScraper(BaseScraper):
    """Scraper for peraturan.bpk.go.id website."""
    
    def __init__(
        self,
        openai_client=None,
        indobert_client=None,
        request_timeout: int = 30
    ):
        """
        Initialize the BPK legal document scraper.
        
        Args:
            openai_client: OpenAI client for language processing
            indobert_client: IndoBERT client for embeddings
            request_timeout: Request timeout in seconds
        """
        super().__init__(request_timeout=request_timeout)
        
        self.openai_client = openai_client
        self.indobert_client = indobert_client
        self.pdf_extractor = PDFExtractor()
        self.text_processor = IndonesianTextProcessor()
        
        # Set base URL
        self.base_url = "https://peraturan.bpk.go.id"
        
        logger.info("BPK Scraper initialized successfully")
    
    def preprocess_query(self, query: str) -> str:
        """
        Preprocess and enhance the user query.
        
        Args:
            query: The original user query
            
        Returns:
            The enhanced query
        """
        try:
            logger.info(f"Preprocessing query: {query}")
            
            # Use stemming if available
            if self.text_processor.has_stemmer:
                # Stem the query
                stemmed_words = []
                for word in query.split():
                    if len(word) > 3:  # Only stem words longer than 3 characters
                        stemmed_word = self.text_processor.stem_text(word)
                        stemmed_words.append(stemmed_word)
                    else:
                        stemmed_words.append(word)
                
                stemmed_query = " ".join(stemmed_words)
                logger.info(f"Stemmed query: {stemmed_query}")
                
                # Combine original and stemmed query for better results
                enhanced_query = f"{query} {stemmed_query}"
            else:
                enhanced_query = query
            
            # Use OpenAI to enhance the query with legal terminology if available
            if self.openai_client and self.openai_client.is_available:
                try:
                    prompt = f"""
                    As a legal expert in Indonesian law, enhance this query to include proper legal terminology and relevant legal concepts:
                    
                    Query: {query}
                    
                    Enhanced query:
                    """
                    
                    response = self.openai_client.invoke(prompt)
                    
                    # Extract the enhanced query from the response
                    enhanced_query = response.strip()
                    
                    logger.info(f"Enhanced query with legal terminology: {enhanced_query}")
                except Exception as e:
                    logger.warning(f"Error enhancing query with OpenAI: {str(e)}")
            
            # Enhance with legal terms using rule-based approach as fallback
            if not self.openai_client or not self.openai_client.is_available:
                enhanced_query = self.text_processor.enhance_query_with_legal_terms(query)
                logger.info(f"Enhanced query with rule-based approach: {enhanced_query}")
            
            return enhanced_query
            
        except Exception as e:
            logger.error(f"Error preprocessing query: {str(e)}")
            return query
    
    def scrape_peraturan_bpk(self, query: str, max_pages: int = 10) -> List[Document]:
        """
        Scrape peraturan.bpk.go.id for legal information based on a query.
        
        Args:
            query: The search query
            max_pages: Maximum number of search result pages to process
            
        Returns:
            List of document objects with content and metadata
        """
        logger.info(f"Searching for legal information related to: {query}")
        
        documents = []
        
        try:
            # Process the query with legal language conversion if available
            processed_query = self.preprocess_query(query)
            
            # If the query was enhanced, log it
            if processed_query != query:
                logger.info(f"Enhanced query: {processed_query}")
                
            # Prepare the search URL
            search_url = f"{self.base_url}/Search"
            
            # Process search result pages
            for page in range(1, max_pages + 1):
                try:
                    logger.info(f"Searching page {page}")
                    
                    # Construct the page URL with parameters
                    params = {
                        'keywords': processed_query,
                        'page': page if page > 1 else None
                    }
                    
                    # Remove None values
                    params = {k: v for k, v in params.items() if v is not None}
                    
                    # Get the page content
                    soup = self.get_page_content(search_url, params)
                    if not soup:
                        logger.warning(f"Failed to get page {page}")
                        continue
                    
                    # Find all search result items - try multiple selectors
                    result_items = []
                    
                    # Try different selectors for result items
                    selectors = [
                        '.card', 
                        '.card-body', 
                        '.search-result', 
                        '.search-result-item', 
                        '.row .col-md-12'
                    ]
                    
                    for selector in selectors:
                        items = soup.select(selector)
                        if items:
                            logger.info(f"Found {len(items)} results using selector: {selector}")
                            result_items = items
                            break
                    
                    if not result_items:
                        # Last resort: look for any links that might be results
                        links = soup.select('a[href*="/Home/Detail/"]')
                        if links:
                            logger.info(f"Found {len(links)} results by searching for detail links")
                            
                            # Create simple result items from links
                            result_items = []
                            for link in links:
                                # Create a simple wrapper div for each link
                                div = soup.new_tag('div')
                                div.append(link)
                                result_items.append(div)
                    
                    if not result_items:
                        logger.warning(f"No results found on page {page}")
                        break
                    
                    logger.info(f"Found {len(result_items)} results on page {page}")
                    
                    # Process each result item
                    for i, item in enumerate(result_items):
                        try:
                            logger.info(f"Processing result item {i+1}/{len(result_items)}")
                            
                            # Extract title and link - try multiple approaches
                            title_element = None
                            
                            # Try different selectors to find the title and link
                            title_selectors = [
                                'h3.fw-bold.text-gray-800.mb-5 a', 
                                'h3 a', 
                                '.fw-bold.text-gray-800 a',
                                'a[href*="/Home/Detail/"]',
                                'a'
                            ]
                            
                            for selector in title_selectors:
                                candidates = item.select(selector)
                                for candidate in candidates:
                                    href = candidate.get('href', '')
                                    if href and ('/Home/Detail/' in href or '/Details/' in href):
                                        title_element = candidate
                                        logger.info(f"Found title using selector: {selector}")
                                        break
                                if title_element:
                                    break
                            
                            if not title_element:
                                logger.warning("Could not find title element, skipping item")
                                continue
                                
                            title = title_element.text.strip()
                            link = title_element.get('href')
                            if not link:
                                logger.warning("No link found, skipping item")
                                continue
                                
                            # Make the link absolute
                            link = urljoin(self.base_url, link)
                            
                            logger.info(f"Found document: {title}")
                            logger.info(f"Link: {link}")
                            
                            # Extract metadata where available
                            doc_type = "Unknown Type"
                            date = "Unknown Date"
                            preview = ""
                            
                            # Try to extract metadata - updated selectors for current website structure
                            try:
                                # Try different selectors for metadata
                                meta_elements = item.select('.text-gray-600 span, .text-muted span, small, .card-text small') or item.select('.search-result-item-meta span')
                                if meta_elements and len(meta_elements) > 0:
                                    doc_type = meta_elements[0].text.strip()
                                if meta_elements and len(meta_elements) > 1:
                                    date = meta_elements[1].text.strip()
                                    
                                # Try different selectors for preview
                                preview_element = item.select_one('.card-text:not(:has(small))') or item.select_one('.search-result-item-preview')
                                if preview_element:
                                    preview = preview_element.text.strip()
                            except Exception as meta_error:
                                logger.warning(f"Error extracting metadata: {str(meta_error)}")
                            
                            # Retrieve the full document content
                            try:
                                logger.info(f"Retrieving document content from: {link}")
                                
                                # Get the document page content
                                doc_soup = self.get_page_content(link)
                                if not doc_soup:
                                    logger.warning(f"Failed to get document page content for {link}")
                                    continue
                                
                                # Extract the main content - try multiple approaches
                                content = ""
                                
                                # Approach 1: Try specific selectors
                                content_selectors = [
                                    '.card-body', 
                                    'main .container', 
                                    '.document-content', 
                                    '.content', 
                                    'article', 
                                    '#mainContent', 
                                    '.detail-content'
                                ]
                                
                                for selector in content_selectors:
                                    content_element = doc_soup.select_one(selector)
                                    if content_element and len(content_element.get_text(strip=True)) > 100:
                                        content = content_element.get_text(separator='\n', strip=True)
                                        logger.info(f"Found content using selector: {selector} ({len(content)} chars)")
                                        break
                                
                                # Approach 2: If no content yet, try to extract from paragraphs
                                if not content or len(content) < 200:
                                    paragraphs = doc_soup.select('p') or doc_soup.select('.card-text') or doc_soup.select('div > div')
                                    if paragraphs:
                                        content = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                                
                                # Approach 3: If still no content, try to get any text from the page
                                if not content or len(content) < 200:
                                    # Get all text from the body, excluding scripts and styles
                                    for script in doc_soup(["script", "style"]):
                                        script.extract()
                                    content = doc_soup.body.get_text(separator='\n', strip=True)
                                
                                if content and len(content) > 200:
                                    # Create a Document object
                                    document = Document(
                                        content=content,
                                        metadata={
                                            'title': title,
                                            'source': link,
                                            'type': doc_type,
                                            'date': date,
                                            'preview': preview,
                                            'page': page
                                        }
                                    )
                                    
                                    documents.append(document)
                                    logger.info(f"Added document: {title} ({len(content)} chars)")
                                else:
                                    logger.warning(f"Could not extract sufficient content for: {title}")
                                    
                                    # Try to find PDF links
                                    pdf_links = self.find_pdf_links(link)
                                    
                                    if pdf_links:
                                        logger.info(f"Found {len(pdf_links)} PDF links for: {title}")
                                        
                                        # Extract content from the first PDF
                                        try:
                                            pdf_content, pdf_metadata = self.pdf_extractor.download_and_extract(
                                                pdf_links[0]['url'],
                                                self.headers,
                                                title
                                            )
                                            
                                            if pdf_content:
                                                # Create a Document object for the PDF
                                                pdf_document = Document(
                                                    content=pdf_content,
                                                    metadata={
                                                        'title': title,
                                                        'source': pdf_links[0]['url'],
                                                        'type': f"{doc_type} (PDF)",
                                                        'date': date,
                                                        'preview': preview,
                                                        'pdf_metadata': pdf_metadata,
                                                        'page': page
                                                    }
                                                )
                                                
                                                documents.append(pdf_document)
                                                logger.info(f"Added PDF document: {title} ({len(pdf_content)} chars)")
                                        except Exception as pdf_error:
                                            logger.warning(f"Error extracting PDF content: {str(pdf_error)}")
                            except Exception as doc_error:
                                logger.warning(f"Error retrieving document content: {str(doc_error)}")
                        except Exception as item_error:
                            logger.warning(f"Error processing result item: {str(item_error)}")
                    
                    # Check if there are more pages - updated selectors for pagination
                    next_page = soup.select_one('.pagination .next:not(.disabled)') or soup.select_one('.pagination .page-item:not(.active):not(.disabled) .page-link')
                    if not next_page:
                        logger.info("No more pages available")
                        break
                        
                except Exception as page_error:
                    logger.error(f"Error scraping page {page}: {str(page_error)}")
            
            logger.info(f"Scraped {len(documents)} documents from peraturan.bpk.go.id")
            
            # Rank documents by relevance if IndoBERT is available
            if self.indobert_client and self.indobert_client.is_available and documents:
                logger.info("Ranking documents by relevance using IndoBERT")
                
                # Extract content and metadata for IndoBERT ranking
                doc_dicts = [
                    {"content": doc.content, "metadata": doc.metadata}
                    for doc in documents
                ]
                
                # Rank the documents
                ranked_docs = self.indobert_client.rank_documents(query, doc_dicts)
                
                # Convert back to Document objects
                documents = [
                    Document(
                        content=doc["content"],
                        metadata=doc["metadata"]
                    )
                    for doc in ranked_docs
                ]
                
                logger.info("Documents ranked by relevance using IndoBERT")
            
        except Exception as e:
            logger.error(f"Error scraping peraturan.bpk.go.id: {str(e)}")
            raise ScraperError(f"Error scraping peraturan.bpk.go.id: {str(e)}")
        
        return documents
    
    def search_pdf_documents(self, query: str, max_pages: int = 5) -> List[Document]:
        """
        Search for PDF documents on peraturan.bpk.go.id based on a query.
        
        Args:
            query: The search query
            max_pages: Maximum number of search result pages to process
            
        Returns:
            List of document objects with PDF content and metadata
        """
        logger.info(f"Searching for PDF documents related to: {query}")
        
        if not self.pdf_extractor.is_available:
            logger.warning("PyPDF2 is not available. Cannot extract PDF content.")
            return []
            
        try:
            # Process the query with legal language conversion if available
            processed_query = self.preprocess_query(query)
            
            # If the query was enhanced, log it
            if processed_query != query:
                logger.info(f"Enhanced query for PDF search: {processed_query}")
                
            # Prepare the search URL
            search_url = f"{self.base_url}/Search/Results?query={processed_query.replace(' ', '+')}"
            
            documents = []
            pdf_urls_processed = set()  # Track processed PDFs to avoid duplicates
            
            # Process search result pages
            for page_num in range(1, max_pages + 1):
                page_url = f"{search_url}&page={page_num}"
                
                # Find PDF links on the search results page
                pdf_links = self.find_pdf_links(page_url)
                
                # Process each PDF link
                for pdf_link in pdf_links:
                    pdf_url = pdf_link['url']
                    
                    # Skip if already processed
                    if pdf_url in pdf_urls_processed:
                        continue
                        
                    pdf_urls_processed.add(pdf_url)
                    
                    # Download and extract the PDF
                    content, metadata = self.pdf_extractor.download_and_extract(
                        pdf_url, 
                        self.headers,
                        pdf_link['text']
                    )
                    
                    if content and metadata:
                        # Add additional metadata
                        metadata.update({
                            'query': query,
                            'enhanced_query': processed_query,
                            'link_text': pdf_link['text'],
                            'source_page': pdf_link['source_page']
                        })
                        
                        # Create document
                        doc = Document(content=content, metadata=metadata)
                        documents.append(doc)
                        
                        logger.info(f"Added PDF document: {metadata.get('title', 'Untitled')}")
            
            # Sort documents by relevance if embeddings are available
            if self.indobert_client and self.indobert_client.is_available and documents:
                logger.info("Sorting PDF documents by relevance using IndoBERT")
                
                # Extract content and metadata for IndoBERT ranking
                doc_dicts = [
                    {"content": doc.content, "metadata": doc.metadata}
                    for doc in documents
                ]
                
                # Rank the documents
                ranked_docs = self.indobert_client.rank_documents(query, doc_dicts)
                
                # Convert back to Document objects
                documents = [
                    Document(
                        content=doc["content"],
                        metadata=doc["metadata"]
                    )
                    for doc in ranked_docs
                ]
                
                logger.info("PDF documents sorted by relevance using IndoBERT")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching for PDF documents: {str(e)}")
            return []
    
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
        logger.info(f"Searching for documents related to: {query}")
        
        try:
            # Process the query with legal language conversion if available
            processed_query = self.preprocess_query(query)
            
            # If the query was enhanced, log it
            if processed_query != query:
                logger.info(f"Enhanced query: {processed_query}")
            
            # Scrape documents from peraturan.bpk.go.id
            documents = self.scrape_peraturan_bpk(processed_query, max_pages=max_pages)
            
            # Search for PDF documents if PyPDF2 is available
            if self.pdf_extractor.is_available:
                logger.info("Searching for PDF documents...")
                pdf_documents = self.search_pdf_documents(processed_query, max_pages=max_pages)
                
                if pdf_documents:
                    logger.info(f"Found {len(pdf_documents)} PDF documents")
                    documents.extend(pdf_documents)
            
            # Sort all documents by relevance if embeddings are available
            if self.indobert_client and self.indobert_client.is_available and documents:
                logger.info("Sorting all documents by relevance using IndoBERT")
                
                # Extract content and metadata for IndoBERT ranking
                doc_dicts = [
                    {"content": doc.content, "metadata": doc.metadata}
                    for doc in documents
                ]
                
                # Rank the documents
                ranked_docs = self.indobert_client.rank_documents(query, doc_dicts)
                
                # Convert back to Document objects
                documents = [
                    Document(
                        content=doc["content"],
                        metadata=doc["metadata"]
                    )
                    for doc in ranked_docs
                ]
                
                logger.info("All documents sorted by relevance using IndoBERT")
            
            # Limit results
            if max_results and len(documents) > max_results:
                documents = documents[:max_results]
            
            if documents:
                logger.info(f"Found {len(documents)} relevant documents in total")
            else:
                logger.warning(f"No documents found for query: {query}")
                
            return documents
            
        except Exception as e:
            logger.error(f"Error searching for documents: {str(e)}")
            raise ScraperError(f"Error searching for documents: {str(e)}")
    
    def generate_html_report(self, query: str, documents: List[Document], response: str) -> str:
        """
        Generate an HTML report of the scraped documents.
        
        Args:
            query: The original query
            documents: List of Document objects
            response: The response from the LLM
            
        Returns:
            The path to the generated HTML file
        """
        try:
            # Create timestamp for unique filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Generate a safe filename from the query
            safe_query = re.sub(r'[^\w\s-]', '', query)
            safe_query = re.sub(r'[\s-]+', '_', safe_query)
            
            # Create the filename
            filename = f"bpk_report_{safe_query}_{timestamp}.html"
            
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>BPK Legal Document Report: {query}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        color: #333;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: #fff;
                        padding: 20px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }}
                    header {{
                        background-color: #005A9C;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                    h1 {{
                        margin: 0;
                        font-size: 24px;
                    }}
                    h2 {{
                        color: #005A9C;
                        border-bottom: 1px solid #ddd;
                        padding-bottom: 10px;
                        margin-top: 30px;
                    }}
                    .query-info {{
                        background-color: #f5f5f5;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }}
                    .document {{
                        margin-bottom: 30px;
                        padding: 15px;
                        background-color: #f9f9f9;
                        border-radius: 5px;
                        border-left: 5px solid #005A9C;
                    }}
                    .document-header {{
                        margin-bottom: 10px;
                    }}
                    .document-title {{
                        font-weight: bold;
                        font-size: 18px;
                        color: #005A9C;
                    }}
                    .document-meta {{
                        color: #666;
                        font-size: 14px;
                        margin: 5px 0;
                    }}
                    .document-content {{
                        max-height: 300px;
                        overflow-y: auto;
                        padding: 10px;
                        background-color: #fff;
                        border: 1px solid #ddd;
                        border-radius: 3px;
                        margin-top: 10px;
                    }}
                    .document-content pre {{
                        white-space: pre-wrap;
                        font-family: monospace;
                        margin: 0;
                    }}
                    .response {{
                        background-color: #e6f7ff;
                        padding: 20px;
                        border-radius: 5px;
                        margin-bottom: 30px;
                        border-left: 5px solid #1890ff;
                    }}
                    footer {{
                        text-align: center;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #ddd;
                        color: #666;
                        font-size: 14px;
                    }}
                    .relevance-score {{
                        display: inline-block;
                        padding: 3px 8px;
                        background-color: #005A9C;
                        color: white;
                        border-radius: 12px;
                        font-size: 12px;
                        margin-left: 10px;
                    }}
                    .pdf-badge {{
                        display: inline-block;
                        padding: 3px 8px;
                        background-color: #d9534f;
                        color: white;
                        border-radius: 12px;
                        font-size: 12px;
                        margin-left: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <header>
                        <h1>BPK Legal Document Report</h1>
                    </header>
                    
                    <div class="query-info">
                        <h2>Query Information</h2>
                        <p><strong>Original Query:</strong> {query}</p>
                        <p><strong>Search Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        <p><strong>Documents Found:</strong> {len(documents)}</p>
                    </div>
                    
                    <div class="response">
                        <h2>Response</h2>
                        <p>{response.replace('\n', '<br>')}</p>
                    </div>
                    
                    <h2>Retrieved Documents</h2>
            """
            
            # Add each document to the HTML
            for i, doc in enumerate(documents):
                title = doc.metadata.get('title', 'Untitled Document')
                source = doc.metadata.get('source', 'Unknown Source')
                doc_type = doc.metadata.get('type', 'html')
                
                # Get document type indicator
                doc_type_badge = ""
                if "PDF" in doc_type:
                    doc_type_badge = '<span class="pdf-badge">PDF</span>'
                
                # Get relevance score if available
                relevance_badge = ""
                if 'relevance_score' in doc.metadata:
                    score = doc.metadata['relevance_score']
                    relevance_badge = f'<span class="relevance-score">Relevance: {score:.2f}</span>'
                
                # Format content based on type
                if "PDF" in doc_type:
                    # For PDF content, preserve formatting
                    content_html = f"<pre>{doc.content}</pre>"
                else:
                    # For HTML content, preserve HTML formatting
                    content_html = doc.content.replace('\n', '<br>')
                
                # Add document to HTML
                html_content += f"""
                    <div class="document">
                        <div class="document-header">
                            <div class="document-title">{i+1}. {title} {doc_type_badge} {relevance_badge}</div>
                            <div class="document-meta"><strong>Source:</strong> <a href="{source}" target="_blank">{source}</a></div>
                            <div class="document-meta"><strong>Type:</strong> {doc_type}</div>
                """
                
                # Add date if available
                if 'date' in doc.metadata:
                    html_content += f"""
                            <div class="document-meta"><strong>Date:</strong> {doc.metadata['date']}</div>
                    """
                
                # Add content preview
                html_content += f"""
                        </div>
                        <div class="document-content">
                            {content_html}
                        </div>
                    </div>
                """
            
            # Close HTML tags
            html_content += """
                </div>
                
                <footer>
                    <p>This report was generated using the BPK Legal Document API.</p>
                </footer>
            </body>
            </html>
            """
            
            # Write HTML to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Report saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            return f"Error generating report: {str(e)}"